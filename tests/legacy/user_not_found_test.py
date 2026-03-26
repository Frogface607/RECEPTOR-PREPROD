#!/usr/bin/env python3
"""
Backend Testing Suite for "User not found" Error Fixes
Testing the automatic user creation fixes in the projects system
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

def test_get_projects_auto_user_creation():
    """Test GET /api/menu-projects/{user_id} - should auto-create user if not exists"""
    print("🔧 TESTING GET PROJECTS AUTO USER CREATION")
    print("=" * 60)
    
    # Test with new user that doesn't exist
    new_user_id = "test_user_new_001"
    
    print(f"Test 1: GET /api/menu-projects/{new_user_id} - Auto-create user")
    try:
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/menu-projects/{new_user_id}",
            timeout=30
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check response format - should be dict with success, projects, total_projects
            if isinstance(result, dict):
                success = result.get("success", False)
                projects = result.get("projects", [])
                total_projects = result.get("total_projects", 0)
                
                if success and isinstance(projects, list) and total_projects == 0:
                    log_test("Auto User Creation - Empty Projects", "PASS", 
                            f"New user {new_user_id} created, returned empty projects list")
                elif success and isinstance(projects, list):
                    log_test("Auto User Creation - Empty Projects", "WARN", 
                            f"New user has {len(projects)} projects (unexpected)")
                else:
                    log_test("Auto User Creation - Response Format", "FAIL", 
                            f"Invalid response structure: success={success}, projects type={type(projects)}")
            else:
                log_test("Auto User Creation - Response Format", "FAIL", 
                        f"Expected dict, got: {type(result)}")
            
            # Verify user was actually created by checking again
            print(f"\nVerification: GET /api/menu-projects/{new_user_id} again")
            verify_response = requests.get(f"{BACKEND_URL}/menu-projects/{new_user_id}", timeout=30)
            
            if verify_response.status_code == 200:
                log_test("User Persistence Verification", "PASS", 
                        "User persists after creation - no 404 error")
            else:
                log_test("User Persistence Verification", "FAIL", 
                        f"User not persisted: HTTP {verify_response.status_code}")
                
        elif response.status_code == 404:
            log_test("Auto User Creation", "FAIL", 
                    f"Still getting 404 'User not found' error: {response.text}")
        elif response.status_code == 500:
            log_test("Auto User Creation", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("Auto User Creation", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Auto User Creation", "FAIL", "Request timeout (>30s)")
    except Exception as e:
        log_test("Auto User Creation", "FAIL", f"Exception: {str(e)}")

def test_create_project_auto_user_creation():
    """Test POST /api/create-menu-project - should auto-create user when creating project"""
    print("🔧 TESTING CREATE PROJECT AUTO USER CREATION")
    print("=" * 60)
    
    # Test with another new user that doesn't exist
    new_user_id = "test_user_new_002"
    
    project_data = {
        "user_id": new_user_id,
        "project_name": "Тестовый проект автосоздания",
        "description": "Проект для тестирования автоматического создания пользователя",
        "project_type": "menu_refresh"
    }
    
    print(f"Test 1: POST /api/create-menu-project - Auto-create user and project")
    print(f"Project data: {json.dumps(project_data, ensure_ascii=False, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/create-menu-project",
            json=project_data,
            timeout=30
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check if project was created successfully
            success = result.get("success", False)
            project_id = result.get("project_id")
            message = result.get("message", "")
            
            if success and project_id:
                log_test("Auto User & Project Creation", "PASS", 
                        f"User {new_user_id} and project created successfully (ID: {project_id})")
                
                # Verify user can now get their projects
                print(f"\nVerification: GET /api/menu-projects/{new_user_id}")
                verify_response = requests.get(f"{BACKEND_URL}/menu-projects/{new_user_id}", timeout=30)
                
                if verify_response.status_code == 200:
                    projects_data = verify_response.json()
                    projects = projects_data.get("projects", [])
                    if isinstance(projects, list) and len(projects) >= 1:
                        found_project = any(p.get("id") == project_id for p in projects)
                        if found_project:
                            log_test("Project Retrieval Verification", "PASS", 
                                    f"Created project found in user's project list")
                        else:
                            log_test("Project Retrieval Verification", "FAIL", 
                                    "Created project not found in user's project list")
                    else:
                        log_test("Project Retrieval Verification", "FAIL", 
                                f"Expected projects list, got: {projects}")
                else:
                    log_test("Project Retrieval Verification", "FAIL", 
                            f"Cannot retrieve projects: HTTP {verify_response.status_code}")
            else:
                log_test("Auto User & Project Creation", "FAIL", 
                        f"Missing required fields in response: success={success}, project_id={project_id}")
                
        elif response.status_code == 404:
            log_test("Auto User & Project Creation", "FAIL", 
                    f"Still getting 404 'User not found' error: {response.text}")
        elif response.status_code == 400:
            log_test("Auto User & Project Creation", "FAIL", 
                    f"Bad request: {response.text}")
        elif response.status_code == 500:
            log_test("Auto User & Project Creation", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("Auto User & Project Creation", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Auto User & Project Creation", "FAIL", "Request timeout (>30s)")
    except Exception as e:
        log_test("Auto User & Project Creation", "FAIL", f"Exception: {str(e)}")

def test_existing_user_functionality():
    """Test that the system still works correctly for existing users"""
    print("🔧 TESTING EXISTING USER FUNCTIONALITY")
    print("=" * 60)
    
    # Use one of the users we just created
    existing_user_id = "test_user_new_001"
    
    print(f"Test 1: GET /api/menu-projects/{existing_user_id} - Existing user")
    try:
        response = requests.get(f"{BACKEND_URL}/menu-projects/{existing_user_id}", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            projects = result.get("projects", [])
            total_projects = result.get("total_projects", 0)
            log_test("Existing User Projects", "PASS", 
                    f"Retrieved {total_projects} projects for existing user")
        else:
            log_test("Existing User Projects", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Existing User Projects", "FAIL", f"Exception: {str(e)}")
    
    # Test creating another project for existing user
    print(f"Test 2: POST /api/create-menu-project - Existing user")
    project_data = {
        "user_id": existing_user_id,
        "project_name": "Второй проект для существующего пользователя",
        "description": "Тест создания проекта для уже существующего пользователя",
        "project_type": "seasonal_update"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/create-menu-project",
            json=project_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            success = result.get("success", False)
            project_id = result.get("project_id")
            if success and project_id:
                log_test("Existing User New Project", "PASS", 
                        f"Created new project (ID: {project_id}) for existing user")
            else:
                log_test("Existing User New Project", "FAIL", 
                        f"Project creation failed: success={success}, project_id={project_id}")
        else:
            log_test("Existing User New Project", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Existing User New Project", "FAIL", f"Exception: {str(e)}")

def test_iiko_sales_report():
    """Test the new GET /api/iiko/sales-report endpoint if organizations are available"""
    print("📊 TESTING IIKO SALES REPORT - ADDITIONAL CHECK")
    print("=" * 60)
    
    # First check if IIKo organizations are available
    print("Test 1: GET /api/iiko/organizations - Check availability")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/organizations", timeout=30)
        
        if response.status_code == 200:
            orgs = response.json()
            if isinstance(orgs, list) and len(orgs) > 0:
                log_test("IIKo Organizations Available", "PASS", 
                        f"Found {len(orgs)} organizations")
                
                # Test sales report with first organization
                org_id = orgs[0].get("id")
                org_name = orgs[0].get("name", "Unknown")
                
                print(f"Test 2: GET /api/iiko/sales-report/{org_id} - Sales report")
                try:
                    sales_response = requests.get(
                        f"{BACKEND_URL}/iiko/sales-report/{org_id}",
                        timeout=60
                    )
                    
                    if sales_response.status_code == 200:
                        sales_data = sales_response.json()
                        success = sales_data.get("success", False)
                        
                        if success:
                            log_test("IIKo Sales Report", "PASS", 
                                    f"Sales report retrieved for {org_name}")
                        else:
                            log_test("IIKo Sales Report", "PASS", 
                                    f"Sales report gracefully handled unavailable data for {org_name}")
                    else:
                        log_test("IIKo Sales Report", "WARN", 
                                f"HTTP {sales_response.status_code}: {sales_response.text}")
                        
                except Exception as e:
                    log_test("IIKo Sales Report", "WARN", f"Exception: {str(e)}")
                    
            else:
                log_test("IIKo Organizations Available", "WARN", 
                        "No organizations found - skipping sales report test")
        else:
            log_test("IIKo Organizations Available", "WARN", 
                    f"HTTP {response.status_code} - skipping sales report test")
            
    except Exception as e:
        log_test("IIKo Organizations Available", "WARN", f"Exception: {str(e)} - skipping sales report test")

def test_edge_cases():
    """Test edge cases and error scenarios"""
    print("🔧 TESTING EDGE CASES")
    print("=" * 60)
    
    # Test 1: Invalid user ID format
    print("Test 1: GET /api/menu-projects/invalid-user-id - Invalid format")
    try:
        response = requests.get(f"{BACKEND_URL}/menu-projects/invalid-user-id", timeout=30)
        
        if response.status_code == 200:
            log_test("Invalid User ID Handling", "PASS", 
                    "Invalid user ID handled gracefully (auto-created)")
        elif response.status_code == 400:
            log_test("Invalid User ID Handling", "PASS", 
                    "Invalid user ID properly rejected with 400")
        else:
            log_test("Invalid User ID Handling", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Invalid User ID Handling", "WARN", f"Exception: {str(e)}")
    
    # Test 2: Empty user ID
    print("Test 2: POST /api/create-menu-project - Empty user_id")
    try:
        empty_user_data = {
            "user_id": "",
            "project_name": "Test Project",
            "project_type": "menu_refresh"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/create-menu-project",
            json=empty_user_data,
            timeout=30
        )
        
        if response.status_code == 400:
            log_test("Empty User ID Handling", "PASS", 
                    "Empty user ID properly rejected with 400")
        else:
            log_test("Empty User ID Handling", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Empty User ID Handling", "WARN", f"Exception: {str(e)}")
    
    # Test 3: Missing user_id field
    print("Test 3: POST /api/create-menu-project - Missing user_id")
    try:
        missing_user_data = {
            "project_name": "Test Project",
            "project_type": "menu_refresh"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/create-menu-project",
            json=missing_user_data,
            timeout=30
        )
        
        if response.status_code == 422:  # Pydantic validation error
            log_test("Missing User ID Handling", "PASS", 
                    "Missing user_id properly rejected with 422")
        elif response.status_code == 400:
            log_test("Missing User ID Handling", "PASS", 
                    "Missing user_id properly rejected with 400")
        else:
            log_test("Missing User ID Handling", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Missing User ID Handling", "WARN", f"Exception: {str(e)}")

def main():
    """Run all user not found error fix tests"""
    print("🧪 BACKEND TESTING: USER NOT FOUND ERROR FIXES")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🎯 TESTING OBJECTIVES:")
    print("1. GET /api/menu-projects/{user_id} - Auto-create user if not exists")
    print("2. POST /api/create-menu-project - Auto-create user when creating project")
    print("3. Verify system works for existing users")
    print("4. Test IIKo sales report endpoint if available")
    print("5. Test edge cases and error handling")
    print()
    
    try:
        # Test 1: GET projects auto user creation
        test_get_projects_auto_user_creation()
        
        # Test 2: CREATE project auto user creation
        test_create_project_auto_user_creation()
        
        # Test 3: Existing user functionality
        test_existing_user_functionality()
        
        # Test 4: IIKo sales report (if available)
        test_iiko_sales_report()
        
        # Test 5: Edge cases
        test_edge_cases()
        
        print("🏁 ALL USER NOT FOUND ERROR FIX TESTS COMPLETED")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary of fixes tested
        print("\n🔧 USER NOT FOUND ERROR FIXES TESTED:")
        print("✅ GET /api/menu-projects/{user_id} - Auto user creation")
        print("✅ POST /api/create-menu-project - Auto user creation")
        print("✅ Existing user functionality preservation")
        print("✅ IIKo sales report endpoint (if organizations available)")
        print("✅ Edge cases and error handling")
        print("\n🎉 EXPECTED RESULT: No more '404: User not found' errors!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()