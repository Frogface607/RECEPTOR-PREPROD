#!/usr/bin/env python3
"""
V1→V2 Converter and V2 Generation Fixes Testing
Тестировать исправления V1→V2 и V2 генерации

Test Plan:
1. V2 основная генерация - проверить endpoint `/api/v1/techcards.v2/generate`
   - Название: "Стейк"
   - user_id: "demo_user"
   - Timeout: должен быть в пределах 90 секунд

2. V1→V2 конвертер - проверить endpoint `/api/v1/convert-recipe-to-techcard`
   - recipe_content: "Простой тестовый рецепт для конвертации"
   - recipe_name: "Тест V1→V2"
   - user_id: "demo_user"
   - Проверить структуру ответа: ingredients[], process[], yield{}, nutrition{}, cost{}

Цель: Убедиться что исправления решили проблемы таймаута и структуры данных
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

class V1V2FixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'V1V2-Fixes-Tester/1.0'
        })
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None, duration: float = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.1f}s)" if duration else ""
        print(f"{status} {test_name}{duration_str}")
        print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
        
    def test_backend_health(self) -> bool:
        """Test 0: Backend Health Check"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test(
                    "Backend Health Check",
                    True,
                    f"Backend responding correctly (HTTP {response.status_code})",
                    None,
                    duration
                )
                return True
            else:
                self.log_test(
                    "Backend Health Check", 
                    False,
                    f"Backend returned HTTP {response.status_code}",
                    response.text[:200],
                    duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Backend Health Check",
                False, 
                f"Backend connection failed: {str(e)}"
            )
            return False
    
    def test_v2_generation(self) -> bool:
        """Test 1: V2 основная генерация - проверить endpoint /api/v1/techcards.v2/generate"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Test payload as specified in review request
            payload = {
                "name": "Стейк",
                "user_id": TEST_USER_ID,
                "cuisine": "европейская",
                "equipment": ["плита", "сковорода"],
                "budget": 800.0,
                "dietary": []
            }
            
            print(f"   Generating V2 tech card: {payload['name']}")
            print(f"   Testing timeout within 90 seconds...")
            
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=95)  # 95s timeout to test 90s requirement
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check timeout requirement (должен быть в пределах 90 секунд)
                timeout_ok = duration <= 90.0
                
                # Check response structure
                if 'status' in data and 'card' in data:
                    card = data['card']
                    card_id = card.get('meta', {}).get('id')
                    status = data['status']
                    
                    # Check for required V2 structure
                    ingredients = card.get('ingredients', [])
                    process = card.get('process', [])
                    
                    structure_ok = bool(card_id and ingredients and process)
                    
                    if timeout_ok and structure_ok:
                        self.log_test(
                            "V2 Tech Card Generation",
                            True,
                            f"V2 generation successful within timeout. ID: {card_id}, Status: {status}, Duration: {duration:.1f}s (≤90s ✅), Ingredients: {len(ingredients)}, Process steps: {len(process)}",
                            {
                                'id': card_id,
                                'status': status,
                                'duration_seconds': duration,
                                'timeout_requirement_met': timeout_ok,
                                'ingredients_count': len(ingredients),
                                'process_steps_count': len(process),
                                'structure_valid': structure_ok
                            },
                            duration
                        )
                        return True
                    else:
                        issues = []
                        if not timeout_ok:
                            issues.append(f"Timeout exceeded: {duration:.1f}s > 90s")
                        if not structure_ok:
                            issues.append("Missing required V2 structure (id, ingredients, process)")
                        
                        self.log_test(
                            "V2 Tech Card Generation",
                            False,
                            f"V2 generation issues: {'; '.join(issues)}",
                            {
                                'duration_seconds': duration,
                                'timeout_requirement_met': timeout_ok,
                                'structure_valid': structure_ok,
                                'response': data
                            },
                            duration
                        )
                        return False
                else:
                    self.log_test(
                        "V2 Tech Card Generation",
                        False,
                        f"Response missing required fields (status, card). Duration: {duration:.1f}s",
                        data,
                        duration
                    )
                    return False
            else:
                self.log_test(
                    "V2 Tech Card Generation",
                    False,
                    f"V2 generation API returned HTTP {response.status_code}. Duration: {duration:.1f}s",
                    response.text[:200],
                    duration
                )
                return False
                
        except requests.exceptions.Timeout as e:
            duration = time.time() - start_time if 'start_time' in locals() else 95.0
            self.log_test(
                "V2 Tech Card Generation",
                False,
                f"V2 generation timed out after {duration:.1f}s (requirement: ≤90s)",
                str(e),
                duration
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
        """Test 2: V1→V2 конвертер - проверить endpoint /api/v1/convert-recipe-to-techcard"""
        try:
            url = f"{API_BASE}/v1/convert-recipe-to-techcard"
            
            # Test payload as specified in review request
            payload = {
                "recipe_content": "Простой тестовый рецепт для конвертации",
                "recipe_name": "Тест V1→V2",
                "user_id": TEST_USER_ID
            }
            
            print(f"   Converting V1 recipe to V2 tech card: {payload['recipe_name']}")
            print("   Checking response structure: ingredients[], process[], yield{}, nutrition{}, cost{}")
            
            start_time = time.time()
            response = self.session.post(url, json=payload, timeout=60)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # The API returns data nested under 'techcard' key
                techcard_data = data.get('techcard', {})
                
                # Check response structure as specified in review request
                required_fields = ['ingredients', 'process', 'yield', 'nutrition', 'cost']
                structure_checks = {}
                
                for field in required_fields:
                    if field in techcard_data:
                        field_data = techcard_data[field]
                        if field in ['ingredients', 'process']:
                            # Should be arrays
                            structure_checks[field] = isinstance(field_data, list)
                        else:
                            # Should be objects (yield, nutrition, cost)
                            structure_checks[field] = isinstance(field_data, dict)
                    else:
                        structure_checks[field] = False
                
                all_fields_valid = all(structure_checks.values())
                
                # Additional checks
                ingredients_count = len(techcard_data.get('ingredients', [])) if isinstance(techcard_data.get('ingredients'), list) else 0
                process_count = len(techcard_data.get('process', [])) if isinstance(techcard_data.get('process'), list) else 0
                
                # Check if conversion was successful - structure is valid and we have content
                has_content = bool(techcard_data.get('content', '').strip())
                conversion_successful = data.get('success', False)
                has_techcard_id = bool(techcard_data.get('meta', {}).get('id'))
                
                if all_fields_valid and conversion_successful and has_content and has_techcard_id:
                    self.log_test(
                        "V1→V2 Recipe Converter",
                        True,
                        f"V1→V2 conversion successful. Duration: {duration:.1f}s, Structure valid ✅, Content generated ✅, Process steps: {process_count}, ID: {techcard_data.get('meta', {}).get('id')}",
                        {
                            'duration_seconds': duration,
                            'structure_checks': structure_checks,
                            'ingredients_count': ingredients_count,
                            'process_steps_count': process_count,
                            'yield_data': techcard_data.get('yield', {}),
                            'nutrition_data': techcard_data.get('nutrition', {}),
                            'cost_data': techcard_data.get('cost', {}),
                            'techcard_id': techcard_data.get('meta', {}).get('id')
                        },
                        duration
                    )
                    return True
                else:
                    missing_fields = [field for field, valid in structure_checks.items() if not valid]
                    issues = []
                    if missing_fields:
                        issues.append(f"Missing/invalid fields: {missing_fields}")
                    if not conversion_successful:
                        issues.append("Conversion not successful")
                    if not has_content:
                        issues.append("No content generated")
                    if not has_techcard_id:
                        issues.append("No techcard ID generated")
                    
                    self.log_test(
                        "V1→V2 Recipe Converter",
                        False,
                        f"V1→V2 conversion structure issues: {'; '.join(issues)}",
                        {
                            'duration_seconds': duration,
                            'structure_checks': structure_checks,
                            'ingredients_count': ingredients_count,
                            'process_steps_count': process_count,
                            'response': data
                        },
                        duration
                    )
                    return False
            else:
                self.log_test(
                    "V1→V2 Recipe Converter",
                    False,
                    f"V1→V2 converter API returned HTTP {response.status_code}. Duration: {duration:.1f}s",
                    response.text[:200],
                    duration
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
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all V1→V2 and V2 generation fix tests"""
        print("🚀 STARTING V1→V2 CONVERTER AND V2 GENERATION FIXES TESTING")
        print("=" * 70)
        print("ЗАДАЧА: Проверить оба критических исправления после изменений")
        print()
        print("ТЕСТ-КЕЙСЫ:")
        print("1. V2 основная генерация - /api/v1/techcards.v2/generate")
        print("   - Название: 'Стейк', user_id: 'demo_user'")
        print("   - Timeout: должен быть в пределах 90 секунд")
        print()
        print("2. V1→V2 конвертер - /api/v1/convert-recipe-to-techcard")
        print("   - recipe_content: 'Простой тестовый рецепт для конвертации'")
        print("   - recipe_name: 'Тест V1→V2', user_id: 'demo_user'")
        print("   - Проверить структуру: ingredients[], process[], yield{}, nutrition{}, cost{}")
        print()
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
        print("🎯 V1→V2 AND V2 GENERATION FIXES TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            duration_str = f" ({result['duration_seconds']:.1f}s)" if result.get('duration_seconds') else ""
            print(f"{status} {result['test_name']}{duration_str}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 V1→V2 AND V2 GENERATION FIXES: FULLY OPERATIONAL")
            print("✅ Исправления решили проблемы таймаута и структуры данных")
        elif success_rate >= 66:
            print("⚠️ V1→V2 AND V2 GENERATION FIXES: PARTIALLY WORKING")
            print("⚠️ Некоторые исправления требуют дополнительной работы")
        else:
            print("🚨 V1→V2 AND V2 GENERATION FIXES: CRITICAL ISSUES")
            print("❌ Исправления не решили основные проблемы")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results
        }

def main():
    """Main test execution"""
    print("V1→V2 Converter and V2 Generation Fixes Testing")
    print("Тестировать исправления V1→V2 и V2 генерации")
    print()
    
    tester = V1V2FixesTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] == 100:
        sys.exit(0)  # Complete success
    elif results['success_rate'] >= 66:
        sys.exit(1)  # Partial success but issues remain
    else:
        sys.exit(2)  # Critical failures

if __name__ == "__main__":
    main()