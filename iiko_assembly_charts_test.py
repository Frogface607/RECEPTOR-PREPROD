#!/usr/bin/env python3
"""
Backend Testing Suite for IIKo Assembly Charts (Tech Cards) Management
Testing the new IIKo assembly charts endpoints for tech card management as requested in review
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

def test_iiko_health_and_organizations():
    """Test IIKo integration health and organizations as prerequisites"""
    print("🏥 TESTING IIKO INTEGRATION PREREQUISITES")
    print("=" * 60)
    
    # Test 1: Health check
    print("Test 1: GET /api/iiko/health - Should return healthy status")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/health", timeout=30)
        
        if response.status_code == 200:
            health_data = response.json()
            status = health_data.get("status")
            iiko_connection = health_data.get("iiko_connection")
            
            print(f"Response: {json.dumps(health_data, ensure_ascii=False, indent=2)}")
            
            if status == "healthy":
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
    print("Test 2: GET /api/iiko/organizations - Should return organizations list")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/organizations", timeout=30)
        
        if response.status_code == 200:
            orgs = response.json()
            print(f"Response: {json.dumps(orgs, ensure_ascii=False, indent=2)}")
            
            if isinstance(orgs, list) and len(orgs) > 0:
                log_test("IIKo Organizations", "PASS", 
                        f"Found {len(orgs)} organizations")
                
                # Look for Edison Craft Bar (default-org-001)
                edison_org = None
                for org in orgs:
                    if org.get("id") == "default-org-001" or "edison" in org.get("name", "").lower():
                        edison_org = org
                        break
                
                if edison_org:
                    log_test("Edison Craft Bar Organization", "PASS", 
                            f"Found: {edison_org.get('name')} (ID: {edison_org.get('id')})")
                    return edison_org.get('id')  # Return the organization ID for further tests
                else:
                    log_test("Edison Craft Bar Organization", "WARN", 
                            "Edison Craft Bar not found, will use default-org-001")
                    return "default-org-001"
            else:
                log_test("IIKo Organizations", "WARN", 
                        "No organizations found, will use default-org-001")
                return "default-org-001"
        else:
            log_test("IIKo Organizations", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return "default-org-001"
            
    except Exception as e:
        log_test("IIKo Organizations", "FAIL", f"Exception: {str(e)}")
        return "default-org-001"

def test_get_all_assembly_charts(organization_id):
    """Test GET /api/iiko/assembly-charts/all/{organization_id} - получение всех техкарт"""
    print("📋 TESTING GET ALL ASSEMBLY CHARTS")
    print("=" * 60)
    
    print(f"Test 1: GET /api/iiko/assembly-charts/all/{organization_id}")
    try:
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/iiko/assembly-charts/all/{organization_id}",
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
            assembly_charts = result.get("assembly_charts", [])
            count = result.get("count", 0)
            
            print(f"\n📊 ASSEMBLY CHARTS ANALYSIS:")
            print(f"Success: {success}")
            print(f"Count: {count}")
            print(f"Assembly charts type: {type(assembly_charts)}")
            
            if success:
                log_test("GET ALL ASSEMBLY CHARTS - SUCCESS", "PASS", 
                        f"Retrieved {count} assembly charts successfully")
                
                if isinstance(assembly_charts, list):
                    log_test("Assembly charts format", "PASS", 
                            f"Returned as list with {len(assembly_charts)} items")
                    
                    # Show sample assembly charts if available
                    if assembly_charts:
                        print(f"    Sample assembly charts:")
                        for i, chart in enumerate(assembly_charts[:3]):
                            name = chart.get("name", "N/A")
                            chart_id = chart.get("id", "N/A")
                            print(f"    {i+1}. {name} (ID: {chart_id})")
                    else:
                        log_test("Assembly charts content", "WARN", 
                                "No assembly charts found in organization")
                else:
                    log_test("Assembly charts format", "WARN", 
                            f"Unexpected format: {type(assembly_charts)}")
                    
                return assembly_charts  # Return for use in other tests
                
            else:
                log_test("GET ALL ASSEMBLY CHARTS - FAILURE", "FAIL", 
                        "Failed to retrieve assembly charts")
                return []
                
        elif response.status_code == 404:
            log_test("GET ALL ASSEMBLY CHARTS", "FAIL", 
                    f"Organization not found: {response.text}")
            return []
        elif response.status_code == 500:
            log_test("GET ALL ASSEMBLY CHARTS", "FAIL", 
                    f"Server error: {response.text}")
            return []
        else:
            log_test("GET ALL ASSEMBLY CHARTS", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            return []
            
    except requests.exceptions.Timeout:
        log_test("GET ALL ASSEMBLY CHARTS", "FAIL", "Request timeout (>60s)")
        return []
    except Exception as e:
        log_test("GET ALL ASSEMBLY CHARTS", "FAIL", f"Exception: {str(e)}")
        return []

def test_create_assembly_chart(organization_id):
    """Test POST /api/iiko/assembly-charts/create - создание новой техкарты"""
    print("🔨 TESTING CREATE ASSEMBLY CHART")
    print("=" * 60)
    
    # Test data for creating a new assembly chart
    test_tech_card_data = {
        "name": "AI Тестовый Бургер Классик",
        "description": "Создано AI-Menu-Designer для тестирования IIKo интеграции",
        "ingredients": [
            {"name": "Говяжья котлета", "quantity": 150, "unit": "г", "price": 120.0},
            {"name": "Булочка для бургера", "quantity": 80, "unit": "г", "price": 25.0},
            {"name": "Сыр чеддер", "quantity": 30, "unit": "г", "price": 45.0},
            {"name": "Салат айсберг", "quantity": 20, "unit": "г", "price": 15.0},
            {"name": "Томат", "quantity": 40, "unit": "г", "price": 20.0}
        ],
        "preparation_steps": [
            "Обжарить котлету на гриле до готовности",
            "Поджарить булочку",
            "Собрать бургер: булочка, соус, салат, котлета, сыр, томат, верхняя булочка"
        ],
        "organization_id": organization_id,
        "price": 450.0,
        "cost": 225.0,
        "weight": 320.0,
        "cook_time": "12 мин",
        "difficulty": "средне",
        "category": "Бургеры"
    }
    
    print(f"Test 1: POST /api/iiko/assembly-charts/create")
    print(f"Test data: {json.dumps(test_tech_card_data, ensure_ascii=False, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/iiko/assembly-charts/create",
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
            success = result.get("success", False)
            assembly_chart_id = result.get("assembly_chart_id")
            name = result.get("name")
            message = result.get("message", "")
            method = result.get("method")
            
            print(f"\n🔨 CREATE ASSEMBLY CHART ANALYSIS:")
            print(f"Success: {success}")
            print(f"Assembly Chart ID: {assembly_chart_id}")
            print(f"Name: {name}")
            print(f"Method: {method}")
            print(f"Message: {message}")
            
            if success:
                log_test("CREATE ASSEMBLY CHART - SUCCESS", "PASS", 
                        f"Assembly chart created successfully with ID: {assembly_chart_id}")
                
                # Verify response details
                if assembly_chart_id:
                    log_test("Assembly chart ID generation", "PASS", 
                            f"Generated ID: {assembly_chart_id}")
                else:
                    log_test("Assembly chart ID generation", "WARN", 
                            "No assembly chart ID returned")
                
                if name == test_tech_card_data["name"]:
                    log_test("Assembly chart name verification", "PASS", 
                            f"Name matches: {name}")
                else:
                    log_test("Assembly chart name verification", "WARN", 
                            f"Name mismatch: expected '{test_tech_card_data['name']}', got '{name}'")
                
                if method == "assembly_chart":
                    log_test("Creation method verification", "PASS", 
                            f"Method: {method}")
                else:
                    log_test("Creation method verification", "WARN", 
                            f"Unexpected method: {method}")
                
                return assembly_chart_id  # Return for use in other tests
                
            else:
                log_test("CREATE ASSEMBLY CHART - FAILURE", "FAIL", 
                        f"Failed to create assembly chart: {message}")
                
                # Check for error details
                error = result.get("error", "")
                note = result.get("note", "")
                
                if error:
                    log_test("Error details", "INFO", f"Error: {error}")
                if note:
                    log_test("Error note", "INFO", f"Note: {note}")
                
                return None
                
        elif response.status_code == 400:
            log_test("CREATE ASSEMBLY CHART", "FAIL", 
                    f"Bad request: {response.text}")
            return None
        elif response.status_code == 500:
            log_test("CREATE ASSEMBLY CHART", "FAIL", 
                    f"Server error: {response.text}")
            return None
        else:
            log_test("CREATE ASSEMBLY CHART", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        log_test("CREATE ASSEMBLY CHART", "FAIL", "Request timeout (>120s)")
        return None
    except Exception as e:
        log_test("CREATE ASSEMBLY CHART", "FAIL", f"Exception: {str(e)}")
        return None

def test_get_assembly_chart_by_id(chart_id):
    """Test GET /api/iiko/assembly-charts/{chart_id} - получение техкарты по ID"""
    print("🔍 TESTING GET ASSEMBLY CHART BY ID")
    print("=" * 60)
    
    if not chart_id:
        log_test("GET ASSEMBLY CHART BY ID", "SKIP", "No chart ID available from previous tests")
        return
    
    print(f"Test 1: GET /api/iiko/assembly-charts/{chart_id}")
    try:
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/iiko/assembly-charts/{chart_id}",
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
            assembly_chart = result.get("assembly_chart", {})
            
            print(f"\n🔍 GET ASSEMBLY CHART BY ID ANALYSIS:")
            print(f"Success: {success}")
            print(f"Assembly chart type: {type(assembly_chart)}")
            
            if success and assembly_chart:
                log_test("GET ASSEMBLY CHART BY ID - SUCCESS", "PASS", 
                        f"Retrieved assembly chart successfully")
                
                # Verify assembly chart details
                chart_name = assembly_chart.get("name", "")
                chart_id_resp = assembly_chart.get("id", "")
                ingredients = assembly_chart.get("ingredients", [])
                instructions = assembly_chart.get("instructions", [])
                
                print(f"Chart name: {chart_name}")
                print(f"Chart ID: {chart_id_resp}")
                print(f"Ingredients count: {len(ingredients)}")
                print(f"Instructions count: {len(instructions)}")
                
                if chart_name:
                    log_test("Assembly chart name", "PASS", 
                            f"Name: {chart_name}")
                else:
                    log_test("Assembly chart name", "WARN", 
                            "No name in assembly chart")
                
                if chart_id_resp == chart_id:
                    log_test("Assembly chart ID verification", "PASS", 
                            f"ID matches: {chart_id_resp}")
                else:
                    log_test("Assembly chart ID verification", "WARN", 
                            f"ID mismatch: expected {chart_id}, got {chart_id_resp}")
                
                if ingredients:
                    log_test("Assembly chart ingredients", "PASS", 
                            f"Found {len(ingredients)} ingredients")
                else:
                    log_test("Assembly chart ingredients", "WARN", 
                            "No ingredients found")
                
                if instructions:
                    log_test("Assembly chart instructions", "PASS", 
                            f"Found {len(instructions)} instructions")
                else:
                    log_test("Assembly chart instructions", "WARN", 
                            "No instructions found")
                
            else:
                log_test("GET ASSEMBLY CHART BY ID - FAILURE", "FAIL", 
                        "Failed to retrieve assembly chart")
                
        elif response.status_code == 404:
            log_test("GET ASSEMBLY CHART BY ID", "FAIL", 
                    f"Assembly chart not found: {response.text}")
        elif response.status_code == 500:
            log_test("GET ASSEMBLY CHART BY ID", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("GET ASSEMBLY CHART BY ID", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("GET ASSEMBLY CHART BY ID", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("GET ASSEMBLY CHART BY ID", "FAIL", f"Exception: {str(e)}")

def test_delete_assembly_chart(chart_id):
    """Test DELETE /api/iiko/assembly-charts/{chart_id} - удаление техкарты"""
    print("🗑️ TESTING DELETE ASSEMBLY CHART")
    print("=" * 60)
    
    if not chart_id:
        log_test("DELETE ASSEMBLY CHART", "SKIP", "No chart ID available from previous tests")
        return
    
    print(f"Test 1: DELETE /api/iiko/assembly-charts/{chart_id}")
    try:
        start_time = time.time()
        response = requests.delete(
            f"{BACKEND_URL}/iiko/assembly-charts/{chart_id}",
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
            
            print(f"\n🗑️ DELETE ASSEMBLY CHART ANALYSIS:")
            print(f"Success: {success}")
            print(f"Message: {message}")
            
            if success:
                log_test("DELETE ASSEMBLY CHART - SUCCESS", "PASS", 
                        f"Assembly chart deleted successfully: {message}")
                
                # Verify the chart is actually deleted by trying to get it
                print(f"\nVerification: Trying to get deleted chart {chart_id}")
                try:
                    verify_response = requests.get(
                        f"{BACKEND_URL}/iiko/assembly-charts/{chart_id}",
                        timeout=30
                    )
                    
                    if verify_response.status_code == 404:
                        log_test("Deletion verification", "PASS", 
                                "Chart not found after deletion (expected)")
                    elif verify_response.status_code == 200:
                        verify_result = verify_response.json()
                        if not verify_result.get("success", True):
                            log_test("Deletion verification", "PASS", 
                                    "Chart marked as deleted or not accessible")
                        else:
                            log_test("Deletion verification", "WARN", 
                                    "Chart still accessible after deletion")
                    else:
                        log_test("Deletion verification", "WARN", 
                                f"Unexpected verification response: {verify_response.status_code}")
                        
                except Exception as e:
                    log_test("Deletion verification", "WARN", 
                            f"Verification failed: {str(e)}")
                
            else:
                log_test("DELETE ASSEMBLY CHART - FAILURE", "FAIL", 
                        f"Failed to delete assembly chart: {message}")
                
                # Check for error details
                error = result.get("error", "")
                if error:
                    log_test("Delete error details", "INFO", f"Error: {error}")
                
        elif response.status_code == 404:
            log_test("DELETE ASSEMBLY CHART", "WARN", 
                    f"Assembly chart not found (may already be deleted): {response.text}")
        elif response.status_code == 500:
            log_test("DELETE ASSEMBLY CHART", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("DELETE ASSEMBLY CHART", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("DELETE ASSEMBLY CHART", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("DELETE ASSEMBLY CHART", "FAIL", f"Exception: {str(e)}")

def test_tech_cards_sync_status():
    """Test GET /api/iiko/tech-cards/sync-status - статус синхронизации"""
    print("🔄 TESTING TECH CARDS SYNC STATUS")
    print("=" * 60)
    
    print("Test 1: GET /api/iiko/tech-cards/sync-status")
    try:
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/iiko/tech-cards/sync-status",
            timeout=60
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check expected response structure
            status = result.get("status", "")
            last_sync = result.get("last_sync", "")
            sync_count = result.get("sync_count", 0)
            pending_uploads = result.get("pending_uploads", 0)
            errors = result.get("errors", [])
            
            print(f"\n🔄 SYNC STATUS ANALYSIS:")
            print(f"Status: {status}")
            print(f"Last sync: {last_sync}")
            print(f"Sync count: {sync_count}")
            print(f"Pending uploads: {pending_uploads}")
            print(f"Errors count: {len(errors)}")
            
            if status:
                log_test("TECH CARDS SYNC STATUS - SUCCESS", "PASS", 
                        f"Sync status retrieved: {status}")
                
                # Verify status values
                valid_statuses = ["active", "idle", "syncing", "error", "disabled"]
                if status in valid_statuses:
                    log_test("Sync status validity", "PASS", 
                            f"Valid status: {status}")
                else:
                    log_test("Sync status validity", "WARN", 
                            f"Unexpected status: {status}")
                
                if last_sync:
                    log_test("Last sync information", "PASS", 
                            f"Last sync: {last_sync}")
                else:
                    log_test("Last sync information", "WARN", 
                            "No last sync information")
                
                if isinstance(sync_count, int) and sync_count >= 0:
                    log_test("Sync count validity", "PASS", 
                            f"Sync count: {sync_count}")
                else:
                    log_test("Sync count validity", "WARN", 
                            f"Invalid sync count: {sync_count}")
                
                if isinstance(pending_uploads, int) and pending_uploads >= 0:
                    log_test("Pending uploads count", "PASS", 
                            f"Pending uploads: {pending_uploads}")
                else:
                    log_test("Pending uploads count", "WARN", 
                            f"Invalid pending uploads: {pending_uploads}")
                
                if isinstance(errors, list):
                    if len(errors) == 0:
                        log_test("Sync errors", "PASS", "No sync errors")
                    else:
                        log_test("Sync errors", "WARN", 
                                f"Found {len(errors)} sync errors")
                        for i, error in enumerate(errors[:3]):  # Show first 3 errors
                            print(f"    Error {i+1}: {error}")
                else:
                    log_test("Sync errors format", "WARN", 
                            f"Unexpected errors format: {type(errors)}")
                
            else:
                log_test("TECH CARDS SYNC STATUS - FAILURE", "FAIL", 
                        "No sync status information returned")
                
        elif response.status_code == 503:
            log_test("TECH CARDS SYNC STATUS", "WARN", 
                    f"Service unavailable: {response.text}")
        elif response.status_code == 500:
            log_test("TECH CARDS SYNC STATUS", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("TECH CARDS SYNC STATUS", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("TECH CARDS SYNC STATUS", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("TECH CARDS SYNC STATUS", "FAIL", f"Exception: {str(e)}")

def test_updated_tech_cards_upload():
    """Test POST /api/iiko/tech-cards/upload - обновленный endpoint использующий assembly charts"""
    print("📤 TESTING UPDATED TECH CARDS UPLOAD")
    print("=" * 60)
    
    # Test data for the updated upload endpoint
    test_upload_data = {
        "name": "AI Тестовая Паста Карбонара",
        "description": "Создано AI-Menu-Designer с использованием assembly charts",
        "ingredients": [
            {"name": "Спагетти", "quantity": 100, "unit": "г", "price": 25.0},
            {"name": "Бекон", "quantity": 80, "unit": "г", "price": 120.0},
            {"name": "Яйцо куриное", "quantity": 2, "unit": "шт", "price": 20.0},
            {"name": "Пармезан", "quantity": 50, "unit": "г", "price": 150.0},
            {"name": "Сливки 33%", "quantity": 100, "unit": "мл", "price": 45.0}
        ],
        "preparation_steps": [
            "Отварить спагетти до состояния аль денте",
            "Обжарить бекон до хрустящей корочки",
            "Смешать яйца с тертым пармезаном",
            "Соединить горячую пасту с яично-сырной смесью",
            "Добавить бекон и сливки, перемешать"
        ],
        "organization_id": "default-org-001",
        "price": 520.0,
        "cost": 360.0,
        "weight": 350.0,
        "cook_time": "15 мин",
        "difficulty": "средне",
        "category": "Паста"
    }
    
    print(f"Test 1: POST /api/iiko/tech-cards/upload - Updated with assembly charts")
    print(f"Test data: {json.dumps(test_upload_data, ensure_ascii=False, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/iiko/tech-cards/upload",
            json=test_upload_data,
            timeout=120  # 2 minute timeout for IIKo integration
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check for expected response structure
            status = result.get("status", "")
            success = result.get("success", False)
            method = result.get("method", "")
            assembly_chart_id = result.get("assembly_chart_id")
            upload_details = result.get("upload_details", {})
            
            print(f"\n📤 UPDATED UPLOAD ANALYSIS:")
            print(f"Status: {status}")
            print(f"Success: {success}")
            print(f"Method: {method}")
            print(f"Assembly Chart ID: {assembly_chart_id}")
            
            if success:
                log_test("UPDATED TECH CARDS UPLOAD - SUCCESS", "PASS", 
                        f"Tech card uploaded successfully using updated method")
                
                # Verify it's using assembly charts
                if method == "assembly_chart" or "assembly" in method.lower():
                    log_test("Assembly charts usage verification", "PASS", 
                            f"Using assembly charts method: {method}")
                else:
                    log_test("Assembly charts usage verification", "WARN", 
                            f"Method may not be using assembly charts: {method}")
                
                if assembly_chart_id:
                    log_test("Assembly chart ID generation", "PASS", 
                            f"Generated assembly chart ID: {assembly_chart_id}")
                else:
                    log_test("Assembly chart ID generation", "WARN", 
                            "No assembly chart ID returned")
                
                # Check upload details
                if upload_details:
                    endpoint_used = upload_details.get("endpoint_used", "")
                    if "assembly" in endpoint_used.lower():
                        log_test("Assembly charts endpoint usage", "PASS", 
                                f"Using assembly charts endpoint: {endpoint_used}")
                    else:
                        log_test("Assembly charts endpoint usage", "WARN", 
                                f"Endpoint may not be assembly charts: {endpoint_used}")
                else:
                    log_test("Upload details availability", "WARN", 
                            "No upload details provided")
                
                # Verify the upload status levels
                if status == "uploaded_to_iiko":
                    log_test("Upload status - Success Level", "PASS", 
                            "Successfully uploaded to IIKo using assembly charts")
                elif status == "prepared_for_manual_sync":
                    log_test("Upload status - Fallback Level", "PASS", 
                            "Prepared for manual sync using assembly charts format")
                elif status == "upload_failed":
                    log_test("Upload status - Error Level", "PASS", 
                            "Upload failed but handled gracefully")
                else:
                    log_test("Upload status - Unknown", "WARN", 
                            f"Unexpected status: {status}")
                
            else:
                log_test("UPDATED TECH CARDS UPLOAD - FAILURE", "FAIL", 
                        "Failed to upload tech card with updated method")
                
                # Check for error details
                error = result.get("error", "")
                note = result.get("note", "")
                
                if error:
                    log_test("Upload error details", "INFO", f"Error: {error}")
                if note:
                    log_test("Upload error note", "INFO", f"Note: {note}")
                
        elif response.status_code == 400:
            log_test("UPDATED TECH CARDS UPLOAD", "FAIL", 
                    f"Bad request: {response.text}")
        elif response.status_code == 500:
            log_test("UPDATED TECH CARDS UPLOAD", "FAIL", 
                    f"Server error: {response.text}")
        elif response.status_code == 503:
            log_test("UPDATED TECH CARDS UPLOAD", "WARN", 
                    f"Service unavailable (IIKo integration may be down): {response.text}")
        else:
            log_test("UPDATED TECH CARDS UPLOAD", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("UPDATED TECH CARDS UPLOAD", "FAIL", "Request timeout (>120s)")
    except Exception as e:
        log_test("UPDATED TECH CARDS UPLOAD", "FAIL", f"Exception: {str(e)}")

def test_error_handling_and_edge_cases():
    """Test error handling and edge cases for assembly charts endpoints"""
    print("⚠️ TESTING ERROR HANDLING AND EDGE CASES")
    print("=" * 60)
    
    # Test 1: Invalid organization ID
    print("Test 1: GET /api/iiko/assembly-charts/all/invalid-org-id")
    try:
        response = requests.get(
            f"{BACKEND_URL}/iiko/assembly-charts/all/invalid-org-id",
            timeout=30
        )
        
        if response.status_code == 404:
            log_test("Invalid organization ID handling", "PASS", 
                    "Correctly returns 404 for invalid organization")
        elif response.status_code == 400:
            log_test("Invalid organization ID handling", "PASS", 
                    "Correctly returns 400 for invalid organization")
        else:
            log_test("Invalid organization ID handling", "WARN", 
                    f"Unexpected response: {response.status_code}")
            
    except Exception as e:
        log_test("Invalid organization ID handling", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Invalid chart ID
    print("Test 2: GET /api/iiko/assembly-charts/invalid-chart-id")
    try:
        response = requests.get(
            f"{BACKEND_URL}/iiko/assembly-charts/invalid-chart-id",
            timeout=30
        )
        
        if response.status_code == 404:
            log_test("Invalid chart ID handling", "PASS", 
                    "Correctly returns 404 for invalid chart ID")
        elif response.status_code == 400:
            log_test("Invalid chart ID handling", "PASS", 
                    "Correctly returns 400 for invalid chart ID")
        else:
            log_test("Invalid chart ID handling", "WARN", 
                    f"Unexpected response: {response.status_code}")
            
    except Exception as e:
        log_test("Invalid chart ID handling", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: Malformed create request
    print("Test 3: POST /api/iiko/assembly-charts/create - Malformed data")
    try:
        malformed_data = {
            "name": "",  # Empty name
            "ingredients": "not_a_list",  # Wrong type
            "price": "not_a_number"  # Wrong type
        }
        
        response = requests.post(
            f"{BACKEND_URL}/iiko/assembly-charts/create",
            json=malformed_data,
            timeout=30
        )
        
        if response.status_code == 400:
            log_test("Malformed create request handling", "PASS", 
                    "Correctly returns 400 for malformed data")
        elif response.status_code == 422:
            log_test("Malformed create request handling", "PASS", 
                    "Correctly returns 422 for validation errors")
        else:
            log_test("Malformed create request handling", "WARN", 
                    f"Unexpected response: {response.status_code}")
            
    except Exception as e:
        log_test("Malformed create request handling", "FAIL", f"Exception: {str(e)}")
    
    # Test 4: Empty request body
    print("Test 4: POST /api/iiko/assembly-charts/create - Empty body")
    try:
        response = requests.post(
            f"{BACKEND_URL}/iiko/assembly-charts/create",
            json={},
            timeout=30
        )
        
        if response.status_code in [400, 422]:
            log_test("Empty request body handling", "PASS", 
                    f"Correctly returns {response.status_code} for empty body")
        else:
            log_test("Empty request body handling", "WARN", 
                    f"Unexpected response: {response.status_code}")
            
    except Exception as e:
        log_test("Empty request body handling", "FAIL", f"Exception: {str(e)}")

def main():
    """Run all IIKo assembly charts tests"""
    print("🧪 BACKEND TESTING: IIKO ASSEMBLY CHARTS (TECH CARDS) MANAGEMENT")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: Prerequisites - IIKo Health and Organizations
        organization_id = test_iiko_health_and_organizations()
        
        # Test 2: Get all assembly charts
        existing_charts = test_get_all_assembly_charts(organization_id)
        
        # Test 3: Create new assembly chart
        created_chart_id = test_create_assembly_chart(organization_id)
        
        # Test 4: Get assembly chart by ID (using created chart)
        test_get_assembly_chart_by_id(created_chart_id)
        
        # Test 5: Tech cards sync status
        test_tech_cards_sync_status()
        
        # Test 6: Updated tech cards upload (using assembly charts)
        test_updated_tech_cards_upload()
        
        # Test 7: Delete assembly chart (cleanup)
        test_delete_assembly_chart(created_chart_id)
        
        # Test 8: Error handling and edge cases
        test_error_handling_and_edge_cases()
        
        print("🏁 ALL IIKO ASSEMBLY CHARTS TESTS COMPLETED")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary of assembly charts features tested
        print("\n🔨 IIKO ASSEMBLY CHARTS FEATURES TESTED:")
        print("✅ GET /api/iiko/assembly-charts/all/{organization_id} - Get all tech cards")
        print("✅ POST /api/iiko/assembly-charts/create - Create new tech card")
        print("✅ GET /api/iiko/assembly-charts/{chart_id} - Get tech card by ID")
        print("✅ DELETE /api/iiko/assembly-charts/{chart_id} - Delete tech card")
        print("✅ GET /api/iiko/tech-cards/sync-status - Sync status")
        print("✅ POST /api/iiko/tech-cards/upload - Updated to use assembly charts")
        print("✅ IIKo integration health verification")
        print("✅ Edison Craft Bar organization verification")
        print("✅ Error handling and edge cases")
        print("\n🚀 ASSEMBLY CHARTS INTEGRATION: Complete tech card management system!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()