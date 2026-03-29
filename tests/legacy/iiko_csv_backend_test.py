#!/usr/bin/env python3
"""
Backend Testing for iiko CSV Export Implementation
Testing iiko CSV export functionality as specified in review request
"""

import requests
import json
import sys
import os
import zipfile
import csv
import io
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

class IikoCsvExportTester:
    """Comprehensive tester for iiko CSV export functionality"""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.errors = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success:
            self.errors.append(f"{test_name}: {details}")
    
    def create_test_techcard(self, dish_name: str = "Говядина тушеная с овощами") -> Dict[str, Any]:
        """Create a test tech card for testing"""
        return {
            "meta": {
                "title": dish_name,
                "description": f"Тестовое блюдо {dish_name}",
                "category": "Горячие блюда"
            },
            "ingredients": [
                {
                    "name": "говядина",
                    "netto_g": 400,
                    "brutto_g": 450,
                    "loss_pct": 11.1,
                    "unit": "g",
                    "skuId": "CAT_BEEF_001",
                    "canonical_id": "beef_stew"
                },
                {
                    "name": "лук репчатый", 
                    "netto_g": 100,
                    "brutto_g": 120,
                    "loss_pct": 16.7,
                    "unit": "g",
                    "skuId": "CAT_ONION_001",
                    "canonical_id": "onion"
                },
                {
                    "name": "морковь",
                    "netto_g": 80,
                    "brutto_g": 100,
                    "loss_pct": 20.0,
                    "unit": "g",
                    "skuId": None,  # Missing SKU to test validation
                    "canonical_id": None
                },
                {
                    "name": "растительное масло",
                    "netto_g": 30,
                    "brutto_g": 30,
                    "loss_pct": 0.0,
                    "unit": "ml",
                    "skuId": "CAT_OIL_001",
                    "canonical_id": "vegetable_oil"
                },
                {
                    "name": "соль поваренная",
                    "netto_g": 8,
                    "brutto_g": 8,
                    "loss_pct": 0.0,
                    "unit": "g",
                    "skuId": "CAT_SALT_001",
                    "canonical_id": "salt"
                }
            ],
            "portions": 4,
            "yield": {
                "perPortion_g": 150,
                "perBatch_g": 600
            },
            "process": [
                {
                    "n": 1,
                    "action": "Подготовить ингредиенты",
                    "time_min": 10,
                    "temp_c": None
                },
                {
                    "n": 2,
                    "action": "Обжарить говядину",
                    "time_min": 15,
                    "temp_c": 180
                },
                {
                    "n": 3,
                    "action": "Добавить овощи и тушить",
                    "time_min": 25,
                    "temp_c": 160
                }
            ],
            "storage": {
                "conditions": "Холодильник +2...+6°C",
                "shelfLife_hours": 24
            },
            "cost": {
                "rawCost": 320.50,
                "costPerPortion": 80.12,
                "markup_pct": 300,
                "vat_pct": 20
            }
        }
    
    def test_csv_export_endpoint(self):
        """Test 1: New CSV Export Endpoint - POST /api/v1/techcards.v2/export/iiko.csv"""
        print("\n🔍 Testing CSV Export Endpoint...")
        
        try:
            url = f"{self.backend_url}/v1/techcards.v2/export/iiko.csv"
            test_card = self.create_test_techcard()
            
            response = requests.post(url, json=test_card, timeout=30)
            
            # Test 1.1: Endpoint exists and responds
            if response.status_code == 200:
                self.log_test("CSV Export - Endpoint Response", True, 
                             f"HTTP 200 - endpoint accessible")
                
                # Test 1.2: Returns ZIP file
                content_type = response.headers.get('content-type', '')
                if 'application/zip' in content_type:
                    self.log_test("CSV Export - ZIP Content Type", True, 
                                 f"Content-Type: {content_type}")
                else:
                    self.log_test("CSV Export - ZIP Content Type", False, 
                                 f"Expected application/zip, got: {content_type}")
                
                # Test 1.3: Content-Disposition header with filename
                content_disposition = response.headers.get('content-disposition', '')
                if 'attachment' in content_disposition and 'iiko_export_' in content_disposition and '.zip' in content_disposition:
                    self.log_test("CSV Export - Content Disposition", True, 
                                 f"Proper filename: {content_disposition}")
                else:
                    self.log_test("CSV Export - Content Disposition", False, 
                                 f"Invalid Content-Disposition: {content_disposition}")
                
                # Test 1.4: ZIP file is valid and contains expected files
                try:
                    zip_content = io.BytesIO(response.content)
                    with zipfile.ZipFile(zip_content, 'r') as zip_file:
                        file_list = zip_file.namelist()
                        
                        if 'products.csv' in file_list and 'recipes.csv' in file_list:
                            self.log_test("CSV Export - ZIP Contents", True, 
                                         f"Contains both files: {file_list}")
                            
                            # Store ZIP content for further testing
                            self.test_zip_content = zip_content
                            self.test_zip_files = zip_file
                            return True
                        else:
                            self.log_test("CSV Export - ZIP Contents", False, 
                                         f"Missing files. Found: {file_list}")
                            return False
                            
                except zipfile.BadZipFile:
                    self.log_test("CSV Export - ZIP Validity", False, 
                                 "Response is not a valid ZIP file")
                    return False
                    
            else:
                self.log_test("CSV Export - Endpoint Response", False, 
                             f"HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("CSV Export - Endpoint Test", False, f"Exception: {str(e)}")
            return False
    
    def test_csv_file_structure(self):
        """Test 2: CSV File Generation and Structure"""
        print("\n🔍 Testing CSV File Structure...")
        
        if not hasattr(self, 'test_zip_content'):
            self.log_test("CSV Structure - Prerequisites", False, "ZIP content not available from previous test")
            return False
        
        try:
            self.test_zip_content.seek(0)
            with zipfile.ZipFile(self.test_zip_content, 'r') as zip_file:
                
                # Test 2.1: Products.csv structure
                products_content = zip_file.read('products.csv')
                
                # Check UTF-8 BOM
                if products_content.startswith(b'\xef\xbb\xbf'):
                    self.log_test("Products CSV - UTF-8 BOM", True, "UTF-8 BOM present")
                    products_text = products_content[3:].decode('utf-8')  # Skip BOM
                else:
                    self.log_test("Products CSV - UTF-8 BOM", False, "UTF-8 BOM missing")
                    products_text = products_content.decode('utf-8')
                
                # Parse products CSV
                products_reader = csv.reader(io.StringIO(products_text), delimiter=';')
                products_rows = list(products_reader)
                
                if len(products_rows) > 0:
                    products_header = products_rows[0]
                    expected_products_header = ['sku', 'name', 'unit', 'price_per_unit', 'currency', 'vat_pct', 'category']
                    
                    if products_header == expected_products_header:
                        self.log_test("Products CSV - Header Structure", True, 
                                     f"Correct headers: {products_header}")
                    else:
                        self.log_test("Products CSV - Header Structure", False, 
                                     f"Expected: {expected_products_header}, Got: {products_header}")
                    
                    # Test semicolon delimiter
                    if ';' in products_content.decode('utf-8'):
                        self.log_test("Products CSV - Semicolon Delimiter", True, "Semicolon delimiter used")
                    else:
                        self.log_test("Products CSV - Semicolon Delimiter", False, "Semicolon delimiter not found")
                    
                    # Test data rows
                    if len(products_rows) > 1:
                        sample_row = products_rows[1]
                        if len(sample_row) == 7:  # Should have 7 columns
                            self.log_test("Products CSV - Data Row Structure", True, 
                                         f"Sample row: {sample_row}")
                            
                            # Test decimal format (should use dot separator)
                            price = sample_row[3]  # price_per_unit column
                            if '.' in price and ',' not in price:
                                self.log_test("Products CSV - Decimal Format", True, 
                                             f"Dot separator used: {price}")
                            else:
                                self.log_test("Products CSV - Decimal Format", False, 
                                             f"Invalid decimal format: {price}")
                        else:
                            self.log_test("Products CSV - Data Row Structure", False, 
                                         f"Expected 7 columns, got {len(sample_row)}")
                    else:
                        self.log_test("Products CSV - Data Rows", False, "No data rows found")
                else:
                    self.log_test("Products CSV - File Content", False, "Empty products.csv file")
                
                # Test 2.2: Recipes.csv structure
                recipes_content = zip_file.read('recipes.csv')
                
                # Check UTF-8 BOM
                if recipes_content.startswith(b'\xef\xbb\xbf'):
                    self.log_test("Recipes CSV - UTF-8 BOM", True, "UTF-8 BOM present")
                    recipes_text = recipes_content[3:].decode('utf-8')  # Skip BOM
                else:
                    self.log_test("Recipes CSV - UTF-8 BOM", False, "UTF-8 BOM missing")
                    recipes_text = recipes_content.decode('utf-8')
                
                # Parse recipes CSV
                recipes_reader = csv.reader(io.StringIO(recipes_text), delimiter=';')
                recipes_rows = list(recipes_reader)
                
                if len(recipes_rows) > 0:
                    recipes_header = recipes_rows[0]
                    expected_recipes_header = ['dish_code', 'dish_name', 'output_qty', 'output_unit', 'ingredient_sku', 'qty_net', 'loss_pct', 'unit']
                    
                    if recipes_header == expected_recipes_header:
                        self.log_test("Recipes CSV - Header Structure", True, 
                                     f"Correct headers: {recipes_header}")
                    else:
                        self.log_test("Recipes CSV - Header Structure", False, 
                                     f"Expected: {expected_recipes_header}, Got: {recipes_header}")
                    
                    # Test data rows
                    if len(recipes_rows) > 1:
                        sample_row = recipes_rows[1]
                        if len(sample_row) == 8:  # Should have 8 columns
                            self.log_test("Recipes CSV - Data Row Structure", True, 
                                         f"Sample row: {sample_row}")
                            
                            # Test dish_code generation
                            dish_code = sample_row[0]
                            if dish_code and len(dish_code) > 0:
                                self.log_test("Recipes CSV - Dish Code Generation", True, 
                                             f"Dish code: {dish_code}")
                            else:
                                self.log_test("Recipes CSV - Dish Code Generation", False, 
                                             "Empty dish code")
                        else:
                            self.log_test("Recipes CSV - Data Row Structure", False, 
                                         f"Expected 8 columns, got {len(sample_row)}")
                    else:
                        self.log_test("Recipes CSV - Data Rows", False, "No data rows found")
                else:
                    self.log_test("Recipes CSV - File Content", False, "Empty recipes.csv file")
                    
        except Exception as e:
            self.log_test("CSV Structure - Analysis", False, f"Exception: {str(e)}")
            return False
        
        return True
    
    def test_sku_validation_and_issues(self):
        """Test 3: SKU Validation and Issues Generation"""
        print("\n🔍 Testing SKU Validation and Issues...")
        
        try:
            # Create test card with missing SKUs
            test_card = self.create_test_techcard("Борщ классический")
            
            # Remove SKUs from some ingredients to test validation
            test_card["ingredients"][2]["skuId"] = None  # морковь
            test_card["ingredients"][2]["canonical_id"] = None
            
            # Add ingredient without any SKU
            test_card["ingredients"].append({
                "name": "свекла",
                "netto_g": 150,
                "brutto_g": 180,
                "loss_pct": 16.7,
                "unit": "g",
                "skuId": None,
                "canonical_id": None
            })
            
            url = f"{self.backend_url}/v1/techcards.v2/export/iiko.csv"
            response = requests.post(url, json=test_card, timeout=30)
            
            if response.status_code == 200:
                self.log_test("SKU Validation - Export Success", True, 
                             "Export completed despite missing SKUs")
                
                # Analyze ZIP content for generated SKUs
                zip_content = io.BytesIO(response.content)
                with zipfile.ZipFile(zip_content, 'r') as zip_file:
                    products_content = zip_file.read('products.csv')
                    products_text = products_content.decode('utf-8-sig')  # Handle BOM
                    
                    # Check for generated SKUs
                    if 'GENERATED_' in products_text:
                        self.log_test("SKU Validation - Generated SKUs", True, 
                                     "Generated SKUs found in products.csv")
                        
                        # Count generated SKUs
                        generated_count = products_text.count('GENERATED_')
                        if generated_count >= 2:  # Should have at least 2 (морковь, свекла)
                            self.log_test("SKU Validation - Generated Count", True, 
                                         f"Found {generated_count} generated SKUs")
                        else:
                            self.log_test("SKU Validation - Generated Count", False, 
                                         f"Expected ≥2 generated SKUs, found {generated_count}")
                    else:
                        self.log_test("SKU Validation - Generated SKUs", False, 
                                     "No generated SKUs found")
                
                # Test that export still works (non-blocking warnings)
                self.log_test("SKU Validation - Non-blocking", True, 
                             "Missing SKUs don't block export (warnings only)")
                
            else:
                self.log_test("SKU Validation - Export Failure", False, 
                             f"Export failed with missing SKUs: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("SKU Validation - Test", False, f"Exception: {str(e)}")
    
    def test_unit_normalization(self):
        """Test 4: Unit Normalization for iiko"""
        print("\n🔍 Testing Unit Normalization...")
        
        try:
            # Create test card with various units
            test_card = self.create_test_techcard("Тест единиц измерения")
            test_card["ingredients"] = [
                {
                    "name": "мука пшеничная",
                    "netto_g": 500,
                    "brutto_g": 500,
                    "loss_pct": 0.0,
                    "unit": "g",  # Should become 'г'
                    "skuId": "TEST_FLOUR"
                },
                {
                    "name": "молоко",
                    "netto_g": 250,
                    "brutto_g": 250,
                    "loss_pct": 0.0,
                    "unit": "ml",  # Should become 'мл'
                    "skuId": "TEST_MILK"
                },
                {
                    "name": "яйца",
                    "netto_g": 100,
                    "brutto_g": 100,
                    "loss_pct": 0.0,
                    "unit": "pcs",  # Should become 'шт'
                    "skuId": "TEST_EGGS"
                },
                {
                    "name": "сахар",
                    "netto_g": 1000,
                    "brutto_g": 1000,
                    "loss_pct": 0.0,
                    "unit": "kg",  # Should become 'кг'
                    "skuId": "TEST_SUGAR"
                }
            ]
            
            url = f"{self.backend_url}/v1/techcards.v2/export/iiko.csv"
            response = requests.post(url, json=test_card, timeout=30)
            
            if response.status_code == 200:
                zip_content = io.BytesIO(response.content)
                with zipfile.ZipFile(zip_content, 'r') as zip_file:
                    products_content = zip_file.read('products.csv')
                    products_text = products_content.decode('utf-8-sig')
                    
                    # Check unit normalization in products.csv
                    expected_units = ['г', 'мл', 'шт', 'кг']
                    found_units = []
                    
                    products_reader = csv.reader(io.StringIO(products_text), delimiter=';')
                    products_rows = list(products_reader)
                    
                    for row in products_rows[1:]:  # Skip header
                        if len(row) >= 3:
                            unit = row[2]  # unit column
                            found_units.append(unit)
                    
                    # Check if all expected units are found
                    normalized_correctly = all(unit in found_units for unit in expected_units)
                    
                    if normalized_correctly:
                        self.log_test("Unit Normalization - Products CSV", True, 
                                     f"Units normalized correctly: {found_units}")
                    else:
                        self.log_test("Unit Normalization - Products CSV", False, 
                                     f"Expected: {expected_units}, Found: {found_units}")
                    
                    # Check recipes.csv as well
                    recipes_content = zip_file.read('recipes.csv')
                    recipes_text = recipes_content.decode('utf-8-sig')
                    
                    recipes_reader = csv.reader(io.StringIO(recipes_text), delimiter=';')
                    recipes_rows = list(recipes_reader)
                    
                    recipe_units = []
                    for row in recipes_rows[1:]:  # Skip header
                        if len(row) >= 8:
                            unit = row[7]  # unit column
                            recipe_units.append(unit)
                    
                    if all(unit in expected_units for unit in recipe_units):
                        self.log_test("Unit Normalization - Recipes CSV", True, 
                                     f"Recipe units normalized: {recipe_units}")
                    else:
                        self.log_test("Unit Normalization - Recipes CSV", False, 
                                     f"Some recipe units not normalized: {recipe_units}")
            else:
                self.log_test("Unit Normalization - Export Failed", False, 
                             f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Unit Normalization - Test", False, f"Exception: {str(e)}")
    
    def test_price_calculation_and_currency(self):
        """Test 5: Price Calculation and Currency (RUB)"""
        print("\n🔍 Testing Price Calculation and Currency...")
        
        try:
            test_card = self.create_test_techcard()
            
            url = f"{self.backend_url}/v1/techcards.v2/export/iiko.csv"
            response = requests.post(url, json=test_card, timeout=30)
            
            if response.status_code == 200:
                zip_content = io.BytesIO(response.content)
                with zipfile.ZipFile(zip_content, 'r') as zip_file:
                    products_content = zip_file.read('products.csv')
                    products_text = products_content.decode('utf-8-sig')
                    
                    products_reader = csv.reader(io.StringIO(products_text), delimiter=';')
                    products_rows = list(products_reader)
                    
                    prices_valid = True
                    currencies_valid = True
                    
                    for row in products_rows[1:]:  # Skip header
                        if len(row) >= 5:
                            price = row[3]  # price_per_unit
                            currency = row[4]  # currency
                            
                            # Check price format (should be decimal with dot)
                            try:
                                price_float = float(price)
                                if price_float < 0:
                                    prices_valid = False
                            except ValueError:
                                prices_valid = False
                            
                            # Check currency is RUB
                            if currency != "RUB":
                                currencies_valid = False
                    
                    if prices_valid:
                        self.log_test("Price Calculation - Valid Prices", True, 
                                     "All prices are valid decimal numbers")
                    else:
                        self.log_test("Price Calculation - Valid Prices", False, 
                                     "Some prices are invalid")
                    
                    if currencies_valid:
                        self.log_test("Price Calculation - Currency RUB", True, 
                                     "All currencies are RUB")
                    else:
                        self.log_test("Price Calculation - Currency RUB", False, 
                                     "Some currencies are not RUB")
                        
            else:
                self.log_test("Price Calculation - Export Failed", False, 
                             f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Price Calculation - Test", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test 6: Error Handling for Edge Cases"""
        print("\n🔍 Testing Error Handling...")
        
        try:
            url = f"{self.backend_url}/v1/techcards.v2/export/iiko.csv"
            
            # Test 6.1: Invalid TechCardV2 data
            invalid_card = {"invalid": "data"}
            response = requests.post(url, json=invalid_card, timeout=30)
            
            if response.status_code in [400, 422]:  # Should return validation error
                self.log_test("Error Handling - Invalid Data", True, 
                             f"Properly rejected invalid data: HTTP {response.status_code}")
            else:
                self.log_test("Error Handling - Invalid Data", False, 
                             f"Should reject invalid data, got: HTTP {response.status_code}")
            
            # Test 6.2: Empty ingredients list
            empty_card = self.create_test_techcard()
            empty_card["ingredients"] = []
            
            response = requests.post(url, json=empty_card, timeout=30)
            
            if response.status_code == 200:
                # Should still work but produce empty/minimal CSV
                self.log_test("Error Handling - Empty Ingredients", True, 
                             "Handles empty ingredients gracefully")
            else:
                self.log_test("Error Handling - Empty Ingredients", False, 
                             f"Failed with empty ingredients: HTTP {response.status_code}")
            
            # Test 6.3: Missing required fields
            incomplete_card = {
                "meta": {"title": "Test"},
                # Missing ingredients, portions, yield, etc.
            }
            
            response = requests.post(url, json=incomplete_card, timeout=30)
            
            if response.status_code in [400, 422]:
                self.log_test("Error Handling - Missing Fields", True, 
                             f"Properly validates required fields: HTTP {response.status_code}")
            else:
                self.log_test("Error Handling - Missing Fields", False, 
                             f"Should validate required fields, got: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Test", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all iiko CSV export tests"""
        print("🚀 Starting iiko CSV Export Implementation Backend Testing")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Run all test suites in order
        endpoint_success = self.test_csv_export_endpoint()
        
        if endpoint_success:
            self.test_csv_file_structure()
            self.test_sku_validation_and_issues()
            self.test_unit_normalization()
            self.test_price_calculation_and_currency()
        
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.errors:
            print(f"\n🚨 FAILED TESTS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        # Determine overall result
        critical_tests = [
            "CSV Export - Endpoint Response",
            "CSV Export - ZIP Contents",
            "Products CSV - Header Structure",
            "Recipes CSV - Header Structure",
            "Products CSV - UTF-8 BOM",
            "Recipes CSV - UTF-8 BOM"
        ]
        
        critical_passed = 0
        for test in self.test_results:
            if any(critical in test["test"] for critical in critical_tests) and test["success"]:
                critical_passed += 1
        
        if critical_passed >= 5:  # At least 5 out of 6 critical tests
            print(f"\n🎉 IIKO CSV EXPORT: WORKING")
            print("Core functionality verified - CSV export produces import-ready files")
            return True
        else:
            print(f"\n🚨 IIKO CSV EXPORT: FAILING")
            print(f"Critical issues found - only {critical_passed}/6 critical tests passed")
            return False

def main():
    """Main test execution"""
    tester = IikoCsvExportTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()