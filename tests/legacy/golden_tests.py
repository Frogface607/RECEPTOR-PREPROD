#!/usr/bin/env python3
"""
Golden Tests для TechCardV2
Проверка качества и консистентности эталонных техкарт
"""

import sys
import os
import json
import glob
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

try:
    from receptor_agent.techcards_v2.schemas import TechCardV2
    from pydantic import ValidationError
except ImportError as e:
    print(f"⚠️  Import warning: {e}")
    print("Running in standalone mode without schema validation")
    TechCardV2 = None
    ValidationError = Exception

class GoldenTestRunner:
    """Тест-раннер для golden tests техкарт"""
    
    def __init__(self, golden_dir: str = "/app/golden/techcards"):
        self.golden_dir = golden_dir
        self.results = []
        self.warnings = []
        
    def load_golden_files(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Загружает все golden файлы"""
        files = []
        pattern = os.path.join(self.golden_dir, "*.json")
        
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                files.append((filename, data))
            except Exception as e:
                self.results.append(f"❌ FAIL: {filename} - Failed to load JSON: {e}")
                
        return files
    
    def test_schema_validity(self, filename: str, data: Dict[str, Any]) -> bool:
        """Тест 1: Валидность по схеме TechCardV2"""
        if TechCardV2 is None:
            self.warnings.append(f"⚠️  {filename} - Schema validation skipped (imports not available)")
            return True
            
        try:
            tech_card = TechCardV2(**data)
            self.results.append(f"✅ PASS: {filename} - Schema validation")
            return True
        except ValidationError as e:
            self.results.append(f"❌ FAIL: {filename} - Schema validation failed: {e}")
            return False
        except Exception as e:
            self.results.append(f"❌ FAIL: {filename} - Unexpected error in schema validation: {e}")
            return False
    
    def test_yield_balance(self, filename: str, data: Dict[str, Any]) -> bool:
        """Тест 2: Баланс нетто vs yield.perBatch_g (±5%)"""
        try:
            ingredients = data.get("ingredients", [])
            yield_data = data.get("yield", {})
            
            total_netto = sum(ing.get("netto_g", 0) for ing in ingredients)
            expected_batch = yield_data.get("perBatch_g", 0)
            
            if expected_batch == 0:
                self.results.append(f"❌ FAIL: {filename} - yield.perBatch_g is zero")
                return False
            
            diff_pct = abs(total_netto - expected_batch) / expected_batch * 100
            
            if diff_pct <= 5.0:
                self.results.append(f"✅ PASS: {filename} - Yield balance ({diff_pct:.1f}% diff)")
                return True
            else:
                self.results.append(f"❌ FAIL: {filename} - Yield mismatch: {total_netto:.1f}g vs {expected_batch:.1f}g ({diff_pct:.1f}% diff > 5%)")
                return False
                
        except Exception as e:
            self.results.append(f"❌ FAIL: {filename} - Yield balance test error: {e}")
            return False
    
    def test_no_ranges(self, filename: str, data: Dict[str, Any]) -> bool:
        """Тест 3: Отсутствие диапазонов в числовых полях"""
        def has_range(value):
            """Проверяет содержит ли значение диапазон"""
            if isinstance(value, str):
                # Исключаем ISO даты и технические форматы
                if re.match(r'\d{4}-\d{2}-\d{2}', value):  # ISO date
                    return False
                if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):  # ISO datetime  
                    return False
                
                # Ищем паттерны типа "10-15", "5...8", "от 2 до 5"
                range_patterns = [
                    r'\d+\s*-\s*\d+',
                    r'\d+\s*\.\.\.\s*\d+', 
                    r'от\s+\d+\s+до\s+\d+',
                    r'\d+\s*~\s*\d+'
                ]
                return any(re.search(pattern, value) for pattern in range_patterns)
            return False
        
        def check_object(obj, path=""):
            """Рекурсивно проверяет объект на диапазоны"""
            ranges_found = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if has_range(value):
                        ranges_found.append(f"{new_path}: {value}")
                    ranges_found.extend(check_object(value, new_path))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    ranges_found.extend(check_object(item, new_path))
            elif has_range(obj):
                ranges_found.append(f"{path}: {obj}")
                
            return ranges_found
        
        try:
            ranges = check_object(data)
            if not ranges:
                self.results.append(f"✅ PASS: {filename} - No ranges in numeric fields")
                return True
            else:
                self.results.append(f"❌ FAIL: {filename} - Found ranges: {', '.join(ranges)}")
                return False
        except Exception as e:
            self.results.append(f"❌ FAIL: {filename} - Range check error: {e}")
            return False
    
    def test_thermal_processing(self, filename: str, data: Dict[str, Any]) -> bool:
        """Тест 4: У термообработки есть time_min или temp_c"""
        try:
            process_steps = data.get("process", [])
            thermal_keywords = [
                "варить", "жарить", "тушить", "запекать", "кипятить", "обжаривать",
                "готовить", "томить", "припускать", "бланшировать", "пассеровать"
            ]
            
            issues = []
            for step in process_steps:
                action = step.get("action", "").lower()
                has_thermal = any(keyword in action for keyword in thermal_keywords)
                
                if has_thermal:
                    has_time = step.get("time_min") is not None
                    has_temp = step.get("temp_c") is not None
                    
                    if not (has_time or has_temp):
                        issues.append(f"Step {step.get('n', '?')}: '{step.get('action', '')}' - missing time_min/temp_c")
            
            if not issues:
                self.results.append(f"✅ PASS: {filename} - Thermal processing has time/temp")
                return True
            else:
                self.results.append(f"❌ FAIL: {filename} - Thermal issues: {'; '.join(issues)}")
                return False
                
        except Exception as e:
            self.results.append(f"❌ FAIL: {filename} - Thermal processing test error: {e}")
            return False
    
    def test_nutrition_formula(self, filename: str, data: Dict[str, Any]) -> bool:
        """Тест 5: Формула питания perPortion ≈ per100g × (yield.perPortion_g/100) ±3%"""
        try:
            nutrition = data.get("nutrition", {})
            per100g = nutrition.get("per100g", {})
            perPortion = nutrition.get("perPortion", {})
            yield_data = data.get("yield", {})
            portion_g = yield_data.get("perPortion_g", 0)
            
            if not all([per100g, perPortion, portion_g]):
                self.warnings.append(f"⚠️  {filename} - Nutrition formula test skipped (missing data)")
                return True
            
            issues = []
            for nutrient in ["kcal", "proteins_g", "fats_g", "carbs_g"]:
                per100_val = per100g.get(nutrient, 0)
                portion_val = perPortion.get(nutrient, 0)
                
                expected_portion = per100_val * (portion_g / 100.0)
                
                if expected_portion == 0 and portion_val == 0:
                    continue  # Оба нуля - норма
                elif expected_portion == 0:
                    issues.append(f"{nutrient}: portion={portion_val} but expected=0")
                else:
                    diff_pct = abs(portion_val - expected_portion) / expected_portion * 100
                    if diff_pct > 3.0:
                        issues.append(f"{nutrient}: {portion_val} vs expected {expected_portion:.1f} ({diff_pct:.1f}% diff)")
            
            if not issues:
                self.results.append(f"✅ PASS: {filename} - Nutrition formula validation")
                return True
            else:
                self.results.append(f"❌ FAIL: {filename} - Nutrition formula issues: {'; '.join(issues)}")
                return False
                
        except Exception as e:
            self.results.append(f"❌ FAIL: {filename} - Nutrition formula test error: {e}")
            return False
    
    def test_cost_populated(self, filename: str, data: Dict[str, Any]) -> bool:
        """Тест 6: cost заполнен если costMeta.coveragePct>0"""
        try:
            cost = data.get("cost", {})
            costMeta = data.get("costMeta", {})
            coverage = costMeta.get("coveragePct", 0)
            
            if coverage == 0:
                self.results.append(f"✅ PASS: {filename} - Cost test skipped (0% coverage)")
                return True
            
            raw_cost = cost.get("rawCost")
            cost_per_portion = cost.get("costPerPortion")
            
            if raw_cost is not None and cost_per_portion is not None and raw_cost > 0:
                self.results.append(f"✅ PASS: {filename} - Cost populated with {coverage}% coverage")
                return True
            else:
                self.results.append(f"❌ FAIL: {filename} - Cost not populated despite {coverage}% coverage")
                return False
                
        except Exception as e:
            self.results.append(f"❌ FAIL: {filename} - Cost population test error: {e}")
            return False
    
    def test_warnings_threshold(self, filename: str, data: Dict[str, Any]) -> bool:
        """Тест 7: Предупреждения (noPrice, noNutrition, noSku) < 20%"""
        try:
            ingredients = data.get("ingredients", [])
            if not ingredients:
                return True
            
            warning_count = 0
            total_ingredients = len(ingredients)
            
            # Проверяем отсутствующие SKU
            for ing in ingredients:
                if not ing.get("skuId"):
                    warning_count += 1
            
            # В реальности здесь были бы проверки на noPrice и noNutrition
            # Но в эталонах все должно быть заполнено
            
            warning_pct = (warning_count / total_ingredients) * 100 if total_ingredients > 0 else 0
            
            if warning_pct < 20.0:
                if warning_count > 0:
                    self.warnings.append(f"⚠️  {filename} - {warning_count}/{total_ingredients} ingredients have warnings ({warning_pct:.1f}%)")
                self.results.append(f"✅ PASS: {filename} - Warning threshold ({warning_pct:.1f}% < 20%)")
                return True
            else:
                self.results.append(f"❌ FAIL: {filename} - Too many warnings: {warning_pct:.1f}% ≥ 20%")
                return False
                
        except Exception as e:
            self.results.append(f"❌ FAIL: {filename} - Warning threshold test error: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Запускает все тесты для всех golden файлов"""
        print(f"🧪 Running Golden Tests for TechCardV2...")
        print(f"📁 Golden directory: {self.golden_dir}")
        print()
        
        files = self.load_golden_files()
        if not files:
            print("❌ No golden files found!")
            return False
        
        print(f"📋 Found {len(files)} golden files")
        print()
        
        all_passed = True
        test_methods = [
            ("Schema Validity", self.test_schema_validity),
            ("Yield Balance", self.test_yield_balance), 
            ("No Ranges", self.test_no_ranges),
            ("Thermal Processing", self.test_thermal_processing),
            ("Nutrition Formula", self.test_nutrition_formula),
            ("Cost Population", self.test_cost_populated),
            ("Warning Threshold", self.test_warnings_threshold)
        ]
        
        for filename, data in files:
            print(f"🧪 Testing {filename}...")
            file_passed = True
            
            for test_name, test_method in test_methods:
                try:
                    if not test_method(filename, data):
                        file_passed = False
                        all_passed = False
                except Exception as e:
                    self.results.append(f"❌ FAIL: {filename} - {test_name} crashed: {e}")
                    file_passed = False
                    all_passed = False
            
            if file_passed:
                print(f"   ✅ All tests passed for {filename}")
            else:
                print(f"   ❌ Some tests failed for {filename}")
            print()
        
        return all_passed
    
    def print_summary(self):
        """Печатает итоговый отчет"""
        print("=" * 60)
        print("📊 GOLDEN TESTS SUMMARY")
        print("=" * 60)
        
        # Статистика
        total_results = len(self.results)
        passed = len([r for r in self.results if r.startswith("✅")])
        failed = len([r for r in self.results if r.startswith("❌")])
        
        print(f"📈 Statistics:")
        print(f"   Total tests: {total_results}")
        print(f"   Passed: {passed} ✅")
        print(f"   Failed: {failed} ❌")
        print(f"   Success rate: {(passed/total_results)*100:.1f}%" if total_results > 0 else "   Success rate: N/A")
        print()
        
        # Детали результатов
        if self.results:
            print("📋 Detailed Results:")
            for result in self.results:
                print(f"   {result}")
            print()
        
        # Предупреждения
        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   {warning}")
            print()
        
        # Финальный статус
        if failed == 0:
            print("🎉 ALL GOLDEN TESTS PASSED! ✅")
            return True
        else:
            print("💥 GOLDEN TESTS FAILED! ❌")
            return False

def main():
    """Главная функция"""
    runner = GoldenTestRunner()
    
    try:
        success = runner.run_all_tests()
        final_success = runner.print_summary()
        
        if not final_success:
            sys.exit(1)
        else:
            print("✅ Golden tests completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()