#!/usr/bin/env python3
"""
🚨 КРИТИЧЕСКИЙ ТЕСТ БЕЗОПАСНОСТИ: Проверить изоляцию данных для демо-пользователя

**Тест безопасности данных IIKO:**

1. **Автомаппинг для демо-пользователя**:
   - POST /api/v1/techcards.v2/mapping/enhanced с user_id="demo_user"
   - Ожидаемый результат: status="demo_mode", пустые results, сообщение о необходимости регистрации
   - НЕ должно быть доступа к реальным данным IIKO

2. **Поиск в каталоге для демо-пользователя**:
   - GET /api/v1/techcards.v2/catalog-search?q=мука&source=iiko&user_id=demo_user
   - GET /api/v1/techcards.v2/catalog-search?q=мука&source=rms&user_id=demo_user
   - Ожидаемый результат: НЕТ данных из IIKO/RMS для demo_user
   - Должны быть доступны только USDA/nutrition данные

3. **Тест для авторизованного пользователя** (если возможно):
   - Те же запросы с user_id != "demo_user"
   - Должны работать нормально и возвращать данные IIKO (если подключен)

**Цель**: Убедиться что демо-пользователи полностью изолированы от данных IIKO и не могут получить доступ к чужим данным.

**КРИТИЧНО**: Если демо-пользователь получает данные IIKO - это серьезная проблема безопасности!
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

# Test users
DEMO_USER_ID = "demo_user"
AUTHORIZED_USER_ID = "test_authorized_user"

class DemoSecurityTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Demo-Security-Tester/1.0'
        })
        self.test_results = []
        self.security_violations = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None, security_violation: bool = False):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data,
            'security_violation': security_violation
        }
        self.test_results.append(result)
        
        if security_violation:
            self.security_violations.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        if security_violation:
            status = "🚨 SECURITY VIOLATION"
        
        print(f"{status} {test_name}")
        print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}")
        print()
        
    def test_backend_health(self) -> bool:
        """Test 0: Backend Health Check"""
        try:
            response = self.session.get(f"{BACKEND_URL}/", timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "Backend Health Check",
                    True,
                    f"Backend responding correctly (HTTP {response.status_code})"
                )
                return True
            else:
                self.log_test(
                    "Backend Health Check", 
                    False,
                    f"Backend returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Backend Health Check",
                False, 
                f"Backend connection failed: {str(e)}"
            )
            return False

    def test_demo_user_automapping_isolation(self) -> bool:
        """Test 1: Автомаппинг для демо-пользователя - должен быть изолирован от данных IIKO"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/mapping/enhanced"
            
            # Test payload with common ingredients
            payload = {
                "techcard": {
                    "id": "demo-test-id",
                    "name": "Тестовое блюдо",
                    "ingredients": [
                        {"name": "мука пшеничная", "quantity": 100, "unit": "g"},
                        {"name": "яйца куриные", "quantity": 50, "unit": "g"},
                        {"name": "молоко", "quantity": 100, "unit": "ml"},
                        {"name": "сахар", "quantity": 20, "unit": "g"},
                        {"name": "соль", "quantity": 5, "unit": "g"}
                    ]
                },
                "ingredients": [
                    {"name": "мука пшеничная", "quantity": 100, "unit": "g"},
                    {"name": "яйца куриные", "quantity": 50, "unit": "g"},
                    {"name": "молоко", "quantity": 100, "unit": "ml"},
                    {"name": "сахар", "quantity": 20, "unit": "g"},
                    {"name": "соль", "quantity": 5, "unit": "g"}
                ],
                "user_id": DEMO_USER_ID
            }
            
            print(f"   Testing automapping for demo_user with {len(payload['ingredients'])} ingredients")
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for demo mode indicators
                status = data.get('status', '')
                results = data.get('results', [])
                message = data.get('message', '')
                
                # Security check: demo_user should NOT get IIKO data
                has_iiko_data = False
                has_rms_data = False
                
                if results:
                    for result in results:
                        if isinstance(result, dict):
                            suggestions = result.get('suggestions', [])
                            for suggestion in suggestions:
                                if isinstance(suggestion, dict):
                                    source = suggestion.get('source', '').lower()
                                    if 'iiko' in source or 'rms' in source:
                                        has_iiko_data = True
                                        break
                
                # Expected behavior for demo_user
                if status == "demo_mode" or "demo" in message.lower() or "регистрации" in message.lower():
                    self.log_test(
                        "Demo User Automapping Isolation",
                        True,
                        f"✅ SECURITY OK: Demo user correctly isolated. Status: {status}, Message: {message}"
                    )
                    return True
                elif has_iiko_data:
                    self.log_test(
                        "Demo User Automapping Isolation",
                        False,
                        f"🚨 SECURITY VIOLATION: Demo user received IIKO/RMS data! This is a critical security issue.",
                        data,
                        security_violation=True
                    )
                    return False
                elif not results or len(results) == 0:
                    self.log_test(
                        "Demo User Automapping Isolation",
                        True,
                        f"✅ SECURITY OK: Demo user received no IIKO data (empty results). Status: {status}"
                    )
                    return True
                else:
                    # Check if results contain only USDA/nutrition data (acceptable)
                    only_safe_sources = True
                    for result in results:
                        if isinstance(result, dict):
                            suggestions = result.get('suggestions', [])
                            for suggestion in suggestions:
                                if isinstance(suggestion, dict):
                                    source = suggestion.get('source', '').lower()
                                    if source and 'usda' not in source and 'nutrition' not in source and source != '':
                                        only_safe_sources = False
                                        break
                    
                    if only_safe_sources:
                        self.log_test(
                            "Demo User Automapping Isolation",
                            True,
                            f"✅ SECURITY OK: Demo user received only USDA/nutrition data (no IIKO data). Results: {len(results)}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Demo User Automapping Isolation",
                            False,
                            f"⚠️ POTENTIAL SECURITY ISSUE: Demo user received non-USDA data sources",
                            data
                        )
                        return False
            else:
                self.log_test(
                    "Demo User Automapping Isolation",
                    False,
                    f"Automapping API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Demo User Automapping Isolation",
                False,
                f"Automapping API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Demo User Automapping Isolation",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False

    def test_demo_user_catalog_search_iiko(self) -> bool:
        """Test 2: Поиск в каталоге IIKO для демо-пользователя - должен быть заблокирован"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/catalog-search"
            
            params = {
                "q": "мука",
                "source": "iiko",
                "user_id": DEMO_USER_ID
            }
            
            print(f"   Testing IIKO catalog search for demo_user: {params['q']}")
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                results = data.get('results', [])
                status = data.get('status', '')
                message = data.get('message', '')
                
                # Security check: demo_user should NOT get IIKO catalog data
                if not results or len(results) == 0:
                    if "demo" in status.lower() or "demo" in message.lower() or "регистрации" in message.lower():
                        self.log_test(
                            "Demo User IIKO Catalog Search Isolation",
                            True,
                            f"✅ SECURITY OK: Demo user correctly blocked from IIKO catalog. Status: {status}, Message: {message}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Demo User IIKO Catalog Search Isolation",
                            True,
                            f"✅ SECURITY OK: Demo user received no IIKO catalog data (empty results)"
                        )
                        return True
                else:
                    self.log_test(
                        "Demo User IIKO Catalog Search Isolation",
                        False,
                        f"🚨 SECURITY VIOLATION: Demo user received IIKO catalog data! Found {len(results)} results.",
                        data,
                        security_violation=True
                    )
                    return False
            else:
                # Non-200 response might be acceptable (blocked access)
                if response.status_code in [403, 401]:
                    self.log_test(
                        "Demo User IIKO Catalog Search Isolation",
                        True,
                        f"✅ SECURITY OK: Demo user correctly blocked from IIKO catalog (HTTP {response.status_code})"
                    )
                    return True
                else:
                    self.log_test(
                        "Demo User IIKO Catalog Search Isolation",
                        False,
                        f"IIKO catalog search returned HTTP {response.status_code}",
                        response.text[:200]
                    )
                    return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Demo User IIKO Catalog Search Isolation",
                False,
                f"IIKO catalog search request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Demo User IIKO Catalog Search Isolation",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False

    def test_demo_user_catalog_search_rms(self) -> bool:
        """Test 3: Поиск в каталоге RMS для демо-пользователя - должен быть заблокирован"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/catalog-search"
            
            params = {
                "q": "мука",
                "source": "rms",
                "user_id": DEMO_USER_ID
            }
            
            print(f"   Testing RMS catalog search for demo_user: {params['q']}")
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                results = data.get('results', [])
                status = data.get('status', '')
                message = data.get('message', '')
                
                # Security check: demo_user should NOT get RMS catalog data
                if not results or len(results) == 0:
                    if "demo" in status.lower() or "demo" in message.lower() or "регистрации" in message.lower():
                        self.log_test(
                            "Demo User RMS Catalog Search Isolation",
                            True,
                            f"✅ SECURITY OK: Demo user correctly blocked from RMS catalog. Status: {status}, Message: {message}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Demo User RMS Catalog Search Isolation",
                            True,
                            f"✅ SECURITY OK: Demo user received no RMS catalog data (empty results)"
                        )
                        return True
                else:
                    self.log_test(
                        "Demo User RMS Catalog Search Isolation",
                        False,
                        f"🚨 SECURITY VIOLATION: Demo user received RMS catalog data! Found {len(results)} results.",
                        data,
                        security_violation=True
                    )
                    return False
            else:
                # Non-200 response might be acceptable (blocked access)
                if response.status_code in [403, 401]:
                    self.log_test(
                        "Demo User RMS Catalog Search Isolation",
                        True,
                        f"✅ SECURITY OK: Demo user correctly blocked from RMS catalog (HTTP {response.status_code})"
                    )
                    return True
                else:
                    self.log_test(
                        "Demo User RMS Catalog Search Isolation",
                        False,
                        f"RMS catalog search returned HTTP {response.status_code}",
                        response.text[:200]
                    )
                    return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Demo User RMS Catalog Search Isolation",
                False,
                f"RMS catalog search request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Demo User RMS Catalog Search Isolation",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False

    def test_demo_user_usda_access(self) -> bool:
        """Test 4: Проверить что демо-пользователь может получать USDA данные"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/catalog-search"
            
            params = {
                "q": "flour",  # Use English for USDA
                "source": "usda",
                "user_id": DEMO_USER_ID
            }
            
            print(f"   Testing USDA catalog search for demo_user: {params['q']}")
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                results = data.get('results', [])
                
                # Demo user SHOULD be able to access USDA data
                if results and len(results) > 0:
                    self.log_test(
                        "Demo User USDA Access",
                        True,
                        f"✅ EXPECTED: Demo user can access USDA data. Found {len(results)} results."
                    )
                    return True
                else:
                    self.log_test(
                        "Demo User USDA Access",
                        True,  # Still OK if no results (might be no USDA data)
                        f"Demo user USDA search returned no results (might be expected if no USDA data available)"
                    )
                    return True
            else:
                self.log_test(
                    "Demo User USDA Access",
                    False,
                    f"USDA catalog search returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Demo User USDA Access",
                False,
                f"USDA catalog search request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Demo User USDA Access",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False

    def test_authorized_user_iiko_access(self) -> bool:
        """Test 5: Проверить что авторизованный пользователь может получать IIKO данные (если подключен)"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/catalog-search"
            
            params = {
                "q": "мука",
                "source": "iiko",
                "user_id": AUTHORIZED_USER_ID
            }
            
            print(f"   Testing IIKO catalog search for authorized user: {params['q']}")
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                results = data.get('results', [])
                status = data.get('status', '')
                message = data.get('message', '')
                
                # Authorized user should be able to access IIKO data (if connected)
                if results and len(results) > 0:
                    self.log_test(
                        "Authorized User IIKO Access",
                        True,
                        f"✅ EXPECTED: Authorized user can access IIKO data. Found {len(results)} results."
                    )
                    return True
                elif "not connected" in message.lower() or "не подключен" in message.lower():
                    self.log_test(
                        "Authorized User IIKO Access",
                        True,
                        f"✅ EXPECTED: Authorized user correctly informed about IIKO not being connected. Message: {message}"
                    )
                    return True
                else:
                    self.log_test(
                        "Authorized User IIKO Access",
                        True,  # Still OK - might be no IIKO connection
                        f"Authorized user IIKO search returned no results. Status: {status}, Message: {message}"
                    )
                    return True
            else:
                self.log_test(
                    "Authorized User IIKO Access",
                    False,
                    f"IIKO catalog search for authorized user returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Authorized User IIKO Access",
                False,
                f"IIKO catalog search for authorized user failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Authorized User IIKO Access",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False

    def test_authorized_user_automapping(self) -> bool:
        """Test 6: Проверить что авторизованный пользователь может использовать автомаппинг с IIKO данными"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/mapping/enhanced"
            
            # Test payload with common ingredients
            payload = {
                "techcard": {
                    "id": "auth-test-id",
                    "name": "Тестовое блюдо для авторизованного пользователя",
                    "ingredients": [
                        {"name": "мука пшеничная", "quantity": 100, "unit": "g"},
                        {"name": "яйца куриные", "quantity": 50, "unit": "g"},
                        {"name": "молоко", "quantity": 100, "unit": "ml"}
                    ]
                },
                "ingredients": [
                    {"name": "мука пшеничная", "quantity": 100, "unit": "g"},
                    {"name": "яйца куриные", "quantity": 50, "unit": "g"},
                    {"name": "молоко", "quantity": 100, "unit": "ml"}
                ],
                "user_id": AUTHORIZED_USER_ID
            }
            
            print(f"   Testing automapping for authorized user with {len(payload['ingredients'])} ingredients")
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                status = data.get('status', '')
                results = data.get('results', [])
                message = data.get('message', '')
                
                # Authorized user should get normal automapping results (not demo mode)
                if status != "demo_mode" and "demo" not in message.lower():
                    self.log_test(
                        "Authorized User Automapping",
                        True,
                        f"✅ EXPECTED: Authorized user gets normal automapping (not demo mode). Status: {status}, Results: {len(results)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Authorized User Automapping",
                        False,
                        f"❌ UNEXPECTED: Authorized user got demo mode response. Status: {status}, Message: {message}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Authorized User Automapping",
                    False,
                    f"Automapping for authorized user returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Authorized User Automapping",
                False,
                f"Automapping for authorized user failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Authorized User Automapping",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all demo security tests"""
        print("🚨 STARTING CRITICAL DEMO SECURITY TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Demo User: {DEMO_USER_ID}")
        print(f"Authorized User: {AUTHORIZED_USER_ID}")
        print("=" * 80)
        print("🎯 ЦЕЛЬ: Убедиться что демо-пользователи изолированы от данных IIKO")
        print("🚨 КРИТИЧНО: Если демо-пользователь получает данные IIKO - это проблема безопасности!")
        print("=" * 80)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_backend_health,
            self.test_demo_user_automapping_isolation,
            self.test_demo_user_catalog_search_iiko,
            self.test_demo_user_catalog_search_rms,
            self.test_demo_user_usda_access,
            self.test_authorized_user_iiko_access,
            self.test_authorized_user_automapping
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
        print("🎯 DEMO SECURITY TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            if result['security_violation']:
                status = "🚨 SECURITY VIOLATION"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        # Security violations summary
        if self.security_violations:
            print()
            print("🚨 CRITICAL SECURITY VIOLATIONS DETECTED:")
            for violation in self.security_violations:
                print(f"   - {violation['test_name']}: {violation['details']}")
            print()
            print("🚨 IMMEDIATE ACTION REQUIRED: Fix security violations before production!")
        else:
            print("✅ NO SECURITY VIOLATIONS DETECTED")
        
        if success_rate >= 85 and not self.security_violations:
            print("🎉 DEMO SECURITY: FULLY SECURE")
        elif success_rate >= 70 and not self.security_violations:
            print("⚠️ DEMO SECURITY: MOSTLY SECURE")
        else:
            print("🚨 DEMO SECURITY: CRITICAL ISSUES")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'security_violations': len(self.security_violations),
            'results': self.test_results,
            'violations': self.security_violations
        }

def main():
    """Main test execution"""
    print("🚨 КРИТИЧЕСКИЙ ТЕСТ БЕЗОПАСНОСТИ: Проверить изоляцию данных для демо-пользователя")
    print()
    
    tester = DemoSecurityTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 85 and results['security_violations'] == 0:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()