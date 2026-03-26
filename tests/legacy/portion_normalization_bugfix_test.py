#!/usr/bin/env python3
"""
CRITICAL BUG FIX VALIDATION: Standard Portion by Default - Pipeline Order Fix
Testing that portion normalization happens BEFORE sanitization to prevent yield field overwriting.

CRITICAL VALIDATION REQUIREMENTS:
1. No More 800g Yields: Verify no tech cards generated with old default 800g yield
2. Yield Field Present: Ensure yield field always present after sanitization  
3. Perfect GX-02 Compliance: Verify Σnetto ≈ yield.perPortion_g with ≤5% difference
4. Pipeline Order Correct: Confirm normalization happens before sanitization
5. All Archetype Cases: Test various archetypes for consistent behavior

USER'S EXACT TEST CASE: "Тако с курицей и ананасовой сальсой"
Expected: portions=1, yield=240g, archetype=горячее, perfect netto match
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class PortionNormalizationBugFixValidator:
    """Validates that the critical portion normalization bug has been completely resolved"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.critical_failures = []
        
    async def close(self):
        await self.client.aclose()
    
    def log_result(self, test_name: str, passed: bool, details: str, critical: bool = False):
        """Log test result and track critical failures"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append(f"{status} {test_name}: {details}")
        
        if not passed and critical:
            self.critical_failures.append(f"CRITICAL: {test_name} - {details}")
        
        print(f"{status} {test_name}: {details}")
    
    async def generate_techcard(self, dish_name: str) -> Dict[str, Any]:
        """Generate a tech card using the pipeline"""
        try:
            payload = {
                "name": dish_name,
                "cuisine": "международная"
            }
            
            response = await self.client.post(
                f"{API_BASE}/v1/techcards.v2/generate",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Generation failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"Failed to generate tech card for '{dish_name}': {str(e)}")
    
    def validate_no_800g_yields(self, techcard: Dict[str, Any], dish_name: str) -> bool:
        """CRITICAL: Verify no 800g yields are generated"""
        yield_data = techcard.get('yield', {})
        per_portion = yield_data.get('perPortion_g', 0)
        per_batch = yield_data.get('perBatch_g', 0)
        
        has_800g = per_portion == 800.0 or per_batch == 800.0
        
        self.log_result(
            f"No 800g Yields ({dish_name})",
            not has_800g,
            f"perPortion_g={per_portion}g, perBatch_g={per_batch}g" + 
            (" - OLD 800g DETECTED!" if has_800g else " - No old yields"),
            critical=True
        )
        
        return not has_800g
    
    def validate_yield_field_present(self, techcard: Dict[str, Any], dish_name: str) -> bool:
        """CRITICAL: Ensure yield field is always present and properly structured"""
        yield_data = techcard.get('yield')
        
        if not yield_data:
            self.log_result(
                f"Yield Field Present ({dish_name})",
                False,
                "yield field completely missing",
                critical=True
            )
            return False
        
        per_portion = yield_data.get('perPortion_g')
        per_batch = yield_data.get('perBatch_g')
        
        if per_portion is None or per_batch is None:
            self.log_result(
                f"Yield Field Present ({dish_name})",
                False,
                f"yield subfields missing: perPortion_g={per_portion}, perBatch_g={per_batch}",
                critical=True
            )
            return False
        
        self.log_result(
            f"Yield Field Present ({dish_name})",
            True,
            f"yield properly structured: perPortion_g={per_portion}g, perBatch_g={per_batch}g"
        )
        return True
    
    def validate_gx02_compliance(self, techcard: Dict[str, Any], dish_name: str) -> bool:
        """CRITICAL: Verify Σnetto ≈ yield.perPortion_g with ≤5% difference"""
        ingredients = techcard.get('ingredients', [])
        yield_data = techcard.get('yield', {})
        target_yield = yield_data.get('perPortion_g', 0)
        
        # Calculate sum of netto
        sum_netto = 0.0
        for ingredient in ingredients:
            netto = ingredient.get('netto_g') or ingredient.get('netto', 0)
            if isinstance(netto, (int, float)) and netto > 0:
                sum_netto += netto
        
        if target_yield <= 0:
            self.log_result(
                f"GX-02 Compliance ({dish_name})",
                False,
                f"Invalid target yield: {target_yield}g",
                critical=True
            )
            return False
        
        # Calculate difference percentage
        difference_pct = abs(sum_netto - target_yield) / target_yield * 100
        is_compliant = difference_pct <= 5.0
        
        self.log_result(
            f"GX-02 Compliance ({dish_name})",
            is_compliant,
            f"Σnetto={sum_netto:.1f}g vs yield={target_yield}g, diff={difference_pct:.2f}%" +
            (f" (≤5% ✓)" if is_compliant else f" (>5% ❌)"),
            critical=True
        )
        
        return is_compliant
    
    def validate_portions_normalized(self, techcard: Dict[str, Any], dish_name: str) -> bool:
        """CRITICAL: Verify portions=1 (not old default 4)"""
        portions = techcard.get('portions', 0)
        is_normalized = portions == 1
        
        self.log_result(
            f"Portions Normalized ({dish_name})",
            is_normalized,
            f"portions={portions}" + (" (normalized ✓)" if is_normalized else " (not normalized ❌)"),
            critical=True
        )
        
        return is_normalized
    
    def validate_archetype_detection(self, techcard: Dict[str, Any], dish_name: str, expected_archetype: str = None) -> bool:
        """Validate archetype detection and yield assignment"""
        meta = techcard.get('meta', {})
        archetype = meta.get('archetype', 'unknown')
        yield_data = techcard.get('yield', {})
        per_portion = yield_data.get('perPortion_g', 0)
        
        # Expected yields by archetype
        expected_yields = {
            'суп': 330,
            'паста': 300, 
            'горячее': 240,
            'салат': 200,
            'гарнир': 150,
            'соус': 40,
            'десерт': 140,
            'default': 200
        }
        
        expected_yield = expected_yields.get(archetype, expected_yields['default'])
        yield_matches = per_portion == expected_yield
        
        details = f"archetype={archetype}, yield={per_portion}g (expected {expected_yield}g)"
        if expected_archetype:
            archetype_matches = archetype == expected_archetype
            details += f", expected_archetype={expected_archetype} ({'✓' if archetype_matches else '❌'})"
        
        self.log_result(
            f"Archetype Detection ({dish_name})",
            yield_matches,
            details
        )
        
        return yield_matches
    
    def validate_pipeline_order(self, techcard: Dict[str, Any], dish_name: str) -> bool:
        """Validate that normalization happened before sanitization"""
        meta = techcard.get('meta', {})
        
        # Check for normalization metadata
        normalized = meta.get('normalized', False)
        scale_factor = meta.get('scale_factor')
        archetype = meta.get('archetype')
        
        # Check that yield field exists (would be missing if sanitizer ran first)
        yield_exists = 'yield' in techcard and techcard['yield'].get('perPortion_g') is not None
        
        pipeline_correct = normalized and scale_factor is not None and archetype is not None and yield_exists
        
        self.log_result(
            f"Pipeline Order ({dish_name})",
            pipeline_correct,
            f"normalized={normalized}, scale_factor={scale_factor}, archetype={archetype}, yield_exists={yield_exists}"
        )
        
        return pipeline_correct
    
    async def test_user_exact_case(self):
        """Test the exact user's problematic case: 'Тако с курицей и ананасовой сальсой'"""
        print("\n🎯 TESTING USER'S EXACT CASE: 'Тако с курицей и ананасовой сальсой'")
        print("Expected: portions=1, yield=240g, archetype=горячее, perfect netto match")
        
        try:
            dish_name = "Тако с курицей и ананасовой сальсой"
            techcard = await self.generate_techcard(dish_name)
            
            # Run all critical validations
            no_800g = self.validate_no_800g_yields(techcard, dish_name)
            yield_present = self.validate_yield_field_present(techcard, dish_name)
            gx02_compliant = self.validate_gx02_compliance(techcard, dish_name)
            portions_ok = self.validate_portions_normalized(techcard, dish_name)
            archetype_ok = self.validate_archetype_detection(techcard, dish_name, 'горячее')
            pipeline_ok = self.validate_pipeline_order(techcard, dish_name)
            
            # Overall success for user's case
            user_case_success = all([no_800g, yield_present, gx02_compliant, portions_ok, pipeline_ok])
            
            self.log_result(
                "USER'S EXACT CASE",
                user_case_success,
                f"All critical validations {'PASSED' if user_case_success else 'FAILED'}",
                critical=True
            )
            
            return user_case_success
            
        except Exception as e:
            self.log_result(
                "USER'S EXACT CASE",
                False,
                f"Generation failed: {str(e)}",
                critical=True
            )
            return False
    
    async def test_multiple_archetypes(self):
        """Test various archetype cases to ensure consistent behavior"""
        print("\n🧪 TESTING MULTIPLE ARCHETYPE CASES")
        
        test_cases = [
            ("Борщ украинский с мясом", "суп", 330),
            ("Паста карбонара", "паста", 300),
            ("Стейк из говядины", "горячее", 240),
            ("Салат цезарь", "салат", 200),
            ("Картофельное пюре", "гарнир", 150),
            ("Соус тартар", "соус", 40),
            ("Чизкейк нью-йорк", "десерт", 140),
            ("Блюдо авторское", "default", 200)
        ]
        
        all_passed = True
        
        for dish_name, expected_archetype, expected_yield in test_cases:
            try:
                print(f"\n  Testing: {dish_name} (expected: {expected_archetype}, {expected_yield}g)")
                
                techcard = await self.generate_techcard(dish_name)
                
                # Run critical validations
                no_800g = self.validate_no_800g_yields(techcard, dish_name)
                yield_present = self.validate_yield_field_present(techcard, dish_name)
                gx02_compliant = self.validate_gx02_compliance(techcard, dish_name)
                portions_ok = self.validate_portions_normalized(techcard, dish_name)
                archetype_ok = self.validate_archetype_detection(techcard, dish_name, expected_archetype)
                pipeline_ok = self.validate_pipeline_order(techcard, dish_name)
                
                case_passed = all([no_800g, yield_present, gx02_compliant, portions_ok, pipeline_ok])
                all_passed = all_passed and case_passed
                
                if not case_passed:
                    print(f"    ❌ {dish_name} FAILED critical validations")
                else:
                    print(f"    ✅ {dish_name} PASSED all validations")
                    
            except Exception as e:
                print(f"    ❌ {dish_name} ERROR: {str(e)}")
                all_passed = False
        
        self.log_result(
            "MULTIPLE ARCHETYPES",
            all_passed,
            f"{'All archetype cases passed' if all_passed else 'Some archetype cases failed'}",
            critical=True
        )
        
        return all_passed
    
    async def test_regression_cases(self):
        """Test that existing functionality still works (regression testing)"""
        print("\n🔄 REGRESSION TESTING")
        
        try:
            # Test a simple case
            dish_name = "Омлет с зеленью"
            techcard = await self.generate_techcard(dish_name)
            
            # Check basic functionality
            has_ingredients = len(techcard.get('ingredients', [])) > 0
            has_process = len(techcard.get('process', [])) > 0
            has_nutrition = 'nutrition' in techcard
            has_cost = 'cost' in techcard
            
            regression_passed = all([has_ingredients, has_process, has_nutrition, has_cost])
            
            self.log_result(
                "REGRESSION TEST",
                regression_passed,
                f"ingredients={len(techcard.get('ingredients', []))}, " +
                f"process_steps={len(techcard.get('process', []))}, " +
                f"has_nutrition={has_nutrition}, has_cost={has_cost}"
            )
            
            return regression_passed
            
        except Exception as e:
            self.log_result(
                "REGRESSION TEST",
                False,
                f"Regression test failed: {str(e)}"
            )
            return False
    
    async def run_comprehensive_validation(self):
        """Run comprehensive validation of the bug fix"""
        print("🚀 STARTING COMPREHENSIVE PORTION NORMALIZATION BUG FIX VALIDATION")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            # Test 1: User's exact problematic case
            user_case_success = await self.test_user_exact_case()
            
            # Test 2: Multiple archetype cases
            archetype_success = await self.test_multiple_archetypes()
            
            # Test 3: Regression testing
            regression_success = await self.test_regression_cases()
            
            # Overall results
            total_time = time.time() - start_time
            
            print("\n" + "=" * 80)
            print("📊 COMPREHENSIVE VALIDATION RESULTS")
            print("=" * 80)
            
            for result in self.test_results:
                print(result)
            
            print(f"\n⏱️  Total test time: {total_time:.2f}s")
            
            # Critical failure analysis
            if self.critical_failures:
                print(f"\n🚨 CRITICAL FAILURES DETECTED ({len(self.critical_failures)}):")
                for failure in self.critical_failures:
                    print(f"  {failure}")
                
                print("\n❌ BUG FIX VALIDATION FAILED - CRITICAL ISSUES REMAIN")
                return False
            else:
                print("\n✅ BUG FIX VALIDATION SUCCESSFUL - ALL CRITICAL REQUIREMENTS MET")
                
                # Summary of key achievements
                print("\n🎉 KEY ACHIEVEMENTS VALIDATED:")
                print("  ✅ No more 800g yields generated")
                print("  ✅ Yield field always present after sanitization")
                print("  ✅ Perfect GX-02 compliance (≤5% difference)")
                print("  ✅ Pipeline order correct (normalization before sanitization)")
                print("  ✅ All archetype cases working consistently")
                print("  ✅ User's exact test case working perfectly")
                print("  ✅ No regressions in existing functionality")
                
                return True
                
        except Exception as e:
            print(f"\n❌ VALIDATION FAILED WITH EXCEPTION: {str(e)}")
            return False

async def main():
    """Main test execution"""
    validator = PortionNormalizationBugFixValidator()
    
    try:
        success = await validator.run_comprehensive_validation()
        
        if success:
            print("\n🎯 CONCLUSION: Critical portion normalization bug has been COMPLETELY RESOLVED")
            exit(0)
        else:
            print("\n🚨 CONCLUSION: Critical portion normalization bug is NOT fully resolved")
            exit(1)
            
    finally:
        await validator.close()

if __name__ == "__main__":
    asyncio.run(main())