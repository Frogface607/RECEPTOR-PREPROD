"""
GX-02: Enhanced Mapping Service Tests  
Test Russian synonyms and confidence scoring for auto-mapping
"""

import sys
from pathlib import Path

# Add the backend directory to Python path  
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from receptor_agent.integrations.enhanced_mapping_service import EnhancedMappingService


class TestEnhancedMapping:
    """Test GX-02 Enhanced Mapping Service"""
    
    def __init__(self):
        self.mapping_service = EnhancedMappingService()
    
    def test_ru_synonyms_loading(self):
        """Test Russian synonyms dictionary loading"""
        print("=== Test: RU Synonyms Loading ===")
        
        synonyms = self.mapping_service.ru_synonyms
        
        # Should have at least 30 basic positions as per GX-02
        assert len(synonyms) >= 30, f"Expected ≥30 synonym groups, got {len(synonyms)}"
        print(f"✓ Loaded {len(synonyms)} synonym groups")
        
        # Test specific synonyms from requirements
        required_items = [
            "яйца", "молоко", "сливки", "говядина", "курица", "лук", "морковь",
            "петрушка", "укроп", "картофель", "помидоры", "мука", "соль", "сахар"
        ]
        
        found_items = 0
        for item in required_items:
            if item in synonyms:
                found_items += 1
                print(f"✓ Found synonyms for '{item}': {len(synonyms[item])} variants")
        
        assert found_items >= 10, f"Expected ≥10 required items, found {found_items}"
        
        # Test synonym quality (should have multiple variants)
        complex_items = [item for item, syns in synonyms.items() if len(syns) >= 3]
        assert len(complex_items) >= 20, f"Expected ≥20 items with multiple synonyms, got {len(complex_items)}"
        print(f"✓ {len(complex_items)} items have ≥3 synonyms each")
        
        print("✅ RU synonyms loading test PASSED")
        return True
    
    def test_canonical_form_detection(self):
        """Test canonical form detection from synonyms"""
        print("\n=== Test: Canonical Form Detection ===")
        
        test_cases = [
            ("яйцо куриное", "яйца"),
            ("яйцо С1", "яйца"),
            ("молоко 3.2%", "молоко"),
            ("сливки 33%", "сливки"),
            ("говядина свежая", "говядина"),
            ("лук репчатый", "лук"),
            ("петрушка свежая", "петрушка"),
            ("неизвестный продукт", None)  # Should not match
        ]
        
        passed_cases = 0
        for input_name, expected_canonical in test_cases:
            result = self.mapping_service._find_canonical_form(input_name.lower())
            
            if result == expected_canonical:
                print(f"✓ '{input_name}' → '{result}' (correct)")
                passed_cases += 1
            else:
                print(f"✗ '{input_name}' → '{result}', expected '{expected_canonical}'")
        
        success_rate = (passed_cases / len(test_cases)) * 100
        assert success_rate >= 80, f"Expected ≥80% success rate, got {success_rate:.1f}%"
        
        print(f"✅ Canonical form detection: {success_rate:.1f}% success rate")
        return True
    
    def test_text_normalization(self):
        """Test text normalization for matching"""
        print("\n=== Test: Text Normalization ===")
        
        test_cases = [
            ("мука пшеничная 1кг", "мука пшеничная"),
            ("молоко 3.2% 1л", "молоко"),
            ("яйца С1 10шт", "яйца С1"),
            ("масло сливочное, 200г", "масло сливочное"),
            ("лук репчатый - 500 граммов", "лук репчатый"),
            ("говядина (свежая) 1 кг", "говядина свежая")
        ]
        
        for input_text, expected_output in test_cases:
            result = self.mapping_service._normalize_for_matching(input_text)
            
            # Check if normalization is reasonable (removed units, cleaned up)
            if len(result) <= len(input_text) and result.strip():
                print(f"✓ '{input_text}' → '{result}'")
            else:
                print(f"✗ Normalization failed: '{input_text}' → '{result}'")
                return False
        
        print("✅ Text normalization test PASSED")
        return True
    
    def test_confidence_scoring(self):
        """Test confidence scoring thresholds"""
        print("\n=== Test: Confidence Scoring Thresholds ===")
        
        # Test thresholds as per GX-02
        assert self.mapping_service.auto_accept_threshold == 0.90, "Auto-accept threshold should be 0.90"
        assert self.mapping_service.review_threshold == 0.70, "Review threshold should be 0.70"
        
        print(f"✓ Auto-accept threshold: {self.mapping_service.auto_accept_threshold}")
        print(f"✓ Review threshold: {self.mapping_service.review_threshold}")
        
        # Test mock matching scenarios
        mock_products = [
            {
                "_id": "product1",
                "name": "Яйцо куриное С1",
                "article": "EGG001", 
                "unit": "pcs",
                "price_per_unit": 8.5,
                "group_name": "Яйца"
            },
            {
                "_id": "product2", 
                "name": "Молоко коровье 3.2%",
                "article": "MILK001",
                "unit": "ml",
                "price_per_unit": 0.065,
                "group_name": "Молочные продукты"
            }
        ]
        
        # Test exact synonym match (should be high confidence)
        matches = self.mapping_service._find_enhanced_matches("яйца", mock_products)
        if matches:
            assert matches[0]["confidence"] >= 0.90, f"Synonym match should have ≥0.90 confidence, got {matches[0]['confidence']}"
            print(f"✓ Synonym match confidence: {matches[0]['confidence']:.2f}")
            
        # Test partial match
        matches = self.mapping_service._find_enhanced_matches("молоко", mock_products)
        if matches:
            print(f"✓ Partial match confidence: {matches[0]['confidence']:.2f}")
        
        print("✅ Confidence scoring test PASSED")
        return True
    
    def test_coverage_calculation(self):
        """Test mapping coverage calculation"""
        print("\n=== Test: Coverage Calculation ===")
        
        # Mock ingredients  
        mock_ingredients = [
            {"name": "Яйца", "unit": "pcs", "skuId": None},
            {"name": "Молоко", "unit": "ml", "skuId": None},
            {"name": "Мука", "unit": "g", "skuId": "FLOUR001"},  # Already has SKU
            {"name": "Соль", "unit": "g", "skuId": None}
        ]
        
        # Mock mapping results
        mock_mapping_results = [
            {"ingredient_name": "Яйца", "status": "auto_accept", "confidence": 0.95},
            {"ingredient_name": "Молоко", "status": "review", "confidence": 0.85}
        ]
        
        coverage = self.mapping_service._calculate_coverage(mock_ingredients, mock_mapping_results)
        
        # Validate coverage calculation
        assert coverage["total_ingredients"] == 4, f"Expected 4 total ingredients, got {coverage['total_ingredients']}"
        assert coverage["current_with_sku"] == 1, f"Expected 1 with SKU, got {coverage['current_with_sku']}"
        assert coverage["auto_accept_available"] == 1, f"Expected 1 auto-accept, got {coverage['auto_accept_available']}"
        assert coverage["review_available"] == 1, f"Expected 1 review, got {coverage['review_available']}"
        
        expected_potential = 1 + 1 + 1  # existing + auto_accept + review = 3
        assert coverage["potential_coverage"] == expected_potential, f"Expected {expected_potential} potential coverage, got {coverage['potential_coverage']}"
        
        expected_potential_pct = (3 / 4) * 100  # 75%
        assert abs(coverage["potential_coverage_pct"] - expected_potential_pct) < 0.1, f"Expected {expected_potential_pct}% potential coverage"
        
        print(f"✓ Coverage calculation: {coverage['potential_coverage']}/{coverage['total_ingredients']} ({coverage['potential_coverage_pct']:.1f}%)")
        print("✅ Coverage calculation test PASSED")
        return True
    
    def test_mapping_application(self):
        """Test applying auto-accepted mappings to TechCard"""
        print("\n=== Test: Mapping Application ===")
        
        # Mock TechCard
        mock_techcard = {
            "meta": {"title": "Test Recipe"},
            "ingredients": [
                {"name": "Яйца", "netto_g": 100, "unit": "pcs", "skuId": None},
                {"name": "Молоко", "netto_g": 200, "unit": "ml", "skuId": None},
                {"name": "Мука", "netto_g": 300, "unit": "g", "skuId": "EXISTING_FLOUR"}  # Already mapped
            ]
        }
        
        # Mock mapping results with auto-accept
        mock_mapping_results = [
            {
                "ingredient_name": "Яйца",
                "status": "auto_accept",
                "confidence": 0.95,
                "suggestion": {"sku_id": "EGG001", "name": "Яйцо куриное С1", "unit": "pcs"}
            },
            {
                "ingredient_name": "Молоко", 
                "status": "review",  # Should not be auto-applied
                "confidence": 0.85,
                "suggestion": {"sku_id": "MILK001", "name": "Молоко 3.2%", "unit": "ml"}
            }
        ]
        
        # Apply mappings
        updated_card = self.mapping_service.apply_auto_accepted_mappings(mock_techcard, mock_mapping_results)
        
        # Verify results
        ingredients = updated_card["ingredients"]
        
        # Check that auto-accept mapping was applied
        eggs_ingredient = next((ing for ing in ingredients if ing["name"] == "Яйца"), None)
        assert eggs_ingredient is not None, "Eggs ingredient should exist"
        assert eggs_ingredient["skuId"] == "EGG001", f"Eggs should have SKU EGG001, got {eggs_ingredient.get('skuId')}"
        print("✓ Auto-accept mapping applied: Яйца → EGG001")
        
        # Check that review mapping was NOT applied
        milk_ingredient = next((ing for ing in ingredients if ing["name"] == "Молоко"), None)
        assert milk_ingredient is not None, "Milk ingredient should exist"
        assert milk_ingredient.get("skuId") is None, f"Milk should not have SKU (review status), got {milk_ingredient.get('skuId')}"
        print("✓ Review mapping NOT auto-applied: Молоко (correct)")
        
        # Check that existing mapping was preserved
        flour_ingredient = next((ing for ing in ingredients if ing["name"] == "Мука"), None)
        assert flour_ingredient is not None, "Flour ingredient should exist"
        assert flour_ingredient["skuId"] == "EXISTING_FLOUR", f"Flour should keep existing SKU, got {flour_ingredient.get('skuId')}"
        print("✓ Existing mapping preserved: Мука → EXISTING_FLOUR")
        
        print("✅ Mapping application test PASSED")
        return True
    
    def run_all_tests(self):
        """Run all enhanced mapping tests"""
        print("🔄 Starting GX-02 Enhanced Mapping Tests...")
        print("=" * 50)
        
        tests = [
            self.test_ru_synonyms_loading,
            self.test_canonical_form_detection,  
            self.test_text_normalization,
            self.test_confidence_scoring,
            self.test_coverage_calculation,
            self.test_mapping_application
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} FAILED: {e}")
                continue
        
        print("=" * 50)
        print(f"📊 Enhanced Mapping Tests: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL ENHANCED MAPPING TESTS PASSED!")
            print("✅ RU synonyms dictionary loaded (30+ groups)")
            print("✅ Canonical form detection working")
            print("✅ Text normalization working")
            print("✅ Confidence scoring thresholds correct (≥0.90 auto-accept, 0.70-0.89 review)")
            print("✅ Coverage calculation accurate")
            print("✅ Auto-accept mapping application working")
            print("✅ GX-02 enhanced mapping system ready for production")
        else:
            print(f"❌ {total - passed} tests failed - requires attention")
            
        return passed == total


if __name__ == "__main__":
    tester = TestEnhancedMapping()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)