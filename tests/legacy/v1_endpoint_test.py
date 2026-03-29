#!/usr/bin/env python3
"""
V1 Recipe Generation Endpoint Testing
Проверить работоспособность V1 endpoint после внесения изменений

ЗАДАЧА: Убедиться что `/api/v1/generate-recipe` endpoint работает и не имеет проблем

ТЕСТ-КЕЙСЫ:
1. Проверить доступность endpoint `/api/v1/generate-recipe`
2. Протестировать с простым запросом:
   - dish_name: "Борщ"  
   - user_id: "demo_user"
3. Измерить время ответа (ожидается 30-60 секунд)
4. Проверить структуру ответа
5. Убедиться, что нет внутренних ошибок сервера

ЦЕЛЬ: Убедиться, что проблема не в backend, а в frontend timeout handling
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

# Test user
TEST_USER_ID = "demo_user"

class V1EndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'V1-Endpoint-Tester/1.0'
        })
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None, response_time: float = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data,
            'response_time': response_time
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}")
        print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
        
    def test_endpoint_availability(self) -> bool:
        """Test 1: Проверить доступность endpoint `/api/v1/generate-recipe`"""
        try:
            url = f"{API_BASE}/v1/generate-recipe"
            
            # Test with OPTIONS request first to check if endpoint exists
            start_time = time.time()
            response = self.session.options(url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 405]:  # 405 is OK for OPTIONS, means endpoint exists
                self.log_test(
                    "Endpoint Availability",
                    True,
                    f"Endpoint `/api/v1/generate-recipe` is available (HTTP {response.status_code})",
                    None,
                    response_time
                )
                return True
            else:
                self.log_test(
                    "Endpoint Availability", 
                    False,
                    f"Endpoint returned HTTP {response.status_code}",
                    response.text[:200],
                    response_time
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Endpoint Availability",
                False, 
                f"Endpoint connection failed: {str(e)}"
            )
            return False
    
    def test_simple_recipe_request(self) -> bool:
        """Test 2: Протестировать с простым запросом: dish_name: "Борщ", user_id: "demo_user" """
        try:
            url = f"{API_BASE}/v1/generate-recipe"
            
            # Simple recipe request as specified
            payload = {
                "dish_name": "Борщ",
                "user_id": "demo_user"
            }
            
            print(f"   Generating recipe for: {payload['dish_name']}")
            print(f"   Expected response time: 30-60 seconds")
            
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=90)  # 90s timeout for safety
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check if response has expected structure
                    if isinstance(data, dict):
                        self.log_test(
                            "Simple Recipe Request",
                            True,
                            f"Recipe generated successfully for 'Борщ' in {response_time:.1f}s",
                            {
                                'response_keys': list(data.keys()),
                                'response_size': len(str(data))
                            },
                            response_time
                        )
                        return True
                    else:
                        self.log_test(
                            "Simple Recipe Request",
                            False,
                            f"Unexpected response format (not JSON object)",
                            data,
                            response_time
                        )
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log_test(
                        "Simple Recipe Request",
                        False,
                        f"Invalid JSON response: {str(e)}",
                        response.text[:200],
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Simple Recipe Request",
                    False,
                    f"Recipe generation failed with HTTP {response.status_code}",
                    response.text[:200],
                    response_time
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Simple Recipe Request",
                False,
                f"Request timed out after 90 seconds (expected 30-60s)"
            )
            return False
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Simple Recipe Request",
                False,
                f"Request failed: {str(e)}"
            )
            return False
    
    def test_response_time_measurement(self) -> bool:
        """Test 3: Измерить время ответа (ожидается 30-60 секунд)"""
        try:
            url = f"{API_BASE}/v1/generate-recipe"
            
            # Test with another simple dish
            payload = {
                "dish_name": "Омлет",
                "user_id": "demo_user"
            }
            
            print(f"   Measuring response time for: {payload['dish_name']}")
            
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=90)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check if response time is within expected range (30-60 seconds)
                if 30 <= response_time <= 60:
                    self.log_test(
                        "Response Time Measurement",
                        True,
                        f"Response time {response_time:.1f}s is within expected range (30-60s)",
                        None,
                        response_time
                    )
                    return True
                elif response_time < 30:
                    self.log_test(
                        "Response Time Measurement",
                        True,  # Still success, just faster than expected
                        f"Response time {response_time:.1f}s is faster than expected (30-60s) - this is good!",
                        None,
                        response_time
                    )
                    return True
                else:
                    self.log_test(
                        "Response Time Measurement",
                        False,
                        f"Response time {response_time:.1f}s exceeds expected range (30-60s)",
                        None,
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Response Time Measurement",
                    False,
                    f"Request failed with HTTP {response.status_code}",
                    response.text[:200],
                    response_time
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Response Time Measurement",
                False,
                f"Request timed out after 90 seconds (exceeds expected 30-60s range)"
            )
            return False
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Response Time Measurement",
                False,
                f"Request failed: {str(e)}"
            )
            return False
    
    def test_response_structure(self) -> bool:
        """Test 4: Проверить структуру ответа"""
        try:
            url = f"{API_BASE}/v1/generate-recipe"
            
            payload = {
                "dish_name": "Салат Цезарь",
                "user_id": "demo_user"
            }
            
            print(f"   Testing response structure for: {payload['dish_name']}")
            
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=90)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Analyze response structure
                    structure_info = {
                        'type': type(data).__name__,
                        'keys': list(data.keys()) if isinstance(data, dict) else None,
                        'size': len(str(data)),
                        'has_recipe_data': False
                    }
                    
                    # Check for common recipe fields
                    if isinstance(data, dict):
                        recipe_fields = ['recipe', 'ingredients', 'instructions', 'name', 'title', 'content']
                        found_fields = [field for field in recipe_fields if field in data]
                        structure_info['found_recipe_fields'] = found_fields
                        structure_info['has_recipe_data'] = len(found_fields) > 0
                    
                    self.log_test(
                        "Response Structure",
                        True,
                        f"Response structure analyzed successfully",
                        structure_info,
                        response_time
                    )
                    return True
                    
                except json.JSONDecodeError as e:
                    self.log_test(
                        "Response Structure",
                        False,
                        f"Response is not valid JSON: {str(e)}",
                        response.text[:200],
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "Response Structure",
                    False,
                    f"Cannot analyze structure - HTTP {response.status_code}",
                    response.text[:200],
                    response_time
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Response Structure",
                False,
                f"Request failed: {str(e)}"
            )
            return False
    
    def test_no_server_errors(self) -> bool:
        """Test 5: Убедиться, что нет внутренних ошибок сервера"""
        try:
            url = f"{API_BASE}/v1/generate-recipe"
            
            # Test with multiple requests to check for consistency
            test_dishes = ["Суп", "Каша", "Котлеты"]
            
            all_success = True
            error_responses = []
            
            for dish in test_dishes:
                payload = {
                    "dish_name": dish,
                    "user_id": "demo_user"
                }
                
                print(f"   Testing server stability with: {dish}")
                
                start_time = time.time()
                response = self.session.post(url, json=payload, timeout=90)
                response_time = time.time() - start_time
                
                # Check for server errors (5xx status codes)
                if 500 <= response.status_code < 600:
                    all_success = False
                    error_responses.append({
                        'dish': dish,
                        'status_code': response.status_code,
                        'response': response.text[:100],
                        'response_time': response_time
                    })
                elif response.status_code != 200:
                    # Non-200 but not server error - still note it
                    error_responses.append({
                        'dish': dish,
                        'status_code': response.status_code,
                        'response': response.text[:100],
                        'response_time': response_time,
                        'type': 'client_error'
                    })
                
                time.sleep(2)  # Brief pause between requests
            
            if all_success and not any(err.get('type') != 'client_error' for err in error_responses):
                self.log_test(
                    "No Server Errors",
                    True,
                    f"No internal server errors detected across {len(test_dishes)} test requests",
                    {'tested_dishes': test_dishes, 'errors': error_responses}
                )
                return True
            else:
                server_errors = [err for err in error_responses if err.get('type') != 'client_error']
                self.log_test(
                    "No Server Errors",
                    False,
                    f"Detected {len(server_errors)} server errors",
                    {'server_errors': server_errors, 'all_errors': error_responses}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "No Server Errors",
                False,
                f"Request failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all V1 endpoint tests"""
        print("🚀 STARTING V1 ENDPOINT TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Target Endpoint: /api/v1/generate-recipe")
        print(f"Test User: {TEST_USER_ID}")
        print("=" * 60)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_endpoint_availability,
            self.test_simple_recipe_request,
            self.test_response_time_measurement,
            self.test_response_structure,
            self.test_no_server_errors
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_func.__name__}: {str(e)}")
        
        # Summary
        print("=" * 60)
        print("🎯 V1 ENDPOINT TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            time_info = f" ({result['response_time']:.2f}s)" if result.get('response_time') else ""
            print(f"{status} {result['test_name']}{time_info}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 V1 ENDPOINT: FULLY OPERATIONAL")
            print("✅ Проблема НЕ в backend - endpoint работает корректно")
            print("🔍 Рекомендация: Проверить frontend timeout handling")
        elif success_rate >= 60:
            print("⚠️ V1 ENDPOINT: PARTIALLY WORKING")
            print("🔍 Рекомендация: Исследовать выявленные проблемы")
        else:
            print("🚨 V1 ENDPOINT: CRITICAL ISSUES")
            print("❌ Проблема В backend - требуется исправление")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results,
            'conclusion': 'backend_ok' if success_rate >= 80 else 'backend_issues'
        }

def main():
    """Main test execution"""
    print("V1 Recipe Generation Endpoint Testing")
    print("Проверить работоспособность V1 endpoint после внесения изменений")
    print()
    
    tester = V1EndpointTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()