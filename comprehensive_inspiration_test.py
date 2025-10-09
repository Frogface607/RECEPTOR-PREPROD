#!/usr/bin/env python3
"""
Comprehensive test for /api/generate-inspiration endpoint
Testing all requirements from the review request
"""

import requests
import json
import re
import time

def comprehensive_inspiration_test():
    """Comprehensive test covering all review requirements"""
    
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    print("🎯 COMPREHENSIVE INSPIRATION ENDPOINT TEST")
    print("Testing all requirements from review request")
    print("=" * 60)
    
    # Test data exactly as specified in review
    test_data = {
        "user_id": "test_user_12345",
        "tech_card": "**Название:** Борщ украинский\n\n**Категория:** суп\n\n**Описание:** Классический борщ со свеклой и капустой\n\n**Ингредиенты:**\n- Свекла — 100 г — ~25 ₽\n- Капуста — 80 г — ~15 ₽\n- Морковь — 50 г — ~8 ₽\n\n**Пошаговый рецепт:**\n1. Нарезать свеклу\n2. Варить в бульоне\n\n**Время:** 60 минут\n\n**Выход:** 300 мл\n\n**Себестоимость:** 48 ₽",
        "inspiration_prompt": "Создай азиатский твист на это блюдо"
    }
    
    results = {
        "endpoint_works": False,
        "dish_name_parsed": False,
        "creative_twist": False,
        "correct_json": False,
        "no_errors": True,
        "response_time": 0,
        "content_length": 0
    }
    
    print("📋 REVIEW REQUIREMENTS CHECKLIST:")
    print("1. ✓ Работает ли endpoint")
    print("2. ✓ Правильно ли парсится название блюда") 
    print("3. ✓ Генерируется ли креативный твист")
    print("4. ✓ Возвращается ли правильный JSON с полем 'inspiration'")
    print("5. ✓ Есть ли ошибки в логах")
    print()
    
    # REQUIREMENT 1: Endpoint functionality
    print("🔍 REQUIREMENT 1: Endpoint Functionality")
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/generate-inspiration", json=test_data, timeout=120)
        end_time = time.time()
        results["response_time"] = end_time - start_time
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {results['response_time']:.2f} seconds")
        
        if response.status_code == 200:
            results["endpoint_works"] = True
            print("   ✅ REQUIREMENT 1 PASSED: Endpoint is working")
        else:
            print(f"   ❌ REQUIREMENT 1 FAILED: Status {response.status_code}")
            print(f"   Error: {response.text}")
            return results
            
    except Exception as e:
        print(f"   ❌ REQUIREMENT 1 FAILED: {str(e)}")
        results["no_errors"] = False
        return results
    
    # REQUIREMENT 4: JSON format with "inspiration" field
    print("\n🔍 REQUIREMENT 4: JSON Response Format")
    try:
        response_data = response.json()
        print(f"   Response keys: {list(response_data.keys())}")
        
        if "inspiration" in response_data:
            results["correct_json"] = True
            inspiration_content = response_data["inspiration"]
            results["content_length"] = len(inspiration_content)
            print("   ✅ REQUIREMENT 4 PASSED: Correct JSON with 'inspiration' field")
            print(f"   Content length: {results['content_length']} characters")
        else:
            print("   ❌ REQUIREMENT 4 FAILED: Missing 'inspiration' field")
            return results
            
    except json.JSONDecodeError:
        print("   ❌ REQUIREMENT 4 FAILED: Invalid JSON response")
        results["no_errors"] = False
        return results
    
    # REQUIREMENT 2: Dish name parsing
    print("\n🔍 REQUIREMENT 2: Dish Name Parsing")
    
    # Check if original dish name is referenced
    original_dish_keywords = ["борщ", "украинский", "свекла", "капуста"]
    found_keywords = []
    
    for keyword in original_dish_keywords:
        if keyword.lower() in inspiration_content.lower():
            found_keywords.append(keyword)
    
    # Also check if the new dish name is properly formatted
    title_match = re.search(r'\*\*Название:\*\*\s*(.*?)(?=\n|$)', inspiration_content)
    new_dish_name = title_match.group(1).strip() if title_match else "Not found"
    
    print(f"   Original dish references found: {found_keywords}")
    print(f"   New dish name: {new_dish_name}")
    
    if found_keywords and title_match:
        results["dish_name_parsed"] = True
        print("   ✅ REQUIREMENT 2 PASSED: Dish name correctly parsed and referenced")
    else:
        print("   ❌ REQUIREMENT 2 FAILED: Dish name parsing issues")
    
    # REQUIREMENT 3: Creative twist generation
    print("\n🔍 REQUIREMENT 3: Creative Twist Generation")
    
    # Check for Asian elements as requested in prompt
    asian_elements = ["азиат", "китай", "япон", "корей", "тай", "вьетнам", "соевый", "имбирь", 
                     "кунжут", "мисо", "рамен", "фо", "том", "кимчи", "васаби", "нори", "рис"]
    found_asian = []
    
    for element in asian_elements:
        if element in inspiration_content.lower():
            found_asian.append(element)
    
    # Check for creative modifications
    creative_indicators = ["твист", "креативн", "неожиданн", "оригинальн", "интересн", "замен"]
    found_creative = []
    
    for indicator in creative_indicators:
        if indicator in inspiration_content.lower():
            found_creative.append(indicator)
    
    print(f"   Asian elements found: {found_asian}")
    print(f"   Creative indicators: {found_creative}")
    
    if found_asian and len(inspiration_content) > 1000:
        results["creative_twist"] = True
        print("   ✅ REQUIREMENT 3 PASSED: Creative Asian twist generated")
    else:
        print("   ❌ REQUIREMENT 3 FAILED: Insufficient creative content")
    
    # REQUIREMENT 5: Check for errors (already monitored throughout)
    print("\n🔍 REQUIREMENT 5: Error Checking")
    if results["no_errors"]:
        print("   ✅ REQUIREMENT 5 PASSED: No errors detected during testing")
    else:
        print("   ❌ REQUIREMENT 5 FAILED: Errors detected")
    
    # Display sample of generated content
    print("\n📄 GENERATED CONTENT SAMPLE:")
    print("   " + "="*50)
    print(f"   {inspiration_content[:800]}...")
    if len(inspiration_content) > 800:
        print("   [Content truncated for display]")
    print("   " + "="*50)
    
    return results

def test_additional_scenarios():
    """Test additional edge cases and scenarios"""
    
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    print("\n🔍 ADDITIONAL TESTING SCENARIOS")
    print("=" * 40)
    
    # Test with different inspiration prompts
    test_cases = [
        {
            "name": "Italian twist",
            "prompt": "Создай итальянский твист на это блюдо",
            "expected_keywords": ["итальян", "паста", "пармезан", "базилик", "томат"]
        },
        {
            "name": "Modern molecular",
            "prompt": "Создай молекулярный гастрономический твист",
            "expected_keywords": ["молекуляр", "сфер", "гель", "пена", "современн"]
        }
    ]
    
    base_tech_card = "**Название:** Борщ украинский\n\n**Категория:** суп\n\n**Описание:** Классический борщ со свеклой и капустой\n\n**Ингредиенты:**\n- Свекла — 100 г — ~25 ₽\n- Капуста — 80 г — ~15 ₽\n- Морковь — 50 г — ~8 ₽\n\n**Пошаговый рецепт:**\n1. Нарезать свеклу\n2. Варить в бульоне\n\n**Время:** 60 минут\n\n**Выход:** 300 мл\n\n**Себестоимость:** 48 ₽"
    
    for test_case in test_cases:
        print(f"\n🧪 Testing {test_case['name']}...")
        
        test_data = {
            "user_id": "test_user_12345",
            "tech_card": base_tech_card,
            "inspiration_prompt": test_case["prompt"]
        }
        
        try:
            response = requests.post(f"{base_url}/generate-inspiration", json=test_data, timeout=60)
            
            if response.status_code == 200:
                content = response.json().get("inspiration", "")
                found_keywords = [kw for kw in test_case["expected_keywords"] if kw in content.lower()]
                
                print(f"   Status: ✅ Success")
                print(f"   Keywords found: {found_keywords}")
                print(f"   Content length: {len(content)} chars")
            else:
                print(f"   Status: ❌ Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   Status: ❌ Error - {str(e)}")

if __name__ == "__main__":
    print("🚀 STARTING COMPREHENSIVE INSPIRATION TESTING")
    print("Testing all requirements from review request")
    print("=" * 60)
    
    # Run main test
    results = comprehensive_inspiration_test()
    
    # Summary
    print("\n📊 FINAL RESULTS SUMMARY:")
    print("=" * 40)
    print(f"✅ Endpoint works: {'PASS' if results['endpoint_works'] else 'FAIL'}")
    print(f"✅ Dish name parsed: {'PASS' if results['dish_name_parsed'] else 'FAIL'}")
    print(f"✅ Creative twist: {'PASS' if results['creative_twist'] else 'FAIL'}")
    print(f"✅ Correct JSON: {'PASS' if results['correct_json'] else 'FAIL'}")
    print(f"✅ No errors: {'PASS' if results['no_errors'] else 'FAIL'}")
    print(f"📈 Response time: {results['response_time']:.2f} seconds")
    print(f"📄 Content length: {results['content_length']} characters")
    
    # Overall result
    all_passed = all([
        results['endpoint_works'],
        results['dish_name_parsed'], 
        results['creative_twist'],
        results['correct_json'],
        results['no_errors']
    ])
    
    if all_passed:
        print("\n🎉 ALL REQUIREMENTS PASSED!")
        print("The /api/generate-inspiration endpoint is working correctly.")
        
        # Run additional tests
        test_additional_scenarios()
        
    else:
        print("\n❌ SOME REQUIREMENTS FAILED")
        print("Check the detailed results above for specific issues.")