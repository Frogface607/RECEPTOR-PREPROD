"""
AA-01: ArticleAllocator - автогенерация артикулов (номенклатурный код iiko)

Выдаёт свободные артикулы фиксированной ширины с резервированием,
ведёт реестр резервов для блюд и товаров.

Источник ширины: max(len(num)) по номенклатуре организации (iiko RMS/Cloud -> nomenclature.item.num)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import asyncio
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
import os
import time
from enum import Enum

logger = logging.getLogger(__name__)


class ArticleType(str, Enum):
    """Типы артикулов для аллокации"""
    DISH = "dish"
    PRODUCT = "product"


class ReservationStatus(str, Enum):
    """Статусы резерва артикулов"""
    RESERVED = "reserved"      # Мягкий резерв (48ч)
    CLAIMED = "claimed"        # Жесткий резерв (при экспорте skeletons)
    RELEASED = "released"      # Освобожден


class ArticleReservation:
    """Модель резерва артикула"""
    
    def __init__(self, 
                 article: str,
                 article_type: ArticleType,
                 organization_id: str,
                 entity_id: str,  # dishId или productId
                 entity_name: str,
                 user_id: str = "anonymous",
                 status: ReservationStatus = ReservationStatus.RESERVED):
        self.article = article
        self.article_type = article_type
        self.organization_id = organization_id
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.user_id = user_id
        self.status = status
        self.reserved_at = datetime.utcnow()
        self.claimed_at = None
        self.released_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для MongoDB"""
        return {
            'article': self.article,
            'article_type': self.article_type.value,
            'organization_id': self.organization_id,
            'entity_id': self.entity_id,
            'entity_name': self.entity_name,
            'user_id': self.user_id,
            'status': self.status.value,
            'reserved_at': self.reserved_at,
            'claimed_at': self.claimed_at,
            'released_at': self.released_at,
            'expires_at': self.reserved_at + timedelta(hours=48)  # TTL 48ч
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArticleReservation':
        """Создание из словаря MongoDB"""
        reservation = cls(
            article=data['article'],
            article_type=ArticleType(data['article_type']),
            organization_id=data['organization_id'],
            entity_id=data['entity_id'],
            entity_name=data['entity_name'],
            user_id=data.get('user_id', 'anonymous'),
            status=ReservationStatus(data['status'])
        )
        reservation.reserved_at = data['reserved_at']
        reservation.claimed_at = data.get('claimed_at')
        reservation.released_at = data.get('released_at')
        return reservation


class ArticleAllocator:
    """
    AA-01: Сервис автоаллокации артикулов
    
    Стратегия ширины: org_max_or_default
    - max(len(num)) по номенклатуре организации
    - дефолт = 5, мин = 4, макс = 6
    - кеширование ширины на 24ч
    
    Резервирование:
    - Мягкий резерв: 48ч
    - Жесткий резерв: при экспорте skeletons
    - Идемпотентность: по dishId/productId
    - Уникальность: по (orgId, article)
    """
    
    def __init__(self, mongo_client: MongoClient = None):
        if mongo_client is None:
            mongo_url = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017/ai_menu_designer')
            mongo_client = MongoClient(mongo_url)
        
        # BUGFIX: Use DB_NAME env var instead of parsing URL (MongoDB limit: 63 chars)
        db_name = os.environ.get('DB_NAME', 'receptor_pro').strip('"')
        
        # Validate DB name length (MongoDB limit)
        if len(db_name) > 63:
            logger.error(f"❌ DB name too long ({len(db_name)} chars): {db_name}")
            db_name = db_name[:63]  # Truncate to 63 chars
            logger.warning(f"⚠️ Truncated to: {db_name}")
        
        self.db = mongo_client[db_name]
        
        # Коллекции
        self.reservations = self.db.article_reservations
        self.width_cache = self.db.article_width_cache
        
        # Создаем индексы
        self._create_indexes()
        
        # Параметры конфигурации
        self.config = {
            "width_strategy": "org_max_or_default",
            "default_width": 5,
            "min_width": 4,
            "max_width": 6,
            "reserve_ttl_hours": 48,
            "width_cache_ttl_hours": 24,
            "max_allocation_attempts": 100,  # Максимум попыток поиска свободного артикула
            "retry_attempts": 3,  # Ретраи при коллизиях
            "retry_backoff_ms": [100, 300, 500]  # Backoff для ретраев
        }
    
    def _create_indexes(self):
        """Создание индексов для производительности и уникальности"""
        try:
            # Уникальный индекс для (orgId, article)
            self.reservations.create_index([
                ("organization_id", ASCENDING),
                ("article", ASCENDING)
            ], unique=True, name="org_article_unique")
            
            # Индекс для поиска по entity_id (идемпотентность)
            self.reservations.create_index([
                ("organization_id", ASCENDING),
                ("entity_id", ASCENDING),
                ("article_type", ASCENDING)
            ], name="org_entity_lookup")
            
            # TTL индекс для автоочистки expired резервов
            self.reservations.create_index([
                ("expires_at", ASCENDING)
            ], expireAfterSeconds=0, name="ttl_cleanup")
            
            # Индекс для width cache
            self.width_cache.create_index([
                ("organization_id", ASCENDING)
            ], unique=True, name="org_width_unique")
            
            logger.info("✅ Article allocator indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")
    
    def get_article_width(self, organization_id: str) -> int:
        """
        Получить ширину артикула для организации
        
        Стратегия: org_max_or_default
        1. Проверяем кеш (TTL 24ч)
        2. Если нет - вычисляем max(len(num)) по номенклатуре
        3. Применяем ограничения: мин 4, макс 6, дефолт 5
        """
        try:
            # Проверяем кеш
            cached = self.width_cache.find_one({
                "organization_id": organization_id,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if cached:
                logger.debug(f"Article width from cache for {organization_id}: {cached['width']}")
                return cached['width']
            
            # Вычисляем ширину по номенклатуре
            width = self._calculate_article_width(organization_id)
            
            # Сохраняем в кеш
            self.width_cache.replace_one(
                {"organization_id": organization_id},
                {
                    "organization_id": organization_id,
                    "width": width,
                    "calculated_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=self.config["width_cache_ttl_hours"])
                },
                upsert=True
            )
            
            logger.info(f"Article width calculated for {organization_id}: {width}")
            return width
            
        except Exception as e:
            logger.error(f"Error calculating article width for {organization_id}: {e}")
            return self.config["default_width"]
    
    def _calculate_article_width(self, organization_id: str) -> int:
        """Вычисляет ширину артикула по номенклатуре организации"""
        try:
            from .iiko_rms_service import get_iiko_rms_service
            
            rms_service = get_iiko_rms_service()
            
            # Получаем все продукты организации с артикулами
            products = rms_service.products.find({
                "organization_id": organization_id,
                "article": {"$ne": None, "$ne": ""}
            })
            
            max_width = 0
            sample_count = 0
            
            for product in products:
                article = str(product.get('article', ''))
                if article and article.isdigit():
                    max_width = max(max_width, len(article))
                    sample_count += 1
            
            # Применяем ограничения
            if max_width < self.config["min_width"]:
                width = self.config["default_width"]
            elif max_width > self.config["max_width"]:
                width = self.config["max_width"]
            else:
                width = max_width or self.config["default_width"]
            
            logger.info(f"Width calculation: {sample_count} products, max_width={max_width}, final={width}")
            
            return width
            
        except Exception as e:
            logger.error(f"Error in _calculate_article_width: {e}")
            return self.config["default_width"]
    
    def allocate_articles(self, 
                         article_type: ArticleType,
                         count: int = 1,
                         organization_id: str = "default",
                         entity_ids: List[str] = None,
                         entity_names: List[str] = None,
                         user_id: str = "anonymous") -> List[str]:
        """
        Аллоцирует артикулы с резервированием
        
        Args:
            article_type: Тип артикула (dish/product)
            count: Количество артикулов
            organization_id: ID организации
            entity_ids: ID сущностей для идемпотентности
            entity_names: Названия сущностей
            user_id: ID пользователя
            
        Returns:
            Список выделенных артикулов
            
        Raises:
            ValueError: Если не удалось выделить артикулы
        """
        if count <= 0:
            raise ValueError("Count must be positive")
        
        if entity_ids and len(entity_ids) != count:
            raise ValueError("entity_ids count must match requested count")
            
        if entity_names and len(entity_names) != count:
            raise ValueError("entity_names count must match requested count")
        
        # Получаем ширину артикула
        width = self.get_article_width(organization_id)
        
        allocated_articles = []
        
        for i in range(count):
            entity_id = entity_ids[i] if entity_ids else f"temp_{article_type}_{i}_{int(time.time())}"
            entity_name = entity_names[i] if entity_names else f"Temporary {article_type} {i+1}"
            
            # Проверяем идемпотентность
            existing = self._check_existing_allocation(organization_id, entity_id, article_type)
            if existing:
                allocated_articles.append(existing.article)
                logger.info(f"Returning existing allocation: {existing.article} for {entity_id}")
                continue
            
            # Аллоцируем новый артикул
            article = self._allocate_single_article(
                article_type=article_type,
                organization_id=organization_id,
                entity_id=entity_id,
                entity_name=entity_name,
                user_id=user_id,
                width=width
            )
            
            allocated_articles.append(article)
        
        return allocated_articles
    
    def _check_existing_allocation(self, 
                                 organization_id: str, 
                                 entity_id: str, 
                                 article_type: ArticleType) -> Optional[ArticleReservation]:
        """Проверяет существующую аллокацию для идемпотентности"""
        try:
            doc = self.reservations.find_one({
                "organization_id": organization_id,
                "entity_id": entity_id,
                "article_type": article_type.value,
                "status": {"$in": [ReservationStatus.RESERVED.value, ReservationStatus.CLAIMED.value]}
            })
            
            return ArticleReservation.from_dict(doc) if doc else None
            
        except Exception as e:
            logger.error(f"Error checking existing allocation: {e}")
            return None
    
    def _allocate_single_article(self, 
                               article_type: ArticleType,
                               organization_id: str,
                               entity_id: str,
                               entity_name: str,
                               user_id: str,
                               width: int) -> str:
        """Аллоцирует один артикул с ретраями при коллизиях"""
        
        for attempt in range(self.config["retry_attempts"]):
            try:
                article = self._find_free_article(organization_id, width)
                
                reservation = ArticleReservation(
                    article=article,
                    article_type=article_type,
                    organization_id=organization_id,
                    entity_id=entity_id,
                    entity_name=entity_name,
                    user_id=user_id
                )
                
                # Пытаемся зарезервировать (может быть DuplicateKeyError при коллизии)
                self.reservations.insert_one(reservation.to_dict())
                
                logger.info(f"✅ Allocated article {article} for {entity_name} ({article_type.value})")
                return article
                
            except DuplicateKeyError:
                # Коллизия - артикул уже занят, ретраим
                if attempt < self.config["retry_attempts"] - 1:
                    backoff = self.config["retry_backoff_ms"][attempt]
                    logger.warning(f"Article collision, retrying in {backoff}ms (attempt {attempt + 1})")
                    time.sleep(backoff / 1000.0)
                else:
                    logger.error(f"Failed to allocate article after {self.config['retry_attempts']} attempts")
                    raise ValueError(f"Could not allocate article for {entity_name} after retries")
            
            except Exception as e:
                logger.error(f"Error in article allocation attempt {attempt + 1}: {e}")
                if attempt == self.config["retry_attempts"] - 1:
                    raise ValueError(f"Article allocation failed: {str(e)}")
        
        raise ValueError("Article allocation failed after all retries")
    
    def _find_free_article(self, organization_id: str, width: int) -> str:
        """
        Ищет свободный артикул лексикографически
        
        Алгоритм:
        1. Получаем все занятые артикулы для организации
        2. Ищем первый свободный артикул нужной ширины
        3. Начинаем с минимального значения (например, 00001 для width=5)
        """
        try:
            # Получаем все занятые артикулы
            occupied_articles = set()
            
            reservations_cursor = self.reservations.find({
                "organization_id": organization_id,
                "status": {"$in": [ReservationStatus.RESERVED.value, ReservationStatus.CLAIMED.value]}
            }, {"article": 1})
            
            for doc in reservations_cursor:
                occupied_articles.add(doc['article'])
            
            # Также проверяем существующие артикулы в RMS
            try:
                from .iiko_rms_service import get_iiko_rms_service
                rms_service = get_iiko_rms_service()
                
                existing_cursor = rms_service.products.find({
                    "organization_id": organization_id,
                    "article": {"$ne": None, "$ne": ""}
                }, {"article": 1})
                
                for doc in existing_cursor:
                    article = str(doc.get('article', ''))
                    if article and len(article) == width:
                        occupied_articles.add(article)
                        
            except Exception as e:
                logger.warning(f"Could not check existing RMS articles: {e}")
            
            # Ищем свободный артикул
            min_value = int('1' + '0' * (width - 1))  # Например, 10000 для width=5
            max_value = int('9' * width)              # Например, 99999 для width=5
            
            for candidate_int in range(min_value, max_value + 1):
                candidate = str(candidate_int).zfill(width)
                
                if candidate not in occupied_articles:
                    return candidate
            
            # Если не нашли в диапазоне, пробуем с начала (00001...)
            for candidate_int in range(1, min_value):
                candidate = str(candidate_int).zfill(width)
                
                if candidate not in occupied_articles:
                    return candidate
            
            raise ValueError(f"No free articles available (width={width}, occupied={len(occupied_articles)})")
            
        except Exception as e:
            logger.error(f"Error finding free article: {e}")
            raise ValueError(f"Could not find free article: {str(e)}")
    
    def claim_articles(self, articles: List[str], organization_id: str = "default") -> Dict[str, bool]:
        """
        Переводит артикулы в статус CLAIMED (жесткий резерв при экспорте skeletons)
        
        Returns:
            Словарь {article: success_flag}
        """
        results = {}
        
        for article in articles:
            try:
                result = self.reservations.update_one(
                    {
                        "organization_id": organization_id,
                        "article": article,
                        "status": ReservationStatus.RESERVED.value
                    },
                    {
                        "$set": {
                            "status": ReservationStatus.CLAIMED.value,
                            "claimed_at": datetime.utcnow()
                        }
                    }
                )
                
                success = result.modified_count > 0
                results[article] = success
                
                if success:
                    logger.info(f"✅ Claimed article {article}")
                else:
                    logger.warning(f"⚠️ Could not claim article {article} (not found or already claimed)")
                    
            except Exception as e:
                logger.error(f"Error claiming article {article}: {e}")
                results[article] = False
        
        return results
    
    def release_articles(self, 
                        entity_ids: List[str], 
                        organization_id: str = "default",
                        reason: str = "manual_release") -> Dict[str, bool]:
        """
        Освобождает артикулы по entity_id (при отмене экспорта/удалении черновика)
        
        Returns:
            Словарь {entity_id: success_flag}
        """
        results = {}
        
        for entity_id in entity_ids:
            try:
                result = self.reservations.update_many(
                    {
                        "organization_id": organization_id,
                        "entity_id": entity_id,
                        "status": {"$in": [ReservationStatus.RESERVED.value]}  # Только мягкие резервы
                    },
                    {
                        "$set": {
                            "status": ReservationStatus.RELEASED.value,
                            "released_at": datetime.utcnow(),
                            "release_reason": reason
                        }
                    }
                )
                
                success = result.modified_count > 0
                results[entity_id] = success
                
                if success:
                    logger.info(f"✅ Released articles for entity {entity_id} (reason: {reason})")
                else:
                    logger.info(f"ℹ️ No articles to release for entity {entity_id}")
                    
            except Exception as e:
                logger.error(f"Error releasing articles for {entity_id}: {e}")
                results[entity_id] = False
        
        return results
    
    def get_allocation_stats(self, organization_id: str = "default") -> Dict[str, Any]:
        """Статистика аллокаций для организации"""
        try:
            pipeline = [
                {"$match": {"organization_id": organization_id}},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "by_type": {
                            "$push": {
                                "type": "$article_type",
                                "article": "$article"
                            }
                        }
                    }
                }
            ]
            
            stats = {"total": 0, "by_status": {}, "width": self.get_article_width(organization_id)}
            
            for group in self.reservations.aggregate(pipeline):
                status = group["_id"]
                count = group["count"]
                stats["by_status"][status] = count
                stats["total"] += count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting allocation stats: {e}")
            return {"error": str(e)}


# Singleton instance
_article_allocator = None

def get_article_allocator() -> ArticleAllocator:
    """Получить singleton instance ArticleAllocator"""
    global _article_allocator
    if _article_allocator is None:
        _article_allocator = ArticleAllocator()
    return _article_allocator