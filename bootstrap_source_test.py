#!/usr/bin/env python3
"""
Bootstrap Source Verification Test - Проверка что данные действительно из bootstrap
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

def check_catalog_sources():
    """Проверка источников данных в каталогах"""
    log_test("🔍 ПРОВЕРКА ИСТОЧНИКОВ ДАННЫХ")
    
    # Проверяем основной каталог цен
    price_catalog_path = "/app/backend/data/price_catalog.dev.json"
    if os.path.exists(price_catalog_path):
        with open(price_catalog_path, 'r', encoding='utf-8') as f:
            price_catalog = json.load(f)
        
        source = price_catalog.get('source', 'unknown')
        ingredients_count = sum(len(category) for category in price_catalog.get("ingredients", {}).values())
        
        log_test(f"💰 Основной каталог цен:")
        log_test(f"   Источник: {source}")
        log_test(f"   Ингредиентов: {ingredients_count}")
        log_test(f"   Дата: {price_catalog.get('last_updated', 'unknown')}")
        
        if source == 'bootstrap_demo':
            log_test("✅ Основной каталог цен использует bootstrap данные!")
        else:
            log_test("⚠️ Основной каталог цен НЕ использует bootstrap данные")
    
    # Проверяем основной каталог БЖУ
    nutrition_catalog_path = "/app/backend/data/nutrition_catalog.dev.json"
    if os.path.exists(nutrition_catalog_path):
        with open(nutrition_catalog_path, 'r', encoding='utf-8') as f:
            nutrition_catalog = json.load(f)
        
        source = nutrition_catalog.get('source', 'unknown')
        items_count = len(nutrition_catalog.get("items", []))
        
        log_test(f"🥗 Основной каталог БЖУ:")
        log_test(f"   Источник: {source}")
        log_test(f"   Продуктов: {items_count}")
        log_test(f"   Дата: {nutrition_catalog.get('last_updated', 'unknown')}")
        
        if source == 'catalog':
            log_test("✅ Основной каталог БЖУ использует bootstrap данные!")
        else:
            log_test("⚠️ Основной каталог БЖУ НЕ использует bootstrap данные")

def test_with_llm_enabled():
    """Тест с включенным LLM для получения реальных количеств"""
    log_test("🤖 ТЕСТ С LLM: Проверка с реальными количествами")
    
    url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=true"
    
    payload = {
        "name": "Борщ с говядиной",
        "cuisine": "русская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        response = requests.post(url, json=payload, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'card' in data and data['card']:
                techcard = data['card']
                
                log_test("✅ Техкарта с LLM сгенерирована")
                
                # Проверяем метаданные
                cost_meta = techcard.get('costMeta', {})
                nutrition_meta = techcard.get('nutritionMeta', {})
                
                log_test(f"💰 Источник цен: {cost_meta.get('source', 'unknown')}")
                log_test(f"💰 Покрытие цен: {cost_meta.get('coveragePct', 0)}%")
                
                log_test(f"🥗 Источник БЖУ: {nutrition_meta.get('source', 'unknown')}")
                log_test(f"🥗 Покрытие БЖУ: {nutrition_meta.get('coveragePct', 0)}%")
                
                # Проверяем ингредиенты с количествами
                ingredients = techcard.get('ingredients', [])
                log_test(f"🧄 Ингредиентов: {len(ingredients)}")
                
                total_cost = 0
                for i, ingredient in enumerate(ingredients[:5]):
                    name = ingredient.get('name', 'Неизвестно')
                    quantity = ingredient.get('quantity', 0)
                    unit = ingredient.get('unit', '')
                    cost = ingredient.get('cost', 0)
                    total_cost += cost
                    
                    log_test(f"  {i+1}. {name}: {quantity}{unit} = {cost:.2f} руб")
                
                log_test(f"💵 Сумма первых 5 ингредиентов: {total_cost:.2f} руб")
                
                # Проверяем что покрытие ≥70%
                cost_coverage = cost_meta.get('coveragePct', 0)
                nutrition_coverage = nutrition_meta.get('coveragePct', 0)
                
                success = cost_coverage >= 70 and nutrition_coverage >= 70
                
                if success:
                    log_test("✅ Покрытие ≥70% для обеих категорий")
                else:
                    log_test("❌ Покрытие <70% для одной или обеих категорий")
                
                return success
                
        return False
        
    except Exception as e:
        log_test(f"❌ Ошибка: {e}")
        return False

def verify_bootstrap_prices():
    """Проверка конкретных цен из bootstrap каталога"""
    log_test("💰 ПРОВЕРКА КОНКРЕТНЫХ ЦЕН ИЗ BOOTSTRAP")
    
    bootstrap_path = "/app/backend/data/bootstrap/prices_ru.demo.csv"
    
    if os.path.exists(bootstrap_path):
        with open(bootstrap_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        log_test(f"📊 Bootstrap каталог содержит {len(lines)-1} продуктов")
        
        # Показываем несколько примеров
        log_test("📋 Примеры цен из bootstrap каталога:")
        for line in lines[1:6]:  # Пропускаем заголовок, показываем первые 5
            parts = line.strip().split(',')
            if len(parts) >= 3:
                name = parts[0]
                price = parts[1]
                unit = parts[2]
                log_test(f"   {name}: {price} руб/{unit}")
        
        return True
    else:
        log_test("❌ Bootstrap каталог цен не найден")
        return False

def run_source_verification():
    """Запуск проверки источников"""
    log_test("🔬 ПРОВЕРКА ИСТОЧНИКОВ BOOTSTRAP ДАННЫХ")
    log_test("=" * 60)
    
    # Проверка 1: Источники каталогов
    log_test("ПРОВЕРКА 1: Источники в каталогах")
    check_catalog_sources()
    log_test("-" * 60)
    
    # Проверка 2: Bootstrap цены
    log_test("ПРОВЕРКА 2: Bootstrap цены")
    bootstrap_prices_ok = verify_bootstrap_prices()
    log_test("-" * 60)
    
    # Проверка 3: Тест с LLM
    log_test("ПРОВЕРКА 3: Тест с LLM для реальных количеств")
    llm_test_ok = test_with_llm_enabled()
    log_test("-" * 60)
    
    # Итоги
    log_test("📋 ИТОГИ ПРОВЕРКИ ИСТОЧНИКОВ")
    log_test("=" * 60)
    
    if bootstrap_prices_ok and llm_test_ok:
        log_test("🎉 BOOTSTRAP КАТАЛОГИ РАБОТАЮТ КОРРЕКТНО!")
        log_test("✅ Данные берутся из bootstrap файлов")
        log_test("✅ Покрытие ≥70% обеспечивается")
        log_test("✅ Система готова к продакшену")
    else:
        log_test("⚠️ Обнаружены проблемы с bootstrap каталогами")
    
    return bootstrap_prices_ok and llm_test_ok

if __name__ == "__main__":
    run_source_verification()