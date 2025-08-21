"""
AA-01 API: Article Allocator endpoints

POST /api/v1/iiko/articles/allocate - выдает свободные артикулы
GET /api/v1/iiko/articles/width - возвращает ширину артикулов для организации
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from ..integrations.article_allocator import (
    get_article_allocator, 
    ArticleAllocator, 
    ArticleType,
    ReservationStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/iiko/articles", tags=["Article Allocator"])


class AllocateArticlesRequest(BaseModel):
    """Запрос на аллокацию артикулов"""
    type: ArticleType = Field(..., description="Тип артикула: dish или product")
    count: int = Field(1, ge=1, le=100, description="Количество артикулов (1-100)")
    organization_id: str = Field("default", description="ID организации")
    entity_ids: Optional[List[str]] = Field(None, description="ID сущностей для идемпотентности")
    entity_names: Optional[List[str]] = Field(None, description="Названия сущностей")
    user_id: str = Field("anonymous", description="ID пользователя")


class AllocateArticlesResponse(BaseModel):
    """Ответ с выделенными артикулами"""
    status: str = Field("success", description="Статус операции")
    articles: List[str] = Field(..., description="Выделенные артикулы")
    width: int = Field(..., description="Ширина артикулов")
    organization_id: str = Field(..., description="ID организации")
    reserved_until: str = Field(..., description="Резерв действует до (ISO datetime)")


class ArticleWidthResponse(BaseModel):
    """Ответ с шириной артикулов"""
    width: int = Field(..., description="Ширина артикулов для организации")
    organization_id: str = Field(..., description="ID организации")
    strategy: str = Field("org_max_or_default", description="Стратегия вычисления ширины")


class ClaimArticlesRequest(BaseModel):
    """Запрос на claim артикулов (жесткий резерв)"""
    articles: List[str] = Field(..., description="Артикулы для claim")
    organization_id: str = Field("default", description="ID организации")


class ClaimArticlesResponse(BaseModel):
    """Ответ claim операции"""
    status: str = Field("success", description="Статус операции")
    results: Dict[str, bool] = Field(..., description="Результаты claim по артикулам")
    claimed_count: int = Field(..., description="Количество успешно claimed артикулов")


class ReleaseArticlesRequest(BaseModel):
    """Запрос на освобождение артикулов"""
    entity_ids: List[str] = Field(..., description="ID сущностей для освобождения")
    organization_id: str = Field("default", description="ID организации")
    reason: str = Field("manual_release", description="Причина освобождения")


class ReleaseArticlesResponse(BaseModel):
    """Ответ операции освобождения"""
    status: str = Field("success", description="Статус операции")
    results: Dict[str, bool] = Field(..., description="Результаты освобождения по entity_id")
    released_count: int = Field(..., description="Количество освобожденных сущностей")


@router.post("/allocate", response_model=AllocateArticlesResponse)
async def allocate_articles(request: AllocateArticlesRequest):
    """
    Аллоцирует свободные артикулы с резервированием
    
    Основные принципы:
    - Идемпотентность: повторный запрос по тому же entity_id возвращает тот же артикул
    - Уникальность: один артикул не может быть выдан дважды в одной организации
    - Резерв: мягкий резерв на 48ч, затем автоочистка
    - Ширина: автоматически определяется по номенклатуре организации
    
    Примеры использования:
    - Генерация артикулов для новых блюд при preflight
    - Генерация артикулов для новых продуктов при preflight
    - Резервирование артикулов перед экспортом skeletons
    """
    try:
        allocator = get_article_allocator()
        
        logger.info(f"Allocating {request.count} {request.type} articles for org {request.organization_id}")
        
        # Валидация
        if request.entity_ids and len(request.entity_ids) != request.count:
            raise HTTPException(400, "entity_ids count must match requested count")
            
        if request.entity_names and len(request.entity_names) != request.count:
            raise HTTPException(400, "entity_names count must match requested count")
        
        # Аллоцируем артикулы
        articles = allocator.allocate_articles(
            article_type=request.type,
            count=request.count,
            organization_id=request.organization_id,
            entity_ids=request.entity_ids,
            entity_names=request.entity_names,
            user_id=request.user_id
        )
        
        # Получаем ширину для ответа
        width = allocator.get_article_width(request.organization_id)
        
        # Рассчитываем время истечения резерва
        from datetime import datetime, timedelta
        reserved_until = (datetime.utcnow() + timedelta(hours=48)).isoformat() + "Z"
        
        return AllocateArticlesResponse(
            articles=articles,
            width=width,
            organization_id=request.organization_id,
            reserved_until=reserved_until
        )
        
    except ValueError as e:
        logger.error(f"Article allocation error: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Unexpected error in article allocation: {e}")
        raise HTTPException(500, f"Article allocation failed: {str(e)}")


@router.get("/width", response_model=ArticleWidthResponse)
async def get_article_width(organization_id: str = "default"):
    """
    Возвращает ширину артикулов для организации
    
    Стратегия org_max_or_default:
    1. Вычисляется max(len(num)) по номенклатуре организации
    2. Кешируется на 24ч для производительности  
    3. Применяются ограничения: мин=4, макс=6, дефолт=5
    
    Используется для:
    - Понимания формата артикулов перед аллокацией
    - Валидации пользовательского ввода артикулов
    - Отображения в UI (плейсхолдеры, форматирование)
    """
    try:
        allocator = get_article_allocator()
        width = allocator.get_article_width(organization_id)
        
        return ArticleWidthResponse(
            width=width,
            organization_id=organization_id
        )
        
    except Exception as e:
        logger.error(f"Error getting article width: {e}")
        raise HTTPException(500, f"Could not get article width: {str(e)}")


@router.post("/claim", response_model=ClaimArticlesResponse)
async def claim_articles(request: ClaimArticlesRequest):
    """
    Переводит артикулы в статус CLAIMED (жесткий резерв)
    
    Используется при экспорте Skeletons - после этого артикулы
    больше не освобождаются автоматически и закреплены за сущностями.
    
    CLAIMED артикулы:
    - Не освобождаются по TTL
    - Не могут быть переиспользованы
    - Переходят в "производственное" состояние
    """
    try:
        allocator = get_article_allocator()
        
        logger.info(f"Claiming {len(request.articles)} articles for org {request.organization_id}")
        
        results = allocator.claim_articles(
            articles=request.articles,
            organization_id=request.organization_id
        )
        
        claimed_count = sum(1 for success in results.values() if success)
        
        return ClaimArticlesResponse(
            results=results,
            claimed_count=claimed_count
        )
        
    except Exception as e:
        logger.error(f"Error claiming articles: {e}")
        raise HTTPException(500, f"Could not claim articles: {str(e)}")


@router.post("/release", response_model=ReleaseArticlesResponse)
async def release_articles(request: ReleaseArticlesRequest):
    """
    Освобождает артикулы по entity_ids
    
    Используется при:
    - Отмене экспорта пользователем
    - Удалении черновика техкарты
    - Ручной очистке зарезервированных артикулов
    
    Примечание: освобождаются только RESERVED артикулы,
    CLAIMED артикулы остаются зафиксированными.
    """
    try:
        allocator = get_article_allocator()
        
        logger.info(f"Releasing articles for {len(request.entity_ids)} entities (reason: {request.reason})")
        
        results = allocator.release_articles(
            entity_ids=request.entity_ids,
            organization_id=request.organization_id,
            reason=request.reason
        )
        
        released_count = sum(1 for success in results.values() if success)
        
        return ReleaseArticlesResponse(
            results=results,
            released_count=released_count
        )
        
    except Exception as e:
        logger.error(f"Error releasing articles: {e}")
        raise HTTPException(500, f"Could not release articles: {str(e)}")


@router.get("/stats")
async def get_allocation_stats(organization_id: str = "default"):
    """
    Статистика аллокаций для организации
    
    Возвращает:
    - Общее количество резервов
    - Разбивку по статусам (RESERVED/CLAIMED/RELEASED)
    - Текущую ширину артикулов
    - Информацию о занятых диапазонах
    """
    try:
        allocator = get_article_allocator()
        stats = allocator.get_allocation_stats(organization_id)
        
        return {
            "status": "success",
            "organization_id": organization_id,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting allocation stats: {e}")
        raise HTTPException(500, f"Could not get stats: {str(e)}")