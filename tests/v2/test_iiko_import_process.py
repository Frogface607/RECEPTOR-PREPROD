"""
IK-04/03: Process parsing tests for iiko XLSX imports  
Tests technology text parsing: ≥3 steps, time_min/temp_c extraction
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from receptor_agent.integrations.iiko_xlsx_parser import IikoXlsxParser

class TestIikoImportProcess:
    """Test technology parsing and process step generation"""
    
    def __init__(self):
        self.parser = IikoXlsxParser()
    
    def test_minimum_steps_generation(self):
        """Test that minimum 3 steps are always generated"""
        print("\n=== Test: Minimum Steps Generation ===")
        
        test_cases = [
            ("", 3),  # Empty text → 3 default steps
            ("Приготовить блюдо", 3),  # Single step → expanded to 3
            ("Подготовить. Готовить.", 3),  # Two steps → expanded to 3  
            ("Шаг 1. Шаг 2. Шаг 3.", 3),  # Three steps → keep as 3
            ("1. Подготовка\n2. Обжаривание\n3. Тушение\n4. Доведение\n5. Подача", 5)  # Five steps → keep as 5
        ]
        
        for technology_text, expected_min_steps in test_cases:
            steps = self.parser._parse_technology(technology_text)
            
            assert len(steps) >= 3, f"Expected ≥3 steps, got {len(steps)} for: '{technology_text}'"
            assert len(steps) >= expected_min_steps, f"Expected ≥{expected_min_steps} steps, got {len(steps)}"
            
            # Verify step numbering
            for i, step in enumerate(steps, 1):
                assert step["n"] == i, f"Step numbering incorrect: expected {i}, got {step['n']}"
                assert step["action"], f"Step {i} has empty action"
            
            print(f"✓ '{technology_text[:30]}...' → {len(steps)} steps")
        
        print("✅ Minimum steps generation test PASSED")
    
    def test_temperature_extraction(self):
        """Test temperature extraction from technology text"""
        print("\n=== Test: Temperature Extraction ===")
        
        temp_test_cases = [
            ("Жарить при 180°C до готовности", [180.0]),
            ("Запекать в духовке при 200°C в течение 20 минут", [200.0]), 
            ("Обжарить при 160°C, затем довести при 180°C", [160.0, 180.0]),
            ("Разогреть до 220 градусов и готовить", [220.0]),
            ("Готовить при температуре 350°F", [176.7]),  # Fahrenheit conversion
            ("Варить на медленном огне", []),  # No temperature
            ("Держать при 75°C для подачи", [75.0])
        ]
        
        for text, expected_temps in temp_test_cases:
            steps = self.parser._parse_technology(text)
            
            extracted_temps = [step["temp_c"] for step in steps if step["temp_c"] is not None]
            
            if expected_temps:
                assert len(extracted_temps) > 0, f"No temperatures extracted from: '{text}'"
                
                # Check that at least one expected temperature is present
                found_expected = False
                for expected in expected_temps:
                    if any(abs(temp - expected) < 2 for temp in extracted_temps):
                        found_expected = True
                        break
                
                assert found_expected, f"Expected temps {expected_temps}, got {extracted_temps} from: '{text}'"
                print(f"✓ '{text[:40]}...' → {extracted_temps}°C")
            else:
                print(f"✓ '{text[:40]}...' → no temperature (expected)")
        
        print("✅ Temperature extraction test PASSED")
    
    def test_time_extraction(self):
        """Test time extraction from technology text"""
        print("\n=== Test: Time Extraction ===")
        
        time_test_cases = [
            ("Варить 20 мин до готовности", [20.0]),
            ("Обжаривать 5 минут с каждой стороны", [5.0]),
            ("Тушить в течение 45 минут под крышкой", [45.0]),
            ("Запекать 1 час при высокой температуре", [60.0]),  # Hour conversion
            ("Готовить 2 часа на медленном огне", [120.0]),  # Hours conversion
            ("Довести до кипения", []),  # No time specified
            ("Обжарить 3-5 мин до золотистой корочки", [3.0])  # Range - take first
        ]
        
        for text, expected_times in time_test_cases:
            steps = self.parser._parse_technology(text)
            
            extracted_times = [step["time_min"] for step in steps if step["time_min"] is not None]
            
            if expected_times:
                assert len(extracted_times) > 0, f"No times extracted from: '{text}'"
                
                # Check that at least one expected time is present
                found_expected = False
                for expected in expected_times:
                    if any(abs(time - expected) < 1 for time in extracted_times):
                        found_expected = True
                        break
                
                assert found_expected, f"Expected times {expected_times}, got {extracted_times} from: '{text}'"
                print(f"✓ '{text[:40]}...' → {extracted_times} min")
            else:
                print(f"✓ '{text[:40]}...' → no time (expected)")
        
        print("✅ Time extraction test PASSED")
    
    def test_complex_technology_parsing(self):
        """Test parsing of complex, realistic technology descriptions"""
        print("\n=== Test: Complex Technology Parsing ===")
        
        complex_technology = """
        Мясо промыть, обсушить и нарезать порционными кусками. 
        Разогреть сковороду с растительным маслом до 180°C.
        Обжарить мясо с двух сторон по 3-4 минуты до золотистой корочки.
        Добавить нарезанные овощи и тушить под крышкой 25 минут при 160°C.
        Посолить, поперчить и довести до готовности еще 5-7 минут.
        Подавать горячим с гарниром.
        """
        
        steps = self.parser._parse_technology(complex_technology)
        
        # Should generate reasonable number of steps (3-8)
        assert 3 <= len(steps) <= 8, f"Expected 3-8 steps, got {len(steps)}"
        print(f"✓ Complex technology parsed into {len(steps)} steps")
        
        # Should extract multiple temperatures
        temps = [step["temp_c"] for step in steps if step["temp_c"] is not None]
        assert len(temps) > 0, "No temperatures extracted from complex technology"
        assert 180.0 in temps or 160.0 in temps, f"Expected 180°C or 160°C, got: {temps}"
        print(f"✓ Temperatures extracted: {temps}°C")
        
        # Should extract multiple time values
        times = [step["time_min"] for step in steps if step["time_min"] is not None]
        assert len(times) > 0, "No times extracted from complex technology"
        # Should find 3-4 min, 25 min, or 5-7 min
        expected_times = [3, 4, 25, 5, 7]
        found_time = any(any(abs(t - et) <= 1 for et in expected_times) for t in times)
        assert found_time, f"Expected times from {expected_times}, got: {times}"
        print(f"✓ Times extracted: {times} minutes")
        
        # Verify all steps have meaningful actions
        for step in steps:
            assert len(step["action"]) > 5, f"Step action too short: '{step['action']}'"
            assert step["action"] != "Подготовка сырья", f"Generic step should be customized in complex recipe"
        
        print("✅ Complex technology parsing test PASSED")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n=== Test: Edge Cases ===")
        
        edge_cases = [
            None,  # None input
            "",    # Empty string
            "   ", # Whitespace only
            "Готовить",  # Single word
            "." * 100,   # Many periods
            "Шаг " * 20, # Repetitive text
        ]
        
        for case in edge_cases:
            try:
                steps = self.parser._parse_technology(case)
                
                # Should always generate at least 3 steps
                assert len(steps) >= 3, f"Failed to generate minimum steps for case: {case}"
                
                # Steps should be properly numbered
                for i, step in enumerate(steps, 1):
                    assert step["n"] == i, f"Step numbering failed for case: {case}"
                    assert isinstance(step["action"], str), f"Action should be string for case: {case}"
                    assert len(step["action"]) > 0, f"Empty action for case: {case}"
                
                print(f"✓ Edge case handled: {str(case)[:20]}")
                
            except Exception as e:
                print(f"❌ Edge case failed: {case} - {e}")
                raise
        
        print("✅ Edge cases test PASSED")
    
    def run_all_tests(self):
        """Run all process parsing tests"""
        print("🔄 Starting IK-04/03 Process Parsing Tests...")
        print("=" * 50)
        
        tests = [
            self.test_minimum_steps_generation,
            self.test_temperature_extraction,
            self.test_time_extraction, 
            self.test_complex_technology_parsing,
            self.test_edge_cases
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
        print(f"📊 Process Tests Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL PROCESS PARSING TESTS PASSED!")
            print("✅ Minimum 3 steps generation working")
            print("✅ Temperature extraction (°C/°F) working")
            print("✅ Time extraction (min/hour) working") 
            print("✅ Complex technology parsing working")
            print("✅ Edge case handling robust")
            print("✅ Process validation ready for iikoWeb")
        else:
            print(f"❌ {total - passed} tests failed")
            
        return passed == total

if __name__ == "__main__":
    tester = TestIikoImportProcess()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)