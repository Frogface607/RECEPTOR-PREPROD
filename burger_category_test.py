#!/usr/bin/env python3
"""
🍔 BURGER CATEGORY TESTING - Edison Craft Bar
Testing GET /api/iiko/category/{org_id}/бургеры and alternatives
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_burger_categories():
    """🍔 Test getting all burgers from Edison Craft Bar - SIMPLE LIST"""
    print("🍔 TESTING BURGER CATEGORIES - EDISON CRAFT BAR")
    print("=" * 60)
    print("🎯 ЦЕЛЬ: Получить простой список всех бургеров для пользователя")
    print("📍 Организация: Edison Craft Bar (default-org-001)")
    print()
    
    # Edison Craft Bar organization ID from previous tests
    org_id_edison = "default-org-001"
    
    # Alternative search terms as requested
    search_terms = ["бургеры", "бургер", "burger", "сандвич", "гамбургер"]
    
    burgers_found = []
    successful_category = None
    
    for i, category_name in enumerate(search_terms, 1):
        print(f"🔍 Test {i}: GET /api/iiko/category/{org_id_edison}/{category_name}")
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{BACKEND_URL}/iiko/category/{org_id_edison}/{category_name}",
                timeout=30
            )
            end_time = time.time()
            
            print(f"Response time: {end_time - start_time:.2f} seconds")
            print(f"HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # Check if we found items
                items = result.get("items", [])
                category_info = result.get("category", {})
                
                if items:
                    log_test(f"CATEGORY '{category_name}' - SUCCESS", "PASS", 
                            f"Найдено {len(items)} позиций в категории '{category_name}'")
                    
                    burgers_found.extend(items)
                    successful_category = category_name
                    
                    # Log category details
                    if category_info:
                        cat_name = category_info.get("name", "N/A")
                        cat_id = category_info.get("id", "N/A")
                        print(f"    📂 Категория: {cat_name} (ID: {cat_id})")
                    
                    # Show sample items
                    print(f"    🍔 Найденные позиции:")
                    for j, item in enumerate(items[:10], 1):  # Show first 10
                        name = item.get("name", "N/A")
                        price = item.get("price", 0)
                        description = item.get("description", "")
                        
                        print(f"    {j}. {name}")
                        if price > 0:
                            print(f"       Цена: {price}₽")
                        if description:
                            print(f"       Описание: {description[:100]}...")
                        print()
                    
                    # If we found items, we can stop searching
                    break
                else:
                    log_test(f"CATEGORY '{category_name}' - EMPTY", "WARN", 
                            f"Категория '{category_name}' найдена, но пуста")
                    
            elif response.status_code == 404:
                log_test(f"CATEGORY '{category_name}' - NOT FOUND", "WARN", 
                        f"Категория '{category_name}' не найдена")
                print(f"    Response: {response.text}")
                
            elif response.status_code == 500:
                log_test(f"CATEGORY '{category_name}' - ERROR", "FAIL", 
                        f"Ошибка сервера при поиске '{category_name}': {response.text}")
                
            else:
                log_test(f"CATEGORY '{category_name}' - UNEXPECTED", "FAIL", 
                        f"Неожиданный HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            log_test(f"CATEGORY '{category_name}' - TIMEOUT", "FAIL", 
                    f"Таймаут при поиске '{category_name}' (>30s)")
        except Exception as e:
            log_test(f"CATEGORY '{category_name}' - EXCEPTION", "FAIL", 
                    f"Исключение при поиске '{category_name}': {str(e)}")
        
        print()  # Add spacing between tests
    
    # Final results summary
    print("🎯 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print("=" * 60)
    
    if burgers_found:
        log_test("🎉 БУРГЕРЫ НАЙДЕНЫ!", "PASS", 
                f"Успешно найдено {len(burgers_found)} бургеров в категории '{successful_category}'")
        
        # Create simple text list as requested
        print("📋 ПРОСТОЙ СПИСОК ВСЕХ БУРГЕРОВ:")
        print("-" * 40)
        
        for i, burger in enumerate(burgers_found, 1):
            name = burger.get("name", "Без названия")
            price = burger.get("price", 0)
            
            if price > 0:
                print(f"{i}. {name} - {price}₽")
            else:
                print(f"{i}. {name}")
        
        print("-" * 40)
        print(f"Всего найдено: {len(burgers_found)} бургеров")
        print(f"Успешная категория: '{successful_category}'")
        print(f"Организация: Edison Craft Bar ({org_id_edison})")
        
        # Additional analysis
        if len(burgers_found) > 0:
            prices = [item.get("price", 0) for item in burgers_found if item.get("price", 0) > 0]
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                
                print(f"\n💰 АНАЛИЗ ЦЕН:")
                print(f"Средняя цена: {avg_price:.0f}₽")
                print(f"Минимальная цена: {min_price}₽")
                print(f"Максимальная цена: {max_price}₽")
        
        return True
    else:
        log_test("❌ БУРГЕРЫ НЕ НАЙДЕНЫ", "FAIL", 
                f"Ни одна из категорий {search_terms} не содержит бургеров")
        
        print("🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("- Бургеры могут быть в другой категории с неожиданным названием")
        print("- Меню Edison Craft Bar может не содержать бургеров")
        print("- Категории могут иметь другие названия (например, 'Основные блюда', 'Горячее')")
        print()
        print("💡 РЕКОМЕНДАЦИИ:")
        print("- Проверить полный список категорий через GET /api/iiko/menu/{org_id}")
        print("- Поискать в категориях 'Основные блюда', 'Горячее', 'Мясные блюда'")
        print("- Проверить, что Edison Craft Bar действительно подает бургеры")
        
        return False

def test_menu_overview():
    """📋 Get menu overview to understand available categories"""
    print("📋 TESTING MENU OVERVIEW - ПОНИМАНИЕ СТРУКТУРЫ МЕНЮ")
    print("=" * 60)
    
    org_id_edison = "default-org-001"
    
    print(f"🔍 Test: GET /api/iiko/menu/{org_id_edison} - Обзор всего меню")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/iiko/menu/{org_id_edison}",
            timeout=60
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            categories = result.get("categories", [])
            items = result.get("items", [])
            
            log_test("MENU OVERVIEW - SUCCESS", "PASS", 
                    f"Получено {len(categories)} категорий, {len(items)} позиций")
            
            # Show all categories to help find burgers
            print(f"📂 ВСЕ ДОСТУПНЫЕ КАТЕГОРИИ ({len(categories)}):")
            print("-" * 50)
            
            for i, category in enumerate(categories, 1):
                cat_name = category.get("name", "Без названия")
                cat_id = category.get("id", "N/A")
                
                # Count items in this category
                items_in_category = [item for item in items if item.get("category_id") == cat_id]
                items_count = len(items_in_category)
                
                print(f"{i}. {cat_name} ({items_count} позиций)")
                
                # Check if category name might contain burgers
                burger_keywords = ["бургер", "burger", "сандвич", "гамбургер", "мясн", "горяч", "основн"]
                if any(keyword in cat_name.lower() for keyword in burger_keywords):
                    print(f"   🍔 ПОТЕНЦИАЛЬНАЯ КАТЕГОРИЯ ДЛЯ БУРГЕРОВ!")
                    
                    # Show some items from this category
                    if items_in_category:
                        print(f"   Примеры позиций:")
                        for j, item in enumerate(items_in_category[:3], 1):
                            item_name = item.get("name", "N/A")
                            print(f"   {j}. {item_name}")
            
            print("-" * 50)
            
            # Look for burger-like items across all categories
            print(f"\n🔍 ПОИСК БУРГЕРОВ ПО ВСЕМУ МЕНЮ:")
            print("-" * 50)
            
            burger_keywords = ["бургер", "burger", "гамбургер", "чизбургер", "биг", "мак"]
            potential_burgers = []
            
            for item in items:
                item_name = item.get("name", "").lower()
                if any(keyword in item_name for keyword in burger_keywords):
                    potential_burgers.append(item)
            
            if potential_burgers:
                print(f"🎉 НАЙДЕНО {len(potential_burgers)} ПОТЕНЦИАЛЬНЫХ БУРГЕРОВ:")
                for i, burger in enumerate(potential_burgers, 1):
                    name = burger.get("name", "N/A")
                    price = burger.get("price", 0)
                    category_id = burger.get("category_id", "")
                    
                    # Find category name
                    category_name = "Неизвестная категория"
                    for cat in categories:
                        if cat.get("id") == category_id:
                            category_name = cat.get("name", "Неизвестная категория")
                            break
                    
                    print(f"{i}. {name}")
                    if price > 0:
                        print(f"   Цена: {price}₽")
                    print(f"   Категория: {category_name}")
                    print()
            else:
                print("❌ Бургеры не найдены по ключевым словам в названиях позиций")
            
            print("-" * 50)
            
            return categories, items
            
        elif response.status_code == 404:
            log_test("MENU OVERVIEW", "FAIL", 
                    f"Организация {org_id_edison} не найдена")
        elif response.status_code == 500:
            log_test("MENU OVERVIEW", "FAIL", 
                    f"Ошибка сервера: {response.text}")
        else:
            log_test("MENU OVERVIEW", "FAIL", 
                    f"Неожиданный HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("MENU OVERVIEW", "FAIL", "Таймаут (>60s)")
    except Exception as e:
        log_test("MENU OVERVIEW", "FAIL", f"Исключение: {str(e)}")
    
    return [], []

def main():
    """🍔 Run burger category testing for Edison Craft Bar"""
    print("🍔 BURGER CATEGORY TESTING - EDISON CRAFT BAR")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🎯 ЗАДАЧА: Получить все бургеры из Edison Craft Bar простым списком")
    print("📋 ПЛАН ТЕСТИРОВАНИЯ:")
    print("1. Попробовать GET /api/iiko/category/{org_id}/бургеры")
    print("2. Если не найдено, попробовать альтернативы: бургер, burger, сандвич, гамбургер")
    print("3. Получить обзор меню для понимания структуры категорий")
    print("4. Выдать простой текстовый список найденных бургеров")
    print()
    
    try:
        # Step 1: Try to find burgers directly
        burgers_found = test_burger_categories()
        
        print("\n" + "="*60 + "\n")
        
        # Step 2: Get menu overview for better understanding
        categories, items = test_menu_overview()
        
        print("\n" + "="*60 + "\n")
        
        # Final summary
        print("🏁 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        print("=" * 80)
        
        if burgers_found:
            print("✅ УСПЕХ! Бургеры найдены и выведены списком выше")
            print("🎉 Пользователь получил запрошенный простой список бургеров")
        else:
            print("❌ Бургеры не найдены в стандартных категориях")
            print("💡 Рекомендуется проверить категории, отмеченные как потенциальные выше")
            
            if categories:
                print(f"📊 Доступно {len(categories)} категорий для дальнейшего поиска")
                print("🔍 Проверьте категории с ключевыми словами: мясн, горяч, основн")
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()