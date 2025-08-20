#!/usr/bin/env python3
"""
Backend Testing for D. Dish Code Resolver (актуализировать)

This test suite validates the comprehensive Dish Code Resolver implementation
focusing on:
1. Dish Code Search: POST /api/v1/techcards.v2/dish-codes/find endpoint
2. Dish Code Generation: POST /api/v1/techcards.v2/dish-codes/generate endpoint  
3. Dish Skeletons Export: create_dish_skeletons_xlsx() function and dual export integration
4. Enhanced Dual Export: POST /api/v1/techcards.v2/export/enhanced-dual/iiko.xlsx with dish codes mapping
5. Pre-flight Warnings: missing dish codes detection in preflight-check endpoint
6. Excel File Structure: Verify Dish-Skeletons.xlsx has correct format for iiko import
"""

import requests
import json
import time
import os
import zipfile
import io
from typing import Dict, List, Any
import openpyxl

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://iiko-connect.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

class DishCodeResolverTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.3f}s" if response_time > 0 else "N/A"
        }
        self.test_results.append(result)
        print(f"{status} {test_name} ({response_time:.3f}s): {details}")
        
    def create_sample_techcard(self, dish_name: str) -> Dict[str, Any]:
        """Create a sample techcard for testing"""
        return {
            "meta": {
                "id": f"test-{dish_name.lower().replace(' ', '-')}",
                "title": dish_name,
                "description": f"Test techcard for {dish_name}",
                "created_at": "2025-01-27T10:00:00Z"
            },
            "ingredients": [
                {
                    "name": "Куриное филе",
                    "brutto_g": 200,
                    "netto_g": 180,
                    "loss_pct": 10,
                    "unit": "г",
                    "skuId": "test-chicken-guid-001"
                },
                {
                    "name": "Салат Романо", 
                    "brutto_g": 50,
                    "netto_g": 45,
                    "loss_pct": 10,
                    "unit": "г",
                    "skuId": "test-lettuce-guid-002"
                },
                {
                    "name": "Пармезан",
                    "brutto_g": 30,
                    "netto_g": 30,
                    "loss_pct": 0,
                    "unit": "г",
                    "skuId": "test-cheese-guid-003"
                }
            ],
            "yield_": {
                "perPortion_g": 240,
                "perBatch_g": 240
            },
            "portions": 1,
            "process": [
                {
                    "n": 1,
                    "action": "Подготовить ингредиенты",
                    "time_min": 5,
                    "equipment": ["нож", "доска"]
                },
                {
                    "n": 2,
                    "action": "Нарезать куриное филе",
                    "time_min": 3,
                    "equipment": ["нож"]
                },
                {
                    "n": 3,
                    "action": "Обжарить курицу",
                    "time_min": 10,
                    "temp_c": 180,
                    "equipment": ["сковорода"]
                },
                {
                    "n": 4,
                    "action": "Подать с салатом и сыром",
                    "time_min": 2
                }
            ],
            "storage": {
                "conditions": "Хранить в холодильнике при температуре +2...+6°C",
                "shelfLife_hours": 24,
                "servingTemp_c": 65
            },
            "nutrition": {"per100g": {}, "perPortion": {}},
            "cost": {"per100g": {}, "perPortion": {}}
        }
        
    def test_dish_codes_find_endpoint(self):
        """Test POST /api/v1/techcards.v2/dish-codes/find endpoint"""
        print("\n🔍 Testing Dish Code Search Endpoint...")
        
        test_cases = [
            {
                "name": "Find existing dishes",
                "payload": {
                    "dish_names": ["Салат Цезарь", "Борщ украинский", "Стейк из говядины"],
                    "organization_id": "default"
                }
            },
            {
                "name": "Find non-existent dishes", 
                "payload": {
                    "dish_names": ["Несуществующее блюдо 123", "Тестовое блюдо XYZ"],
                    "organization_id": "default"
                }
            },
            {
                "name": "Empty dish names",
                "payload": {
                    "dish_names": [],
                    "organization_id": "default"
                },
                "expect_error": True
            }
        ]
        
        for case in test_cases:
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/techcards.v2/dish-codes/find",
                    json=case["payload"]
                )
                response_time = time.time() - start_time
                
                if case.get("expect_error"):
                    if response.status_code == 400:
                        self.log_test(f"Find Dish Codes - {case['name']}", True, 
                                    "Correctly returned 400 for empty dish names", response_time)
                    else:
                        self.log_test(f"Find Dish Codes - {case['name']}", False,
                                    f"Expected 400, got {response.status_code}", response_time)
                    continue
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate response structure
                    if "status" in data and "results" in data:
                        results = data["results"]
                        
                        # Check each result has required fields
                        valid_results = True
                        for result in results:
                            required_fields = ["dish_name", "status"]
                            if not all(field in result for field in required_fields):
                                valid_results = False
                                break
                                
                            # If found, should have dish_code and confidence
                            if result["status"] == "found":
                                if "dish_code" not in result or "confidence" not in result:
                                    valid_results = False
                                    break
                        
                        if valid_results:
                            found_count = sum(1 for r in results if r["status"] == "found")
                            self.log_test(f"Find Dish Codes - {case['name']}", True,
                                        f"Found {found_count}/{len(results)} dishes with valid structure", response_time)
                        else:
                            self.log_test(f"Find Dish Codes - {case['name']}", False,
                                        "Invalid result structure", response_time)
                    else:
                        self.log_test(f"Find Dish Codes - {case['name']}", False,
                                    "Missing status or results in response", response_time)
                else:
                    self.log_test(f"Find Dish Codes - {case['name']}", False,
                                f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                    
            except Exception as e:
                self.log_test(f"Find Dish Codes - {case['name']}", False, f"Exception: {str(e)}")
                
    def test_dish_codes_generate_endpoint(self):
        """Test POST /api/v1/techcards.v2/dish-codes/generate endpoint"""
        print("\n🔢 Testing Dish Code Generation Endpoint...")
        
        test_cases = [
            {
                "name": "Generate codes for new dishes",
                "payload": {
                    "dish_names": ["Новое блюдо 1", "Новое блюдо 2", "Тестовое блюдо 3"],
                    "organization_id": "default",
                    "width": 5
                }
            },
            {
                "name": "Generate with custom width",
                "payload": {
                    "dish_names": ["Блюдо с длинным кодом"],
                    "organization_id": "default", 
                    "width": 6
                }
            },
            {
                "name": "Generate for 10 dishes (performance test)",
                "payload": {
                    "dish_names": [f"Тестовое блюдо {i}" for i in range(1, 11)],
                    "organization_id": "default",
                    "width": 5
                }
            }
        ]
        
        for case in test_cases:
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/techcards.v2/dish-codes/generate",
                    json=case["payload"]
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "status" in data and "generated_codes" in data:
                        generated_codes = data["generated_codes"]
                        expected_count = len(case["payload"]["dish_names"])
                        
                        if len(generated_codes) == expected_count:
                            # Validate code format
                            width = case["payload"].get("width", 5)
                            valid_codes = True
                            unique_codes = set()
                            
                            for dish_name, code in generated_codes.items():
                                # Check code format (should be numeric with leading zeros)
                                if not code.isdigit() or len(code) != width:
                                    valid_codes = False
                                    break
                                    
                                # Check uniqueness
                                if code in unique_codes:
                                    valid_codes = False
                                    break
                                unique_codes.add(code)
                            
                            if valid_codes:
                                self.log_test(f"Generate Dish Codes - {case['name']}", True,
                                            f"Generated {len(generated_codes)} unique codes with width {width}", response_time)
                            else:
                                self.log_test(f"Generate Dish Codes - {case['name']}", False,
                                            "Invalid code format or duplicates found", response_time)
                        else:
                            self.log_test(f"Generate Dish Codes - {case['name']}", False,
                                        f"Expected {expected_count} codes, got {len(generated_codes)}", response_time)
                    else:
                        self.log_test(f"Generate Dish Codes - {case['name']}", False,
                                    "Missing status or generated_codes in response", response_time)
                else:
                    self.log_test(f"Generate Dish Codes - {case['name']}", False,
                                f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                    
            except Exception as e:
                self.log_test(f"Generate Dish Codes - {case['name']}", False, f"Exception: {str(e)}")
                
    def test_enhanced_dual_export(self):
        """Test POST /api/v1/techcards.v2/export/enhanced-dual/iiko.xlsx with dish codes mapping"""
        print("\n📦 Testing Enhanced Dual Export with Dish Codes...")
        
        # Create sample techcards
        sample_cards = [
            self.create_sample_techcard("Салат Цезарь с курицей"),
            self.create_sample_techcard("Стейк с грибным соусом")
        ]
        
        # Create dish codes mapping
        dish_codes_mapping = {
            "Салат Цезарь с курицей": "12345",
            "Стейк с грибным соусом": "12346"
        }
        
        test_payload = {
            "techcards": sample_cards,
            "export_options": {
                "use_product_codes": True,
                "dish_codes_mapping": dish_codes_mapping
            },
            "organization_id": "default",
            "user_email": "test@example.com"
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/techcards.v2/export/enhanced-dual/iiko.xlsx",
                json=test_payload
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check if response is a ZIP file
                if response.headers.get('content-type') == 'application/zip':
                    zip_content = response.content
                    
                    # Validate ZIP structure
                    try:
                        with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                            file_list = zip_file.namelist()
                            
                            # Check for required files
                            has_skeletons = any('Dish-Skeletons.xlsx' in f for f in file_list)
                            has_ttk = any('iiko_TTK' in f and f.endswith('.xlsx') for f in file_list)
                            
                            if has_skeletons and has_ttk:
                                self.log_test("Enhanced Dual Export - ZIP Structure", True,
                                            f"ZIP contains {len(file_list)} files including Dish-Skeletons.xlsx and TTK files", response_time)
                                
                                # Test Dish-Skeletons.xlsx structure
                                self.validate_dish_skeletons_xlsx(zip_file, dish_codes_mapping)
                                
                            else:
                                self.log_test("Enhanced Dual Export - ZIP Structure", False,
                                            f"Missing required files. Found: {file_list}", response_time)
                    except Exception as e:
                        self.log_test("Enhanced Dual Export - ZIP Validation", False,
                                    f"ZIP validation error: {str(e)}", response_time)
                else:
                    self.log_test("Enhanced Dual Export - Response Type", False,
                                f"Expected ZIP, got {response.headers.get('content-type')}", response_time)
            else:
                self.log_test("Enhanced Dual Export - Request", False,
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            self.log_test("Enhanced Dual Export - Request", False, f"Exception: {str(e)}")
            
    def validate_dish_skeletons_xlsx(self, zip_file: zipfile.ZipFile, dish_codes_mapping: Dict[str, str]):
        """Validate Dish-Skeletons.xlsx file structure and content"""
        print("\n📊 Validating Dish-Skeletons.xlsx Structure...")
        
        try:
            # Extract Dish-Skeletons.xlsx
            skeletons_file = None
            for filename in zip_file.namelist():
                if 'Dish-Skeletons.xlsx' in filename:
                    skeletons_file = filename
                    break
                    
            if not skeletons_file:
                self.log_test("Dish Skeletons XLSX - File Exists", False, "Dish-Skeletons.xlsx not found in ZIP")
                return
                
            # Read Excel file
            excel_data = zip_file.read(skeletons_file)
            workbook = openpyxl.load_workbook(io.BytesIO(excel_data))
            worksheet = workbook.active
            
            # Expected headers for iiko import
            expected_headers = ["Артикул", "Наименование", "Тип", "Ед. выпуска", "Выход"]
            
            # Check headers
            actual_headers = []
            for col in range(1, 6):  # First 5 columns
                cell_value = worksheet.cell(row=1, column=col).value
                actual_headers.append(cell_value)
                
            if actual_headers == expected_headers:
                self.log_test("Dish Skeletons XLSX - Headers", True,
                            f"Correct headers: {actual_headers}")
            else:
                self.log_test("Dish Skeletons XLSX - Headers", False,
                            f"Expected {expected_headers}, got {actual_headers}")
                return
                
            # Check data rows
            data_rows = 0
            codes_found = []
            
            for row in range(2, worksheet.max_row + 1):
                dish_code = worksheet.cell(row=row, column=1).value  # Артикул
                dish_name = worksheet.cell(row=row, column=2).value  # Наименование
                dish_type = worksheet.cell(row=row, column=3).value  # Тип
                unit = worksheet.cell(row=row, column=4).value       # Ед. выпуска
                yield_val = worksheet.cell(row=row, column=5).value  # Выход
                
                if dish_code and dish_name:
                    data_rows += 1
                    codes_found.append(dish_code)
                    
                    # Validate dish type
                    if dish_type != "Блюдо":
                        self.log_test("Dish Skeletons XLSX - Data Validation", False,
                                    f"Row {row}: Expected type 'Блюдо', got '{dish_type}'")
                        return
                        
                    # Check if code format is preserved (text format)
                    cell = worksheet.cell(row=row, column=1)
                    if cell.number_format != '@':
                        self.log_test("Dish Skeletons XLSX - Code Format", False,
                                    f"Row {row}: Code not formatted as text (@)")
                        return
            
            # Validate that dish codes from mapping are present
            mapping_codes = set(dish_codes_mapping.values())
            found_codes = set(str(code) for code in codes_found)
            
            if mapping_codes.issubset(found_codes):
                self.log_test("Dish Skeletons XLSX - Data Content", True,
                            f"Found {data_rows} dishes with correct codes and structure")
            else:
                missing_codes = mapping_codes - found_codes
                self.log_test("Dish Skeletons XLSX - Data Content", False,
                            f"Missing codes from mapping: {missing_codes}")
                
        except Exception as e:
            self.log_test("Dish Skeletons XLSX - Validation", False, f"Validation error: {str(e)}")
            
    def test_preflight_warnings(self):
        """Test POST /api/v1/techcards.v2/export/preflight-check endpoint"""
        print("\n⚠️ Testing Pre-flight Warnings...")
        
        # Create techcards with and without dish codes
        sample_cards = [
            self.create_sample_techcard("Блюдо с кодом"),
            self.create_sample_techcard("Блюдо без кода")
        ]
        
        test_cases = [
            {
                "name": "Cards with missing dish codes",
                "payload": {
                    "techcards": sample_cards,
                    "export_options": {
                        "use_product_codes": True,
                        "dish_codes_mapping": {
                            "Блюдо с кодом": "12345"
                            # "Блюдо без кода" intentionally missing
                        }
                    },
                    "organization_id": "default"
                },
                "expect_warnings": True
            },
            {
                "name": "Cards with all dish codes",
                "payload": {
                    "techcards": sample_cards,
                    "export_options": {
                        "use_product_codes": False,  # Disable product code checking
                        "dish_codes_mapping": {
                            "Блюдо с кодом": "12345",
                            "Блюдо без кода": "12346"
                        }
                    },
                    "organization_id": "default"
                },
                "expect_warnings": False
            }
        ]
        
        for case in test_cases:
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/techcards.v2/export/preflight-check",
                    json=case["payload"]
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate response structure
                    required_fields = ["status", "warnings", "cards_checked", "export_ready"]
                    if all(field in data for field in required_fields):
                        
                        has_warnings = len(data["warnings"]) > 0
                        status = data["status"]
                        export_ready = data["export_ready"]
                        
                        # Check logic consistency
                        if case["expect_warnings"]:
                            if has_warnings and status == "warnings" and not export_ready:
                                # Validate warning structure
                                valid_warnings = True
                                for warning in data["warnings"]:
                                    required_warning_fields = ["type", "title", "items", "action", "severity"]
                                    if not all(field in warning for field in required_warning_fields):
                                        valid_warnings = False
                                        break
                                
                                if valid_warnings:
                                    self.log_test(f"Preflight Check - {case['name']}", True,
                                                f"Detected {len(data['warnings'])} warnings correctly", response_time)
                                else:
                                    self.log_test(f"Preflight Check - {case['name']}", False,
                                                "Invalid warning structure", response_time)
                            else:
                                self.log_test(f"Preflight Check - {case['name']}", False,
                                            f"Expected warnings but got status={status}, warnings={len(data['warnings'])}", response_time)
                        else:
                            if not has_warnings and status == "ready" and export_ready:
                                self.log_test(f"Preflight Check - {case['name']}", True,
                                            "No warnings detected as expected", response_time)
                            else:
                                self.log_test(f"Preflight Check - {case['name']}", False,
                                            f"Unexpected warnings: status={status}, warnings={len(data['warnings'])}", response_time)
                    else:
                        missing_fields = [f for f in required_fields if f not in data]
                        self.log_test(f"Preflight Check - {case['name']}", False,
                                    f"Missing required fields: {missing_fields}", response_time)
                else:
                    self.log_test(f"Preflight Check - {case['name']}", False,
                                f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                    
            except Exception as e:
                self.log_test(f"Preflight Check - {case['name']}", False, f"Exception: {str(e)}")
                
    def test_performance_requirements(self):
        """Test performance requirements for dish code operations"""
        print("\n⚡ Testing Performance Requirements...")
        
        # Test dish code generation performance (should be <2s for 10 dishes)
        dish_names = [f"Тестовое блюдо {i}" for i in range(1, 11)]
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/techcards.v2/dish-codes/generate",
                json={
                    "dish_names": dish_names,
                    "organization_id": "default",
                    "width": 5
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200 and response_time < 2.0:
                self.log_test("Performance - Dish Code Generation", True,
                            f"Generated 10 codes in {response_time:.3f}s (target: <2s)", response_time)
            else:
                self.log_test("Performance - Dish Code Generation", False,
                            f"Too slow: {response_time:.3f}s (target: <2s)", response_time)
                            
        except Exception as e:
            self.log_test("Performance - Dish Code Generation", False, f"Exception: {str(e)}")
            
        # Test preflight check performance (should be <3s for validation)
        sample_cards = [self.create_sample_techcard(f"Блюдо {i}") for i in range(1, 6)]
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{API_BASE}/techcards.v2/export/preflight-check",
                json={
                    "techcards": sample_cards,
                    "export_options": {"use_product_codes": True, "dish_codes_mapping": {}},
                    "organization_id": "default"
                }
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200 and response_time < 3.0:
                self.log_test("Performance - Preflight Check", True,
                            f"Validated 5 cards in {response_time:.3f}s (target: <3s)", response_time)
            else:
                self.log_test("Performance - Preflight Check", False,
                            f"Too slow: {response_time:.3f}s (target: <3s)", response_time)
                            
        except Exception as e:
            self.log_test("Performance - Preflight Check", False, f"Exception: {str(e)}")
            
    def test_integration_workflow(self):
        """Test end-to-end workflow: generate codes → integrate with dual export → validate ZIP"""
        print("\n🔄 Testing Complete Integration Workflow...")
        
        # Step 1: Generate dish codes
        dish_names = ["Интеграционное блюдо 1", "Интеграционное блюдо 2"]
        
        try:
            # Generate codes
            start_time = time.time()
            gen_response = self.session.post(
                f"{API_BASE}/techcards.v2/dish-codes/generate",
                json={
                    "dish_names": dish_names,
                    "organization_id": "default",
                    "width": 5
                }
            )
            gen_time = time.time() - start_time
            
            if gen_response.status_code != 200:
                self.log_test("Integration Workflow - Code Generation", False,
                            f"Code generation failed: {gen_response.status_code}")
                return
                
            generated_codes = gen_response.json().get("generated_codes", {})
            
            # Step 2: Create techcards with generated codes
            sample_cards = [self.create_sample_techcard(name) for name in dish_names]
            
            # Step 3: Export with dual export
            start_time = time.time()
            export_response = self.session.post(
                f"{API_BASE}/techcards.v2/export/enhanced-dual/iiko.xlsx",
                json={
                    "techcards": sample_cards,
                    "export_options": {
                        "use_product_codes": True,
                        "dish_codes_mapping": generated_codes
                    },
                    "organization_id": "default",
                    "user_email": "integration@test.com"
                }
            )
            export_time = time.time() - start_time
            
            if export_response.status_code == 200:
                # Step 4: Validate ZIP contents
                if export_response.headers.get('content-type') == 'application/zip':
                    zip_content = export_response.content
                    
                    with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                        file_list = zip_file.namelist()
                        
                        # Check for both required files
                        has_skeletons = any('Dish-Skeletons.xlsx' in f for f in file_list)
                        has_ttk = any('iiko_TTK' in f and f.endswith('.xlsx') for f in file_list)
                        
                        if has_skeletons and has_ttk:
                            total_time = gen_time + export_time
                            self.log_test("Integration Workflow - Complete", True,
                                        f"Generated codes → exported ZIP with both files in {total_time:.3f}s", total_time)
                        else:
                            self.log_test("Integration Workflow - ZIP Content", False,
                                        f"Missing files in ZIP: {file_list}")
                else:
                    self.log_test("Integration Workflow - Export Format", False,
                                "Export did not return ZIP file")
            else:
                self.log_test("Integration Workflow - Export", False,
                            f"Export failed: {export_response.status_code}")
                
        except Exception as e:
            self.log_test("Integration Workflow - Complete", False, f"Exception: {str(e)}")
            
    def run_all_tests(self):
        """Run all Dish Code Resolver tests"""
        print("🎯 STARTING D. DISH CODE RESOLVER COMPREHENSIVE TESTING")
        print("=" * 80)
        
        # Run all test categories
        self.test_dish_codes_find_endpoint()
        self.test_dish_codes_generate_endpoint()
        self.test_enhanced_dual_export()
        self.test_preflight_warnings()
        self.test_performance_requirements()
        self.test_integration_workflow()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 DISH CODE RESOLVER TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n🎯 DISH CODE RESOLVER TESTING COMPLETED")
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = DishCodeResolverTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)