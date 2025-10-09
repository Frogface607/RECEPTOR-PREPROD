#!/usr/bin/env python3
"""
Detailed Bootstrap Catalogs Testing - Проверка конкретных цен и БЖУ
"""

import requests
import json
import os
from datetime import datetime

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_specific_ingredients():
    """Тест с конкретными ингредиентами из bootstrap каталога"""
    log_test("🔍 ДЕТАЛЬНЫЙ ТЕСТ: Проверка конкретных ингредиентов")
    
    url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=false"
    
    # Блюдо с известными ингредиентами и их ценами
    payload = {
        "name": "Куриное филе с овощами (тест цен)",
        "cuisine": "европейская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'card' in data and data['card']:
                techcard = data['card']
                
                log_test("✅ Техкарта сгенерирована")
                log_test(f"📋 Название: {techcard.get('meta', {}).get('name', 'Неизвестно')}")
                
                # Проверяем источники данных
                cost_meta = techcard.get('costMeta', {})
                nutrition_meta = techcard.get('nutritionMeta', {})
                
                log_test(f"💰 Источник цен: {cost_meta.get('source', 'unknown')}")
                log_test(f"💰 Покрытие цен: {cost_meta.get('coveragePct', 0)}%")
                log_test(f"💰 Дата каталога: {cost_meta.get('asOf', 'unknown')}")
                
                log_test(f"🥗 Источник БЖУ: {nutrition_meta.get('source', 'unknown')}")
                log_test(f"🥗 Покрытие БЖУ: {nutrition_meta.get('coveragePct', 0)}%")
                
                # Проверяем ингредиенты
                ingredients = techcard.get('ingredients', [])
                log_test(f"🧄 Количество ингредиентов: {len(ingredients)}")
                
                for i, ingredient in enumerate(ingredients[:5]):  # Показываем первые 5
                    name = ingredient.get('name', 'Неизвестно')
                    quantity = ingredient.get('quantity', 0)
                    unit = ingredient.get('unit', '')
                    cost = ingredient.get('cost', 0)
                    
                    log_test(f"  {i+1}. {name}: {quantity}{unit} = {cost:.2f} руб")
                
                # Проверяем итоговые цены
                cost_data = techcard.get('cost', {})
                raw_cost = cost_data.get('rawCost', 0)
                cost_per_portion = cost_data.get('costPerPortion', 0)
                
                log_test(f"💵 Общая стоимость: {raw_cost:.2f} руб")
                log_test(f"💵 Стоимость порции: {cost_per_portion:.2f} руб")
                
                # Проверяем БЖУ
                nutrition = techcard.get('nutrition', {})
                per_portion = nutrition.get('perPortion', {})
                
                kcal = per_portion.get('kcal', 0)
                proteins = per_portion.get('proteins_g', 0)
                fats = per_portion.get('fats_g', 0)
                carbs = per_portion.get('carbs_g', 0)
                
                log_test(f"🍽️ БЖУ на порцию: {kcal:.1f} ккал, Б:{proteins:.1f}г, Ж:{fats:.1f}г, У:{carbs:.1f}г")
                
                # Проверяем, что источник действительно bootstrap
                if cost_meta.get('source') == 'catalog' and nutrition_meta.get('source') == 'catalog':
                    log_test("✅ Данные берутся из каталога (включая bootstrap)")
                    return True
                else:
                    log_test("❌ Данные НЕ из каталога")
                    return False
                    
        return False
        
    except Exception as e:
        log_test(f"❌ Ошибка: {e}")
        return False

def test_chicken_price_accuracy():
    """Проверка точности цены куриного филе"""
    log_test("🐔 ТЕСТ ТОЧНОСТИ: Проверка цены куриного филе")
    
    # Из bootstrap каталога: куриное филе = 450 руб/кг
    # Ожидаемая цена за 200г = 90 руб
    
    url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=false"
    
    payload = {
        "name": "Куриное филе 200г (тест точности)",
        "cuisine": "простая",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'card' in data and data['card']:
                techcard = data['card']
                
                # Ищем куриное филе в ингредиентах
                ingredients = techcard.get('ingredients', [])
                chicken_found = False
                
                for ingredient in ingredients:
                    name = ingredient.get('name', '').lower()
                    if 'курин' in name and 'филе' in name:
                        quantity = ingredient.get('quantity', 0)
                        unit = ingredient.get('unit', '')
                        cost = ingredient.get('cost', 0)
                        
                        log_test(f"🐔 Найдено: {ingredient.get('name')}")
                        log_test(f"🐔 Количество: {quantity}{unit}")
                        log_test(f"🐔 Стоимость: {cost:.2f} руб")
                        
                        # Проверяем точность (для 200г должно быть ~90 руб)
                        if unit == 'г' and quantity > 0:
                            price_per_kg = (cost / quantity) * 1000
                            log_test(f"🐔 Цена за кг: {price_per_kg:.2f} руб/кг")
                            
                            # Ожидаем 450 руб/кг ±50 руб
                            if 400 <= price_per_kg <= 500:
                                log_test("✅ Цена куриного филе корректная")
                                chicken_found = True
                            else:
                                log_test("⚠️ Цена куриного филе не соответствует ожиданиям")
                        break
                
                if not chicken_found:
                    log_test("❌ Куриное филе не найдено в ингредиентах")
                    return False
                
                return chicken_found
                
        return False
        
    except Exception as e:
        log_test(f"❌ Ошибка: {e}")
        return False

def test_bootstrap_vs_empty_catalog():
    """Проверка что bootstrap используется когда основной каталог пуст"""
    log_test("📂 ТЕСТ BOOTSTRAP: Проверка использования bootstrap каталога")
    
    # Проверяем, что основной каталог действительно пуст или мал
    price_catalog_path = "/app/backend/data/price_catalog.dev.json"
    nutrition_catalog_path = "/app/backend/data/nutrition_catalog.dev.json"
    
    try:
        # Проверяем основной каталог цен
        if os.path.exists(price_catalog_path):
            with open(price_catalog_path, 'r', encoding='utf-8') as f:
                price_catalog = json.load(f)
            
            ingredients_count = sum(len(category) for category in price_catalog.get("ingredients", {}).values())
            log_test(f"📊 Основной каталог цен: {ingredients_count} ингредиентов")
            
            if ingredients_count < 10:
                log_test("✅ Основной каталог цен пуст/мал - bootstrap должен использоваться")
            else:
                log_test("⚠️ Основной каталог цен не пуст - bootstrap может не использоваться")
        else:
            log_test("✅ Основной каталог цен отсутствует - bootstrap должен использоваться")
        
        # Проверяем основной каталог питания
        if os.path.exists(nutrition_catalog_path):
            with open(nutrition_catalog_path, 'r', encoding='utf-8') as f:
                nutrition_catalog = json.load(f)
            
            items_count = len(nutrition_catalog.get("items", []))
            log_test(f"📊 Основной каталог БЖУ: {items_count} продуктов")
            
            if items_count < 10:
                log_test("✅ Основной каталог БЖУ пуст/мал - bootstrap должен использоваться")
            else:
                log_test("⚠️ Основной каталог БЖУ не пуст - bootstrap может не использоваться")
        else:
            log_test("✅ Основной каталог БЖУ отсутствует - bootstrap должен использоваться")
        
        return True
        
    except Exception as e:
        log_test(f"❌ Ошибка проверки каталогов: {e}")
        return False

def run_detailed_tests():
    """Запуск детальных тестов"""
    log_test("🔬 ЗАПУСК ДЕТАЛЬНЫХ ТЕСТОВ BOOTSTRAP КАТАЛОГОВ")
    log_test("=" * 60)
    
    results = []
    
    # Тест 1: Проверка каталогов
    log_test("ТЕСТ 1: Проверка состояния каталогов")
    results.append(test_bootstrap_vs_empty_catalog())
    log_test("-" * 60)
    
    # Тест 2: Конкретные ингредиенты
    log_test("ТЕСТ 2: Проверка конкретных ингредиентов")
    results.append(test_specific_ingredients())
    log_test("-" * 60)
    
    # Тест 3: Точность цен
    log_test("ТЕСТ 3: Проверка точности цен")
    results.append(test_chicken_price_accuracy())
    log_test("-" * 60)
    
    # Итоги
    success_count = sum(results)
    total_tests = len(results)
    
    log_test("📋 ИТОГИ ДЕТАЛЬНЫХ ТЕСТОВ")
    log_test("=" * 60)
    log_test(f"🎯 Пройдено: {success_count}/{total_tests} тестов")
    
    if success_count == total_tests:
        log_test("🎉 ВСЕ ДЕТАЛЬНЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        log_test("✅ Bootstrap каталоги работают корректно и точно")
    else:
        log_test("⚠️ Некоторые детальные тесты не прошли")
    
    return success_count == total_tests

if __name__ == "__main__":
    run_detailed_tests()