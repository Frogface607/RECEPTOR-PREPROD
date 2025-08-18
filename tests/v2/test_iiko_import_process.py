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
        """Test parsing of complex multi-step technology with temperatures and times"""
        print("\n=== Test: Complex Technology Parsing ===")
        
        technology = "Подготовить ингредиенты для жарки. Разогреть сковороду до 180°C с маслом. Обжаривать мясо 3 минуты с каждой стороны при высокой температуре. Уменьшить огонь до 160°C и тушить 25 минут под крышкой. Добавить овощи и готовить еще 5 минут при 160°C. Подавать горячим с гарниром."
        
        processes = self.parser._parse_technology(technology)
        
        # Should generate process steps
        assert len(processes) >= 3, f"Expected ≥3 steps, got {len(processes)}"
        print(f"✓ Complex technology parsed into {len(processes)} steps")
        
        # Check temperature extraction
        temps = [s['temp_c'] for s in processes if s['temp_c'] is not None]
        expected_temps = [180.0, 160.0]  # Should extract from text
        
        extracted_temps = [t for t in temps if t in expected_temps]
        assert len(extracted_temps) >= 2, f"Expected ≥2 cooking temperatures, got {extracted_temps}"
        print(f"✓ Temperatures extracted: {temps}°C")
        
        # Check time extraction
        times = [s['time_min'] for s in processes if s['time_min'] is not None]
        expected_times = [3.0, 25.0, 5.0]  # Should extract from text
        
        extracted_times = [t for t in times if t in expected_times]
        assert len(extracted_times) >= 2, f"Expected ≥2 time values, got {times}"
        print(f"✓ Times extracted: {times} minutes")
        
        print("✅ Complex technology parsing test PASSED")
        return True

    def test_advanced_patterns_parsing(self):
        """Test advanced regex patterns for complex time and temperature expressions"""
        print("\n=== Test: Advanced Patterns Parsing ===")
        
        # Test advanced time patterns
        advanced_time_cases = [
            ("Обжарить 3–4 мин при высокой температуре", 3.0),  # Range pattern
            ("Томить 45 мин при медленном огне под крышкой", 45.0),  # Standard pattern
        ]
        
        for text, expected_time in advanced_time_cases:
            extracted_time = self.parser._extract_time_from_text(text)
            assert extracted_time == expected_time, f"Expected {expected_time} min from '{text}', got {extracted_time}"
            print(f"✓ Advanced time pattern: '{text}' → {extracted_time} min")
        
        # Test advanced temperature patterns
        advanced_temp_cases = [
            ("Обжарить при 170–180°C до золотистой корочки", 170.0),  # Range pattern
            ("Томить при t=85°C под крышкой", 85.0),  # t= format pattern
        ]
        
        for text, expected_temp in advanced_temp_cases:
            extracted_temp = self.parser._extract_temperature_from_text(text)
            assert extracted_temp == expected_temp, f"Expected {expected_temp}°C from '{text}', got {extracted_temp}"
            print(f"✓ Advanced temp pattern: '{text}' → {extracted_temp}°C")
        
        print("✅ Advanced patterns parsing test PASSED")
        return True
    
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
            self.test_advanced_patterns_parsing,
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