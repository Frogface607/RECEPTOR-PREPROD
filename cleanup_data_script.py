#!/usr/bin/env python3
"""
CLEANUP TECH CARD DATA & UI - Data Cleanup Script
Навести полный порядок в данных: заменить диапазоны ID на чистые UUID
"""

import json
import uuid
import os
import re
from datetime import datetime

def generate_clean_uuid():
    """Генерируем чистый UUID"""
    return str(uuid.uuid4())

def clean_catalog_ids():
    """Очищаем ID диапазоны в каталогах данных"""
    
    print("🧹 CLEANUP TECH CARD DATA & UI: Начинаем очистку данных...")
    
    # Пути к каталогам данных
    data_dir = "/app/backend/data"
    nutrition_catalog_path = os.path.join(data_dir, "nutrition_catalog.dev.json")
    price_catalog_path = os.path.join(data_dir, "price_catalog.dev.json")
    
    # Счетчики изменений
    changes_count = 0
    
    # 1. Очищаем nutrition catalog
    print("📋 Очищаем nutrition_catalog.dev.json...")
    if os.path.exists(nutrition_catalog_path):
        with open(nutrition_catalog_path, 'r', encoding='utf-8') as f:
            nutrition_data = json.load(f)
        
        # Nutrition catalog имеет структуру с "items" массивом
        if 'items' in nutrition_data:
            for ingredient in nutrition_data['items']:
                # Проверяем canonical_id на диапазоны типа '9969-86'  
                if 'canonical_id' in ingredient:
                    canonical_id = ingredient['canonical_id']
                    # Ищем паттерны вида числа-числа или другие проблемные ID
                    if re.match(r'^\d{4}-\d{2}$', canonical_id) or \
                       re.match(r'^\d+-\d+$', canonical_id) or \
                       'mock' in canonical_id.lower() or \
                       'test' in canonical_id.lower():
                        # Генерируем чистый ID на основе имени
                        clean_name = ingredient['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')
                        # Удаляем спецсимволы и оставляем только буквы и подчеркивания
                        clean_name = re.sub(r'[^a-zA-Zа-яёА-ЯЁ0-9_]', '', clean_name)
                        ingredient['canonical_id'] = clean_name
                        changes_count += 1
                        print(f"  ✅ Заменили ID '{canonical_id}' → '{clean_name}'")
        
        # Сохраняем обновленный nutrition catalog
        with open(nutrition_catalog_path, 'w', encoding='utf-8') as f:
            json.dump(nutrition_data, f, ensure_ascii=False, indent=2)
        print(f"📋 Nutrition catalog обновлен. Изменений: {changes_count}")
    
    # 2. Очищаем price catalog
    print("💰 Очищаем price_catalog.dev.json...")
    if os.path.exists(price_catalog_path):
        with open(price_catalog_path, 'r', encoding='utf-8') as f:
            price_data = json.load(f)
        
        price_changes = 0
        
        # Проходим по всем категориям и продуктам
        for category_name, products in price_data.get('ingredients', {}).items():
            for product_name, product_info in products.items():
                if 'product_code' in product_info:
                    product_code = product_info['product_code']
                    # Все product_code уже UUID формата, но проверим на всякий случай
                    if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', product_code):
                        # Если не UUID, генерируем новый
                        new_uuid = generate_clean_uuid()
                        product_info['product_code'] = new_uuid
                        product_info['updated_date'] = datetime.now().isoformat()
                        price_changes += 1
                        print(f"  ✅ Заменили product_code '{product_code}' → '{new_uuid}'")
        
        # Сохраняем обновленный price catalog
        with open(price_catalog_path, 'w', encoding='utf-8') as f:
            json.dump(price_data, f, ensure_ascii=False, indent=2)
        print(f"💰 Price catalog обновлен. Изменений: {price_changes}")
        changes_count += price_changes
    
    print(f"✨ CLEANUP завершен! Всего изменений: {changes_count}")
    
    return changes_count

def validate_clean_data():
    """Проверяем, что данные теперь чистые"""
    print("🔍 Проверяем качество данных после очистки...")
    
    issues_found = []
    
    # Проверяем nutrition catalog
    nutrition_path = "/app/backend/data/nutrition_catalog.dev.json"
    if os.path.exists(nutrition_path):
        with open(nutrition_path, 'r', encoding='utf-8') as f:
            nutrition_data = json.load(f)
        
        # Проверяем items в nutrition catalog
        if 'items' in nutrition_data:
            for ingredient in nutrition_data['items']:
                canonical_id = ingredient.get('canonical_id', '')
                if re.match(r'^\d+-\d+$', canonical_id):
                    issues_found.append(f"Nutrition: найден диапазон ID '{canonical_id}'")
                if 'mock' in canonical_id.lower() or 'test' in canonical_id.lower():
                    issues_found.append(f"Nutrition: найден mock ID '{canonical_id}'")
    
    # Проверяем price catalog  
    price_path = "/app/backend/data/price_catalog.dev.json"
    if os.path.exists(price_path):
        with open(price_path, 'r', encoding='utf-8') as f:
            price_data = json.load(f)
        
        for category_name, products in price_data.get('ingredients', {}).items():
            for product_name, product_info in products.items():
                product_code = product_info.get('product_code', '')
                if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', product_code):
                    issues_found.append(f"Price: некорректный UUID '{product_code}' для '{product_name}'")
    
    if issues_found:
        print(f"❌ Найдены проблемы ({len(issues_found)}):")
        for issue in issues_found:
            print(f"  • {issue}")
        return False
    else:
        print("✅ Все данные чистые! Диапазоны ID и mock-значения отсутствуют.")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 CLEANUP TECH CARD DATA & UI - Data Cleanup Script")
    print("=" * 60)
    
    # Выполняем очистку
    changes = clean_catalog_ids()
    
    # Проверяем результат
    is_clean = validate_clean_data()
    
    print("=" * 60)
    if is_clean and changes > 0:
        print("🎉 УСПЕХ! Данные очищены и готовы для продакшена.")
    elif is_clean and changes == 0:
        print("✅ Данные уже были чистыми.")
    else:
        print("⚠️ Есть проблемы, требующие дополнительной очистки.")
    print("=" * 60)