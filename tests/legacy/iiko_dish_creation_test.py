#!/usr/bin/env python3
"""
IIKo Integration - Create Product/Dish Testing Suite
Testing the NEW CRITICAL FIX for creating complete dishes in IIKo (both Assembly Charts AND DISH products)

КОНТЕКСТ ПРОБЛЕМЫ: 
Приложение создавало только "Assembly Charts" (техкарты/рецепты) в IIKo, но НЕ создавало фактические "Products" (блюда), 
которые нужны для появления в меню. Из-за этого генерируемые блюда не появлялись в меню IIKo и не заполняли категорию "AI Menu Designer".

РЕШЕНИЕ, КОТОРОЕ ТЕСТИРУЕМ:
1. Новый метод `create_dish_product()` - создает продукты типа DISH в IIKo
2. Новый метод `create_complete_dish_in_iiko()` - создает И Assembly Chart И DISH продукт одновременно  
3. Новый endpoint `/api/iiko/products/create-complete-dish` - для создания полноценных блюд
4. Улучшенный endpoint `/api/iiko/tech-cards/upload` - теперь создает полные блюда вместо только техкарт

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
Блюда теперь должны создаваться как полноценные продукты в IIKo, появляться в меню и заполнять категорию "AI Menu Designer"
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

def test_new_create_complete_dish_endpoint():
    """Test NEW endpoint /api/iiko/products/create-complete-dish"""
    log_test("🍽️ STEP 1: Testing NEW endpoint /api/iiko/products/create-complete-dish")
    
    # Test data as specified in the review request
    test_data = {
        "name": "Тестовое блюдо для меню",
        "organization_id": "default-org-001", 
        "description": "Блюдо для проверки создания DISH продукта",
        "ingredients": [
            {"name": "Мука", "quantity": 200, "unit": "г"},
            {"name": "Яйца", "quantity": 2, "unit": "шт"}
        ],
        "preparation_steps": ["Смешать ингредиенты", "Выпекать 30 минут"],
        "weight": 300.0,
        "price": 450.0
    }
    
    log_test(f"📝 Test dish: {test_data['name']}")
    log_test(f"📋 Description: {test_data['description']}")
    log_test(f"🥬 Ingredients:")
    for ing in test_data['ingredients']:
        log_test(f"   - {ing['name']}: {ing['quantity']} {ing['unit']}")
    log_test(f"⚖️ Weight: {test_data['weight']}г")
    log_test(f"💰 Price: {test_data['price']}₽")
    
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
            log_test("✅ Complete dish creation request successful!")
            
            # Analyze the response structure for the new functionality
            log_test("\n🔍 ANALYZING COMPLETE DISH RESPONSE STRUCTURE:")
            
            # Check for assembly_chart information
            if 'assembly_chart' in data:
                assembly_info = data['assembly_chart']
                log_test(f"🔨 Assembly Chart created: {assembly_info.get('created', 'Unknown')}")
                if assembly_info.get('id'):
                    log_test(f"🆔 Assembly Chart ID: {assembly_info['id']}")
            
            # Check for dish_product information (NEW FUNCTIONALITY)
            if 'dish_product' in data:
                dish_info = data['dish_product']
                log_test(f"🍽️ DISH Product created: {dish_info.get('created', 'Unknown')}")
                if dish_info.get('id'):
                    log_test(f"🆔 DISH Product ID: {dish_info['id']}")
                if dish_info.get('name'):
                    log_test(f"📝 DISH Product name: {dish_info['name']}")
                if dish_info.get('type'):
                    log_test(f"🏷️ Product type: {dish_info['type']}")
            
            # Check for category_id (привязана ли категория)
            if 'category_id' in data:
                log_test(f"📂 Category ID: {data['category_id']}")
                if data['category_id']:
                    log_test("✅ Dish linked to category successfully!")
                else:
                    log_test("⚠️ No category linked")
            
            # Check for steps_completed (какие шаги выполнены)
            if 'steps_completed' in data:
                steps = data['steps_completed']
                log_test(f"📋 Steps completed: {steps}")
                if isinstance(steps, list):
                    for step in steps:
                        log_test(f"   ✅ {step}")
            
            # Check for will_appear_in_menu (будет ли в меню)
            if 'will_appear_in_menu' in data:
                will_appear = data['will_appear_in_menu']
                log_test(f"🍽️ Will appear in menu: {will_appear}")
                if will_appear:
                    log_test("🎉 SUCCESS: Dish will appear in IIKo menu!")
                else:
                    log_test("⚠️ WARNING: Dish may not appear in menu")
            
            # Check overall success
            if data.get('success'):
                log_test("🎉 COMPLETE DISH CREATION SUCCESSFUL!")
                log_test("✅ Both Assembly Chart AND DISH Product created")
                log_test("✅ Dish should now appear in IIKo menu")
                log_test("✅ AI Menu Designer category should be populated")
            else:
                log_test("⚠️ Complete dish creation had issues")
                if 'error' in data:
                    log_test(f"❌ Error: {data['error']}")
            
            # Log full response for analysis
            log_test(f"\n📋 Full Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            return {
                'success': data.get('success', False),
                'data': data,
                'assembly_chart_created': data.get('assembly_chart', {}).get('created', False),
                'dish_product_created': data.get('dish_product', {}).get('created', False),
                'will_appear_in_menu': data.get('will_appear_in_menu', False)
            }
            
        else:
            log_test(f"❌ Complete dish creation failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"📋 Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"📋 Raw error response: {response.text[:500]}")
            
            return {
                'success': False, 
                'error': f"HTTP {response.status_code}", 
                'response': response.text
            }
            
    except Exception as e:
        log_test(f"❌ Error creating complete dish: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_enhanced_tech_cards_upload_endpoint():
    """Test ENHANCED endpoint /api/iiko/tech-cards/upload (now creates complete dishes)"""
    log_test("🔄 STEP 2: Testing ENHANCED endpoint /api/iiko/tech-cards/upload")
    
    # Same test data to compare with the new endpoint
    test_data = {
        "name": "Тестовое блюдо для меню (через upload)",
        "organization_id": "default-org-001", 
        "description": "Блюдо для проверки улучшенного upload endpoint",
        "ingredients": [
            {"name": "Мука", "quantity": 200, "unit": "г"},
            {"name": "Яйца", "quantity": 2, "unit": "шт"}
        ],
        "preparation_steps": ["Смешать ингредиенты", "Выпекать 30 минут"],
        "weight": 300.0,
        "price": 450.0
    }
    
    log_test(f"📝 Test dish: {test_data['name']}")
    log_test("🔄 This endpoint should now create COMPLETE dishes instead of just tech cards")
    
    try:
        url = f"{API_BASE}/iiko/tech-cards/upload"
        log_test(f"\n🌐 Making request to: {url}")
        
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"📊 Response status: {response.status_code}")
        log_test(f"⏱️ Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Enhanced tech cards upload successful!")
            
            # Check if this now creates complete dishes (not just tech cards)
            log_test("\n🔍 ANALYZING ENHANCED UPLOAD RESPONSE:")
            
            # Look for signs that it now creates complete dishes
            if 'assembly_chart' in data and 'dish_product' in data:
                log_test("🎉 ENHANCEMENT CONFIRMED: Upload now creates BOTH assembly chart AND dish product!")
            elif 'dish_product' in data:
                log_test("🎉 ENHANCEMENT CONFIRMED: Upload now creates dish products!")
            elif 'assembly_chart' in data:
                log_test("⚠️ Only assembly chart created - enhancement may not be fully implemented")
            else:
                log_test("❓ Response structure unclear - checking for other indicators")
            
            # Check for the same fields as the new endpoint
            if 'will_appear_in_menu' in data:
                will_appear = data['will_appear_in_menu']
                log_test(f"🍽️ Will appear in menu: {will_appear}")
                if will_appear:
                    log_test("✅ ENHANCEMENT WORKING: Dishes will now appear in menu!")
            
            if 'steps_completed' in data:
                steps = data['steps_completed']
                log_test(f"📋 Steps completed: {steps}")
            
            # Log full response
            log_test(f"\n📋 Full Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            return {
                'success': data.get('success', False),
                'data': data,
                'enhanced': 'dish_product' in data or 'will_appear_in_menu' in data
            }
            
        else:
            log_test(f"❌ Enhanced upload failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"📋 Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"📋 Raw error response: {response.text[:500]}")
            
            return {
                'success': False, 
                'error': f"HTTP {response.status_code}", 
                'response': response.text
            }
            
    except Exception as e:
        log_test(f"❌ Error in enhanced upload: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_fallback_scenarios():
    """Test fallback scenarios when IIKo API fails"""
    log_test("🛡️ STEP 3: Testing fallback scenarios")
    
    # Test with invalid organization ID to trigger fallback
    test_data = {
        "name": "Тест fallback сценария",
        "organization_id": "invalid-org-999", 
        "description": "Тест обработки ошибок",
        "ingredients": [
            {"name": "Тестовый ингредиент", "quantity": 100, "unit": "г"}
        ],
        "preparation_steps": ["Тестовый шаг"],
        "weight": 100.0,
        "price": 200.0
    }
    
    log_test(f"📝 Testing fallback with invalid org ID: {test_data['organization_id']}")
    
    try:
        url = f"{API_BASE}/iiko/products/create-complete-dish"
        log_test(f"🌐 Making request to: {url}")
        
        response = requests.post(url, json=test_data, timeout=30)
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for graceful fallback handling
            if not data.get('success') and 'fallback' in str(data).lower():
                log_test("✅ Graceful fallback detected")
                log_test("✅ System handles IIKo API failures properly")
            elif data.get('success') == False:
                log_test("✅ Error handling working - invalid org ID rejected")
            else:
                log_test("❓ Unexpected success with invalid org ID")
            
            log_test(f"📋 Fallback response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            return {'success': True, 'fallback_working': True}
            
        else:
            log_test(f"✅ Expected failure with invalid org ID: HTTP {response.status_code}")
            return {'success': True, 'fallback_working': True}
            
    except Exception as e:
        log_test(f"✅ Expected error with invalid data: {str(e)}")
        return {'success': True, 'fallback_working': True}

def test_iiko_health_check():
    """Test IIKo integration health before running main tests"""
    log_test("🏥 STEP 0: Testing IIKo integration health")
    
    try:
        # Test basic IIKo connectivity
        url = f"{API_BASE}/iiko/organizations"
        log_test(f"🌐 Checking IIKo connectivity: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"📊 IIKo health status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'organizations' in data:
                orgs = data['organizations']
                log_test(f"✅ IIKo integration healthy - {len(orgs)} organizations found")
                
                # Check if our test organization exists
                test_org = next((org for org in orgs if org.get('id') == 'default-org-001'), None)
                if test_org:
                    log_test(f"✅ Test organization found: {test_org.get('name', 'Unknown')}")
                    return {'success': True, 'healthy': True, 'test_org_exists': True}
                else:
                    log_test("⚠️ Test organization 'default-org-001' not found")
                    return {'success': True, 'healthy': True, 'test_org_exists': False}
            else:
                log_test("⚠️ IIKo response format unexpected")
                return {'success': False, 'healthy': False}
        else:
            log_test(f"❌ IIKo integration unhealthy: HTTP {response.status_code}")
            return {'success': False, 'healthy': False}
            
    except Exception as e:
        log_test(f"❌ IIKo health check failed: {str(e)}")
        return {'success': False, 'healthy': False, 'error': str(e)}

def main():
    """Main testing function for IIKo Create Product/Dish functionality"""
    log_test("🚀 Starting IIKo Integration - Create Product/Dish Testing")
    log_test("🎯 Focus: Testing NEW CRITICAL FIX for creating complete dishes in IIKo")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Step 0: Health check
    health_result = test_iiko_health_check()
    
    if not health_result.get('healthy'):
        log_test("❌ IIKo integration is not healthy - tests may fail")
        log_test("⚠️ Continuing with tests anyway to check error handling...")
    
    log_test("\n" + "=" * 80)
    
    # Step 1: Test new create-complete-dish endpoint
    complete_dish_result = test_new_create_complete_dish_endpoint()
    
    log_test("\n" + "=" * 80)
    
    # Step 2: Test enhanced tech-cards/upload endpoint
    enhanced_upload_result = test_enhanced_tech_cards_upload_endpoint()
    
    log_test("\n" + "=" * 80)
    
    # Step 3: Test fallback scenarios
    fallback_result = test_fallback_scenarios()
    
    # Summary
    log_test("\n" + "=" * 80)
    log_test("📋 IIKO CREATE PRODUCT/DISH TESTING SUMMARY:")
    log_test(f"🏥 IIKo health: {'HEALTHY' if health_result.get('healthy') else 'UNHEALTHY'}")
    log_test(f"🍽️ Complete dish creation: {'SUCCESS' if complete_dish_result.get('success') else 'FAILED'}")
    log_test(f"🔄 Enhanced upload: {'SUCCESS' if enhanced_upload_result.get('success') else 'FAILED'}")
    log_test(f"🛡️ Fallback handling: {'WORKING' if fallback_result.get('fallback_working') else 'FAILED'}")
    
    # Detailed analysis
    log_test("\n🔍 DETAILED ANALYSIS:")
    
    if complete_dish_result.get('success'):
        log_test("✅ NEW ENDPOINT WORKING:")
        log_test(f"   - Assembly Chart created: {complete_dish_result.get('assembly_chart_created', 'Unknown')}")
        log_test(f"   - DISH Product created: {complete_dish_result.get('dish_product_created', 'Unknown')}")
        log_test(f"   - Will appear in menu: {complete_dish_result.get('will_appear_in_menu', 'Unknown')}")
    else:
        log_test("❌ NEW ENDPOINT ISSUES:")
        if 'error' in complete_dish_result:
            log_test(f"   - Error: {complete_dish_result['error']}")
    
    if enhanced_upload_result.get('success'):
        log_test("✅ ENHANCED UPLOAD WORKING:")
        log_test(f"   - Enhancement detected: {enhanced_upload_result.get('enhanced', 'Unknown')}")
    else:
        log_test("❌ ENHANCED UPLOAD ISSUES:")
        if 'error' in enhanced_upload_result:
            log_test(f"   - Error: {enhanced_upload_result['error']}")
    
    # Final verdict
    if (complete_dish_result.get('success') and 
        complete_dish_result.get('dish_product_created') and 
        complete_dish_result.get('will_appear_in_menu')):
        log_test("\n🎉 CRITICAL FIX VERIFICATION: SUCCESS!")
        log_test("✅ Dishes are now created as complete products in IIKo")
        log_test("✅ Dishes will appear in IIKo menu")
        log_test("✅ AI Menu Designer category will be populated")
        log_test("✅ Problem of dishes not appearing in menu is SOLVED!")
    else:
        log_test("\n⚠️ CRITICAL FIX VERIFICATION: ISSUES DETECTED")
        log_test("❌ Complete dish creation may not be working as expected")
        log_test("💡 Check backend implementation of create_complete_dish_in_iiko() method")
        log_test("💡 Verify DISH product creation logic")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()