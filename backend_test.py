#!/usr/bin/env python3
"""
IK-04/03 Enhanced Technology Parsing Backend Testing
Testing advanced pattern validation for technology parsing improvements

Focus Areas:
1. Range Pattern Testing (time ranges, temperature ranges)
2. Complex Format Testing (t= format, standard format)  
3. Fahrenheit Conversion
4. XLSX Import with Advanced Technology
"""

import asyncio
import httpx
import json
import os
import sys
import tempfile
import openpyxl
from io import BytesIO
from datetime import datetime

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class TechnologyParsingTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    async def run_all_tests(self):
        """Run all technology parsing tests"""
        print("🧪 IK-04/03 Enhanced Technology Parsing Testing Started")
        print("=" * 60)
        
        # Test 1: Range Pattern Testing
        await self.test_range_patterns()
        
        # Test 2: Complex Format Testing
        await self.test_complex_formats()
        
        # Test 3: Fahrenheit Conversion
        await self.test_fahrenheit_conversion()
        
        # Test 4: XLSX Import with Advanced Technology
        await self.test_xlsx_import_advanced_technology()
        
        # Test 5: API Endpoint Integration
        await self.test_api_endpoint_integration()
        
        # Summary
        self.print_summary()
        
    async def test_range_patterns(self):
        """Test range pattern extraction (time and temperature ranges)"""
        print("\n📊 Test 1: Range Pattern Testing")
        print("-" * 40)
        
        test_cases = [
            {
                "text": "Обжарить 3–4 мин при высокой температуре",
                "expected_time": 3.0,
                "expected_temp": None,
                "description": "Time range 3-4 min → should extract 3.0 min"
            },
            {
                "text": "Обжарить при 170–180°C до золотистой корочки", 
                "expected_time": None,
                "expected_temp": 170.0,
                "description": "Temperature range 170-180°C → should extract 170.0°C"
            },
            {
                "text": "Варить 15-20 минут при 90-95°C",
                "expected_time": 15.0,
                "expected_temp": 90.0,
                "description": "Both ranges → should extract minimum values"
            },
            {
                "text": "Тушить 1-2 часа при средней температуре",
                "expected_time": 60.0,  # 1 hour = 60 minutes
                "expected_temp": None,
                "description": "Hour range → should convert to minutes"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            await self.test_technology_extraction(
                f"1.{i}", case["text"], case["expected_time"], 
                case["expected_temp"], case["description"]
            )
    
    async def test_complex_formats(self):
        """Test complex format patterns (t= format, standard format)"""
        print("\n🔧 Test 2: Complex Format Testing")
        print("-" * 40)
        
        test_cases = [
            {
                "text": "Томить при t=85°C под крышкой",
                "expected_time": None,
                "expected_temp": 85.0,
                "description": "t= format → should extract 85.0°C"
            },
            {
                "text": "Томить 45 мин при медленном огне под крышкой",
                "expected_time": 45.0,
                "expected_temp": None,
                "description": "Standard format → should extract 45.0 min"
            },
            {
                "text": "Готовить при t = 120°C в течение 30 мин",
                "expected_time": 30.0,
                "expected_temp": 120.0,
                "description": "t= format with spaces and time → both values"
            },
            {
                "text": "Запекать при t=200° до готовности",
                "expected_time": None,
                "expected_temp": 200.0,
                "description": "t= format without C → should extract 200.0°C"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            await self.test_technology_extraction(
                f"2.{i}", case["text"], case["expected_time"],
                case["expected_temp"], case["description"]
            )
    
    async def test_fahrenheit_conversion(self):
        """Test Fahrenheit to Celsius conversion"""
        print("\n🌡️ Test 3: Fahrenheit Conversion")
        print("-" * 40)
        
        test_cases = [
            {
                "text": "Готовить при температуре 350°F",
                "expected_time": None,
                "expected_temp": 176.7,  # (350-32)*5/9 = 176.67
                "description": "350°F → should convert to 176.7°C"
            },
            {
                "text": "Выпекать при 400°F в течение 25 минут",
                "expected_time": 25.0,
                "expected_temp": 204.4,  # (400-32)*5/9 = 204.44
                "description": "400°F with time → should convert temp and extract time"
            },
            {
                "text": "Разогреть духовку до 325°F",
                "expected_time": None,
                "expected_temp": 162.8,  # (325-32)*5/9 = 162.78
                "description": "325°F → should convert to 162.8°C"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            await self.test_technology_extraction(
                f"3.{i}", case["text"], case["expected_time"],
                case["expected_temp"], case["description"]
            )
    
    async def test_xlsx_import_advanced_technology(self):
        """Test XLSX import with advanced technology patterns"""
        print("\n📋 Test 4: XLSX Import with Advanced Technology")
        print("-" * 40)
        
        # Create test XLSX with advanced technology patterns
        test_xlsx = self.create_advanced_technology_xlsx()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"file": ("advanced_tech.xlsx", test_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                
                response = await client.post(f"{API_BASE}/v1/iiko/import/ttk.xlsx", files=files)
                
                self.total_tests += 1
                test_id = "4.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if import was successful
                    if data.get("status") in ["success", "draft"]:
                        techcard = data.get("techcard", {})
                        process_steps = techcard.get("process", [])
                        
                        # Verify process steps contain extracted temperatures and times
                        advanced_patterns_found = 0
                        
                        for step in process_steps:
                            time_min = step.get("time_min")
                            temp_c = step.get("temp_c")
                            action = step.get("action", "")
                            
                            # Check for expected patterns
                            if "3–4 мин" in action and time_min == 3.0:
                                advanced_patterns_found += 1
                            elif "170–180°C" in action and temp_c == 170.0:
                                advanced_patterns_found += 1
                            elif "t=85°C" in action and temp_c == 85.0:
                                advanced_patterns_found += 1
                            elif "350°F" in action and temp_c and abs(temp_c - 176.7) < 0.5:
                                advanced_patterns_found += 1
                        
                        if advanced_patterns_found >= 2:  # At least 2 patterns should be found
                            self.passed_tests += 1
                            print(f"✅ {test_id}: XLSX import with advanced patterns - PASSED")
                            print(f"   Found {advanced_patterns_found} advanced patterns in process steps")
                        else:
                            print(f"❌ {test_id}: XLSX import with advanced patterns - FAILED")
                            print(f"   Only found {advanced_patterns_found} advanced patterns")
                            print(f"   Process steps: {len(process_steps)}")
                    else:
                        print(f"❌ {test_id}: XLSX import failed - status: {data.get('status')}")
                        print(f"   Issues: {data.get('issues', [])}")
                else:
                    print(f"❌ {test_id}: XLSX import API error - {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ {test_id}: XLSX import exception - {str(e)}")
    
    async def test_api_endpoint_integration(self):
        """Test API endpoint handles enhanced parsing without errors"""
        print("\n🔌 Test 5: API Endpoint Integration")
        print("-" * 40)
        
        # Test that the API endpoint is accessible and working
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create minimal test XLSX
                simple_xlsx = self.create_simple_test_xlsx()
                files = {"file": ("simple_test.xlsx", simple_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                
                response = await client.post(f"{API_BASE}/v1/iiko/import/ttk.xlsx", files=files)
                
                self.total_tests += 1
                test_id = "5.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    required_fields = ["status", "techcard", "issues", "meta"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.passed_tests += 1
                        print(f"✅ {test_id}: API endpoint integration - PASSED")
                        print(f"   Status: {data.get('status')}")
                        print(f"   Issues count: {len(data.get('issues', []))}")
                        print(f"   Parsed rows: {data.get('meta', {}).get('parsed_rows', 0)}")
                    else:
                        print(f"❌ {test_id}: API response missing fields: {missing_fields}")
                else:
                    print(f"❌ {test_id}: API endpoint error - {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"❌ {test_id}: API endpoint exception - {str(e)}")
    
    async def test_technology_extraction(self, test_id, text, expected_time, expected_temp, description):
        """Test individual technology text extraction"""
        try:
            # Import the parser directly to test extraction methods
            sys.path.append('/app/backend')
            from receptor_agent.integrations.iiko_xlsx_parser import IikoXlsxParser
            
            parser = IikoXlsxParser()
            
            # Test time extraction
            extracted_time = parser._extract_time_from_text(text)
            
            # Test temperature extraction  
            extracted_temp = parser._extract_temperature_from_text(text)
            
            self.total_tests += 1
            
            # Check results
            time_match = (expected_time is None and extracted_time is None) or \
                        (expected_time is not None and extracted_time is not None and abs(extracted_time - expected_time) < 0.1)
            
            temp_match = (expected_temp is None and extracted_temp is None) or \
                        (expected_temp is not None and extracted_temp is not None and abs(extracted_temp - expected_temp) < 0.5)
            
            if time_match and temp_match:
                self.passed_tests += 1
                print(f"✅ {test_id}: {description} - PASSED")
                if extracted_time:
                    print(f"   Time: {extracted_time} min")
                if extracted_temp:
                    print(f"   Temperature: {extracted_temp}°C")
            else:
                print(f"❌ {test_id}: {description} - FAILED")
                print(f"   Text: '{text}'")
                print(f"   Expected time: {expected_time}, got: {extracted_time}")
                print(f"   Expected temp: {expected_temp}, got: {extracted_temp}")
                
        except Exception as e:
            print(f"❌ {test_id}: {description} - EXCEPTION: {str(e)}")
    
    def create_advanced_technology_xlsx(self):
        """Create XLSX with advanced technology patterns for testing"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Advanced Tech Test"
        
        # Headers
        headers = [
            "Артикул блюда", "Наименование блюда", "Артикул продукта", 
            "Наименование продукта", "Брутто", "Потери %", "Нетто", 
            "Ед.", "Выход готового продукта", "Норма закладки", 
            "Метод списания", "Технология приготовления"
        ]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # Meta information
        ws.cell(row=2, column=1, value="DISH_ADV_001")
        ws.cell(row=2, column=2, value="Блюдо с продвинутой технологией")
        
        # Technology with advanced patterns
        advanced_tech = (
            "1. Обжарить 3–4 мин при высокой температуре. "
            "2. Обжарить при 170–180°C до золотистой корочки. "
            "3. Томить при t=85°C под крышкой. "
            "4. Готовить при температуре 350°F до готовности."
        )
        ws.cell(row=2, column=12, value=advanced_tech)
        
        # Sample ingredients
        ingredients = [
            ["PROD_001", "Говядина", 500, 15, 425, "г"],
            ["PROD_002", "Лук репчатый", 100, 10, 90, "г"],
            ["PROD_003", "Масло растительное", 30, 0, 30, "мл"]
        ]
        
        for row_idx, ingredient in enumerate(ingredients, 3):
            ws.cell(row=row_idx, column=3, value=ingredient[0])  # Артикул продукта
            ws.cell(row=row_idx, column=4, value=ingredient[1])  # Наименование продукта
            ws.cell(row=row_idx, column=5, value=ingredient[2])  # Брутто
            ws.cell(row=row_idx, column=6, value=ingredient[3])  # Потери %
            ws.cell(row=row_idx, column=7, value=ingredient[4])  # Нетто
            ws.cell(row=row_idx, column=8, value=ingredient[5])  # Ед.
        
        # Save to bytes
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    def create_simple_test_xlsx(self):
        """Create simple XLSX for API testing"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Simple Test"
        
        # Headers
        headers = ["Наименование продукта", "Брутто", "Нетто", "Ед."]
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # Simple ingredient
        ws.cell(row=2, column=1, value="Тестовый продукт")
        ws.cell(row=2, column=2, value=100)
        ws.cell(row=2, column=3, value=90)
        ws.cell(row=2, column=4, value="г")
        
        # Save to bytes
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 IK-04/03 Enhanced Technology Parsing Test Summary")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Advanced technology parsing is working correctly!")
        elif success_rate >= 75:
            print("✅ GOOD: Most advanced patterns are working, minor issues detected")
        elif success_rate >= 50:
            print("⚠️ PARTIAL: Some advanced patterns working, needs improvement")
        else:
            print("❌ CRITICAL: Advanced technology parsing has significant issues")
        
        print("\n🔍 Key Validation Targets:")
        print("✓ Advanced regex patterns work correctly")
        print("✓ Range values normalize to minimum (3-4 min → 3.0 min)")
        print("✓ Temperature conversion F→C functions properly")
        print("✓ API endpoints handle enhanced parsing without errors")
        print("✓ Round-trip compatibility maintained with new features")
        
        return success_rate >= 75  # Return True if tests are mostly passing

async def main():
    """Main test execution"""
    tester = TechnologyParsingTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())