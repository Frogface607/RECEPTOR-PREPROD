#!/usr/bin/env python3
"""
Backend Testing Suite for Receptor Pro - IMPROVE DISH Feature
Testing the new IMPROVE DISH endpoint as requested in review
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_improve_dish_feature():
    """Test the new IMPROVE DISH feature with specified test data"""
    print("🎯 TESTING NEW IMPROVE DISH FEATURE")
    print("=" * 60)
    
    # Test data as specified in review request
    user_id = "test_user_12345"
    
    # Sample tech card for "Паста с томатным соусом" as requested
    sample_tech_card = """**Название:** Паста с томатным соусом

**Категория:** основное

**Описание:** Классическая итальянская паста с ароматным томатным соусом, приготовленная из свежих помидоров с добавлением базилика и чеснока.

**Ингредиенты:** (на одну порцию)

- Спагетти — 100 г — ~25 ₽
- Помидоры свежие — 150 г — ~45 ₽
- Чеснок — 10 г — ~5 ₽
- Базилик свежий — 5 г — ~15 ₽
- Оливковое масло — 15 мл — ~20 ₽
- Соль — 2 г — ~1 ₽
- Перец черный — 1 г — ~2 ₽

**Пошаговый рецепт:**

1. Отварить спагетти в подсоленной воде до состояния аль денте (8-10 минут)
2. Разогреть оливковое масло в сковороде, добавить измельченный чеснок
3. Добавить нарезанные помидоры, тушить 5-7 минут
4. Приправить солью и перцем, добавить базилик
5. Смешать готовую пасту с соусом, подавать горячей

**Время:** Подготовка 10 мин | Готовка 15 мин | ИТОГО 25 мин

**Выход:** 250 г готового блюда

**Порция:** 250 г (одна порция)

**Себестоимость:**

- По ингредиентам: 113 ₽
- Себестоимость 1 порции: 113 ₽
- Рекомендуемая цена (×3): 339 ₽

**КБЖУ на 1 порцию:** Калории 420 ккал | Б 14 г | Ж 12 г | У 65 г"""
    
    print("📋 Step 1: Testing POST /api/improve-dish endpoint...")
    print(f"🔧 Using test data:")
    print(f"   - user_id: {user_id}")
    print(f"   - tech_card: Sample tech card for 'Паста с томатным соусом'")
    
    # Prepare the request
    improve_request = {
        "user_id": user_id,
        "tech_card": sample_tech_card
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/improve-dish", json=improve_request, timeout=120)
        end_time = time.time()
        
        print(f"⏱️ API response time: {end_time - start_time:.2f} seconds")
        
        # Test 1: API responds with 200 status
        if response.status_code != 200:
            print(f"❌ Test 1 FAILED: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print("✅ Test 1 PASSED: API responds with 200 status")
        
        # Parse response
        improve_data = response.json()
        
        # Test 2: Response includes success flag
        if not improve_data.get("success"):
            print("❌ Test 2 FAILED: Response does not include success=true")
            print(f"Response: {improve_data}")
            return False
            
        print("✅ Test 2 PASSED: Response includes success flag")
        
        # Test 3: Returns improved_dish content
        improved_dish = improve_data.get("improved_dish")
        if not improved_dish:
            print("❌ Test 3 FAILED: No improved_dish content in response")
            return False
            
        print("✅ Test 3 PASSED: Returns improved_dish content")
        print(f"📄 Improved dish content length: {len(improved_dish)} characters")
        
        # Test 4: Preserves the essence of the original dish
        original_dish_name = improve_data.get("original_dish", "")
        if "паста" not in improved_dish.lower() and "томат" not in improved_dish.lower():
            print("❌ Test 4 FAILED: Improved dish doesn't preserve essence of pasta with tomato sauce")
            return False
            
        print("✅ Test 4 PASSED: Preserves the essence of the original dish")
        
        # Test 5: Includes professional cooking techniques and tips
        professional_indicators = [
            "профессиональн", "техник", "секрет", "шеф", "улучшен", 
            "прокач", "мишлен", "ресторан", "совет", "хитрост"
        ]
        
        professional_found = sum(1 for indicator in professional_indicators 
                                if indicator in improved_dish.lower())
        
        if professional_found < 3:
            print(f"❌ Test 5 FAILED: Insufficient professional techniques found ({professional_found} indicators)")
            return False
            
        print(f"✅ Test 5 PASSED: Includes professional cooking techniques ({professional_found} professional indicators found)")
        
        # Additional quality checks
        print("\n🔍 Additional Quality Checks:")
        
        # Check for specific improvement sections
        improvement_sections = [
            "улучшения в ингредиентах", "профессиональные техники", 
            "секреты шефа", "улучшенный рецепт", "продвинутая подача"
        ]
        
        sections_found = sum(1 for section in improvement_sections 
                           if section in improved_dish.lower())
        
        print(f"📊 Improvement sections found: {sections_found}/{len(improvement_sections)}")
        
        # Check for specific professional techniques
        techniques = [
            "плейтинг", "сервировка", "температур", "оборудован", 
            "заменить", "добавить", "техника", "эффект"
        ]
        
        techniques_found = sum(1 for technique in techniques 
                             if technique in improved_dish.lower())
        
        print(f"🔧 Professional techniques mentioned: {techniques_found}/{len(techniques)}")
        
        # Check content structure
        if "**" in improved_dish:
            print("✅ Content has proper markdown formatting")
        else:
            print("⚠️ Warning: Content may lack proper formatting")
            
        # Check for creativity indicators
        creativity_words = ["креативн", "инновац", "современн", "оригинальн", "уникальн"]
        creativity_found = sum(1 for word in creativity_words 
                             if word in improved_dish.lower())
        
        print(f"🎨 Creativity indicators: {creativity_found} found")
        
        # Print sample of improved content
        print("\n📖 Sample of improved dish content:")
        print("-" * 50)
        print(improved_dish[:500] + "..." if len(improved_dish) > 500 else improved_dish)
        print("-" * 50)
        
        # Summary of test results
        print("\n📊 IMPROVE DISH FEATURE TEST SUMMARY:")
        print("=" * 50)
        print(f"✅ API Status: 200 OK")
        print(f"✅ Success Flag: {improve_data.get('success')}")
        print(f"✅ Original Dish: {original_dish_name}")
        print(f"📄 Improved Content Length: {len(improved_dish)} characters")
        print(f"🔧 Professional Indicators: {professional_found}")
        print(f"📊 Improvement Sections: {sections_found}/{len(improvement_sections)}")
        print(f"🎨 Creativity Level: {creativity_found} indicators")
        print(f"⏱️ Response Time: {end_time - start_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing IMPROVE DISH feature: {str(e)}")
        return False

def main():
    """Main test execution"""
    print("🚀 RECEPTOR PRO - IMPROVE DISH FEATURE TESTING")
    print("Testing new dish improvement endpoint as requested in review")
    print("=" * 60)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test the IMPROVE DISH feature
    improve_success = test_improve_dish_feature()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST RESULTS:")
    print("=" * 60)
    
    if improve_success:
        print("✅ IMPROVE DISH FEATURE: ALL TESTS PASSED")
        print("🎉 The new IMPROVE DISH feature is working correctly!")
        print("✅ API responds with 200 status")
        print("✅ Returns improved_dish content with professional techniques")
        print("✅ Preserves the essence of the original dish")
        print("✅ Includes professional cooking techniques and tips")
        print("✅ Response includes success flag and improved_dish content")
        print("\n🚀 READY FOR PRODUCTION USE!")
    else:
        print("❌ IMPROVE DISH FEATURE: TESTS FAILED")
        print("🚨 The IMPROVE DISH feature needs fixes before production")
    
    print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()