#!/usr/bin/env python3
"""
КРИТИЧНЫЙ ТЕСТ: Venue Profile Modal - Backend Endpoints
Тестирование backend endpoints для модального окна "ПРОФИЛЬ ЗАВЕДЕНИЯ"
Проверка что кнопка ДАЛЕЕ должна активироваться при получении данных
"""

import requests
import json
import time
from datetime import datetime

# Configuration - используем URL из frontend/.env
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_venue_types_endpoint():
    """Тест 1: GET /api/venue-types - должен вернуть типы заведений"""
    print("🏢 ТЕСТ 1: GET /api/venue-types")
    print("-" * 50)
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/venue-types", timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Время ответа: {response_time:.2f} секунд")
        print(f"📊 Статус код: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ КРИТИЧНАЯ ОШИБКА: venue-types endpoint вернул {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return False
        
        venue_types = response.json()
        print(f"📋 Получено типов заведений: {len(venue_types)}")
        
        # Проверяем что данные не пустые
        if not venue_types:
            print("❌ КРИТИЧНАЯ ОШИБКА: venue-types вернул пустые данные")
            return False
        
        # Проверяем структуру данных
        print("🔍 Проверка структуры данных...")
        for venue_key, venue_data in venue_types.items():
            required_fields = ["name", "description", "price_multiplier", "complexity_level"]
            for field in required_fields:
                if field not in venue_data:
                    print(f"❌ ОШИБКА: Отсутствует поле '{field}' в типе заведения '{venue_key}'")
                    return False
        
        # Выводим примеры типов заведений
        print("✅ Примеры типов заведений:")
        count = 0
        for venue_key, venue_data in venue_types.items():
            if count < 3:  # Показываем первые 3
                print(f"   • {venue_key}: {venue_data['name']} - {venue_data['description'][:50]}...")
                count += 1
        
        print(f"✅ ТЕСТ 1 ПРОЙДЕН: venue-types endpoint работает корректно")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ КРИТИЧНАЯ ОШИБКА: Таймаут при запросе venue-types")
        return False
    except Exception as e:
        print(f"❌ КРИТИЧНАЯ ОШИБКА: {str(e)}")
        return False

def test_cuisine_types_endpoint():
    """Тест 2: GET /api/cuisine-types - должен вернуть типы кухонь"""
    print("\n🍽️  ТЕСТ 2: GET /api/cuisine-types")
    print("-" * 50)
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/cuisine-types", timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Время ответа: {response_time:.2f} секунд")
        print(f"📊 Статус код: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ КРИТИЧНАЯ ОШИБКА: cuisine-types endpoint вернул {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return False
        
        cuisine_types = response.json()
        print(f"🍜 Получено типов кухонь: {len(cuisine_types)}")
        
        # Проверяем что данные не пустые
        if not cuisine_types:
            print("❌ КРИТИЧНАЯ ОШИБКА: cuisine-types вернул пустые данные")
            return False
        
        # Проверяем структуру данных
        print("🔍 Проверка структуры данных...")
        for cuisine_key, cuisine_data in cuisine_types.items():
            required_fields = ["name", "subcategories", "key_ingredients", "cooking_methods"]
            for field in required_fields:
                if field not in cuisine_data:
                    print(f"❌ ОШИБКА: Отсутствует поле '{field}' в типе кухни '{cuisine_key}'")
                    return False
        
        # Выводим примеры типов кухонь
        print("✅ Примеры типов кухонь:")
        count = 0
        for cuisine_key, cuisine_data in cuisine_types.items():
            if count < 3:  # Показываем первые 3
                print(f"   • {cuisine_key}: {cuisine_data['name']} - ингредиенты: {', '.join(cuisine_data['key_ingredients'][:3])}...")
                count += 1
        
        print(f"✅ ТЕСТ 2 ПРОЙДЕН: cuisine-types endpoint работает корректно")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ КРИТИЧНАЯ ОШИБКА: Таймаут при запросе cuisine-types")
        return False
    except Exception as e:
        print(f"❌ КРИТИЧНАЯ ОШИБКА: {str(e)}")
        return False

def test_average_check_categories_endpoint():
    """Тест 3: GET /api/average-check-categories - должен вернуть категории среднего чека"""
    print("\n💰 ТЕСТ 3: GET /api/average-check-categories")
    print("-" * 50)
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/average-check-categories", timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Время ответа: {response_time:.2f} секунд")
        print(f"📊 Статус код: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ КРИТИЧНАЯ ОШИБКА: average-check-categories endpoint вернул {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return False
        
        check_categories = response.json()
        print(f"💵 Получено категорий среднего чека: {len(check_categories)}")
        
        # Проверяем что данные не пустые
        if not check_categories:
            print("❌ КРИТИЧНАЯ ОШИБКА: average-check-categories вернул пустые данные")
            return False
        
        # Проверяем структуру данных
        print("🔍 Проверка структуры данных...")
        for category_key, category_data in check_categories.items():
            required_fields = ["name", "range", "description", "ingredient_quality"]
            for field in required_fields:
                if field not in category_data:
                    print(f"❌ ОШИБКА: Отсутствует поле '{field}' в категории чека '{category_key}'")
                    return False
        
        # Выводим примеры категорий
        print("✅ Примеры категорий среднего чека:")
        for category_key, category_data in check_categories.items():
            range_str = f"{category_data['range'][0]}-{category_data['range'][1]}₽"
            print(f"   • {category_key}: {category_data['name']} ({range_str}) - {category_data['description'][:40]}...")
        
        print(f"✅ ТЕСТ 3 ПРОЙДЕН: average-check-categories endpoint работает корректно")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ КРИТИЧНАЯ ОШИБКА: Таймаут при запросе average-check-categories")
        return False
    except Exception as e:
        print(f"❌ КРИТИЧНАЯ ОШИБКА: {str(e)}")
        return False

def test_venue_profile_endpoint():
    """Тест 4: GET /api/venue-profile/{user_id} - должен вернуть профиль заведения"""
    print("\n👤 ТЕСТ 4: GET /api/venue-profile/{user_id}")
    print("-" * 50)
    
    test_user_id = "test_user_venue_modal"
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/venue-profile/{test_user_id}", timeout=30)
        response_time = time.time() - start_time
        
        print(f"⏱️  Время ответа: {response_time:.2f} секунд")
        print(f"📊 Статус код: {response.status_code}")
        
        if response.status_code == 404:
            print("ℹ️  Пользователь не найден - это нормально для тестового ID")
            print("✅ ТЕСТ 4 ПРОЙДЕН: venue-profile endpoint доступен")
            return True
        elif response.status_code != 200:
            print(f"❌ ОШИБКА: venue-profile endpoint вернул {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return False
        
        profile = response.json()
        print(f"👤 Получен профиль заведения: {json.dumps(profile, indent=2, ensure_ascii=False)}")
        
        # Проверяем структуру ответа
        expected_fields = ["venue_type", "cuisine_focus", "average_check", "venue_name", "has_pro_features"]
        for field in expected_fields:
            if field not in profile:
                print(f"❌ ОШИБКА: Отсутствует поле '{field}' в профиле заведения")
                return False
        
        print(f"✅ ТЕСТ 4 ПРОЙДЕН: venue-profile endpoint работает корректно")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ КРИТИЧНАЯ ОШИБКА: Таймаут при запросе venue-profile")
        return False
    except Exception as e:
        print(f"❌ КРИТИЧНАЯ ОШИБКА: {str(e)}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚨 КРИТИЧНЫЙ ТЕСТ: Venue Profile Modal Backend Endpoints")
    print("=" * 70)
    print("Проверяем что backend правильно отдает данные для venue profile modal")
    print("Цель: убедиться что кнопка ДАЛЕЕ может активироваться при получении данных")
    print()
    
    start_time = time.time()
    
    # Запускаем все тесты
    tests = [
        ("Venue Types Endpoint", test_venue_types_endpoint),
        ("Cuisine Types Endpoint", test_cuisine_types_endpoint),
        ("Average Check Categories", test_average_check_categories_endpoint),
        ("Venue Profile Endpoint", test_venue_profile_endpoint)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
            else:
                print(f"❌ {test_name} ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} ПРОВАЛЕН с ошибкой: {str(e)}")
    
    # Итоговый отчет
    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print(f"⏱️  Общее время тестирования: {total_time:.2f} секунд")
    print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")
    print(f"❌ Провалено тестов: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Backend endpoints для venue profile modal работают корректно")
        print("✅ Данные доступны для активации кнопки ДАЛЕЕ")
        print("✅ Структура данных соответствует ожидаемой")
        print("\n🔧 РЕКОМЕНДАЦИЯ: Проверьте frontend код venue profile modal")
        print("   Возможные причины неактивной кнопки ДАЛЕЕ:")
        print("   • Неправильная обработка полученных данных в frontend")
        print("   • Ошибка в логике валидации формы")
        print("   • Проблема с состоянием React компонента")
        return True
    else:
        print(f"\n🚨 КРИТИЧНЫЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ!")
        print(f"❌ {total_tests - passed_tests} из {total_tests} endpoints не работают")
        print("🔧 ТРЕБУЕТСЯ НЕМЕДЛЕННОЕ ИСПРАВЛЕНИЕ backend endpoints")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)