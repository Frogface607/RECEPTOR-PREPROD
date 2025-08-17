"""
IK-04/03: Unit conversion tests for iiko XLSX imports
Tests kg/l/ml/pcs conversions with density mappings and warnings
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from receptor_agent.integrations.iiko_xlsx_parser import IikoXlsxParser
from receptor_agent.techcards_v2.schemas import TechCardV2

class TestIikoImportUnits:
    """Test unit conversions and density handling"""
    
    def __init__(self):
        self.parser = IikoXlsxParser()
    
    def test_weight_conversions(self):
        """Test kg → g conversions"""
        print("\n=== Test: Weight Conversions ===")
        
        # Test data with kg/g units
        test_cases = [
            ("кг", 1.5, 1500.0),  # 1.5 kg → 1500g
            ("kg", 0.8, 800.0),   # 0.8 kg → 800g  
            ("г", 500, 500.0),    # 500g → 500g (no change)
            ("g", 250, 250.0)     # 250g → 250g (no change)
        ]
        
        for unit, input_val, expected in test_cases:
            normalized_unit, brutto_norm, netto_norm = self.parser._normalize_unit_and_quantities(
                unit, input_val, input_val * 0.9, "тестовый ингредиент"
            )
            
            assert normalized_unit == "g", f"Unit should normalize to 'g', got '{normalized_unit}'"
            assert abs(netto_norm - expected * 0.9) < 0.1, f"Weight conversion failed: {netto_norm} vs {expected * 0.9}"
            print(f"✓ {input_val}{unit} → {netto_norm}g")
        
        print("✅ Weight conversions test PASSED")
    
    def test_volume_conversions(self):
        """Test l → ml and ml → g conversions with densities"""
        print("\n=== Test: Volume Conversions ===")
        
        # Test l → ml conversion  
        normalized_unit, brutto_norm, netto_norm = self.parser._normalize_unit_and_quantities(
            "л", 1.5, 1.4, "вода"
        )
        assert normalized_unit == "ml", f"Expected 'ml', got '{normalized_unit}'"
        assert abs(netto_norm - 1400) < 1, f"l→ml conversion failed: {netto_norm} vs 1400"
        print("✓ 1.4л → 1400мл")
        
        # Test ml → g conversions with different densities
        density_tests = [
            ("вода", 1000, 1000.0),      # Water: 1.0 density
            ("молоко", 1000, 1030.0),    # Milk: 1.03 density  
            ("масло", 1000, 900.0),      # Oil: 0.9 density
            ("сироп", 1000, 1300.0),     # Syrup: 1.3 density
            ("мёд", 500, 700.0)          # Honey: 1.4 density (500ml → 700g)
        ]
        
        for ingredient, ml_amount, expected_grams in density_tests:
            normalized_unit, brutto_norm, netto_norm = self.parser._normalize_unit_and_quantities(
                "мл", ml_amount, ml_amount, ingredient
            )
            
            assert normalized_unit == "g", f"ml should convert to g for {ingredient}"
            assert abs(netto_norm - expected_grams) < 5, f"Density conversion failed for {ingredient}: {netto_norm}g vs {expected_grams}g"
            print(f"✓ {ml_amount}мл {ingredient} → {netto_norm}g")
        
        print("✅ Volume conversions test PASSED")
    
    def test_piece_conversions(self):
        """Test pcs → g conversions with standard weights"""
        print("\n=== Test: Piece Conversions ===")
        
        # Test known piece weights
        piece_tests = [
            ("яйцо", 2, 100.0),       # 2 eggs → 100g (50g each)
            ("лук", 1, 150.0),        # 1 onion → 150g
            ("морковь", 3, 300.0),    # 3 carrots → 300g (100g each)
            ("картофель", 2, 240.0),  # 2 potatoes → 240g (120g each)
            ("помидор", 1, 120.0),    # 1 tomato → 120g
            ("чеснок", 5, 25.0)       # 5 garlic cloves → 25g (5g each)
        ]
        
        for ingredient, pieces, expected_grams in piece_tests:
            normalized_unit, brutto_norm, netto_norm = self.parser._normalize_unit_and_quantities(
                "шт", pieces, pieces, ingredient
            )
            
            assert normalized_unit == "g", f"pcs should convert to g for {ingredient}"
            assert abs(netto_norm - expected_grams) < 1, f"Piece conversion failed for {ingredient}: {netto_norm}g vs {expected_grams}g"
            print(f"✓ {pieces}шт {ingredient} → {netto_norm}g")
        
        # Test unknown piece (should stay as pcs)
        normalized_unit, brutto_norm, netto_norm = self.parser._normalize_unit_and_quantities(
            "шт", 3, 3, "неизвестный продукт"
        )
        assert normalized_unit == "pcs", f"Unknown piece should stay as pcs, got {normalized_unit}"
        print("✓ Unknown piece stays as pcs")
        
        print("✅ Piece conversions test PASSED")
    
    def test_warning_generation(self):
        """Test that appropriate warnings are generated"""
        print("\n=== Test: Warning Generation ===")
        
        # Clear issues from previous tests
        self.parser.issues = []
        
        # Test density warning (non-water)
        self.parser._normalize_unit_and_quantities("мл", 500, 500, "масло растительное")
        density_warnings = [i for i in self.parser.issues if "densityUsed" in i.get("code", "")]
        assert len(density_warnings) > 0, "Expected density warning for oil"
        print("✓ Density warning generated for oil")
        
        # Clear and test water density warning
        self.parser.issues = []
        self.parser._normalize_unit_and_quantities("мл", 300, 300, "неизвестная жидкость")
        water_warnings = [i for i in self.parser.issues if "densityAssumedWater" in i.get("code", "")]
        assert len(water_warnings) > 0, "Expected water density warning"
        print("✓ Water density warning generated")
        
        # Clear and test missing piece weight warning
        self.parser.issues = []
        self.parser._normalize_unit_and_quantities("шт", 2, 2, "странный продукт")
        piece_warnings = [i for i in self.parser.issues if "massPerPieceMissing" in i.get("code", "")]
        assert len(piece_warnings) > 0, "Expected missing piece weight warning"
        print("✓ Missing piece weight warning generated")
        
        # Clear and test unknown unit warning
        self.parser.issues = []
        self.parser._normalize_unit_and_quantities("непонятная_единица", 100, 100, "продукт")
        unit_warnings = [i for i in self.parser.issues if "unitUnknown" in i.get("code", "")]
        assert len(unit_warnings) > 0, "Expected unknown unit warning"
        print("✓ Unknown unit warning generated")
        
        print("✅ Warning generation test PASSED")
    
    def run_all_tests(self):
        """Run all unit conversion tests"""
        print("🔄 Starting IK-04/03 Unit Conversion Tests...")
        print("=" * 50)
        
        tests = [
            self.test_weight_conversions,
            self.test_volume_conversions,
            self.test_piece_conversions,
            self.test_warning_generation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                test()
                passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} FAILED: {e}")
                continue
        
        print("=" * 50)
        print(f"📊 Unit Tests Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL UNIT CONVERSION TESTS PASSED!")
            print("✅ Weight conversions (kg→g) working")
            print("✅ Volume conversions (l→ml, ml→g) working")  
            print("✅ Piece conversions (pcs→g) working")
            print("✅ Density mappings functional")
            print("✅ Warning system operational")
        else:
            print(f"❌ {total - passed} tests failed")
            
        return passed == total

if __name__ == "__main__":
    tester = TestIikoImportUnits()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)