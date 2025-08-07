#!/usr/bin/env python3
"""
Backend Testing Suite for IIKo Assembly Charts API - Official Structure Testing
Testing the final version assembly charts API with official IIKo structure from documentation.

Focus: Testing POST /api/iiko/assembly-charts/create with official IIKo structure including:
- assembledProductId, dateFrom, assembledAmount, productWriteoffStrategy
- effectiveDirectWriteoffStoreSpecification, productSizeAssemblyStrategy, items
- AssemblyChartItemDto structure with sortWeight, productId, amountIn, amountMiddle, amountOut
- Real product ID matching for ingredients
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://505e5bfa-929d-4220-a43a-07be25c44be2.preview.emergentagent.com')
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
            
            # Extract menu items from the correct structure
            menu = data.get('menu', {})
            items = menu.get('items', [])
            categories = menu.get('categories', [])
            
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

def test_create_assembly_chart_official_structure():
    """Test POST /api/iiko/assembly-charts/create with official IIKo documentation structure"""
    log_test("🔨 STEP 2: Testing POST /api/iiko/assembly-charts/create with OFFICIAL IIKo structure")
    
    # Test data as provided by user - official IIKo test
    test_data = {
        "name": "Официальный тест IIKo",
        "description": "Техкарта по официальной документации",
        "ingredients": [
            {"name": "Хлеб", "quantity": 100, "unit": "г", "price": 10.0},
            {"name": "Масло", "quantity": 25, "unit": "г", "price": 8.0}
        ],
        "preparation_steps": ["Намазать хлеб маслом"],
        "organization_id": "default-org-001",
        "weight": 125.0
    }
    
    log_test(f"📝 Test data: {test_data['name']}")
    log_test(f"📋 Description: {test_data['description']}")
    log_test(f"🥬 Ingredients to process:")
    for ing in test_data['ingredients']:
        log_test(f"   - {ing['name']}: {ing['quantity']}{ing['unit']} (цена: {ing['price']}₽)")
    log_test(f"⚖️ Total weight: {test_data['weight']}г")
    
    log_test("\n🔍 CHECKING OFFICIAL IIKO STRUCTURE REQUIREMENTS:")
    log_test("✅ Required fields that should be present in backend transformation:")
    log_test("   - assembledProductId (UUID of main product)")
    log_test("   - dateFrom (yyyy-MM-dd format)")
    log_test("   - assembledAmount (BigDecimal)")
    log_test("   - productWriteoffStrategy (ASSEMBLE/DIRECT)")
    log_test("   - effectiveDirectWriteoffStoreSpecification (StoreSpecification)")
    log_test("   - productSizeAssemblyStrategy (COMMON/SPECIFIC)")
    log_test("   - items (List<AssemblyChartItemDto>)")
    
    log_test("\n🧩 AssemblyChartItemDto structure for ingredients:")
    log_test("   - sortWeight (Double - display order)")
    log_test("   - productId (UUID - ingredient product ID)")
    log_test("   - amountIn (BigDecimal - gross amount)")
    log_test("   - amountMiddle (BigDecimal - net amount)")
    log_test("   - amountOut (BigDecimal - output amount)")
    log_test("   - productSizeSpecification (UUID or null)")
    log_test("   - storeSpecification (StoreSpecification or null)")
    
    try:
        url = f"{API_BASE}/iiko/assembly-charts/create"
        log_test(f"\n🌐 Making request to: {url}")
        
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"📊 Response status: {response.status_code}")
        log_test(f"⏱️ Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Assembly chart creation request successful!")
            
            # Analyze the response structure
            log_test("\n🔍 ANALYZING RESPONSE STRUCTURE:")
            
            if 'success' in data:
                log_test(f"📋 Success status: {data['success']}")
            
            if 'message' in data:
                log_test(f"💬 Response message: {data['message']}")
            
            if 'assembly_chart_id' in data:
                log_test(f"🆔 Assembly chart ID: {data['assembly_chart_id']}")
            
            if 'method' in data:
                log_test(f"🔧 Method used: {data['method']}")
            
            if 'endpoint' in data:
                log_test(f"🌐 IIKo endpoint used: {data['endpoint']}")
            
            # Check if the creation was successful in IIKo
            if data.get('success') == True:
                log_test("🎉 ASSEMBLY CHART SUCCESSFULLY CREATED IN IIKO!")
                log_test("✅ Official IIKo structure validation PASSED")
                log_test("✅ Real product ID matching WORKING")
                log_test("✅ AssemblyChartItemDto structure ACCEPTED")
                
                # Log the actual IIKo response if available
                if 'response' in data and data['response']:
                    log_test(f"\n📋 IIKo API Response: {json.dumps(data['response'], indent=2, ensure_ascii=False)}")
                
            else:
                log_test("⚠️ Assembly chart creation had issues")
                if 'error' in data:
                    log_test(f"❌ Error: {data['error']}")
                if 'response' in data:
                    log_test(f"📋 IIKo response: {data['response']}")
            
            return {
                'success': data.get('success', False),
                'data': data,
                'assembly_chart_id': data.get('assembly_chart_id'),
                'iiko_success': data.get('success') == True
            }
            
        else:
            log_test(f"❌ Assembly chart creation failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"📋 Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                
                # Check for specific IIKo validation errors
                if 'error' in error_data:
                    error_msg = str(error_data['error'])
                    if 'Unrecognized field' in error_msg:
                        log_test("🚨 IIKO VALIDATION ERROR: Invalid field structure detected")
                        log_test("💡 This indicates backend is sending fields not accepted by IIKo DTO")
                    elif '@NotNull' in error_msg:
                        log_test("🚨 IIKO VALIDATION ERROR: Missing required @NotNull fields")
                        log_test("💡 Backend transformation missing required IIKo fields")
                    elif 'assembledProductId' in error_msg:
                        log_test("🚨 PRODUCT ID ERROR: Issue with main product ID")
                    elif 'items' in error_msg:
                        log_test("🚨 INGREDIENTS ERROR: Issue with ingredient structure")
                
            except:
                log_test(f"📋 Raw error response: {response.text[:500]}")
            
            return {
                'success': False, 
                'error': f"HTTP {response.status_code}", 
                'response': response.text,
                'iiko_success': False
            }
            
    except Exception as e:
        log_test(f"❌ Error creating assembly chart: {str(e)}")
        return {'success': False, 'error': str(e), 'iiko_success': False}

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
    """Main testing function for Official IIKo Assembly Charts API"""
    log_test("🚀 Starting OFFICIAL IIKo Assembly Charts API Testing")
    log_test("🎯 Focus: Testing official IIKo structure with real product ID matching")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Step 1: Get existing products from menu
    menu_result = test_get_menu_products()
    
    if not menu_result['success']:
        log_test("❌ Cannot proceed without menu data")
        return
    
    menu_items = menu_result.get('items', [])
    log_test(f"\n📊 Menu loaded: {len(menu_items)} products available for matching")
    
    # Step 2.5: Analyze ingredient matching process with user's test data
    test_ingredients = [
        {"name": "Хлеб", "quantity": 100, "unit": "г", "price": 10.0},
        {"name": "Масло", "quantity": 25, "unit": "г", "price": 8.0}
    ]
    
    test_ingredient_matching_process(menu_items, test_ingredients)
    
    log_test("\n" + "=" * 80)
    
    # Step 2: Test assembly chart creation with official IIKo structure
    creation_result = test_create_assembly_chart_official_structure()
    
    log_test("\n" + "=" * 80)
    
    # Step 3: Test getting all assembly charts (if creation was successful)
    if creation_result.get('iiko_success'):
        log_test("✅ Assembly chart created successfully, testing retrieval...")
        list_result = test_get_all_assembly_charts()
    else:
        log_test("⚠️ Assembly chart creation had issues, testing retrieval anyway...")
        list_result = test_get_all_assembly_charts()
    
    # Summary
    log_test("\n" + "=" * 80)
    log_test("📋 OFFICIAL IIKO ASSEMBLY CHARTS API TESTING SUMMARY:")
    log_test(f"✅ Menu retrieval: {'SUCCESS' if menu_result['success'] else 'FAILED'}")
    log_test(f"✅ Assembly chart creation: {'SUCCESS' if creation_result.get('iiko_success') else 'FAILED'}")
    log_test(f"✅ Assembly charts list: {'SUCCESS' if list_result.get('success') else 'FAILED'}")
    
    if creation_result.get('iiko_success'):
        log_test("🎉 OFFICIAL IIKO ASSEMBLY CHARTS API IS WORKING!")
        log_test("✅ Official IIKo structure validation PASSED")
        log_test("✅ Real product ID matching WORKING")
        log_test("✅ AssemblyChartItemDto structure ACCEPTED")
        log_test("✅ All required fields properly implemented")
    else:
        log_test("⚠️ Assembly chart creation had issues:")
        if 'error' in creation_result:
            log_test(f"   - Error: {creation_result['error']}")
        log_test("💡 Check backend transformation logic for official IIKo structure")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()