#!/usr/bin/env python3
"""
GX-02 Enhanced Auto-mapping API Backend Testing
Testing the newly implemented GX-02 Enhanced Auto-mapping API endpoints and RU-synonyms functionality

Focus Areas:
1. Enhanced Auto-mapping Endpoint: POST /api/v1/techcards.v2/mapping/enhanced
2. Mapping Application Endpoint: POST /api/v1/techcards.v2/mapping/apply  
3. RU-Synonyms Endpoint: GET /api/v1/techcards.v2/mapping/synonyms
4. Russian ingredient matching with confidence scoring
5. Coverage calculation and statistics
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class GX02EnhancedMappingTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    async def run_all_tests(self):
        """Run all GX-02 Enhanced Auto-mapping tests"""
        print("🧪 GX-02 Enhanced Auto-mapping API Testing Started")
        print("=" * 60)
        
        # Test 1: RU-Synonyms Endpoint
        await self.test_ru_synonyms_endpoint()
        
        # Test 2: Enhanced Auto-mapping with Russian Ingredients
        await self.test_enhanced_mapping_russian_ingredients()
        
        # Test 3: Confidence Scoring Test
        await self.test_confidence_scoring()
        
        # Test 4: Coverage Calculation
        await self.test_coverage_calculation()
        
        # Test 5: Auto-apply Functionality
        await self.test_auto_apply_functionality()
        
        # Test 6: Mapping Application Endpoint
        await self.test_mapping_application()
        
        # Test 7: Error Handling
        await self.test_error_handling()
        
        # Summary
        self.print_summary()
        
    async def test_ru_synonyms_endpoint(self):
        """Test GET /api/v1/techcards.v2/mapping/synonyms"""
        print("\n📚 Test 1: RU-Synonyms Endpoint")
        print("-" * 40)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/v1/techcards.v2/mapping/synonyms")
                
                self.total_tests += 1
                test_id = "1.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    required_fields = ["status", "synonyms_preview", "total_groups", "message"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields and data.get("status") == "success":
                        synonyms_preview = data.get("synonyms_preview", {})
                        total_groups = data.get("total_groups", 0)
                        
                        # Verify we have 30+ synonym groups as specified
                        if total_groups >= 30:
                            # Check for key Russian ingredients
                            key_ingredients = ["яйца", "молоко", "говядина", "лук"]
                            found_ingredients = [ing for ing in key_ingredients if ing in synonyms_preview]
                            
                            if len(found_ingredients) >= 2:  # At least 2 key ingredients found
                                self.passed_tests += 1
                                print(f"✅ {test_id}: RU-Synonyms endpoint - PASSED")
                                print(f"   Total groups: {total_groups}")
                                print(f"   Preview items: {len(synonyms_preview)}")
                                print(f"   Key ingredients found: {found_ingredients}")
                                
                                # Test specific synonym examples
                                if "яйца" in synonyms_preview:
                                    egg_synonyms = synonyms_preview["яйца"]
                                    if "яйцо куриное" in egg_synonyms:
                                        print(f"   ✓ яйца → яйцо куриное mapping confirmed")
                                
                                if "молоко" in synonyms_preview:
                                    milk_synonyms = synonyms_preview["молоко"]
                                    if "молоко 3.2%" in milk_synonyms:
                                        print(f"   ✓ молоко → молоко 3.2% mapping confirmed")
                            else:
                                print(f"❌ {test_id}: Key Russian ingredients not found in synonyms")
                                print(f"   Expected: {key_ingredients}, Found: {found_ingredients}")
                        else:
                            print(f"❌ {test_id}: Insufficient synonym groups - expected ≥30, got {total_groups}")
                    else:
                        print(f"❌ {test_id}: Invalid response structure - missing fields: {missing_fields}")
                else:
                    print(f"❌ {test_id}: Synonyms endpoint error - {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Synonyms endpoint exception - {str(e)}")
    
    async def test_enhanced_mapping_russian_ingredients(self):
        """Test enhanced auto-mapping with Russian ingredient names"""
        print("\n🇷🇺 Test 2: Enhanced Auto-mapping with Russian Ingredients")
        print("-" * 40)
        
        # Create test TechCard with Russian ingredients
        test_techcard = {
            "meta": {
                "title": "Тестовое блюдо с русскими ингредиентами",
                "description": "Блюдо для тестирования русских синонимов"
            },
            "ingredients": [
                {"name": "яйца", "brutto_g": 100, "unit": "г"},
                {"name": "молоко", "brutto_g": 200, "unit": "мл"},
                {"name": "говядина", "brutto_g": 300, "unit": "г"},
                {"name": "лук репчатый", "brutto_g": 50, "unit": "г"}
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "techcard": test_techcard,
                    "organization_id": "default"
                }
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                    json=payload
                )
                
                self.total_tests += 1
                test_id = "2.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        mapping_results = data.get("mapping_results", {})
                        results = mapping_results.get("results", [])
                        stats = mapping_results.get("stats", {})
                        
                        # Check if we found matches for Russian ingredients
                        matched_ingredients = [r["ingredient_name"] for r in results]
                        russian_matches = [ing for ing in ["яйца", "молоко", "говядина", "лук репчатый"] 
                                         if ing in matched_ingredients]
                        
                        if len(russian_matches) >= 2:  # At least 2 Russian ingredients matched
                            self.passed_tests += 1
                            print(f"✅ {test_id}: Russian ingredients mapping - PASSED")
                            print(f"   Total ingredients: {stats.get('total', 0)}")
                            print(f"   Matched ingredients: {len(results)}")
                            print(f"   Russian matches: {russian_matches}")
                            
                            # Check confidence scores and match types
                            for result in results:
                                if result["ingredient_name"] in russian_matches:
                                    confidence = result.get("confidence", 0)
                                    match_type = result.get("match_type", "unknown")
                                    suggestion = result.get("suggestion", {})
                                    print(f"   {result['ingredient_name']}: {confidence:.2f} ({match_type}) → {suggestion.get('name', 'N/A')}")
                        else:
                            print(f"❌ {test_id}: Insufficient Russian ingredient matches")
                            print(f"   Expected matches for: яйца, молоко, говядина, лук репчатый")
                            print(f"   Found matches: {matched_ingredients}")
                    else:
                        print(f"❌ {test_id}: Enhanced mapping failed - status: {data.get('status')}")
                        print(f"   Message: {data.get('mapping_results', {}).get('message', 'No message')}")
                else:
                    print(f"❌ {test_id}: Enhanced mapping API error - {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Enhanced mapping exception - {str(e)}")
    
    async def test_confidence_scoring(self):
        """Test confidence scoring thresholds (≥0.90 auto-accept, 0.70-0.89 review)"""
        print("\n🎯 Test 3: Confidence Scoring Test")
        print("-" * 40)
        
        # Create test with ingredients that should have different confidence levels
        test_techcard = {
            "meta": {"title": "Confidence Scoring Test"},
            "ingredients": [
                {"name": "яйцо С1", "brutto_g": 50, "unit": "шт"},  # Should match "яйца" with high confidence
                {"name": "молоко свежее", "brutto_g": 100, "unit": "мл"},  # Should match "молоко" 
                {"name": "неизвестный ингредиент xyz", "brutto_g": 10, "unit": "г"}  # Should not match
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "techcard": test_techcard,
                    "organization_id": "default"
                }
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                    json=payload
                )
                
                self.total_tests += 1
                test_id = "3.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        mapping_results = data.get("mapping_results", {})
                        results = mapping_results.get("results", [])
                        stats = mapping_results.get("stats", {})
                        
                        # Check confidence scoring categories
                        auto_accept_count = stats.get("auto_accept", 0)
                        review_count = stats.get("review", 0)
                        no_match_count = stats.get("no_match", 0)
                        
                        # Verify confidence thresholds are working
                        confidence_test_passed = False
                        for result in results:
                            confidence = result.get("confidence", 0)
                            status = result.get("status", "")
                            
                            # Check threshold logic
                            if confidence >= 0.90 and status == "auto_accept":
                                confidence_test_passed = True
                                print(f"   ✓ High confidence: {result['ingredient_name']} ({confidence:.2f}) → auto_accept")
                            elif 0.70 <= confidence < 0.90 and status == "review":
                                confidence_test_passed = True
                                print(f"   ✓ Medium confidence: {result['ingredient_name']} ({confidence:.2f}) → review")
                        
                        if confidence_test_passed or (auto_accept_count + review_count) > 0:
                            self.passed_tests += 1
                            print(f"✅ {test_id}: Confidence scoring - PASSED")
                            print(f"   Auto-accept: {auto_accept_count}")
                            print(f"   Review: {review_count}")
                            print(f"   No match: {no_match_count}")
                        else:
                            print(f"❌ {test_id}: Confidence scoring logic not working properly")
                    else:
                        print(f"❌ {test_id}: Confidence scoring test failed - {data.get('status')}")
                else:
                    print(f"❌ {test_id}: Confidence scoring API error - {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Confidence scoring exception - {str(e)}")
    
    async def test_coverage_calculation(self):
        """Test coverage calculation and statistics"""
        print("\n📊 Test 4: Coverage Calculation")
        print("-" * 40)
        
        # Create test with mixed ingredients (some with existing SKUs)
        test_techcard = {
            "meta": {"title": "Coverage Test"},
            "ingredients": [
                {"name": "говядина", "brutto_g": 200, "unit": "г"},  # Should find match
                {"name": "лук", "brutto_g": 50, "unit": "г"},  # Should find match
                {"name": "соль", "brutto_g": 5, "unit": "г", "skuId": "EXISTING_SKU_001"},  # Already has SKU
                {"name": "редкий ингредиент", "brutto_g": 10, "unit": "г"}  # Unlikely to match
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "techcard": test_techcard,
                    "organization_id": "default"
                }
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                    json=payload
                )
                
                self.total_tests += 1
                test_id = "4.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        mapping_results = data.get("mapping_results", {})
                        coverage = mapping_results.get("coverage", {})
                        
                        # Check coverage calculation fields
                        required_coverage_fields = [
                            "total_ingredients", "current_with_sku", "auto_accept_available",
                            "review_available", "potential_coverage", "potential_coverage_pct"
                        ]
                        
                        missing_coverage_fields = [field for field in required_coverage_fields 
                                                 if field not in coverage]
                        
                        if not missing_coverage_fields:
                            total_ingredients = coverage.get("total_ingredients", 0)
                            current_with_sku = coverage.get("current_with_sku", 0)
                            potential_coverage_pct = coverage.get("potential_coverage_pct", 0)
                            
                            # Verify calculations make sense
                            if (total_ingredients == 4 and  # 4 test ingredients
                                current_with_sku >= 1 and  # At least 1 existing SKU
                                0 <= potential_coverage_pct <= 100):  # Valid percentage
                                
                                self.passed_tests += 1
                                print(f"✅ {test_id}: Coverage calculation - PASSED")
                                print(f"   Total ingredients: {total_ingredients}")
                                print(f"   Current with SKU: {current_with_sku}")
                                print(f"   Auto-accept available: {coverage.get('auto_accept_available', 0)}")
                                print(f"   Review available: {coverage.get('review_available', 0)}")
                                print(f"   Potential coverage: {potential_coverage_pct}%")
                            else:
                                print(f"❌ {test_id}: Coverage calculation values incorrect")
                                print(f"   Coverage data: {coverage}")
                        else:
                            print(f"❌ {test_id}: Missing coverage fields: {missing_coverage_fields}")
                    else:
                        print(f"❌ {test_id}: Coverage test failed - {data.get('status')}")
                else:
                    print(f"❌ {test_id}: Coverage API error - {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Coverage calculation exception - {str(e)}")
    
    async def test_auto_apply_functionality(self):
        """Test auto_apply parameter functionality"""
        print("\n⚡ Test 5: Auto-apply Functionality")
        print("-" * 40)
        
        test_techcard = {
            "meta": {"title": "Auto-apply Test"},
            "ingredients": [
                {"name": "яйца", "brutto_g": 100, "unit": "г"},
                {"name": "молоко", "brutto_g": 200, "unit": "мл"}
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "techcard": test_techcard,
                    "organization_id": "default",
                    "auto_apply": True  # Enable auto-apply
                }
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                    json=payload
                )
                
                self.total_tests += 1
                test_id = "5.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        auto_applied = data.get("auto_applied", False)
                        updated_techcard = data.get("mapping_results", {}).get("updated_techcard")
                        
                        if auto_applied and updated_techcard:
                            # Check if SKUs were applied to ingredients
                            updated_ingredients = updated_techcard.get("ingredients", [])
                            ingredients_with_sku = [ing for ing in updated_ingredients if ing.get("skuId")]
                            
                            if len(ingredients_with_sku) > 0:
                                self.passed_tests += 1
                                print(f"✅ {test_id}: Auto-apply functionality - PASSED")
                                print(f"   Auto-applied: {auto_applied}")
                                print(f"   Ingredients with SKU: {len(ingredients_with_sku)}")
                                
                                for ing in ingredients_with_sku:
                                    print(f"   {ing['name']} → SKU: {ing['skuId']}")
                            else:
                                print(f"❌ {test_id}: Auto-apply enabled but no SKUs applied")
                        else:
                            print(f"❌ {test_id}: Auto-apply not working - auto_applied: {auto_applied}")
                    else:
                        print(f"❌ {test_id}: Auto-apply test failed - {data.get('status')}")
                else:
                    print(f"❌ {test_id}: Auto-apply API error - {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Auto-apply exception - {str(e)}")
    
    async def test_mapping_application(self):
        """Test POST /api/v1/techcards.v2/mapping/apply"""
        print("\n🔧 Test 6: Mapping Application Endpoint")
        print("-" * 40)
        
        test_techcard = {
            "meta": {"title": "Mapping Application Test"},
            "ingredients": [
                {"name": "говядина", "brutto_g": 200, "unit": "г"},
                {"name": "лук", "brutto_g": 50, "unit": "г"}
            ]
        }
        
        # Simulate user mapping decisions
        mapping_decisions = {
            "говядина": {
                "action": "accept",
                "suggestion": {
                    "sku_id": "TEST_BEEF_SKU_001",
                    "name": "Говядина тестовая",
                    "unit": "г"
                }
            },
            "лук": {
                "action": "reject"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "techcard": test_techcard,
                    "mapping_decisions": mapping_decisions,
                    "organization_id": "default"
                }
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/mapping/apply",
                    json=payload
                )
                
                self.total_tests += 1
                test_id = "6.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        updated_techcard = data.get("updated_techcard", {})
                        applied_count = data.get("applied_count", 0)
                        
                        # Check if accepted mapping was applied
                        updated_ingredients = updated_techcard.get("ingredients", [])
                        beef_ingredient = next((ing for ing in updated_ingredients if ing["name"] == "говядина"), None)
                        onion_ingredient = next((ing for ing in updated_ingredients if ing["name"] == "лук"), None)
                        
                        if (beef_ingredient and beef_ingredient.get("skuId") == "TEST_BEEF_SKU_001" and
                            onion_ingredient and not onion_ingredient.get("skuId") and
                            applied_count == 1):
                            
                            self.passed_tests += 1
                            print(f"✅ {test_id}: Mapping application - PASSED")
                            print(f"   Applied count: {applied_count}")
                            print(f"   Beef SKU applied: {beef_ingredient.get('skuId')}")
                            print(f"   Onion SKU (should be None): {onion_ingredient.get('skuId')}")
                        else:
                            print(f"❌ {test_id}: Mapping application logic incorrect")
                            print(f"   Expected: beef with SKU, onion without SKU")
                            print(f"   Got: beef SKU={beef_ingredient.get('skuId') if beef_ingredient else 'N/A'}, onion SKU={onion_ingredient.get('skuId') if onion_ingredient else 'N/A'}")
                    else:
                        print(f"❌ {test_id}: Mapping application failed - {data.get('status')}")
                else:
                    print(f"❌ {test_id}: Mapping application API error - {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Mapping application exception - {str(e)}")
    
    async def test_error_handling(self):
        """Test error handling for various invalid inputs"""
        print("\n🚨 Test 7: Error Handling")
        print("-" * 40)
        
        error_test_cases = [
            {
                "name": "Missing techcard data",
                "payload": {},
                "expected_status": 400
            },
            {
                "name": "Empty ingredients list",
                "payload": {"techcard": {"ingredients": []}},
                "expected_status": 400
            },
            {
                "name": "Invalid organization_id",
                "payload": {
                    "techcard": {"ingredients": [{"name": "test", "brutto_g": 100}]},
                    "organization_id": "nonexistent_org"
                },
                "expected_status": 200  # Should handle gracefully
            }
        ]
        
        for i, test_case in enumerate(error_test_cases, 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                        json=test_case["payload"]
                    )
                    
                    self.total_tests += 1
                    test_id = f"7.{i}"
                    
                    if response.status_code == test_case["expected_status"]:
                        self.passed_tests += 1
                        print(f"✅ {test_id}: {test_case['name']} - PASSED")
                        print(f"   Expected status: {test_case['expected_status']}, Got: {response.status_code}")
                    else:
                        print(f"❌ {test_id}: {test_case['name']} - FAILED")
                        print(f"   Expected status: {test_case['expected_status']}, Got: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ {test_id}: {test_case['name']} - EXCEPTION: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 GX-02 Enhanced Auto-mapping Test Summary")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: GX-02 Enhanced Auto-mapping is working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD: Most GX-02 features working, minor issues detected")
        elif success_rate >= 50:
            print("⚠️ PARTIAL: Some GX-02 features working, needs improvement")
        else:
            print("❌ CRITICAL: GX-02 Enhanced Auto-mapping has significant issues")
        
        print("\n🔍 Key Validation Targets:")
        print("✓ RU-synonyms dictionary loaded (30+ groups)")
        print("✓ Russian ingredient matching (яйца → яйцо куриное)")
        print("✓ Confidence scoring (≥0.90 auto-accept, 0.70-0.89 review)")
        print("✓ Coverage calculation and statistics")
        print("✓ Auto-apply parameter functionality")
        print("✓ Mapping application endpoint")
        print("✓ Error handling for invalid inputs")
        
        return success_rate >= 75  # Return True if tests are mostly passing

async def main():
    """Main test execution"""
    tester = GX02EnhancedMappingTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())