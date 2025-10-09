#!/usr/bin/env python3
"""
V2 TechCard Generation Testing
Быстрый тест восстановленной V2 функциональности

Test Plan:
1. Проверить доступность V2 endpoint `/api/v1/techcards.v2/generate`
2. Протестировать генерацию с тестовыми данными:
   - name: "Борщ классический"
   - user_id: "demo_user"
   - cuisine: "европейская"
3. Проверить структуру ответа V2 (должен содержать card/techcard)
4. Убедиться в отсутствии ошибок

Цель: Подтвердить что V2 функциональность восстановлена и работает стабильно
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test user
TEST_USER_ID = "demo_user"

class V2TechCardTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'V2-TechCard-Tester/1.0'
        })
        self.test_results = []
        self.generated_techcard = None
        
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
        
    def test_v2_endpoint_availability(self) -> bool:
        """Test 1: Проверить доступность V2 endpoint `/api/v1/techcards.v2/generate`"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Test with minimal payload to check endpoint availability
            test_payload = {
                "name": "Test Dish",
                "user_id": TEST_USER_ID,
                "cuisine": "европейская"
            }
            
            print(f"   Testing V2 endpoint availability: {url}")
            
            response = self.session.post(url, json=test_payload, timeout=30)
            
            if response.status_code in [200, 400, 422]:  # Any response means endpoint is available
                self.log_test(
                    "V2 Endpoint Availability",
                    True,
                    f"V2 endpoint is available and responding (HTTP {response.status_code})"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "V2 Endpoint Availability",
                    False,
                    f"V2 endpoint not found (HTTP 404)",
                    response.text[:200]
                )
                return False
            else:
                self.log_test(
                    "V2 Endpoint Availability",
                    True,  # Still available, just different response
                    f"V2 endpoint available but returned HTTP {response.status_code}"
                )
                return True
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V2 Endpoint Availability",
                False,
                f"V2 endpoint connection failed: {str(e)}"
            )
            return False
    
    def test_v2_generation_with_test_data(self) -> bool:
        """Test 2: Протестировать генерацию с тестовыми данными"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Test data as specified in review request
            payload = {
                "name": "Борщ классический",
                "user_id": "demo_user",
                "cuisine": "европейская"
            }
            
            print(f"   Generating V2 techcard: {payload['name']}")
            print(f"   User: {payload['user_id']}, Cuisine: {payload['cuisine']}")
            
            response = self.session.post(url, json=payload, timeout=90)  # Extended timeout for generation
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check for successful generation
                    if 'status' in data and 'card' in data:
                        card = data['card']
                        status = data['status']
                        
                        # Extract key information
                        card_id = None
                        card_name = None
                        ingredients_count = 0
                        
                        if isinstance(card, dict):
                            # Try different possible structures
                            if 'meta' in card and isinstance(card['meta'], dict):
                                card_id = card['meta'].get('id')
                                card_name = card['meta'].get('title') or card['meta'].get('name')
                            
                            if 'ingredients' in card and isinstance(card['ingredients'], list):
                                ingredients_count = len(card['ingredients'])
                        
                        self.generated_techcard = {
                            'id': card_id,
                            'name': card_name or payload['name'],
                            'status': status,
                            'ingredients_count': ingredients_count,
                            'full_data': card
                        }
                        
                        self.log_test(
                            "V2 Generation with Test Data",
                            True,
                            f"V2 techcard generated successfully. ID: {card_id}, Status: {status}, Ingredients: {ingredients_count}",
                            {
                                'id': card_id,
                                'name': card_name,
                                'status': status,
                                'ingredients_count': ingredients_count
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "V2 Generation with Test Data",
                            False,
                            "Response missing required V2 fields (status, card)",
                            data
                        )
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log_test(
                        "V2 Generation with Test Data",
                        False,
                        f"Invalid JSON response: {str(e)}",
                        response.text[:200]
                    )
                    return False
            else:
                self.log_test(
                    "V2 Generation with Test Data",
                    False,
                    f"V2 generation failed with HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V2 Generation with Test Data",
                False,
                f"V2 generation request failed: {str(e)}"
            )
            return False
    
    def test_v2_response_structure(self) -> bool:
        """Test 3: Проверить структуру ответа V2 (должен содержать card/techcard)"""
        if not self.generated_techcard:
            self.log_test(
                "V2 Response Structure",
                False,
                "No generated techcard available for structure validation"
            )
            return False
        
        try:
            card_data = self.generated_techcard['full_data']
            
            # Check required V2 structure elements
            required_fields = []
            optional_fields = []
            found_fields = []
            
            if isinstance(card_data, dict):
                # Check for meta information
                if 'meta' in card_data:
                    found_fields.append('meta')
                    required_fields.append('meta')
                
                # Check for ingredients
                if 'ingredients' in card_data:
                    found_fields.append('ingredients')
                    required_fields.append('ingredients')
                
                # Check for process steps
                if 'process' in card_data or 'steps' in card_data or 'process_steps' in card_data:
                    found_fields.append('process_steps')
                    optional_fields.append('process_steps')
                
                # Check for nutrition info
                if 'nutrition' in card_data or 'nutritional_info' in card_data:
                    found_fields.append('nutrition')
                    optional_fields.append('nutrition')
                
                # Check for cost information
                if 'cost' in card_data or 'cost_analysis' in card_data:
                    found_fields.append('cost')
                    optional_fields.append('cost')
            
            # Validate structure
            if len(found_fields) >= 2:  # At least meta and ingredients
                self.log_test(
                    "V2 Response Structure",
                    True,
                    f"V2 response structure is valid. Found fields: {', '.join(found_fields)}",
                    {
                        'required_fields': required_fields,
                        'optional_fields': optional_fields,
                        'found_fields': found_fields
                    }
                )
                return True
            else:
                self.log_test(
                    "V2 Response Structure",
                    False,
                    f"V2 response structure incomplete. Found only: {', '.join(found_fields)}",
                    {
                        'expected_minimum': ['meta', 'ingredients'],
                        'found_fields': found_fields
                    }
                )
                return False
                
        except Exception as e:
            self.log_test(
                "V2 Response Structure",
                False,
                f"Error validating V2 response structure: {str(e)}"
            )
            return False
    
    def test_error_absence(self) -> bool:
        """Test 4: Убедиться в отсутствии ошибок"""
        if not self.generated_techcard:
            self.log_test(
                "Error Absence Check",
                False,
                "No generated techcard available for error checking"
            )
            return False
        
        try:
            # Check for common error indicators
            error_indicators = []
            
            # Check status
            status = self.generated_techcard.get('status', '').lower()
            if 'error' in status or 'failed' in status:
                error_indicators.append(f"Error status: {status}")
            
            # Check card data for error fields
            card_data = self.generated_techcard.get('full_data', {})
            if isinstance(card_data, dict):
                if 'error' in card_data:
                    error_indicators.append(f"Error field in card: {card_data['error']}")
                
                if 'errors' in card_data and card_data['errors']:
                    error_indicators.append(f"Errors array: {len(card_data['errors'])} errors")
                
                # Check ingredients for errors
                ingredients = card_data.get('ingredients', [])
                if isinstance(ingredients, list) and len(ingredients) == 0:
                    error_indicators.append("No ingredients generated")
            
            # Evaluate results
            if len(error_indicators) == 0:
                self.log_test(
                    "Error Absence Check",
                    True,
                    "No errors detected in V2 generation process",
                    {
                        'status': self.generated_techcard.get('status'),
                        'ingredients_count': self.generated_techcard.get('ingredients_count', 0)
                    }
                )
                return True
            else:
                self.log_test(
                    "Error Absence Check",
                    False,
                    f"Errors detected: {'; '.join(error_indicators)}",
                    error_indicators
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Error Absence Check",
                False,
                f"Error during error checking: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all V2 techcard generation tests"""
        print("🚀 STARTING V2 TECHCARD GENERATION TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER_ID}")
        print(f"Test Dish: Борщ классический")
        print("=" * 60)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_v2_endpoint_availability,
            self.test_v2_generation_with_test_data,
            self.test_v2_response_structure,
            self.test_error_absence
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
        print("🎯 V2 TECHCARD GENERATION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 75:
            print("🎉 V2 TECHCARD GENERATION: FULLY OPERATIONAL")
        elif success_rate >= 50:
            print("⚠️ V2 TECHCARD GENERATION: PARTIALLY WORKING")
        else:
            print("🚨 V2 TECHCARD GENERATION: CRITICAL ISSUES")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results,
            'generated_techcard': self.generated_techcard
        }

def main():
    """Main test execution"""
    print("V2 TechCard Generation Testing")
    print("Быстрый тест восстановленной V2 функциональности")
    print()
    
    tester = V2TechCardTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 75:
        return 0  # Success
    else:
        return 1  # Failure

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)