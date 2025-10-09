#!/usr/bin/env python3
"""
ZIP Export HTTP 500 Validation Fix Test
Testing the fix for HTTP 500 error in ZIP export due to Pydantic validation after operational rounding.
The fix increased validation tolerance from ±1g to ±3g for compatibility with operational rounding.
"""

import asyncio
import json
import os
import sys
import time
import traceback
import zipfile
import io
from datetime import datetime
from typing import Dict, List, Any, Optional

import httpx
from pymongo import MongoClient

# Test Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
DB_NAME = os.getenv('DB_NAME', 'receptor_pro')

class ZipExportValidationTester:
    """Test suite for ZIP export HTTP 500 validation fix"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.organization_id = "test-org-zip-validation"
        self.generated_techcard_ids = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0.0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.3f}s" if response_time > 0 else "N/A"
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} ({response_time:.3f}s) - {details}")
    
    async def generate_new_techcard(self, dish_name: str) -> Optional[str]:
        """Generate a new tech card for testing"""
        try:
            start_time = time.time()
            
            payload = {
                "name": dish_name,
                "description": f"Тестовое блюдо для проверки исправления HTTP 500 в ZIP экспорте: {dish_name}",
                "category": "горячее",
                "portions": 1
            }
            
            response = await self.client.post(f"{API_BASE}/techcards.v2/generate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Try different possible ID fields
                techcard_id = (data.get("id") or 
                             data.get("techcard_id") or 
                             data.get("uuid") or
                             (data.get("card", {}).get("meta", {}).get("id") if isinstance(data.get("card"), dict) else None))
                
                if techcard_id:
                    self.generated_techcard_ids.append(techcard_id)
                    self.log_test(f"Generate TechCard: {dish_name}", True, 
                                f"ID: {techcard_id[:8]}...", response_time)
                    return techcard_id
                else:
                    self.log_test(f"Generate TechCard: {dish_name}", False, 
                                f"No ID in response. Keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}", response_time)
                    return None
            else:
                self.log_test(f"Generate TechCard: {dish_name}", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                return None
                
        except Exception as e:
            self.log_test(f"Generate TechCard: {dish_name}", False, f"Exception: {str(e)}", 0.0)
            return None
    
    async def test_zip_export_no_http500(self, techcard_id: str, dish_name: str):
        """Test that ZIP export doesn't return HTTP 500 with operational rounding"""
        try:
            start_time = time.time()
            
            # First run preflight
            preflight_payload = {
                "techcardIds": [techcard_id],
                "organization_id": self.organization_id
            }
            
            preflight_response = await self.client.post(f"{API_BASE}/export/preflight", json=preflight_payload)
            
            if preflight_response.status_code != 200:
                self.log_test(f"ZIP Export Preflight: {dish_name}", False, 
                            f"Preflight failed: HTTP {preflight_response.status_code}", 0.0)
                return False
            
            preflight_data = preflight_response.json()
            
            # Now test ZIP export with operational rounding
            export_payload = {
                "techcardIds": [techcard_id],
                "operational_rounding": True,  # This was causing the HTTP 500
                "organization_id": self.organization_id,
                "preflight_result": preflight_data
            }
            
            export_response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
            response_time = time.time() - start_time
            
            # Check for HTTP 500 error
            if export_response.status_code == 500:
                self.log_test(f"ZIP Export No HTTP 500: {dish_name}", False, 
                            f"Still getting HTTP 500: {export_response.text[:200]}", response_time)
                return False
            elif export_response.status_code == 200:
                # Check if we got a ZIP file
                is_zip = export_response.content.startswith(b'PK')
                zip_size = len(export_response.content)
                
                if is_zip and zip_size > 0:
                    self.log_test(f"ZIP Export No HTTP 500: {dish_name}", True, 
                                f"ZIP created successfully: {zip_size} bytes", response_time)
                    return True
                else:
                    self.log_test(f"ZIP Export No HTTP 500: {dish_name}", False, 
                                f"Response not a ZIP file: {zip_size} bytes", response_time)
                    return False
            else:
                self.log_test(f"ZIP Export No HTTP 500: {dish_name}", False, 
                            f"HTTP {export_response.status_code}: {export_response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"ZIP Export No HTTP 500: {dish_name}", False, f"Exception: {str(e)}", 0.0)
            return False
    
    async def test_operational_rounding_validation(self, techcard_id: str, dish_name: str):
        """Test that operational rounding validation now works with ±3g tolerance"""
        try:
            start_time = time.time()
            
            # Test export with operational_rounding=true
            preflight_payload = {
                "techcardIds": [techcard_id],
                "organization_id": self.organization_id
            }
            
            preflight_response = await self.client.post(f"{API_BASE}/export/preflight", json=preflight_payload)
            
            if preflight_response.status_code != 200:
                self.log_test(f"Operational Rounding Validation: {dish_name}", False, 
                            "Preflight failed", 0.0)
                return False
            
            export_payload = {
                "techcardIds": [techcard_id],
                "operational_rounding": True,
                "organization_id": self.organization_id,
                "preflight_result": preflight_response.json()
            }
            
            export_response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
            response_time = time.time() - start_time
            
            # The key test: should not fail with validation errors
            if export_response.status_code == 200:
                # Check if ZIP was created successfully
                is_zip = export_response.content.startswith(b'PK')
                
                if is_zip:
                    self.log_test(f"Operational Rounding Validation: {dish_name}", True, 
                                "Validation passed with operational rounding", response_time)
                    return True
                else:
                    self.log_test(f"Operational Rounding Validation: {dish_name}", False, 
                                "Response not a ZIP file", response_time)
                    return False
            elif export_response.status_code == 422:
                # Check if it's a validation error related to netto_g
                error_text = export_response.text.lower()
                if "netto" in error_text or "validation" in error_text:
                    self.log_test(f"Operational Rounding Validation: {dish_name}", False, 
                                f"Still getting validation errors: {export_response.text[:200]}", response_time)
                    return False
                else:
                    self.log_test(f"Operational Rounding Validation: {dish_name}", False, 
                                f"HTTP 422 (other): {export_response.text[:200]}", response_time)
                    return False
            else:
                self.log_test(f"Operational Rounding Validation: {dish_name}", False, 
                            f"HTTP {export_response.status_code}: {export_response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"Operational Rounding Validation: {dish_name}", False, f"Exception: {str(e)}", 0.0)
            return False
    
    async def test_zip_content_validation(self, techcard_id: str, dish_name: str):
        """Test that ZIP contains expected files and structure"""
        try:
            start_time = time.time()
            
            # Run preflight and export
            preflight_payload = {
                "techcardIds": [techcard_id],
                "organization_id": self.organization_id
            }
            
            preflight_response = await self.client.post(f"{API_BASE}/export/preflight", json=preflight_payload)
            
            if preflight_response.status_code != 200:
                self.log_test(f"ZIP Content Validation: {dish_name}", False, "Preflight failed", 0.0)
                return False
            
            export_payload = {
                "techcardIds": [techcard_id],
                "operational_rounding": True,
                "organization_id": self.organization_id,
                "preflight_result": preflight_response.json()
            }
            
            export_response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
            response_time = time.time() - start_time
            
            if export_response.status_code == 200 and export_response.content.startswith(b'PK'):
                # Validate ZIP contents
                try:
                    zip_buffer = io.BytesIO(export_response.content)
                    with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                        file_list = zip_file.namelist()
                        
                        # Check for expected files
                        has_ttk_file = any('iiko_TTK.xlsx' in f for f in file_list)
                        file_count = len(file_list)
                        
                        if has_ttk_file and file_count > 0:
                            self.log_test(f"ZIP Content Validation: {dish_name}", True, 
                                        f"ZIP contains {file_count} files including TTK", response_time)
                            return True
                        else:
                            self.log_test(f"ZIP Content Validation: {dish_name}", False, 
                                        f"Missing expected files: {file_list}", response_time)
                            return False
                            
                except zipfile.BadZipFile:
                    self.log_test(f"ZIP Content Validation: {dish_name}", False, 
                                "Invalid ZIP file", response_time)
                    return False
            else:
                self.log_test(f"ZIP Content Validation: {dish_name}", False, 
                            f"Export failed: HTTP {export_response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"ZIP Content Validation: {dish_name}", False, f"Exception: {str(e)}", 0.0)
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of the ZIP export validation fix"""
        print("🎯 ZIP EXPORT HTTP 500 VALIDATION FIX TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing validation tolerance fix (±1g → ±3g)")
        print()
        
        # Test dishes that might trigger operational rounding issues
        test_dishes = [
            "Борщ украинский с мясом",
            "Стейк из говядины с гарниром", 
            "Салат Цезарь с курицей"
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for dish_name in test_dishes:
            print(f"\n🍽️ Testing with dish: {dish_name}")
            print("-" * 40)
            
            # Step 1: Generate new tech card
            techcard_id = await self.generate_new_techcard(dish_name)
            if not techcard_id:
                continue
            
            # Step 2: Test ZIP export doesn't return HTTP 500
            test1_result = await self.test_zip_export_no_http500(techcard_id, dish_name)
            total_tests += 1
            if test1_result:
                passed_tests += 1
            
            # Step 3: Test operational rounding validation
            test2_result = await self.test_operational_rounding_validation(techcard_id, dish_name)
            total_tests += 1
            if test2_result:
                passed_tests += 1
            
            # Step 4: Test ZIP content validation
            test3_result = await self.test_zip_content_validation(techcard_id, dish_name)
            total_tests += 1
            if test3_result:
                passed_tests += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 ZIP EXPORT VALIDATION FIX TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if passed_tests == total_tests:
            print("\n✅ ALL TESTS PASSED - ZIP Export HTTP 500 fix is working correctly!")
            print("✅ Operational rounding validation tolerance fix (±3g) is operational")
            print("✅ ZIP export creates files without HTTP 500 errors")
        else:
            print(f"\n❌ {total_tests - passed_tests} TESTS FAILED - ZIP Export fix needs attention")
            
            # Show failed tests
            failed_tests = [r for r in self.test_results if not r["success"]]
            if failed_tests:
                print("\nFailed Tests:")
                for test in failed_tests:
                    print(f"  ❌ {test['test']}: {test['details']}")
        
        print(f"\nGenerated TechCard IDs: {len(self.generated_techcard_ids)}")
        for i, tc_id in enumerate(self.generated_techcard_ids, 1):
            print(f"  {i}. {tc_id}")
        
        return success_rate >= 80  # 80% success rate threshold

async def main():
    """Main test execution"""
    try:
        async with ZipExportValidationTester() as tester:
            success = await tester.run_comprehensive_test()
            return 0 if success else 1
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)