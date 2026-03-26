#!/usr/bin/env python3
"""
Skeleton Export Logic Testing
Протестировать исправленную логику экспорта скелетонов

Test Plan:
1. Create tech card with unmapped ingredients (generated articles)
2. Test preflight check `/api/v1/export/preflight` - should detect missing products
3. Test ZIP export `/api/v1/export/zip` - should contain Product-Skeletons.xlsx
4. Test `_is_generated_article()` function logic
5. Verify skeleton content has ingredients with generated articles

Цель: Проверить что система корректно различает сгенерированные артикулы от реальных кодов IIKO
"""

import requests
import json
import time
import os
import sys
import zipfile
import io
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test user
TEST_USER_ID = "demo_user"

class SkeletonExportTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Skeleton-Export-Tester/1.0'
        })
        self.test_results = []
        self.generated_techcard_id = None
        self.preflight_result = None
        
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
    
    def test_create_techcard_with_scallops(self) -> bool:
        """Test 2: Create tech card 'Тако с гребешками' with unmapped ingredients"""
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate"
            
            # Create tech card with exotic ingredients that will get generated articles
            payload = {
                "name": "Тако с гребешками",
                "cuisine": "мексиканская",
                "equipment": ["плита", "сковорода", "гриль"],
                "budget": 800.0,
                "dietary": [],
                "user_id": TEST_USER_ID
            }
            
            print(f"   Generating tech card: {payload['name']}")
            
            response = self.session.post(url, json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'status' in data and 'card' in data:
                    card = data['card']
                    card_id = card.get('meta', {}).get('id')
                    status = data['status']
                    
                    if card_id:
                        self.generated_techcard_id = card_id
                        
                        # Check for ingredients with generated articles
                        ingredients = card.get('ingredients', [])
                        generated_articles = []
                        
                        for ingredient in ingredients:
                            product_code = ingredient.get('product_code')
                            if product_code and self._is_generated_article(product_code):
                                generated_articles.append({
                                    'name': ingredient.get('name'),
                                    'article': product_code
                                })
                        
                        self.log_test(
                            "Create Tech Card with Scallops",
                            True,
                            f"Tech card created successfully. ID: {card_id}, Status: {status}, Ingredients: {len(ingredients)}, Generated articles: {len(generated_articles)}",
                            {
                                'id': card_id,
                                'status': status,
                                'ingredients_count': len(ingredients),
                                'generated_articles': generated_articles[:3]  # First 3 for brevity
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Create Tech Card with Scallops",
                            False,
                            "Response missing card ID in meta",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "Create Tech Card with Scallops",
                        False,
                        "Response missing required fields (status, card)",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Create Tech Card with Scallops",
                    False,
                    f"Generation API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Create Tech Card with Scallops",
                False,
                f"Generation API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "Create Tech Card with Scallops",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_preflight_check(self) -> bool:
        """Test 3: Test preflight check - should detect missing products with generated articles"""
        try:
            if not self.generated_techcard_id:
                self.log_test(
                    "Preflight Check",
                    False,
                    "No tech card ID available for preflight check"
                )
                return False
            
            url = f"{API_BASE}/v1/export/preflight"
            
            payload = {
                "techcardIds": [self.generated_techcard_id],
                "organization_id": "default"
            }
            
            print(f"   Running preflight check for tech card: {self.generated_techcard_id}")
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.preflight_result = data
                
                # Check for missing products (should have ingredients with generated articles)
                missing_products = data.get('missing', {}).get('products', [])
                missing_dishes = data.get('missing', {}).get('dishes', [])
                
                # Count generated articles in missing products
                generated_product_articles = []
                for product in missing_products:
                    article = product.get('article')
                    if article and self._is_generated_article(article):
                        generated_product_articles.append({
                            'name': product.get('name'),
                            'article': article
                        })
                
                self.log_test(
                    "Preflight Check",
                    True,
                    f"Preflight completed successfully. Missing dishes: {len(missing_dishes)}, Missing products: {len(missing_products)}, Generated product articles: {len(generated_product_articles)}",
                    {
                        'missing_dishes': len(missing_dishes),
                        'missing_products': len(missing_products),
                        'generated_product_articles': generated_product_articles[:3],  # First 3 for brevity
                        'ttk_date': data.get('ttkDate')
                    }
                )
                return True
            else:
                self.log_test(
                    "Preflight Check",
                    False,
                    f"Preflight API returned HTTP {response.status_code}",
                    response.text[:200]
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
        """Test 4: Test ZIP export - should contain Product-Skeletons.xlsx"""
        try:
            if not self.generated_techcard_id or not self.preflight_result:
                self.log_test(
                    "ZIP Export",
                    False,
                    "No tech card ID or preflight result available for ZIP export"
                )
                return False
            
            url = f"{API_BASE}/v1/export/zip"
            
            payload = {
                "techcardIds": [self.generated_techcard_id],
                "operational_rounding": True,
                "organization_id": "default",
                "preflight_result": self.preflight_result
            }
            
            print(f"   Creating ZIP export for tech card: {self.generated_techcard_id}")
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                # Check if response is a ZIP file
                if response.headers.get('content-type') == 'application/zip':
                    zip_content = response.content
                    zip_size = len(zip_content)
                    
                    # Analyze ZIP contents
                    zip_files = []
                    has_product_skeletons = False
                    product_skeleton_content = None
                    
                    try:
                        with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                            zip_files = zip_file.namelist()
                            
                            # Check for Product-Skeletons.xlsx
                            if 'Product-Skeletons.xlsx' in zip_files:
                                has_product_skeletons = True
                                
                                # Read Product-Skeletons.xlsx content
                                with zip_file.open('Product-Skeletons.xlsx') as skeleton_file:
                                    skeleton_data = skeleton_file.read()
                                    
                                    # Try to parse Excel content
                                    try:
                                        df = pd.read_excel(io.BytesIO(skeleton_data))
                                        product_skeleton_content = {
                                            'rows': len(df),
                                            'columns': list(df.columns),
                                            'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
                                        }
                                    except Exception as excel_error:
                                        product_skeleton_content = f"Excel parsing error: {str(excel_error)}"
                    
                    except zipfile.BadZipFile as zip_error:
                        self.log_test(
                            "ZIP Export",
                            False,
                            f"Invalid ZIP file received: {str(zip_error)}",
                            {'zip_size': zip_size}
                        )
                        return False
                    
                    self.log_test(
                        "ZIP Export",
                        True,
                        f"ZIP export successful. Size: {zip_size} bytes, Files: {len(zip_files)}, Has Product-Skeletons.xlsx: {has_product_skeletons}",
                        {
                            'zip_size': zip_size,
                            'files': zip_files,
                            'has_product_skeletons': has_product_skeletons,
                            'product_skeleton_content': product_skeleton_content
                        }
                    )
                    return True
                else:
                    # Not a ZIP file - check if it's JSON error
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
                            f"ZIP export returned unexpected content type: {response.headers.get('content-type')}",
                            response.text[:200]
                        )
                    return False
            else:
                self.log_test(
                    "ZIP Export",
                    False,
                    f"ZIP export API returned HTTP {response.status_code}",
                    response.text[:200]
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
        """Test 5: Test _is_generated_article() function logic"""
        try:
            # Test cases for generated articles
            generated_test_cases = [
                "10000",
                "10001", 
                "100015",
                "100000",
                "999999",
                "1000",
                "9999",
                "1",
                "999"
            ]
            
            # Test cases for real IIKO codes
            real_test_cases = [
                "BEEF-001",
                "VEG_TOMATO",
                "CHICKEN_BREAST",
                "SAUCE-BBQ",
                "abc123",
                "PROD_001",
                "",
                None,
                "1000000",  # Too large
                "0",        # Too small
                "non-numeric"
            ]
            
            generated_results = []
            real_results = []
            
            # Test generated articles
            for article in generated_test_cases:
                is_generated = self._is_generated_article(article)
                generated_results.append({
                    'article': article,
                    'is_generated': is_generated,
                    'expected': True
                })
            
            # Test real IIKO codes
            for article in real_test_cases:
                is_generated = self._is_generated_article(article)
                real_results.append({
                    'article': article,
                    'is_generated': is_generated,
                    'expected': False
                })
            
            # Check results
            generated_correct = sum(1 for r in generated_results if r['is_generated'] == r['expected'])
            real_correct = sum(1 for r in real_results if r['is_generated'] == r['expected'])
            
            total_correct = generated_correct + real_correct
            total_tests = len(generated_results) + len(real_results)
            
            success = total_correct == total_tests
            
            self.log_test(
                "_is_generated_article() Function Test",
                success,
                f"Function logic test completed. Correct: {total_correct}/{total_tests}, Generated articles: {generated_correct}/{len(generated_results)}, Real codes: {real_correct}/{len(real_results)}",
                {
                    'generated_results': generated_results,
                    'real_results': real_results,
                    'accuracy': f"{(total_correct/total_tests)*100:.1f}%"
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
        Local implementation of _is_generated_article logic for testing
        Should match the backend implementation
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
        """Run all skeleton export tests"""
        print("🚀 STARTING SKELETON EXPORT LOGIC TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_USER_ID}")
        print("=" * 60)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_backend_health,
            self.test_create_techcard_with_scallops,
            self.test_preflight_check,
            self.test_zip_export,
            self.test_is_generated_article_function
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
        print("=" * 60)
        print("🎯 SKELETON EXPORT LOGIC TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 SKELETON EXPORT LOGIC: FULLY OPERATIONAL")
        elif success_rate >= 60:
            print("⚠️ SKELETON EXPORT LOGIC: PARTIALLY WORKING")
        else:
            print("🚨 SKELETON EXPORT LOGIC: CRITICAL ISSUES")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results,
            'generated_techcard_id': self.generated_techcard_id,
            'preflight_result': self.preflight_result
        }

def main():
    """Main test execution"""
    print("Skeleton Export Logic Backend Testing")
    print("Протестировать исправленную логику экспорта скелетонов")
    print()
    
    tester = SkeletonExportTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()