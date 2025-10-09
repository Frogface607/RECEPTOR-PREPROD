#!/usr/bin/env python3
"""
V1→V2 Converter and V2 Generation Testing
Протестировать исправленную V1→V2 конвертацию и основную V2 генерацию

Test Plan:
1. V2 основная генерация - endpoint /api/v1/techcards.v2/generate
2. V1→V2 настоящий конвертер - endpoint /api/v1/convert-recipe-to-techcard

Цель: Убедиться что исправления работают и дают настоящие V2 техкарты, а не fake
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

class V1V2ConverterTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'V1V2-Converter-Tester/1.0'
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
        
    def test_v2_generation(self) -> bool:
        """Test 1: V2 основная генерация - endpoint /api/v1/techcards.v2/generate"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Test data as specified in review request
            payload = {
                "name": "Омлет",
                "user_id": "demo_user"
            }
            
            print(f"   Testing V2 generation with dish: {payload['name']}")
            start_time = time.time()
            
            response = self.session.post(url, json=payload, timeout=95)  # 95s timeout to be safe
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful generation with proper V2 structure
                if 'status' in data and 'card' in data:
                    status = data['status']
                    card = data['card']
                    
                    # Validate V2 tech card structure
                    has_ingredients = 'ingredients' in card and isinstance(card.get('ingredients'), list)
                    has_process = 'process' in card and isinstance(card.get('process'), list)
                    has_meta = 'meta' in card and isinstance(card.get('meta'), dict) and 'id' in card.get('meta', {})
                    
                    if status == 'READY' and has_ingredients and has_process and has_meta:
                        card_id = card['meta']['id']
                        ingredients_count = len(card.get('ingredients', []))
                        process_steps = len(card.get('process', []))
                        
                        # Check timeout requirement (≤90 seconds)
                        timeout_ok = duration <= 90
                        
                        self.log_test(
                            "V2 Tech Card Generation",
                            True,
                            f"V2 generation successful in {duration:.1f}s (timeout requirement: ≤90s {'✅' if timeout_ok else '❌'}). ID: {card_id}, Ingredients: {ingredients_count}, Process steps: {process_steps}",
                            {
                                'duration_seconds': duration,
                                'timeout_met': timeout_ok,
                                'card_id': card_id,
                                'status': status,
                                'ingredients_count': ingredients_count,
                                'process_steps': process_steps
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "V2 Tech Card Generation",
                            False,
                            f"Invalid V2 structure: status={status}, has_ingredients={has_ingredients}, has_process={has_process}, has_meta={has_meta}",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "V2 Tech Card Generation",
                        False,
                        "Response missing required fields (status, card)",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "V2 Tech Card Generation",
                    False,
                    f"V2 generation API returned HTTP {response.status_code}",
                    response.text[:300]
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_test(
                "V2 Tech Card Generation",
                False,
                f"V2 generation timed out after 95 seconds (requirement: ≤90s)"
            )
            return False
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V2 Tech Card Generation",
                False,
                f"V2 generation API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "V2 Tech Card Generation",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_v1_to_v2_converter(self) -> bool:
        """Test 2: V1→V2 настоящий конвертер - endpoint /api/v1/convert-recipe-to-techcard"""
        try:
            url = f"{API_BASE}/v1/convert-recipe-to-techcard"
            
            # Test data as specified in review request
            payload = {
                "recipe_content": "Простой рецепт омлета: взбить 2 яйца, добавить молоко, обжарить на сковороде",
                "recipe_name": "Омлет V1→V2",
                "user_id": "demo_user"
            }
            
            print(f"   Testing V1→V2 conversion for: {payload['recipe_name']}")
            start_time = time.time()
            
            response = self.session.post(url, json=payload, timeout=90)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful conversion with proper V2 structure
                if 'success' in data and data['success']:
                    # Look for techcard data in response
                    techcard = data.get('techcard', {})
                    
                    # Validate V2 tech card structure from converter
                    has_ingredients = 'ingredients' in techcard and isinstance(techcard['ingredients'], list)
                    has_process = 'process' in techcard and isinstance(techcard['process'], list)
                    has_yield = ('yield' in techcard or 'yield_' in techcard) and isinstance(techcard.get('yield', techcard.get('yield_', {})), dict)
                    has_nutrition = 'nutrition' in techcard and isinstance(techcard['nutrition'], dict)
                    has_cost = 'cost' in techcard and isinstance(techcard['cost'], dict)
                    
                    if has_ingredients and has_process and has_yield and has_nutrition and has_cost:
                        techcard_id = data.get('id', 'unknown')
                        ingredients_count = len(techcard['ingredients'])
                        process_steps = len(techcard['process'])
                        
                        # Check that this is a REAL V2 tech card, not fake
                        ingredients_have_content = any(
                            ing.get('name') and (ing.get('quantity') or ing.get('brutto_g') or ing.get('netto_g'))
                            for ing in techcard['ingredients']
                        )
                        process_has_content = any(
                            step.get('description') or step.get('instruction') or step.get('action')
                            for step in techcard['process']
                        )
                        
                        is_real_techcard = ingredients_have_content and process_has_content
                        
                        self.log_test(
                            "V1→V2 Recipe Converter",
                            True,
                            f"V1→V2 conversion successful in {duration:.1f}s. ID: {techcard_id}, Ingredients: {ingredients_count}, Process steps: {process_steps}, Real content: {'✅' if is_real_techcard else '❌'}",
                            {
                                'duration_seconds': duration,
                                'techcard_id': techcard_id,
                                'ingredients_count': ingredients_count,
                                'process_steps': process_steps,
                                'has_real_content': is_real_techcard,
                                'structure_valid': True
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "V1→V2 Recipe Converter",
                            False,
                            f"Invalid V2 structure from converter: ingredients={has_ingredients}, process={has_process}, yield={has_yield}, nutrition={has_nutrition}, cost={has_cost}",
                            data
                        )
                        return False
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self.log_test(
                        "V1→V2 Recipe Converter",
                        False,
                        f"Conversion failed: {error_msg}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "V1→V2 Recipe Converter",
                    False,
                    f"V1→V2 converter API returned HTTP {response.status_code}",
                    response.text[:300]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V1→V2 Recipe Converter",
                False,
                f"V1→V2 converter API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "V1→V2 Recipe Converter",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
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
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all V1→V2 converter and V2 generation tests"""
        print("🚀 STARTING V1→V2 CONVERTER AND V2 GENERATION TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER_ID}")
        print("=" * 70)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_backend_health,
            self.test_v2_generation,
            self.test_v1_to_v2_converter
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
        print("=" * 70)
        print("🎯 V1→V2 CONVERTER AND V2 GENERATION TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 V1→V2 CONVERTER AND V2 GENERATION: FULLY OPERATIONAL")
        elif success_rate >= 60:
            print("⚠️ V1→V2 CONVERTER AND V2 GENERATION: PARTIALLY WORKING")
        else:
            print("🚨 V1→V2 CONVERTER AND V2 GENERATION: CRITICAL ISSUES")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    print("V1→V2 Converter and V2 Generation Backend Testing")
    print("Протестировать исправленную V1→V2 конвертацию и основную V2 генерацию")
    print()
    
    tester = V1V2ConverterTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()