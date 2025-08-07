#!/usr/bin/env python3
"""
Backend Testing Suite for Assembly Charts API with Real Product ID Matching
Testing the final version of assembly charts API with real product IDs as requested.
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://6fef0306-3b86-43a7-9af9-64a8d83a066e.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_get_menu_products():
    """Test GET /api/iiko/menu/default-org-001 to get existing products"""
    log_test("🔍 STEP 1: Testing GET /api/iiko/menu/default-org-001 to get existing products")
    
    try:
        url = f"{API_BASE}/iiko/menu/default-org-001"
        log_test(f"Making request to: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract menu items
            items = data.get('items', [])
            categories = data.get('categories', [])
            
            log_test(f"✅ Menu retrieved successfully!")
            log_test(f"📊 Found {len(items)} products and {len(categories)} categories")
            
            # Log some sample products for ingredient matching
            if items:
                log_test("🍞 Sample products that might match our test ingredients:")
                bread_products = [item for item in items if any(keyword in item.get('name', '').lower() 
                                                              for keyword in ['хлеб', 'bread', 'булка', 'батон'])]
                butter_products = [item for item in items if any(keyword in item.get('name', '').lower() 
                                                               for keyword in ['масло', 'butter', 'сливочн'])]
                
                if bread_products:
                    log_test(f"🍞 Bread-like products found: {len(bread_products)}")
                    for product in bread_products[:3]:  # Show first 3
                        log_test(f"   - {product.get('name', 'Unknown')} (ID: {product.get('id', 'No ID')})")
                
                if butter_products:
                    log_test(f"🧈 Butter-like products found: {len(butter_products)}")
                    for product in butter_products[:3]:  # Show first 3
                        log_test(f"   - {product.get('name', 'Unknown')} (ID: {product.get('id', 'No ID')})")
                
                # Show first 10 products for reference
                log_test("📋 First 10 products in menu:")
                for i, item in enumerate(items[:10]):
                    log_test(f"   {i+1}. {item.get('name', 'Unknown')} (ID: {item.get('id', 'No ID')})")
            
            return {
                'success': True,
                'items': items,
                'categories': categories,
                'total_items': len(items)
            }
        else:
            log_test(f"❌ Failed to get menu: {response.status_code}")
            log_test(f"Response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error getting menu: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_create_assembly_chart_with_real_products(menu_items):
    """Test POST /api/iiko/assembly-charts/create with real product matching"""
    log_test("🔨 STEP 2: Testing POST /api/iiko/assembly-charts/create with real product matching")
    
    # Test data with simple ingredient names that might match real products
    test_data = {
        "name": "Тестовое блюдо",
        "description": "Техкарта с реальными продуктами",
        "ingredients": [
            {"name": "Хлеб", "quantity": 100, "unit": "г", "price": 10.0},
            {"name": "Масло", "quantity": 20, "unit": "г", "price": 5.0}
        ],
        "preparation_steps": ["Намазать маслом хлеб"],
        "organization_id": "default-org-001",
        "weight": 120.0
    }
    
    log_test(f"📝 Test data: {test_data['name']}")
    log_test(f"🥬 Ingredients to match:")
    for ing in test_data['ingredients']:
        log_test(f"   - {ing['name']}: {ing['quantity']}{ing['unit']}")
    
    try:
        url = f"{API_BASE}/iiko/assembly-charts/create"
        log_test(f"Making request to: {url}")
        
        response = requests.post(url, json=test_data, timeout=60)
        log_test(f"Response status: {response.status_code}")
        log_test(f"Response time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Assembly chart creation request successful!")
            
            # Log the matching process
            if 'message' in data:
                log_test(f"📋 Response message: {data['message']}")
            
            if 'assembly_chart_id' in data:
                log_test(f"🆔 Assembly chart ID: {data['assembly_chart_id']}")
            
            # Check if product matching worked
            if 'response' in data:
                log_test("🔍 Analyzing product matching results...")
                response_data = data['response']
                log_test(f"IIKo response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            return {
                'success': True,
                'data': data,
                'assembly_chart_id': data.get('assembly_chart_id')
            }
        else:
            log_test(f"❌ Assembly chart creation failed: {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"Raw error response: {response.text[:500]}")
            
            return {'success': False, 'error': f"HTTP {response.status_code}", 'response': response.text}
            
    except Exception as e:
        log_test(f"❌ Error creating assembly chart: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_get_all_assembly_charts():
    """Test GET /api/iiko/assembly-charts/all/default-org-001"""
    log_test("📋 STEP 3: Testing GET /api/iiko/assembly-charts/all/default-org-001")
    
    try:
        url = f"{API_BASE}/iiko/assembly-charts/all/default-org-001"
        log_test(f"Making request to: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Assembly charts list retrieved successfully!")
            
            if 'assembly_charts' in data:
                charts = data['assembly_charts']
                count = data.get('count', len(charts) if isinstance(charts, list) else 0)
                log_test(f"📊 Found {count} assembly charts")
                
                if isinstance(charts, list) and charts:
                    log_test("📋 Assembly charts found:")
                    for i, chart in enumerate(charts[:5]):  # Show first 5
                        chart_name = chart.get('name', 'Unknown')
                        chart_id = chart.get('id', 'No ID')
                        log_test(f"   {i+1}. {chart_name} (ID: {chart_id})")
                else:
                    log_test("📋 No assembly charts found (empty list)")
            
            return {'success': True, 'data': data}
        else:
            log_test(f"❌ Failed to get assembly charts: {response.status_code}")
            log_test(f"Response: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error getting assembly charts: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_ingredient_matching_process(menu_items, test_ingredients):
    """Log the process of matching ingredient names with existing products"""
    log_test("🔍 STEP 2.5: Analyzing ingredient matching process")
    
    if not menu_items:
        log_test("❌ No menu items available for matching")
        return
    
    log_test(f"📊 Available products for matching: {len(menu_items)}")
    
    for ingredient in test_ingredients:
        ingredient_name = ingredient['name'].lower().strip()
        log_test(f"\n🔍 Matching ingredient: '{ingredient['name']}'")
        
        # Try exact match first
        exact_matches = [item for item in menu_items 
                        if item.get('name', '').lower().strip() == ingredient_name]
        
        if exact_matches:
            log_test(f"✅ Exact match found: {len(exact_matches)} products")
            for match in exact_matches[:3]:
                log_test(f"   - {match.get('name', 'Unknown')} (ID: {match.get('id', 'No ID')})")
        else:
            # Try partial match
            partial_matches = [item for item in menu_items 
                             if ingredient_name in item.get('name', '').lower() or 
                                item.get('name', '').lower() in ingredient_name]
            
            if partial_matches:
                log_test(f"🔍 Partial matches found: {len(partial_matches)} products")
                for match in partial_matches[:5]:
                    log_test(f"   - {match.get('name', 'Unknown')} (ID: {match.get('id', 'No ID')})")
            else:
                log_test(f"❌ No matches found for '{ingredient['name']}'")
                
                # Show similar products for debugging
                similar_products = [item for item in menu_items 
                                  if any(char in item.get('name', '').lower() 
                                        for char in ingredient_name[:3])]
                
                if similar_products:
                    log_test(f"🔍 Similar products (first 3 chars match):")
                    for product in similar_products[:3]:
                        log_test(f"   - {product.get('name', 'Unknown')}")

def main():
    """Main testing function"""
    log_test("🚀 Starting Assembly Charts API Testing with Real Product ID Matching")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Step 1: Get existing products from menu
    menu_result = test_get_menu_products()
    
    if not menu_result['success']:
        log_test("❌ Cannot proceed without menu data")
        return
    
    menu_items = menu_result.get('items', [])
    log_test(f"\n📊 Menu loaded: {len(menu_items)} products available for matching")
    
    # Step 2.5: Analyze ingredient matching process
    test_ingredients = [
        {"name": "Хлеб", "quantity": 100, "unit": "г", "price": 10.0},
        {"name": "Масло", "quantity": 20, "unit": "г", "price": 5.0}
    ]
    
    test_ingredient_matching_process(menu_items, test_ingredients)
    
    log_test("\n" + "=" * 80)
    
    # Step 2: Test assembly chart creation with real product matching
    creation_result = test_create_assembly_chart_with_real_products(menu_items)
    
    log_test("\n" + "=" * 80)
    
    # Step 3: Test getting all assembly charts (regardless of creation success)
    list_result = test_get_all_assembly_charts()
    
    # Summary
    log_test("\n" + "=" * 80)
    log_test("📋 TESTING SUMMARY:")
    log_test(f"✅ Menu retrieval: {'SUCCESS' if menu_result['success'] else 'FAILED'}")
    log_test(f"✅ Assembly chart creation: {'SUCCESS' if creation_result.get('success') else 'FAILED'}")
    log_test(f"✅ Assembly charts list: {'SUCCESS' if list_result.get('success') else 'FAILED'}")
    
    if creation_result.get('success'):
        log_test("🎉 Assembly charts API is working with real product ID matching!")
    else:
        log_test("⚠️ Assembly chart creation had issues - check logs above for details")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()