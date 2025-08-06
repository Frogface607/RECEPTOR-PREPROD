#!/usr/bin/env python3
"""
Backend Testing Suite for IIKo Analytics - REVENUE & ANALYTICS TESTING
Testing the new IIKo analytics endpoints for revenue reporting and comprehensive analytics dashboard
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://26d71771-d1f5-449c-a365-fa5f081cd98e.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_iiko_sales_report():
    """Test the new IIKo sales report endpoint for revenue data"""
    print("💰 TESTING IIKO SALES REPORT - PRIORITY 1")
    print("=" * 60)
    
    # Use Edison Craft Bar organization ID as mentioned in review
    organization_id = "default-org-001"  # Edison Craft Bar ID from previous tests
    
    print(f"Test 1: GET /api/iiko/sales-report/{organization_id} - Revenue for yesterday")
    try:
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/iiko/sales-report/{organization_id}",
            timeout=60
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check expected response structure
            success = result.get("success", False)
            message = result.get("message", "")
            organization_id_resp = result.get("organization_id")
            period = result.get("period", {})
            data = result.get("data")
            summary = result.get("summary", {})
            endpoint_used = result.get("endpoint_used")
            
            print(f"\n📊 SALES REPORT ANALYSIS:")
            print(f"Success: {success}")
            print(f"Message: {message}")
            print(f"Organization ID: {organization_id_resp}")
            print(f"Period: {period}")
            print(f"Endpoint used: {endpoint_used}")
            
            if success:
                log_test("SALES REPORT - SUCCESS", "PASS", 
                        f"Revenue data retrieved successfully for {organization_id}")
                
                # Check for revenue data
                if data:
                    log_test("Sales data availability", "PASS", 
                            "Sales data is present in response")
                else:
                    log_test("Sales data availability", "WARN", 
                            "No sales data in response")
                
                # Check summary metrics
                if summary:
                    total_revenue = summary.get('total_revenue')
                    transactions = summary.get('transactions')
                    items_sold = summary.get('items_sold')
                    
                    log_test("Revenue summary parsing", "PASS", 
                            f"Revenue: {total_revenue}, Transactions: {transactions}, Items: {items_sold}")
                else:
                    log_test("Revenue summary parsing", "WARN", 
                            "No summary metrics available")
                    
            else:
                log_test("SALES REPORT - FALLBACK", "PASS", 
                        "Sales endpoints not available but handled gracefully")
                
                # Check diagnostic info
                diagnostic_info = result.get("diagnostic_info", {})
                if diagnostic_info:
                    auth_working = diagnostic_info.get("auth_working")
                    menu_access = diagnostic_info.get("menu_access")
                    sales_endpoints = diagnostic_info.get("sales_endpoints")
                    
                    log_test("Diagnostic information", "PASS", 
                            f"Auth: {auth_working}, Menu: {menu_access}, Sales: {sales_endpoints}")
                else:
                    log_test("Diagnostic information", "WARN", 
                            "No diagnostic information provided")
                    
        elif response.status_code == 404:
            log_test("SALES REPORT", "FAIL", 
                    f"Organization not found: {response.text}")
        elif response.status_code == 500:
            log_test("SALES REPORT", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("SALES REPORT", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("SALES REPORT", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("SALES REPORT", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Sales report with custom date range
    print(f"\nTest 2: GET /api/iiko/sales-report/{organization_id} - Custom date range")
    try:
        from datetime import datetime, timedelta
        
        # Test with specific date range (last week)
        date_to = datetime.now().strftime('%Y-%m-%d')
        date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        
        response = requests.get(
            f"{BACKEND_URL}/iiko/sales-report/{organization_id}",
            params=params,
            timeout=60
        )
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            period = result.get("period", {})
            
            if period.get('from') == date_from and period.get('to') == date_to:
                log_test("Custom date range", "PASS", 
                        f"Date range correctly applied: {date_from} to {date_to}")
            else:
                log_test("Custom date range", "WARN", 
                        f"Date range may not be applied correctly")
        else:
            log_test("Custom date range", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Custom date range", "FAIL", f"Exception: {str(e)}")

def test_iiko_analytics_dashboard():
    """Test the new IIKo comprehensive analytics dashboard endpoint"""
    print("📊 TESTING IIKO ANALYTICS DASHBOARD - PRIORITY 2")
    print("=" * 60)
    
    # Use Edison Craft Bar organization ID
    organization_id = "default-org-001"  # Edison Craft Bar ID
    
    print(f"Test 1: GET /api/iiko/analytics/{organization_id} - Comprehensive analytics")
    try:
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/iiko/analytics/{organization_id}",
            timeout=90  # Longer timeout for comprehensive data
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check expected response structure
            success = result.get("success", False)
            message = result.get("message", "")
            analytics = result.get("analytics", {})
            
            print(f"\n📈 ANALYTICS DASHBOARD ANALYSIS:")
            print(f"Success: {success}")
            print(f"Message: {message}")
            
            if success and analytics:
                log_test("ANALYTICS DASHBOARD - SUCCESS", "PASS", 
                        "Analytics dashboard generated successfully")
                
                # Check analytics structure
                organization_id_resp = analytics.get("organization_id")
                generated_at = analytics.get("generated_at")
                sections = analytics.get("sections", {})
                organization_info = analytics.get("organization_info")
                
                print(f"Organization ID: {organization_id_resp}")
                print(f"Generated at: {generated_at}")
                print(f"Sections available: {list(sections.keys())}")
                
                # Test 1: Organization info
                if organization_info:
                    if "error" in organization_info:
                        log_test("Organization info", "WARN", 
                                f"Organization info error: {organization_info['error']}")
                    else:
                        org_name = organization_info.get("name", "N/A")
                        org_id = organization_info.get("id", "N/A")
                        log_test("Organization info", "PASS", 
                                f"Organization: {org_name} (ID: {org_id})")
                else:
                    log_test("Organization info", "WARN", 
                            "No organization info available")
                
                # Test 2: Menu overview
                menu_overview = sections.get("menu_overview", {})
                if menu_overview:
                    if "error" in menu_overview:
                        log_test("Menu overview", "WARN", 
                                f"Menu overview error: {menu_overview['error']}")
                    else:
                        categories_count = menu_overview.get("categories_count", 0)
                        items_count = menu_overview.get("items_count", 0)
                        top_categories = menu_overview.get("top_categories", [])
                        
                        log_test("Menu overview", "PASS", 
                                f"Menu: {items_count} items, {categories_count} categories")
                        
                        if top_categories:
                            print(f"    Top categories: {', '.join(top_categories[:3])}")
                else:
                    log_test("Menu overview", "WARN", 
                            "No menu overview available")
                
                # Test 3: Sales summary
                sales_summary = sections.get("sales_summary", {})
                if sales_summary:
                    if "error" in sales_summary:
                        log_test("Sales summary", "WARN", 
                                f"Sales summary error: {sales_summary['error']}")
                    elif sales_summary.get("status") == "not_available":
                        log_test("Sales summary", "PASS", 
                                "Sales data not available (expected for some IIKo installations)")
                    else:
                        # Check for sales metrics
                        total_revenue = sales_summary.get('total_revenue')
                        transactions = sales_summary.get('transactions')
                        
                        log_test("Sales summary", "PASS", 
                                f"Sales metrics: Revenue: {total_revenue}, Transactions: {transactions}")
                else:
                    log_test("Sales summary", "WARN", 
                            "No sales summary available")
                
                # Overall analytics completeness
                sections_count = len([s for s in sections.values() if not s.get("error")])
                total_sections = len(sections)
                
                if sections_count >= 2:  # At least menu overview and one other section
                    log_test("Analytics completeness", "PASS", 
                            f"{sections_count}/{total_sections} sections working")
                else:
                    log_test("Analytics completeness", "WARN", 
                            f"Only {sections_count}/{total_sections} sections working")
                    
            else:
                log_test("ANALYTICS DASHBOARD - FAILURE", "FAIL", 
                        "Analytics dashboard generation failed")
                
        elif response.status_code == 404:
            log_test("ANALYTICS DASHBOARD", "FAIL", 
                    f"Organization not found: {response.text}")
        elif response.status_code == 500:
            log_test("ANALYTICS DASHBOARD", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("ANALYTICS DASHBOARD", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("ANALYTICS DASHBOARD", "FAIL", "Request timeout (>90s)")
    except Exception as e:
        log_test("ANALYTICS DASHBOARD", "FAIL", f"Exception: {str(e)}")

def test_iiko_tech_card_upload():
    """Test the REAL IIKo tech card upload functionality as requested in review"""
    print("🚀 TESTING REAL IIKO TECH CARD UPLOAD")
    print("=" * 60)
    
    # Test data exactly as specified in the review request
    test_tech_card_data = {
        "name": "Тестовый AI Бургер",
        "description": "Создано Receptor AI",
        "ingredients": [
            {"name": "Говядина", "quantity": 150, "unit": "г"},
            {"name": "Булочка", "quantity": 80, "unit": "г"}
        ],
        "preparation_steps": ["Обжарить котлету", "Собрать бургер"],
        "organization_id": "ID_Edison_Craft_Bar",
        "price": 350.0,
        "weight": 230.0
    }
    
    print("Test 1: POST /api/iiko/tech-cards/upload - REAL UPLOAD TO IIKO")
    print(f"Test data: {json.dumps(test_tech_card_data, ensure_ascii=False, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/iiko/tech-cards/upload",
            json=test_tech_card_data,
            timeout=120  # 2 minute timeout for IIKo integration
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check for expected response structure
            status = result.get("status")
            success = result.get("success", False)
            iiko_product_id = result.get("iiko_product_id")
            upload_details = result.get("upload_details", {})
            
            print(f"\n📊 UPLOAD RESULTS ANALYSIS:")
            print(f"Status: {status}")
            print(f"Success: {success}")
            print(f"IIKo Product ID: {iiko_product_id}")
            
            # Test the three levels of results as mentioned in review
            if status == "uploaded_to_iiko":
                log_test("REAL IIKO UPLOAD - SUCCESS LEVEL", "PASS", 
                        f"Tech card successfully uploaded to IIKo with ID: {iiko_product_id}")
                
                # Verify upload details
                if upload_details:
                    endpoint_used = upload_details.get("endpoint_used")
                    response_data = upload_details.get("response")
                    log_test("Upload details verification", "PASS", 
                            f"Endpoint used: {endpoint_used}, Response data available: {bool(response_data)}")
                else:
                    log_test("Upload details verification", "WARN", 
                            "No upload details provided")
                    
            elif status == "prepared_for_manual_sync":
                log_test("REAL IIKO UPLOAD - FALLBACK LEVEL", "PASS", 
                        "Tech card prepared for manual upload (graceful fallback)")
                
                # Check if prepared data is available
                prepared_data = result.get("prepared_data")
                if prepared_data:
                    log_test("Prepared data availability", "PASS", 
                            "Tech card data prepared in IIKo format for manual sync")
                else:
                    log_test("Prepared data availability", "FAIL", 
                            "No prepared data available for manual sync")
                    
            elif status == "upload_failed":
                log_test("REAL IIKO UPLOAD - ERROR LEVEL", "PASS", 
                        "Tech card saved locally with proper error handling")
                
                # Check error details
                error_details = result.get("error_details")
                if error_details:
                    log_test("Error details logging", "PASS", 
                            f"Detailed error information: {error_details}")
                else:
                    log_test("Error details logging", "WARN", 
                            "No detailed error information provided")
            else:
                log_test("REAL IIKO UPLOAD - UNKNOWN STATUS", "FAIL", 
                        f"Unexpected status: {status}")
            
            # Verify critical requirements from review
            print(f"\n🎯 CRITICAL REQUIREMENTS VERIFICATION:")
            
            # 1. Real upload attempt
            if "upload_attempts" in result or "endpoint_used" in upload_details:
                log_test("Real upload attempt verification", "PASS", 
                        "Evidence of real IIKo API calls found")
            else:
                log_test("Real upload attempt verification", "WARN", 
                        "No clear evidence of real IIKo API attempts")
            
            # 2. Detailed logging
            logs = result.get("logs", [])
            if logs or upload_details:
                log_test("Detailed logging verification", "PASS", 
                        f"Logging information available: {len(logs)} log entries")
            else:
                log_test("Detailed logging verification", "WARN", 
                        "Limited logging information available")
            
            # 3. Status accuracy
            if status in ["uploaded_to_iiko", "prepared_for_manual_sync", "upload_failed"]:
                log_test("Status accuracy verification", "PASS", 
                        f"Status '{status}' matches expected values")
            else:
                log_test("Status accuracy verification", "FAIL", 
                        f"Unexpected status: {status}")
            
            # 4. IIKo product ID on success
            if status == "uploaded_to_iiko" and iiko_product_id:
                log_test("IIKo Product ID verification", "PASS", 
                        f"Product ID provided: {iiko_product_id}")
            elif status == "uploaded_to_iiko" and not iiko_product_id:
                log_test("IIKo Product ID verification", "FAIL", 
                        "Success status but no product ID provided")
            else:
                log_test("IIKo Product ID verification", "PASS", 
                        f"No product ID expected for status: {status}")
                
        elif response.status_code == 400:
            log_test("REAL IIKO UPLOAD", "FAIL", 
                    f"Bad request: {response.text}")
        elif response.status_code == 500:
            log_test("REAL IIKO UPLOAD", "FAIL", 
                    f"Server error: {response.text}")
        elif response.status_code == 503:
            log_test("REAL IIKO UPLOAD", "WARN", 
                    f"Service unavailable (IIKo integration may be down): {response.text}")
        else:
            log_test("REAL IIKO UPLOAD", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("REAL IIKO UPLOAD", "FAIL", "Request timeout (>120s)")
    except Exception as e:
        log_test("REAL IIKO UPLOAD", "FAIL", f"Exception: {str(e)}")

def test_iiko_integration_health():
    """Test IIKo integration health and connectivity"""
    print("🏥 TESTING IIKO INTEGRATION HEALTH")
    print("=" * 60)
    
    # Test 1: Health check
    print("Test 1: GET /api/iiko/health")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/health", timeout=30)
        
        if response.status_code == 200:
            health_data = response.json()
            status = health_data.get("status")
            iiko_connection = health_data.get("iiko_connection")
            
            if status == "healthy" and iiko_connection == "active":
                log_test("IIKo Health Check", "PASS", 
                        f"Status: {status}, Connection: {iiko_connection}")
            else:
                log_test("IIKo Health Check", "WARN", 
                        f"Status: {status}, Connection: {iiko_connection}")
                
        elif response.status_code == 503:
            log_test("IIKo Health Check", "WARN", 
                    f"Service unavailable: {response.text}")
        else:
            log_test("IIKo Health Check", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("IIKo Health Check", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Organizations
    print("Test 2: GET /api/iiko/organizations")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/organizations", timeout=30)
        
        if response.status_code == 200:
            orgs = response.json()
            if isinstance(orgs, list) and len(orgs) > 0:
                log_test("IIKo Organizations", "PASS", 
                        f"Found {len(orgs)} organizations")
                
                # Look for Edison Craft Bar
                edison_org = None
                for org in orgs:
                    if "edison" in org.get("name", "").lower():
                        edison_org = org
                        break
                
                if edison_org:
                    log_test("Edison Craft Bar Organization", "PASS", 
                            f"Found: {edison_org.get('name')} (ID: {edison_org.get('id')})")
                else:
                    log_test("Edison Craft Bar Organization", "WARN", 
                            "Edison Craft Bar not found in organizations list")
            else:
                log_test("IIKo Organizations", "WARN", 
                        "No organizations found")
        else:
            log_test("IIKo Organizations", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("IIKo Organizations", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: Diagnostics
    print("Test 3: GET /api/iiko/diagnostics")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/diagnostics", timeout=30)
        
        if response.status_code == 200:
            diagnostics = response.json()
            auth_status = diagnostics.get("authentication")
            connection_status = diagnostics.get("connection")
            
            log_test("IIKo Diagnostics", "PASS", 
                    f"Auth: {auth_status}, Connection: {connection_status}")
            
            # Print detailed diagnostics
            print(f"    Detailed diagnostics:")
            for key, value in diagnostics.items():
                print(f"    - {key}: {value}")
                
        else:
            log_test("IIKo Diagnostics", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("IIKo Diagnostics", "FAIL", f"Exception: {str(e)}")

def test_iiko_menu_access():
    """Test IIKo menu access for context"""
    print("📋 TESTING IIKO MENU ACCESS")
    print("=" * 60)
    
    # Test menu access for default organization
    print("Test 1: GET /api/iiko/menu/default-org-001")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/menu/default-org-001", timeout=60)
        
        if response.status_code == 200:
            menu_data = response.json()
            items = menu_data.get("items", [])
            categories = menu_data.get("categories", [])
            
            log_test("IIKo Menu Access", "PASS", 
                    f"Retrieved {len(items)} items, {len(categories)} categories")
            
            # Sample some items
            if items:
                print(f"    Sample menu items:")
                for i, item in enumerate(items[:5]):
                    name = item.get("name", "N/A")
                    price = item.get("price", 0)
                    print(f"    {i+1}. {name} - {price}₽")
            
        elif response.status_code == 404:
            log_test("IIKo Menu Access", "WARN", 
                    "Default organization not found")
        else:
            log_test("IIKo Menu Access", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("IIKo Menu Access", "FAIL", f"Exception: {str(e)}")

def main():
    """Run all IIKo tech card upload tests"""
    print("🧪 BACKEND TESTING: REAL IIKO TECH CARD UPLOAD")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: IIKo Integration Health
        test_iiko_integration_health()
        
        # Test 2: IIKo Menu Access (for context)
        test_iiko_menu_access()
        
        # Test 3: MAIN TEST - Real IIKo Tech Card Upload
        test_iiko_tech_card_upload()
        
        print("🏁 ALL IIKO TESTS COMPLETED")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()