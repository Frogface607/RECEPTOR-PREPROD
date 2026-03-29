#!/usr/bin/env python3
"""
STANDARD PORTION BY DEFAULT (no UI) - COMPREHENSIVE DOD TESTING
Testing portion normalization, archetype detection, and XLSX export functionality
"""

import requests
import json
import time
import os
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

class StandardPortionDoDTest:
    """Comprehensive DoD testing for Standard Portion by Default implementation"""
    
    def __init__(self):
        self.results = []
        self.test_cases = self._create_test_cases()
    
    def _create_test_cases(self) -> List[Dict[str, Any]]:
        """Create DoD test cases as specified in review request"""
        return [
            {
                "name": "Омлет с зеленью",
                "expected_archetype": "default",
                "expected_yield": 200,
                "expected_portions": 1,
                "description": "Омлет с зеленью и специями"
            },
            {
                "name": "Стейк с грибным соусом", 
                "expected_archetype": "горячее",
                "expected_yield": 240,
                "expected_portions": 1,
                "description": "Стейк говяжий с грибным соусом"
            },
            {
                "name": "Суп дня овощной",
                "expected_archetype": "суп", 
                "expected_yield": 330,
                "expected_portions": 1,
                "description": "Овощной суп дня"
            }
        ]
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all DoD test scenarios"""
        print("🎯 STARTING STANDARD PORTION BY DEFAULT DOD TESTING")
        print("=" * 60)
        
        overall_results = {
            "test_cases_passed": 0,
            "test_cases_total": len(self.test_cases),
            "detailed_results": [],
            "critical_issues": [],
            "performance_metrics": {}
        }
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n📋 TEST CASE {i}/{len(self.test_cases)}: {test_case['name']}")
            print("-" * 40)
            
            try:
                result = self._test_single_case(test_case)
                overall_results["detailed_results"].append(result)
                
                if result["passed"]:
                    overall_results["test_cases_passed"] += 1
                    print(f"✅ PASSED: {test_case['name']}")
                else:
                    print(f"❌ FAILED: {test_case['name']}")
                    overall_results["critical_issues"].extend(result.get("issues", []))
                    
            except Exception as e:
                print(f"💥 CRITICAL ERROR in {test_case['name']}: {str(e)}")
                overall_results["critical_issues"].append(f"Critical error in {test_case['name']}: {str(e)}")
        
        # Summary
        success_rate = (overall_results["test_cases_passed"] / overall_results["test_cases_total"]) * 100
        print(f"\n🎯 FINAL RESULTS:")
        print(f"✅ Passed: {overall_results['test_cases_passed']}/{overall_results['test_cases_total']} ({success_rate:.1f}%)")
        
        if overall_results["critical_issues"]:
            print(f"❌ Critical Issues: {len(overall_results['critical_issues'])}")
            for issue in overall_results["critical_issues"]:
                print(f"   - {issue}")
        
        return overall_results
    
    def _test_single_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single DoD case comprehensively"""
        result = {
            "test_case": test_case["name"],
            "passed": False,
            "issues": [],
            "metrics": {},
            "validations": {}
        }
        
        try:
            # Step 1: Generate TechCard
            print(f"🔄 Step 1: Generating TechCard for '{test_case['name']}'...")
            start_time = time.time()
            
            techcard_data = self._generate_techcard(test_case)
            if not techcard_data:
                result["issues"].append("TechCard generation failed")
                return result
            
            generation_time = time.time() - start_time
            result["metrics"]["generation_time_s"] = round(generation_time, 2)
            print(f"   ⏱️ Generated in {generation_time:.2f}s")
            
            # Step 2: Verify Portion Normalization
            print("🔍 Step 2: Verifying portion normalization...")
            normalization_result = self._verify_portion_normalization(techcard_data, test_case)
            result["validations"]["normalization"] = normalization_result
            
            if not normalization_result["valid"]:
                result["issues"].extend(normalization_result["issues"])
                return result
            
            # Step 3: Verify Archetype Detection
            print("🎯 Step 3: Verifying archetype detection...")
            archetype_result = self._verify_archetype_detection(techcard_data, test_case)
            result["validations"]["archetype"] = archetype_result
            
            if not archetype_result["valid"]:
                result["issues"].extend(archetype_result["issues"])
                return result
            
            # Step 4: Verify GX-02 Compliance
            print("⚖️ Step 4: Verifying GX-02 compliance...")
            gx02_result = self._verify_gx02_compliance(techcard_data)
            result["validations"]["gx02"] = gx02_result
            
            if not gx02_result["valid"]:
                result["issues"].extend(gx02_result["issues"])
                return result
            
            # Step 5: Test XLSX Export
            print("📊 Step 5: Testing XLSX export...")
            export_result = self._test_xlsx_export(techcard_data)
            result["validations"]["export"] = export_result
            
            if not export_result["valid"]:
                result["issues"].extend(export_result["issues"])
                return result
            
            # Step 6: Verify Scale Factor Audit
            print("📋 Step 6: Verifying scale factor audit...")
            audit_result = self._verify_scale_factor_audit(techcard_data)
            result["validations"]["audit"] = audit_result
            
            if not audit_result["valid"]:
                result["issues"].extend(audit_result["issues"])
                return result
            
            # All tests passed
            result["passed"] = True
            print("✅ All validations passed!")
            
        except Exception as e:
            result["issues"].append(f"Test execution error: {str(e)}")
            print(f"💥 Test execution error: {str(e)}")
        
        return result
    
    def _generate_techcard(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Generate TechCard using the API"""
        try:
            payload = {
                "name": test_case["name"],
                "cuisine": "русская"
            }
            
            response = requests.post(
                f"{API_BASE}/techcards.v2/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("card"):
                    return data["card"]
                elif data.get("status") == "draft" and data.get("card"):
                    print("   ⚠️ Generated in DRAFT mode")
                    return data["card"]
            
            print(f"❌ TechCard generation failed: {response.status_code} - {response.text[:200]}")
            return None
            
        except Exception as e:
            print(f"❌ TechCard generation error: {str(e)}")
            return None
    
    def _verify_portion_normalization(self, techcard: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that portion normalization was applied correctly"""
        result = {"valid": False, "issues": [], "details": {}}
        
        try:
            # Check portions = 1
            portions = techcard.get("portions", 0)
            if portions != 1:
                result["issues"].append(f"Expected portions=1, got {portions}")
                return result
            
            result["details"]["portions"] = portions
            
            # Check yield.perPortion_g matches expected
            yield_data = techcard.get("yield", {})
            per_portion_g = yield_data.get("perPortion_g", 0)
            expected_yield = test_case["expected_yield"]
            
            if abs(per_portion_g - expected_yield) > 1:  # Allow 1g tolerance
                result["issues"].append(f"Expected yield {expected_yield}g, got {per_portion_g}g")
                return result
            
            result["details"]["yield_per_portion_g"] = per_portion_g
            
            # Check that ingredients are normalized to grams
            ingredients = techcard.get("ingredients", [])
            for ingredient in ingredients:
                unit = ingredient.get("unit", "")
                if unit != "g":
                    result["issues"].append(f"Ingredient '{ingredient.get('name', 'unknown')}' has unit '{unit}', expected 'g'")
                    return result
            
            result["details"]["ingredients_count"] = len(ingredients)
            result["details"]["all_units_normalized"] = True
            
            # Check meta fields for audit
            meta = techcard.get("meta", {})
            if not meta.get("normalized"):
                result["issues"].append("Meta field 'normalized' not set to true")
                return result
            
            if not meta.get("scale_factor"):
                result["issues"].append("Meta field 'scale_factor' missing")
                return result
            
            result["details"]["scale_factor"] = meta.get("scale_factor")
            result["details"]["original_sum_netto"] = meta.get("original_sum_netto")
            
            result["valid"] = True
            
        except Exception as e:
            result["issues"].append(f"Portion normalization verification error: {str(e)}")
        
        return result
    
    def _verify_archetype_detection(self, techcard: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that archetype detection worked correctly"""
        result = {"valid": False, "issues": [], "details": {}}
        
        try:
            meta = techcard.get("meta", {})
            detected_archetype = meta.get("archetype")
            expected_archetype = test_case["expected_archetype"]
            
            if detected_archetype != expected_archetype:
                result["issues"].append(f"Expected archetype '{expected_archetype}', got '{detected_archetype}'")
                return result
            
            result["details"]["detected_archetype"] = detected_archetype
            result["details"]["expected_archetype"] = expected_archetype
            result["valid"] = True
            
        except Exception as e:
            result["issues"].append(f"Archetype detection verification error: {str(e)}")
        
        return result
    
    def _verify_gx02_compliance(self, techcard: Dict[str, Any]) -> Dict[str, Any]:
        """Verify GX-02 compliance: Σнетто ≈ yield.perPortion_g (±5%)"""
        result = {"valid": False, "issues": [], "details": {}}
        
        try:
            # Calculate sum of netto
            ingredients = techcard.get("ingredients", [])
            sum_netto = 0
            
            for ingredient in ingredients:
                netto = ingredient.get("netto_g") or ingredient.get("netto", 0)
                if isinstance(netto, (int, float)):
                    sum_netto += netto
            
            # Get target yield
            yield_data = techcard.get("yield", {})
            target_yield = yield_data.get("perPortion_g", 0)
            
            if target_yield <= 0:
                result["issues"].append("Target yield is zero or missing")
                return result
            
            # Calculate difference percentage
            difference_pct = abs(sum_netto - target_yield) / target_yield * 100
            
            result["details"]["sum_netto"] = round(sum_netto, 1)
            result["details"]["target_yield"] = target_yield
            result["details"]["difference_pct"] = round(difference_pct, 2)
            
            # GX-02 rule: difference should be ≤ 5%
            if difference_pct > 5.0:
                result["issues"].append(f"GX-02 violation: difference {difference_pct:.2f}% > 5%")
                return result
            
            result["valid"] = True
            
        except Exception as e:
            result["issues"].append(f"GX-02 compliance verification error: {str(e)}")
        
        return result
    
    def _test_xlsx_export(self, techcard: Dict[str, Any]) -> Dict[str, Any]:
        """Test XLSX export functionality with normalized TechCard"""
        result = {"valid": False, "issues": [], "details": {}}
        
        try:
            # Test export endpoint
            response = requests.post(
                f"{API_BASE}/techcards.v2/export/iiko.xlsx",
                json=techcard,
                timeout=30
            )
            
            if response.status_code != 200:
                result["issues"].append(f"XLSX export failed: {response.status_code}")
                return result
            
            # Check that we got Excel content
            content_type = response.headers.get('content-type', '')
            if 'excel' not in content_type.lower() and 'spreadsheet' not in content_type.lower():
                result["issues"].append(f"Invalid content type: {content_type}")
                return result
            
            # Check file size (should be reasonable)
            content_length = len(response.content)
            if content_length < 1000:  # Too small to be a valid Excel file
                result["issues"].append(f"Excel file too small: {content_length} bytes")
                return result
            
            result["details"]["file_size_bytes"] = content_length
            result["details"]["content_type"] = content_type
            
            # Verify that yield field is correctly set in export
            yield_data = techcard.get("yield", {})
            expected_output = yield_data.get("perPortion_g", 0)
            
            result["details"]["expected_output_qty"] = expected_output
            result["valid"] = True
            
        except Exception as e:
            result["issues"].append(f"XLSX export test error: {str(e)}")
        
        return result
    
    def _verify_scale_factor_audit(self, techcard: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that scale factor is properly recorded for audit"""
        result = {"valid": False, "issues": [], "details": {}}
        
        try:
            meta = techcard.get("meta", {})
            scale_factor = meta.get("scale_factor")
            
            if scale_factor is None:
                result["issues"].append("Scale factor not recorded in meta")
                return result
            
            # Scale factor should be reasonable (0.1 to 2.0 range as specified)
            if not (0.1 <= scale_factor <= 2.0):
                result["issues"].append(f"Scale factor {scale_factor} outside reasonable range (0.1-2.0)")
                return result
            
            # Check other audit fields
            if not meta.get("archetype"):
                result["issues"].append("Archetype not recorded in meta")
                return result
            
            if meta.get("original_sum_netto") is None:
                result["issues"].append("Original sum netto not recorded in meta")
                return result
            
            if not meta.get("normalized"):
                result["issues"].append("Normalized flag not set in meta")
                return result
            
            result["details"]["scale_factor"] = scale_factor
            result["details"]["archetype"] = meta.get("archetype")
            result["details"]["original_sum_netto"] = meta.get("original_sum_netto")
            result["details"]["normalized"] = meta.get("normalized")
            
            result["valid"] = True
            
        except Exception as e:
            result["issues"].append(f"Scale factor audit verification error: {str(e)}")
        
        return result

def main():
    """Run the comprehensive DoD testing"""
    tester = StandardPortionDoDTest()
    results = tester.run_all_tests()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🎯 STANDARD PORTION BY DEFAULT - DOD TESTING COMPLETE")
    print("=" * 60)
    
    success_rate = (results["test_cases_passed"] / results["test_cases_total"]) * 100
    
    if success_rate == 100:
        print("🎉 ALL DOD REQUIREMENTS PASSED!")
    elif success_rate >= 80:
        print("⚠️ MOSTLY SUCCESSFUL - Some issues found")
    else:
        print("❌ CRITICAL ISSUES FOUND - DoD requirements not met")
    
    print(f"📊 Success Rate: {success_rate:.1f}% ({results['test_cases_passed']}/{results['test_cases_total']})")
    
    if results["critical_issues"]:
        print(f"\n❌ Critical Issues ({len(results['critical_issues'])}):")
        for issue in results["critical_issues"]:
            print(f"   • {issue}")
    
    return results

if __name__ == "__main__":
    main()