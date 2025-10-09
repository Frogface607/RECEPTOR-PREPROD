#!/usr/bin/env python3
"""
AI Endpoints Testing - Unified OpenAI Client Fix Verification
Протестировать исправленные AI endpoints с unified OpenAI client

Test Plan:
1. Food Pairing Endpoint - POST /api/generate-food-pairing
2. Inspiration Endpoint - POST /api/generate-inspiration  
3. V1→V2 Converter Endpoint - POST /api/v1/convert-recipe-to-techcard

Цель: Убедиться что использование общего openai_client исправило HTTP 500 ошибки
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

class AIEndpointsTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Endpoints-Tester/1.0'
        })
        self.test_results = []
        
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
    
    def test_food_pairing_endpoint(self) -> bool:
        """Test 1: Food Pairing Endpoint - POST /api/generate-food-pairing"""
        try:
            url = f"{API_BASE}/generate-food-pairing"
            
            # Test data from review request
            payload = {
                "tech_card": {
                    "name": "Борщ",
                    "content": "Классический борщ с мясом"
                },
                "user_id": TEST_USER_ID
            }
            
            print(f"   Testing food pairing for: {payload['tech_card']['name']}")
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful food pairing generation
                if 'pairing' in data or 'suggestions' in data or 'recommendations' in data:
                    pairing_data = data.get('pairing', data.get('suggestions', data.get('recommendations', {})))
                    
                    # Check for typical food pairing content
                    has_content = False
                    if isinstance(pairing_data, dict):
                        has_content = any(key in pairing_data for key in ['drinks', 'wines', 'beverages', 'sides', 'garnishes'])
                    elif isinstance(pairing_data, str) and len(pairing_data) > 50:
                        has_content = True
                    elif isinstance(pairing_data, list) and len(pairing_data) > 0:
                        has_content = True
                    
                    if has_content:
                        self.log_test(
                            "Food Pairing Endpoint",
                            True,
                            f"Food pairing generated successfully for '{payload['tech_card']['name']}'",
                            {
                                'status_code': response.status_code,
                                'has_pairing_data': True,
                                'pairing_type': type(pairing_data).__name__,
                                'content_length': len(str(pairing_data))
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Food Pairing Endpoint",
                            False,
                            "Food pairing response lacks meaningful content",
                            data
                        )
                        return False
                else:
                    # Check if response has any meaningful content
                    if 'content' in data or 'result' in data:
                        content = data.get('content', data.get('result', ''))
                        if isinstance(content, str) and len(content) > 50:
                            self.log_test(
                                "Food Pairing Endpoint",
                                True,
                                f"Food pairing generated with content field (length: {len(content)})",
                                {
                                    'status_code': response.status_code,
                                    'content_length': len(content),
                                    'content_preview': content[:100] + "..." if len(content) > 100 else content
                                }
                            )
                            return True
                    
                    self.log_test(
                        "Food Pairing Endpoint",
                        False,
                        "Response missing expected food pairing fields",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Food Pairing Endpoint",
                    False,
                    f"Food pairing API returned HTTP {response.status_code}",
                    response.text[:300]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Food Pairing Endpoint",
                False,
                f"Food pairing API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Food Pairing Endpoint",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_inspiration_endpoint(self) -> bool:
        """Test 2: Inspiration Endpoint - POST /api/generate-inspiration"""
        try:
            url = f"{API_BASE}/generate-inspiration"
            
            # Test data from review request
            payload = {
                "tech_card": {
                    "name": "Борщ",
                    "content": "Классический борщ с мясом"
                },
                "user_id": TEST_USER_ID
            }
            
            print(f"   Testing inspiration generation for: {payload['tech_card']['name']}")
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful inspiration generation
                if 'inspiration' in data or 'ideas' in data or 'suggestions' in data:
                    inspiration_data = data.get('inspiration', data.get('ideas', data.get('suggestions', {})))
                    
                    # Check for meaningful inspiration content
                    has_content = False
                    if isinstance(inspiration_data, dict):
                        has_content = any(key in inspiration_data for key in ['variations', 'improvements', 'creative_ideas', 'modifications'])
                    elif isinstance(inspiration_data, str) and len(inspiration_data) > 50:
                        has_content = True
                    elif isinstance(inspiration_data, list) and len(inspiration_data) > 0:
                        has_content = True
                    
                    if has_content:
                        self.log_test(
                            "Inspiration Endpoint",
                            True,
                            f"Inspiration generated successfully for '{payload['tech_card']['name']}'",
                            {
                                'status_code': response.status_code,
                                'has_inspiration_data': True,
                                'inspiration_type': type(inspiration_data).__name__,
                                'content_length': len(str(inspiration_data))
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Inspiration Endpoint",
                            False,
                            "Inspiration response lacks meaningful content",
                            data
                        )
                        return False
                else:
                    # Check if response has any meaningful content
                    if 'content' in data or 'result' in data:
                        content = data.get('content', data.get('result', ''))
                        if isinstance(content, str) and len(content) > 50:
                            self.log_test(
                                "Inspiration Endpoint",
                                True,
                                f"Inspiration generated with content field (length: {len(content)})",
                                {
                                    'status_code': response.status_code,
                                    'content_length': len(content),
                                    'content_preview': content[:100] + "..." if len(content) > 100 else content
                                }
                            )
                            return True
                    
                    self.log_test(
                        "Inspiration Endpoint",
                        False,
                        "Response missing expected inspiration fields",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Inspiration Endpoint",
                    False,
                    f"Inspiration API returned HTTP {response.status_code}",
                    response.text[:300]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Inspiration Endpoint",
                False,
                f"Inspiration API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Inspiration Endpoint",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_v1_to_v2_converter_endpoint(self) -> bool:
        """Test 3: V1→V2 Converter Endpoint - POST /api/v1/convert-recipe-to-techcard"""
        try:
            url = f"{API_BASE}/v1/convert-recipe-to-techcard"
            
            # Test data from review request
            payload = {
                "recipe_content": "Простой борщ с капустой и мясом",
                "recipe_name": "Тест конвертации",
                "user_id": TEST_USER_ID
            }
            
            print(f"   Testing V1→V2 conversion for: {payload['recipe_name']}")
            
            response = self.session.post(url, json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful V1→V2 conversion
                if 'success' in data and data.get('success'):
                    # Check for V2 tech card structure
                    if 'techcard' in data:
                        techcard = data['techcard']
                        
                        # Validate V2 tech card structure
                        required_fields = ['ingredients', 'process', 'yield_', 'nutrition', 'cost']
                        has_required_fields = all(field in techcard for field in required_fields)
                        
                        if has_required_fields:
                            ingredients_count = len(techcard.get('ingredients', []))
                            process_steps = len(techcard.get('process', []))
                            
                            self.log_test(
                                "V1→V2 Converter Endpoint",
                                True,
                                f"V1→V2 conversion successful. Ingredients: {ingredients_count}, Process steps: {process_steps}",
                                {
                                    'status_code': response.status_code,
                                    'success': data.get('success'),
                                    'ingredients_count': ingredients_count,
                                    'process_steps': process_steps,
                                    'has_yield': 'yield_' in techcard,
                                    'has_nutrition': 'nutrition' in techcard,
                                    'has_cost': 'cost' in techcard
                                }
                            )
                            return True
                        else:
                            missing_fields = [field for field in required_fields if field not in techcard]
                            self.log_test(
                                "V1→V2 Converter Endpoint",
                                False,
                                f"V2 tech card missing required fields: {missing_fields}",
                                data
                            )
                            return False
                    else:
                        self.log_test(
                            "V1→V2 Converter Endpoint",
                            False,
                            "Response missing 'techcard' field",
                            data
                        )
                        return False
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_test(
                        "V1→V2 Converter Endpoint",
                        False,
                        f"Conversion failed: {error_msg}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "V1→V2 Converter Endpoint",
                    False,
                    f"V1→V2 converter API returned HTTP {response.status_code}",
                    response.text[:300]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V1→V2 Converter Endpoint",
                False,
                f"V1→V2 converter API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "V1→V2 Converter Endpoint",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all AI endpoints tests"""
        print("🚀 STARTING AI ENDPOINTS TESTING - UNIFIED OPENAI CLIENT FIX VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER_ID}")
        print("=" * 80)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_food_pairing_endpoint,
            self.test_inspiration_endpoint,
            self.test_v1_to_v2_converter_endpoint
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
        print("=" * 80)
        print("🎯 AI ENDPOINTS TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 AI ENDPOINTS: UNIFIED OPENAI CLIENT FIX SUCCESSFUL - ALL HTTP 500 ERRORS RESOLVED")
        elif success_rate >= 66:
            print("⚠️ AI ENDPOINTS: PARTIALLY FIXED - SOME HTTP 500 ERRORS REMAIN")
        else:
            print("🚨 AI ENDPOINTS: CRITICAL ISSUES - HTTP 500 ERRORS NOT RESOLVED")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    print("AI Endpoints Testing - Unified OpenAI Client Fix Verification")
    print("Протестировать исправленные AI endpoints с unified OpenAI client")
    print()
    
    tester = AIEndpointsTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] == 100:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()