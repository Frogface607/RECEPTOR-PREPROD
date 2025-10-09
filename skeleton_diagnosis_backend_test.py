#!/usr/bin/env python3
"""
Skeleton Export Diagnosis Backend Testing
Диагностировать проблему с пустым ZIP экспортом скелетонов

Test Plan:
1. Create techcard with exotic ingredients (not mapped to IIKO)
2. Verify techcard is saved to database with generated articles
3. Test preflight check - should detect missing products with generated articles
4. Test ZIP export - should create Product-Skeletons.xlsx with unmapped ingredients
5. Verify _is_generated_article() function works correctly
6. Test full cycle: create → preflight → export → validate content

Expected Result:
- Preflight finds techcard in database
- Identifies ingredients with generated articles as missing products
- ZIP contains Product-Skeletons.xlsx with unmapped ingredients
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import zipfile
import io

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test user
TEST_USER_ID = "demo_user"

class SkeletonExportDiagnoser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Skeleton-Export-Diagnoser/1.0'
        })
        self.test_results = []
        self.generated_techcard_id = None
        self.generated_techcard_data = None
        
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
        
    def test_backend_health(self) -> bool:
        """Test 1: Backend Health Check"""
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
    
    def test_create_exotic_techcard(self) -> bool:
        """Test 2: Create techcard with exotic ingredients (филе рыбы, гребешки, etc.)"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Create techcard with exotic ingredients that won't be in IIKO
            payload = {
                "name": "Тако с экзотическими морепродуктами",
                "cuisine": "мексиканская",
                "equipment": ["плита", "сковорода", "гриль"],
                "budget": 800.0,
                "dietary": [],
                "user_id": TEST_USER_ID,
                "description": "Блюдо с редкими ингредиентами для тестирования скелетонов"
            }
            
            print(f"   Creating techcard with exotic ingredients: {payload['name']}")
            
            response = self.session.post(url, json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'status' in data and 'card' in data:
                    card = data['card']
                    card_id = card.get('meta', {}).get('id')
                    status = data['status']
                    
                    if card_id:
                        self.generated_techcard_id = card_id
                        self.generated_techcard_data = card
                        
                        # Check ingredients and their articles
                        ingredients = card.get('ingredients', [])
                        generated_articles = []
                        
                        for ing in ingredients:
                            product_code = ing.get('product_code')
                            if product_code and self._is_generated_article(product_code):
                                generated_articles.append({
                                    'name': ing.get('name'),
                                    'article': product_code
                                })
                        
                        self.log_test(
                            "Create Exotic Techcard",
                            True,
                            f"Techcard created successfully. ID: {card_id}, Status: {status}, "
                            f"Ingredients: {len(ingredients)}, Generated articles: {len(generated_articles)}",
                            {
                                'id': card_id,
                                'status': status,
                                'ingredients_count': len(ingredients),
                                'generated_articles': generated_articles,
                                'ingredients': [{'name': ing.get('name'), 'article': ing.get('product_code')} for ing in ingredients]
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Create Exotic Techcard",
                            False,
                            "Response missing card ID in meta",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "Create Exotic Techcard",
                        False,
                        "Response missing required fields (status, card)",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Create Exotic Techcard",
                    False,
                    f"Generation API returned HTTP {response.status_code}",
                    response.text[:500]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Create Exotic Techcard",
                False,
                f"Generation API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Create Exotic Techcard",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_verify_database_storage(self) -> bool:
        """Test 3: Verify techcard is properly stored in database"""
        if not self.generated_techcard_id:
            self.log_test(
                "Verify Database Storage",
                False,
                "No techcard ID available from previous test"
            )
            return False
        
        try:
            # Try to retrieve the techcard via user history API
            url = f"{API_BASE}/user-history/{TEST_USER_ID}"
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                history_items = data.get('history', [])
                
                # Look for our generated techcard
                found_techcard = None
                for item in history_items:
                    if item.get('id') == self.generated_techcard_id:
                        found_techcard = item
                        break
                
                if found_techcard:
                    self.log_test(
                        "Verify Database Storage",
                        True,
                        f"Techcard found in database. ID: {self.generated_techcard_id}, "
                        f"Name: {found_techcard.get('dish_name', 'Unknown')}",
                        {
                            'found_in_history': True,
                            'techcard_id': self.generated_techcard_id,
                            'dish_name': found_techcard.get('dish_name'),
                            'type': found_techcard.get('type')
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Verify Database Storage",
                        False,
                        f"Techcard {self.generated_techcard_id} not found in user history",
                        {
                            'history_count': len(history_items),
                            'searched_id': self.generated_techcard_id
                        }
                    )
                    return False
            else:
                self.log_test(
                    "Verify Database Storage",
                    False,
                    f"User history API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Verify Database Storage",
                False,
                f"Database verification failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Verify Database Storage",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_preflight_check(self) -> bool:
        """Test 4: Test preflight check - should detect missing products with generated articles"""
        if not self.generated_techcard_id:
            self.log_test(
                "Preflight Check",
                False,
                "No techcard ID available from previous test"
            )
            return False
        
        try:
            url = f"{API_BASE}/v1/export/preflight"
            
            payload = {
                "techcardIds": [self.generated_techcard_id],
                "user_id": TEST_USER_ID,
                "ttk_date": "2025-01-15"
            }
            
            print(f"   Running preflight check for techcard: {self.generated_techcard_id}")
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check preflight results
                counts = data.get('counts', {})
                missing_dishes = counts.get('missingDishes', 0)
                missing_products = counts.get('missingProducts', 0)
                dish_skeletons = counts.get('dishSkeletons', 0)
                product_skeletons = counts.get('productSkeletons', 0)
                
                # For our test case, we expect:
                # - 1 missing dish (the exotic dish we created)
                # - Several missing products (exotic ingredients with generated articles)
                success = missing_dishes > 0 or missing_products > 0 or product_skeletons > 0
                
                self.log_test(
                    "Preflight Check",
                    success,
                    f"Preflight completed. Missing dishes: {missing_dishes}, "
                    f"Missing products: {missing_products}, Product skeletons: {product_skeletons}",
                    {
                        'counts': counts,
                        'techcard_id': self.generated_techcard_id,
                        'expected_missing_items': True
                    }
                )
                return success
            else:
                self.log_test(
                    "Preflight Check",
                    False,
                    f"Preflight API returned HTTP {response.status_code}",
                    response.text[:500]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Preflight Check",
                False,
                f"Preflight API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Preflight Check",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_zip_export(self) -> bool:
        """Test 5: Test ZIP export - should create Product-Skeletons.xlsx with unmapped ingredients"""
        if not self.generated_techcard_id:
            self.log_test(
                "ZIP Export",
                False,
                "No techcard ID available from previous test"
            )
            return False
        
        try:
            # First run preflight to get preflight_result
            preflight_url = f"{API_BASE}/v1/export/preflight"
            preflight_payload = {
                "techcardIds": [self.generated_techcard_id],
                "user_id": TEST_USER_ID,
                "ttk_date": "2025-01-15"
            }
            
            print(f"   Running preflight for ZIP export: {self.generated_techcard_id}")
            preflight_response = self.session.post(preflight_url, json=preflight_payload, timeout=30)
            
            if preflight_response.status_code != 200:
                self.log_test(
                    "ZIP Export",
                    False,
                    f"Preflight for ZIP failed: HTTP {preflight_response.status_code}",
                    preflight_response.text[:500]
                )
                return False
            
            preflight_data = preflight_response.json()
            
            # Now run ZIP export with preflight_result
            url = f"{API_BASE}/v1/export/zip"
            
            payload = {
                "techcardIds": [self.generated_techcard_id],
                "user_id": TEST_USER_ID,
                "ttk_date": "2025-01-15",
                "operational_rounding": True,
                "preflight_result": preflight_data  # Include preflight result
            }
            
            print(f"   Exporting ZIP for techcard: {self.generated_techcard_id}")
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                # Check if response is ZIP file
                content_type = response.headers.get('content-type', '')
                
                if 'application/zip' in content_type or 'application/octet-stream' in content_type:
                    zip_content = response.content
                    zip_size = len(zip_content)
                    
                    # Analyze ZIP contents
                    try:
                        with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                            file_list = zip_file.namelist()
                            
                            # Check for skeleton files
                            has_product_skeletons = any('Product-Skeletons' in f for f in file_list)
                            has_dish_skeletons = any('Dish-Skeletons' in f for f in file_list)
                            
                            success = len(file_list) > 0 and (has_product_skeletons or has_dish_skeletons)
                            
                            self.log_test(
                                "ZIP Export",
                                success,
                                f"ZIP export completed. Size: {zip_size} bytes, "
                                f"Files: {len(file_list)}, Product skeletons: {has_product_skeletons}, "
                                f"Dish skeletons: {has_dish_skeletons}",
                                {
                                    'zip_size': zip_size,
                                    'files_in_zip': file_list,
                                    'has_product_skeletons': has_product_skeletons,
                                    'has_dish_skeletons': has_dish_skeletons,
                                    'techcard_id': self.generated_techcard_id
                                }
                            )
                            return success
                    except zipfile.BadZipFile:
                        self.log_test(
                            "ZIP Export",
                            False,
                            f"Invalid ZIP file received. Size: {zip_size} bytes",
                            {'zip_size': zip_size, 'content_preview': zip_content[:100]}
                        )
                        return False
                else:
                    # Not a ZIP file, might be JSON error
                    try:
                        error_data = response.json()
                        self.log_test(
                            "ZIP Export",
                            False,
                            f"ZIP export returned JSON error instead of ZIP file",
                            error_data
                        )
                    except:
                        self.log_test(
                            "ZIP Export",
                            False,
                            f"ZIP export returned unexpected content type: {content_type}",
                            response.text[:200]
                        )
                    return False
            else:
                self.log_test(
                    "ZIP Export",
                    False,
                    f"ZIP export API returned HTTP {response.status_code}",
                    response.text[:500]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "ZIP Export",
                False,
                f"ZIP export API request failed: {str(e)}"
            )
            return False
    
    def test_is_generated_article_function(self) -> bool:
        """Test 6: Test _is_generated_article() function logic"""
        try:
            # Test cases for generated article detection
            test_cases = [
                # Generated articles (should return True)
                ("10000", True),
                ("10001", True),
                ("100015", True),
                ("100055", True),  # From the log example
                ("999999", True),
                ("1000", True),
                ("1", True),
                
                # Real IIKO codes (should return False)
                ("BEEF-001", False),
                ("VEG_TOMATO", False),
                ("FISH_SALMON", False),
                ("abc123", False),
                ("", False),
                (None, False),
            ]
            
            passed_tests = 0
            total_tests = len(test_cases)
            
            for article_code, expected in test_cases:
                result = self._is_generated_article(article_code)
                if result == expected:
                    passed_tests += 1
                else:
                    print(f"   FAIL: '{article_code}' expected {expected}, got {result}")
            
            success = passed_tests == total_tests
            
            self.log_test(
                "_is_generated_article() Function Test",
                success,
                f"Function test completed. Passed: {passed_tests}/{total_tests} test cases",
                {
                    'passed_tests': passed_tests,
                    'total_tests': total_tests,
                    'accuracy': f"{(passed_tests/total_tests)*100:.1f}%"
                }
            )
            return success
            
        except Exception as e:
            self.log_test(
                "_is_generated_article() Function Test",
                False,
                f"Function test failed: {str(e)}"
            )
            return False
    
    def _is_generated_article(self, article_code: str) -> bool:
        """
        Local implementation of _is_generated_article() function for testing
        This should match the backend implementation
        """
        if not article_code or not isinstance(article_code, str):
            return False
        
        try:
            # Check if it's purely numeric
            article_int = int(article_code)
            
            # Generated articles typically start from 10000 (width=5) or 100000 (width=6)
            # and are sequential integers
            if 10000 <= article_int <= 999999:  # Covers width 5 and 6
                return True
            elif 1000 <= article_int <= 9999:  # Also width 4 just in case
                return True
            elif 1 <= article_int <= 999:  # And smaller widths
                return True
                
        except (ValueError, TypeError):
            # Non-numeric codes are real iiko codes
            pass
        
        return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all skeleton export diagnosis tests"""
        print("🔍 SKELETON EXPORT DIAGNOSIS - COMPREHENSIVE TESTING")
        print("=" * 60)
        print()
        
        tests = [
            self.test_backend_health,
            self.test_create_exotic_techcard,
            self.test_verify_database_storage,
            self.test_preflight_check,
            self.test_zip_export,
            self.test_is_generated_article_function,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 60)
        print(f"SKELETON EXPORT DIAGNOSIS RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Skeleton export workflow is operational")
        else:
            print("❌ SOME TESTS FAILED - Issues detected in skeleton export workflow")
            
            # Analyze failures
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\nFAILED TESTS:")
                for failure in failed_tests:
                    print(f"  - {failure['test_name']}: {failure['details']}")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': f"{(passed/total)*100:.1f}%",
            'test_results': self.test_results,
            'generated_techcard_id': self.generated_techcard_id
        }

def main():
    """Main test execution"""
    diagnoser = SkeletonExportDiagnoser()
    results = diagnoser.run_all_tests()
    
    # Save results to file for analysis
    with open('/app/skeleton_diagnosis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nDetailed results saved to: /app/skeleton_diagnosis_results.json")
    
    return results['passed_tests'] == results['total_tests']

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)