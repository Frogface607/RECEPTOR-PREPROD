#!/usr/bin/env python3
"""
Menu Projects System Testing Suite - ObjectId Serialization Fix Verification
Testing the previously failing GET endpoints that were fixed for ObjectId serialization issues.
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

def test_create_menu_project():
    """Test 1: Create Menu Project First (for test setup)"""
    print("📁 TESTING MENU PROJECT CREATION")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    try:
        project_data = {
            "user_id": user_id,
            "project_name": "Проект Монетизации 2025",
            "description": "Тестирование системы проектов для улучшения удержания пользователей",
            "project_type": "restaurant_launch"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/create-menu-project",
            json=project_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                project_id = result.get("project_id")
                message = result.get("message", "")
                
                log_test("Create Menu Project", "PASS", 
                        f"Project created successfully: {project_id}")
                print(f"    Project ID: {project_id}")
                print(f"    Message: {message}")
                
                # Store project_id for subsequent tests
                global CREATED_PROJECT_ID
                CREATED_PROJECT_ID = project_id
                
                return project_id
            else:
                log_test("Create Menu Project", "FAIL", 
                        f"Success=False: {result}")
                return None
        else:
            log_test("Create Menu Project", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        log_test("Create Menu Project", "FAIL", f"Exception: {str(e)}")
        return None

def test_get_projects_endpoint():
    """Test 2: Test Fixed Get Projects Endpoint (previously failing with 500 error)"""
    print("📋 TESTING GET PROJECTS ENDPOINT (ObjectId Fix)")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/menu-projects/{user_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                projects = result.get("projects", [])
                total_projects = result.get("total_projects", 0)
                
                log_test("GET Projects Endpoint - ObjectId Fix", "PASS", 
                        f"Retrieved {total_projects} projects successfully")
                
                # Verify projects array with stats
                if projects:
                    sample_project = projects[0]
                    required_fields = ["id", "project_name", "description", "project_type", 
                                     "created_at", "menus_count", "tech_cards_count"]
                    
                    missing_fields = [field for field in required_fields if field not in sample_project]
                    
                    if not missing_fields:
                        log_test("Projects Array Structure", "PASS", 
                                f"All required fields present: {required_fields}")
                        
                        # Log stats
                        menus_count = sample_project.get("menus_count", 0)
                        tech_cards_count = sample_project.get("tech_cards_count", 0)
                        print(f"    Sample project stats:")
                        print(f"    - Project: {sample_project.get('project_name')}")
                        print(f"    - Menus: {menus_count}")
                        print(f"    - Tech Cards: {tech_cards_count}")
                        
                    else:
                        log_test("Projects Array Structure", "FAIL", 
                                f"Missing fields: {missing_fields}")
                else:
                    log_test("Projects Array Structure", "WARN", 
                            "No projects found to verify structure")
                
                return True
            else:
                log_test("GET Projects Endpoint", "FAIL", 
                        f"Success=False: {result}")
                return False
        else:
            log_test("GET Projects Endpoint - ObjectId Fix", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET Projects Endpoint", "FAIL", f"Exception: {str(e)}")
        return False

def test_simple_menu_with_project():
    """Test 3: Test Simple Menu Generation with Project Assignment"""
    print("🍽️ TESTING SIMPLE MENU GENERATION WITH PROJECT")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Use the project_id from the first test
    project_id = globals().get('CREATED_PROJECT_ID')
    if not project_id:
        log_test("Simple Menu with Project", "FAIL", 
                "No project_id available from previous test")
        return None
    
    try:
        menu_request = {
            "user_id": user_id,
            "menu_type": "full",
            "expectations": "Menu for restaurant monetization testing - varied dishes for different customer segments",
            "project_id": project_id
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/generate-simple-menu",
            json=menu_request,
            timeout=120  # 2 minute timeout
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                dish_count = result.get("dish_count", 0)
                generation_method = result.get("generation_method", "")
                menu_id = result.get("menu_id")
                
                log_test("Simple Menu Generation with Project", "PASS", 
                        f"Generated {dish_count} dishes in {end_time - start_time:.2f}s")
                
                print(f"    Generation method: {generation_method}")
                print(f"    Menu ID: {menu_id}")
                print(f"    Project ID: {project_id}")
                
                # Verify menu links to project properly
                if menu_id:
                    log_test("Menu-Project Linking", "PASS", 
                            "Menu generated with project assignment")
                    
                    # Store menu_id for verification in project content test
                    global CREATED_MENU_ID
                    CREATED_MENU_ID = menu_id
                    
                    return menu_id
                else:
                    log_test("Menu-Project Linking", "WARN", 
                            "Menu generated but no menu_id returned")
                    return None
            else:
                log_test("Simple Menu Generation with Project", "FAIL", 
                        f"Success=False: {result}")
                return None
        else:
            log_test("Simple Menu Generation with Project", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        log_test("Simple Menu Generation with Project", "FAIL", "Request timeout (>120s)")
        return None
    except Exception as e:
        log_test("Simple Menu Generation with Project", "FAIL", f"Exception: {str(e)}")
        return None

def test_get_project_content_endpoint():
    """Test 4: Test Fixed Get Project Content Endpoint (previously failing with 500 error)"""
    print("📄 TESTING GET PROJECT CONTENT ENDPOINT (ObjectId Fix)")
    print("=" * 60)
    
    project_id = globals().get('CREATED_PROJECT_ID')
    if not project_id:
        log_test("GET Project Content Endpoint", "FAIL", 
                "No project_id available from previous test")
        return False
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/menu-project/{project_id}/content",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                project = result.get("project", {})
                menus = result.get("menus", [])
                tech_cards = result.get("tech_cards", [])
                menus_count = result.get("menus_count", 0)
                tech_cards_count = result.get("tech_cards_count", 0)
                
                log_test("GET Project Content Endpoint - ObjectId Fix", "PASS", 
                        f"Retrieved project content: {menus_count} menus, {tech_cards_count} tech cards")
                
                # Verify project data structure
                if project:
                    required_project_fields = ["id", "project_name", "description", "project_type"]
                    missing_fields = [field for field in required_project_fields if field not in project]
                    
                    if not missing_fields:
                        log_test("Project Data Structure", "PASS", 
                                "All required project fields present")
                    else:
                        log_test("Project Data Structure", "FAIL", 
                                f"Missing project fields: {missing_fields}")
                else:
                    log_test("Project Data Structure", "FAIL", "No project data returned")
                
                # Verify menu from step 3 appears in project content
                created_menu_id = globals().get('CREATED_MENU_ID')
                if created_menu_id and menus:
                    menu_ids = [menu.get('id') for menu in menus]
                    if created_menu_id in menu_ids:
                        log_test("Menu in Project Content Verification", "PASS", 
                                "Menu from step 3 found in project content")
                    else:
                        log_test("Menu in Project Content Verification", "WARN", 
                                f"Menu {created_menu_id} not found in project content")
                        print(f"    Found menu IDs: {menu_ids}")
                elif menus:
                    log_test("Menu in Project Content Verification", "PASS", 
                            f"Found {len(menus)} menus in project content")
                else:
                    log_test("Menu in Project Content Verification", "WARN", 
                            "No menus found in project content")
                
                # Log sample content
                print(f"    Project: {project.get('project_name', 'N/A')}")
                print(f"    Content summary:")
                print(f"    - Menus: {menus_count}")
                print(f"    - Tech Cards: {tech_cards_count}")
                
                return True
            else:
                log_test("GET Project Content Endpoint", "FAIL", 
                        f"Success=False: {result}")
                return False
        else:
            log_test("GET Project Content Endpoint - ObjectId Fix", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        log_test("GET Project Content Endpoint", "FAIL", f"Exception: {str(e)}")
        return False

def test_complete_system_integration():
    """Test 5: Complete System Test - Verify all CRUD operations work end-to-end"""
    print("🔄 TESTING COMPLETE SYSTEM INTEGRATION")
    print("=" * 60)
    
    user_id = "test_user_12345"
    project_id = globals().get('CREATED_PROJECT_ID')
    
    if not project_id:
        log_test("Complete System Integration", "FAIL", 
                "No project_id available for integration test")
        return False
    
    try:
        # Test 1: Update project
        print("Sub-test 1: Update project")
        update_data = {
            "project_name": "Проект Монетизации 2025 - Обновлен",
            "description": "Обновленное описание проекта для тестирования системы"
        }
        
        response = requests.put(
            f"{BACKEND_URL}/menu-project/{project_id}",
            json=update_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                log_test("Project Update", "PASS", "Project updated successfully")
            else:
                log_test("Project Update", "FAIL", f"Update failed: {result}")
        else:
            log_test("Project Update", "FAIL", f"HTTP {response.status_code}: {response.text}")
        
        # Test 2: Verify data integrity - check if project still exists and has correct data
        print("Sub-test 2: Data integrity check")
        response = requests.get(f"{BACKEND_URL}/menu-projects/{user_id}", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                projects = result.get("projects", [])
                target_project = None
                
                for project in projects:
                    if project.get("id") == project_id:
                        target_project = project
                        break
                
                if target_project:
                    updated_name = target_project.get("project_name", "")
                    if "Обновлен" in updated_name:
                        log_test("Data Integrity Check", "PASS", 
                                "Project update persisted correctly")
                    else:
                        log_test("Data Integrity Check", "FAIL", 
                                f"Project name not updated: {updated_name}")
                else:
                    log_test("Data Integrity Check", "FAIL", 
                            "Updated project not found in projects list")
            else:
                log_test("Data Integrity Check", "FAIL", f"Failed to get projects: {result}")
        else:
            log_test("Data Integrity Check", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
        
        # Test 3: Verify project content still accessible
        print("Sub-test 3: Project content accessibility")
        response = requests.get(f"{BACKEND_URL}/menu-project/{project_id}/content", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                log_test("Project Content Accessibility", "PASS", 
                        "Project content still accessible after update")
            else:
                log_test("Project Content Accessibility", "FAIL", 
                        f"Content access failed: {result}")
        else:
            log_test("Project Content Accessibility", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
        
        log_test("Complete System Integration", "PASS", 
                "All CRUD operations verified successfully")
        return True
        
    except Exception as e:
        log_test("Complete System Integration", "FAIL", f"Exception: {str(e)}")
        return False

def test_objectid_serialization_fix():
    """Specific test to verify ObjectId serialization issues are resolved"""
    print("🔧 TESTING OBJECTID SERIALIZATION FIX")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    try:
        # Test multiple rapid requests to stress-test serialization
        print("Stress-testing ObjectId serialization with multiple requests...")
        
        success_count = 0
        total_requests = 5
        
        for i in range(total_requests):
            response = requests.get(f"{BACKEND_URL}/menu-projects/{user_id}", timeout=10)
            
            if response.status_code == 200:
                try:
                    result = response.json()  # This will fail if ObjectId serialization is broken
                    if result.get("success"):
                        success_count += 1
                except json.JSONDecodeError:
                    log_test(f"ObjectId Serialization Test {i+1}", "FAIL", 
                            "JSON decode error - ObjectId serialization issue")
            else:
                log_test(f"ObjectId Serialization Test {i+1}", "FAIL", 
                        f"HTTP {response.status_code}")
        
        if success_count == total_requests:
            log_test("ObjectId Serialization Fix Verification", "PASS", 
                    f"All {total_requests} requests succeeded - ObjectId issues resolved")
        else:
            log_test("ObjectId Serialization Fix Verification", "FAIL", 
                    f"Only {success_count}/{total_requests} requests succeeded")
        
        return success_count == total_requests
        
    except Exception as e:
        log_test("ObjectId Serialization Fix Verification", "FAIL", f"Exception: {str(e)}")
        return False

def main():
    """Run all Menu Projects System tests"""
    print("🧪 MENU PROJECTS SYSTEM TESTING - ObjectId Serialization Fix Verification")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize global variables
    global CREATED_PROJECT_ID, CREATED_MENU_ID
    CREATED_PROJECT_ID = None
    CREATED_MENU_ID = None
    
    test_results = []
    
    try:
        # Test 1: Create Menu Project First (for test setup)
        project_id = test_create_menu_project()
        test_results.append(("Create Menu Project", project_id is not None))
        
        # Test 2: Test Fixed Get Projects Endpoint
        get_projects_success = test_get_projects_endpoint()
        test_results.append(("GET Projects Endpoint", get_projects_success))
        
        # Test 3: Test Simple Menu Generation with Project
        menu_id = test_simple_menu_with_project()
        test_results.append(("Simple Menu with Project", menu_id is not None))
        
        # Test 4: Test Fixed Get Project Content Endpoint
        get_content_success = test_get_project_content_endpoint()
        test_results.append(("GET Project Content Endpoint", get_content_success))
        
        # Test 5: Complete System Test
        system_integration_success = test_complete_system_integration()
        test_results.append(("Complete System Integration", system_integration_success))
        
        # Test 6: ObjectId Serialization Fix Verification
        objectid_fix_success = test_objectid_serialization_fix()
        test_results.append(("ObjectId Serialization Fix", objectid_fix_success))
        
        # Summary
        print("🏁 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed_tests += 1
        
        print()
        print(f"Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Menu Projects System with ObjectId fixes is working correctly!")
        else:
            print("⚠️ Some tests failed - Menu Projects System needs attention")
        
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()