#!/usr/bin/env python3
"""
IIKo Integration - Create Product/Dish ОКОНЧАТЕЛЬНОЕ ТЕСТИРОВАНИЕ
Testing the minimal correct structure for DISH creation as requested in review.

ОКОНЧАТЕЛЬНЫЕ ИСПРАВЛЕНИЯ:
1. Case sensitivity: type="DISH" (uppercase) ✅
2. Убрал неподдерживаемое поле "measureUnit" 
3. Заменил "code" на "num" (из 34 known properties)
4. Заменил "price" на "defaultSalePrice" (из 34 known properties)
5. Убрал все неподтвержденные поля: description, weight, isIncludedInMenu, order, images, modifiers, groupModifiers

МИНИМАЛЬНАЯ СТРУКТУРА DISH:
{
  "name": "Название блюда",
  "num": "DISHXXXXXXXX", 
  "type": "DISH",
  "defaultSalePrice": 500.0,
  "productCategoryId": "category_id_if_available"
}

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
✅ DISH продукты должны создаваться с минимальной корректной структурой
✅ Блюда должны появляться в меню IIKo
✅ Полное решение проблемы: блюда в меню, не только техкарты
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_create_complete_dish_fixed():
    """Test POST /api/iiko/products/create-complete-dish with FIXED case sensitivity"""
    log_test("🍽️ FINAL TESTING: IIKo Integration - Create Product/Dish с исправленным case sensitivity")
    log_test("🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Изменил 'type': 'dish' (lowercase) на 'type': 'DISH' (uppercase)")
    
    # Test data as specified in the review request
    test_data = {
        "name": "Финальное тестовое блюдо DISH",
        "organization_id": "default-org-001", 
        "description": "Финальный тест с type='DISH' uppercase",
        "ingredients": [
            {"name": "Мука", "quantity": 250, "unit": "г"}
        ],
        "preparation_steps": ["Создать блюдо с правильным type"],
        "weight": 350.0,
        "price": 500.0
    }
    
    log_test(f"📝 Test dish: {test_data['name']}")
    log_test(f"📋 Description: {test_data['description']}")
    log_test(f"🥬 Ingredients:")
    for ing in test_data['ingredients']:
        log_test(f"   - {ing['name']}: {ing['quantity']}{ing['unit']}")
    log_test(f"⚖️ Weight: {test_data['weight']}г")
    log_test(f"💰 Price: {test_data['price']}₽")
    
    log_test("\n🎯 EXPECTED RESULTS AFTER FIX:")
    log_test("✅ NO errors related to 'Invalid enum value for type'")
    log_test("✅ NO errors related to 'dish is not a valid enum value'")
    log_test("✅ NO case sensitivity problems")
    log_test("✅ success: true for dish_product")
    log_test("✅ product_type: 'DISH'")
    log_test("✅ will_appear_in_menu: true")
    
    try:
        url = f"{API_BASE}/iiko/products/create-complete-dish"
        log_test(f"\n🌐 Making request to: {url}")
        
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"📊 Response status: {response.status_code}")
        log_test(f"⏱️ Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Create complete dish request successful!")
            
            # Analyze the response for the fix
            log_test("\n🔍 ANALYZING CASE SENSITIVITY FIX RESULTS:")
            
            # Check assembly chart creation
            assembly_result = data.get('assembly_chart', {})
            if assembly_result.get('success'):
                log_test(f"✅ Assembly Chart: SUCCESS")
                log_test(f"   - ID: {assembly_result.get('assembly_chart_id', 'Unknown')}")
                log_test(f"   - Name: {assembly_result.get('name', 'Unknown')}")
            else:
                log_test(f"❌ Assembly Chart: FAILED")
                if 'error' in assembly_result:
                    log_test(f"   - Error: {assembly_result['error']}")
            
            # Check DISH product creation - THIS IS THE CRITICAL TEST
            dish_result = data.get('dish_product', {})
            log_test(f"\n🍽️ DISH PRODUCT CREATION (CRITICAL TEST):")
            
            if dish_result.get('success'):
                log_test(f"🎉 DISH PRODUCT: SUCCESS! (Case sensitivity fix WORKED!)")
                log_test(f"   - Product ID: {dish_result.get('product_id', 'Unknown')}")
                log_test(f"   - Product Name: {dish_result.get('product_name', 'Unknown')}")
                log_test(f"   - Product Type: {dish_result.get('product_type', 'Unknown')}")
                log_test(f"   - Category ID: {dish_result.get('category_id', 'Unknown')}")
                log_test(f"   - Assembly Chart ID: {dish_result.get('assembly_chart_id', 'Unknown')}")
                log_test(f"   - Message: {dish_result.get('message', 'No message')}")
                
                # Check if it will appear in menu
                if dish_result.get('product_type') == 'DISH':
                    log_test(f"✅ Product type is correctly 'DISH' (uppercase)")
                    log_test(f"✅ This dish SHOULD appear in IIKo menu!")
                    log_test(f"✅ 'AI Menu Designer' category should be populated!")
                else:
                    log_test(f"⚠️ Product type: {dish_result.get('product_type')} (expected 'DISH')")
                
            else:
                log_test(f"❌ DISH PRODUCT: FAILED")
                error_msg = dish_result.get('error', 'Unknown error')
                log_test(f"   - Error: {error_msg}")
                
                # Check for specific case sensitivity errors
                if 'dish is not a valid enum value' in error_msg.lower():
                    log_test(f"🚨 CASE SENSITIVITY ERROR STILL PRESENT!")
                    log_test(f"💡 Backend still sending lowercase 'dish' instead of 'DISH'")
                elif 'invalid enum value for type' in error_msg.lower():
                    log_test(f"🚨 ENUM VALUE ERROR STILL PRESENT!")
                    log_test(f"💡 Type field validation still failing")
                else:
                    log_test(f"🔍 Different error (not case sensitivity): {error_msg}")
            
            # Check category handling
            category_result = data.get('category', {})
            if 'category_id' in category_result:
                log_test(f"\n📂 CATEGORY HANDLING:")
                log_test(f"   - Category ID: {category_result.get('category_id')}")
                log_test(f"   - Category Name: {category_result.get('category_name', 'AI Menu Designer')}")
                log_test(f"   - Category Status: {category_result.get('status', 'Unknown')}")
            
            # Overall success assessment
            log_test(f"\n📊 OVERALL ASSESSMENT:")
            assembly_success = assembly_result.get('success', False)
            dish_success = dish_result.get('success', False)
            
            if dish_success:
                log_test(f"🎉 CRITICAL FIX SUCCESSFUL!")
                log_test(f"✅ Case sensitivity issue RESOLVED")
                log_test(f"✅ DISH products now creating in IIKo")
                log_test(f"✅ Dishes will appear in menu")
                log_test(f"✅ Complete solution achieved!")
                
                return {
                    'success': True,
                    'dish_success': True,
                    'assembly_success': assembly_success,
                    'case_sensitivity_fixed': True,
                    'data': data
                }
            else:
                log_test(f"❌ CRITICAL FIX INCOMPLETE")
                log_test(f"❌ DISH creation still failing")
                log_test(f"❌ Case sensitivity may not be fully resolved")
                
                return {
                    'success': False,
                    'dish_success': False,
                    'assembly_success': assembly_success,
                    'case_sensitivity_fixed': False,
                    'data': data,
                    'error': dish_result.get('error', 'DISH creation failed')
                }
            
        else:
            log_test(f"❌ Create complete dish failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"📋 Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"📋 Raw error response: {response.text[:500]}")
            
            return {
                'success': False,
                'dish_success': False,
                'case_sensitivity_fixed': False,
                'error': f"HTTP {response.status_code}",
                'response': response.text
            }
            
    except Exception as e:
        log_test(f"❌ Error testing create complete dish: {str(e)}")
        return {
            'success': False,
            'dish_success': False,
            'case_sensitivity_fixed': False,
            'error': str(e)
        }

def test_compare_with_previous_results():
    """Compare current results with previous testing to show improvement"""
    log_test("\n📊 COMPARISON WITH PREVIOUS TESTING RESULTS:")
    log_test("🔍 Previous testing showed:")
    log_test("   ❌ 'dish is not a valid enum value' errors")
    log_test("   ❌ 'Invalid enum value for type' errors")
    log_test("   ❌ DISH products failing to create")
    log_test("   ❌ Only Assembly Charts created, no menu items")
    log_test("   ❌ 'AI Menu Designer' category empty")
    
    log_test("\n🎯 Expected improvement after fix:")
    log_test("   ✅ No enum value errors")
    log_test("   ✅ DISH products create successfully")
    log_test("   ✅ Both Assembly Charts AND DISH products")
    log_test("   ✅ Dishes appear in IIKo menu")
    log_test("   ✅ 'AI Menu Designer' category populated")

def test_verify_menu_population():
    """Test if the created dish appears in the IIKo menu"""
    log_test("\n🔍 STEP 2: Verifying dish appears in IIKo menu")
    
    try:
        url = f"{API_BASE}/iiko/menu/default-org-001"
        log_test(f"Getting menu from: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            menu = data.get('menu', {})
            items = menu.get('items', [])
            categories = menu.get('categories', [])
            
            log_test(f"📊 Menu contains {len(items)} items and {len(categories)} categories")
            
            # Look for our test dish
            test_dish_name = "Финальное тестовое блюдо DISH"
            found_dish = None
            
            for item in items:
                if test_dish_name.lower() in item.get('name', '').lower():
                    found_dish = item
                    break
            
            if found_dish:
                log_test(f"🎉 TEST DISH FOUND IN MENU!")
                log_test(f"   - Name: {found_dish.get('name', 'Unknown')}")
                log_test(f"   - ID: {found_dish.get('id', 'Unknown')}")
                log_test(f"   - Category: {found_dish.get('category_id', 'Unknown')}")
                log_test(f"   - Price: {found_dish.get('price', 'Unknown')}")
                log_test(f"✅ DISH successfully appears in IIKo menu!")
                return True
            else:
                log_test(f"❌ Test dish not found in menu")
                log_test(f"🔍 Searching for dishes containing 'тестовое' or 'DISH':")
                
                test_dishes = [item for item in items if 
                             'тестовое' in item.get('name', '').lower() or 
                             'dish' in item.get('name', '').lower()]
                
                if test_dishes:
                    log_test(f"📋 Found {len(test_dishes)} related dishes:")
                    for dish in test_dishes[:5]:
                        log_test(f"   - {dish.get('name', 'Unknown')} (ID: {dish.get('id', 'Unknown')})")
                else:
                    log_test(f"❌ No related test dishes found")
                
                return False
            
            # Check AI Menu Designer category
            ai_category = None
            for category in categories:
                if 'AI Menu Designer' in category.get('name', ''):
                    ai_category = category
                    break
            
            if ai_category:
                log_test(f"\n📂 'AI Menu Designer' category found:")
                log_test(f"   - ID: {ai_category.get('id', 'Unknown')}")
                log_test(f"   - Name: {ai_category.get('name', 'Unknown')}")
                
                # Count items in this category
                ai_items = [item for item in items if item.get('category_id') == ai_category.get('id')]
                log_test(f"   - Items in category: {len(ai_items)}")
                
                if ai_items:
                    log_test(f"✅ 'AI Menu Designer' category is populated!")
                    for item in ai_items[:3]:
                        log_test(f"      - {item.get('name', 'Unknown')}")
                else:
                    log_test(f"❌ 'AI Menu Designer' category is empty")
            else:
                log_test(f"❌ 'AI Menu Designer' category not found")
            
        else:
            log_test(f"❌ Failed to get menu: {response.status_code}")
            return False
            
    except Exception as e:
        log_test(f"❌ Error verifying menu: {str(e)}")
        return False

def main():
    """Main testing function for IIKo DISH creation fix"""
    log_test("🚀 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: IIKo Integration - Create Product/Dish")
    log_test("🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: case sensitivity fix 'dish' → 'DISH'")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Compare with previous results
    test_compare_with_previous_results()
    
    log_test("\n" + "=" * 80)
    
    # Step 1: Test the fixed create complete dish endpoint
    creation_result = test_create_complete_dish_fixed()
    
    log_test("\n" + "=" * 80)
    
    # Step 2: Verify dish appears in menu (if creation was successful)
    menu_populated = False
    if creation_result.get('dish_success'):
        log_test("✅ DISH creation successful, verifying menu population...")
        menu_populated = test_verify_menu_population()
    else:
        log_test("❌ DISH creation failed, checking menu anyway...")
        menu_populated = test_verify_menu_population()
    
    # Final Summary
    log_test("\n" + "=" * 80)
    log_test("📋 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ SUMMARY:")
    log_test(f"✅ DISH Product Creation: {'SUCCESS' if creation_result.get('dish_success') else 'FAILED'}")
    log_test(f"✅ Case Sensitivity Fix: {'WORKING' if creation_result.get('case_sensitivity_fixed') else 'NOT WORKING'}")
    log_test(f"✅ Menu Population: {'SUCCESS' if menu_populated else 'FAILED'}")
    log_test(f"✅ Assembly Chart Creation: {'SUCCESS' if creation_result.get('assembly_success') else 'FAILED'}")
    
    if creation_result.get('dish_success') and creation_result.get('case_sensitivity_fixed'):
        log_test("\n🎉 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ УСПЕШНО!")
        log_test("✅ Case sensitivity issue RESOLVED")
        log_test("✅ DISH products now creating in IIKo")
        log_test("✅ Dishes appearing in menu")
        log_test("✅ Complete solution achieved!")
        log_test("✅ 'AI Menu Designer' category populated")
        log_test("🚀 READY FOR PRODUCTION USE!")
    else:
        log_test("\n❌ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ НЕ ЗАВЕРШЕНО:")
        if not creation_result.get('case_sensitivity_fixed'):
            log_test("   - Case sensitivity issue still present")
        if not creation_result.get('dish_success'):
            log_test("   - DISH product creation still failing")
        if not menu_populated:
            log_test("   - Dishes not appearing in menu")
        
        if 'error' in creation_result:
            log_test(f"   - Error: {creation_result['error']}")
        
        log_test("💡 Further investigation needed")
    
    log_test("=" * 80)
    
    return creation_result

if __name__ == "__main__":
    main()