#!/usr/bin/env python3
"""
Menu Projects System Backend Testing Suite
Testing all new Menu Projects endpoints as specified in the review request
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cc951b09-9773-4d61-a26a-ba72b5f2050b.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_create_menu_project():
    """Test 1: Create Menu Project Test - POST /api/create-menu-project"""
    print("🎯 TEST 1: CREATE MENU PROJECT")
    print("=" * 60)
    
    # Test data as specified in review request
    test_data = {
        "user_id": "test_user_12345",
        "project_name": "Летнее меню 2025",
        "description": "Сезонное обновление меню с акцентом на свежие салаты и холодные супы",
        "project_type": "seasonal_update",
        "venue_type": "family_restaurant"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/create-menu-project", json=test_data)
        response_time = time.time() - start_time
        
        print(f"Request URL: POST {BACKEND_URL}/create-menu-project")
        print(f"Request Data: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Data: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Verify project creation success and proper ID generation
            if result.get("success") and result.get("project_id"):
                project_id = result.get("project_id")
                log_test("Create Menu Project", "PASS", f"Project created successfully with ID: {project_id}")
                return project_id
            else:
                log_test("Create Menu Project", "FAIL", "Missing success flag or project_id in response")
                return None
        else:
            error_text = response.text
            log_test("Create Menu Project", "FAIL", f"HTTP {response.status_code}: {error_text}")
            return None
            
    except Exception as e:
        log_test("Create Menu Project", "FAIL", f"Exception: {str(e)}")
        return None

def test_get_user_projects():
    """Test 2: Get User Projects Test - GET /api/menu-projects/{user_id}"""
    print("🎯 TEST 2: GET USER PROJECTS")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/menu-projects/{user_id}")
        response_time = time.time() - start_time
        
        print(f"Request URL: GET {BACKEND_URL}/menu-projects/{user_id}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Data: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Verify projects list with stats (menus_count, tech_cards_count)
            if "projects" in result:
                projects = result["projects"]
                log_test("Get User Projects", "PASS", f"Retrieved {len(projects)} projects")
                
                # Check response structure and project details
                for project in projects:
                    required_fields = ["id", "project_name", "description", "project_type", "created_at"]
                    missing_fields = [field for field in required_fields if field not in project]
                    if missing_fields:
                        log_test("Project Structure", "FAIL", f"Missing fields: {missing_fields}")
                    else:
                        log_test("Project Structure", "PASS", "All required fields present")
                
                return projects
            else:
                log_test("Get User Projects", "FAIL", "Missing 'projects' field in response")
                return []
        else:
            error_text = response.text
            log_test("Get User Projects", "FAIL", f"HTTP {response.status_code}: {error_text}")
            return []
            
    except Exception as e:
        log_test("Get User Projects", "FAIL", f"Exception: {str(e)}")
        return []

def test_simple_menu_generation_with_project(project_id):
    """Test 3: Simple Menu Generation with Project Test"""
    print("🎯 TEST 3: SIMPLE MENU GENERATION WITH PROJECT")
    print("=" * 60)
    
    if not project_id:
        log_test("Simple Menu Generation with Project", "SKIP", "No project_id available from previous test")
        return None
    
    # Test data as specified in review request
    test_data = {
        "user_id": "test_user_12345",
        "menu_type": "seasonal",
        "expectations": "Light summer dishes, cold soups, fresh salads, grilled fish",
        "project_id": project_id
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-simple-menu", json=test_data)
        response_time = time.time() - start_time
        
        print(f"Request URL: POST {BACKEND_URL}/generate-simple-menu")
        print(f"Request Data: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Data: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Verify menu is linked to project correctly
            if result.get("success") and result.get("menu_id"):
                menu_id = result.get("menu_id")
                # Check if project_id is referenced in the response
                if result.get("project_id") == project_id:
                    log_test("Simple Menu Generation with Project", "PASS", f"Menu created and linked to project {project_id}")
                    return menu_id
                else:
                    log_test("Simple Menu Generation with Project", "FAIL", "Menu not properly linked to project")
                    return None
            else:
                log_test("Simple Menu Generation with Project", "FAIL", "Missing success flag or menu_id in response")
                return None
        else:
            error_text = response.text
            log_test("Simple Menu Generation with Project", "FAIL", f"HTTP {response.status_code}: {error_text}")
            return None
            
    except Exception as e:
        log_test("Simple Menu Generation with Project", "FAIL", f"Exception: {str(e)}")
        return None

def test_get_project_content(project_id):
    """Test 4: Get Project Content Test - GET /api/menu-project/{project_id}/content"""
    print("🎯 TEST 4: GET PROJECT CONTENT")
    print("=" * 60)
    
    if not project_id:
        log_test("Get Project Content", "SKIP", "No project_id available from previous test")
        return
    
    try:
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/menu-project/{project_id}/content")
        response_time = time.time() - start_time
        
        print(f"Request URL: GET {BACKEND_URL}/menu-project/{project_id}/content")
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Data: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Verify it returns project details with associated menus and tech cards
            required_fields = ["project", "menus", "tech_cards"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                project_data = result["project"]
                menus = result["menus"]
                tech_cards = result["tech_cards"]
                
                log_test("Get Project Content", "PASS", f"Project content retrieved: {len(menus)} menus, {len(tech_cards)} tech cards")
                
                # Check that menu created in step 3 appears in project content
                if len(menus) > 0:
                    log_test("Menu in Project Content", "PASS", "Menu appears in project content")
                else:
                    log_test("Menu in Project Content", "FAIL", "No menus found in project content")
            else:
                log_test("Get Project Content", "FAIL", f"Missing required fields: {missing_fields}")
        else:
            error_text = response.text
            log_test("Get Project Content", "FAIL", f"HTTP {response.status_code}: {error_text}")
            
    except Exception as e:
        log_test("Get Project Content", "FAIL", f"Exception: {str(e)}")

def test_update_project(project_id):
    """Test 5: Update Project Test - PUT /api/menu-project/{project_id}"""
    print("🎯 TEST 5: UPDATE PROJECT")
    print("=" * 60)
    
    if not project_id:
        log_test("Update Project", "SKIP", "No project_id available from previous test")
        return
    
    # Test updating project name and description
    update_data = {
        "project_name": "Обновленное летнее меню 2025",
        "description": "Обновленное сезонное меню с расширенным ассортиментом холодных блюд и освежающих напитков"
    }
    
    try:
        start_time = time.time()
        response = requests.put(f"{BACKEND_URL}/menu-project/{project_id}", json=update_data)
        response_time = time.time() - start_time
        
        print(f"Request URL: PUT {BACKEND_URL}/menu-project/{project_id}")
        print(f"Request Data: {json.dumps(update_data, ensure_ascii=False, indent=2)}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Data: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Verify update success
            if result.get("success"):
                log_test("Update Project", "PASS", "Project updated successfully")
            else:
                log_test("Update Project", "FAIL", "Missing success flag in response")
        else:
            error_text = response.text
            log_test("Update Project", "FAIL", f"HTTP {response.status_code}: {error_text}")
            
    except Exception as e:
        log_test("Update Project", "FAIL", f"Exception: {str(e)}")

def main():
    """Run all Menu Projects System tests"""
    print("🚀 MENU PROJECTS SYSTEM BACKEND TESTING SUITE")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Test 1: Create Menu Project
    project_id = test_create_menu_project()
    
    # Test 2: Get User Projects
    test_get_user_projects()
    
    # Test 3: Simple Menu Generation with Project
    menu_id = test_simple_menu_generation_with_project(project_id)
    
    # Test 4: Get Project Content
    test_get_project_content(project_id)
    
    # Test 5: Update Project
    test_update_project(project_id)
    
    print("=" * 80)
    print("🎉 MENU PROJECTS SYSTEM TESTING COMPLETED")
    print(f"Test Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()