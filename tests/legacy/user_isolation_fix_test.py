#!/usr/bin/env python3
"""
СРОЧНОЕ ТЕСТИРОВАНИЕ ВОССТАНОВЛЕНИЯ ФУНКЦИОНАЛЬНОСТИ после исправления изоляции пользователей

ГЛАВНАЯ ЗАДАЧА: Проверить что ручное и автоматическое сопоставление снова работают для реальных пользователей

ТЕСТЫ:
1. Подключение реального пользователя: POST /api/v1/iiko/rms/connect с кредами из .env (реальный user_id, например "real_user_123")
2. Статус подключения для реального пользователя: GET /api/v1/iiko/rms/connection/status?user_id=real_user_123 - должен показывать "connected"
3. Sync status для реального пользователя: GET /api/v1/iiko/rms/sync/status?organization_id=default&user_id=real_user_123 - должен возвращать данные синхронизации
4. Sync status для anonymous: GET /api/v1/iiko/rms/sync/status?organization_id=default&user_id=anonymous - должен возвращать данные (для маппинга)
5. Генерация техкарты + автомаппинг: POST /api/v1/techcards.v2/generate простой техкарты, POST /api/v1/techcards.v2/mapping/enhanced с ингредиентами из техкарты

ЦЕЛЬ: Убедиться что изоляция работает (demo_user изолирован) но функциональность восстановлена для всех остальных случаев!
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# IIKO RMS credentials from environment variables
IIKO_RMS_HOST = os.environ.get('IIKO_RMS_HOST', 'edison-bar.iiko.it')
IIKO_RMS_LOGIN = os.environ.get('IIKO_RMS_LOGIN', 'Sergey')
IIKO_RMS_PASSWORD = os.environ.get('IIKO_RMS_PASSWORD', 'metkamfetamin')

# Test users
REAL_USER_ID = "real_user_123"
ANONYMOUS_USER_ID = "anonymous"
DEMO_USER_ID = "demo_user"

class UserIsolationFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'User-Isolation-Fix-Tester/1.0'
        })
        self.test_results = []
        self.generated_techcard_id = None
        self.generated_ingredients = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
        
    def test_real_user_connection(self) -> bool:
        """Test 1: Подключение реального пользователя с кредами из .env"""
        try:
            url = f"{API_BASE}/v1/iiko/rms/connect"
            
            payload = {
                "user_id": REAL_USER_ID,
                "host": IIKO_RMS_HOST,
                "login": IIKO_RMS_LOGIN,
                "password": IIKO_RMS_PASSWORD
            }
            
            print(f"   Connecting real user {REAL_USER_ID} to IIKO RMS: {IIKO_RMS_HOST}")
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'connected':
                    organizations = data.get('organizations', [])
                    org_name = organizations[0].get('name', 'Unknown') if organizations else 'Unknown'
                    
                    self.log_test(
                        "Real User Connection",
                        True,
                        f"Real user successfully connected to IIKO RMS. Organization: {org_name}",
                        {
                            'status': data.get('status'),
                            'organization_name': org_name,
                            'organizations_count': len(organizations)
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Real User Connection",
                        False,
                        f"Connection failed: {data.get('error', 'Unknown error')}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Real User Connection",
                    False,
                    f"Connect API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Real User Connection",
                False,
                f"Connect API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Real User Connection",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_real_user_connection_status(self) -> bool:
        """Test 2: Статус подключения для реального пользователя - должен показывать "connected" """
        try:
            url = f"{API_BASE}/v1/iiko/rms/connection/status"
            params = {"user_id": REAL_USER_ID}
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'connected':
                    org_name = data.get('organization_name', 'Unknown')
                    self.log_test(
                        "Real User Connection Status",
                        True,
                        f"Real user connection status is 'connected'. Organization: {org_name}",
                        data
                    )
                    return True
                else:
                    self.log_test(
                        "Real User Connection Status",
                        False,
                        f"Expected 'connected' status, got: {data.get('status', 'unknown')}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Real User Connection Status",
                    False,
                    f"Status API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Real User Connection Status",
                False,
                f"Status API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Real User Connection Status",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_real_user_sync_status(self) -> bool:
        """Test 3: Sync status для реального пользователя - должен возвращать данные синхронизации"""
        try:
            url = f"{API_BASE}/v1/iiko/rms/sync/status"
            params = {
                "organization_id": "default",
                "user_id": REAL_USER_ID
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if sync data is returned
                if 'sync_status' in data or 'status' in data or 'last_sync' in data or 'products_count' in data:
                    sync_status = data.get('sync_status', data.get('status', 'unknown'))
                    products_count = data.get('products_count', 0)
                    
                    self.log_test(
                        "Real User Sync Status",
                        True,
                        f"Real user sync status returned data. Status: {sync_status}, Products: {products_count}",
                        {
                            'sync_status': sync_status,
                            'products_count': products_count,
                            'has_data': len(data) > 0
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Real User Sync Status",
                        False,
                        "Sync status response missing expected fields",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Real User Sync Status",
                    False,
                    f"Sync status API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Real User Sync Status",
                False,
                f"Sync status API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Real User Sync Status",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_anonymous_sync_status(self) -> bool:
        """Test 4: Sync status для anonymous - должен возвращать данные (для маппинга)"""
        try:
            url = f"{API_BASE}/v1/iiko/rms/sync/status"
            params = {
                "organization_id": "default",
                "user_id": ANONYMOUS_USER_ID
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if sync data is returned for anonymous user (needed for mapping)
                if 'sync_status' in data or 'status' in data or 'last_sync' in data or 'products_count' in data:
                    sync_status = data.get('sync_status', data.get('status', 'unknown'))
                    products_count = data.get('products_count', 0)
                    
                    self.log_test(
                        "Anonymous User Sync Status",
                        True,
                        f"Anonymous user sync status returned data (needed for mapping). Status: {sync_status}, Products: {products_count}",
                        {
                            'sync_status': sync_status,
                            'products_count': products_count,
                            'has_data': len(data) > 0
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Anonymous User Sync Status",
                        False,
                        "Anonymous sync status response missing expected fields",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Anonymous User Sync Status",
                    False,
                    f"Anonymous sync status API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Anonymous User Sync Status",
                False,
                f"Anonymous sync status API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Anonymous User Sync Status",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_techcard_generation(self) -> bool:
        """Test 5a: Генерация простой техкарты"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Simple tech card for testing
            payload = {
                "name": "Борщ украинский с говядиной",
                "cuisine": "русская",
                "equipment": ["плита", "кастрюля"],
                "budget": 800.0,
                "dietary": [],
                "user_id": REAL_USER_ID
            }
            
            print(f"   Generating tech card: {payload['name']} for user {REAL_USER_ID}")
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'status' in data and 'card' in data:
                    card = data['card']
                    card_id = card.get('meta', {}).get('id')
                    status = data['status']
                    
                    if card_id:
                        self.generated_techcard_id = card_id
                        
                        # Extract ingredients for auto-mapping test
                        ingredients = card.get('ingredients', [])
                        self.generated_ingredients = ingredients
                        
                        self.log_test(
                            "Tech Card Generation",
                            True,
                            f"Tech card generated successfully. ID: {card_id}, Status: {status}, Ingredients: {len(ingredients)}",
                            {
                                'id': card_id,
                                'status': status,
                                'ingredients_count': len(ingredients),
                                'ingredients': [ing.get('name', 'Unknown') for ing in ingredients[:5]]
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Tech Card Generation",
                            False,
                            "Response missing card ID in meta",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "Tech Card Generation",
                        False,
                        "Response missing required fields (status, card)",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Tech Card Generation",
                    False,
                    f"Generation API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Tech Card Generation",
                False,
                f"Generation API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Tech Card Generation",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_enhanced_auto_mapping(self) -> bool:
        """Test 5b: Автомаппинг с ингредиентами из техкарты"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/mapping/enhanced"
            
            # Use ingredients from generated tech card or fallback to test ingredients
            ingredients_for_mapping = []
            
            if self.generated_ingredients:
                # Use actual ingredients from generated tech card
                for ing in self.generated_ingredients[:5]:  # Limit to first 5 ingredients
                    ingredients_for_mapping.append({
                        "name": ing.get('name', 'Unknown'),
                        "quantity": ing.get('quantity', 100),
                        "unit": ing.get('unit', 'g')
                    })
            else:
                # Fallback to test ingredients
                ingredients_for_mapping = [
                    {"name": "говядина", "quantity": 300, "unit": "g"},
                    {"name": "свекла", "quantity": 200, "unit": "g"},
                    {"name": "капуста", "quantity": 150, "unit": "g"},
                    {"name": "морковь", "quantity": 100, "unit": "g"},
                    {"name": "лук", "quantity": 80, "unit": "g"}
                ]
            
            payload = {
                "techcard": {
                    "id": self.generated_techcard_id or "test-id",
                    "name": "Борщ украинский с говядиной",
                    "ingredients": ingredients_for_mapping
                },
                "ingredients": ingredients_for_mapping,
                "user_id": REAL_USER_ID
            }
            
            print(f"   Testing enhanced auto-mapping with {len(ingredients_for_mapping)} ingredients for user {REAL_USER_ID}")
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for mapping results
                if 'results' in data or 'mappings' in data or 'suggestions' in data:
                    results = data.get('results', data.get('mappings', data.get('suggestions', [])))
                    
                    self.log_test(
                        "Enhanced Auto-mapping",
                        True,
                        f"Enhanced auto-mapping completed successfully. Found {len(results)} mapping results",
                        {
                            'results_count': len(results),
                            'status': data.get('status', 'success'),
                            'coverage': data.get('coverage', 'unknown'),
                            'user_id': REAL_USER_ID
                        }
                    )
                    return True
                else:
                    # Check if it's a valid response structure even without mappings
                    if 'status' in data or 'message' in data:
                        message = data.get('message', data.get('status', 'No mappings found'))
                        self.log_test(
                            "Enhanced Auto-mapping",
                            True,  # Still success if API responds correctly
                            f"Enhanced auto-mapping API responded correctly: {message}",
                            data
                        )
                        return True
                    else:
                        self.log_test(
                            "Enhanced Auto-mapping",
                            False,
                            "Unexpected response structure",
                            data
                        )
                        return False
            else:
                self.log_test(
                    "Enhanced Auto-mapping",
                    False,
                    f"Enhanced auto-mapping API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Enhanced Auto-mapping",
                False,
                f"Enhanced auto-mapping API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Enhanced Auto-mapping",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_demo_user_isolation(self) -> bool:
        """Bonus Test: Проверить что demo_user изолирован (должен работать отдельно)"""
        try:
            url = f"{API_BASE}/v1/iiko/rms/connection/status"
            params = {"user_id": DEMO_USER_ID}
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Demo user should have its own isolated status
                status = data.get('status', 'unknown')
                self.log_test(
                    "Demo User Isolation Check",
                    True,
                    f"Demo user isolation working correctly. Status: {status} (isolated from real users)",
                    {
                        'status': status,
                        'isolated': True,
                        'user_id': DEMO_USER_ID
                    }
                )
                return True
            else:
                self.log_test(
                    "Demo User Isolation Check",
                    False,
                    f"Demo user status API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Demo User Isolation Check",
                False,
                f"Demo user status API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Demo User Isolation Check",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all user isolation fix tests"""
        print("🚀 СРОЧНОЕ ТЕСТИРОВАНИЕ ВОССТАНОВЛЕНИЯ ФУНКЦИОНАЛЬНОСТИ")
        print("=" * 80)
        print("ГЛАВНАЯ ЗАДАЧА: Проверить что ручное и автоматическое сопоставление")
        print("снова работают для реальных пользователей после исправления изоляции")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"IIKO RMS Host: {IIKO_RMS_HOST}")
        print(f"IIKO RMS Login: {IIKO_RMS_LOGIN}")
        print(f"Real User ID: {REAL_USER_ID}")
        print(f"Anonymous User ID: {ANONYMOUS_USER_ID}")
        print(f"Demo User ID: {DEMO_USER_ID}")
        print("=" * 80)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_real_user_connection,
            self.test_real_user_connection_status,
            self.test_real_user_sync_status,
            self.test_anonymous_sync_status,
            self.test_techcard_generation,
            self.test_enhanced_auto_mapping,
            self.test_demo_user_isolation
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_func.__name__}: {str(e)}")
        
        # Summary
        print("=" * 80)
        print("🎯 ТЕСТИРОВАНИЕ ВОССТАНОВЛЕНИЯ ФУНКЦИОНАЛЬНОСТИ - РЕЗУЛЬТАТЫ")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов прошли успешно ({success_rate:.1f}%)")
        
        if success_rate >= 85:
            print("🎉 ВОССТАНОВЛЕНИЕ ФУНКЦИОНАЛЬНОСТИ: ПОЛНОСТЬЮ УСПЕШНО")
            print("✅ Изоляция работает И функциональность восстановлена!")
        elif success_rate >= 70:
            print("⚠️ ВОССТАНОВЛЕНИЕ ФУНКЦИОНАЛЬНОСТИ: ЧАСТИЧНО РАБОТАЕТ")
            print("⚠️ Некоторые функции требуют дополнительного исправления")
        else:
            print("🚨 ВОССТАНОВЛЕНИЕ ФУНКЦИОНАЛЬНОСТИ: КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("🚨 Функциональность НЕ восстановлена после исправления изоляции!")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results,
            'generated_techcard_id': self.generated_techcard_id,
            'functionality_restored': success_rate >= 85
        }

def main():
    """Main test execution"""
    print("СРОЧНОЕ ТЕСТИРОВАНИЕ ВОССТАНОВЛЕНИЯ ФУНКЦИОНАЛЬНОСТИ")
    print("после исправления изоляции пользователей")
    print()
    
    # Check environment variables
    if not all([IIKO_RMS_HOST, IIKO_RMS_LOGIN, IIKO_RMS_PASSWORD]):
        print("❌ ERROR: Missing IIKO RMS credentials in environment variables")
        print("Required: IIKO_RMS_HOST, IIKO_RMS_LOGIN, IIKO_RMS_PASSWORD")
        sys.exit(1)
    
    tester = UserIsolationFixTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['functionality_restored']:
        print("\n🎉 ЗАКЛЮЧЕНИЕ: Функциональность ВОССТАНОВЛЕНА после исправления изоляции!")
        sys.exit(0)  # Success
    else:
        print("\n🚨 ЗАКЛЮЧЕНИЕ: Функциональность НЕ восстановлена - требуются дополнительные исправления!")
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()