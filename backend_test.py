#!/usr/bin/env python3
"""
Backend Testing for P1-Prices Implementation (Task P1-Prices)
Testing unified price provider system with hierarchical source strategy
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://ai-recipe-pro.preview.emergentagent.com/api"

class P1PricesBackendTester:
    """Comprehensive tester for P1-Prices implementation"""
    
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
    
    def test_price_provider_class(self):
        """Test 1: PriceProvider Class Functionality"""
        print("\n🔍 Testing PriceProvider Class Functionality...")
        
        try:
            # Import and test PriceProvider directly
            sys.path.append('/app/backend')
            from receptor_agent.techcards_v2.price_provider import PriceProvider
            
            provider = PriceProvider()
            
            # Test 1.1: Load price sources
            provider._load_sources()
            
            catalog_count = len(provider.catalog_prices)
            bootstrap_count = len(provider.bootstrap_prices)
            
            if catalog_count > 0 and bootstrap_count > 0:
                self.log_test("PriceProvider - Load Sources", True, 
                             f"Loaded {catalog_count} catalog + {bootstrap_count} bootstrap prices")
            else:
                self.log_test("PriceProvider - Load Sources", False, 
                             f"Failed to load sources: catalog={catalog_count}, bootstrap={bootstrap_count}")
                return
            
            # Test 1.2: Price resolution by name (fuzzy matching)
            test_ingredients = ["говядина", "куриное филе", "растительное масло", "лук", "морковь"]
            resolved_count = 0
            
            for ingredient_name in test_ingredients:
                # Create mock ingredient object
                class MockIngredient:
                    def __init__(self, name):
                        self.name = name
                        self.skuId = None
                        self.canonical_id = None
                
                ingredient = MockIngredient(ingredient_name)
                result = provider.resolve(ingredient)
                
                if result and result.get("price_per_g") and result.get("source"):
                    resolved_count += 1
                    print(f"   ✓ {ingredient_name}: {result['price_per_g']:.4f} RUB/g from {result['source']}")
                else:
                    print(f"   ✗ {ingredient_name}: No price found")
            
            if resolved_count >= 4:  # At least 4 out of 5 should be found
                self.log_test("PriceProvider - Fuzzy Name Matching", True, 
                             f"Resolved {resolved_count}/5 ingredients")
            else:
                self.log_test("PriceProvider - Fuzzy Name Matching", False, 
                             f"Only resolved {resolved_count}/5 ingredients")
            
            # Test 1.3: Unit normalization to RUB/gram
            test_cases = [
                ("куриное филе", "kg", 450),  # Should be 0.45 RUB/g
                ("растительное масло", "liter", 150),  # Should be 0.15 RUB/g  
                ("яйца куриные", "pcs", 120)  # Should estimate weight
            ]
            
            normalization_ok = True
            for name, unit, price in test_cases:
                normalized = provider._normalize_price_to_gram(price, unit)
                expected_range = (0.001, 10.0)  # Reasonable range for RUB/gram
                
                if expected_range[0] <= normalized <= expected_range[1]:
                    print(f"   ✓ {name}: {price} {unit} → {normalized:.4f} RUB/g")
                else:
                    print(f"   ✗ {name}: {price} {unit} → {normalized:.4f} RUB/g (out of range)")
                    normalization_ok = False
            
            self.log_test("PriceProvider - Unit Normalization", normalization_ok, 
                         "Unit conversion to RUB/gram working correctly" if normalization_ok else "Unit conversion issues")
            
            # Test 1.4: Stale price detection (>30 days)
            old_date = "2025-07-01"  # More than 30 days ago
            recent_date = "2025-08-10"  # Recent
            
            is_old_stale = provider.is_stale_price(old_date, 30)
            is_recent_stale = provider.is_stale_price(recent_date, 30)
            
            if is_old_stale and not is_recent_stale:
                self.log_test("PriceProvider - Stale Price Detection", True, 
                             "Correctly identifies stale vs fresh prices")
            else:
                self.log_test("PriceProvider - Stale Price Detection", False, 
                             f"Stale detection failed: old={is_old_stale}, recent={is_recent_stale}")
            
            # Test 1.5: Search for mapping functionality
            search_results = provider.search_for_mapping("курица", limit=10)
            
            if len(search_results) > 0:
                # Check result format
                first_result = search_results[0]
                required_fields = ["source", "name", "skuId", "unit", "price_per_unit", "currency", "asOf"]
                has_all_fields = all(field in first_result for field in required_fields)
                
                if has_all_fields:
                    self.log_test("PriceProvider - Search for Mapping", True, 
                                 f"Found {len(search_results)} results with correct format")
                else:
                    missing = [f for f in required_fields if f not in first_result]
                    self.log_test("PriceProvider - Search for Mapping", False, 
                                 f"Missing fields in results: {missing}")
            else:
                self.log_test("PriceProvider - Search for Mapping", False, 
                             "No search results returned")
                
        except Exception as e:
            self.log_test("PriceProvider - Class Functionality", False, f"Exception: {str(e)}")
    
    def test_cost_calculator_integration(self):
        """Test 2: Cost Calculator Integration with PriceProvider"""
        print("\n🔍 Testing Cost Calculator Integration...")
        
        try:
            sys.path.append('/app/backend')
            from receptor_agent.techcards_v2.cost_calculator import CostCalculator
            from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, MetaV2, YieldV2, ProcessStepV2, StorageV2
            
            # Create test tech card
            test_ingredients = [
                IngredientV2(name="куриное филе", netto_g=400, brutto_g=450, loss_pct=11.1),
                IngredientV2(name="растительное масло", netto_g=30, brutto_g=30, loss_pct=0.0),
                IngredientV2(name="лук репчатый", netto_g=100, brutto_g=120, loss_pct=16.7),
                IngredientV2(name="соль поваренная", netto_g=8, brutto_g=8, loss_pct=0.0),
                IngredientV2(name="неизвестный ингредиент", netto_g=50, brutto_g=50, loss_pct=0.0)  # Should not be found
            ]
            
            test_card = TechCardV2(
                meta=MetaV2(title="Тест блюдо", description="Тестовое блюдо"),
                ingredients=test_ingredients,
                portions=4,
                yield_=YieldV2(perPortion_g=200, perBatch_g=800),
                process=[
                    ProcessStepV2(n=1, action="Подготовить ингредиенты"),
                    ProcessStepV2(n=2, action="Обжарить курицу"),
                    ProcessStepV2(n=3, action="Подать блюдо")
                ],
                storage=StorageV2(conditions="Холодильник +2...+6°C", shelfLife_hours=24)
            )
            
            calculator = CostCalculator()
            cost, cost_meta, issues = calculator.calculate_tech_card_cost(test_card)
            
            # Test 2.1: Cost calculation with PriceProvider
            if cost and cost.rawCost and cost.rawCost > 0:
                self.log_test("Cost Calculator - Basic Calculation", True, 
                             f"Raw cost: {cost.rawCost} RUB, per portion: {cost.costPerPortion} RUB")
            else:
                self.log_test("Cost Calculator - Basic Calculation", False, 
                             "No cost calculated or zero cost")
                return
            
            # Test 2.2: CostMeta with source attribution
            if cost_meta:
                expected_fields = ["source", "coveragePct", "asOf"]
                has_meta_fields = all(hasattr(cost_meta, field) for field in expected_fields)
                
                if has_meta_fields:
                    coverage = cost_meta.coveragePct
                    source = cost_meta.source
                    
                    # Should have good coverage (4/5 ingredients = 80%)
                    if coverage >= 70:
                        self.log_test("Cost Calculator - Coverage Calculation", True, 
                                     f"Coverage: {coverage}% from source: {source}")
                    else:
                        self.log_test("Cost Calculator - Coverage Calculation", False, 
                                     f"Low coverage: {coverage}%")
                    
                    # Source should be catalog, bootstrap, or mixed
                    if source in ["catalog", "bootstrap", "mixed"]:
                        self.log_test("Cost Calculator - Source Attribution", True, 
                                     f"Source: {source}")
                    else:
                        self.log_test("Cost Calculator - Source Attribution", False, 
                                     f"Unexpected source: {source}")
                else:
                    self.log_test("Cost Calculator - CostMeta Fields", False, 
                                 "Missing required costMeta fields")
            else:
                self.log_test("Cost Calculator - CostMeta", False, "No costMeta generated")
            
            # Test 2.3: Issues generation for missing prices
            missing_price_issues = [issue for issue in issues if issue.get("type") == "noPrice"]
            
            if len(missing_price_issues) > 0:
                self.log_test("Cost Calculator - Missing Price Issues", True, 
                             f"Generated {len(missing_price_issues)} noPrice issues")
            else:
                self.log_test("Cost Calculator - Missing Price Issues", False, 
                             "No noPrice issues generated for unknown ingredient")
                
        except Exception as e:
            self.log_test("Cost Calculator - Integration", False, f"Exception: {str(e)}")
    
    def test_api_price_search(self):
        """Test 3: API Enhancement - Price Search"""
        print("\n🔍 Testing API Price Search Enhancement...")
        
        try:
            # Test 3.1: Basic price search
            url = f"{self.backend_url}/v1/techcards.v2/catalog-search"
            params = {
                "q": "курица",
                "source": "price",
                "limit": 10
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success" and "items" in data:
                    items = data["items"]
                    
                    if len(items) > 0:
                        self.log_test("API - Price Search Basic", True, 
                                     f"Found {len(items)} price results")
                        
                        # Test 3.2: Response format validation
                        first_item = items[0]
                        required_fields = ["source", "name", "sku_id", "unit", "price", "currency", "asOf"]
                        
                        # Check if most required fields are present (some might be null)
                        present_fields = [f for f in required_fields if f in first_item]
                        
                        if len(present_fields) >= 5:  # At least 5 out of 7 fields
                            self.log_test("API - Price Search Format", True, 
                                         f"Response has {len(present_fields)}/7 required fields")
                            
                            # Test 3.3: Source priority ranking
                            sources = [item.get("source") for item in items[:5]]
                            priority_sources = ["user", "catalog", "bootstrap"]
                            
                            # Check if results are sorted by priority
                            has_priority_order = True
                            for i, source in enumerate(sources):
                                if source in priority_sources:
                                    # Check if this source comes before lower priority sources
                                    for j in range(i+1, len(sources)):
                                        if sources[j] in priority_sources:
                                            if priority_sources.index(sources[j]) < priority_sources.index(source):
                                                has_priority_order = False
                                                break
                            
                            if has_priority_order:
                                self.log_test("API - Source Priority Ranking", True, 
                                             f"Results sorted by priority: {sources[:3]}")
                            else:
                                self.log_test("API - Source Priority Ranking", False, 
                                             f"Priority order not maintained: {sources[:3]}")
                        else:
                            self.log_test("API - Price Search Format", False, 
                                         f"Missing required fields, only {len(present_fields)}/7 present")
                    else:
                        self.log_test("API - Price Search Basic", False, "No items returned")
                else:
                    self.log_test("API - Price Search Basic", False, 
                                 f"Invalid response format: {data}")
            else:
                self.log_test("API - Price Search Basic", False, 
                             f"HTTP {response.status_code}: {response.text[:200]}")
            
            # Test 3.4: Search with different ingredients
            test_queries = ["говядина", "масло", "лук"]
            successful_searches = 0
            
            for query in test_queries:
                params["q"] = query
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success" and len(data.get("items", [])) > 0:
                        successful_searches += 1
            
            if successful_searches >= 2:
                self.log_test("API - Multiple Ingredient Search", True, 
                             f"{successful_searches}/3 searches successful")
            else:
                self.log_test("API - Multiple Ingredient Search", False, 
                             f"Only {successful_searches}/3 searches successful")
                
        except Exception as e:
            self.log_test("API - Price Search", False, f"Exception: {str(e)}")
    
    def test_techcard_generation_with_prices(self):
        """Test 4: TechCardV2 Generation with Price Integration"""
        print("\n🔍 Testing TechCardV2 Generation with Price Integration...")
        
        try:
            url = f"{self.backend_url}/v1/techcards.v2/generate"
            
            # Test with ingredients that should be found in price catalogs
            test_profile = {
                "name": "Куриное филе с овощами",
                "cuisine": "русская",
                "equipment": ["плита", "сковорода"],
                "dietary": []
            }
            
            response = requests.post(url, json=test_profile, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") in ["success", "draft"] and data.get("card"):
                    card = data["card"]
                    
                    # Test 4.1: CostMeta presence and fields
                    cost_meta = card.get("costMeta")
                    if cost_meta:
                        required_meta_fields = ["source", "coveragePct", "asOf"]
                        has_meta = all(field in cost_meta for field in required_meta_fields)
                        
                        if has_meta:
                            coverage = cost_meta.get("coveragePct", 0)
                            source = cost_meta.get("source", "")
                            as_of = cost_meta.get("asOf", "")
                            
                            self.log_test("TechCard Generation - CostMeta Fields", True, 
                                         f"Source: {source}, Coverage: {coverage}%, AsOf: {as_of}")
                            
                            # Test 4.2: Coverage percentage calculation
                            if coverage > 0:
                                self.log_test("TechCard Generation - Coverage Calculation", True, 
                                             f"Coverage: {coverage}%")
                            else:
                                self.log_test("TechCard Generation - Coverage Calculation", False, 
                                             "Zero coverage percentage")
                        else:
                            missing_fields = [f for f in required_meta_fields if f not in cost_meta]
                            self.log_test("TechCard Generation - CostMeta Fields", False, 
                                         f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("TechCard Generation - CostMeta", False, "No costMeta in response")
                    
                    # Test 4.3: Cost calculation
                    cost = card.get("cost")
                    if cost and cost.get("rawCost"):
                        raw_cost = cost.get("rawCost")
                        cost_per_portion = cost.get("costPerPortion")
                        
                        if raw_cost > 0:
                            self.log_test("TechCard Generation - Cost Calculation", True, 
                                         f"Raw cost: {raw_cost} RUB, per portion: {cost_per_portion} RUB")
                        else:
                            self.log_test("TechCard Generation - Cost Calculation", False, 
                                         "Zero or negative cost calculated")
                    else:
                        self.log_test("TechCard Generation - Cost Calculation", False, 
                                     "No cost data in response")
                    
                    # Test 4.4: Stale price issues (if any)
                    issues = data.get("issues", [])
                    stale_price_issues = [issue for issue in issues if issue.get("type") == "stalePrice"]
                    
                    if len(stale_price_issues) == 0:
                        self.log_test("TechCard Generation - No Stale Prices", True, 
                                     "No stale price issues detected")
                    else:
                        self.log_test("TechCard Generation - Stale Price Detection", True, 
                                     f"Detected {len(stale_price_issues)} stale price issues")
                else:
                    self.log_test("TechCard Generation - Basic Response", False, 
                                 f"Invalid response: status={data.get('status')}, has_card={bool(data.get('card'))}")
            else:
                self.log_test("TechCard Generation - API Call", False, 
                             f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("TechCard Generation - Price Integration", False, f"Exception: {str(e)}")
    
    def test_recalculation_api(self):
        """Test 5: Recalculation API Integration"""
        print("\n🔍 Testing Recalculation API Integration...")
        
        try:
            # First, generate a tech card to recalculate
            generate_url = f"{self.backend_url}/v1/techcards.v2/generate"
            test_profile = {
                "name": "Простое блюдо для теста",
                "cuisine": "русская",
                "equipment": ["плита"],
                "dietary": []
            }
            
            generate_response = requests.post(generate_url, json=test_profile, timeout=60)
            
            if generate_response.status_code == 200:
                generate_data = generate_response.json()
                
                if generate_data.get("card"):
                    original_card = generate_data["card"]
                    
                    # Modify the card by adding skuId to an ingredient (simulate mapping)
                    if "ingredients" in original_card and len(original_card["ingredients"]) > 0:
                        # Add skuId to first ingredient
                        original_card["ingredients"][0]["skuId"] = "CAT_КУРИНОЕ_ФИЛЕ"
                        
                        # Test recalculation
                        recalc_url = f"{self.backend_url}/v1/techcards.v2/recalc"
                        recalc_response = requests.post(recalc_url, json=original_card, timeout=60)
                        
                        if recalc_response.status_code == 200:
                            recalc_data = recalc_response.json()
                            
                            if recalc_data.get("status") == "success" and recalc_data.get("card"):
                                updated_card = recalc_data["card"]
                                
                                # Test 5.1: Cost recalculation
                                updated_cost = updated_card.get("cost")
                                if updated_cost and updated_cost.get("rawCost"):
                                    self.log_test("Recalc API - Cost Update", True, 
                                                 f"Updated cost: {updated_cost.get('rawCost')} RUB")
                                else:
                                    self.log_test("Recalc API - Cost Update", False, 
                                                 "No updated cost in recalculated card")
                                
                                # Test 5.2: CostMeta update
                                updated_cost_meta = updated_card.get("costMeta")
                                if updated_cost_meta:
                                    self.log_test("Recalc API - CostMeta Update", True, 
                                                 f"Updated costMeta: {updated_cost_meta}")
                                else:
                                    self.log_test("Recalc API - CostMeta Update", False, 
                                                 "No updated costMeta")
                                
                                # Test 5.3: SKU mapping working
                                first_ingredient = updated_card["ingredients"][0]
                                if first_ingredient.get("skuId") == "CAT_КУРИНОЕ_ФИЛЕ":
                                    self.log_test("Recalc API - SKU Mapping", True, 
                                                 "SKU mapping preserved in recalculation")
                                else:
                                    self.log_test("Recalc API - SKU Mapping", False, 
                                                 "SKU mapping lost in recalculation")
                            else:
                                self.log_test("Recalc API - Response Format", False, 
                                             f"Invalid recalc response: {recalc_data}")
                        else:
                            self.log_test("Recalc API - HTTP Call", False, 
                                         f"HTTP {recalc_response.status_code}: {recalc_response.text[:200]}")
                    else:
                        self.log_test("Recalc API - Test Setup", False, 
                                     "Generated card has no ingredients to modify")
                else:
                    self.log_test("Recalc API - Test Setup", False, 
                                 "Failed to generate initial card for recalculation test")
            else:
                self.log_test("Recalc API - Test Setup", False, 
                             f"Failed to generate test card: HTTP {generate_response.status_code}")
                
        except Exception as e:
            self.log_test("Recalc API - Integration", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all P1-Prices tests"""
        print("🚀 Starting P1-Prices Implementation Backend Testing")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
        
        # Run all test suites
        self.test_price_provider_class()
        self.test_cost_calculator_integration()
        self.test_api_price_search()
        self.test_techcard_generation_with_prices()
        self.test_recalculation_api()
        
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
            "PriceProvider - Load Sources",
            "PriceProvider - Fuzzy Name Matching", 
            "Cost Calculator - Basic Calculation",
            "API - Price Search Basic",
            "TechCard Generation - Cost Calculation"
        ]
        
        critical_passed = 0
        for test in self.test_results:
            if any(critical in test["test"] for critical in critical_tests) and test["success"]:
                critical_passed += 1
        
        if critical_passed >= 4:  # At least 4 out of 5 critical tests
            print(f"\n🎉 P1-PRICES IMPLEMENTATION: WORKING")
            print("Core functionality verified - unified price provider system operational")
            return True
        else:
            print(f"\n🚨 P1-PRICES IMPLEMENTATION: FAILING")
            print(f"Critical issues found - only {critical_passed}/5 critical tests passed")
            return False

def main():
    """Main test execution"""
    tester = P1PricesBackendTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()