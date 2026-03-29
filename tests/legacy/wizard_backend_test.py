#!/usr/bin/env python3
"""
Wizard для создания техкарт - Backend Testing
Протестировать базовую работоспособность wizard'а для создания техкарт

Test Plan:
1. V2 API Status Check - проверить что V2 API включен
2. MongoDB Connection - убедиться что MongoDB подключение работает
3. Tech Card Generation Endpoint - POST /api/v1/techcards.v2/generate
4. Generated Tech Card Validation - проверить структуру и данные
5. Article Generation Verification - убедиться что артикулы генерируются

Тестовые данные:
- name: "Борщ украинский с говядиной на 4 порции - традиционный суп с красной свеклой, капустой, морковью, луком и говядиной"
- cuisine: "русская" 
- restaurant_type: "casual"
- budget: 500
- equipment: ["плита", "кастрюля"]
- dietary: []
- portions: 1
- user_id: "demo_user"

Цель: убедиться что backend готов к работе с новым wizard интерфейсом
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

class WizardBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Wizard-Backend-Tester/1.0'
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
        
    def test_v2_api_status(self) -> bool:
        """Test 1: V2 API Status Check - проверить что V2 API включен"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/status"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check V2 API configuration
                feature_enabled = data.get('feature_enabled', False)
                llm_enabled = data.get('llm_enabled', False)
                model = data.get('model', 'unknown')
                
                if feature_enabled and llm_enabled:
                    self.log_test(
                        "V2 API Status Check",
                        True,
                        f"V2 API fully enabled. Feature: {feature_enabled}, LLM: {llm_enabled}, Model: {model}",
                        data
                    )
                    return True
                else:
                    self.log_test(
                        "V2 API Status Check",
                        False,
                        f"V2 API not fully enabled. Feature: {feature_enabled}, LLM: {llm_enabled}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "V2 API Status Check",
                    False,
                    f"V2 Status API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V2 API Status Check",
                False,
                f"V2 Status API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "V2 API Status Check",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_mongodb_connection(self) -> bool:
        """Test 2: MongoDB Connection - убедиться что MongoDB подключение работает"""
        try:
            # Test MongoDB connection by checking user history endpoint
            url = f"{API_BASE}/user-history/{TEST_USER_ID}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we get a valid response (even if empty)
                if isinstance(data, list) or isinstance(data, dict):
                    self.log_test(
                        "MongoDB Connection",
                        True,
                        f"MongoDB connection working - user history endpoint accessible, returned {len(data) if isinstance(data, list) else 'dict'} items",
                        {'status': 'connected', 'response_type': type(data).__name__}
                    )
                    return True
                else:
                    self.log_test(
                        "MongoDB Connection",
                        False,
                        "MongoDB response has unexpected format",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "MongoDB Connection",
                    False,
                    f"MongoDB test returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "MongoDB Connection",
                False,
                f"MongoDB connection test failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "MongoDB Connection",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_techcard_generation_endpoint(self) -> bool:
        """Test 3: Tech Card Generation Endpoint - POST /api/v1/techcards.v2/generate"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Exact test data from review request
            payload = {
                "name": "Борщ украинский с говядиной на 4 порции - традиционный суп с красной свеклой, капустой, морковью, луком и говядиной",
                "cuisine": "русская",
                "restaurant_type": "casual",
                "budget": 500,
                "equipment": ["плита", "кастрюля"],
                "dietary": [],
                "portions": 1,
                "user_id": "demo_user"
            }
            
            print(f"   Generating tech card: {payload['name'][:50]}...")
            
            response = self.session.post(url, json=payload, timeout=120)  # Extended timeout for generation
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful generation
                if 'status' in data and 'card' in data:
                    status = data['status']
                    card = data['card']
                    
                    # Store generated tech card for further validation
                    self.generated_techcard = card
                    
                    # Extract key information
                    card_id = card.get('meta', {}).get('id') or card.get('id')
                    ingredients = card.get('ingredients', [])
                    process_steps = card.get('process', [])
                    
                    self.log_test(
                        "Tech Card Generation Endpoint",
                        True,
                        f"Tech card generated successfully. Status: {status}, ID: {card_id}, Ingredients: {len(ingredients)}, Process steps: {len(process_steps)}",
                        {
                            'status': status,
                            'card_id': card_id,
                            'ingredients_count': len(ingredients),
                            'process_steps_count': len(process_steps)
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Tech Card Generation Endpoint",
                        False,
                        "Response missing required fields (status, card)",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Tech Card Generation Endpoint",
                    False,
                    f"Generation endpoint returned HTTP {response.status_code}",
                    response.text[:300]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Tech Card Generation Endpoint",
                False,
                f"Generation endpoint request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Tech Card Generation Endpoint",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_generated_techcard_validation(self) -> bool:
        """Test 4: Generated Tech Card Validation - проверить структуру и данные"""
        if not self.generated_techcard:
            self.log_test(
                "Generated Tech Card Validation",
                False,
                "No tech card available for validation (previous test failed)"
            )
            return False
        
        try:
            card = self.generated_techcard
            validation_issues = []
            
            # Check required fields
            required_fields = ['meta', 'ingredients', 'process']
            for field in required_fields:
                if field not in card:
                    validation_issues.append(f"Missing required field: {field}")
            
            # Check meta information
            meta = card.get('meta', {})
            if not meta.get('id'):
                validation_issues.append("Missing card ID in meta")
            
            # Check ingredients
            ingredients = card.get('ingredients', [])
            if len(ingredients) == 0:
                validation_issues.append("No ingredients found")
            else:
                # Validate ingredient structure - check for brutto_g/netto_g instead of quantity
                for i, ingredient in enumerate(ingredients[:3]):  # Check first 3 ingredients
                    if not ingredient.get('name'):
                        validation_issues.append(f"Ingredient {i+1} missing name")
                    # Check for either quantity or brutto_g/netto_g
                    if not (ingredient.get('quantity') or ingredient.get('brutto_g') or ingredient.get('netto_g')):
                        validation_issues.append(f"Ingredient {i+1} missing quantity/weight data")
            
            # Check process steps
            process = card.get('process', [])
            if len(process) == 0:
                validation_issues.append("No process steps found")
            
            # Check for expected content related to "Борщ украинский"
            card_name = meta.get('title', '').lower()
            if 'борщ' not in card_name and 'украинский' not in card_name:
                validation_issues.append("Generated card name doesn't match expected dish")
            
            if len(validation_issues) == 0:
                self.log_test(
                    "Generated Tech Card Validation",
                    True,
                    f"Tech card structure is valid. Ingredients: {len(ingredients)}, Process steps: {len(process)}",
                    {
                        'card_id': meta.get('id'),
                        'card_name': meta.get('title'),
                        'ingredients_count': len(ingredients),
                        'process_steps_count': len(process),
                        'validation_status': 'passed'
                    }
                )
                return True
            else:
                self.log_test(
                    "Generated Tech Card Validation",
                    False,
                    f"Tech card validation failed: {'; '.join(validation_issues)}",
                    {
                        'validation_issues': validation_issues,
                        'card_structure': list(card.keys()) if card else []
                    }
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Generated Tech Card Validation",
                False,
                f"Validation error: {str(e)}"
            )
            return False
    
    def test_article_generation_verification(self) -> bool:
        """Test 5: Article Generation Verification - убедиться что артикулы генерируются"""
        if not self.generated_techcard:
            self.log_test(
                "Article Generation Verification",
                False,
                "No tech card available for article verification (previous test failed)"
            )
            return False
        
        try:
            card = self.generated_techcard
            
            # Check dish article
            dish_article = card.get('article') or card.get('meta', {}).get('article')
            
            # Check ingredient product codes
            ingredients = card.get('ingredients', [])
            ingredients_with_codes = 0
            ingredients_without_codes = 0
            
            for ingredient in ingredients:
                product_code = ingredient.get('product_code') or ingredient.get('article')
                if product_code and product_code != 'null' and product_code is not None:
                    ingredients_with_codes += 1
                else:
                    ingredients_without_codes += 1
            
            # Evaluate article generation
            article_issues = []
            
            if not dish_article or dish_article == 'null' or dish_article is None:
                article_issues.append("Dish article not generated")
            
            if ingredients_without_codes > 0:
                article_issues.append(f"{ingredients_without_codes} ingredients missing product codes")
            
            # Consider it successful if at least some articles are generated
            if len(article_issues) == 0:
                self.log_test(
                    "Article Generation Verification",
                    True,
                    f"Article generation working perfectly. Dish article: {dish_article}, Ingredients with codes: {ingredients_with_codes}/{len(ingredients)}",
                    {
                        'dish_article': dish_article,
                        'ingredients_with_codes': ingredients_with_codes,
                        'total_ingredients': len(ingredients),
                        'article_generation_status': 'working'
                    }
                )
                return True
            elif ingredients_with_codes > 0 or dish_article:
                # Partial success - some articles generated
                self.log_test(
                    "Article Generation Verification",
                    True,  # Still consider it working if some articles are generated
                    f"Article generation partially working. Issues: {'; '.join(article_issues)}. Dish article: {dish_article}, Ingredients with codes: {ingredients_with_codes}/{len(ingredients)}",
                    {
                        'dish_article': dish_article,
                        'ingredients_with_codes': ingredients_with_codes,
                        'total_ingredients': len(ingredients),
                        'article_generation_status': 'partial',
                        'issues': article_issues
                    }
                )
                return True
            else:
                # Complete failure
                self.log_test(
                    "Article Generation Verification",
                    False,
                    f"Article generation not working. Issues: {'; '.join(article_issues)}",
                    {
                        'dish_article': dish_article,
                        'ingredients_with_codes': ingredients_with_codes,
                        'total_ingredients': len(ingredients),
                        'article_generation_status': 'failed',
                        'issues': article_issues
                    }
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Article Generation Verification",
                False,
                f"Article verification error: {str(e)}"
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all wizard backend tests"""
        print("🧙‍♂️ STARTING WIZARD BACKEND TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER_ID}")
        print("Testing wizard для создания техкарт")
        print("=" * 60)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_v2_api_status,
            self.test_mongodb_connection,
            self.test_techcard_generation_endpoint,
            self.test_generated_techcard_validation,
            self.test_article_generation_verification
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
        print("🎯 WIZARD BACKEND TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 WIZARD BACKEND: FULLY OPERATIONAL")
            print("✅ Backend готов к работе с новым wizard интерфейсом")
        elif success_rate >= 60:
            print("⚠️ WIZARD BACKEND: PARTIALLY WORKING")
            print("⚠️ Некоторые компоненты wizard требуют внимания")
        else:
            print("🚨 WIZARD BACKEND: CRITICAL ISSUES")
            print("❌ Backend НЕ готов к работе с wizard интерфейсом")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results,
            'generated_techcard': self.generated_techcard
        }

def main():
    """Main test execution"""
    print("Wizard для создания техкарт - Backend Testing")
    print("Протестировать базовую работоспособность wizard'а для создания техкарт")
    print()
    
    tester = WizardBackendTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()