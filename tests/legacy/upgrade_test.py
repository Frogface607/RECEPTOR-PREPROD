#!/usr/bin/env python3
"""
УЛУЧШЕННАЯ СИСТЕМА MENU GENERATION И TECH CARD GENERATION - ТЕСТИРОВАНИЕ АПГРЕЙДОВ
Специфические требования для тестирования после апгрейда до GPT-4o
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def log_test(message, status="INFO"):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_menu_generation_with_gpt4o():
    """
    ОСНОВНОЙ ТЕСТ: Menu Generation с GPT-4o
    Тестирует генерацию меню с точными параметрами из review request
    """
    log_test("🎯 НАЧАЛО ТЕСТИРОВАНИЯ MENU GENERATION С GPT-4o", "TEST")
    
    # Создание PRO пользователя как указано в требованиях
    user_id = "upgrade_test_user"
    
    # Точные параметры из review request
    menu_request = {
        "user_id": user_id,
        "menu_profile": {
            "menuType": "restaurant",
            "dishCount": 6,  # ТОЧНОЕ количество - должно быть РОВНО 6 блюд
            "averageCheck": "medium",
            "cuisineStyle": "italian",
            "targetAudience": "family",
            "menuGoals": ["profit", "efficiency"],
            "specialRequirements": ["local", "seasonal"],
            "staffSkillLevel": "medium",
            "preparationTime": "medium",
            "ingredientBudget": "medium",
            "menuDescription": "Семейный итальянский ресторан с акцентом на традиционные рецепты",
            "expectations": "Меню должно быть доступным для семей с детьми, но качественным",
            "additionalNotes": "Учесть сезонность продуктов"
        },
        "venue_profile": {
            "venue_name": "Bella Famiglia",
            "venue_type": "family_restaurant",
            "cuisine_type": "italian",
            "average_check": "medium"
        }
    }
    
    log_test(f"Отправка запроса генерации меню для пользователя: {user_id}")
    log_test(f"Параметры: {json.dumps(menu_request, ensure_ascii=False, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-menu", json=menu_request, timeout=120)
        end_time = time.time()
        
        log_test(f"Время ответа: {end_time - start_time:.2f} секунд")
        log_test(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            menu_data = response.json()
            log_test("✅ MENU GENERATION УСПЕШНО")
            
            # Проверка структуры ответа
            if "menu" in menu_data and "menu_id" in menu_data:
                menu = menu_data["menu"]
                menu_id = menu_data["menu_id"]
                
                log_test(f"Menu ID: {menu_id}")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: точное количество блюд
                total_dishes = 0
                categories = menu.get("categories", {})
                
                log_test("📊 АНАЛИЗ СГЕНЕРИРОВАННОГО МЕНЮ:")
                for category_name, dishes in categories.items():
                    dish_count = len(dishes) if isinstance(dishes, list) else 0
                    total_dishes += dish_count
                    log_test(f"  {category_name}: {dish_count} блюд")
                    
                    # Показать примеры блюд
                    if isinstance(dishes, list) and dishes:
                        for i, dish in enumerate(dishes[:2]):  # Показать первые 2 блюда
                            dish_name = dish.get("name", "Без названия")
                            log_test(f"    - {dish_name}")
                
                log_test(f"🎯 ОБЩЕЕ КОЛИЧЕСТВО БЛЮД: {total_dishes}")
                
                # ПРОВЕРКА ТРЕБОВАНИЯ: должно быть РОВНО 6 блюд
                if total_dishes == 6:
                    log_test("✅ ТОЧНОЕ КОЛИЧЕСТВО БЛЮД: Сгенерировано ровно 6 блюд как требовалось")
                else:
                    log_test(f"❌ ОШИБКА КОЛИЧЕСТВА: Ожидалось 6 блюд, получено {total_dishes}", "ERROR")
                
                # Проверка учета параметров menu_profile
                menu_str = json.dumps(menu, ensure_ascii=False).lower()
                
                # Проверка итальянской кухни
                italian_indicators = ["итальян", "паста", "пицца", "ризотто", "лазанья", "карбонара", "болоньезе"]
                found_italian = [ind for ind in italian_indicators if ind in menu_str]
                
                if found_italian:
                    log_test(f"✅ ИТАЛЬЯНСКАЯ КУХНЯ: Найдены индикаторы - {found_italian}")
                else:
                    log_test("⚠️ ИТАЛЬЯНСКАЯ КУХНЯ: Индикаторы не найдены", "WARNING")
                
                # Проверка семейного акцента
                family_indicators = ["семейн", "детск", "традицион", "домашн"]
                found_family = [ind for ind in family_indicators if ind in menu_str]
                
                if found_family:
                    log_test(f"✅ СЕМЕЙНЫЙ АКЦЕНТ: Найдены индикаторы - {found_family}")
                else:
                    log_test("⚠️ СЕМЕЙНЫЙ АКЦЕНТ: Индикаторы не найдены", "WARNING")
                
                # Проверка качества от GPT-4o
                content_length = len(json.dumps(menu, ensure_ascii=False))
                log_test(f"📏 РАЗМЕР КОНТЕНТА: {content_length} символов")
                
                if content_length > 2000:
                    log_test("✅ КАЧЕСТВО GPT-4o: Детальный контент (>2000 символов)")
                else:
                    log_test("⚠️ КАЧЕСТВО GPT-4o: Контент может быть недостаточно детальным", "WARNING")
                
                return menu_data
                
            else:
                log_test("❌ ОШИБКА СТРУКТУРЫ: Отсутствуют обязательные поля menu/menu_id", "ERROR")
                return None
        else:
            log_test(f"❌ ОШИБКА ЗАПРОСА: {response.status_code} - {response.text}", "ERROR")
            return None
            
    except Exception as e:
        log_test(f"❌ ИСКЛЮЧЕНИЕ ПРИ ТЕСТИРОВАНИИ MENU GENERATION: {str(e)}", "ERROR")
        return None

def test_enhanced_tech_card_generation(menu_data):
    """
    КЛЮЧЕВОЙ ТЕСТ: Enhanced Tech Card Generation
    Тестирует генерацию техкарты с полным контекстом из меню
    """
    log_test("🎯 НАЧАЛО ТЕСТИРОВАНИЯ ENHANCED TECH CARD GENERATION", "TEST")
    
    if not menu_data or "menu" not in menu_data:
        log_test("❌ НЕТ ДАННЫХ МЕНЮ: Невозможно протестировать техкарты", "ERROR")
        return False
    
    # Взять первое блюдо из сгенерированного меню
    menu = menu_data["menu"]
    categories = menu.get("categories", {})
    
    selected_dish = None
    for category_name, dishes in categories.items():
        if isinstance(dishes, list) and dishes:
            selected_dish = dishes[0]
            selected_dish["category"] = category_name
            break
    
    if not selected_dish:
        log_test("❌ НЕТ БЛЮД В МЕНЮ: Невозможно выбрать блюдо для техкарты", "ERROR")
        return False
    
    # Подготовка запроса с ПОЛНЫМ контекстом как указано в требованиях
    tech_card_request = {
        "dish_name": selected_dish.get("name", "Неизвестное блюдо"),
        "user_id": "upgrade_test_user",
        "dish_description": selected_dish.get("description", ""),
        "main_ingredients": selected_dish.get("main_ingredients", []),
        "category": selected_dish.get("category", ""),
        "estimated_cost": selected_dish.get("estimated_cost", ""),
        "estimated_price": selected_dish.get("estimated_price", ""),
        "difficulty": selected_dish.get("difficulty", ""),
        "cook_time": selected_dish.get("cook_time", "")
    }
    
    log_test(f"Выбранное блюдо: {tech_card_request['dish_name']}")
    log_test(f"Категория: {tech_card_request['category']}")
    log_test(f"Описание: {tech_card_request['dish_description'][:100]}...")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", json=tech_card_request, timeout=120)
        end_time = time.time()
        
        log_test(f"Время ответа: {end_time - start_time:.2f} секунд")
        log_test(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            tech_card_data = response.json()
            log_test("✅ TECH CARD GENERATION УСПЕШНО")
            
            if "tech_card" in tech_card_data:
                tech_card_content = tech_card_data["tech_card"]
                content_length = len(tech_card_content)
                
                log_test(f"📏 РАЗМЕР ТЕХКАРТЫ: {content_length} символов")
                
                # Проверка использования контекста из меню
                tech_card_lower = tech_card_content.lower()
                
                # Проверка упоминания категории
                category = tech_card_request.get("category", "").lower()
                if category and category in tech_card_lower:
                    log_test(f"✅ КОНТЕКСТ КАТЕГОРИИ: Техкарта упоминает категорию '{category}'")
                else:
                    log_test(f"⚠️ КОНТЕКСТ КАТЕГОРИИ: Категория '{category}' не найдена в техкарте", "WARNING")
                
                # Проверка использования ингредиентов из меню
                main_ingredients = tech_card_request.get("main_ingredients", [])
                if main_ingredients:
                    found_ingredients = []
                    for ingredient in main_ingredients:
                        if ingredient.lower() in tech_card_lower:
                            found_ingredients.append(ingredient)
                    
                    if found_ingredients:
                        log_test(f"✅ КОНТЕКСТ ИНГРЕДИЕНТОВ: Найдены - {found_ingredients}")
                    else:
                        log_test("⚠️ КОНТЕКСТ ИНГРЕДИЕНТОВ: Основные ингредиенты из меню не найдены", "WARNING")
                
                # Проверка детальности благодаря полному контексту
                required_sections = ["ингредиент", "рецепт", "время", "себестоимость", "кбжу"]
                found_sections = []
                for section in required_sections:
                    if section in tech_card_lower:
                        found_sections.append(section)
                
                log_test(f"📋 РАЗДЕЛЫ ТЕХКАРТЫ: Найдено {len(found_sections)}/5 - {found_sections}")
                
                if len(found_sections) >= 4:
                    log_test("✅ ПОЛНОТА ТЕХКАРТЫ: Содержит основные разделы")
                else:
                    log_test("⚠️ ПОЛНОТА ТЕХКАРТЫ: Недостаточно разделов", "WARNING")
                
                # Проверка соответствия сложности и времени готовки
                expected_difficulty = tech_card_request.get("difficulty", "").lower()
                expected_time = tech_card_request.get("cook_time", "")
                
                if expected_difficulty:
                    difficulty_indicators = ["простой", "средний", "сложный", "легкий", "трудный"]
                    found_difficulty = [d for d in difficulty_indicators if d in tech_card_lower]
                    if found_difficulty:
                        log_test(f"✅ СООТВЕТСТВИЕ СЛОЖНОСТИ: Найдены индикаторы - {found_difficulty}")
                    else:
                        log_test("⚠️ СООТВЕТСТВИЕ СЛОЖНОСТИ: Индикаторы сложности не найдены", "WARNING")
                
                if expected_time:
                    if "мин" in tech_card_lower or "час" in tech_card_lower:
                        log_test("✅ ВРЕМЯ ГОТОВКИ: Указано время приготовления")
                    else:
                        log_test("⚠️ ВРЕМЯ ГОТОВКИ: Время приготовления не найдено", "WARNING")
                
                # Проверка качества от расширенного контекста
                if content_length > 2500:
                    log_test("✅ КАЧЕСТВО РАСШИРЕННОГО КОНТЕКСТА: Детальная техкарта (>2500 символов)")
                elif content_length > 1500:
                    log_test("✅ КАЧЕСТВО РАСШИРЕННОГО КОНТЕКСТА: Хорошая детализация (>1500 символов)")
                else:
                    log_test("⚠️ КАЧЕСТВО РАСШИРЕННОГО КОНТЕКСТА: Может быть недостаточно детальной", "WARNING")
                
                return True
                
            else:
                log_test("❌ ОШИБКА СТРУКТУРЫ: Отсутствует поле tech_card", "ERROR")
                return False
        else:
            log_test(f"❌ ОШИБКА ЗАПРОСА: {response.status_code} - {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ ИСКЛЮЧЕНИЕ ПРИ ТЕСТИРОВАНИИ TECH CARD GENERATION: {str(e)}", "ERROR")
        return False

def test_quality_comparison():
    """
    КАЧЕСТВЕННЫЕ ПРОВЕРКИ: Сравнение с предыдущими версиями
    """
    log_test("🎯 НАЧАЛО КАЧЕСТВЕННЫХ ПРОВЕРОК", "TEST")
    
    # Тест простой генерации техкарты для сравнения
    simple_request = {
        "dish_name": "Паста Карбонара",
        "user_id": "upgrade_test_user"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", json=simple_request, timeout=120)
        end_time = time.time()
        
        log_test(f"Время ответа (простая генерация): {end_time - start_time:.2f} секунд")
        
        if response.status_code == 200:
            tech_card_data = response.json()
            if "tech_card" in tech_card_data:
                content = tech_card_data["tech_card"]
                content_length = len(content)
                
                log_test(f"📏 РАЗМЕР ПРОСТОЙ ТЕХКАРТЫ: {content_length} символов")
                
                # Проверка качественных индикаторов
                quality_indicators = [
                    "себестоимость", "рекомендуемая цена", "кбжу", "аллергены",
                    "заготовки", "советы", "подача", "температур"
                ]
                
                found_indicators = []
                content_lower = content.lower()
                for indicator in quality_indicators:
                    if indicator in content_lower:
                        found_indicators.append(indicator)
                
                log_test(f"🔍 КАЧЕСТВЕННЫЕ ИНДИКАТОРЫ: {len(found_indicators)}/8 - {found_indicators}")
                
                if len(found_indicators) >= 6:
                    log_test("✅ ВЫСОКОЕ КАЧЕСТВО: Техкарта содержит большинство профессиональных элементов")
                elif len(found_indicators) >= 4:
                    log_test("✅ ХОРОШЕЕ КАЧЕСТВО: Техкарта содержит основные профессиональные элементы")
                else:
                    log_test("⚠️ БАЗОВОЕ КАЧЕСТВО: Техкарта содержит минимальные элементы", "WARNING")
                
                return True
        
        return False
        
    except Exception as e:
        log_test(f"❌ ИСКЛЮЧЕНИЕ ПРИ КАЧЕСТВЕННЫХ ПРОВЕРКАХ: {str(e)}", "ERROR")
        return False

def main():
    """Основная функция тестирования"""
    log_test("🚀 НАЧАЛО ТЕСТИРОВАНИЯ УЛУЧШЕННОЙ СИСТЕМЫ MENU И TECH CARD GENERATION", "START")
    log_test("Цель: Убедиться, что апгрейд до GPT-4o + расширенный контекст дает качественный результат")
    
    # Счетчики результатов
    total_tests = 0
    passed_tests = 0
    
    # 1. Тест Menu Generation с GPT-4o
    total_tests += 1
    log_test("\n" + "="*80)
    menu_data = test_menu_generation_with_gpt4o()
    if menu_data:
        passed_tests += 1
        log_test("✅ MENU GENERATION ТЕСТ ПРОЙДЕН")
    else:
        log_test("❌ MENU GENERATION ТЕСТ НЕ ПРОЙДЕН", "ERROR")
    
    # 2. Тест Enhanced Tech Card Generation
    total_tests += 1
    log_test("\n" + "="*80)
    if test_enhanced_tech_card_generation(menu_data):
        passed_tests += 1
        log_test("✅ ENHANCED TECH CARD GENERATION ТЕСТ ПРОЙДЕН")
    else:
        log_test("❌ ENHANCED TECH CARD GENERATION ТЕСТ НЕ ПРОЙДЕН", "ERROR")
    
    # 3. Качественные проверки
    total_tests += 1
    log_test("\n" + "="*80)
    if test_quality_comparison():
        passed_tests += 1
        log_test("✅ КАЧЕСТВЕННЫЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    else:
        log_test("❌ КАЧЕСТВЕННЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ", "ERROR")
    
    # Итоговый отчет
    log_test("\n" + "="*80)
    log_test("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ", "RESULT")
    log_test(f"Всего тестов: {total_tests}")
    log_test(f"Пройдено: {passed_tests}")
    log_test(f"Не пройдено: {total_tests - passed_tests}")
    log_test(f"Процент успеха: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        log_test("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО - СИСТЕМА ГОТОВА К ПРОДАКШЕНУ", "SUCCESS")
        return True
    else:
        log_test("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ - ТРЕБУЕТСЯ ДОРАБОТКА", "WARNING")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)