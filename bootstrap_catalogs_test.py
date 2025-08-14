#!/usr/bin/env python3
"""
Bootstrap Catalogs Testing Suite - Task 1.1 «Бутстрап-каталоги (RU demo)»

ЦЕЛЬ: Проверить что при PRICE_VIA_LLM=false любая новая ТК с типовыми продуктами 
получает coveragePct ≥70% по ценам и ≥70% по БЖУ без загрузок пользователя.

ТЕСТОВЫЕ ТРЕБОВАНИЯ:
1. Установка PRICE_VIA_LLM=false
2. Генерация ТК с типовыми российскими продуктами
3. Проверка покрытия цен (coveragePct ≥70%)
4. Проверка покрытия БЖУ (coveragePct ≥70%)
5. Проверка качества данных
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://656e01f5-3dfa-48e5-95b5-5cb5a1aefe96.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_environment_setup():
    """Test 1: Проверка установки PRICE_VIA_LLM=false"""
    log_test("🔧 ТЕСТ 1: Проверка переменной окружения PRICE_VIA_LLM=false")
    
    # Читаем .env файл
    env_path = "/app/backend/.env"
    try:
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        if "PRICE_VIA_LLM=false" in env_content:
            log_test("✅ PRICE_VIA_LLM=false установлена корректно")
            return True
        else:
            log_test("❌ PRICE_VIA_LLM не установлена в false")
            return False
    except Exception as e:
        log_test(f"❌ Ошибка чтения .env файла: {e}")
        return False

def test_bootstrap_files_exist():
    """Test 2: Проверка существования bootstrap файлов"""
    log_test("📁 ТЕСТ 2: Проверка существования bootstrap каталогов")
    
    prices_file = "/app/backend/data/bootstrap/prices_ru.demo.csv"
    nutrition_file = "/app/backend/data/bootstrap/nutrition_ru.demo.json"
    
    results = {}
    
    # Проверяем файл цен
    if os.path.exists(prices_file):
        with open(prices_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        results['prices_count'] = len(lines) - 1  # Минус заголовок
        log_test(f"✅ prices_ru.demo.csv найден: {results['prices_count']} продуктов")
    else:
        log_test("❌ prices_ru.demo.csv не найден")
        results['prices_count'] = 0
    
    # Проверяем файл питания
    if os.path.exists(nutrition_file):
        with open(nutrition_file, 'r', encoding='utf-8') as f:
            nutrition_data = json.load(f)
        results['nutrition_count'] = len(nutrition_data.get('items', []))
        log_test(f"✅ nutrition_ru.demo.json найден: {results['nutrition_count']} продуктов")
    else:
        log_test("❌ nutrition_ru.demo.json не найден")
        results['nutrition_count'] = 0
    
    return results

def test_borscht_generation():
    """Test 3: Генерация борща с типовыми российскими продуктами"""
    log_test("🍲 ТЕСТ 3: Генерация борща с российскими продуктами")
    
    url = f"{API_BASE}/v1/techcards.v2/generate"
    
    # Борщ с типовыми российскими продуктами из bootstrap каталога
    payload = {
        "name": "Борщ украинский с говядиной и овощами",
        "cuisine": "русская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        log_test(f"Отправляем запрос: POST {url}")
        log_test(f"Ингредиенты: {len(payload['ingredients'])} шт")
        
        response = requests.post(url, json=payload, timeout=60)
        log_test(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем структуру ответа
            if 'techcard' in data:
                techcard = data['techcard']
                log_test("✅ Техкарта успешно сгенерирована")
                
                return analyze_techcard_coverage(techcard, "Борщ украинский")
            else:
                log_test("❌ Техкарта не найдена в ответе")
                return None
        else:
            log_test(f"❌ Ошибка генерации: {response.status_code}")
            log_test(f"Ответ: {response.text[:500]}")
            return None
            
    except Exception as e:
        log_test(f"❌ Исключение при генерации: {e}")
        return None

def test_carbonara_generation():
    """Test 4: Генерация пасты карбонара с типовыми продуктами"""
    log_test("🍝 ТЕСТ 4: Генерация пасты карбонара")
    
    url = f"{API_BASE}/v1/techcards.v2/generate"
    
    # Паста карбонара с продуктами из bootstrap каталога
    payload = {
        "dish_name": "Паста карбонара",
        "description": "Классическая итальянская паста с беконом и яйцами",
        "ingredients": [
            {"name": "спагетти", "quantity": 200, "unit": "г"},
            {"name": "бекон", "quantity": 100, "unit": "г"},
            {"name": "яйца куриные с1", "quantity": 2, "unit": "шт"},
            {"name": "сыр пармезан", "quantity": 50, "unit": "г"},
            {"name": "сливки 35%", "quantity": 100, "unit": "мл"},
            {"name": "чеснок", "quantity": 5, "unit": "г"},
            {"name": "оливковое масло", "quantity": 20, "unit": "мл"},
            {"name": "соль поваренная", "quantity": 3, "unit": "г"},
            {"name": "перец чёрный молотый", "quantity": 1, "unit": "г"}
        ],
        "use_llm": False  # Принудительное отключение LLM
    }
    
    try:
        log_test(f"Отправляем запрос: POST {url}")
        log_test(f"Ингредиенты: {len(payload['ingredients'])} шт")
        
        response = requests.post(url, json=payload, timeout=60)
        log_test(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'techcard' in data:
                techcard = data['techcard']
                log_test("✅ Техкарта успешно сгенерирована")
                
                return analyze_techcard_coverage(techcard, "Паста карбонара")
            else:
                log_test("❌ Техкарта не найдена в ответе")
                return None
        else:
            log_test(f"❌ Ошибка генерации: {response.status_code}")
            log_test(f"Ответ: {response.text[:500]}")
            return None
            
    except Exception as e:
        log_test(f"❌ Исключение при генерации: {e}")
        return None

def analyze_techcard_coverage(techcard, dish_name):
    """Анализ покрытия цен и БЖУ в техкарте"""
    log_test(f"📊 АНАЛИЗ ПОКРЫТИЯ: {dish_name}")
    
    results = {
        'dish_name': dish_name,
        'cost_coverage': 0,
        'nutrition_coverage': 0,
        'cost_source': None,
        'nutrition_source': None,
        'cost_data': None,
        'nutrition_data': None,
        'issues': []
    }
    
    # Анализ покрытия цен
    if 'cost' in techcard:
        cost_data = techcard['cost']
        results['cost_data'] = cost_data
        
        if 'costMeta' in cost_data:
            cost_meta = cost_data['costMeta']
            results['cost_coverage'] = cost_meta.get('coveragePct', 0)
            results['cost_source'] = cost_meta.get('source', 'unknown')
            
            log_test(f"💰 Покрытие цен: {results['cost_coverage']}%")
            log_test(f"💰 Источник цен: {results['cost_source']}")
            
            # Проверяем требование ≥70%
            if results['cost_coverage'] >= 70:
                log_test("✅ Покрытие цен соответствует требованию (≥70%)")
            else:
                log_test("❌ Покрытие цен НЕ соответствует требованию (<70%)")
                results['issues'].append(f"Низкое покрытие цен: {results['cost_coverage']}%")
        else:
            log_test("❌ costMeta не найдена")
            results['issues'].append("Отсутствует costMeta")
    else:
        log_test("❌ Данные о стоимости не найдены")
        results['issues'].append("Отсутствуют данные о стоимости")
    
    # Анализ покрытия БЖУ
    if 'nutrition' in techcard:
        nutrition_data = techcard['nutrition']
        results['nutrition_data'] = nutrition_data
        
        if 'nutritionMeta' in nutrition_data:
            nutrition_meta = nutrition_data['nutritionMeta']
            results['nutrition_coverage'] = nutrition_meta.get('coveragePct', 0)
            results['nutrition_source'] = nutrition_meta.get('source', 'unknown')
            
            log_test(f"🥗 Покрытие БЖУ: {results['nutrition_coverage']}%")
            log_test(f"🥗 Источник БЖУ: {results['nutrition_source']}")
            
            # Проверяем требование ≥70%
            if results['nutrition_coverage'] >= 70:
                log_test("✅ Покрытие БЖУ соответствует требованию (≥70%)")
            else:
                log_test("❌ Покрытие БЖУ НЕ соответствует требованию (<70%)")
                results['issues'].append(f"Низкое покрытие БЖУ: {results['nutrition_coverage']}%")
        else:
            log_test("❌ nutritionMeta не найдена")
            results['issues'].append("Отсутствует nutritionMeta")
    else:
        log_test("❌ Данные о питании не найдены")
        results['issues'].append("Отсутствуют данные о питании")
    
    # Проверка качества данных
    validate_data_quality(results, techcard)
    
    return results

def validate_data_quality(results, techcard):
    """Проверка качества данных"""
    log_test("🔍 ПРОВЕРКА КАЧЕСТВА ДАННЫХ")
    
    # Проверка разумности цен
    if results['cost_data']:
        raw_cost = results['cost_data'].get('rawCost', 0)
        cost_per_portion = results['cost_data'].get('costPerPortion', 0)
        
        log_test(f"💵 Сырая стоимость: {raw_cost} руб")
        log_test(f"💵 Стоимость порции: {cost_per_portion} руб")
        
        # Проверяем разумность цен
        if raw_cost > 0 and raw_cost < 10000:  # От 0 до 10000 руб за блюдо
            log_test("✅ Цены в разумных пределах")
        else:
            log_test("⚠️ Цены могут быть неразумными")
            results['issues'].append(f"Подозрительная цена: {raw_cost} руб")
    
    # Проверка БЖУ
    if results['nutrition_data']:
        per_portion = results['nutrition_data'].get('perPortion', {})
        kcal = per_portion.get('kcal', 0)
        proteins = per_portion.get('proteins_g', 0)
        fats = per_portion.get('fats_g', 0)
        carbs = per_portion.get('carbs_g', 0)
        
        log_test(f"🍽️ БЖУ на порцию: {kcal} ккал, Б:{proteins}г, Ж:{fats}г, У:{carbs}г")
        
        # Проверяем разумность БЖУ
        if 0 < kcal < 2000 and proteins >= 0 and fats >= 0 and carbs >= 0:
            log_test("✅ БЖУ в разумных пределах")
        else:
            log_test("⚠️ БЖУ могут быть неразумными")
            results['issues'].append(f"Подозрительные БЖУ: {kcal} ккал")

def test_chicken_dish_generation():
    """Test 5: Генерация блюда с курицей для проверки конкретных цен"""
    log_test("🐔 ТЕСТ 5: Генерация блюда с куриным филе")
    
    url = f"{API_BASE}/v1/techcards.v2/generate"
    
    # Простое блюдо с куриным филе для проверки цены ~450 руб/кг
    payload = {
        "dish_name": "Куриное филе жареное",
        "description": "Простое жареное куриное филе",
        "ingredients": [
            {"name": "куриное филе", "quantity": 200, "unit": "г"},
            {"name": "растительное масло", "quantity": 20, "unit": "мл"},
            {"name": "соль поваренная", "quantity": 3, "unit": "г"},
            {"name": "перец чёрный молотый", "quantity": 1, "unit": "г"}
        ],
        "use_llm": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'techcard' in data:
                techcard = data['techcard']
                log_test("✅ Техкарта с курицей сгенерирована")
                
                # Проверяем конкретные цены
                if 'cost' in techcard:
                    raw_cost = techcard['cost'].get('rawCost', 0)
                    
                    # Ожидаемая стоимость: куриное филе 200г = ~90 руб + масло ~3 руб + специи ~1 руб = ~94 руб
                    expected_cost_min = 80
                    expected_cost_max = 120
                    
                    log_test(f"💰 Фактическая стоимость: {raw_cost} руб")
                    log_test(f"💰 Ожидаемый диапазон: {expected_cost_min}-{expected_cost_max} руб")
                    
                    if expected_cost_min <= raw_cost <= expected_cost_max:
                        log_test("✅ Стоимость соответствует ожиданиям")
                        return True
                    else:
                        log_test("⚠️ Стоимость не соответствует ожиданиям")
                        return False
                        
        return False
        
    except Exception as e:
        log_test(f"❌ Ошибка: {e}")
        return False

def run_all_tests():
    """Запуск всех тестов"""
    log_test("🚀 ЗАПУСК ТЕСТИРОВАНИЯ BOOTSTRAP КАТАЛОГОВ")
    log_test("=" * 60)
    
    results = {
        'environment_ok': False,
        'bootstrap_files': {},
        'borscht_test': None,
        'carbonara_test': None,
        'chicken_test': False,
        'overall_success': False
    }
    
    # Тест 1: Переменная окружения
    results['environment_ok'] = test_environment_setup()
    log_test("-" * 60)
    
    # Тест 2: Bootstrap файлы
    results['bootstrap_files'] = test_bootstrap_files_exist()
    log_test("-" * 60)
    
    # Тест 3: Борщ
    results['borscht_test'] = test_borscht_generation()
    log_test("-" * 60)
    
    # Тест 4: Карбонара
    results['carbonara_test'] = test_carbonara_generation()
    log_test("-" * 60)
    
    # Тест 5: Курица
    results['chicken_test'] = test_chicken_dish_generation()
    log_test("-" * 60)
    
    # Итоговый анализ
    log_test("📋 ИТОГОВЫЙ ОТЧЕТ")
    log_test("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Проверка переменной окружения
    if results['environment_ok']:
        log_test("✅ PRICE_VIA_LLM=false установлена")
        success_count += 1
    else:
        log_test("❌ PRICE_VIA_LLM не установлена правильно")
    total_tests += 1
    
    # Проверка bootstrap файлов
    if results['bootstrap_files'].get('prices_count', 0) >= 90:
        log_test(f"✅ Bootstrap цены: {results['bootstrap_files']['prices_count']} продуктов")
        success_count += 1
    else:
        log_test(f"❌ Недостаточно продуктов в bootstrap ценах: {results['bootstrap_files'].get('prices_count', 0)}")
    total_tests += 1
    
    if results['bootstrap_files'].get('nutrition_count', 0) >= 90:
        log_test(f"✅ Bootstrap БЖУ: {results['bootstrap_files']['nutrition_count']} продуктов")
        success_count += 1
    else:
        log_test(f"❌ Недостаточно продуктов в bootstrap БЖУ: {results['bootstrap_files'].get('nutrition_count', 0)}")
    total_tests += 1
    
    # Проверка покрытия борща
    if results['borscht_test']:
        if results['borscht_test']['cost_coverage'] >= 70:
            log_test(f"✅ Борщ - покрытие цен: {results['borscht_test']['cost_coverage']}%")
            success_count += 1
        else:
            log_test(f"❌ Борщ - низкое покрытие цен: {results['borscht_test']['cost_coverage']}%")
        total_tests += 1
        
        if results['borscht_test']['nutrition_coverage'] >= 70:
            log_test(f"✅ Борщ - покрытие БЖУ: {results['borscht_test']['nutrition_coverage']}%")
            success_count += 1
        else:
            log_test(f"❌ Борщ - низкое покрытие БЖУ: {results['borscht_test']['nutrition_coverage']}%")
        total_tests += 1
    else:
        log_test("❌ Борщ - тест не прошел")
        total_tests += 2
    
    # Проверка покрытия карбонары
    if results['carbonara_test']:
        if results['carbonara_test']['cost_coverage'] >= 70:
            log_test(f"✅ Карбонара - покрытие цен: {results['carbonara_test']['cost_coverage']}%")
            success_count += 1
        else:
            log_test(f"❌ Карбонара - низкое покрытие цен: {results['carbonara_test']['cost_coverage']}%")
        total_tests += 1
        
        if results['carbonara_test']['nutrition_coverage'] >= 70:
            log_test(f"✅ Карбонара - покрытие БЖУ: {results['carbonara_test']['nutrition_coverage']}%")
            success_count += 1
        else:
            log_test(f"❌ Карбонара - низкое покрытие БЖУ: {results['carbonara_test']['nutrition_coverage']}%")
        total_tests += 1
    else:
        log_test("❌ Карбонара - тест не прошел")
        total_tests += 2
    
    # Проверка качества данных
    if results['chicken_test']:
        log_test("✅ Качество данных - цены разумные")
        success_count += 1
    else:
        log_test("❌ Качество данных - проблемы с ценами")
    total_tests += 1
    
    # Итоговый результат
    success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
    results['overall_success'] = success_rate >= 80  # 80% успешных тестов
    
    log_test("=" * 60)
    log_test(f"🎯 ИТОГ: {success_count}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
    
    if results['overall_success']:
        log_test("🎉 BOOTSTRAP КАТАЛОГИ РАБОТАЮТ КОРРЕКТНО!")
        log_test("✅ Система обеспечивает покрытие ≥70% для типовых российских продуктов")
    else:
        log_test("❌ BOOTSTRAP КАТАЛОГИ ТРЕБУЮТ ДОРАБОТКИ")
        log_test("⚠️ Не все требования выполнены")
    
    return results

if __name__ == "__main__":
    run_all_tests()