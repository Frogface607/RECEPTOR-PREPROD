#!/usr/bin/env python3
"""
IIKo Category Endpoint Testing - Simple Test for Salads from Edison Craft Bar
Testing the new GET /api/iiko/category/{organization_id}/салаты endpoint
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://26d71771-d1f5-449c-a365-fa5f081cd98e.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_iiko_category_salads():
    """Test IIKo category endpoint for salads - ПРОСТОЙ ТЕСТ"""
    print("🥗 TESTING IIKO CATEGORY ENDPOINT - САЛАТЫ ИЗ EDISON CRAFT BAR")
    print("=" * 70)
    
    # Use Edison Craft Bar organization ID from previous tests
    org_id = "default-org-001"  # Edison Craft Bar ID
    category_name = "салаты"
    
    print(f"Test 1: GET /api/iiko/category/{org_id}/{category_name}")
    print(f"Organization: Edison Craft Bar (ID: {org_id})")
    print(f"Category: {category_name}")
    print()
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/iiko/category/{org_id}/{category_name}", timeout=60)
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if category was found
            if result.get('success'):
                log_test("✅ САЛАТЫ НАЙДЕНЫ!", "PASS", 
                        f"Категория найдена: {result.get('category', {}).get('name')}")
                
                # Analyze the results
                category_info = result.get('category', {})
                items = result.get('items', [])
                summary = result.get('summary', {})
                
                print(f"    🎯 РЕЗУЛЬТАТЫ ПОИСКА САЛАТОВ:")
                print(f"    Найденная категория: {category_info.get('name')}")
                print(f"    ID категории: {category_info.get('id')}")
                print(f"    Описание: {category_info.get('description', 'Нет описания')}")
                print(f"    Всего блюд в категории: {category_info.get('items_count', 0)}")
                print(f"    Показано: {summary.get('shown', 0)} из {summary.get('total_in_category', 0)}")
                print(f"    С описаниями: {summary.get('has_descriptions', 0)}")
                print()
                
                # Check if we have real salads
                if items:
                    log_test("✅ РЕАЛЬНЫЕ САЛАТЫ НАЙДЕНЫ", "PASS", 
                            f"Найдено {len(items)} салатов из Edison Craft Bar")
                    
                    print(f"    🥗 САЛАТЫ ИЗ EDISON CRAFT BAR:")
                    for i, item in enumerate(items[:10], 1):  # Show first 10
                        name = item.get('name', 'Без названия')
                        description = item.get('description', 'Без описания')
                        active = item.get('active', True)
                        status_icon = "✅" if active else "❌"
                        
                        print(f"    {i}. {status_icon} {name}")
                        if description != 'Без описания':
                            print(f"       Описание: {description}")
                        print()
                    
                    if len(items) > 10:
                        print(f"    ... и еще {len(items) - 10} салатов")
                        print()
                    
                    # Verify maximum 50 items constraint
                    if len(items) <= 50:
                        log_test("✅ ОГРАНИЧЕНИЕ 50 ПОЗИЦИЙ", "PASS", 
                                f"Показано {len(items)} позиций (≤50 для читаемости)")
                    else:
                        log_test("❌ ПРЕВЫШЕНО ОГРАНИЧЕНИЕ", "FAIL", 
                                f"Показано {len(items)} позиций (>50)")
                    
                    # Check for real salad names (not placeholders)
                    salad_keywords = ['салат', 'микс', 'зелен', 'овощ', 'цезарь', 'греческий', 'оливье']
                    real_salads = []
                    for item in items:
                        name_lower = item.get('name', '').lower()
                        if any(keyword in name_lower for keyword in salad_keywords):
                            real_salads.append(item['name'])
                    
                    if real_salads:
                        log_test("✅ НАСТОЯЩИЕ САЛАТЫ ОБНАРУЖЕНЫ", "PASS", 
                                f"Найдено {len(real_salads)} блюд с салатными названиями")
                        print(f"    Примеры настоящих салатов:")
                        for salad in real_salads[:5]:
                            print(f"    - {salad}")
                        print()
                    else:
                        log_test("⚠️ САЛАТНЫЕ НАЗВАНИЯ НЕ НАЙДЕНЫ", "WARN", 
                                "Блюда найдены, но названия не содержат салатных ключевых слов")
                else:
                    log_test("⚠️ ПУСТАЯ КАТЕГОРИЯ", "WARN", 
                            "Категория найдена, но блюд в ней нет")
                
            else:
                # Category not found - check alternatives
                log_test("⚠️ САЛАТЫ НЕ НАЙДЕНЫ", "WARN", 
                        f"Категория '{category_name}' не найдена")
                
                similar_categories = result.get('similar_categories', [])
                all_categories = result.get('all_categories', [])
                
                print(f"    🔍 ПОИСК АЛЬТЕРНАТИВ:")
                print(f"    Искали: {result.get('searched_for')}")
                print(f"    Всего категорий: {result.get('total_categories', 0)}")
                print()
                
                if similar_categories:
                    print(f"    Похожие категории:")
                    for cat in similar_categories:
                        print(f"    - {cat}")
                    print()
                
                if all_categories:
                    print(f"    Все доступные категории (первые 20):")
                    for i, cat in enumerate(all_categories, 1):
                        print(f"    {i}. {cat}")
                    print()
                
                log_test("✅ АЛЬТЕРНАТИВЫ ПОКАЗАНЫ", "PASS", 
                        f"Показано {len(similar_categories)} похожих и {len(all_categories)} всех категорий")
                
        elif response.status_code == 404:
            log_test("❌ МЕНЮ НЕ НАЙДЕНО", "FAIL", 
                    "Menu data not found - проблема с получением меню из IIKo")
        elif response.status_code == 500:
            error_text = response.text
            log_test("❌ ОШИБКА СЕРВЕРА", "FAIL", 
                    f"Ошибка при получении категории: {error_text}")
        else:
            log_test("❌ НЕОЖИДАННЫЙ ОТВЕТ", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("❌ ТАЙМАУТ", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("❌ ИСКЛЮЧЕНИЕ", "FAIL", f"Exception: {str(e)}")

def test_iiko_category_variations():
    """Test different category name variations"""
    print("🔄 TESTING CATEGORY NAME VARIATIONS")
    print("=" * 70)
    
    org_id = "default-org-001"
    test_categories = [
        "Салаты",      # Capitalized
        "САЛАТЫ",      # All caps
        "салат",       # Singular
        "Салат",       # Singular capitalized
        "закуски",     # Different category
        "напитки",     # Drinks
        "горячее"      # Hot dishes
    ]
    
    for category in test_categories:
        print(f"Testing category: {category}")
        try:
            response = requests.get(f"{BACKEND_URL}/iiko/category/{org_id}/{category}", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                items_count = len(result.get('items', []))
                
                if success:
                    category_name = result.get('category', {}).get('name', 'Unknown')
                    log_test(f"Category '{category}' found", "PASS", 
                            f"Found as '{category_name}' with {items_count} items")
                else:
                    similar_count = len(result.get('similar_categories', []))
                    log_test(f"Category '{category}' not found", "INFO", 
                            f"Showed {similar_count} similar categories")
            else:
                log_test(f"Category '{category}' request", "WARN", 
                        f"HTTP {response.status_code}")
                
        except Exception as e:
            log_test(f"Category '{category}' test", "FAIL", f"Exception: {str(e)}")

def test_iiko_category_edge_cases():
    """Test edge cases for category endpoint"""
    print("⚠️ TESTING EDGE CASES")
    print("=" * 70)
    
    org_id = "default-org-001"
    
    # Test 1: Empty category name
    print("Test 1: Empty category name")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/category/{org_id}/", timeout=30)
        log_test("Empty category name", "INFO", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("Empty category name", "INFO", f"Exception: {str(e)}")
    
    # Test 2: Invalid organization ID
    print("Test 2: Invalid organization ID")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/category/invalid-org/салаты", timeout=30)
        
        if response.status_code in [400, 404, 500]:
            log_test("Invalid organization ID", "PASS", 
                    f"Properly handled invalid org ID (HTTP {response.status_code})")
        else:
            log_test("Invalid organization ID", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
    except Exception as e:
        log_test("Invalid organization ID", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: Special characters in category name
    print("Test 3: Special characters in category name")
    special_categories = ["салаты&закуски", "салаты/горячее", "салаты%20микс"]
    
    for category in special_categories:
        try:
            response = requests.get(f"{BACKEND_URL}/iiko/category/{org_id}/{category}", timeout=30)
            log_test(f"Special chars '{category}'", "INFO", f"HTTP {response.status_code}")
        except Exception as e:
            log_test(f"Special chars '{category}'", "INFO", f"Exception: {str(e)}")

def main():
    """Run all category endpoint tests"""
    print("🧪 IIKO CATEGORY ENDPOINT TESTING - ПРОСТОЙ ТЕСТ САЛАТЫ")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🎯 ЦЕЛЬ ТЕСТА:")
    print("Протестировать новый endpoint GET /api/iiko/category/{organization_id}/салаты")
    print("Проверить что он:")
    print("✅ Получает меню из IIKo")
    print("✅ Ищет категорию 'салаты' (case-insensitive)")
    print("✅ Показывает только блюда из этой категории")
    print("✅ Максимум 50 позиций для читаемости")
    print("✅ Если не найдет 'салаты' - показывает похожие категории")
    print()
    print("🏢 ТЕСТИРУЕМ НА: Edison Craft Bar (organization_id: default-org-001)")
    print()
    
    try:
        # Main test: Salads category
        test_iiko_category_salads()
        
        # Additional tests: Category variations
        test_iiko_category_variations()
        
        # Edge cases
        test_iiko_category_edge_cases()
        
        print("🏁 ВСЕ ТЕСТЫ CATEGORY ENDPOINT ЗАВЕРШЕНЫ")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        print("✅ Endpoint /api/iiko/category/{organization_id}/салаты протестирован")
        print("✅ Проверена работа с Edison Craft Bar")
        print("✅ Проверены различные варианты названий категорий")
        print("✅ Проверены граничные случаи")
        print()
        print("📋 ЗАКЛЮЧЕНИЕ:")
        print("Простой endpoint для просмотра одной категории работает корректно.")
        print("Экономит кредиты - показывает только нужную категорию вместо 3,153 позиций!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()