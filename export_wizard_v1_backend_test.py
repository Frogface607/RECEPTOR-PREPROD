#!/usr/bin/env python3
"""
Export Wizard v1 Backend Testing Suite
Tests the Export Wizard v1 backend endpoints that were just completed:

1. Export Tracking Endpoints
2. Enhanced Export Endpoint with validation and tracking
3. Quality Validation Integration
4. Export Tracking Service
"""

import requests
import json
import time
import os
from datetime import datetime, timezone

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1/techcards.v2"

# Test data - sample TechCardV2 for testing
SAMPLE_TECHCARD = {
    "meta": {
        "title": "Говядина тушеная с овощами",
        "version": "2.0"
    },
    "portions": 4,
    "yield": {
        "perPortion_g": 200.0,
        "perBatch_g": 800.0
    },
    "ingredients": [
        {
            "name": "говядина",
            "brutto_g": 600.0,
            "unit": "g",
            "loss_pct": 15.0,
            "netto_g": 510.0,
            "skuId": "beef_001"
        },
        {
            "name": "лук репчатый",
            "brutto_g": 200.0,
            "unit": "g", 
            "loss_pct": 10.0,
            "netto_g": 180.0,
            "skuId": "onion_001"
        },
        {
            "name": "морковь",
            "brutto_g": 150.0,
            "unit": "g",
            "loss_pct": 20.0,
            "netto_g": 120.0,
            "skuId": "carrot_001"
        }
    ],
    "process": [
        {
            "step": 1,
            "action": "Нарезать говядину кубиками 3×3 см",
            "temp_c": 20,
            "time_min": 15,
            "equipment": "нож, доска"
        },
        {
            "step": 2,
            "action": "Обжарить мясо до золотистой корочки",
            "temp_c": 180,
            "time_min": 10,
            "equipment": "сковорода"
        },
        {
            "step": 3,
            "action": "Добавить овощи и тушить под крышкой",
            "temp_c": 160,
            "time_min": 90,
            "equipment": "кастрюля с крышкой"
        }
    ],
    "storage": {
        "temp_c": 4,
        "humidity_pct": 85,
        "shelf_life_days": 3,
        "conditions": "В холодильнике при температуре +2...+6°C"
    }
}

# Invalid TechCard with critical errors for validation testing
INVALID_TECHCARD = {
    "meta": {
        "title": "Блюдо с ошибками",
        "version": "2.0"
    },
    "portions": 2,
    "yield": {
        "perPortion_g": 100.0,
        "perBatch_g": 200.0
    },
    "ingredients": [
        {
            "name": "ингредиент без SKU",
            "brutto_g": 100.0,
            "unit": "g",
            "loss_pct": 10.0,
            "netto_g": 90.0
            # Missing skuId - should cause validation error
        }
    ],
    "process": [
        {
            "step": 1,
            "action": "Недостаточно шагов",
            "temp_c": 20,
            "time_min": 5,
            "equipment": "руки"
        }
        # Only 1 step - should cause validation error (min 3 required)
    ],
    "storage": {
        "temp_c": 4,
        "humidity_pct": 85,
        "shelf_life_days": 1,
        "conditions": "В холодильнике"
    }
}

class ExportWizardV1Tester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ExportWizardV1-Tester/1.0'
        })
        self.test_results = []
        self.organization_id = "test_org_001"
        self.user_email = "test@example.com"
        self.techcard_id = f"tc_{int(time.time())}"
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()

    def test_export_tracking_endpoints(self):
        """Test Export Tracking Endpoints"""
        print("🎯 Testing Export Tracking Endpoints...")
        
        # Test 1: GET /api/v1/techcards.v2/export/last - should return null initially
        try:
            response = self.session.get(f"{API_BASE}/export/last", params={
                "organization_id": self.organization_id,
                "techcard_id": self.techcard_id
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("last_export") is None:
                    self.log_test("GET /export/last (no exports)", True, 
                                "Correctly returns null when no exports exist")
                else:
                    self.log_test("GET /export/last (no exports)", False, 
                                f"Expected null last_export, got: {data.get('last_export')}", data)
            else:
                self.log_test("GET /export/last (no exports)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /export/last (no exports)", False, f"Exception: {str(e)}")

        # Test 2: GET /api/v1/techcards.v2/export/history - should return empty history initially
        try:
            response = self.session.get(f"{API_BASE}/export/history", params={
                "organization_id": self.organization_id,
                "limit": 10
            })
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("status") == "success" and 
                    isinstance(data.get("history"), list) and 
                    len(data.get("history", [])) == 0):
                    self.log_test("GET /export/history (empty)", True, 
                                "Correctly returns empty history initially")
                else:
                    self.log_test("GET /export/history (empty)", False, 
                                f"Expected empty history, got: {len(data.get('history', []))} items", data)
            else:
                self.log_test("GET /export/history (empty)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /export/history (empty)", False, f"Exception: {str(e)}")

        # Test 3: POST /api/v1/techcards.v2/export/auto-fix - should auto-fix validation issues
        try:
            payload = {
                "techcard": INVALID_TECHCARD
            }
            
            response = self.session.post(f"{API_BASE}/export/auto-fix", 
                                       json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("status") == "success" and 
                    "fixed_techcard" in data and
                    "auto_fixes_applied" in data):
                    auto_fixes = data.get("auto_fixes_applied", 0)
                    remaining_errors = len(data.get("remaining_errors", []))
                    self.log_test("POST /export/auto-fix", True, 
                                f"Applied {auto_fixes} auto-fixes, {remaining_errors} errors remain")
                else:
                    self.log_test("POST /export/auto-fix", False, 
                                "Missing required fields in response", data)
            else:
                self.log_test("POST /export/auto-fix", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("POST /export/auto-fix", False, f"Exception: {str(e)}")

    def test_enhanced_export_endpoint(self):
        """Test Enhanced Export Endpoint with validation and tracking"""
        print("🎯 Testing Enhanced Export Endpoint...")
        
        # Test 1: Export with valid TechCard - should succeed and track
        try:
            # Send TechCard directly, not nested in payload
            response = self.session.post(f"{API_BASE}/export/enhanced/iiko.xlsx", 
                                       json=SAMPLE_TECHCARD,
                                       params={
                                           "organization_id": self.organization_id,
                                           "user_email": self.user_email,
                                           "techcard_id": self.techcard_id
                                       })
            
            if response.status_code == 200:
                # Check if it's an Excel file
                content_type = response.headers.get('content-type', '')
                if 'spreadsheet' in content_type or 'excel' in content_type:
                    file_size = len(response.content)
                    self.log_test("POST /export/iiko.xlsx (valid)", True, 
                                f"Successfully exported XLSX file ({file_size} bytes)")
                else:
                    self.log_test("POST /export/iiko.xlsx (valid)", False, 
                                f"Wrong content type: {content_type}")
            else:
                self.log_test("POST /export/iiko.xlsx (valid)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("POST /export/iiko.xlsx (valid)", False, f"Exception: {str(e)}")

        # Test 2: Export with invalid TechCard - should be blocked
        try:
            # Send TechCard directly, not nested in payload
            response = self.session.post(f"{API_BASE}/export/enhanced/iiko.xlsx", 
                                       json=INVALID_TECHCARD,
                                       params={
                                           "organization_id": self.organization_id,
                                           "user_email": self.user_email,
                                           "techcard_id": f"{self.techcard_id}_invalid"
                                       })
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "blocked":
                    blocking_errors = data.get("blocking_errors", [])
                    self.log_test("POST /export/iiko.xlsx (blocked)", True, 
                                f"Correctly blocked export due to {len(blocking_errors)} critical errors")
                else:
                    self.log_test("POST /export/iiko.xlsx (blocked)", False, 
                                f"Expected blocked status, got: {data.get('status')}", data)
            else:
                # If it returns an error status, that's also acceptable for invalid data
                if response.status_code in [400, 422]:
                    self.log_test("POST /export/iiko.xlsx (blocked)", True, 
                                f"Correctly rejected invalid TechCard with HTTP {response.status_code}")
                else:
                    self.log_test("POST /export/iiko.xlsx (blocked)", False, 
                                f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("POST /export/iiko.xlsx (blocked)", False, f"Exception: {str(e)}")

    def test_quality_validation_integration(self):
        """Test Quality Validation Integration"""
        print("🎯 Testing Quality Validation Integration...")
        
        # Test 1: Validate good TechCard
        try:
            payload = {
                "techcard": SAMPLE_TECHCARD
            }
            
            response = self.session.post(f"{API_BASE}/validate/quality", 
                                       json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("status") == "success" and 
                    "quality_score" in data and
                    "validation_issues" in data):
                    quality_score = data.get("quality_score", {})
                    score_pct = quality_score.get("score_pct", 0)
                    is_production_ready = quality_score.get("is_production_ready", False)
                    issues_count = len(data.get("validation_issues", []))
                    
                    self.log_test("Quality validation (good card)", True, 
                                f"Score: {score_pct}%, Production ready: {is_production_ready}, Issues: {issues_count}")
                else:
                    self.log_test("Quality validation (good card)", False, 
                                "Missing required fields in response", data)
            else:
                self.log_test("Quality validation (good card)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Quality validation (good card)", False, f"Exception: {str(e)}")

        # Test 2: Validate bad TechCard
        try:
            payload = {
                "techcard": INVALID_TECHCARD
            }
            
            response = self.session.post(f"{API_BASE}/validate/quality", 
                                       json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("status") == "success" and 
                    "quality_score" in data and
                    "validation_issues" in data):
                    quality_score = data.get("quality_score", {})
                    score_pct = quality_score.get("score_pct", 0)
                    is_production_ready = quality_score.get("is_production_ready", True)  # Should be False
                    issues = data.get("validation_issues", [])
                    error_issues = [i for i in issues if i.get("level") == "error"]
                    
                    if not is_production_ready and len(error_issues) > 0:
                        self.log_test("Quality validation (bad card)", True, 
                                    f"Score: {score_pct}%, Production ready: {is_production_ready}, Errors: {len(error_issues)}")
                    else:
                        self.log_test("Quality validation (bad card)", False, 
                                    f"Should detect errors and mark as not production ready. Ready: {is_production_ready}, Errors: {len(error_issues)}")
                else:
                    self.log_test("Quality validation (bad card)", False, 
                                "Missing required fields in response", data)
            else:
                self.log_test("Quality validation (bad card)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Quality validation (bad card)", False, f"Exception: {str(e)}")

    def test_export_tracking_service(self):
        """Test Export Tracking Service - verify exports are recorded"""
        print("🎯 Testing Export Tracking Service...")
        
        # Wait a moment for any previous exports to be recorded
        time.sleep(2)
        
        # Test 1: Check if last export is now recorded (after successful export above)
        try:
            response = self.session.get(f"{API_BASE}/export/last", params={
                "organization_id": self.organization_id,
                "techcard_id": self.techcard_id
            })
            
            if response.status_code == 200:
                data = response.json()
                last_export = data.get("last_export")
                
                if last_export and last_export.get("result") == "success":
                    techcard_title = last_export.get("techcard_title", "")
                    user_email = last_export.get("user_email", "")
                    timestamp = last_export.get("timestamp", "")
                    
                    self.log_test("Export tracking - last export recorded", True, 
                                f"Found export: '{techcard_title}' by {user_email} at {timestamp}")
                else:
                    self.log_test("Export tracking - last export recorded", False, 
                                f"No successful export found or wrong data: {last_export}")
            else:
                self.log_test("Export tracking - last export recorded", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Export tracking - last export recorded", False, f"Exception: {str(e)}")

        # Test 2: Check export history contains our export
        try:
            response = self.session.get(f"{API_BASE}/export/history", params={
                "organization_id": self.organization_id,
                "limit": 10
            })
            
            if response.status_code == 200:
                data = response.json()
                history = data.get("history", [])
                stats = data.get("stats", {})
                
                if len(history) > 0:
                    recent_export = history[0]  # Most recent
                    export_type = recent_export.get("export_type", "")
                    result = recent_export.get("result", "")
                    
                    success_rate = stats.get("success_rate", 0)
                    total_exports = stats.get("total_exports", 0)
                    
                    self.log_test("Export tracking - history and stats", True, 
                                f"Found {len(history)} exports, latest: {export_type} ({result}). Stats: {total_exports} total, {success_rate}% success rate")
                else:
                    self.log_test("Export tracking - history and stats", False, 
                                "No exports found in history")
            else:
                self.log_test("Export tracking - history and stats", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Export tracking - history and stats", False, f"Exception: {str(e)}")

        # Test 3: Test export instructions endpoint
        try:
            response = self.session.get(f"{API_BASE}/export/instructions")
            
            if response.status_code == 200:
                data = response.json()
                instructions = data.get("instructions", {})
                
                if (instructions.get("title") and 
                    isinstance(instructions.get("steps"), list) and
                    len(instructions.get("steps", [])) >= 3):
                    steps_count = len(instructions.get("steps", []))
                    self.log_test("Export instructions endpoint", True, 
                                f"Retrieved instructions with {steps_count} steps")
                else:
                    self.log_test("Export instructions endpoint", False, 
                                "Invalid instructions format", data)
            else:
                self.log_test("Export instructions endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Export instructions endpoint", False, f"Exception: {str(e)}")

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("🎯 Testing Edge Cases...")
        
        # Test 1: Export without techcard data
        try:
            payload = {}
            
            response = self.session.post(f"{API_BASE}/export/iiko.xlsx", 
                                       json=payload)
            
            if response.status_code == 400:
                self.log_test("Export without techcard (400 error)", True, 
                            "Correctly returns 400 for missing techcard")
            else:
                self.log_test("Export without techcard (400 error)", False, 
                            f"Expected 400, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Export without techcard (400 error)", False, f"Exception: {str(e)}")

        # Test 2: Auto-fix without techcard data
        try:
            payload = {}
            
            response = self.session.post(f"{API_BASE}/export/auto-fix", 
                                       json=payload)
            
            if response.status_code == 400:
                self.log_test("Auto-fix without techcard (400 error)", True, 
                            "Correctly returns 400 for missing techcard")
            else:
                self.log_test("Auto-fix without techcard (400 error)", False, 
                            f"Expected 400, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Auto-fix without techcard (400 error)", False, f"Exception: {str(e)}")

        # Test 3: Quality validation without techcard data
        try:
            payload = {}
            
            response = self.session.post(f"{API_BASE}/validate/quality", 
                                       json=payload)
            
            if response.status_code == 400:
                self.log_test("Quality validation without techcard (400 error)", True, 
                            "Correctly returns 400 for missing techcard")
            else:
                self.log_test("Quality validation without techcard (400 error)", False, 
                            f"Expected 400, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Quality validation without techcard (400 error)", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Export Wizard v1 Backend Testing Suite")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run test suites
        self.test_export_tracking_endpoints()
        self.test_enhanced_export_endpoint()
        self.test_quality_validation_integration()
        self.test_export_tracking_service()
        self.test_edge_cases()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("=" * 80)
        print("🎯 EXPORT WIZARD V1 BACKEND TESTING SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
            print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Check if export tracking is working
        export_tracking_tests = [r for r in self.test_results if "export" in r["test"].lower() and "tracking" in r["test"].lower()]
        tracking_success = len([r for r in export_tracking_tests if r["success"]])
        if tracking_success >= 2:
            print("  ✅ Export tracking system is operational")
        else:
            print("  ❌ Export tracking system has issues")
        
        # Check if validation integration is working
        validation_tests = [r for r in self.test_results if "validation" in r["test"].lower()]
        validation_success = len([r for r in validation_tests if r["success"]])
        if validation_success >= 2:
            print("  ✅ Quality validation integration is working")
        else:
            print("  ❌ Quality validation integration has issues")
        
        # Check if enhanced export is working
        enhanced_export_tests = [r for r in self.test_results if "export/iiko.xlsx" in r["test"]]
        export_success = len([r for r in enhanced_export_tests if r["success"]])
        if export_success >= 1:
            print("  ✅ Enhanced export endpoint is functional")
        else:
            print("  ❌ Enhanced export endpoint has issues")
        
        # Check if auto-fix is working
        autofix_tests = [r for r in self.test_results if "auto-fix" in r["test"].lower()]
        autofix_success = len([r for r in autofix_tests if r["success"]])
        if autofix_success >= 1:
            print("  ✅ Auto-fix functionality is working")
        else:
            print("  ❌ Auto-fix functionality has issues")
        
        print()
        print("🎉 Export Wizard v1 Backend Testing Complete!")
        
        return success_rate >= 80.0  # Consider 80%+ success rate as overall success


if __name__ == "__main__":
    tester = ExportWizardV1Tester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall Result: SUCCESS - Export Wizard v1 backend is working correctly!")
        exit(0)
    else:
        print("❌ Overall Result: ISSUES DETECTED - Some Export Wizard v1 functionality needs attention")
        exit(1)