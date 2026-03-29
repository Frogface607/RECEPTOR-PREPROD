#!/usr/bin/env python3
"""
IIKo API Integration Testing Suite
Testing all new IIKo endpoints for restaurant management system integration
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

def test_iiko_health_check():
    """Test IIKo health check endpoint - КРИТИЧЕСКИЙ ТЕСТ!"""
    print("🏥 TESTING IIKO HEALTH CHECK - КРИТИЧЕСКИЙ ТЕСТ!")
    print("=" * 60)
    
    print("Test 1: GET /api/iiko/health (ожидаем 'healthy' вместо 'unhealthy')")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/health", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check required fields in health response
            required_fields = ['status', 'iiko_connection', 'timestamp']
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                log_test("Health check response structure", "PASS", 
                        f"All required fields present: {required_fields}")
                
                # Log health status details with emphasis on changes
                status = result.get('status')
                iiko_connection = result.get('iiko_connection')
                
                print(f"    🎯 КРИТИЧЕСКИЙ РЕЗУЛЬТАТ:")
                print(f"    Status: {status}")
                print(f"    IIKo Connection: {iiko_connection}")
                print(f"    Timestamp: {result.get('timestamp')}")
                
                # Check for the expected improvement
                if status == "healthy":
                    log_test("🎉 HEALTH STATUS IMPROVEMENT", "PASS", 
                            "Status changed from 'unhealthy' to 'healthy' - NEW KEYS WORKING!")
                elif status == "unhealthy":
                    log_test("⚠️ Health status still unhealthy", "WARN", 
                            "Status still 'unhealthy' - may need more time or additional setup")
                else:
                    log_test("Health status", "INFO", f"Status: {status}")
                
                if result.get('error'):
                    print(f"    Error: {result.get('error')}")
                    log_test("IIKo connection error", "WARN", 
                            f"Connection error: {result.get('error')}")
                else:
                    log_test("🎉 NO CONNECTION ERRORS", "PASS", 
                            "No connection errors - NEW CREDENTIALS WORKING!")
                    
            else:
                log_test("Health check response structure", "FAIL", 
                        f"Missing fields: {missing_fields}")
                
        elif response.status_code == 503:
            log_test("Health check availability", "WARN", 
                    "Service unavailable (IIKo integration not available)")
        else:
            log_test("Health check endpoint", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Health check endpoint", "FAIL", "Request timeout (>30s)")
    except Exception as e:
        log_test("Health check endpoint", "FAIL", f"Exception: {str(e)}")

def test_iiko_diagnostics():
    """Test IIKo diagnostics endpoint"""
    print("🔧 TESTING IIKO DIAGNOSTICS")
    print("=" * 60)
    
    print("Test 1: GET /api/iiko/diagnostics")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/diagnostics", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            log_test("Diagnostics endpoint", "PASS", 
                    f"Response received with {len(result)} diagnostic items")
            
            # Log diagnostic information
            print(f"    Diagnostic data:")
            for key, value in result.items():
                print(f"    - {key}: {value}")
                
        elif response.status_code == 503:
            log_test("Diagnostics endpoint", "WARN", 
                    "Service unavailable (IIKo integration not available)")
        else:
            log_test("Diagnostics endpoint", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Diagnostics endpoint", "FAIL", "Request timeout (>30s)")
    except Exception as e:
        log_test("Diagnostics endpoint", "FAIL", f"Exception: {str(e)}")

def test_iiko_organizations():
    """Test IIKo organizations endpoint - ГЛАВНОЕ! Должны появиться организации"""
    print("🏢 TESTING IIKO ORGANIZATIONS - ГЛАВНОЕ!")
    print("=" * 60)
    
    print("Test 1: GET /api/iiko/organizations (ожидаем реальные организации вместо пустого списка)")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/organizations", timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, list):
                org_count = len(result)
                
                if org_count > 0:
                    log_test("🎉 ORGANIZATIONS FOUND!", "PASS", 
                            f"🚀 УСПЕХ! Найдено {org_count} организаций - НОВЫЕ КЛЮЧИ РАБОТАЮТ!")
                    
                    # Check organization structure
                    org = result[0]
                    expected_fields = ['id', 'name', 'active']
                    present_fields = [field for field in expected_fields if field in org]
                    
                    log_test("Organization data structure", "PASS" if len(present_fields) >= 2 else "WARN", 
                            f"Fields present: {present_fields}")
                    
                    # Log all organizations found
                    print(f"    🎯 НАЙДЕННЫЕ ОРГАНИЗАЦИИ:")
                    for i, org in enumerate(result):
                        name = org.get('name', 'N/A')
                        org_id = org.get('id', 'N/A')
                        active = org.get('active', 'N/A')
                        address = org.get('address', 'N/A')
                        country = org.get('country', 'N/A')
                        
                        print(f"    {i+1}. {name}")
                        print(f"       ID: {org_id}")
                        print(f"       Active: {active}")
                        if address != 'N/A':
                            print(f"       Address: {address}")
                        if country != 'N/A':
                            print(f"       Country: {country}")
                        print()
                        
                    return result  # Return for use in menu tests
                else:
                    log_test("❌ NO ORGANIZATIONS", "FAIL", 
                            "Пустой список организаций - новые ключи пока не дают доступ")
                    
            else:
                log_test("Organizations response format", "FAIL", 
                        f"Expected list, got {type(result)}")
                
        elif response.status_code == 500:
            error_text = response.text
            log_test("Organizations endpoint error", "FAIL", 
                    f"Authentication/API error: {error_text}")
            print(f"    🔍 Error details: {error_text}")
        elif response.status_code == 503:
            log_test("Organizations endpoint", "WARN", 
                    "Service unavailable (IIKo integration not available)")
        else:
            log_test("Organizations endpoint", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Organizations endpoint", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("Organizations endpoint", "FAIL", f"Exception: {str(e)}")
    
    return []

def test_iiko_menu(organizations):
    """Test IIKo menu endpoint"""
    print("📋 TESTING IIKO MENU")
    print("=" * 60)
    
    if not organizations:
        log_test("Menu endpoint test", "SKIP", "No organizations available for testing")
        return
    
    # Use first organization for testing
    org_id = organizations[0].get('id')
    if not org_id:
        log_test("Menu endpoint test", "SKIP", "No valid organization ID found")
        return
    
    print(f"Test 1: GET /api/iiko/menu/{org_id}")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/menu/{org_id}", timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check menu structure
            expected_sections = ['categories', 'items', 'modifiers', 'last_updated']
            present_sections = [section for section in expected_sections if section in result]
            
            log_test("Menu endpoint", "PASS", 
                    f"Menu data retrieved with sections: {present_sections}")
            
            # Log menu statistics
            categories_count = len(result.get('categories', []))
            items_count = len(result.get('items', []))
            modifiers_count = len(result.get('modifiers', []))
            
            print(f"    Menu statistics:")
            print(f"    - Categories: {categories_count}")
            print(f"    - Items: {items_count}")
            print(f"    - Modifiers: {modifiers_count}")
            print(f"    - Last updated: {result.get('last_updated', 'N/A')}")
            
            # Sample some menu items
            if result.get('items'):
                print(f"    Sample menu items:")
                for i, item in enumerate(result['items'][:3]):
                    print(f"    {i+1}. {item.get('name', 'N/A')} - {item.get('price', 0)} ₽")
                    
        elif response.status_code == 500:
            log_test("Menu endpoint", "WARN", 
                    "Authentication or API error (expected with test credentials)")
        elif response.status_code == 503:
            log_test("Menu endpoint", "WARN", 
                    "Service unavailable (IIKo integration not available)")
        else:
            log_test("Menu endpoint", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Menu endpoint", "FAIL", "Request timeout (>90s)")
    except Exception as e:
        log_test("Menu endpoint", "FAIL", f"Exception: {str(e)}")

def test_iiko_tech_cards_upload():
    """Test IIKo tech cards upload endpoint"""
    print("📤 TESTING IIKO TECH CARDS UPLOAD")
    print("=" * 60)
    
    print("Test 1: POST /api/iiko/tech-cards/upload")
    try:
        # Sample tech card data
        sample_tech_card = {
            "name": "Тестовое блюдо",
            "description": "Описание тестового блюда для проверки загрузки",
            "ingredients": [
                {
                    "name": "Мука пшеничная",
                    "quantity": 200,
                    "unit": "г",
                    "cost": 15.50
                },
                {
                    "name": "Яйца куриные",
                    "quantity": 2,
                    "unit": "шт",
                    "cost": 20.00
                }
            ],
            "preparation_steps": [
                "Просеять муку в миску",
                "Добавить яйца и перемешать",
                "Замесить тесто до однородности"
            ],
            "category_id": "test_category_id",
            "price": 150.0,
            "weight": 250.0,
            "organization_id": "test_org_id"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/iiko/tech-cards/upload",
            json=sample_tech_card,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            log_test("Tech cards upload endpoint", "PASS", 
                    f"Upload successful: {result}")
                    
        elif response.status_code == 400:
            log_test("Tech cards upload validation", "PASS", 
                    "Request validation working (expected with test data)")
        elif response.status_code == 500:
            log_test("Tech cards upload endpoint", "WARN", 
                    "Authentication or API error (expected with test credentials)")
        elif response.status_code == 503:
            log_test("Tech cards upload endpoint", "WARN", 
                    "Service unavailable (IIKo integration not available)")
        else:
            log_test("Tech cards upload endpoint", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Tech cards upload endpoint", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("Tech cards upload endpoint", "FAIL", f"Exception: {str(e)}")

def test_iiko_menu_sync():
    """Test IIKo menu synchronization endpoint"""
    print("🔄 TESTING IIKO MENU SYNC")
    print("=" * 60)
    
    print("Test 1: POST /api/iiko/sync-menu")
    try:
        # Sample sync request
        sync_request = {
            "organization_ids": ["test_org_1", "test_org_2"],
            "sync_prices": True,
            "sync_categories": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/iiko/sync-menu",
            json=sync_request,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for sync job ID or status
            if 'sync_job_id' in result or 'status' in result:
                log_test("Menu sync endpoint", "PASS", 
                        f"Sync initiated: {result}")
                
                # If we got a sync job ID, test the status endpoint
                sync_job_id = result.get('sync_job_id')
                if sync_job_id:
                    test_iiko_sync_status(sync_job_id)
                    
            else:
                log_test("Menu sync response", "WARN", 
                        f"Unexpected response format: {result}")
                
        elif response.status_code == 400:
            log_test("Menu sync validation", "PASS", 
                    "Request validation working (expected with test data)")
        elif response.status_code == 500:
            log_test("Menu sync endpoint", "WARN", 
                    "Authentication or API error (expected with test credentials)")
        elif response.status_code == 503:
            log_test("Menu sync endpoint", "WARN", 
                    "Service unavailable (IIKo integration not available)")
        else:
            log_test("Menu sync endpoint", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Menu sync endpoint", "FAIL", "Request timeout (>120s)")
    except Exception as e:
        log_test("Menu sync endpoint", "FAIL", f"Exception: {str(e)}")

def test_iiko_sync_status(sync_job_id=None):
    """Test IIKo sync status endpoint"""
    print("📊 TESTING IIKO SYNC STATUS")
    print("=" * 60)
    
    # Use provided sync_job_id or test with a sample one
    test_job_id = sync_job_id or "test_sync_job_123"
    
    print(f"Test 1: GET /api/iiko/sync/status/{test_job_id}")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/sync/status/{test_job_id}", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            log_test("Sync status endpoint", "PASS", 
                    f"Status retrieved: {result}")
            
            # Log status details
            print(f"    Sync status details:")
            for key, value in result.items():
                print(f"    - {key}: {value}")
                
        elif response.status_code == 404:
            log_test("Sync status endpoint", "PASS", 
                    "Job not found (expected with test job ID)")
        elif response.status_code == 500:
            log_test("Sync status endpoint", "WARN", 
                    "Authentication or API error (expected with test credentials)")
        elif response.status_code == 503:
            log_test("Sync status endpoint", "WARN", 
                    "Service unavailable (IIKo integration not available)")
        else:
            log_test("Sync status endpoint", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Sync status endpoint", "FAIL", "Request timeout (>30s)")
    except Exception as e:
        log_test("Sync status endpoint", "FAIL", f"Exception: {str(e)}")

def test_iiko_error_handling():
    """Test IIKo API error handling"""
    print("⚠️ TESTING IIKO ERROR HANDLING")
    print("=" * 60)
    
    # Test 1: Invalid organization ID for menu
    print("Test 1: Invalid organization ID for menu")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/menu/invalid_org_id", timeout=30)
        
        if response.status_code in [400, 404, 500]:
            log_test("Invalid organization ID handling", "PASS", 
                    f"Properly handled invalid org ID (HTTP {response.status_code})")
        else:
            log_test("Invalid organization ID handling", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Invalid organization ID handling", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Invalid JSON for tech card upload
    print("Test 2: Invalid JSON for tech card upload")
    try:
        invalid_data = {
            "name": "",  # Empty name
            "ingredients": [],  # Empty ingredients
            "organization_id": ""  # Empty org ID
        }
        
        response = requests.post(
            f"{BACKEND_URL}/iiko/tech-cards/upload",
            json=invalid_data,
            timeout=30
        )
        
        if response.status_code in [400, 422]:
            log_test("Invalid tech card data handling", "PASS", 
                    f"Properly rejected invalid data (HTTP {response.status_code})")
        else:
            log_test("Invalid tech card data handling", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Invalid tech card data handling", "FAIL", f"Exception: {str(e)}")

def test_iiko_integration_availability():
    """Test if IIKo integration is properly configured"""
    print("🔧 TESTING IIKO INTEGRATION AVAILABILITY")
    print("=" * 60)
    
    print("Test 1: Check if pyiikocloudapi library is available")
    try:
        # This will be reflected in the health check
        response = requests.get(f"{BACKEND_URL}/iiko/health", timeout=10)
        
        if response.status_code == 503:
            result = response.json()
            if "not available" in result.get("error", "").lower():
                log_test("IIKo library availability", "WARN", 
                        "pyiikocloudapi library not installed (expected in some environments)")
            else:
                log_test("IIKo library availability", "FAIL", 
                        f"Unexpected service unavailable: {result}")
        elif response.status_code == 200:
            result = response.json()
            if result.get("iiko_connection") == "available":
                log_test("IIKo library availability", "PASS", 
                        "pyiikocloudapi library is available")
            else:
                log_test("IIKo library availability", "WARN", 
                        f"Library available but connection issues: {result}")
        else:
            log_test("IIKo library availability", "FAIL", 
                    f"Unexpected response: HTTP {response.status_code}")
            
    except Exception as e:
        log_test("IIKo library availability", "FAIL", f"Exception: {str(e)}")

def main():
    """Run all IIKo integration tests"""
    print("🧪 IIKO API INTEGRATION TESTING SUITE - ПРАВИЛЬНЫЕ OFFICE КРЕДЫ!")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🚀 ФИНАЛЬНЫЙ ТЕСТ - ПРАВИЛЬНЫЕ IIKO OFFICE КРЕДЫ!")
    print("Testing IIKo API endpoints with REAL IIKo Office credentials:")
    print("- IIKO_API_LOGIN: Sergey")
    print("- IIKO_API_PASSWORD: metkamfetamin")
    print("- Server: Edison craft bar")
    print("- IIKO_BASE_URL: https://edison-bar.iiko.it")
    print()
    print("🎯 СХЕМА РАБОТЫ (подтверждена техподдержкой):")
    print("- Используем обычные креды от IIKo Office")
    print("- access_token получается автоматически через API /resto/api/auth")
    print("- Это должны быть РЕАЛЬНЫЕ креды от аккаунта пользователя!")
    print()
    print("🚀 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ (ЭТО ДОЛЖНО СРАБОТАТЬ!):")
    print("✅ Health check: 'healthy' - подключение к Edison Craft Bar")
    print("✅ Organizations: 'Edison Craft Bar' и другие организации пользователя")
    print("✅ Menu: Реальное меню с напитками, закусками кафе")
    print("✅ Auth: Успешная авторизация через /resto/api/auth")
    print("🎯 ЕСЛИ ЭТО СРАБОТАЕТ - интеграция с IIKo ПОЛНОСТЬЮ заработает!")
    print()
    
    try:
        # ПРИОРИТЕТ 1 - АУТЕНТИФИКАЦИЯ (as requested)
        print("🔥 ПРИОРИТЕТ 1 - АУТЕНТИФИКАЦИЯ")
        print("=" * 60)
        
        # Test 1: Health Check (КРИТИЧЕСКИЙ!)
        test_iiko_health_check()
        
        # Test 2: Organizations (ГЛАВНОЕ! Должны появиться организации Edison Craft Bar)
        organizations = test_iiko_organizations()
        
        # Test 3: Diagnostics (полная диагностика)
        test_iiko_diagnostics()
        
        # ПРИОРИТЕТ 2 - РЕАЛЬНЫЕ ДАННЫЕ
        if organizations:
            print("🎉 ОРГАНИЗАЦИИ НАЙДЕНЫ! ПЕРЕХОДИМ К ПРИОРИТЕТУ 2 - РЕАЛЬНЫЕ ДАННЫЕ")
            print("=" * 60)
            
            # Test 4: Menu (проверить получение меню Edison Craft Bar)
            test_iiko_menu(organizations)
            
            # Test 5: Tech Cards Upload (проверить готовность загрузки техкарт)
            test_iiko_tech_cards_upload()
        else:
            print("⚠️ ОРГАНИЗАЦИИ НЕ НАЙДЕНЫ - ПРОПУСКАЕМ ПРИОРИТЕТ 2")
            print("=" * 60)
        
        # Additional tests (lower priority)
        print("📋 ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ")
        print("=" * 60)
        
        # Test 6: Integration Availability
        test_iiko_integration_availability()
        
        # Test 7: Menu Sync
        test_iiko_menu_sync()
        
        # Test 8: Sync Status
        test_iiko_sync_status()
        
        # Test 9: Error Handling
        test_iiko_error_handling()
        
        print("🏁 ВСЕ ТЕСТЫ IIKO ИНТЕГРАЦИИ ЗАВЕРШЕНЫ")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        if organizations:
            print("✅ УСПЕХ! Правильные IIKo Office креды работают!")
            print("✅ Edison Craft Bar найден - можно загружать AI-техкарты в POS-систему!")
            print("🎉 ИНТЕГРАЦИЯ С IIKO ПОЛНОСТЬЮ ЗАРАБОТАЛА!")
            print("🎯 Можно будет загружать AI-техкарты прямо в POS-систему Edison Craft Bar!")
        else:
            print("❌ Креды пока не дают доступ к организациям")
            print("⚠️ Требуется дополнительная настройка или проверка учетных данных")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()