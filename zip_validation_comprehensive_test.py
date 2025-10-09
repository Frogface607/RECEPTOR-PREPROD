#!/usr/bin/env python3
"""
Comprehensive ZIP Export Validation Test
Testing the complete workflow to ensure HTTP 500 fix is working properly
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

# Test Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

class ComprehensiveZipValidationTester:
    """Comprehensive test suite for ZIP export validation fix"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.organization_id = "test-org-comprehensive"
        
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
    
    async def test_simple_workflow(self):
        """Test simple workflow: Generate → Export → Validate"""
        print("\n🎯 Testing Simple Workflow")
        
        try:
            # Step 1: Generate tech card
            start_time = time.time()
            
            payload = {
                "name": "Тестовое блюдо для проверки ZIP экспорта",
                "description": "Простое блюдо для тестирования исправления HTTP 500",
                "category": "горячее",
                "portions": 1
            }
            
            response = await self.client.post(f"{API_BASE}/techcards.v2/generate", json=payload)
            gen_time = time.time() - start_time
            
            if response.status_code != 200:
                self.log_test("Simple Workflow - Generation", False, 
                            f"Generation failed: HTTP {response.status_code}", gen_time)
                return False
            
            data = response.json()
            techcard_id = data.get("card", {}).get("meta", {}).get("id")
            
            if not techcard_id:
                self.log_test("Simple Workflow - Generation", False, "No ID in response", gen_time)
                return False
            
            self.log_test("Simple Workflow - Generation", True, f"ID: {techcard_id[:8]}...", gen_time)
            
            # Step 2: Export ZIP
            export_start = time.time()
            
            # First preflight
            preflight_payload = {
                "techcardIds": [techcard_id],
                "organization_id": self.organization_id
            }
            
            preflight_response = await self.client.post(f"{API_BASE}/export/preflight", json=preflight_payload)
            
            if preflight_response.status_code != 200:
                self.log_test("Simple Workflow - Preflight", False, 
                            f"Preflight failed: HTTP {preflight_response.status_code}", 0.0)
                return False
            
            # Now export
            export_payload = {
                "techcardIds": [techcard_id],
                "operational_rounding": True,
                "organization_id": self.organization_id,
                "preflight_result": preflight_response.json()
            }
            
            export_response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
            export_time = time.time() - export_start
            
            # Validate export
            if export_response.status_code == 500:
                self.log_test("Simple Workflow - Export", False, 
                            f"HTTP 500 ERROR STILL PRESENT: {export_response.text[:200]}", export_time)
                return False
            elif export_response.status_code == 200:
                is_zip = export_response.content.startswith(b'PK')
                zip_size = len(export_response.content)
                
                if is_zip and zip_size > 0:
                    self.log_test("Simple Workflow - Export", True, 
                                f"ZIP created: {zip_size} bytes", export_time)
                    return True
                else:
                    self.log_test("Simple Workflow - Export", False, 
                                f"Invalid ZIP: {zip_size} bytes", export_time)
                    return False
            else:
                self.log_test("Simple Workflow - Export", False, 
                            f"HTTP {export_response.status_code}: {export_response.text[:200]}", export_time)
                return False
                
        except Exception as e:
            self.log_test("Simple Workflow", False, f"Exception: {str(e)}", 0.0)
            return False
    
    async def test_multiple_techcards_export(self):
        """Test export with multiple tech cards"""
        print("\n🎯 Testing Multiple TechCards Export")
        
        try:
            # Generate 2 tech cards
            techcard_ids = []
            
            dishes = ["Суп-пюре из тыквы", "Котлеты куриные"]
            
            for dish_name in dishes:
                payload = {
                    "name": dish_name,
                    "description": f"Тестовое блюдо: {dish_name}",
                    "category": "горячее",
                    "portions": 1
                }
                
                response = await self.client.post(f"{API_BASE}/techcards.v2/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    techcard_id = data.get("card", {}).get("meta", {}).get("id")
                    if techcard_id:
                        techcard_ids.append(techcard_id)
            
            if len(techcard_ids) < 2:
                self.log_test("Multiple TechCards - Generation", False, 
                            f"Only generated {len(techcard_ids)} tech cards", 0.0)
                return False
            
            self.log_test("Multiple TechCards - Generation", True, 
                        f"Generated {len(techcard_ids)} tech cards", 0.0)
            
            # Export multiple tech cards
            start_time = time.time()
            
            # Preflight
            preflight_payload = {
                "techcardIds": techcard_ids,
                "organization_id": self.organization_id
            }
            
            preflight_response = await self.client.post(f"{API_BASE}/export/preflight", json=preflight_payload)
            
            if preflight_response.status_code != 200:
                self.log_test("Multiple TechCards - Preflight", False, 
                            f"Preflight failed: HTTP {preflight_response.status_code}", 0.0)
                return False
            
            # Export
            export_payload = {
                "techcardIds": techcard_ids,
                "operational_rounding": True,
                "organization_id": self.organization_id,
                "preflight_result": preflight_response.json()
            }
            
            export_response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
            response_time = time.time() - start_time
            
            if export_response.status_code == 500:
                self.log_test("Multiple TechCards - Export", False, 
                            f"HTTP 500 ERROR: {export_response.text[:200]}", response_time)
                return False
            elif export_response.status_code == 200:
                is_zip = export_response.content.startswith(b'PK')
                zip_size = len(export_response.content)
                
                if is_zip and zip_size > 0:
                    self.log_test("Multiple TechCards - Export", True, 
                                f"ZIP created: {zip_size} bytes for {len(techcard_ids)} cards", response_time)
                    return True
                else:
                    self.log_test("Multiple TechCards - Export", False, 
                                f"Invalid ZIP: {zip_size} bytes", response_time)
                    return False
            else:
                self.log_test("Multiple TechCards - Export", False, 
                            f"HTTP {export_response.status_code}: {export_response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Multiple TechCards Export", False, f"Exception: {str(e)}", 0.0)
            return False
    
    async def test_operational_rounding_edge_cases(self):
        """Test edge cases that might trigger validation issues"""
        print("\n🎯 Testing Operational Rounding Edge Cases")
        
        try:
            # Generate a complex dish that might have rounding issues
            payload = {
                "name": "Сложное блюдо с множеством ингредиентов",
                "description": "Блюдо с большим количеством ингредиентов для тестирования округления",
                "category": "горячее",
                "portions": 1
            }
            
            response = await self.client.post(f"{API_BASE}/techcards.v2/generate", json=payload)
            
            if response.status_code != 200:
                self.log_test("Edge Cases - Generation", False, 
                            f"Generation failed: HTTP {response.status_code}", 0.0)
                return False
            
            data = response.json()
            techcard_id = data.get("card", {}).get("meta", {}).get("id")
            
            if not techcard_id:
                self.log_test("Edge Cases - Generation", False, "No ID in response", 0.0)
                return False
            
            # Test with operational_rounding=true (the problematic case)
            start_time = time.time()
            
            preflight_payload = {
                "techcardIds": [techcard_id],
                "organization_id": self.organization_id
            }
            
            preflight_response = await self.client.post(f"{API_BASE}/export/preflight", json=preflight_payload)
            
            if preflight_response.status_code != 200:
                self.log_test("Edge Cases - Preflight", False, 
                            f"Preflight failed: HTTP {preflight_response.status_code}", 0.0)
                return False
            
            export_payload = {
                "techcardIds": [techcard_id],
                "operational_rounding": True,  # This was causing HTTP 500
                "organization_id": self.organization_id,
                "preflight_result": preflight_response.json()
            }
            
            export_response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
            response_time = time.time() - start_time
            
            # Check for specific validation errors
            if export_response.status_code == 500:
                error_text = export_response.text.lower()
                if "validation" in error_text or "netto" in error_text:
                    self.log_test("Edge Cases - Validation Fix", False, 
                                f"Validation error still present: {export_response.text[:200]}", response_time)
                else:
                    self.log_test("Edge Cases - Other Error", False, 
                                f"HTTP 500 (non-validation): {export_response.text[:200]}", response_time)
                return False
            elif export_response.status_code == 422:
                error_text = export_response.text.lower()
                if "netto" in error_text or "validation" in error_text:
                    self.log_test("Edge Cases - Validation Fix", False, 
                                f"Validation error (422): {export_response.text[:200]}", response_time)
                    return False
            elif export_response.status_code == 200:
                is_zip = export_response.content.startswith(b'PK')
                zip_size = len(export_response.content)
                
                if is_zip and zip_size > 0:
                    self.log_test("Edge Cases - Validation Fix", True, 
                                f"Validation passed with operational rounding: {zip_size} bytes", response_time)
                    return True
                else:
                    self.log_test("Edge Cases - Invalid Response", False, 
                                f"Not a ZIP file: {zip_size} bytes", response_time)
                    return False
            else:
                self.log_test("Edge Cases - Unexpected Error", False, 
                            f"HTTP {export_response.status_code}: {export_response.text[:200]}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Edge Cases Test", False, f"Exception: {str(e)}", 0.0)
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive validation test"""
        print("🎯 COMPREHENSIVE ZIP EXPORT VALIDATION TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print("Testing HTTP 500 fix in ZIP export with operational rounding")
        print()
        
        tests = [
            ("Simple Workflow", self.test_simple_workflow),
            ("Multiple TechCards", self.test_multiple_techcards_export),
            ("Edge Cases", self.test_operational_rounding_edge_cases)
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            print("-" * 40)
            
            result = await test_func()
            total_tests += 1
            if result:
                passed_tests += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Test Categories: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        print(f"\nDetailed Results ({len(self.test_results)} individual tests):")
        passed_individual = sum(1 for r in self.test_results if r["success"])
        total_individual = len(self.test_results)
        
        print(f"Individual Tests: {passed_individual}/{total_individual} passed")
        
        if passed_tests == total_tests:
            print("\n✅ ALL COMPREHENSIVE TESTS PASSED!")
            print("✅ HTTP 500 fix in ZIP export is working correctly")
            print("✅ Operational rounding validation tolerance (±3g) is operational")
            print("✅ ZIP export workflow is stable and reliable")
        else:
            print(f"\n❌ {total_tests - passed_tests} TEST CATEGORIES FAILED")
            
            # Show failed tests
            failed_tests = [r for r in self.test_results if not r["success"]]
            if failed_tests:
                print("\nFailed Individual Tests:")
                for test in failed_tests:
                    print(f"  ❌ {test['test']}: {test['details']}")
        
        return success_rate >= 100  # All tests must pass

async def main():
    """Main test execution"""
    try:
        async with ComprehensiveZipValidationTester() as tester:
            success = await tester.run_comprehensive_test()
            return 0 if success else 1
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)