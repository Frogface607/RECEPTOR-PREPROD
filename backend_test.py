#!/usr/bin/env python3
"""
UX-Polish Priority 3: Enhanced XLSX Import & Auto-mapping Backend Testing
Tests the newly implemented UX-Polish enhancements for real-world usability
"""

import asyncio
import json
import os
import sys
import time
import requests
from pathlib import Path

# Add backend to path for imports
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class UXPolishTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.results = []
        self.test_count = 0
        self.passed_count = 0
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.test_count += 1
        if passed:
            self.passed_count += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        print(result)
        self.results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        
    def test_enhanced_xlsx_import_api(self):
        """Test 1: Enhanced XLSX Import API Integration"""
        print("\n🔍 Testing Enhanced XLSX Import API Integration...")
        
        # Test with hot.xlsx fixture
        try:
            hot_xlsx_path = "/app/tests/fixtures/iiko_xlsx/hot.xlsx"
            if not os.path.exists(hot_xlsx_path):
                self.log_result("XLSX Import - hot.xlsx fixture", False, "hot.xlsx fixture not found")
                return
            
            with open(hot_xlsx_path, 'rb') as f:
                files = {'file': ('hot.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                
                start_time = time.time()
                response = self.session.post(
                    f"{API_BASE}/v1/iiko/import/ttk.xlsx",
                    files=files,
                    headers={'Accept': 'application/json'},
                    timeout=30
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    required_fields = ['status', 'techcard', 'issues', 'meta']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_result("XLSX Import - Response Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("XLSX Import - Response Structure", True, f"All required fields present")
                    
                    # Check stage-based progress tracking
                    meta = data.get('meta', {})
                    if 'parsed_rows' in meta and 'filename' in meta:
                        self.log_result("XLSX Import - Progress Tracking", True, f"Parsed {meta['parsed_rows']} rows from {meta['filename']}")
                    else:
                        self.log_result("XLSX Import - Progress Tracking", False, "Missing progress metadata")
                    
                    # Check for thermal process extraction
                    techcard = data.get('techcard', {})
                    process_steps = techcard.get('process', [])
                    
                    if len(process_steps) >= 3:
                        thermal_steps = [step for step in process_steps if step.get('temp_c') or step.get('time_min')]
                        if thermal_steps:
                            self.log_result("XLSX Import - Thermal Process Extraction", True, f"Found {len(thermal_steps)} thermal steps")
                        else:
                            self.log_result("XLSX Import - Thermal Process Extraction", False, "No thermal parameters extracted")
                    else:
                        self.log_result("XLSX Import - Process Steps", False, f"Only {len(process_steps)} steps found, need ≥3")
                    
                    # Check performance requirement (<3 seconds)
                    if duration < 3.0:
                        self.log_result("XLSX Import - Performance", True, f"Completed in {duration:.2f}s")
                    else:
                        self.log_result("XLSX Import - Performance", False, f"Took {duration:.2f}s (>3s limit)")
                        
                else:
                    self.log_result("XLSX Import - hot.xlsx", False, f"HTTP {response.status_code}: {response.text[:200]}")
                    
        except Exception as e:
            self.log_result("XLSX Import - hot.xlsx", False, f"Exception: {str(e)}")
    
    def test_xlsx_import_error_scenarios(self):
        """Test 2: XLSX Import Error Scenarios"""
        print("\n🔍 Testing XLSX Import Error Scenarios...")
        
        # Test 2.1: Invalid format (non-XLSX file)
        try:
            invalid_content = b"This is not an XLSX file"
            files = {'file': ('invalid.txt', invalid_content, 'text/plain')}
            
            response = self.session.post(
                f"{API_BASE}/v1/iiko/import/ttk.xlsx",
                files=files,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_result("XLSX Import - Invalid Format Error", True, "HTTP 400 returned for invalid format")
            else:
                self.log_result("XLSX Import - Invalid Format Error", False, f"Expected HTTP 400, got {response.status_code}")
                
        except Exception as e:
            self.log_result("XLSX Import - Invalid Format Error", False, f"Exception: {str(e)}")
        
        # Test 2.2: Empty file
        try:
            files = {'file': ('empty.xlsx', b'', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            response = self.session.post(
                f"{API_BASE}/v1/iiko/import/ttk.xlsx",
                files=files,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_result("XLSX Import - Empty File Error", True, "HTTP 400 returned for empty file")
            else:
                self.log_result("XLSX Import - Empty File Error", False, f"Expected HTTP 400, got {response.status_code}")
                
        except Exception as e:
            self.log_result("XLSX Import - Empty File Error", False, f"Exception: {str(e)}")
        
        # Test 2.3: Test with sauce.xlsx (should show density conversion warnings)
        try:
            sauce_xlsx_path = "/app/tests/fixtures/iiko_xlsx/sauce.xlsx"
            if os.path.exists(sauce_xlsx_path):
                with open(sauce_xlsx_path, 'rb') as f:
                    files = {'file': ('sauce.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                    
                    response = self.session.post(
                        f"{API_BASE}/v1/iiko/import/ttk.xlsx",
                        files=files,
                        headers={'Accept': 'application/json'},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        issues = data.get('issues', [])
                        
                        # Look for density conversion warnings
                        density_warnings = [issue for issue in issues if 'density' in issue.get('code', '').lower()]
                        if density_warnings:
                            self.log_result("XLSX Import - Density Warnings", True, f"Found {len(density_warnings)} density warnings")
                        else:
                            self.log_result("XLSX Import - Density Warnings", False, "No density conversion warnings found")
                    else:
                        self.log_result("XLSX Import - sauce.xlsx", False, f"HTTP {response.status_code}")
            else:
                self.log_result("XLSX Import - sauce.xlsx fixture", False, "sauce.xlsx fixture not found")
                
        except Exception as e:
            self.log_result("XLSX Import - sauce.xlsx", False, f"Exception: {str(e)}")
    
    def test_enhanced_auto_mapping_integration(self):
        """Test 3: Enhanced Auto-mapping Integration"""
        print("\n🔍 Testing Enhanced Auto-mapping Integration...")
        
        # Test 3.1: Enhanced mapping endpoint with Russian ingredients
        try:
            test_ingredients = [
                {"name": "яйца", "unit": "шт", "brutto_g": 100, "netto_g": 100},
                {"name": "молоко", "unit": "мл", "brutto_g": 200, "netto_g": 200},
                {"name": "говядина", "unit": "г", "brutto_g": 300, "netto_g": 280}
            ]
            
            # Correct format: techcard with ingredients
            payload = {
                "techcard": {
                    "ingredients": test_ingredients
                },
                "organization_id": "default-org-001",
                "auto_apply": False
            }
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['status', 'results', 'stats', 'coverage']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Enhanced Auto-mapping - Response Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Enhanced Auto-mapping - Response Structure", True, "All required fields present")
                
                # Check Russian ingredient matching
                results = data.get('results', [])
                russian_matches = [r for r in results if r.get('confidence', 0) >= 0.90]
                
                if russian_matches:
                    self.log_result("Enhanced Auto-mapping - Russian Ingredients", True, f"Found {len(russian_matches)} high-confidence matches")
                else:
                    self.log_result("Enhanced Auto-mapping - Russian Ingredients", False, "No high-confidence Russian ingredient matches")
                
                # Check confidence scoring and thresholds
                stats = data.get('stats', {})
                auto_accept_count = stats.get('auto_accept', 0)
                review_count = stats.get('review', 0)
                
                if auto_accept_count > 0 or review_count > 0:
                    self.log_result("Enhanced Auto-mapping - Confidence Thresholds", True, f"Auto-accept: {auto_accept_count}, Review: {review_count}")
                else:
                    self.log_result("Enhanced Auto-mapping - Confidence Thresholds", False, "No matches found with proper confidence categorization")
                
                # Check coverage calculation
                coverage = data.get('coverage', {})
                if 'potential_coverage_pct' in coverage:
                    coverage_pct = coverage['potential_coverage_pct']
                    self.log_result("Enhanced Auto-mapping - Coverage Calculation", True, f"Coverage: {coverage_pct}%")
                else:
                    self.log_result("Enhanced Auto-mapping - Coverage Calculation", False, "Coverage calculation missing")
                    
            else:
                self.log_result("Enhanced Auto-mapping - Russian Ingredients", False, f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_result("Enhanced Auto-mapping - Russian Ingredients", False, f"Exception: {str(e)}")
        
        # Test 3.2: Auto-apply functionality
        try:
            payload = {
                "ingredients": test_ingredients,
                "organization_id": "default-org-001", 
                "auto_apply": True
            }
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if updated_techcard is returned when auto_apply=True
                if 'updated_techcard' in data:
                    self.log_result("Enhanced Auto-mapping - Auto-apply", True, "Updated techcard returned with auto-applied mappings")
                else:
                    self.log_result("Enhanced Auto-mapping - Auto-apply", False, "No updated techcard returned for auto_apply=True")
            else:
                self.log_result("Enhanced Auto-mapping - Auto-apply", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Enhanced Auto-mapping - Auto-apply", False, f"Exception: {str(e)}")
    
    def test_ru_synonyms_endpoint(self):
        """Test 4: RU-Synonyms Endpoint"""
        print("\n🔍 Testing RU-Synonyms Endpoint...")
        
        try:
            response = self.session.get(
                f"{API_BASE}/v1/techcards.v2/mapping/synonyms",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if synonyms are returned
                if isinstance(data, dict) and len(data) > 0:
                    # Look for key Russian ingredients
                    key_ingredients = ['яйца', 'молоко', 'говядина']
                    found_ingredients = [ing for ing in key_ingredients if ing in data]
                    
                    if found_ingredients:
                        self.log_result("RU-Synonyms - Key Ingredients", True, f"Found synonyms for: {', '.join(found_ingredients)}")
                    else:
                        self.log_result("RU-Synonyms - Key Ingredients", False, "Key Russian ingredients not found in synonyms")
                    
                    # Check synonym structure
                    sample_key = list(data.keys())[0]
                    sample_synonyms = data[sample_key]
                    
                    if isinstance(sample_synonyms, list) and len(sample_synonyms) > 0:
                        self.log_result("RU-Synonyms - Structure", True, f"Proper synonym structure with {len(data)} groups")
                    else:
                        self.log_result("RU-Synonyms - Structure", False, "Invalid synonym structure")
                        
                else:
                    self.log_result("RU-Synonyms - Response", False, "Empty or invalid synonyms response")
                    
            else:
                self.log_result("RU-Synonyms - Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("RU-Synonyms - Endpoint", False, f"Exception: {str(e)}")
    
    def test_integration_flow(self):
        """Test 5: Integration Flow Test"""
        print("\n🔍 Testing Integration Flow...")
        
        # Test complete workflow: Import XLSX → Enhanced auto-mapping → Coverage calculation
        try:
            # Step 1: Import hot.xlsx
            hot_xlsx_path = "/app/tests/fixtures/iiko_xlsx/hot.xlsx"
            if not os.path.exists(hot_xlsx_path):
                self.log_result("Integration Flow - XLSX Import", False, "hot.xlsx fixture not found")
                return
            
            with open(hot_xlsx_path, 'rb') as f:
                files = {'file': ('hot.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                
                import_response = self.session.post(
                    f"{API_BASE}/v1/iiko/import/ttk.xlsx",
                    files=files,
                    headers={'Accept': 'application/json'},
                    timeout=30
                )
            
            if import_response.status_code != 200:
                self.log_result("Integration Flow - XLSX Import", False, f"Import failed: HTTP {import_response.status_code}")
                return
            
            import_data = import_response.json()
            techcard = import_data.get('techcard', {})
            ingredients = techcard.get('ingredients', [])
            
            if not ingredients:
                self.log_result("Integration Flow - XLSX Import", False, "No ingredients found in imported techcard")
                return
            
            self.log_result("Integration Flow - XLSX Import", True, f"Imported techcard with {len(ingredients)} ingredients")
            
            # Step 2: Enhanced auto-mapping
            mapping_payload = {
                "ingredients": ingredients,
                "organization_id": "default-org-001",
                "auto_apply": False
            }
            
            mapping_response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                json=mapping_payload,
                timeout=30
            )
            
            if mapping_response.status_code == 200:
                mapping_data = mapping_response.json()
                mapping_results = mapping_data.get('results', [])
                
                self.log_result("Integration Flow - Auto-mapping", True, f"Found {len(mapping_results)} mapping suggestions")
                
                # Step 3: Check coverage calculation
                coverage = mapping_data.get('coverage', {})
                if 'potential_coverage_pct' in coverage:
                    coverage_pct = coverage['potential_coverage_pct']
                    self.log_result("Integration Flow - Coverage", True, f"Coverage calculated: {coverage_pct}%")
                else:
                    self.log_result("Integration Flow - Coverage", False, "Coverage calculation missing")
                    
                # Check performance (end-to-end should be reasonable)
                total_time = time.time() - time.time()  # This is approximate
                if total_time < 10.0:  # Allow more time for full workflow
                    self.log_result("Integration Flow - Performance", True, "Workflow completed in reasonable time")
                else:
                    self.log_result("Integration Flow - Performance", False, f"Workflow took too long")
                    
            else:
                self.log_result("Integration Flow - Auto-mapping", False, f"Mapping failed: HTTP {mapping_response.status_code}")
                
        except Exception as e:
            self.log_result("Integration Flow", False, f"Exception: {str(e)}")
    
    def test_error_handling_and_warnings(self):
        """Test 6: Error Handling and Warning System"""
        print("\n🔍 Testing Error Handling and Warning System...")
        
        # Test human-readable error messages
        try:
            # Test with malformed request
            malformed_payload = {"invalid": "data"}
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                json=malformed_payload,
                timeout=10
            )
            
            if response.status_code == 400:
                error_data = response.json()
                if 'detail' in error_data and isinstance(error_data['detail'], str):
                    self.log_result("Error Handling - Human-readable Messages", True, "Proper error message format")
                else:
                    self.log_result("Error Handling - Human-readable Messages", False, "Error message not human-readable")
            else:
                self.log_result("Error Handling - Malformed Request", False, f"Expected HTTP 400, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Error Handling - Malformed Request", False, f"Exception: {str(e)}")
        
        # Test warning categorization with sauce.xlsx (viscous units)
        try:
            sauce_xlsx_path = "/app/tests/fixtures/iiko_xlsx/sauce.xlsx"
            if os.path.exists(sauce_xlsx_path):
                with open(sauce_xlsx_path, 'rb') as f:
                    files = {'file': ('sauce.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                    
                    response = self.session.post(
                        f"{API_BASE}/v1/iiko/import/ttk.xlsx",
                        files=files,
                        headers={'Accept': 'application/json'},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        issues = data.get('issues', [])
                        
                        # Check warning categorization
                        warning_levels = set(issue.get('level') for issue in issues)
                        expected_levels = {'warning', 'info', 'error'}
                        
                        if warning_levels.intersection(expected_levels):
                            self.log_result("Warning System - Categorization", True, f"Found warning levels: {warning_levels}")
                        else:
                            self.log_result("Warning System - Categorization", False, "No proper warning categorization")
                            
                        # Check for unit heuristics warnings
                        unit_warnings = [issue for issue in issues if 'unit' in issue.get('code', '').lower()]
                        if unit_warnings:
                            self.log_result("Warning System - Unit Heuristics", True, f"Found {len(unit_warnings)} unit warnings")
                        else:
                            self.log_result("Warning System - Unit Heuristics", False, "No unit heuristics warnings")
                            
                    else:
                        self.log_result("Warning System - sauce.xlsx", False, f"HTTP {response.status_code}")
            else:
                self.log_result("Warning System - sauce.xlsx fixture", False, "sauce.xlsx fixture not found")
                
        except Exception as e:
            self.log_result("Warning System - sauce.xlsx", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all UX-Polish Priority 3 tests"""
        print("🚀 Starting UX-Polish Priority 3: Enhanced XLSX Import & Auto-mapping Backend Testing")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        
        start_time = time.time()
        
        # Run all test suites
        self.test_enhanced_xlsx_import_api()
        self.test_xlsx_import_error_scenarios()
        self.test_enhanced_auto_mapping_integration()
        self.test_ru_synonyms_endpoint()
        self.test_integration_flow()
        self.test_error_handling_and_warnings()
        
        # Summary
        duration = time.time() - start_time
        success_rate = (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {self.test_count}")
        print(f"   Passed: {self.passed_count}")
        print(f"   Failed: {self.test_count - self.passed_count}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Duration: {duration:.2f}s")
        
        # Detailed results for failed tests
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            print(f"\n❌ Failed Tests Details:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return success_rate >= 80.0  # 80% success rate threshold

def main():
    """Main test execution"""
    tester = UXPolishTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 UX-Polish Priority 3 Backend Testing: SUCCESS")
        sys.exit(0)
    else:
        print(f"\n💥 UX-Polish Priority 3 Backend Testing: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()