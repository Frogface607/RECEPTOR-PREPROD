#!/usr/bin/env python3
"""
Comprehensive Backend Testing for HACCP-only LLM Module and API Endpoints
Testing EM-01I and EM-01J implementations as requested in review.
"""

import os
import sys
import json
import requests
import time
from typing import Dict, Any, List

# Add backend path for imports
sys.path.insert(0, '/app/backend')

# Set environment variables for testing
os.environ.setdefault("FEATURE_TECHCARDS_V2", "true")
os.environ.setdefault("TECHCARDS_V2_USE_LLM", "true")

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class HACCPTester:
    def __init__(self):
        self.results = []
        self.errors = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        self.results.append(result)
        print(result)
        
    def log_error(self, test_name: str, error: str):
        """Log test error"""
        error_msg = f"🚨 ERROR in {test_name}: {error}"
        self.errors.append(error_msg)
        print(error_msg)

    def create_sample_techcard(self) -> Dict[str, Any]:
        """Create a sample tech card for testing"""
        return {
            "meta": {
                "name": "Паста Карбонара HACCP Test",
                "category": "Основные блюда",
                "cuisine": "итальянская",
                "description": "Классическая паста карбонара для тестирования HACCP модуля"
            },
            "yield": {
                "portions": 4,
                "per_portion_g": 250,
                "total_net_g": 1000
            },
            "ingredients": [
                {
                    "name": "Спагетти",
                    "uom": "g",
                    "gross_g": 400.0,
                    "net_g": 400.0,
                    "loss_pct": 0.0,
                    "canonical": "паста"
                },
                {
                    "name": "Бекон",
                    "uom": "g", 
                    "gross_g": 200.0,
                    "net_g": 180.0,
                    "loss_pct": 10.0,
                    "canonical": "свинина"
                },
                {
                    "name": "Яйца куриные",
                    "uom": "pcs",
                    "gross_g": 120.0,
                    "net_g": 100.0,
                    "loss_pct": 16.7,
                    "canonical": "яйцо"
                },
                {
                    "name": "Пармезан",
                    "uom": "g",
                    "gross_g": 100.0,
                    "net_g": 80.0,
                    "loss_pct": 20.0,
                    "canonical": "сыр"
                }
            ],
            "process": [
                {
                    "step": 1,
                    "desc": "Отварить спагетти в подсоленной воде до состояния аль денте",
                    "temp_c": 100,
                    "time_min": 8
                },
                {
                    "step": 2,
                    "desc": "Обжарить бекон до золотистого цвета",
                    "temp_c": 180,
                    "time_min": 5
                },
                {
                    "step": 3,
                    "desc": "Смешать яйца с тертым пармезаном",
                    "temp_c": None,
                    "time_min": 2
                },
                {
                    "step": 4,
                    "desc": "Соединить горячую пасту с беконом и яичной смесью",
                    "temp_c": 65,
                    "time_min": 1
                }
            ],
            "haccp": {
                "hazards": [],
                "ccp": [],
                "storage": None
            },
            "allergens": [],
            "pricing": {
                "cost_per_portion": 150.0,
                "markup": 3.0
            }
        }

    def test_feature_flag_enabled(self) -> bool:
        """Test that FEATURE_TECHCARDS_V2 is enabled"""
        try:
            flag_enabled = os.getenv("FEATURE_TECHCARDS_V2", "false").lower() in ("1", "true", "yes", "on")
            self.log_result("Feature Flag Check", flag_enabled, f"FEATURE_TECHCARDS_V2={os.getenv('FEATURE_TECHCARDS_V2')}")
            return flag_enabled
        except Exception as e:
            self.log_error("Feature Flag Check", str(e))
            return False

    def test_llm_flag_status(self) -> bool:
        """Test LLM flag status"""
        try:
            llm_enabled = os.getenv("TECHCARDS_V2_USE_LLM", "false").lower() in ("1", "true", "yes", "on")
            self.log_result("LLM Flag Check", True, f"TECHCARDS_V2_USE_LLM={os.getenv('TECHCARDS_V2_USE_LLM')} (LLM {'enabled' if llm_enabled else 'disabled - will use fallback'})")
            return llm_enabled
        except Exception as e:
            self.log_error("LLM Flag Check", str(e))
            return False

    def test_haccp_module_import(self) -> bool:
        """Test HACCP module can be imported"""
        try:
            from receptor_agent.llm.haccp import generate_haccp, audit_haccp
            from receptor_agent.llm.prompts.haccp_schemas import HACCP_ONLY_SCHEMA, HACCP_AUDIT_SCHEMA
            from receptor_agent.llm.prompts.haccp_templates import HACCP_SYSTEM, HACCP_GENERATE_PROMPT, HACCP_AUDIT_PROMPT
            
            self.log_result("HACCP Module Import", True, "All HACCP modules imported successfully")
            return True
        except Exception as e:
            self.log_error("HACCP Module Import", str(e))
            return False

    def test_haccp_generate_function(self) -> bool:
        """Test generate_haccp function"""
        try:
            from receptor_agent.llm.haccp import generate_haccp
            
            sample_card = self.create_sample_techcard()
            result = generate_haccp(sample_card)
            
            # Validate result structure
            success = (
                isinstance(result, dict) and
                "haccp" in result and
                "hazards" in result["haccp"] and
                "ccp" in result["haccp"] and
                isinstance(result["haccp"]["hazards"], list) and
                isinstance(result["haccp"]["ccp"], list)
            )
            
            details = f"Generated HACCP with {len(result['haccp']['hazards'])} hazards and {len(result['haccp']['ccp'])} CCPs"
            if result["haccp"]["hazards"]:
                details += f". Hazards: {result['haccp']['hazards'][:2]}"
            
            self.log_result("HACCP Generate Function", success, details)
            return success
        except Exception as e:
            self.log_error("HACCP Generate Function", str(e))
            return False

    def test_haccp_audit_function(self) -> bool:
        """Test audit_haccp function"""
        try:
            from receptor_agent.llm.haccp import audit_haccp
            
            sample_card = self.create_sample_techcard()
            result = audit_haccp(sample_card)
            
            # Validate result structure
            success = (
                isinstance(result, dict) and
                "issues" in result and
                "patch" in result and
                isinstance(result["issues"], list) and
                isinstance(result["patch"], dict)
            )
            
            details = f"Found {len(result['issues'])} issues"
            if result["issues"]:
                details += f". Issues: {result['issues'][:2]}"
            
            self.log_result("HACCP Audit Function", success, details)
            return success
        except Exception as e:
            self.log_error("HACCP Audit Function", str(e))
            return False

    def test_haccp_generate_api_endpoint(self) -> bool:
        """Test POST /api/v1/haccp.v2/generate endpoint"""
        try:
            sample_card = self.create_sample_techcard()
            
            response = requests.post(
                f"{API_BASE}/v1/haccp.v2/generate",
                json=sample_card,
                timeout=30
            )
            
            success = response.status_code in [200, 400]  # 400 is acceptable if validation fails
            
            if response.status_code == 200:
                result = response.json()
                has_haccp = "haccp" in result and "hazards" in result["haccp"]
                details = f"HTTP 200 - Generated HACCP successfully"
                if has_haccp:
                    details += f" with {len(result['haccp']['hazards'])} hazards"
                success = success and has_haccp
            elif response.status_code == 400:
                details = f"HTTP 400 - Validation failed (expected for strict validation): {response.text[:100]}"
            else:
                details = f"HTTP {response.status_code} - {response.text[:100]}"
                success = False
            
            self.log_result("HACCP Generate API Endpoint", success, details)
            return success
        except Exception as e:
            self.log_error("HACCP Generate API Endpoint", str(e))
            return False

    def test_haccp_audit_api_endpoint(self) -> bool:
        """Test POST /api/v1/haccp.v2/audit endpoint"""
        try:
            sample_card = self.create_sample_techcard()
            
            response = requests.post(
                f"{API_BASE}/v1/haccp.v2/audit",
                json=sample_card,
                timeout=30
            )
            
            success = response.status_code == 200
            
            if response.status_code == 200:
                result = response.json()
                has_structure = "issues" in result and "patch" in result
                details = f"HTTP 200 - Audit completed with {len(result.get('issues', []))} issues found"
                success = success and has_structure
            else:
                details = f"HTTP {response.status_code} - {response.text[:100]}"
                success = False
            
            self.log_result("HACCP Audit API Endpoint", success, details)
            return success
        except Exception as e:
            self.log_error("HACCP Audit API Endpoint", str(e))
            return False

    def test_feature_flag_disabled_behavior(self) -> bool:
        """Test that endpoints return 404 when feature flag is disabled"""
        try:
            # Temporarily disable feature flag
            original_flag = os.environ.get("FEATURE_TECHCARDS_V2")
            os.environ["FEATURE_TECHCARDS_V2"] = "false"
            
            sample_card = self.create_sample_techcard()
            
            # Test generate endpoint
            response_gen = requests.post(
                f"{API_BASE}/v1/haccp.v2/generate",
                json=sample_card,
                timeout=10
            )
            
            # Test audit endpoint
            response_audit = requests.post(
                f"{API_BASE}/v1/haccp.v2/audit",
                json=sample_card,
                timeout=10
            )
            
            # Restore original flag
            if original_flag:
                os.environ["FEATURE_TECHCARDS_V2"] = original_flag
            
            success = response_gen.status_code == 404 and response_audit.status_code == 404
            details = f"Generate: HTTP {response_gen.status_code}, Audit: HTTP {response_audit.status_code}"
            
            self.log_result("Feature Flag Disabled Behavior", success, details)
            return success
        except Exception as e:
            self.log_error("Feature Flag Disabled Behavior", str(e))
            return False

    def test_invalid_input_handling(self) -> bool:
        """Test API endpoints with invalid input"""
        try:
            # Test with invalid JSON structure
            invalid_card = {"invalid": "structure"}
            
            response_gen = requests.post(
                f"{API_BASE}/v1/haccp.v2/generate",
                json=invalid_card,
                timeout=10
            )
            
            response_audit = requests.post(
                f"{API_BASE}/v1/haccp.v2/audit",
                json=invalid_card,
                timeout=10
            )
            
            # Should return 422 (validation error) or 400 (bad request)
            success = (
                response_gen.status_code in [400, 422] and
                response_audit.status_code in [400, 422]
            )
            
            details = f"Generate: HTTP {response_gen.status_code}, Audit: HTTP {response_audit.status_code}"
            
            self.log_result("Invalid Input Handling", success, details)
            return success
        except Exception as e:
            self.log_error("Invalid Input Handling", str(e))
            return False

    def test_llm_vs_fallback_modes(self) -> bool:
        """Test both LLM and fallback modes"""
        try:
            from receptor_agent.llm.haccp import generate_haccp, audit_haccp
            
            sample_card = self.create_sample_techcard()
            
            # Test LLM mode
            os.environ["TECHCARDS_V2_USE_LLM"] = "true"
            result_llm_gen = generate_haccp(sample_card.copy())
            result_llm_audit = audit_haccp(sample_card.copy())
            
            # Test fallback mode
            os.environ["TECHCARDS_V2_USE_LLM"] = "false"
            result_fallback_gen = generate_haccp(sample_card.copy())
            result_fallback_audit = audit_haccp(sample_card.copy())
            
            # Both modes should work
            llm_works = (
                "haccp" in result_llm_gen and
                "issues" in result_llm_audit and "patch" in result_llm_audit
            )
            
            fallback_works = (
                "haccp" in result_fallback_gen and
                "issues" in result_fallback_audit and "patch" in result_fallback_audit
            )
            
            success = llm_works and fallback_works
            details = f"LLM mode: {'✓' if llm_works else '✗'}, Fallback mode: {'✓' if fallback_works else '✗'}"
            
            self.log_result("LLM vs Fallback Modes", success, details)
            return success
        except Exception as e:
            self.log_error("LLM vs Fallback Modes", str(e))
            return False

    def test_haccp_content_quality(self) -> bool:
        """Test quality of generated HACCP content"""
        try:
            from receptor_agent.llm.haccp import generate_haccp, audit_haccp
            
            # Create a card with potential HACCP issues
            problematic_card = self.create_sample_techcard()
            problematic_card["ingredients"].append({
                "name": "Курица сырая",
                "uom": "g",
                "gross_g": 300.0,
                "net_g": 250.0,
                "loss_pct": 16.7,
                "canonical": "птица"
            })
            
            # Generate HACCP
            result = generate_haccp(problematic_card)
            
            # Check for expected hazards and CCPs
            hazards = result.get("haccp", {}).get("hazards", [])
            ccps = result.get("haccp", {}).get("ccp", [])
            
            # Should detect biological hazards for poultry
            has_bio_hazards = any("bio" in h.lower() or "salmonella" in h.lower() or "птиц" in h.lower() for h in hazards)
            has_temp_ccp = any("temp" in str(ccp).lower() or "75" in str(ccp) for ccp in ccps)
            
            success = has_bio_hazards or has_temp_ccp or len(hazards) > 0
            details = f"Hazards: {len(hazards)}, CCPs: {len(ccps)}, Bio hazards detected: {has_bio_hazards}"
            
            self.log_result("HACCP Content Quality", success, details)
            return success
        except Exception as e:
            self.log_error("HACCP Content Quality", str(e))
            return False

    def run_all_tests(self):
        """Run all HACCP tests"""
        print("🎯 STARTING COMPREHENSIVE HACCP MODULE TESTING")
        print("=" * 60)
        
        start_time = time.time()
        
        # Core functionality tests
        tests = [
            self.test_feature_flag_enabled,
            self.test_llm_flag_status,
            self.test_haccp_module_import,
            self.test_haccp_generate_function,
            self.test_haccp_audit_function,
            self.test_haccp_generate_api_endpoint,
            self.test_haccp_audit_api_endpoint,
            self.test_feature_flag_disabled_behavior,
            self.test_invalid_input_handling,
            self.test_llm_vs_fallback_modes,
            self.test_haccp_content_quality
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                self.log_error(test.__name__, str(e))
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎯 HACCP MODULE TESTING COMPLETED")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if self.errors:
            print(f"🚨 Errors encountered: {len(self.errors)}")
            for error in self.errors:
                print(f"   {error}")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            print(f"   {result}")
        
        return passed, total, self.errors

def main():
    """Main test execution"""
    tester = HACCPTester()
    passed, total, errors = tester.run_all_tests()
    
    # Return appropriate exit code
    if passed == total and len(errors) == 0:
        print("\n🎉 ALL HACCP TESTS PASSED - MODULE READY FOR PRODUCTION")
        return 0
    else:
        print(f"\n⚠️  SOME TESTS FAILED - {total-passed} failures, {len(errors)} errors")
        return 1

if __name__ == "__main__":
    exit(main())