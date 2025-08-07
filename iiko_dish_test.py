#!/usr/bin/env python3
"""
IIKo Integration - Create Product/Dish Testing with CORRECTED Structure
Testing the fixed endpoint /api/iiko/products/create-complete-dish with corrected ProductDto structure.

Focus: Testing the corrected DISH creation structure according to official IIKo documentation:
- name, code, type='dish' (lowercase)
- measureUnit='порция', price, weight  
- isIncludedInMenu=true, order=1000
- productCategoryId, parentGroup (for categories)
- images=[], modifiers=[], groupModifiers=[]
- REMOVED invalid fields: active, deleted, defaultSalePrice, cookingPlace, assembly, measurementUnit='PORTION', tags, additionalInfo
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://a8a5672b-ce8b-43b7-b77c-996ec8e61bdd.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_corrected_dish_creation():
    """Test POST /api/iiko/products/create-complete-dish with CORRECTED structure"""
    log_test("🍽️ TESTING CORRECTED DISH CREATION STRUCTURE")
    log_test("=" * 80)
    
    # Test data from review request
    test_data = {
        "name": "Исправленное тестовое блюдо",
        "organization_id": "default-org-001", 
        "description": "Тест с исправленной структурой ProductDto",
        "ingredients": [
            {"name": "Мука", "quantity": 200, "unit": "г"},
            {"name": "Яйца", "quantity": 2, "unit": "шт"}
        ],
        "preparation_steps": ["Смешать ингредиенты", "Выпекать 30 минут"],
        "weight": 300.0,
        "price": 450.0
    }
    
    try:
        url = f"{API_BASE}/iiko/products/create-complete-dish"
        log_test(f"🔗 Making request to: {url}")
        log_test(f"📋 Test data: {test_data['name']} - {test_data['price']}₽")
        
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=60)
        duration = time.time() - start_time
        
        log_test(f"⏱️ Response time: {duration:.2f} seconds")
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                log_test(f"✅ SUCCESS: Endpoint responded with HTTP 200")
                
                # Check response structure
                log_test("\n🔍 ANALYZING RESPONSE STRUCTURE:")
                
                # Check for assembly chart creation
                assembly_result = data.get('assembly_chart_result', {})
                if assembly_result.get('success'):
                    log_test(f"✅ Assembly Chart: {assembly_result.get('message', 'Created successfully')}")
                    log_test(f"📋 Assembly Chart ID: {assembly_result.get('assembly_chart_id', 'N/A')}")
                else:
                    log_test(f"❌ Assembly Chart: {assembly_result.get('error', 'Failed')}")
                
                # Check for DISH product creation - THIS IS THE KEY TEST
                dish_result = data.get('dish_product_result', {})
                if dish_result.get('success'):
                    log_test(f"✅ DISH Product: {dish_result.get('message', 'Created successfully')}")
                    log_test(f"🍽️ DISH Product ID: {dish_result.get('product_id', 'N/A')}")
                    log_test(f"🍽️ DISH Product Name: {dish_result.get('product_name', 'N/A')}")
                    log_test(f"🍽️ DISH Product Type: {dish_result.get('product_type', 'N/A')}")
                    
                    # Verify corrected structure fields
                    log_test("\n🔍 VERIFYING CORRECTED DISH STRUCTURE:")
                    
                    # Check if response contains structure details
                    if 'prepared_dish_data' in dish_result:
                        dish_data = dish_result['prepared_dish_data']
                        log_test(f"✅ type: {dish_data.get('type', 'MISSING')} (should be 'dish')")
                        log_test(f"✅ measureUnit: {dish_data.get('measureUnit', 'MISSING')} (should be 'порция')")
                        log_test(f"✅ isIncludedInMenu: {dish_data.get('isIncludedInMenu', 'MISSING')} (should be true)")
                        
                        # Check for REMOVED invalid fields
                        invalid_fields = ['active', 'deleted', 'defaultSalePrice', 'cookingPlace', 'assembly', 'measurementUnit', 'tags', 'additionalInfo']
                        for field in invalid_fields:
                            if field in dish_data:
                                log_test(f"❌ INVALID FIELD FOUND: {field} = {dish_data[field]} (should be removed)")
                            else:
                                log_test(f"✅ INVALID FIELD REMOVED: {field}")
                    
                else:
                    log_test(f"❌ DISH Product: {dish_result.get('error', 'Failed')}")
                    log_test(f"📝 Note: {dish_result.get('note', 'No additional info')}")
                    
                    # Check if fallback was used
                    if 'fallback_instructions' in dish_result:
                        log_test(f"🔄 Fallback: {dish_result.get('fallback_instructions', 'N/A')}")
                
                # Check category handling
                category_result = data.get('category_result', {})
                if category_result.get('success'):
                    log_test(f"✅ Category: {category_result.get('message', 'Handled successfully')}")
                else:
                    log_test(f"ℹ️ Category: {category_result.get('note', 'Using existing or default')}")
                
                # Overall assessment
                log_test("\n🎯 OVERALL ASSESSMENT:")
                if dish_result.get('success'):
                    log_test("✅ CORRECTED DISH STRUCTURE TEST: PASSED")
                    log_test("✅ DISH products should now be created with proper structure")
                else:
                    log_test("❌ CORRECTED DISH STRUCTURE TEST: FAILED")
                    log_test("❌ DISH creation still has issues despite structure corrections")
                
                return data
                
            except json.JSONDecodeError as e:
                log_test(f"❌ JSON parsing failed: {str(e)}")
                log_test(f"📄 Raw response: {response.text[:500]}")
                return None
                
        else:
            log_test(f"❌ HTTP Error: {response.status_code}")
            log_test(f"📄 Error response: {response.text[:500]}")
            return None
            
    except requests.exceptions.Timeout:
        log_test("❌ Request timeout (60 seconds)")
        return None
    except requests.exceptions.RequestException as e:
        log_test(f"❌ Request failed: {str(e)}")
        return None

def test_fallback_minimal_structure():
    """Test if the fallback minimal structure works when main structure fails"""
    log_test("\n🔄 TESTING FALLBACK MINIMAL STRUCTURE")
    log_test("=" * 80)
    
    # Simpler test data to trigger fallback
    minimal_test_data = {
        "name": "Минимальное тестовое блюдо",
        "organization_id": "default-org-001",
        "description": "Тест минимальной структуры fallback",
        "weight": 250.0,
        "price": 350.0
    }
    
    try:
        url = f"{API_BASE}/iiko/products/create-complete-dish"
        log_test(f"🔗 Making request to: {url}")
        log_test(f"📋 Minimal test data: {minimal_test_data['name']}")
        
        response = requests.post(url, json=minimal_test_data, timeout=60)
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            dish_result = data.get('dish_product_result', {})
            
            if dish_result.get('success'):
                log_test("✅ FALLBACK MINIMAL STRUCTURE: WORKING")
                log_test(f"🍽️ Minimal DISH created: {dish_result.get('product_name', 'N/A')}")
            else:
                log_test("❌ FALLBACK MINIMAL STRUCTURE: FAILED")
                log_test(f"📝 Error: {dish_result.get('error', 'Unknown error')}")
            
            return data
        else:
            log_test(f"❌ Minimal structure test failed: {response.status_code}")
            return None
            
    except Exception as e:
        log_test(f"❌ Minimal structure test error: {str(e)}")
        return None

def compare_with_previous_results():
    """Compare current results with previous testing to show improvement"""
    log_test("\n📊 COMPARISON WITH PREVIOUS RESULTS")
    log_test("=" * 80)
    
    log_test("🔍 PREVIOUS ISSUES (from test_result.md):")
    log_test("❌ IIKo ProductDto only accepts 34 specific fields")
    log_test("❌ Backend sent invalid fields like 'active', 'deleted', 'type', 'description', 'weight', 'cookingPlace'")
    log_test("❌ Most DISH creation endpoints returned 404 (not available)")
    log_test("❌ Only /resto/api/v2/entities/products/save accessible but rejected structure")
    log_test("❌ Existing IIKo menu has 3,153 products but ZERO DISH type products")
    
    log_test("\n🔧 APPLIED FIXES:")
    log_test("✅ Corrected ProductDto structure using official IIKo documentation")
    log_test("✅ Using CORRECT fields: name, code, type='dish', measureUnit='порция', price, weight")
    log_test("✅ Added proper menu integration: isIncludedInMenu=true, order=1000")
    log_test("✅ REMOVED invalid fields: active, deleted, defaultSalePrice, cookingPlace, assembly")
    log_test("✅ Added fallback to minimal structure if main structure fails")
    
    log_test("\n🎯 EXPECTED IMPROVEMENTS:")
    log_test("✅ DISH products should now pass IIKo validation")
    log_test("✅ Should progress further in creation process without structure errors")
    log_test("✅ Better error handling with meaningful fallback options")

def main():
    """Main testing function"""
    log_test("🚀 STARTING IIKO DISH CREATION TESTING WITH CORRECTED STRUCTURE")
    log_test("=" * 80)
    log_test(f"🔗 Backend URL: {BACKEND_URL}")
    log_test(f"🔗 API Base: {API_BASE}")
    log_test(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Compare with previous results first
    compare_with_previous_results()
    
    # Test corrected dish creation
    result1 = test_corrected_dish_creation()
    
    # Test fallback minimal structure
    result2 = test_fallback_minimal_structure()
    
    # Final summary
    log_test("\n🎯 FINAL TESTING SUMMARY")
    log_test("=" * 80)
    
    if result1:
        dish_result = result1.get('dish_product_result', {})
        if dish_result.get('success'):
            log_test("✅ CORRECTED DISH STRUCTURE: WORKING")
            log_test("✅ Main agent's fixes have resolved the ProductDto structure issues")
        else:
            log_test("❌ CORRECTED DISH STRUCTURE: STILL HAS ISSUES")
            log_test("❌ Further investigation needed despite structure corrections")
    else:
        log_test("❌ CORRECTED DISH STRUCTURE: ENDPOINT NOT ACCESSIBLE")
    
    if result2:
        dish_result2 = result2.get('dish_product_result', {})
        if dish_result2.get('success'):
            log_test("✅ FALLBACK MINIMAL STRUCTURE: WORKING")
        else:
            log_test("❌ FALLBACK MINIMAL STRUCTURE: NOT WORKING")
    
    log_test("\n🏁 TESTING COMPLETED")
    log_test("📋 Results logged above for main agent review")

if __name__ == "__main__":
    main()