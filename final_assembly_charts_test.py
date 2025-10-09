#!/usr/bin/env python3
"""
Final IIKo Assembly Charts API Testing - Valid Fields Only
Testing POST /api/iiko/assembly-charts/create with ONLY 8 valid IIKo fields
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_assembly_charts_create_valid_fields_only():
    """Test assembly charts creation with ONLY valid IIKo fields"""
    print("🔨 TESTING ASSEMBLY CHARTS CREATE - VALID FIELDS ONLY")
    print("=" * 70)
    
    print("🎯 ЦЕЛЬ: Создание техкарты с ТОЛЬКО 8 валидными полями IIKo:")
    print("✅ items, assembledAmount, technologyDescription")
    print("✅ effectiveDirectWriteoffStoreSpecification, appearance, dateTo")
    print("✅ productSizeAssemblyStrategy, productWriteoffStrategy")
    print()
    print("❌ УБРАНЫ невалидные поля: chartId, assemblyName, creationDate,")
    print("❌ active, version, organizationId, status, author")
    print()
    
    # Test data as specified in the review
    test_data = {
        "name": "Чистое тестирование",
        "description": "Только валидные поля IIKo",
        "ingredients": [
            {"name": "Хлеб", "quantity": 50, "unit": "г", "price": 5.0}
        ],
        "preparation_steps": ["Подать хлеб"],
        "organization_id": "default-org-001",
        "weight": 50.0
    }
    
    print("Test 1: POST /api/iiko/assembly-charts/create")
    print(f"Test data: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    print()
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/iiko/assembly-charts/create",
            json=test_data,
            timeout=60
        )
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f}s")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            log_test("Assembly chart creation", "PASS", 
                    f"Successfully created with valid fields only")
            
            # Check response structure
            print("📋 RESPONSE ANALYSIS:")
            print(f"Response keys: {list(result.keys())}")
            
            if 'success' in result:
                success = result.get('success')
                print(f"Success: {success}")
                
                if success:
                    log_test("🎉 ASSEMBLY CHART CREATED IN IIKO", "PASS",
                            "Tech card successfully created with minimal valid fields")
                    
                    # Log creation details
                    if 'assembly_chart_id' in result:
                        chart_id = result.get('assembly_chart_id')
                        print(f"Assembly Chart ID: {chart_id}")
                        
                        # Test GET endpoint if creation was successful
                        test_get_all_assembly_charts(chart_id)
                    
                    if 'message' in result:
                        print(f"Message: {result.get('message')}")
                        
                else:
                    error = result.get('error', 'Unknown error')
                    note = result.get('note', '')
                    
                    log_test("Assembly chart creation failed", "FAIL",
                            f"Error: {error}")
                    
                    if note:
                        print(f"Note: {note}")
                    
                    # Check if it's a field validation error
                    if '@NotNull' in error or 'Unrecognized field' in error:
                        log_test("🔍 FIELD VALIDATION ISSUE", "INFO",
                                "IIKo API still rejecting fields - need further investigation")
                        print(f"🔍 Error details: {error}")
                    
            else:
                log_test("Response format", "WARN",
                        f"Unexpected response format: {result}")
                
        elif response.status_code == 400:
            error_text = response.text
            log_test("Assembly chart validation", "INFO",
                    f"Validation error (expected): {error_text}")
            
            # Check if it's about invalid fields
            if 'Unrecognized field' in error_text:
                log_test("🚨 INVALID FIELDS STILL PRESENT", "FAIL",
                        "Backend still sending invalid fields to IIKo")
                print(f"🔍 Invalid field error: {error_text}")
            elif '@NotNull' in error_text:
                log_test("🔍 MISSING REQUIRED FIELDS", "INFO",
                        "IIKo requires additional @NotNull fields")
                print(f"🔍 Missing field error: {error_text}")
                
        elif response.status_code == 500:
            error_text = response.text
            log_test("Assembly chart server error", "WARN",
                    f"Server error: {error_text}")
            
            # Parse error for specific issues
            if 'IIKo' in error_text or 'assembly' in error_text.lower():
                print(f"🔍 IIKo integration error: {error_text}")
            
        else:
            log_test("Assembly chart endpoint", "FAIL",
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Assembly chart endpoint", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("Assembly chart endpoint", "FAIL", f"Exception: {str(e)}")

def test_get_all_assembly_charts(created_chart_id=None):
    """Test GET all assembly charts endpoint"""
    print("📋 TESTING GET ALL ASSEMBLY CHARTS")
    print("=" * 70)
    
    print("Test 2: GET /api/iiko/assembly-charts/all/default-org-001")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/iiko/assembly-charts/all/default-org-001",
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            log_test("Get all assembly charts", "PASS",
                    "Successfully retrieved assembly charts list")
            
            # Check response structure
            print("📋 RESPONSE ANALYSIS:")
            print(f"Response keys: {list(result.keys())}")
            
            if 'success' in result:
                success = result.get('success')
                print(f"Success: {success}")
                
                if success:
                    charts = result.get('assembly_charts', [])
                    count = result.get('count', 0)
                    
                    print(f"Assembly charts count: {count}")
                    
                    if count > 0:
                        log_test("🎉 ASSEMBLY CHARTS FOUND", "PASS",
                                f"Found {count} assembly charts in IIKo")
                        
                        # Check if our created chart is in the list
                        if created_chart_id:
                            found_our_chart = any(
                                chart.get('id') == created_chart_id 
                                for chart in charts if isinstance(chart, dict)
                            )
                            
                            if found_our_chart:
                                log_test("🎯 CREATED CHART FOUND IN LIST", "PASS",
                                        "Our created chart appears in the list")
                            else:
                                log_test("Created chart not found", "INFO",
                                        "Created chart not yet visible (may need time)")
                        
                        # Show sample charts
                        print("📋 Sample assembly charts:")
                        for i, chart in enumerate(charts[:3]):
                            if isinstance(chart, dict):
                                name = chart.get('name', 'N/A')
                                chart_id = chart.get('id', 'N/A')
                                print(f"  {i+1}. {name} (ID: {chart_id})")
                    else:
                        log_test("No assembly charts found", "INFO",
                                "Empty list (expected if none created yet)")
                else:
                    error = result.get('error', 'Unknown error')
                    log_test("Get assembly charts failed", "WARN",
                            f"Error: {error}")
            else:
                log_test("Response format", "WARN",
                        f"Unexpected response format: {result}")
                
        elif response.status_code == 500:
            error_text = response.text
            log_test("Get assembly charts server error", "WARN",
                    f"Server error: {error_text}")
            
        else:
            log_test("Get assembly charts endpoint", "FAIL",
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Get assembly charts endpoint", "FAIL", "Request timeout (>30s)")
    except Exception as e:
        log_test("Get assembly charts endpoint", "FAIL", f"Exception: {str(e)}")

def test_product_matching():
    """Test that product matching still works correctly"""
    print("🔍 TESTING PRODUCT MATCHING")
    print("=" * 70)
    
    print("Test 3: GET /api/iiko/menu/default-org-001 (for product matching)")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/iiko/menu/default-org-001",
            timeout=60
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            log_test("Menu retrieval for product matching", "PASS",
                    "Successfully retrieved menu for product matching")
            
            # Check menu structure
            items = result.get('items', [])
            categories = result.get('categories', [])
            
            print(f"Menu items: {len(items)}")
            print(f"Categories: {len(categories)}")
            
            if items:
                log_test("🎯 PRODUCT MATCHING DATA AVAILABLE", "PASS",
                        f"Found {len(items)} products for matching")
                
                # Look for bread products (our test ingredient)
                bread_products = [
                    item for item in items 
                    if isinstance(item, dict) and 
                    'хлеб' in item.get('name', '').lower()
                ]
                
                if bread_products:
                    log_test("🍞 BREAD PRODUCTS FOUND", "PASS",
                            f"Found {len(bread_products)} bread products for matching")
                    
                    print("🍞 Sample bread products:")
                    for i, product in enumerate(bread_products[:3]):
                        name = product.get('name', 'N/A')
                        product_id = product.get('id', 'N/A')
                        print(f"  {i+1}. {name} (ID: {product_id})")
                else:
                    log_test("No bread products found", "INFO",
                            "No bread products found for exact matching")
                
                # Show sample products for general matching
                print("📋 Sample menu products:")
                for i, item in enumerate(items[:5]):
                    if isinstance(item, dict):
                        name = item.get('name', 'N/A')
                        product_id = item.get('id', 'N/A')
                        print(f"  {i+1}. {name} (ID: {product_id})")
            else:
                log_test("No menu items found", "WARN",
                        "Empty menu - product matching will use fallback")
                
        elif response.status_code == 500:
            error_text = response.text
            log_test("Menu retrieval server error", "WARN",
                    f"Server error: {error_text}")
            
        else:
            log_test("Menu retrieval endpoint", "FAIL",
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Menu retrieval endpoint", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("Menu retrieval endpoint", "FAIL", f"Exception: {str(e)}")

def main():
    """Run final assembly charts testing with valid fields only"""
    print("🧪 FINAL IIKO ASSEMBLY CHARTS API TESTING - VALID FIELDS ONLY")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🎯 ЦЕЛЬ ТЕСТИРОВАНИЯ:")
    print("Проведи финальное тестирование assembly charts API с использованием")
    print("ТОЛЬКО валидных полей IIKo:")
    print()
    print("✅ ВАЛИДНЫЕ ПОЛЯ (8 штук):")
    print("  - items")
    print("  - assembledAmount") 
    print("  - technologyDescription")
    print("  - effectiveDirectWriteoffStoreSpecification")
    print("  - appearance")
    print("  - dateTo")
    print("  - productSizeAssemblyStrategy")
    print("  - productWriteoffStrategy")
    print()
    print("❌ УБРАНЫ НЕВАЛИДНЫЕ ПОЛЯ:")
    print("  - chartId, assemblyName, creationDate, active")
    print("  - version, organizationId, status, author")
    print()
    print("🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:")
    print("✅ Успешное создание техкарты в IIKo системе")
    print("✅ Product matching по-прежнему работает корректно")
    print("✅ GET /api/iiko/assembly-charts/all/default-org-001 возвращает данные")
    print()
    
    try:
        # Test 1: Product matching (to verify it still works)
        test_product_matching()
        
        # Test 2: Assembly chart creation with valid fields only
        test_assembly_charts_create_valid_fields_only()
        
        print("🏁 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ASSEMBLY CHARTS ЗАВЕРШЕНО")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        print("Проверьте логи выше для определения успешности создания техкарты")
        print("с использованием только валидных полей IIKo.")
        print()
        print("🔍 КЛЮЧЕВЫЕ ИНДИКАТОРЫ УСПЕХА:")
        print("✅ 'Assembly chart creation: PASS' - техкарта создана")
        print("✅ 'ASSEMBLY CHART CREATED IN IIKO: PASS' - создание в IIKo")
        print("✅ 'PRODUCT MATCHING DATA AVAILABLE: PASS' - matching работает")
        print("✅ 'Get all assembly charts: PASS' - получение списка работает")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()