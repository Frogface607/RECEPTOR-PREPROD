#!/usr/bin/env python3
"""
КРИТИЧЕСКИЙ ТЕСТ: Проверить исправление бага с техкартами после апгрейда
Testing tech card generation with full context to ensure all sections are properly generated
"""

import requests
import json
import time
import re
from datetime import datetime

# Configuration
BACKEND_URL = "https://fdf58838-b548-48aa-b986-f766bf021f59.preview.emergentagent.com/api"

def test_tech_card_generation_fix():
    """
    КРИТИЧЕСКИЙ ТЕСТ: Проверить исправление бага с техкартами после апгрейда
    Тестируем генерацию техкарт с полным контекстом и без него
    """
    print("🎯 КРИТИЧЕСКИЙ ТЕСТ: ИСПРАВЛЕНИЕ БАГА С ТЕХКАРТАМИ")
    print("=" * 70)
    
    test_results = {
        "enhanced_tech_card": False,
        "regular_tech_card": False,
        "all_sections_present": False,
        "sufficient_content_length": False
    }
    
    # Test 1: Enhanced Tech Card с контекстом из меню
    print("\n📋 Test 1: Enhanced Tech Card с полным контекстом из меню...")
    
    enhanced_request = {
        "dish_name": "Брускетта с помидорами и базиликом",
        "user_id": "fix_test_user",
        "dish_description": "Традиционная итальянская закуска с сочными помидорами и свежим базиликом",
        "main_ingredients": ["хлеб", "помидоры", "базилик", "оливковое масло"],
        "category": "Антипасти",
        "estimated_cost": "120",
        "estimated_price": "360",
        "difficulty": "легко",
        "cook_time": "15"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/generate-tech-card",
            json=enhanced_request,
            timeout=120
        )
        response_time = time.time() - start_time
        
        print(f"⏱️ Response time: {response_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ Enhanced Tech Card FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            return test_results
        
        enhanced_data = response.json()
        
        if not enhanced_data.get("success"):
            print(f"❌ Enhanced Tech Card FAILED: success=false")
            print(f"Response: {enhanced_data}")
            return test_results
        
        enhanced_content = enhanced_data.get("tech_card", "")
        print(f"✅ Enhanced Tech Card generated successfully")
        print(f"📊 Content length: {len(enhanced_content)} characters")
        
        # Analyze enhanced content
        enhanced_analysis = analyze_tech_card_content(enhanced_content, "Enhanced")
        test_results["enhanced_tech_card"] = True
        
    except Exception as e:
        print(f"❌ Enhanced Tech Card FAILED with exception: {str(e)}")
        return test_results
    
    # Test 2: Regular Tech Card без дополнительного контекста
    print("\n📋 Test 2: Regular Tech Card без дополнительного контекста...")
    
    regular_request = {
        "dish_name": "Паста карбонара",
        "user_id": "fix_test_user"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/generate-tech-card",
            json=regular_request,
            timeout=120
        )
        response_time = time.time() - start_time
        
        print(f"⏱️ Response time: {response_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ Regular Tech Card FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            return test_results
        
        regular_data = response.json()
        
        if not regular_data.get("success"):
            print(f"❌ Regular Tech Card FAILED: success=false")
            print(f"Response: {regular_data}")
            return test_results
        
        regular_content = regular_data.get("tech_card", "")
        print(f"✅ Regular Tech Card generated successfully")
        print(f"📊 Content length: {len(regular_content)} characters")
        
        # Analyze regular content
        regular_analysis = analyze_tech_card_content(regular_content, "Regular")
        test_results["regular_tech_card"] = True
        
        # Check if both tech cards have sufficient content
        if len(enhanced_content) >= 2500 and len(regular_content) >= 2500:
            test_results["sufficient_content_length"] = True
            print(f"✅ Both tech cards have sufficient content length (2500+ characters)")
        else:
            print(f"⚠️ Content length concern - Enhanced: {len(enhanced_content)}, Regular: {len(regular_content)}")
        
        # Check if all critical sections are present in both
        if (enhanced_analysis["all_sections"] and regular_analysis["all_sections"]):
            test_results["all_sections_present"] = True
            print(f"✅ All critical sections present in both tech cards")
        else:
            print(f"❌ Missing sections detected")
        
    except Exception as e:
        print(f"❌ Regular Tech Card FAILED with exception: {str(e)}")
        return test_results
    
    return test_results

def analyze_tech_card_content(content, card_type):
    """Analyze tech card content for completeness"""
    print(f"\n🔍 Analyzing {card_type} Tech Card Content:")
    
    analysis = {
        "step_by_step_recipe": False,
        "storage_tips": False,
        "chef_tips": False,
        "kbju": False,
        "allergens": False,
        "all_sections": False
    }
    
    # Check for пошаговый рецепт
    recipe_patterns = [
        r"пошаговый рецепт",
        r"рецепт:",
        r"\d+\.\s+.*",  # Numbered steps
        r"этап\s+\d+",
        r"шаг\s+\d+"
    ]
    
    recipe_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in recipe_patterns)
    if recipe_found:
        analysis["step_by_step_recipe"] = True
        print("✅ Пошаговый рецепт: НАЙДЕН")
    else:
        print("❌ Пошаговый рецепт: НЕ НАЙДЕН")
    
    # Check for ЗАГОТОВКИ И ХРАНЕНИЕ
    storage_patterns = [
        r"заготовки и хранение",
        r"заготовки:",
        r"хранение:",
        r"температур.*режим",
        r"срок.*годности",
        r"заморозк",
        r"контейнер"
    ]
    
    storage_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in storage_patterns)
    # Check it's not just "-" or emoji
    storage_detailed = False
    if storage_found:
        storage_section = re.search(r"заготовки и хранение:.*?(?=\*\*|$)", content, re.IGNORECASE | re.DOTALL)
        if storage_section:
            storage_text = storage_section.group(0)
            # Check if it contains meaningful content (not just "-" or emojis)
            meaningful_content = re.sub(r'[^\w\s]', '', storage_text)
            if len(meaningful_content.strip()) > 20:  # More than just basic symbols
                storage_detailed = True
    
    if storage_detailed:
        analysis["storage_tips"] = True
        print("✅ ЗАГОТОВКИ И ХРАНЕНИЕ: ДЕТАЛЬНЫЙ КОНТЕНТ")
    else:
        print("❌ ЗАГОТОВКИ И ХРАНЕНИЕ: ОТСУТСТВУЕТ ИЛИ ПУСТОЙ")
    
    # Check for СОВЕТЫ ОТ ШЕФА
    chef_patterns = [
        r"советы от шефа",
        r"особенности и советы",
        r"совет от receptor",
        r"фишка для продвинутых",
        r"вариации:",
        r"техника.*текстура.*баланс"
    ]
    
    chef_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in chef_patterns)
    # Check it's not just emoji
    chef_detailed = False
    if chef_found:
        chef_section = re.search(r"советы от шефа:.*?(?=\*\*|$)", content, re.IGNORECASE | re.DOTALL)
        if not chef_section:
            chef_section = re.search(r"особенности и советы.*?:.*?(?=\*\*|$)", content, re.IGNORECASE | re.DOTALL)
        
        if chef_section:
            chef_text = chef_section.group(0)
            # Check if it contains meaningful content (not just emojis)
            meaningful_content = re.sub(r'[^\w\s]', '', chef_text)
            if len(meaningful_content.strip()) > 30:  # More than just basic symbols
                chef_detailed = True
    
    if chef_detailed:
        analysis["chef_tips"] = True
        print("✅ СОВЕТЫ ОТ ШЕФА: ДЕТАЛЬНЫЙ КОНТЕНТ")
    else:
        print("❌ СОВЕТЫ ОТ ШЕФА: ОТСУТСТВУЕТ ИЛИ ТОЛЬКО ЭМОДЗИ")
    
    # Check for КБЖУ
    kbju_patterns = [
        r"кбжу.*порци",
        r"калории.*ккал",
        r"белки.*жиры.*углеводы",
        r"б.*г.*ж.*г.*у.*г"
    ]
    
    kbju_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in kbju_patterns)
    if kbju_found:
        analysis["kbju"] = True
        print("✅ КБЖУ: НАЙДЕН")
    else:
        print("❌ КБЖУ: НЕ НАЙДЕН")
    
    # Check for аллергены
    allergen_patterns = [
        r"аллергены:",
        r"глютен",
        r"лактоза",
        r"веган",
        r"безглютен"
    ]
    
    allergen_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in allergen_patterns)
    if allergen_found:
        analysis["allergens"] = True
        print("✅ АЛЛЕРГЕНЫ: НАЙДЕНЫ")
    else:
        print("❌ АЛЛЕРГЕНЫ: НЕ НАЙДЕНЫ")
    
    # Overall assessment
    critical_sections = [
        analysis["step_by_step_recipe"],
        analysis["storage_tips"],
        analysis["chef_tips"],
        analysis["kbju"]
    ]
    
    if all(critical_sections):
        analysis["all_sections"] = True
        print(f"✅ {card_type} Tech Card: ВСЕ КРИТИЧЕСКИЕ РАЗДЕЛЫ ПРИСУТСТВУЮТ")
    else:
        missing_count = critical_sections.count(False)
        print(f"❌ {card_type} Tech Card: ОТСУТСТВУЕТ {missing_count} критических разделов")
    
    return analysis

def main():
    """Main test execution"""
    print("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТА ИСПРАВЛЕНИЯ ТЕХКАРТ")
    print("=" * 70)
    
    start_time = time.time()
    
    # Run the critical tech card generation test
    results = test_tech_card_generation_fix()
    
    total_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТА")
    print("=" * 70)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"✅ Enhanced Tech Card Generation: {'PASSED' if results['enhanced_tech_card'] else 'FAILED'}")
    print(f"✅ Regular Tech Card Generation: {'PASSED' if results['regular_tech_card'] else 'FAILED'}")
    print(f"✅ All Sections Present: {'PASSED' if results['all_sections_present'] else 'FAILED'}")
    print(f"✅ Sufficient Content Length: {'PASSED' if results['sufficient_content_length'] else 'FAILED'}")
    
    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено")
    print(f"⏱️ Общее время выполнения: {total_time:.2f} секунд")
    
    if passed_tests == total_tests:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Исправление бага с техкартами ПОДТВЕРЖДЕНО")
        print("✅ Все разделы генерируются корректно")
        print("✅ Контент достаточно детальный")
        return True
    else:
        print(f"\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ!")
        print(f"❌ {total_tests - passed_tests} тестов провалились")
        print("❌ Требуется дополнительное исправление")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)