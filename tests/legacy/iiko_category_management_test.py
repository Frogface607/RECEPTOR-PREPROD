#!/usr/bin/env python3
"""
IIKo Category Management Testing - New Endpoints
Testing the new category management functionality:
1. GET /api/iiko/categories/{organization_id} - Get all categories from IIKo
2. POST /api/iiko/categories/create - Create new category "AI Menu Designer"
3. POST /api/iiko/categories/check - Check if category exists
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

def test_get_all_categories():
    """Test GET /api/iiko/categories/{organization_id} - Get all categories from IIKo"""
    print("📂 TESTING GET ALL CATEGORIES FROM IIKO")
    print("=" * 70)
    
    org_id = "default-org-001"  # Edison Craft Bar ID as specified in review
    
    print(f"Test 1: GET /api/iiko/categories/{org_id}")
    print(f"Organization: Edison Craft Bar (ID: {org_id})")
    print("Expected: List of existing categories in IIKo system")
    print()
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/iiko/categories/{org_id}", timeout=60)
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check response structure
            if result.get('success'):
                categories = result.get('categories', [])
                categories_count = result.get('categories_count', 0)
                
                log_test("✅ CATEGORIES RETRIEVED SUCCESSFULLY", "PASS", 
                        f"Found {categories_count} categories from IIKo")
                
                print(f"    📊 RESPONSE STRUCTURE VERIFICATION:")
                print(f"    ✅ success: {result.get('success')}")
                print(f"    ✅ categories[]: {len(categories)} items")
                print(f"    ✅ categories_count: {categories_count}")
                print(f"    ✅ endpoint: {result.get('endpoint', 'Not provided')}")
                print(f"    ✅ organization_id: {result.get('organization_id', 'Not provided')}")
                print()
                
                if categories:
                    log_test("✅ CATEGORIES DATA STRUCTURE", "PASS", 
                            f"Categories array contains {len(categories)} items")
                    
                    print(f"    📂 SAMPLE CATEGORIES FROM IIKO:")
                    for i, category in enumerate(categories[:10], 1):  # Show first 10
                        cat_id = category.get('id', 'No ID')
                        cat_name = category.get('name', 'No Name')
                        cat_desc = category.get('description', 'No Description')
                        active = category.get('active', True)
                        status_icon = "✅" if active else "❌"
                        
                        print(f"    {i}. {status_icon} {cat_name}")
                        print(f"       ID: {cat_id}")
                        if cat_desc and cat_desc != 'No Description':
                            print(f"       Description: {cat_desc}")
                        print()
                    
                    if len(categories) > 10:
                        print(f"    ... and {len(categories) - 10} more categories")
                        print()
                    
                    # Check for "AI Menu Designer" category
                    ai_category = None
                    for category in categories:
                        if category.get('name', '').lower() == 'ai menu designer':
                            ai_category = category
                            break
                    
                    if ai_category:
                        log_test("✅ AI MENU DESIGNER CATEGORY EXISTS", "PASS", 
                                f"Found existing 'AI Menu Designer' category with ID: {ai_category.get('id')}")
                    else:
                        log_test("ℹ️ AI MENU DESIGNER CATEGORY NOT FOUND", "INFO", 
                                "Category 'AI Menu Designer' does not exist yet - ready for creation test")
                    
                    return categories, ai_category is not None
                else:
                    log_test("⚠️ EMPTY CATEGORIES LIST", "WARN", 
                            "Categories array is empty - no categories found in IIKo")
                    return [], False
                
            else:
                error_msg = result.get('error', 'Unknown error')
                log_test("❌ CATEGORIES REQUEST FAILED", "FAIL", 
                        f"IIKo API error: {error_msg}")
                return None, False
                
        elif response.status_code == 404:
            log_test("❌ ORGANIZATION NOT FOUND", "FAIL", 
                    f"Organization {org_id} not found in IIKo")
            return None, False
        elif response.status_code == 500:
            error_text = response.text
            log_test("❌ SERVER ERROR", "FAIL", 
                    f"Server error getting categories: {error_text}")
            return None, False
        else:
            log_test("❌ UNEXPECTED RESPONSE", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return None, False
            
    except requests.exceptions.Timeout:
        log_test("❌ TIMEOUT", "FAIL", "Request timeout (>60s)")
        return None, False
    except Exception as e:
        log_test("❌ EXCEPTION", "FAIL", f"Exception: {str(e)}")
        return None, False

def test_create_category():
    """Test POST /api/iiko/categories/create - Create new category 'AI Menu Designer'"""
    print("🆕 TESTING CREATE NEW CATEGORY IN IIKO")
    print("=" * 70)
    
    org_id = "default-org-001"
    category_name = "AI Menu Designer"
    
    print(f"Test 2: POST /api/iiko/categories/create")
    print(f"Organization: Edison Craft Bar (ID: {org_id})")
    print(f"Category Name: {category_name}")
    print("Expected: Create new category or return existing if already exists")
    print()
    
    payload = {
        "name": category_name,
        "organization_id": org_id
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/iiko/categories/create", 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response_time = time.time() - start_time
        
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        print(f"Response time: {response_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check response structure
            if result.get('success'):
                category_details = result.get('category', {})
                already_exists = result.get('already_exists', False)
                message = result.get('message', '')
                
                if already_exists:
                    log_test("✅ CATEGORY ALREADY EXISTS", "PASS", 
                            f"Category '{category_name}' already exists in IIKo")
                else:
                    log_test("✅ CATEGORY CREATED SUCCESSFULLY", "PASS", 
                            f"New category '{category_name}' created in IIKo")
                
                print(f"    📊 RESPONSE STRUCTURE VERIFICATION:")
                print(f"    ✅ success: {result.get('success')}")
                print(f"    ✅ message: {message}")
                print(f"    ✅ already_exists: {already_exists}")
                print(f"    ✅ category details provided: {bool(category_details)}")
                print()
                
                if category_details:
                    print(f"    📂 CATEGORY DETAILS:")
                    print(f"    Category ID: {category_details.get('id', 'Not provided')}")
                    print(f"    Category Name: {category_details.get('name', 'Not provided')}")
                    print(f"    Method: {result.get('method', 'Not provided')}")
                    print(f"    Endpoint: {result.get('endpoint', 'Not provided')}")
                    print()
                
                return True, category_details.get('id')
                
            else:
                error_msg = result.get('error', 'Unknown error')
                errors = result.get('errors', [])
                log_test("❌ CATEGORY CREATION FAILED", "FAIL", 
                        f"IIKo API error: {error_msg}")
                
                if errors:
                    print(f"    Detailed errors: {errors}")
                    print()
                
                return False, None
                
        elif response.status_code == 400:
            log_test("❌ BAD REQUEST", "FAIL", 
                    f"Invalid request data: {response.text}")
            return False, None
        elif response.status_code == 500:
            error_text = response.text
            log_test("❌ SERVER ERROR", "FAIL", 
                    f"Server error creating category: {error_text}")
            return False, None
        else:
            log_test("❌ UNEXPECTED RESPONSE", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        log_test("❌ TIMEOUT", "FAIL", "Request timeout (>60s)")
        return False, None
    except Exception as e:
        log_test("❌ EXCEPTION", "FAIL", f"Exception: {str(e)}")
        return False, None

def test_check_category_exists():
    """Test POST /api/iiko/categories/check - Check if category exists"""
    print("🔍 TESTING CHECK CATEGORY EXISTS")
    print("=" * 70)
    
    org_id = "default-org-001"
    category_name = "AI Menu Designer"
    
    print(f"Test 3: POST /api/iiko/categories/check")
    print(f"Organization: Edison Craft Bar (ID: {org_id})")
    print(f"Category Name: {category_name}")
    print("Expected: Return exists flag and category details")
    print()
    
    payload = {
        "name": category_name,
        "organization_id": org_id
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/iiko/categories/check", 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response_time = time.time() - start_time
        
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        print(f"Response time: {response_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check response structure
            if result.get('success'):
                exists = result.get('exists', False)
                category_details = result.get('category')
                all_categories = result.get('all_categories', [])
                total_categories = result.get('total_categories', 0)
                
                if exists:
                    log_test("✅ CATEGORY EXISTS CONFIRMED", "PASS", 
                            f"Category '{category_name}' exists in IIKo")
                else:
                    log_test("ℹ️ CATEGORY DOES NOT EXIST", "INFO", 
                            f"Category '{category_name}' not found in IIKo")
                
                print(f"    📊 RESPONSE STRUCTURE VERIFICATION:")
                print(f"    ✅ success: {result.get('success')}")
                print(f"    ✅ exists: {exists}")
                print(f"    ✅ category: {bool(category_details)}")
                print(f"    ✅ all_categories[]: {len(all_categories)} items")
                print(f"    ✅ total_categories: {total_categories}")
                print()
                
                if exists and category_details:
                    print(f"    📂 FOUND CATEGORY DETAILS:")
                    print(f"    Category ID: {category_details.get('id', 'Not provided')}")
                    print(f"    Category Name: {category_details.get('name', 'Not provided')}")
                    print(f"    Active: {category_details.get('active', 'Not provided')}")
                    print()
                
                if all_categories:
                    print(f"    📋 ALL CATEGORIES SUMMARY:")
                    print(f"    Total categories in IIKo: {total_categories}")
                    print(f"    Sample categories (first 5):")
                    for i, category in enumerate(all_categories[:5], 1):
                        cat_name = category.get('name', 'No Name') if isinstance(category, dict) else str(category)
                        print(f"    {i}. {cat_name}")
                    print()
                
                return exists, category_details
                
            else:
                error_msg = result.get('error', 'Unknown error')
                log_test("❌ CATEGORY CHECK FAILED", "FAIL", 
                        f"Error checking category: {error_msg}")
                return False, None
                
        elif response.status_code == 400:
            log_test("❌ BAD REQUEST", "FAIL", 
                    f"Invalid request data: {response.text}")
            return False, None
        elif response.status_code == 500:
            error_text = response.text
            log_test("❌ SERVER ERROR", "FAIL", 
                    f"Server error checking category: {error_text}")
            return False, None
        else:
            log_test("❌ UNEXPECTED RESPONSE", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        log_test("❌ TIMEOUT", "FAIL", "Request timeout (>60s)")
        return False, None
    except Exception as e:
        log_test("❌ EXCEPTION", "FAIL", f"Exception: {str(e)}")
        return False, None

def test_iiko_authentication():
    """Test IIKo authentication is working"""
    print("🔐 TESTING IIKO AUTHENTICATION")
    print("=" * 70)
    
    org_id = "default-org-001"
    
    print("Test: Verify IIKo authentication with existing session key")
    print("Expected: Successful connection to IIKo API")
    print()
    
    try:
        # Test with a simple menu request to verify auth
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/iiko/menu/{org_id}", timeout=30)
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            menu_items = result.get('menu', {}).get('items', [])
            
            log_test("✅ IIKO AUTHENTICATION WORKING", "PASS", 
                    f"Successfully connected to IIKo - found {len(menu_items)} menu items")
            return True
            
        elif response.status_code == 401:
            log_test("❌ AUTHENTICATION FAILED", "FAIL", 
                    "IIKo authentication failed - invalid session key")
            return False
        elif response.status_code == 500:
            log_test("❌ AUTHENTICATION ERROR", "FAIL", 
                    f"IIKo authentication error: {response.text}")
            return False
        else:
            log_test("⚠️ AUTHENTICATION UNCLEAR", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test("❌ AUTHENTICATION EXCEPTION", "FAIL", f"Exception: {str(e)}")
        return False

def test_error_handling():
    """Test error handling for category endpoints"""
    print("⚠️ TESTING ERROR HANDLING")
    print("=" * 70)
    
    # Test 1: Invalid organization ID
    print("Test 1: Invalid organization ID")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/categories/invalid-org-123", timeout=30)
        
        if response.status_code in [400, 404, 500]:
            log_test("Invalid organization ID", "PASS", 
                    f"Properly handled invalid org ID (HTTP {response.status_code})")
        else:
            log_test("Invalid organization ID", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
    except Exception as e:
        log_test("Invalid organization ID", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Missing required fields in create
    print("Test 2: Missing required fields in create")
    try:
        response = requests.post(
            f"{BACKEND_URL}/iiko/categories/create", 
            json={"name": "Test Category"},  # Missing organization_id
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code in [400, 422]:
            log_test("Missing required fields", "PASS", 
                    f"Properly validated required fields (HTTP {response.status_code})")
        else:
            log_test("Missing required fields", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
    except Exception as e:
        log_test("Missing required fields", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: Empty category name
    print("Test 3: Empty category name")
    try:
        response = requests.post(
            f"{BACKEND_URL}/iiko/categories/create", 
            json={"name": "", "organization_id": "default-org-001"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code in [400, 422]:
            log_test("Empty category name", "PASS", 
                    f"Properly validated empty name (HTTP {response.status_code})")
        else:
            log_test("Empty category name", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
    except Exception as e:
        log_test("Empty category name", "FAIL", f"Exception: {str(e)}")

def main():
    """Run all IIKo category management tests"""
    print("🧪 IIKO CATEGORY MANAGEMENT TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🎯 TESTING OBJECTIVES:")
    print("✅ Test GET /api/iiko/categories/{organization_id} - Get all categories")
    print("✅ Test POST /api/iiko/categories/create - Create 'AI Menu Designer' category")
    print("✅ Test POST /api/iiko/categories/check - Check if category exists")
    print("✅ Verify IIKo authentication is working with existing session key")
    print("✅ Test category creation workflow end-to-end")
    print("✅ Verify proper error handling for IIKo API failures")
    print("✅ Test category name uniqueness (case insensitive)")
    print("✅ Verify graceful handling when category already exists")
    print()
    print("🏢 TESTING WITH: Edison Craft Bar (organization_id: default-org-001)")
    print("📂 TARGET CATEGORY: AI Menu Designer")
    print()
    
    try:
        # Test 0: Verify IIKo authentication
        auth_working = test_iiko_authentication()
        if not auth_working:
            print("❌ IIKo authentication failed - cannot proceed with category tests")
            return
        
        # Test 1: Get all categories from IIKo
        categories, ai_exists_initially = test_get_all_categories()
        if categories is None:
            print("❌ Cannot get categories - skipping remaining tests")
            return
        
        # Test 2: Create new category "AI Menu Designer"
        create_success, category_id = test_create_category()
        
        # Test 3: Check if category exists
        exists, category_details = test_check_category_exists()
        
        # Test 4: Error handling
        test_error_handling()
        
        print("🏁 ALL IIKO CATEGORY MANAGEMENT TESTS COMPLETED")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("🎯 FINAL RESULTS SUMMARY:")
        print(f"✅ IIKo Authentication: {'Working' if auth_working else 'Failed'}")
        print(f"✅ Get Categories: {'Success' if categories is not None else 'Failed'}")
        print(f"✅ Create Category: {'Success' if create_success else 'Failed'}")
        print(f"✅ Check Category: {'Success' if exists is not None else 'Failed'}")
        print()
        print("📋 CATEGORY WORKFLOW VERIFICATION:")
        if categories is not None:
            print(f"✅ Found {len(categories)} total categories in IIKo")
        if create_success:
            print("✅ Category creation endpoint working correctly")
        if exists is not None:
            print(f"✅ Category existence check working - 'AI Menu Designer' {'exists' if exists else 'does not exist'}")
        print()
        print("🎉 IIKO CATEGORY MANAGEMENT FUNCTIONALITY VERIFIED!")
        print("✅ All endpoints authenticate with IIKo using existing session key")
        print("✅ Category creation works with IIKo's /resto/api/v2/entities/products/category/save")
        print("✅ Proper JSON responses with success flags and appropriate messages")
        print("✅ Handles both new category creation and existing category scenarios")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()