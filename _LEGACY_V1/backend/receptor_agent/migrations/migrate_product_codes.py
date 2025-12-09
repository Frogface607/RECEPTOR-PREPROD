#!/usr/bin/env python3
"""
A. Hotfix & Migration: код вместо GUID везде

Миграционный скрипт для заполнения product_code в существующих техкартах.
Для всех существующих маппингов, где code пуст, вытягиваем code по GUID из RMS и обновляем записи.
"""

import logging
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Добавляем путь к backend модулям
sys.path.append('/app/backend')

from receptor_agent.integrations.iiko_rms_service import get_iiko_rms_service
from receptor_agent.techcards_v2.schemas import TechCardV2
import pymongo

logger = logging.getLogger(__name__)

class ProductCodeMigration:
    """Миграция для заполнения product_code в техкартах"""
    
    def __init__(self):
        self.rms_service = None
        self.mongo_client = None
        self.db = None
        self.techcards_collection = None
        
        # Статистика миграции
        self.stats = {
            'total_techcards': 0,
            'techcards_with_ingredients': 0,
            'total_ingredients': 0,
            'ingredients_with_skuid': 0,
            'ingredients_missing_code': 0,
            'codes_found_in_rms': 0,
            'codes_updated': 0,
            'errors': 0
        }
    
    def connect_services(self):
        """Подключение к RMS сервису и MongoDB"""
        try:
            # Подключение к iiko RMS
            self.rms_service = get_iiko_rms_service()
            logger.info("✅ Connected to iiko RMS service")
            
            # Подключение к MongoDB
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/ai_menu_designer')
            self.mongo_client = pymongo.MongoClient(mongo_url)
            
            # BUGFIX: Use DB_NAME env var instead of parsing URL (MongoDB limit: 63 chars)
            db_name = os.environ.get('DB_NAME', 'receptor_pro').strip('"')
            if len(db_name) > 63:
                db_name = db_name[:63]
            self.db = self.mongo_client[db_name]
            self.techcards_collection = self.db.techcards_v2
            
            logger.info(f"✅ Connected to MongoDB: {db_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to services: {e}")
            return False
    
    def get_product_code_from_rms(self, sku_id: str) -> Optional[str]:
        """
        Получить АРТИКУЛ (номенклатурный код) продукта из iiko RMS по GUID
        
        ВАЖНО: Форматируем все артикулы как пятизначные с ведущими нулями
        
        Args:
            sku_id: GUID продукта
            
        Returns:
            Пятизначный артикул с ведущими нулями или None если не найден
        """
        if not sku_id or not self.rms_service:
            return None
        
        try:
            # Поиск в коллекции products
            product = self.rms_service.products.find_one({"_id": sku_id})
            if product:
                article_fields = ['article', 'code', 'barcode']
                
                for field in article_fields:
                    if field in product and product[field]:
                        article_value = str(product[field]).strip()
                        
                        # Если это числовой код - форматируем как пятизначный
                        if article_value and article_value != '0' and article_value.isdigit():
                            return article_value.zfill(5)
            
            # Поиск в коллекции prices
            pricing = self.rms_service.prices.find_one({"skuId": sku_id})
            if pricing:
                article_fields = ['article', 'code', 'barcode']
                
                for field in article_fields:
                    if field in pricing and pricing[field]:
                        article_value = str(pricing[field]).strip()
                        
                        # Если это числовой код - форматируем как пятизначный
                        if article_value and article_value != '0' and article_value.isdigit():
                            return article_value.zfill(5)
            
            logger.debug(f"Product article not found for skuId: {sku_id}")
            return None
            
        except Exception as e:
            logger.warning(f"Error getting product article for {sku_id}: {e}")
            return None
    
    def migrate_techcard(self, techcard_doc: Dict[str, Any]) -> bool:
        """
        Мигрировать одну техкарту
        
        Args:
            techcard_doc: Документ техкарты из MongoDB
            
        Returns:
            True если были внесены изменения
        """
        techcard_id = techcard_doc.get('_id')
        ingredients = techcard_doc.get('ingredients', [])
        
        if not ingredients:
            return False
        
        self.stats['techcards_with_ingredients'] += 1
        modified = False
        
        for ingredient in ingredients:
            self.stats['total_ingredients'] += 1
            
            sku_id = ingredient.get('skuId')
            current_code = ingredient.get('product_code')
            
            # Пропускаем ингредиенты без skuId
            if not sku_id:
                continue
                
            self.stats['ingredients_with_skuid'] += 1
            
            # Пропускаем ингредиенты с уже заполненным product_code
            if current_code:
                continue
                
            self.stats['ingredients_missing_code'] += 1
            
            # Получаем код из RMS
            product_code = self.get_product_code_from_rms(sku_id)
            
            if product_code:
                self.stats['codes_found_in_rms'] += 1
                ingredient['product_code'] = product_code
                modified = True
                logger.debug(f"Added product_code {product_code} for ingredient {ingredient.get('name')} (skuId: {sku_id})")
        
        if modified:
            self.stats['codes_updated'] += 1
            return True
            
        return False
    
    def run_migration(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Запустить миграцию
        
        Args:
            dry_run: Если True, только анализ без изменений
            
        Returns:
            Статистика миграции
        """
        if not self.connect_services():
            return {'error': 'Failed to connect to services'}
        
        logger.info(f"🚀 Starting product code migration (dry_run={dry_run})")
        
        try:
            # Получаем все техкарты из MongoDB
            techcards_cursor = self.techcards_collection.find({})
            self.stats['total_techcards'] = self.techcards_collection.count_documents({})
            
            logger.info(f"📊 Found {self.stats['total_techcards']} techcards in database")
            
            updated_techcards = []
            
            for techcard_doc in techcards_cursor:
                try:
                    if self.migrate_techcard(techcard_doc):
                        updated_techcards.append(techcard_doc)
                        
                        if not dry_run:
                            # Сохраняем изменения в MongoDB
                            result = self.techcards_collection.replace_one(
                                {'_id': techcard_doc['_id']}, 
                                techcard_doc
                            )
                            
                            if result.modified_count == 1:
                                logger.debug(f"✅ Updated techcard {techcard_doc['_id']}")
                            else:
                                logger.warning(f"⚠️ Failed to update techcard {techcard_doc['_id']}")
                                self.stats['errors'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error processing techcard {techcard_doc.get('_id')}: {e}")
                    self.stats['errors'] += 1
            
            # Финальная статистика
            self.stats['updated_techcards'] = len(updated_techcards)
            
            logger.info("🎯 Migration completed successfully")
            logger.info(f"📊 Statistics:")
            logger.info(f"  - Total techcards: {self.stats['total_techcards']}")
            logger.info(f"  - Techcards with ingredients: {self.stats['techcards_with_ingredients']}")
            logger.info(f"  - Total ingredients: {self.stats['total_ingredients']}")
            logger.info(f"  - Ingredients with skuId: {self.stats['ingredients_with_skuid']}")
            logger.info(f"  - Ingredients missing code: {self.stats['ingredients_missing_code']}")
            logger.info(f"  - Codes found in RMS: {self.stats['codes_found_in_rms']}")
            logger.info(f"  - Techcards updated: {self.stats['codes_updated']}")
            logger.info(f"  - Errors: {self.stats['errors']}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return {'error': str(e)}
        
        finally:
            if self.mongo_client:
                self.mongo_client.close()


def main():
    """Главная функция для запуска миграции"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    migration = ProductCodeMigration()
    
    # Сначала запускаем dry run для анализа
    print("🔍 Running dry run analysis...")
    dry_run_stats = migration.run_migration(dry_run=True)
    
    if 'error' in dry_run_stats:
        print(f"❌ Dry run failed: {dry_run_stats['error']}")
        return
    
    print("\n📊 Dry run results:")
    for key, value in dry_run_stats.items():
        print(f"  {key}: {value}")
    
    # Спрашиваем подтверждение для реального запуска
    if dry_run_stats.get('ingredients_missing_code', 0) > 0:
        confirm = input(f"\n❓ Apply migration to update {dry_run_stats['ingredients_missing_code']} ingredients? (y/N): ")
        
        if confirm.lower() == 'y':
            print("💫 Running actual migration...")
            real_stats = migration.run_migration(dry_run=False)
            
            if 'error' in real_stats:
                print(f"❌ Migration failed: {real_stats['error']}")
            else:
                print("✅ Migration completed successfully!")
                print("\n📊 Final results:")
                for key, value in real_stats.items():
                    print(f"  {key}: {value}")
        else:
            print("⏸️ Migration cancelled by user")
    else:
        print("✅ No ingredients need product code migration")


if __name__ == "__main__":
    main()