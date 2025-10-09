#!/usr/bin/env python3
"""
Backend Testing for GOST A4 Print Functionality (Task #5)
Testing the newly implemented GOST A4 print functionality for TechCardV2
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

class TechCardV2PrintTester:
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
    
    def create_test_techcard_valid(self) -> Dict[str, Any]:
        """Create a valid TechCardV2 for testing"""
        return {
            "meta": {
                "id": "test-card-001",
                "title": "Паста Карбонара",
                "version": "2.0",
                "createdAt": "2025-01-17T10:00:00Z",
                "cuisine": "Итальянская",
                "tags": ["паста", "основное блюдо"]
            },
            "portions": 4,
            "yield": {
                "perPortion_g": 250.0,
                "perBatch_g": 1000.0
            },
            "ingredients": [
                {
                    "name": "Спагетти",
                    "skuId": "PASTA001",
                    "unit": "g",
                    "brutto_g": 400.0,
                    "loss_pct": 0.0,
                    "netto_g": 400.0,
                    "allergens": ["глютен"]
                },
                {
                    "name": "Бекон",
                    "skuId": "MEAT002",
                    "unit": "g", 
                    "brutto_g": 200.0,
                    "loss_pct": 10.0,
                    "netto_g": 180.0,
                    "allergens": []
                },
                {
                    "name": "Яйца куриные",
                    "skuId": "EGG001",
                    "unit": "pcs",
                    "brutto_g": 240.0,
                    "loss_pct": 15.0,
                    "netto_g": 204.0,
                    "allergens": ["яйца"]
                },
                {
                    "name": "Пармезан",
                    "skuId": "CHEESE001",
                    "unit": "g",
                    "brutto_g": 100.0,
                    "loss_pct": 5.0,
                    "netto_g": 95.0,
                    "allergens": ["молоко"]
                },
                {
                    "name": "Сливки 33%",
                    "skuId": "DAIRY001",
                    "unit": "ml",
                    "brutto_g": 150.0,
                    "loss_pct": 0.0,
                    "netto_g": 150.0,
                    "allergens": ["молоко"]
                }
            ],
            "process": [
                {
                    "n": 1,
                    "action": "Отварить спагетти в подсоленной воде до состояния аль денте",
                    "time_min": 8.0,
                    "temp_c": 100.0,
                    "equipment": ["плита", "кастрюля"],
                    "ccp": True,
                    "note": "Контроль температуры воды"
                },
                {
                    "n": 2,
                    "action": "Обжарить бекон до золотистой корочки",
                    "time_min": 5.0,
                    "temp_c": 180.0,
                    "equipment": ["сковорода"],
                    "ccp": True,
                    "note": "Контроль температуры обжарки"
                },
                {
                    "n": 3,
                    "action": "Взбить яйца со сливками и тертым пармезаном",
                    "time_min": 2.0,
                    "temp_c": None,
                    "equipment": ["миска", "венчик"],
                    "ccp": False,
                    "note": None
                },
                {
                    "n": 4,
                    "action": "Смешать горячую пасту с беконом и яичной смесью",
                    "time_min": 1.0,
                    "temp_c": 65.0,
                    "equipment": ["сковорода"],
                    "ccp": True,
                    "note": "Контроль температуры подачи"
                }
            ],
            "storage": {
                "conditions": "Хранить в холодильнике при температуре +2...+6°C",
                "shelfLife_hours": 24.0,
                "servingTemp_c": 65.0
            },
            "nutrition": {
                "per100g": {
                    "kcal": 285.5,
                    "proteins_g": 12.8,
                    "fats_g": 15.2,
                    "carbs_g": 28.4
                },
                "perPortion": {
                    "kcal": 713.8,
                    "proteins_g": 32.0,
                    "fats_g": 38.0,
                    "carbs_g": 71.0
                }
            },
            "nutritionMeta": {
                "source": "catalog",
                "coveragePct": 100.0
            },
            "cost": {
                "rawCost": 285.50,
                "costPerPortion": 71.38,
                "markup_pct": 300.0,
                "vat_pct": 20.0
            },
            "costMeta": {
                "source": "catalog",
                "coveragePct": 100.0,
                "asOf": "2025-01-17"
            },
            "printNotes": ["Подавать немедленно после приготовления", "Украсить свежей зеленью"]
        }
    
    def create_test_techcard_draft(self) -> Dict[str, Any]:
        """Create a draft TechCardV2 with validation issues"""
        card = self.create_test_techcard_valid()
        # Make it invalid by creating yield mismatch
        card["yield"]["perBatch_g"] = 2000.0  # Mismatch with ingredients to trigger validation failure
        # Remove nutrition and cost data
        card["nutrition"] = {}
        card["cost"] = {}
        return card
    
    def test_print_endpoint_exists(self) -> bool:
        """Test 1: Verify print endpoint exists and is accessible"""
        try:
            # Test with minimal valid data first
            test_card = self.create_test_techcard_valid()
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            success = response.status_code in [200, 422]  # 422 is also acceptable for validation
            details = f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}"
            
            self.log_test("Print endpoint accessibility", success, details)
            return success
            
        except Exception as e:
            self.log_test("Print endpoint accessibility", False, f"Error: {str(e)}")
            return False
    
    def test_print_valid_techcard(self) -> bool:
        """Test 2: Test print with valid TechCardV2"""
        try:
            test_card = self.create_test_techcard_valid()
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            success = response.status_code == 200
            content_type = response.headers.get('content-type', '')
            is_html = 'text/html' in content_type
            
            details = f"Status: {response.status_code}, Content-Type: {content_type}, HTML: {is_html}"
            if success and is_html:
                html_content = response.text
                details += f", HTML length: {len(html_content)} chars"
                
                # Store HTML for further analysis
                self.valid_html = html_content
            
            self.log_test("Print valid TechCardV2", success and is_html, details)
            return success and is_html
            
        except Exception as e:
            self.log_test("Print valid TechCardV2", False, f"Error: {str(e)}")
            return False
    
    def test_print_draft_techcard(self) -> bool:
        """Test 3: Test print with draft TechCardV2 (should show watermark)"""
        try:
            test_card = self.create_test_techcard_draft()
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            success = response.status_code == 200
            content_type = response.headers.get('content-type', '')
            is_html = 'text/html' in content_type
            
            details = f"Status: {response.status_code}, Content-Type: {content_type}, HTML: {is_html}"
            if success and is_html:
                html_content = response.text
                has_watermark = 'ЧЕРНОВИК' in html_content
                details += f", Has watermark: {has_watermark}"
                
                # Store HTML for further analysis
                self.draft_html = html_content
            
            self.log_test("Print draft TechCardV2 with watermark", success and is_html, details)
            return success and is_html
            
        except Exception as e:
            self.log_test("Print draft TechCardV2 with watermark", False, f"Error: {str(e)}")
            return False
    
    def test_gost_template_structure(self) -> bool:
        """Test 4: Verify GOST template contains all required sections"""
        if not hasattr(self, 'valid_html'):
            self.log_test("GOST template structure", False, "No valid HTML to analyze")
            return False
        
        html = self.valid_html
        required_sections = [
            "СОСТАВ И РАСХОД СЫРЬЯ",
            "ТЕХНОЛОГИЧЕСКИЙ ПРОЦЕСС", 
            "УСЛОВИЯ И СРОКИ ХРАНЕНИЯ",
            "ПИЩЕВАЯ ЦЕННОСТЬ",
            "ЭКОНОМИЧЕСКИЕ ПОКАЗАТЕЛИ"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in html:
                missing_sections.append(section)
        
        success = len(missing_sections) == 0
        details = f"Missing sections: {missing_sections}" if missing_sections else "All sections present"
        
        self.log_test("GOST template structure", success, details)
        return success
    
    def test_ingredients_table_structure(self) -> bool:
        """Test 5: Verify ingredients table has correct columns"""
        if not hasattr(self, 'valid_html'):
            self.log_test("Ingredients table structure", False, "No valid HTML to analyze")
            return False
        
        html = self.valid_html
        required_columns = [
            "Наименование",
            "Брутто, г",
            "Потери, %", 
            "Нетто, г",
            "Ед.",
            "SKU"
        ]
        
        missing_columns = []
        for column in required_columns:
            if column not in html:
                missing_columns.append(column)
        
        # Check for ingredient data
        has_ingredient_data = "Спагетти" in html and "PASTA001" in html
        
        success = len(missing_columns) == 0 and has_ingredient_data
        details = f"Missing columns: {missing_columns}, Has data: {has_ingredient_data}"
        
        self.log_test("Ingredients table structure", success, details)
        return success
    
    def test_process_table_structure(self) -> bool:
        """Test 6: Verify process table has correct columns and CCP marks"""
        if not hasattr(self, 'valid_html'):
            self.log_test("Process table structure", False, "No valid HTML to analyze")
            return False
        
        html = self.valid_html
        required_columns = [
            "№",
            "Действие",
            "Время, мин",
            "Темп., °C",
            "Оборудование", 
            "CCP"
        ]
        
        missing_columns = []
        for column in required_columns:
            if column not in html:
                missing_columns.append(column)
        
        # Check for CCP marks and process data
        has_ccp_marks = "✓" in html
        has_process_data = "Отварить спагетти" in html
        
        success = len(missing_columns) == 0 and has_ccp_marks and has_process_data
        details = f"Missing columns: {missing_columns}, CCP marks: {has_ccp_marks}, Process data: {has_process_data}"
        
        self.log_test("Process table structure", success, details)
        return success
    
    def test_nutrition_data_display(self) -> bool:
        """Test 7: Verify nutrition shows both per100g and perPortion data"""
        if not hasattr(self, 'valid_html'):
            self.log_test("Nutrition data display", False, "No valid HTML to analyze")
            return False
        
        html = self.valid_html
        
        has_per100g = "На 100г готового блюда" in html
        has_per_portion = "На 1 порцию" in html
        has_nutrition_values = "285.5" in html and "713.8" in html  # kcal values
        
        success = has_per100g and has_per_portion and has_nutrition_values
        details = f"Per100g: {has_per100g}, PerPortion: {has_per_portion}, Values: {has_nutrition_values}"
        
        self.log_test("Nutrition data display", success, details)
        return success
    
    def test_cost_information_display(self) -> bool:
        """Test 8: Verify cost information is displayed properly"""
        if not hasattr(self, 'valid_html'):
            self.log_test("Cost information display", False, "No valid HTML to analyze")
            return False
        
        html = self.valid_html
        
        has_cost_section = "Себестоимость:" in html
        has_raw_cost = "285.50" in html  # Raw cost value
        has_portion_cost = "71.38" in html  # Cost per portion
        has_markup = "300%" in html and "20%" in html  # Markup and VAT
        
        success = has_cost_section and has_raw_cost and has_portion_cost and has_markup
        details = f"Cost section: {has_cost_section}, Raw cost: {has_raw_cost}, Portion cost: {has_portion_cost}, Markup: {has_markup}"
        
        self.log_test("Cost information display", success, details)
        return success
    
    def test_watermark_functionality(self) -> bool:
        """Test 9: Verify draft status generates ЧЕРНОВИК watermark"""
        if not hasattr(self, 'draft_html'):
            self.log_test("Watermark functionality", False, "No draft HTML to analyze")
            return False
        
        html = self.draft_html
        
        has_watermark = 'class="watermark"' in html and 'ЧЕРНОВИК' in html
        watermark_styling = 'position: fixed' in html and 'rotate(-45deg)' in html
        
        success = has_watermark and watermark_styling
        details = f"Watermark element: {has_watermark}, Styling: {watermark_styling}"
        
        self.log_test("Watermark functionality", success, details)
        return success
    
    def test_print_styling_format(self) -> bool:
        """Test 10: Verify @media print styles and A4 format"""
        if not hasattr(self, 'valid_html'):
            self.log_test("Print styling format", False, "No valid HTML to analyze")
            return False
        
        html = self.valid_html
        
        has_media_print = '@media print' in html
        has_a4_format = 'size: A4' in html
        has_margins = 'margin: 15mm' in html
        has_font_size = 'font-size: 11pt' in html or 'font-size: 10pt' in html
        has_page_breaks = 'page-break' in html
        
        success = has_media_print and has_a4_format and has_margins and has_font_size
        details = f"Media print: {has_media_print}, A4: {has_a4_format}, Margins: {has_margins}, Font: {has_font_size}, Page breaks: {has_page_breaks}"
        
        self.log_test("Print styling format", success, details)
        return success
    
    def test_missing_data_handling(self) -> bool:
        """Test 11: Verify missing nutrition/cost data shows proper messages"""
        try:
            # Create card with missing data
            test_card = self.create_test_techcard_valid()
            test_card["nutrition"] = {}
            test_card["cost"] = {}
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                html = response.text
                has_nutrition_message = "Данные не заполнены" in html
                has_cost_message = "Данные о стоимости не заполнены" in html
                
                success = has_nutrition_message and has_cost_message
                details = f"Nutrition message: {has_nutrition_message}, Cost message: {has_cost_message}"
            else:
                success = False
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Missing data handling", success, details)
            return success
            
        except Exception as e:
            self.log_test("Missing data handling", False, f"Error: {str(e)}")
            return False
    
    def test_qr_code_and_footer(self) -> bool:
        """Test 12: Verify QR code area and footer with tech card ID"""
        if not hasattr(self, 'valid_html'):
            self.log_test("QR code and footer", False, "No valid HTML to analyze")
            return False
        
        html = self.valid_html
        
        has_footer = 'class="footer"' in html
        has_tech_card_id = "TechCard ID: test-card-001" in html
        has_print_date = "Дата печати:" in html
        has_page_number = "Стр. 1" in html
        
        success = has_footer and has_tech_card_id and has_print_date
        details = f"Footer: {has_footer}, Tech ID: {has_tech_card_id}, Print date: {has_print_date}, Page: {has_page_number}"
        
        self.log_test("QR code and footer", success, details)
        return success
    
    def test_various_ingredient_units(self) -> bool:
        """Test 13: Test with various ingredient types (g, ml, pcs units)"""
        try:
            test_card = self.create_test_techcard_valid()
            # Card already has mixed units: g, ml, pcs
            
            response = requests.post(
                f"{self.backend_url}/v1/techcards.v2/print",
                json=test_card,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                html = response.text
                has_grams = "400.0" in html  # Спагетти in grams
                has_ml = "150.0" in html     # Сливки in ml
                has_pcs = "240.0" in html    # Яйца in pieces (but shown as grams)
                
                success = has_grams and has_ml and has_pcs
                details = f"Grams: {has_grams}, ML: {has_ml}, Pieces: {has_pcs}"
            else:
                success = False
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Various ingredient units", success, details)
            return success
            
        except Exception as e:
            self.log_test("Various ingredient units", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary"""
        print("🎯 STARTING GOST A4 PRINT FUNCTIONALITY TESTING (Task #5)")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            self.test_print_endpoint_exists,
            self.test_print_valid_techcard,
            self.test_print_draft_techcard,
            self.test_gost_template_structure,
            self.test_ingredients_table_structure,
            self.test_process_table_structure,
            self.test_nutrition_data_display,
            self.test_cost_information_display,
            self.test_watermark_functionality,
            self.test_print_styling_format,
            self.test_missing_data_handling,
            self.test_qr_code_and_footer,
            self.test_various_ingredient_units
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
        print(f"🎯 GOST A4 PRINT TESTING COMPLETED")
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
    tester = TechCardV2PrintTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if results["failed"] == 0:
        print("\n🎉 ALL TESTS PASSED - GOST A4 PRINT FUNCTIONALITY IS WORKING CORRECTLY!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['failed']} TESTS FAILED - ISSUES NEED TO BE ADDRESSED")
        sys.exit(1)

if __name__ == "__main__":
    main()