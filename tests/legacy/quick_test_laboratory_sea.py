#!/usr/bin/env python3

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_sea_cuisine_name_fix():
    """
    TEST 1: SEA CUISINE NAME FIX
    - GET /api/cuisine-types
    - Verify that "sea" cuisine now shows as "Юго-Восточная Азия" (not "ЮВА (Юго-Восточная Азия)")
    """
    print("🧪 TEST 1: SEA CUISINE NAME FIX")
    print("=" * 50)
    
    try:
        # Test GET /api/cuisine-types
        response = requests.get(f"{API_BASE}/cuisine-types", timeout=30)
        print(f"📡 GET /api/cuisine-types")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            cuisine_types = response.json()
            
            # Check if "sea" cuisine exists
            if "sea" in cuisine_types:
                sea_cuisine = cuisine_types["sea"]
                sea_name = sea_cuisine.get("name", "")
                
                print(f"🌊 SEA Cuisine Found:")
                print(f"   Name: '{sea_name}'")
                print(f"   Subcategories: {sea_cuisine.get('subcategories', [])}")
                
                # Verify the name is correct
                expected_name = "Юго-Восточная Азия"
                if sea_name == expected_name:
                    print(f"✅ SUCCESS: SEA cuisine name is correct: '{sea_name}'")
                    return True
                else:
                    print(f"❌ FAILED: SEA cuisine name is incorrect")
                    print(f"   Expected: '{expected_name}'")
                    print(f"   Actual: '{sea_name}'")
                    return False
            else:
                print("❌ FAILED: 'sea' cuisine not found in response")
                print(f"Available cuisines: {list(cuisine_types.keys())}")
                return False
        else:
            print(f"❌ FAILED: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_laboratory_experiment_saving():
    """
    TEST 2: LABORATORY EXPERIMENT SAVING
    - Test new endpoint: POST /api/save-laboratory-experiment
    - Parameters:
      - user_id: "test_user_12345"
      - experiment: "Sample experiment content"  
      - experiment_type: "random"
      - image_url: "https://example.com/image.jpg" (optional)
    """
    print("\n🧪 TEST 2: LABORATORY EXPERIMENT SAVING")
    print("=" * 50)
    
    try:
        # Test data as specified in review request
        test_data = {
            "user_id": "test_user_12345",
            "experiment": "**НАЗВАНИЕ ЭКСПЕРИМЕНТА:** Молекулярная Паста с Икрой\n\n**ОПИСАНИЕ ЭКСПЕРИМЕНТА:**\nИнновационный подход к классической пасте с использованием молекулярной гастрономии. Создаем сферы из томатного соуса методом сферификации и подаем с пастой аль денте.\n\n**ИНГРЕДИЕНТЫ:**\n- Паста спагетти — 100г\n- Томатный сок — 200мл\n- Альгинат натрия — 2г\n- Хлорид кальция — 5г\n- Икра черная — 20г\n- Оливковое масло — 30мл\n\n**ПРОЦЕСС ЭКСПЕРИМЕНТА:**\n1. Подготавливаем раствор альгината натрия с томатным соком\n2. Создаем ванну из хлорида кальция\n3. Формируем томатные сферы методом сферификации\n4. Варим пасту аль денте\n5. Собираем блюдо с икрой и томатными сферами\n\n**РЕЗУЛЬТАТ:**\nПолучается визуально эффектное блюдо с взрывающимися во рту томатными сферами.",
            "experiment_type": "random",
            "image_url": "https://example.com/image.jpg"
        }
        
        # Test POST /api/save-laboratory-experiment
        response = requests.post(
            f"{API_BASE}/save-laboratory-experiment",
            json=test_data,
            timeout=30
        )
        
        print(f"📡 POST /api/save-laboratory-experiment")
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Response Data:")
            print(f"   Success: {result.get('success', False)}")
            print(f"   ID: {result.get('id', 'N/A')}")
            print(f"   Message: {result.get('message', 'N/A')}")
            
            # Verify response structure
            if result.get('success') and result.get('id'):
                print("✅ SUCCESS: Laboratory experiment saved correctly")
                
                # Test if saved experiment appears in user's history
                tech_card_id = result.get('id')
                return test_experiment_in_history("test_user_12345", tech_card_id)
            else:
                print("❌ FAILED: Invalid response structure")
                return False
        else:
            print(f"❌ FAILED: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_experiment_in_history(user_id, expected_tech_card_id):
    """
    Verify if saved experiment appears in user's tech cards history
    """
    print(f"\n🔍 VERIFICATION: Check experiment in user history")
    print("-" * 40)
    
    try:
        # Test GET /api/user-history/{user_id}
        response = requests.get(f"{API_BASE}/user-history/{user_id}", timeout=30)
        print(f"📡 GET /api/user-history/{user_id}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            history = response_data.get("history", [])
            print(f"📋 Found {len(history)} tech cards in history")
            
            # Look for our saved experiment
            experiment_found = False
            for tech_card in history:
                if tech_card.get('id') == expected_tech_card_id:
                    experiment_found = True
                    print(f"✅ Found saved experiment in history:")
                    print(f"   ID: {tech_card.get('id')}")
                    print(f"   Name: {tech_card.get('dish_name', 'N/A')}")
                    print(f"   Is Laboratory: {tech_card.get('is_laboratory', False)}")
                    print(f"   Experiment Type: {tech_card.get('experiment_type', 'N/A')}")
                    print(f"   Has Image URL: {'Yes' if tech_card.get('image_url') else 'No'}")
                    
                    # Verify laboratory flag
                    if tech_card.get('is_laboratory'):
                        print("✅ SUCCESS: Experiment properly marked as laboratory")
                        return True
                    else:
                        print("❌ FAILED: Experiment not marked as laboratory")
                        return False
            
            if not experiment_found:
                print(f"❌ FAILED: Saved experiment with ID {expected_tech_card_id} not found in history")
                return False
                
        else:
            print(f"❌ FAILED: History API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """
    Main test function for Quick Test - Laboratory Save & SEA Cuisine Fix
    """
    print("🚀 QUICK TEST - LABORATORY SAVE & SEA CUISINE FIX")
    print("=" * 60)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Track test results
    test_results = []
    
    # TEST 1: SEA CUISINE NAME FIX
    result1 = test_sea_cuisine_name_fix()
    test_results.append(("SEA Cuisine Name Fix", result1))
    
    # TEST 2: LABORATORY EXPERIMENT SAVING
    result2 = test_laboratory_experiment_saving()
    test_results.append(("Laboratory Experiment Saving", result2))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Both fixes are working correctly!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Issues need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)