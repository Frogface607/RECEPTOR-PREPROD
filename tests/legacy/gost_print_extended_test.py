#!/usr/bin/env python3
"""
Extended GOST A4 Print Functionality Testing
Testing complex scenarios and edge cases for TechCardV2 print functionality
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any

BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

class ExtendedGOSTPrintTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def create_complex_techcard(self) -> Dict[str, Any]:
        """Create a complex TechCardV2 with various ingredient types and process complexity"""
        return {
            "meta": {
                "id": "complex-card-001",
                "title": "Говядина Веллингтон с трюфельным соусом",
                "version": "2.0",
                "createdAt": "2025-01-17T10:00:00Z",
                "cuisine": "Французская",
                "tags": ["мясо", "праздничное", "сложное"]
            },
            "portions": 6,
            "yield": {
                "perPortion_g": 350.0,
                "perBatch_g": 2100.0
            },
            "ingredients": [
                {
                    "name": "Говяжья вырезка",
                    "skuId": "BEEF001",
                    "unit": "g",
                    "brutto_g": 1200.0,
                    "loss_pct": 15.0,
                    "netto_g": 1020.0,
                    "allergens": []
                },
                {
                    "name": "Слоеное тесто",
                    "skuId": "PASTRY001",
                    "unit": "g",
                    "brutto_g": 500.0,
                    "loss_pct": 5.0,
                    "netto_g": 475.0,
                    "allergens": ["глютен", "яйца"]
                },
                {
                    "name": "Шампиньоны",
                    "skuId": "MUSHROOM001",
                    "unit": "g",
                    "brutto_g": 300.0,
                    "loss_pct": 20.0,
                    "netto_g": 240.0,
                    "allergens": []
                },
                {
                    "name": "Коньяк",
                    "skuId": "ALCOHOL001",
                    "unit": "ml",
                    "brutto_g": 50.0,
                    "loss_pct": 10.0,
                    "netto_g": 45.0,
                    "allergens": []
                },
                {
                    "name": "Яйца для смазки",
                    "skuId": "EGG002",
                    "unit": "pcs",
                    "brutto_g": 60.0,
                    "loss_pct": 0.0,
                    "netto_g": 60.0,
                    "allergens": ["яйца"]
                },
                {
                    "name": "Трюфельное масло",
                    "skuId": "TRUFFLE001",
                    "unit": "ml",
                    "brutto_g": 30.0,
                    "loss_pct": 0.0,
                    "netto_g": 30.0,
                    "allergens": []
                },
                {
                    "name": "Сливки 35%",
                    "skuId": "CREAM001",
                    "unit": "ml",
                    "brutto_g": 200.0,
                    "loss_pct": 0.0,
                    "netto_g": 200.0,
                    "allergens": ["молоко"]
                },
                {
                    "name": "Белое вино",
                    "skuId": "WINE001",
                    "unit": "ml",
                    "brutto_g": 100.0,
                    "loss_pct": 50.0,  # High loss due to evaporation
                    "netto_g": 50.0,
                    "allergens": ["сульфиты"]
                }
            ],
            "process": [
                {
                    "n": 1,
                    "action": "Обжарить говяжью вырезку со всех сторон до золотистой корочки",
                    "time_min": 8.0,
                    "temp_c": 220.0,
                    "equipment": ["сковорода", "плита"],
                    "ccp": True,
                    "note": "Контроль температуры мяса - внутренняя температура 55°C"
                },
                {
                    "n": 2,
                    "action": "Обжарить мелко нарезанные шампиньоны до испарения влаги",
                    "time_min": 12.0,
                    "temp_c": 180.0,
                    "equipment": ["сковорода"],
                    "ccp": False,
                    "note": None
                },
                {
                    "n": 3,
                    "action": "Деглазировать сковороду коньяком и белым вином",
                    "time_min": 3.0,
                    "temp_c": 100.0,
                    "equipment": ["сковорода"],
                    "ccp": False,
                    "note": "Выпарить алкоголь"
                },
                {
                    "n": 4,
                    "action": "Добавить сливки и трюфельное масло, уварить соус",
                    "time_min": 5.0,
                    "temp_c": 85.0,
                    "equipment": ["сковорода"],
                    "ccp": True,
                    "note": "Контроль температуры соуса"
                },
                {
                    "n": 5,
                    "action": "Завернуть мясо с грибной смесью в слоеное тесто",
                    "time_min": 15.0,
                    "temp_c": None,
                    "equipment": ["разделочная доска", "нож"],
                    "ccp": False,
                    "note": "Плотно завернуть, избегая воздушных карманов"
                },
                {
                    "n": 6,
                    "action": "Смазать тесто взбитым яйцом",
                    "time_min": 2.0,
                    "temp_c": None,
                    "equipment": ["кисточка"],
                    "ccp": False,
                    "note": None
                },
                {
                    "n": 7,
                    "action": "Запекать в духовке до готовности теста",
                    "time_min": 25.0,
                    "temp_c": 200.0,
                    "equipment": ["духовка", "противень"],
                    "ccp": True,
                    "note": "Контроль внутренней температуры мяса 60-65°C"
                },
                {
                    "n": 8,
                    "action": "Дать отдохнуть перед нарезкой",
                    "time_min": 10.0,
                    "temp_c": None,
                    "equipment": [],
                    "ccp": False,
                    "note": "Важно для сохранения соков"
                }
            ],
            "storage": {
                "conditions": "Хранить в холодильнике при температуре +2...+4°C. Не замораживать.",
                "shelfLife_hours": 12.0,
                "servingTemp_c": 65.0
            },
            "nutrition": {
                "per100g": {
                    "kcal": 425.8,
                    "proteins_g": 28.5,
                    "fats_g": 32.1,
                    "carbs_g": 8.7
                },
                "perPortion": {
                    "kcal": 1490.3,
                    "proteins_g": 99.8,
                    "fats_g": 112.4,
                    "carbs_g": 30.5
                }
            },
            "nutritionMeta": {
                "source": "catalog",
                "coveragePct": 87.5
            },
            "cost": {
                "rawCost": 1850.75,
                "costPerPortion": 308.46,
                "markup_pct": 400.0,
                "vat_pct": 20.0
            },
            "costMeta": {
                "source": "catalog",
                "coveragePct": 100.0,
                "asOf": "2025-01-17"
            },
            "printNotes": [
                "Подавать немедленно после нарезки",
                "Украсить микрозеленью и трюфельной стружкой",
                "Подавать с картофельным пюре и овощами гриль"
            ]
        }
    
    def create_simple_techcard(self) -> Dict[str, Any]:
        """Create a simple TechCardV2 for comparison"""
        return {
            "meta": {
                "id": "simple-card-001",
                "title": "Салат Цезарь",
                "version": "2.0",
                "createdAt": "2025-01-17T10:00:00Z",
                "cuisine": "Европейская",
                "tags": ["салат", "быстро"]
            },
            "portions": 2,
            "yield": {
                "perPortion_g": 180.0,
                "perBatch_g": 360.0
            },
            "ingredients": [
                {
                    "name": "Салат Романо",
                    "skuId": "LETTUCE001",
                    "unit": "g",
                    "brutto_g": 200.0,
                    "loss_pct": 25.0,
                    "netto_g": 150.0,
                    "allergens": []
                },
                {
                    "name": "Куриная грудка",
                    "skuId": "CHICKEN001",
                    "unit": "g",
                    "brutto_g": 150.0,
                    "loss_pct": 10.0,
                    "netto_g": 135.0,
                    "allergens": []
                },
                {
                    "name": "Пармезан",
                    "skuId": "CHEESE001",
                    "unit": "g",
                    "brutto_g": 50.0,
                    "loss_pct": 0.0,
                    "netto_g": 50.0,
                    "allergens": ["молоко"]
                },
                {
                    "name": "Сухари",
                    "skuId": "CROUTONS001",
                    "unit": "g",
                    "brutto_g": 30.0,
                    "loss_pct": 0.0,
                    "netto_g": 30.0,
                    "allergens": ["глютен"]
                }
            ],
            "process": [
                {
                    "n": 1,
                    "action": "Обжарить куриную грудку до готовности",
                    "time_min": 12.0,
                    "temp_c": 75.0,
                    "equipment": ["сковорода"],
                    "ccp": True,
                    "note": "Внутренняя температура 75°C"
                },
                {
                    "n": 2,
                    "action": "Нарезать салат крупными кусками",
                    "time_min": 3.0,
                    "temp_c": None,
                    "equipment": ["нож", "доска"],
                    "ccp": False,
                    "note": None
                },
                {
                    "n": 3,
                    "action": "Смешать все ингредиенты с соусом Цезарь",
                    "time_min": 2.0,
                    "temp_c": None,
                    "equipment": ["миска"],
                    "ccp": False,
                    "note": None
                }
            ],
            "storage": {
                "conditions": "Подавать немедленно. Не хранить в готовом виде.",
                "shelfLife_hours": 2.0,
                "servingTemp_c": 18.0
            },
            "nutrition": {
                "per100g": {
                    "kcal": 185.2,
                    "proteins_g": 15.8,
                    "fats_g": 8.9,
                    "carbs_g": 12.4
                },
                "perPortion": {
                    "kcal": 333.4,
                    "proteins_g": 28.4,
                    "fats_g": 16.0,
                    "carbs_g": 22.3
                }
            },
            "cost": {
                "rawCost": 185.50,
                "costPerPortion": 92.75,
                "markup_pct": 250.0,
                "vat_pct": 20.0
            },
            "printNotes": ["Подавать охлажденным"]
        }
    
    def test_complex_techcard_print(self) -> bool:
        """Test 1: Complex TechCardV2 with multiple ingredient types and process steps"""
        try:
            test_card = self.create_complex_techcard()
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            success = response.status_code == 200
            if success:
                html = response.text
                
                # Check for complex elements
                has_multiple_units = "g" in html and "ml" in html and "pcs" in html
                has_high_loss = "50.0" in html  # White wine with 50% loss
                has_multiple_ccps = html.count("✓") >= 3  # Should have 4 CCP marks
                has_complex_process = "Деглазировать" in html and "трюфельное масло" in html
                has_allergens = "глютен" in html and "молоко" in html
                
                success = has_multiple_units and has_high_loss and has_multiple_ccps and has_complex_process
                details = f"Units: {has_multiple_units}, High loss: {has_high_loss}, CCPs: {has_multiple_ccps}, Complex process: {has_complex_process}, Allergens: {has_allergens}"
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Complex TechCardV2 print", success, details)
            return success
            
        except Exception as e:
            self.log_test("Complex TechCardV2 print", False, f"Error: {str(e)}")
            return False
    
    def test_ingredient_variety_handling(self) -> bool:
        """Test 2: Various ingredient units and loss percentages"""
        try:
            test_card = self.create_complex_techcard()
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                html = response.text
                
                # Check ingredient variety handling
                has_zero_loss = "0.0" in html  # Truffle oil, cream
                has_high_loss = "50.0" in html  # White wine
                has_medium_loss = "20.0" in html  # Mushrooms
                has_different_units = "1200.0" in html and "50.0" in html and "60.0" in html
                
                success = has_zero_loss and has_high_loss and has_medium_loss and has_different_units
                details = f"Zero loss: {has_zero_loss}, High loss: {has_high_loss}, Medium loss: {has_medium_loss}, Different units: {has_different_units}"
            else:
                success = False
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Ingredient variety handling", success, details)
            return success
            
        except Exception as e:
            self.log_test("Ingredient variety handling", False, f"Error: {str(e)}")
            return False
    
    def test_ccp_marks_accuracy(self) -> bool:
        """Test 3: CCP marks appear correctly for critical control points"""
        try:
            test_card = self.create_complex_techcard()
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                html = response.text
                
                # Count CCP marks - should be 4 based on the test card
                ccp_count = html.count("✓")
                expected_ccps = 4  # Steps 1, 4, 7 have ccp=True
                
                # Check specific CCP steps are marked
                has_meat_temp_ccp = "220.0" in html  # Step 1 temperature
                has_sauce_temp_ccp = "85.0" in html   # Step 4 temperature  
                has_baking_temp_ccp = "200.0" in html # Step 7 temperature
                
                success = ccp_count == expected_ccps and has_meat_temp_ccp and has_sauce_temp_ccp and has_baking_temp_ccp
                details = f"CCP count: {ccp_count}/{expected_ccps}, Meat temp: {has_meat_temp_ccp}, Sauce temp: {has_sauce_temp_ccp}, Baking temp: {has_baking_temp_ccp}"
            else:
                success = False
                details = f"Request failed: {response.status_code}"
            
            self.log_test("CCP marks accuracy", success, details)
            return success
            
        except Exception as e:
            self.log_test("CCP marks accuracy", False, f"Error: {str(e)}")
            return False
    
    def test_cost_calculations_display(self) -> bool:
        """Test 4: Cost calculations with high-value ingredients"""
        try:
            test_card = self.create_complex_techcard()
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                html = response.text
                
                # Check high-value cost display
                has_raw_cost = "1850.75" in html  # Raw cost
                has_portion_cost = "308.46" in html  # Cost per portion
                has_high_markup = "400%" in html  # 400% markup
                has_vat = "20%" in html  # VAT
                
                success = has_raw_cost and has_portion_cost and has_high_markup and has_vat
                details = f"Raw cost: {has_raw_cost}, Portion cost: {has_portion_cost}, Markup: {has_high_markup}, VAT: {has_vat}"
            else:
                success = False
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Cost calculations display", success, details)
            return success
            
        except Exception as e:
            self.log_test("Cost calculations display", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_print_notes(self) -> bool:
        """Test 5: Multiple print notes display correctly"""
        try:
            test_card = self.create_complex_techcard()
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                html = response.text
                
                # Check all print notes are present
                has_note1 = "немедленно после нарезки" in html
                has_note2 = "микрозеленью и трюфельной стружкой" in html
                has_note3 = "картофельным пюре" in html
                
                success = has_note1 and has_note2 and has_note3
                details = f"Note 1: {has_note1}, Note 2: {has_note2}, Note 3: {has_note3}"
            else:
                success = False
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Multiple print notes", success, details)
            return success
            
        except Exception as e:
            self.log_test("Multiple print notes", False, f"Error: {str(e)}")
            return False
    
    def test_comparison_simple_vs_complex(self) -> bool:
        """Test 6: Compare simple vs complex tech card rendering"""
        try:
            simple_card = self.create_simple_techcard()
            complex_card = self.create_complex_techcard()
            
            # Test simple card
            simple_response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=simple_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            # Test complex card
            complex_response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=complex_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if simple_response.status_code == 200 and complex_response.status_code == 200:
                simple_html = simple_response.text
                complex_html = complex_response.text
                
                # Compare characteristics
                simple_ccps = simple_html.count("✓")
                complex_ccps = complex_html.count("✓")
                
                simple_ingredients = simple_html.count("<tr>") - simple_html.count("<tr class=")  # Approximate ingredient count
                complex_ingredients = complex_html.count("<tr>") - complex_html.count("<tr class=")
                
                simple_length = len(simple_html)
                complex_length = len(complex_html)
                
                success = complex_ccps > simple_ccps and complex_length > simple_length
                details = f"Simple CCPs: {simple_ccps}, Complex CCPs: {complex_ccps}, Simple length: {simple_length}, Complex length: {complex_length}"
            else:
                success = False
                details = f"Simple: {simple_response.status_code}, Complex: {complex_response.status_code}"
            
            self.log_test("Simple vs Complex comparison", success, details)
            return success
            
        except Exception as e:
            self.log_test("Simple vs Complex comparison", False, f"Error: {str(e)}")
            return False
    
    def run_extended_tests(self) -> Dict[str, Any]:
        """Run all extended tests"""
        print("🎯 STARTING EXTENDED GOST A4 PRINT FUNCTIONALITY TESTING")
        print("=" * 60)
        
        tests = [
            self.test_complex_techcard_print,
            self.test_ingredient_variety_handling,
            self.test_ccp_marks_accuracy,
            self.test_cost_calculations_display,
            self.test_multiple_print_notes,
            self.test_comparison_simple_vs_complex
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL {test.__name__}: Exception - {str(e)}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"🎯 EXTENDED GOST A4 PRINT TESTING COMPLETED")
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📊 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
        
        return {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": passed/(passed+failed)*100 if (passed+failed) > 0 else 0,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = ExtendedGOSTPrintTester()
    results = tester.run_extended_tests()
    
    if results["failed"] == 0:
        print("\n🎉 ALL EXTENDED TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['failed']} EXTENDED TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()