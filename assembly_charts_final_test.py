#!/usr/bin/env python3
"""
Final Assembly Charts API Testing Suite
Testing the final version with @NotNull fields: chartId, assemblyName, creationDate, active, version, organizationId, status, author
Focus: Resolve @NotNull validation issues and verify all endpoints work correctly
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

def test_create_assembly_chart_final():
    """Test POST /api/iiko/assembly-charts/create with final test data and @NotNull fields"""
    log_test("🎯 TESTING FINAL ASSEMBLY CHARTS API WITH @NotNull FIELDS")
    log_test("=" * 80)
    
    # Use the exact test data provided in the review request
    test_data = {
        "name": "Финальный тест техкарты",
        "description": "Техкарта с полной валидацией",
        "ingredients": [
            {"name": "Хлеб", "quantity": 100, "unit": "г", "price": 10.0},
            {"name": "Масло", "quantity": 20, "unit": "г", "price": 5.0}
        ],
        "preparation_steps": ["Намазать маслом хлеб"],
        "organization_id": "default-org-001",
        "weight": 120.0
    }
    
    log_test("📝 Test Data:")
    log_test(f"   Name: {test_data['name']}")
    log_test(f"   Description: {test_data['description']}")
    log_test(f"   Weight: {test_data['weight']}г")
    log_test(f"   Organization: {test_data['organization_id']}")
    log_test("   Ingredients:")
    for ing in test_data['ingredients']:
        log_test(f"     - {ing['name']}: {ing['quantity']}{ing['unit']} (цена: {ing['price']}₽)")
    log_test(f"   Steps: {test_data['preparation_steps']}")
    
    try:
        url = f"{API_BASE}/iiko/assembly-charts/create"
        log_test(f"\n🔨 Making POST request to: {url}")
        
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"⏱️ Response time: {response_time:.2f}s")
        log_test(f"📊 Response status: {response.status_code}")
        
        # Log response headers for debugging
        log_test("📋 Response headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'content-length']:
                log_test(f"   {key}: {value}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                log_test("✅ SUCCESS: Assembly chart creation returned 200 OK")
                
                # Analyze the response structure
                log_test("\n📋 Response Analysis:")
                log_test(f"   Success: {data.get('success', 'Not specified')}")
                log_test(f"   Method: {data.get('method', 'Not specified')}")
                log_test(f"   Assembly Chart ID: {data.get('assembly_chart_id', 'Not provided')}")
                log_test(f"   Name: {data.get('name', 'Not provided')}")
                log_test(f"   Message: {data.get('message', 'No message')}")
                
                if 'response' in data:
                    log_test("\n🔍 IIKo API Response Details:")
                    iiko_response = data['response']
                    log_test(f"   IIKo Response: {json.dumps(iiko_response, indent=2, ensure_ascii=False)}")
                
                return {
                    'success': True,
                    'data': data,
                    'assembly_chart_id': data.get('assembly_chart_id'),
                    'status_code': response.status_code
                }
                
            except json.JSONDecodeError as e:
                log_test(f"❌ JSON decode error: {str(e)}")
                log_test(f"Raw response: {response.text[:500]}")
                return {'success': False, 'error': 'JSON decode error', 'raw_response': response.text}
                
        else:
            log_test(f"❌ FAILED: Assembly chart creation returned {response.status_code}")
            
            # Try to parse error response
            try:
                error_data = response.json()
                log_test("\n🚨 ERROR DETAILS:")
                log_test(f"   Error Data: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                
                # Look for specific @NotNull validation errors
                error_text = json.dumps(error_data, ensure_ascii=False)
                if '@NotNull' in error_text:
                    log_test("🔍 @NotNull VALIDATION ERROR DETECTED!")
                    log_test("   This indicates missing required fields in IIKo DTO")
                
                if 'detail' in error_data:
                    log_test(f"   Detail: {error_data['detail']}")
                    
            except json.JSONDecodeError:
                log_test(f"   Raw error response: {response.text[:1000]}")
            
            return {
                'success': False, 
                'error': f"HTTP {response.status_code}",
                'status_code': response.status_code,
                'response_text': response.text
            }
            
    except requests.exceptions.Timeout:
        log_test("❌ Request timed out after 60 seconds")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        log_test(f"❌ Exception during request: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_product_matching():
    """Test that product matching is still working correctly"""
    log_test("\n🔍 TESTING PRODUCT MATCHING FUNCTIONALITY")
    log_test("=" * 50)
    
    try:
        # First get the menu to see available products
        url = f"{API_BASE}/iiko/menu/default-org-001"
        log_test(f"📋 Getting menu from: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"📊 Menu response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            menu = data.get('menu', {})
            items = menu.get('items', [])
            
            log_test(f"✅ Menu retrieved: {len(items)} products available")
            
            # Look for our test ingredients
            test_ingredients = ["Хлеб", "Масло"]
            
            for ingredient_name in test_ingredients:
                log_test(f"\n🔍 Searching for '{ingredient_name}':")
                
                # Exact matches
                exact_matches = [item for item in items 
                               if item.get('name', '').lower().strip() == ingredient_name.lower().strip()]
                
                if exact_matches:
                    log_test(f"   ✅ Exact match found: {exact_matches[0].get('name')} (ID: {exact_matches[0].get('id')})")
                else:
                    # Partial matches
                    partial_matches = [item for item in items 
                                     if ingredient_name.lower() in item.get('name', '').lower()]
                    
                    if partial_matches:
                        log_test(f"   🔍 Partial matches found: {len(partial_matches)}")
                        for match in partial_matches[:3]:
                            log_test(f"     - {match.get('name')} (ID: {match.get('id')})")
                    else:
                        log_test(f"   ❌ No matches found for '{ingredient_name}'")
            
            return {'success': True, 'total_products': len(items)}
        else:
            log_test(f"❌ Failed to get menu: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error testing product matching: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_get_all_assembly_charts():
    """Test GET /api/iiko/assembly-charts/all/default-org-001"""
    log_test("\n📋 TESTING GET ALL ASSEMBLY CHARTS")
    log_test("=" * 50)
    
    try:
        url = f"{API_BASE}/iiko/assembly-charts/all/default-org-001"
        log_test(f"📋 Making GET request to: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Assembly charts list retrieved successfully!")
            
            if 'assembly_charts' in data:
                charts = data['assembly_charts']
                count = data.get('count', len(charts) if isinstance(charts, list) else 0)
                log_test(f"📊 Found {count} assembly charts")
                
                if isinstance(charts, list) and charts:
                    log_test("📋 Assembly charts:")
                    for i, chart in enumerate(charts[:5]):
                        chart_name = chart.get('name', 'Unknown')
                        chart_id = chart.get('id', 'No ID')
                        log_test(f"   {i+1}. {chart_name} (ID: {chart_id})")
                else:
                    log_test("📋 No assembly charts found (empty list)")
            
            return {'success': True, 'data': data, 'count': count}
        else:
            log_test(f"❌ Failed to get assembly charts: {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"Raw error: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error getting assembly charts: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_get_assembly_chart_by_id(chart_id=None):
    """Test GET /api/iiko/assembly-charts/{chart_id}"""
    log_test("\n🔍 TESTING GET ASSEMBLY CHART BY ID")
    log_test("=" * 50)
    
    # Use a test ID if none provided
    if not chart_id:
        chart_id = "test-chart-id-12345"
        log_test(f"⚠️ Using test chart ID: {chart_id}")
    else:
        log_test(f"🆔 Using chart ID: {chart_id}")
    
    try:
        url = f"{API_BASE}/iiko/assembly-charts/{chart_id}"
        log_test(f"📋 Making GET request to: {url}")
        
        response = requests.get(url, timeout=30)
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ Assembly chart retrieved successfully!")
            
            if 'assembly_chart' in data:
                chart = data['assembly_chart']
                log_test(f"📋 Chart details: {json.dumps(chart, indent=2, ensure_ascii=False)}")
            
            return {'success': True, 'data': data}
        elif response.status_code == 404:
            log_test("⚠️ Assembly chart not found (404) - this is expected for test ID")
            return {'success': True, 'note': 'Chart not found (expected for test)'}
        else:
            log_test(f"❌ Failed to get assembly chart: {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"Raw error: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error getting assembly chart by ID: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_delete_assembly_chart(chart_id=None):
    """Test DELETE /api/iiko/assembly-charts/{chart_id}"""
    log_test("\n🗑️ TESTING DELETE ASSEMBLY CHART")
    log_test("=" * 50)
    
    # Use a test ID if none provided
    if not chart_id:
        chart_id = "test-chart-id-12345"
        log_test(f"⚠️ Using test chart ID: {chart_id}")
    else:
        log_test(f"🆔 Using chart ID: {chart_id}")
    
    try:
        url = f"{API_BASE}/iiko/assembly-charts/{chart_id}"
        log_test(f"🗑️ Making DELETE request to: {url}")
        
        response = requests.delete(url, timeout=30)
        log_test(f"📊 Response status: {response.status_code}")
        
        if response.status_code in [200, 204]:
            log_test("✅ Delete request successful!")
            try:
                data = response.json() if response.content else {}
                if data:
                    log_test(f"📋 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                log_test("📋 No response body (expected for delete)")
            return {'success': True}
        elif response.status_code == 404:
            log_test("⚠️ Assembly chart not found for deletion (404) - expected for test ID")
            return {'success': True, 'note': 'Chart not found (expected for test)'}
        else:
            log_test(f"❌ Failed to delete assembly chart: {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"Raw error: {response.text[:200]}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error deleting assembly chart: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main testing function for final assembly charts API"""
    log_test("🚀 FINAL ASSEMBLY CHARTS API TESTING")
    log_test("Testing @NotNull fields resolution and all endpoints")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    results = {}
    
    # Test 1: Product matching verification
    log_test("\n🔍 TEST 1: PRODUCT MATCHING VERIFICATION")
    results['product_matching'] = test_product_matching()
    
    # Test 2: Create assembly chart with final data
    log_test("\n🔨 TEST 2: CREATE ASSEMBLY CHART WITH @NotNull FIELDS")
    results['create_chart'] = test_create_assembly_chart_final()
    
    # Test 3: Get all assembly charts
    log_test("\n📋 TEST 3: GET ALL ASSEMBLY CHARTS")
    results['get_all_charts'] = test_get_all_assembly_charts()
    
    # Test 4: Get assembly chart by ID
    log_test("\n🔍 TEST 4: GET ASSEMBLY CHART BY ID")
    chart_id = None
    if results['create_chart'].get('success') and results['create_chart'].get('assembly_chart_id'):
        chart_id = results['create_chart']['assembly_chart_id']
    results['get_chart_by_id'] = test_get_assembly_chart_by_id(chart_id)
    
    # Test 5: Delete assembly chart
    log_test("\n🗑️ TEST 5: DELETE ASSEMBLY CHART")
    results['delete_chart'] = test_delete_assembly_chart(chart_id)
    
    # Final Summary
    log_test("\n" + "=" * 80)
    log_test("📋 FINAL TESTING SUMMARY")
    log_test("=" * 80)
    
    log_test(f"✅ Product Matching: {'SUCCESS' if results['product_matching'].get('success') else 'FAILED'}")
    log_test(f"✅ Create Assembly Chart: {'SUCCESS' if results['create_chart'].get('success') else 'FAILED'}")
    log_test(f"✅ Get All Charts: {'SUCCESS' if results['get_all_charts'].get('success') else 'FAILED'}")
    log_test(f"✅ Get Chart by ID: {'SUCCESS' if results['get_chart_by_id'].get('success') else 'FAILED'}")
    log_test(f"✅ Delete Chart: {'SUCCESS' if results['delete_chart'].get('success') else 'FAILED'}")
    
    # Analyze the main issue
    if not results['create_chart'].get('success'):
        log_test("\n🚨 CRITICAL ISSUE ANALYSIS:")
        create_result = results['create_chart']
        
        if create_result.get('status_code') == 500:
            log_test("   Status: 500 Internal Server Error")
            log_test("   Likely cause: @NotNull validation failure in IIKo API")
            log_test("   Recommendation: Check IIKo DTO requirements for missing fields")
        
        if '@NotNull' in str(create_result.get('response_text', '')):
            log_test("   🔍 @NotNull validation error confirmed!")
            log_test("   Backend transformation needs additional required fields")
        
        log_test(f"   Error details: {create_result.get('error', 'Unknown error')}")
    else:
        log_test("\n🎉 SUCCESS: @NotNull validation issues resolved!")
        log_test("   Assembly charts API is working correctly")
    
    # Product matching status
    if results['product_matching'].get('success'):
        total_products = results['product_matching'].get('total_products', 0)
        log_test(f"\n✅ Product matching is working with {total_products} available products")
    else:
        log_test("\n❌ Product matching has issues")
    
    log_test("\n" + "=" * 80)
    log_test("🏁 TESTING COMPLETE")
    log_test("=" * 80)

if __name__ == "__main__":
    main()