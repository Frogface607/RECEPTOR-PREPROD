"""
GX-02: Quality Validator Tests
Test the TechCardV2 quality validation system
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from receptor_agent.techcards_v2.quality_validator import QualityValidator
from receptor_agent.techcards_v2.schemas import TechCardV2


class TestQualityValidator:
    """Test GX-02 Quality Validator"""
    
    def __init__(self):
        self.validator = QualityValidator()
    
    def test_yield_validation(self):
        """Test yield validation (обязателен г/мл/шт)"""
        print("=== Test: Yield Validation ===")
        
        # Test case 1: Missing yield
        techcard_no_yield = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 1,
            "ingredients": [],
            "process": []
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_no_yield)
        yield_issues = [i for i in issues if i.get('type') == 'yieldMissing']
        assert len(yield_issues) > 0, "Should detect missing yield"
        print(f"✓ Missing yield detected: {yield_issues[0]['message']}")
        
        # Test case 2: Invalid yield values
        techcard_invalid_yield = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 2,
            "yield": {"perPortion_g": 0, "perBatch_g": -10},
            "ingredients": [],
            "process": []
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_invalid_yield)
        portion_issues = [i for i in issues if i.get('type') == 'yieldPerPortionInvalid']
        batch_issues = [i for i in issues if i.get('type') == 'yieldPerBatchInvalid']
        
        assert len(portion_issues) > 0, "Should detect invalid perPortion_g"
        assert len(batch_issues) > 0, "Should detect invalid perBatch_g"
        print(f"✓ Invalid yields detected: portion and batch errors")
        
        # Test case 3: Inconsistent yields
        techcard_inconsistent = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 4,
            "yield": {"perPortion_g": 100, "perBatch_g": 300},  # Should be 400
            "ingredients": [],
            "process": []
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_inconsistent)
        inconsistent_issues = [i for i in issues if i.get('type') == 'yieldInconsistent']
        assert len(inconsistent_issues) > 0, "Should detect yield inconsistency"
        print(f"✓ Yield inconsistency detected: {inconsistent_issues[0]['message']}")
        
        print("✅ Yield validation test PASSED")
        return True
    
    def test_netto_sum_validation(self):
        """Test netto sum ≈ yield validation (допуск 2-3%)"""
        print("\n=== Test: Netto Sum Validation ===")
        
        # Test case 1: Correct netto sum
        techcard_correct = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 1,
            "yield": {"perPortion_g": 100, "perBatch_g": 100},
            "ingredients": [
                {"name": "Ingredient 1", "netto_g": 50, "unit": "g"},
                {"name": "Ingredient 2", "netto_g": 48, "unit": "g"}  # 98g total, within 3% tolerance
            ],
            "process": []
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_correct)
        netto_issues = [i for i in issues if i.get('type') == 'nettoSumMismatch']
        assert len(netto_issues) == 0, "Should accept netto sum within tolerance"
        print("✓ Correct netto sum accepted (within tolerance)")
        
        # Test case 2: Netto sum too different
        techcard_mismatch = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 1,
            "yield": {"perPortion_g": 100, "perBatch_g": 100},
            "ingredients": [
                {"name": "Ingredient 1", "netto_g": 30, "unit": "g"},
                {"name": "Ingredient 2", "netto_g": 40, "unit": "g"}  # 70g total, 30% difference
            ],
            "process": []
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_mismatch)
        mismatch_issues = [i for i in issues if i.get('type') == 'nettoSumMismatch']
        assert len(mismatch_issues) > 0, "Should detect netto sum mismatch"
        print(f"✓ Netto sum mismatch detected: {mismatch_issues[0]['message']}")
        
        # Test case 3: Zero netto sum
        techcard_zero = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 1,
            "yield": {"perPortion_g": 100, "perBatch_g": 100},
            "ingredients": [
                {"name": "Ingredient 1", "netto_g": 0, "unit": "g"},
                {"name": "Ingredient 2", "netto_g": 0, "unit": "g"}
            ],
            "process": []
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_zero)
        zero_issues = [i for i in issues if i.get('type') == 'nettoSumZero']
        assert len(zero_issues) > 0, "Should detect zero netto sum"
        print(f"✓ Zero netto sum detected: {zero_issues[0]['message']}")
        
        print("✅ Netto sum validation test PASSED")
        return True
    
    def test_range_normalization(self):
        """Test range normalization (0-4 → numbers)"""
        print("\n=== Test: Range Normalization ===")
        
        techcard_with_ranges = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 1,
            "yield": {"perPortion_g": "200-250", "perBatch_g": 225},
            "ingredients": [
                {"name": "Ingredient 1", "brutto_g": "100-120", "netto_g": "90–110", "loss_pct": "5 - 10", "unit": "g"}
            ],
            "process": [
                {"n": 1, "action": "Test step", "time_min": "5-8", "temp_c": "180–200"}
            ]
        }
        
        normalized, issues = self.validator._normalize_ranges(techcard_with_ranges)
        
        # Check normalization
        assert isinstance(normalized['yield']['perPortion_g'], (int, float)), "Should normalize yield range"
        assert isinstance(normalized['ingredients'][0]['brutto_g'], (int, float)), "Should normalize brutto range"
        assert isinstance(normalized['ingredients'][0]['netto_g'], (int, float)), "Should normalize netto range"
        assert isinstance(normalized['ingredients'][0]['loss_pct'], (int, float)), "Should normalize loss range"
        assert isinstance(normalized['process'][0]['time_min'], (int, float)), "Should normalize time range"
        assert isinstance(normalized['process'][0]['temp_c'], (int, float)), "Should normalize temp range"
        
        # Check issues
        range_issues = [i for i in issues if i.get('type') == 'rangeNormalized']
        assert len(range_issues) >= 5, f"Should have multiple range normalization issues, got {len(range_issues)}"
        
        print(f"✓ Normalized {len(range_issues)} range values")
        print(f"✓ perPortion_g: '200-250' → {normalized['yield']['perPortion_g']}")
        print(f"✓ brutto_g: '100-120' → {normalized['ingredients'][0]['brutto_g']}")
        print(f"✓ temp_c: '180–200' → {normalized['process'][0]['temp_c']}")
        
        print("✅ Range normalization test PASSED")
        return True
    
    def test_process_steps_validation(self):
        """Test process steps validation (minimum 3 steps)"""
        print("\n=== Test: Process Steps Validation ===")
        
        # Test case 1: Insufficient steps
        techcard_few_steps = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 1,
            "yield": {"perPortion_g": 100, "perBatch_g": 100},
            "ingredients": [],
            "process": [
                {"n": 1, "action": "Step 1"},
                {"n": 2, "action": "Step 2"}
            ]
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_few_steps)
        step_issues = [i for i in issues if i.get('type') == 'processStepsInsufficient']
        assert len(step_issues) > 0, "Should detect insufficient process steps"
        print(f"✓ Insufficient steps detected: {step_issues[0]['message']}")
        
        # Test case 2: Wrong numbering
        techcard_wrong_numbering = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 1,
            "yield": {"perPortion_g": 100, "perBatch_g": 100},
            "ingredients": [],
            "process": [
                {"n": 1, "action": "Step 1"},
                {"n": 3, "action": "Step 2"},  # Should be n=2
                {"n": 2, "action": "Step 3"}   # Should be n=3
            ]
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_wrong_numbering)
        numbering_issues = [i for i in issues if i.get('type') == 'processStepNumbering']
        assert len(numbering_issues) > 0, "Should detect wrong step numbering"
        print(f"✓ Wrong numbering detected: {len(numbering_issues)} issues")
        
        print("✅ Process steps validation test PASSED")
        return True
    
    def test_quality_scoring(self):
        """Test quality scoring system"""
        print("\n=== Test: Quality Scoring ===")
        
        # Test case 1: Perfect techcard
        perfect_card = {
            "meta": {"title": "Perfect Card", "version": "2.0"},
            "portions": 1,
            "yield": {"perPortion_g": 100, "perBatch_g": 100},
            "ingredients": [
                {"name": "Ingredient 1", "netto_g": 50, "unit": "g"},
                {"name": "Ingredient 2", "netto_g": 50, "unit": "g"}
            ],
            "process": [
                {"n": 1, "action": "Step 1", "time_min": 5, "temp_c": 20},
                {"n": 2, "action": "Step 2", "time_min": 10, "temp_c": 60},
                {"n": 3, "action": "Step 3", "time_min": 3, "temp_c": 80}
            ]
        }
        
        normalized, issues = self.validator.validate_techcard(perfect_card)
        quality_score = self.validator.get_quality_score(issues)
        
        assert quality_score['score'] >= 95, f"Perfect card should have high score, got {quality_score['score']}"
        assert quality_score['level'] == 'excellent', f"Perfect card should be excellent, got {quality_score['level']}"
        assert quality_score['is_production_ready'] == True, "Perfect card should be production ready"
        
        print(f"✓ Perfect card quality: {quality_score['score']}% ({quality_score['level']})")
        
        # Test case 2: Poor quality techcard
        poor_card = {
            "meta": {"title": "Poor Card", "version": "2.0"},
            "portions": 1,
            # Missing yield
            "ingredients": [
                {"name": "Bad ingredient", "netto_g": 0, "unit": "invalid"}  # Multiple issues
            ],
            "process": [
                {"n": 1, "action": "Only step"}  # Insufficient steps
            ]
        }
        
        normalized, issues = self.validator.validate_techcard(poor_card)
        quality_score = self.validator.get_quality_score(issues)
        
        assert quality_score['score'] < 60, f"Poor card should have low score, got {quality_score['score']}"
        assert quality_score['level'] == 'poor', f"Poor card should be poor quality, got {quality_score['level']}"
        assert quality_score['is_production_ready'] == False, "Poor card should not be production ready"
        
        print(f"✓ Poor card quality: {quality_score['score']}% ({quality_score['level']})")
        
        print("✅ Quality scoring test PASSED")
        return True
    
    def test_fix_banners(self):
        """Test fix banners generation"""
        print("\n=== Test: Fix Banners ===")
        
        techcard_with_issues = {
            "meta": {"title": "Test Card", "version": "2.0"},
            "portions": 1,
            # Missing yield - error
            "ingredients": [
                {"name": "Ingredient", "netto_g": 0, "unit": "g"}  # Zero netto - error
            ],
            "process": [
                {"n": 1, "action": "Step 1"},
                {"n": 3, "action": "Step 2"}  # Wrong numbering - warning
            ]
        }
        
        normalized, issues = self.validator.validate_techcard(techcard_with_issues)
        banners = self.validator.generate_fix_banners(issues)
        
        # Should have error and warning banners
        error_banners = [b for b in banners if b['type'] == 'error']
        warning_banners = [b for b in banners if b['type'] == 'warning']
        
        assert len(error_banners) > 0, "Should have error banners"
        assert len(warning_banners) > 0, "Should have warning banners"
        
        print(f"✓ Generated {len(error_banners)} error banners")
        print(f"✓ Generated {len(warning_banners)} warning banners")
        
        # Test banner structure
        for banner in banners:
            assert 'type' in banner, "Banner should have type"
            assert 'title' in banner, "Banner should have title"  
            assert 'icon' in banner, "Banner should have icon"
            assert 'messages' in banner, "Banner should have messages"
            assert 'action' in banner, "Banner should have action"
        
        print("✅ Fix banners test PASSED")
        return True
    
    def run_all_tests(self):
        """Run all quality validator tests"""
        print("🔄 Starting GX-02 Quality Validator Tests...")
        print("=" * 50)
        
        tests = [
            self.test_yield_validation,
            self.test_netto_sum_validation,
            self.test_range_normalization,
            self.test_process_steps_validation,
            self.test_quality_scoring,
            self.test_fix_banners
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
        print(f"📊 Quality Validator Tests: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL QUALITY VALIDATOR TESTS PASSED!")
            print("✅ Yield validation working")
            print("✅ Netto sum validation working")
            print("✅ Range normalization working")
            print("✅ Process steps validation working")
            print("✅ Quality scoring working")
            print("✅ Fix banners working")
            print("✅ GX-02 quality system ready for production")
        else:
            print(f"❌ {total - passed} tests failed - requires attention")
            
        return passed == total


if __name__ == "__main__":
    tester = TestQualityValidator()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)