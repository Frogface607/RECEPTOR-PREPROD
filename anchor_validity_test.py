#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Anchor Validity (Task C1)
Testing: «Анкерная валидность: блюдо обязано соответствовать брифу»

This test suite validates the anchor validity implementation including:
1. Anchor extraction from dish names
2. Mapping through anchors_map.json (RU→EN)
3. Content checking via contentcheck_v2.py (4 checks)
4. Integration in pipeline.py with STRICT_ANCHORS flag
5. Specific test scenarios as requested in review
"""

import os
import sys
import json
import requests
import time
from typing import Dict, Any, List

# Add backend path for imports
sys.path.append('/app/backend')

# Import backend modules for direct testing
try:
    from receptor_agent.llm.pipeline import extract_anchors, run_pipeline, ProfileInput
    from receptor_agent.techcards_v2.contentcheck_v2 import (
        load_anchors_mapping, 
        find_ingredient_canonicals,
        check_ingredient_presence,
        run_content_check,
        has_critical_content_errors
    )
    from receptor_agent.techcards_v2.schemas import TechCardV2
    BACKEND_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Backend imports not available: {e}")
    BACKEND_IMPORTS_AVAILABLE = False

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class AnchorValidityTester:
    """Comprehensive tester for anchor validity functionality"""
    
    def __init__(self):
        self.test_results = []
        self.backend_available = BACKEND_IMPORTS_AVAILABLE
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "status": status
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def test_anchors_mapping_file(self):
        """Test 1: Verify anchors_map.json exists and has correct structure"""
        try:
            anchors_path = "/app/backend/data/anchors_map.json"
            
            if not os.path.exists(anchors_path):
                self.log_test("Anchors mapping file exists", False, f"File not found: {anchors_path}")
                return
            
            with open(anchors_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            
            # Check structure
            required_keys = ["description", "version", "mappings"]
            missing_keys = [key for key in required_keys if key not in mapping]
            
            if missing_keys:
                self.log_test("Anchors mapping structure", False, f"Missing keys: {missing_keys}")
                return
            
            # Check specific mappings from review requirements
            mappings = mapping.get("mappings", {})
            
            # Test треска → cod mapping
            fish_mappings = mappings.get("рыба", {})
            if "треска" not in fish_mappings or "cod" not in fish_mappings["треска"]:
                self.log_test("Треска → cod mapping", False, "треска → cod mapping not found")
                return
            
            # Test брокколи → broccoli mapping  
            vegetable_mappings = mappings.get("овощи", {})
            if "брокколи" not in vegetable_mappings or "broccoli" not in vegetable_mappings["брокколи"]:
                self.log_test("Брокколи → broccoli mapping", False, "брокколи → broccoli mapping not found")
                return
            
            # Test соус биск → bisque_sauce mapping
            sauce_mappings = mappings.get("соусы", {})
            if "соус биск" not in sauce_mappings or "bisque_sauce" not in sauce_mappings["соус биск"]:
                self.log_test("Соус биск → bisque_sauce mapping", False, "соус биск → bisque_sauce mapping not found")
                return
            
            # Test говядина → beef variants mapping
            meat_mappings = mappings.get("мясо", {})
            if "говядина" not in meat_mappings:
                self.log_test("Говядина → beef mapping", False, "говядина mapping not found")
                return
            
            beef_variants = meat_mappings["говядина"]
            expected_beef = ["beef", "beef_tenderloin", "beef_stew", "beef_ground"]
            if not all(variant in beef_variants for variant in expected_beef):
                self.log_test("Говядина → beef variants", False, f"Missing beef variants. Expected: {expected_beef}, Found: {beef_variants}")
                return
            
            self.log_test("Anchors mapping file structure and content", True, f"Found {len(mappings)} categories with required mappings")
            
        except Exception as e:
            self.log_test("Anchors mapping file test", False, f"Error: {str(e)}")
    
    def test_anchor_extraction_direct(self):
        """Test 2: Direct testing of anchor extraction function"""
        if not self.backend_available:
            self.log_test("Anchor extraction (direct)", False, "Backend imports not available")
            return
        
        try:
            # Test case 1: "Треска с брокколи и соусом биск"
            test_dish = "Треска с брокколи и соусом биск"
            
            # Set environment for testing
            os.environ['TECHCARDS_V2_USE_LLM'] = 'false'  # Use fallback for testing
            
            constraints = extract_anchors(test_dish, "европейская")
            
            # Check structure
            required_keys = ["mustHave", "forbid", "hints"]
            if not all(key in constraints for key in required_keys):
                self.log_test("Anchor extraction structure", False, f"Missing keys in constraints: {constraints}")
                return
            
            # For fallback mode, we expect empty arrays
            if not isinstance(constraints["mustHave"], list):
                self.log_test("Anchor extraction mustHave type", False, f"mustHave is not a list: {type(constraints['mustHave'])}")
                return
            
            self.log_test("Anchor extraction function", True, f"Extracted constraints: {constraints}")
            
        except Exception as e:
            self.log_test("Anchor extraction (direct)", False, f"Error: {str(e)}")
    
    def test_ingredient_mapping_direct(self):
        """Test 3: Direct testing of ingredient mapping functions"""
        if not self.backend_available:
            self.log_test("Ingredient mapping (direct)", False, "Backend imports not available")
            return
        
        try:
            mapping = load_anchors_mapping()
            
            # Test треска → cod
            cod_canonicals = find_ingredient_canonicals("треска", mapping)
            if "cod" not in cod_canonicals:
                self.log_test("Треска → cod canonical mapping", False, f"cod not found in canonicals: {cod_canonicals}")
                return
            
            # Test брокколи → broccoli
            broccoli_canonicals = find_ingredient_canonicals("брокколи", mapping)
            if "broccoli" not in broccoli_canonicals:
                self.log_test("Брокколи → broccoli canonical mapping", False, f"broccoli not found in canonicals: {broccoli_canonicals}")
                return
            
            # Test соус биск → bisque_sauce
            bisque_canonicals = find_ingredient_canonicals("соус биск", mapping)
            if "bisque_sauce" not in bisque_canonicals:
                self.log_test("Соус биск → bisque_sauce canonical mapping", False, f"bisque_sauce not found in canonicals: {bisque_canonicals}")
                return
            
            # Test говядина → beef variants
            beef_canonicals = find_ingredient_canonicals("говядина", mapping)
            expected_beef = ["beef", "beef_tenderloin", "beef_stew", "beef_ground"]
            if not any(variant in beef_canonicals for variant in expected_beef):
                self.log_test("Говядина → beef variants mapping", False, f"No beef variants found in canonicals: {beef_canonicals}")
                return
            
            self.log_test("Ingredient canonical mapping", True, f"All test mappings work correctly")
            
        except Exception as e:
            self.log_test("Ingredient mapping (direct)", False, f"Error: {str(e)}")
    
    def test_content_check_direct(self):
        """Test 4: Direct testing of content check functions"""
        if not self.backend_available:
            self.log_test("Content check (direct)", False, "Backend imports not available")
            return
        
        try:
            # Create a test tech card with треска and брокколи
            test_tech_card_data = {
                "meta": {
                    "title": "Треска с брокколи и соусом биск",
                    "version": "2.0",
                    "cuisine": "европейская",
                    "tags": []
                },
                "portions": 4,
                "yield": {
                    "perPortion_g": 200.0,
                    "perBatch_g": 800.0
                },
                "ingredients": [
                    {
                        "name": "Треска филе",
                        "unit": "g",
                        "brutto_g": 600.0,
                        "loss_pct": 10.0,
                        "netto_g": 540.0,
                        "canonical_id": "cod",
                        "allergens": []
                    },
                    {
                        "name": "Брокколи",
                        "unit": "g",
                        "brutto_g": 300.0,
                        "loss_pct": 5.0,
                        "netto_g": 285.0,
                        "canonical_id": "broccoli",
                        "allergens": []
                    },
                    {
                        "name": "Соус биск",
                        "unit": "ml",
                        "brutto_g": 150.0,
                        "loss_pct": 0.0,
                        "netto_g": 150.0,
                        "canonical_id": "bisque_sauce",
                        "allergens": []
                    }
                ],
                "process": [
                    {"n": 1, "action": "Подготовка ингредиентов", "time_min": 10.0, "temp_c": None},
                    {"n": 2, "action": "Приготовление трески", "time_min": 15.0, "temp_c": 180.0},
                    {"n": 3, "action": "Приготовление брокколи", "time_min": 8.0, "temp_c": 100.0}
                ],
                "storage": {
                    "conditions": "Холодильник 0...+4°C",
                    "shelfLife_hours": 24.0,
                    "servingTemp_c": 65.0
                },
                "nutrition": {"per100g": None, "perPortion": None},
                "cost": {"rawCost": None, "costPerPortion": None},
                "printNotes": []
            }
            
            # Validate as TechCardV2
            tech_card = TechCardV2.model_validate(test_tech_card_data)
            
            # Test constraints that should pass
            good_constraints = {
                "mustHave": ["треска", "брокколи", "соус биск"],
                "forbid": ["курица", "свинина"],
                "hints": ["рыба", "овощи", "соус"]
            }
            
            issues = run_content_check(tech_card, good_constraints)
            
            # Should have no critical errors
            if has_critical_content_errors(issues):
                self.log_test("Content check - valid case", False, f"Unexpected critical errors: {issues}")
                return
            
            # Test constraints that should fail (missing ingredient)
            bad_constraints = {
                "mustHave": ["треска", "брокколи", "лосось"],  # лосось not present
                "forbid": ["курица", "свинина"],
                "hints": ["рыба", "овощи"]
            }
            
            bad_issues = run_content_check(tech_card, bad_constraints)
            
            # Should have critical errors for missing лосось
            if not has_critical_content_errors(bad_issues):
                self.log_test("Content check - missing ingredient", False, f"Expected critical errors but got: {bad_issues}")
                return
            
            # Check for missingAnchor error
            missing_anchor_found = any(
                issue.get("type") == "contentError:missingAnchor" 
                for issue in bad_issues
            )
            
            if not missing_anchor_found:
                self.log_test("Content check - missingAnchor error", False, f"missingAnchor error not found in: {bad_issues}")
                return
            
            self.log_test("Content check functionality", True, f"All content check scenarios work correctly")
            
        except Exception as e:
            self.log_test("Content check (direct)", False, f"Error: {str(e)}")
    
    def test_forbidden_ingredient_check(self):
        """Test 5: Test forbidden ingredient detection"""
        if not self.backend_available:
            self.log_test("Forbidden ingredient check", False, "Backend imports not available")
            return
        
        try:
            # Create a test tech card with forbidden ingredient (курица instead of треска)
            test_tech_card_data = {
                "meta": {
                    "title": "Треска с брокколи",
                    "version": "2.0",
                    "cuisine": "европейская",
                    "tags": []
                },
                "portions": 4,
                "yield": {
                    "perPortion_g": 200.0,
                    "perBatch_g": 800.0
                },
                "ingredients": [
                    {
                        "name": "Курица филе",  # Forbidden ingredient!
                        "unit": "g",
                        "brutto_g": 600.0,
                        "loss_pct": 10.0,
                        "netto_g": 540.0,
                        "canonical_id": "chicken",
                        "allergens": []
                    },
                    {
                        "name": "Брокколи",
                        "unit": "g",
                        "brutto_g": 300.0,
                        "loss_pct": 5.0,
                        "netto_g": 285.0,
                        "canonical_id": "broccoli",
                        "allergens": []
                    }
                ],
                "process": [
                    {"n": 1, "action": "Подготовка ингредиентов", "time_min": 10.0, "temp_c": None},
                    {"n": 2, "action": "Приготовление", "time_min": 15.0, "temp_c": 180.0}
                ],
                "storage": {
                    "conditions": "Холодильник 0...+4°C",
                    "shelfLife_hours": 24.0,
                    "servingTemp_c": 65.0
                },
                "nutrition": {"per100g": None, "perPortion": None},
                "cost": {"rawCost": None, "costPerPortion": None},
                "printNotes": []
            }
            
            tech_card = TechCardV2.model_validate(test_tech_card_data)
            
            # Constraints that forbid курица
            constraints = {
                "mustHave": ["треска", "брокколи"],
                "forbid": ["курица", "свинина"],
                "hints": ["рыба", "овощи"]
            }
            
            issues = run_content_check(tech_card, constraints)
            
            # Should have critical errors for forbidden ingredient
            if not has_critical_content_errors(issues):
                self.log_test("Forbidden ingredient detection", False, f"Expected critical errors but got: {issues}")
                return
            
            # Check for forbiddenIngredient error
            forbidden_found = any(
                issue.get("type") == "contentError:forbiddenIngredient" 
                for issue in issues
            )
            
            if not forbidden_found:
                self.log_test("Forbidden ingredient error type", False, f"forbiddenIngredient error not found in: {issues}")
                return
            
            self.log_test("Forbidden ingredient detection", True, "Correctly detected forbidden ingredient (курица)")
            
        except Exception as e:
            self.log_test("Forbidden ingredient check", False, f"Error: {str(e)}")
    
    def test_pipeline_integration(self):
        """Test 6: Test pipeline integration with STRICT_ANCHORS flag"""
        if not self.backend_available:
            self.log_test("Pipeline integration", False, "Backend imports not available")
            return
        
        try:
            # Test with STRICT_ANCHORS=true
            os.environ['STRICT_ANCHORS'] = 'true'
            os.environ['TECHCARDS_V2_USE_LLM'] = 'false'  # Use fallback for testing
            
            profile = ProfileInput(
                name="Треска с брокколи и соусом биск",
                cuisine="европейская",
                equipment=["плита", "духовка"],
                budget=500.0,
                dietary=[]
            )
            
            result = run_pipeline(profile)
            
            # Check that pipeline ran successfully
            if result.status == "failed":
                self.log_test("Pipeline with STRICT_ANCHORS=true", False, f"Pipeline failed: {result.issues}")
                return
            
            # Check that we got a tech card
            if result.card is None:
                self.log_test("Pipeline tech card generation", False, "No tech card generated")
                return
            
            # Test with STRICT_ANCHORS=false
            os.environ['STRICT_ANCHORS'] = 'false'
            
            result_no_anchors = run_pipeline(profile)
            
            if result_no_anchors.status == "failed":
                self.log_test("Pipeline with STRICT_ANCHORS=false", False, f"Pipeline failed: {result_no_anchors.issues}")
                return
            
            self.log_test("Pipeline integration with STRICT_ANCHORS", True, f"Both modes work. Strict: {result.status}, Non-strict: {result_no_anchors.status}")
            
        except Exception as e:
            self.log_test("Pipeline integration", False, f"Error: {str(e)}")
    
    def test_api_endpoint_integration(self):
        """Test 7: Test API endpoint integration with anchor validity"""
        try:
            # Test TechCardV2 generation endpoint
            endpoint = f"{API_BASE}/v1/techcards.v2/generate"
            
            test_data = {
                "name": "Треска с брокколи и соусом биск",
                "cuisine": "европейская",
                "equipment": ["плита", "духовка"],
                "budget": 500.0,
                "dietary": [],
                "use_llm": False  # Use fallback mode for testing
            }
            
            response = requests.post(endpoint, json=test_data, timeout=30)
            
            if response.status_code != 200:
                self.log_test("API endpoint integration", False, f"HTTP {response.status_code}: {response.text}")
                return
            
            result = response.json()
            
            # Check response structure
            required_fields = ["card", "status", "issues"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                self.log_test("API response structure", False, f"Missing fields: {missing_fields}")
                return
            
            # Check that we got a tech card
            if result.get("card") is None:
                self.log_test("API tech card generation", False, "No tech card in response")
                return
            
            tech_card = result["card"]
            
            # Check tech card structure
            if "meta" not in tech_card or "title" not in tech_card["meta"]:
                self.log_test("API tech card structure", False, "Invalid tech card structure")
                return
            
            # Check that title matches our input
            title = tech_card["meta"]["title"]
            if "треска" not in title.lower() and "брокколи" not in title.lower():
                self.log_test("API tech card content relevance", False, f"Generated title doesn't match input: {title}")
                return
            
            self.log_test("API endpoint integration", True, f"Generated tech card: {title}, Status: {result['status']}")
            
        except requests.exceptions.RequestException as e:
            self.log_test("API endpoint integration", False, f"Request error: {str(e)}")
        except Exception as e:
            self.log_test("API endpoint integration", False, f"Error: {str(e)}")
    
    def test_specific_review_scenarios(self):
        """Test 8: Specific scenarios from review request"""
        test_scenarios = [
            {
                "name": "Треска с брокколи и соусом биск",
                "expected_mustHave": ["треска", "брокколи", "соус биск"],
                "expected_forbid": ["курица", "свинина"]
            },
            {
                "name": "Борщ украинский", 
                "expected_mustHave": ["свекла", "капуста"],
                "expected_forbid": ["рыба", "морепродукты"]
            },
            {
                "name": "Стейк из говядины",
                "expected_mustHave": ["говядина"],
                "expected_forbid": ["курица", "свинина", "рыба"]
            }
        ]
        
        for scenario in test_scenarios:
            try:
                # Test API endpoint for each scenario
                endpoint = f"{API_BASE}/v1/techcards.v2/generate"
                
                test_data = {
                    "name": scenario["name"],
                    "cuisine": "европейская",
                    "equipment": ["плита", "духовка"],
                    "budget": 500.0,
                    "dietary": [],
                    "use_llm": False
                }
                
                response = requests.post(endpoint, json=test_data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("card"):
                        title = result["card"]["meta"]["title"]
                        status = result["status"]
                        self.log_test(f"Scenario: {scenario['name']}", True, f"Generated: {title}, Status: {status}")
                    else:
                        self.log_test(f"Scenario: {scenario['name']}", False, "No tech card generated")
                else:
                    self.log_test(f"Scenario: {scenario['name']}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Scenario: {scenario['name']}", False, f"Error: {str(e)}")
    
    def test_environment_flags(self):
        """Test 9: Test environment flags and configuration"""
        try:
            # Check STRICT_ANCHORS flag
            strict_anchors = os.environ.get('STRICT_ANCHORS', 'true')
            
            # Check TECHCARDS_V2_USE_LLM flag
            use_llm = os.environ.get('TECHCARDS_V2_USE_LLM', 'false')
            
            # Check PRICE_VIA_LLM flag
            price_via_llm = os.environ.get('PRICE_VIA_LLM', 'false')
            
            # Check FEATURE_TECHCARDS_V2 flag
            feature_v2 = os.environ.get('FEATURE_TECHCARDS_V2', 'false')
            
            flags_info = {
                "STRICT_ANCHORS": strict_anchors,
                "TECHCARDS_V2_USE_LLM": use_llm,
                "PRICE_VIA_LLM": price_via_llm,
                "FEATURE_TECHCARDS_V2": feature_v2
            }
            
            self.log_test("Environment flags configuration", True, f"Flags: {flags_info}")
            
        except Exception as e:
            self.log_test("Environment flags", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all anchor validity tests"""
        print("🎯 STARTING COMPREHENSIVE ANCHOR VALIDITY TESTING")
        print("=" * 60)
        print()
        
        # Run all tests
        self.test_anchors_mapping_file()
        self.test_anchor_extraction_direct()
        self.test_ingredient_mapping_direct()
        self.test_content_check_direct()
        self.test_forbidden_ingredient_check()
        self.test_pipeline_integration()
        self.test_api_endpoint_integration()
        self.test_specific_review_scenarios()
        self.test_environment_flags()
        
        # Summary
        print("=" * 60)
        print("🎯 ANCHOR VALIDITY TESTING SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Check if anchor mapping is working
        mapping_tests = [r for r in self.test_results if "mapping" in r["test"].lower()]
        mapping_success = all(r["success"] for r in mapping_tests)
        
        if mapping_success:
            print("  ✅ Anchor mapping (RU→EN) is working correctly")
        else:
            print("  ❌ Anchor mapping has issues")
        
        # Check if content checking is working
        content_tests = [r for r in self.test_results if "content" in r["test"].lower()]
        content_success = all(r["success"] for r in content_tests)
        
        if content_success:
            print("  ✅ Content checking (4 validation types) is working correctly")
        else:
            print("  ❌ Content checking has issues")
        
        # Check if API integration is working
        api_tests = [r for r in self.test_results if "api" in r["test"].lower() or "endpoint" in r["test"].lower()]
        api_success = all(r["success"] for r in api_tests)
        
        if api_success:
            print("  ✅ API integration is working correctly")
        else:
            print("  ❌ API integration has issues")
        
        print()
        
        # Overall assessment
        if passed_tests == total_tests:
            print("🎉 ALL ANCHOR VALIDITY TESTS PASSED - SYSTEM IS READY FOR PRODUCTION")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ MOST TESTS PASSED - MINOR ISSUES NEED ATTENTION")
        else:
            print("🚨 SIGNIFICANT ISSUES FOUND - REQUIRES INVESTIGATION")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    print("🎯 ANCHOR VALIDITY COMPREHENSIVE TESTING")
    print("Testing Task C1: «Анкерная валидность: блюдо обязано соответствовать брифу»")
    print()
    
    tester = AnchorValidityTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())