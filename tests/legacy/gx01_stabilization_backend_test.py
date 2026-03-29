#!/usr/bin/env python3
"""
GX-01 СТАБИЛИЗАЦИЯ ГЕНЕРАЦИИ V2 - COMPREHENSIVE BACKEND TESTING

Проведение детального тестирования стабилизированной генерации TechCardV2 
с новыми фоллбек-механизмами, таймаутами и инструментированием.

Test Requirements:
1. Test 5 specific dishes with performance metrics (p50 ≤ 20s, p95 ≤ 30s)
2. Verify response contract (never "failed", only "success" or "draft")
3. Check timing instrumentation in card.meta.timings
4. Test fallback mechanisms when LLM unavailable
5. Verify STRICT_ANCHORS=false setting
6. Test skeleton generation with proper structure
"""

import os
import sys
import json
import time
import requests
import statistics
from datetime import datetime
from typing import Dict, Any, List, Optional

# Test configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# GX-01 Test dishes
TEST_DISHES = [
    "Борщ украинский",
    "Цезарь салат", 
    "Карбонара паста",
    "Котлета по-киевски",
    "Бургер классический"
]

# Expected timing fields in meta.timings
REQUIRED_TIMING_FIELDS = [
    'llm_draft_ms', 'llm_normalize_ms', 'validate_ms', 'chef_rules_ms',
    'contentcheck_ms', 'cost_ms', 'nutrition_ms', 'sanitize_ms', 'total_ms'
]

class GX01StabilizationTester:
    """Comprehensive tester for GX-01 stabilization features"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json; charset=utf-8'
        })
        self.test_results = []
        self.generation_times = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result with enhanced formatting"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and data:
            print(f"    Error Data: {json.dumps(data, indent=2)}")
        print()

    def test_dish_generation(self, dish_name: str) -> Dict[str, Any]:
        """Test generation of a specific dish with full metrics"""
        print(f"🔄 Testing dish generation: {dish_name}")
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/generate",
                json={"name": dish_name},
                timeout=35  # Slightly higher than expected p95 of 30s
            )
            
            end_time = time.time()
            total_time_ms = int((end_time - start_time) * 1000)
            self.generation_times.append(total_time_ms)
            
            # Check response status
            if response.status_code != 200:
                self.log_test(
                    f"Dish Generation - {dish_name}",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return {"success": False, "total_time_ms": total_time_ms}
            
            # Check Content-Type
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type or 'charset=utf-8' not in content_type:
                self.log_test(
                    f"Content-Type Check - {dish_name}",
                    False,
                    f"Expected 'application/json; charset=utf-8', got '{content_type}'"
                )
            else:
                self.log_test(
                    f"Content-Type Check - {dish_name}",
                    True,
                    f"Correct Content-Type: {content_type}"
                )
            
            data = response.json()
            
            # GX-01 Contract: Never return "failed" status
            status = data.get('status')
            if status == 'failed':
                self.log_test(
                    f"Status Contract - {dish_name}",
                    False,
                    f"CRITICAL: Status 'failed' returned, violates GX-01 contract",
                    {"status": status, "response": data}
                )
                return {"success": False, "total_time_ms": total_time_ms, "data": data}
            elif status in ['success', 'draft']:
                self.log_test(
                    f"Status Contract - {dish_name}",
                    True,
                    f"Status '{status}' complies with GX-01 contract"
                )
            else:
                self.log_test(
                    f"Status Contract - {dish_name}",
                    False,
                    f"Unexpected status '{status}', expected 'success' or 'draft'",
                    {"status": status}
                )
            
            # Check card structure
            card = data.get('card')
            if not card:
                self.log_test(
                    f"Card Structure - {dish_name}",
                    False,
                    "No 'card' field in response",
                    {"response_keys": list(data.keys())}
                )
                return {"success": False, "total_time_ms": total_time_ms, "data": data}
            
            # Check nutrition and cost are objects (not null)
            nutrition = card.get('nutrition')
            cost = card.get('cost')
            
            nutrition_valid = isinstance(nutrition, dict) and nutrition is not None
            cost_valid = isinstance(cost, dict) and cost is not None
            
            self.log_test(
                f"Nutrition Object - {dish_name}",
                nutrition_valid,
                f"Nutrition is {'valid object' if nutrition_valid else 'null or invalid'}: {type(nutrition)}"
            )
            
            self.log_test(
                f"Cost Object - {dish_name}",
                cost_valid,
                f"Cost is {'valid object' if cost_valid else 'null or invalid'}: {type(cost)}"
            )
            
            # Check timing instrumentation
            meta = card.get('meta', {})
            timings = meta.get('timings', {})
            
            timing_results = []
            for field in REQUIRED_TIMING_FIELDS:
                if field in timings:
                    timing_value = timings[field]
                    if isinstance(timing_value, (int, float)) and timing_value >= 0:
                        timing_results.append(f"{field}: {timing_value}ms")
                    else:
                        timing_results.append(f"{field}: INVALID ({timing_value})")
                else:
                    timing_results.append(f"{field}: MISSING")
            
            missing_timings = [f for f in REQUIRED_TIMING_FIELDS if f not in timings]
            timing_success = len(missing_timings) == 0
            
            self.log_test(
                f"Timing Instrumentation - {dish_name}",
                timing_success,
                f"Missing timings: {missing_timings}" if missing_timings else "All timing fields present",
                {"timings": timings, "missing": missing_timings}
            )
            
            # Performance check
            performance_success = total_time_ms <= 30000  # p95 ≤ 30s
            self.log_test(
                f"Performance Check - {dish_name}",
                performance_success,
                f"Generation time: {total_time_ms}ms ({'✓' if total_time_ms <= 20000 else '⚠' if total_time_ms <= 30000 else '✗'} target: p50≤20s, p95≤30s)"
            )
            
            # Overall success for this dish
            dish_success = (
                response.status_code == 200 and
                status in ['success', 'draft'] and
                status != 'failed' and
                card is not None and
                nutrition_valid and
                cost_valid
            )
            
            self.log_test(
                f"Overall Generation - {dish_name}",
                dish_success,
                f"Complete generation test {'passed' if dish_success else 'failed'} in {total_time_ms}ms"
            )
            
            return {
                "success": dish_success,
                "total_time_ms": total_time_ms,
                "data": data,
                "status": status,
                "timings_complete": timing_success
            }
            
        except requests.exceptions.Timeout:
            end_time = time.time()
            total_time_ms = int((end_time - start_time) * 1000)
            self.generation_times.append(total_time_ms)
            
            self.log_test(
                f"Timeout Handling - {dish_name}",
                False,
                f"Request timed out after {total_time_ms}ms (>35s limit)",
                {"timeout_ms": total_time_ms}
            )
            return {"success": False, "total_time_ms": total_time_ms, "timeout": True}
            
        except Exception as e:
            end_time = time.time()
            total_time_ms = int((end_time - start_time) * 1000)
            self.generation_times.append(total_time_ms)
            
            self.log_test(
                f"Exception Handling - {dish_name}",
                False,
                f"Exception during generation: {str(e)}",
                {"error": str(e), "type": type(e).__name__}
            )
            return {"success": False, "total_time_ms": total_time_ms, "error": str(e)}

    def test_llm_fallback_mechanism(self):
        """Test fallback mechanism when LLM is unavailable"""
        print("🔄 Testing LLM fallback mechanism...")
        
        # First, let's check current environment settings
        try:
            # Try to get backend environment info
            response = self.session.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print("    Backend is accessible for fallback testing")
            
            # Test with a simple dish to trigger fallback
            test_dish = "Простое блюдо для теста"
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/generate",
                json={"name": test_dish, "force_fallback": True},  # Try to force fallback if supported
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                card = data.get('card', {})
                issues = data.get('issues', [])
                
                # Check for llmUnavailable issue
                llm_unavailable_issue = any(
                    issue.get('type') == 'llmUnavailable' 
                    for issue in issues
                )
                
                # Check skeleton structure
                ingredients = card.get('ingredients', [])
                process = card.get('process', [])
                portions = card.get('portions', 0)
                yield_info = card.get('yield', {})
                
                skeleton_valid = (
                    portions == 1 and
                    yield_info.get('perPortion_g') == 250 and
                    isinstance(ingredients, list) and
                    isinstance(process, list) and
                    len(process) >= 1 and
                    process[0].get('step') == 1 and
                    'Подготовка сырья' in process[0].get('action', '')
                )
                
                self.log_test(
                    "LLM Fallback - Skeleton Structure",
                    skeleton_valid,
                    f"Skeleton structure {'valid' if skeleton_valid else 'invalid'}: portions={portions}, yield={yield_info.get('perPortion_g')}, ingredients={len(ingredients)}, process_steps={len(process)}"
                )
                
                self.log_test(
                    "LLM Fallback - Issue Detection",
                    llm_unavailable_issue,
                    f"llmUnavailable issue {'found' if llm_unavailable_issue else 'not found'} in issues"
                )
                
            else:
                self.log_test(
                    "LLM Fallback Test",
                    False,
                    f"Could not test fallback mechanism: HTTP {response.status_code}",
                    {"response": response.text}
                )
                
        except Exception as e:
            self.log_test(
                "LLM Fallback Test",
                False,
                f"Exception during fallback test: {str(e)}",
                {"error": str(e)}
            )

    def test_strict_anchors_setting(self):
        """Test STRICT_ANCHORS=false setting"""
        print("🔄 Testing STRICT_ANCHORS=false setting...")
        
        try:
            # Test with a dish that might trigger anchor validation
            test_dish = "Борщ с мясом и овощами"
            
            response = self.session.post(
                f"{API_BASE}/v1/techcards.v2/generate",
                json={"name": test_dish},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get('issues', [])
                status = data.get('status')
                
                # Check that stepsMin3 doesn't block in skeleton mode
                steps_blocking = any(
                    issue.get('type') == 'stepsMin3' and issue.get('level') == 'error'
                    for issue in issues
                )
                
                # Should be warning, not error
                steps_warning = any(
                    issue.get('type') == 'stepsMin3' and issue.get('level') == 'warning'
                    for issue in issues
                )
                
                self.log_test(
                    "STRICT_ANCHORS - stepsMin3 Handling",
                    not steps_blocking,
                    f"stepsMin3 {'not blocking' if not steps_blocking else 'blocking'} (should be warning, not error)"
                )
                
                # Check that generation succeeds even with potential anchor issues
                generation_success = status in ['success', 'draft']
                
                self.log_test(
                    "STRICT_ANCHORS - Generation Success",
                    generation_success,
                    f"Generation {'succeeded' if generation_success else 'failed'} with STRICT_ANCHORS=false"
                )
                
            else:
                self.log_test(
                    "STRICT_ANCHORS Test",
                    False,
                    f"Could not test STRICT_ANCHORS: HTTP {response.status_code}",
                    {"response": response.text}
                )
                
        except Exception as e:
            self.log_test(
                "STRICT_ANCHORS Test",
                False,
                f"Exception during STRICT_ANCHORS test: {str(e)}",
                {"error": str(e)}
            )

    def calculate_performance_metrics(self):
        """Calculate p50 and p95 performance metrics"""
        if not self.generation_times:
            return None, None
            
        sorted_times = sorted(self.generation_times)
        n = len(sorted_times)
        
        p50_index = int(n * 0.5)
        p95_index = int(n * 0.95)
        
        p50 = sorted_times[p50_index] if p50_index < n else sorted_times[-1]
        p95 = sorted_times[p95_index] if p95_index < n else sorted_times[-1]
        
        return p50, p95

    def run_comprehensive_test(self):
        """Run complete GX-01 stabilization test suite"""
        print("=" * 80)
        print("GX-01 СТАБИЛИЗАЦИЯ ГЕНЕРАЦИИ V2 - COMPREHENSIVE TESTING")
        print("=" * 80)
        print()
        
        # Test 1: Generate all 5 test dishes
        print("📋 PHASE 1: Testing 5 GX-01 acceptance dishes")
        print("-" * 50)
        
        dish_results = []
        for dish in TEST_DISHES:
            result = self.test_dish_generation(dish)
            dish_results.append(result)
            time.sleep(1)  # Brief pause between tests
        
        # Test 2: Performance metrics
        print("📊 PHASE 2: Performance metrics analysis")
        print("-" * 50)
        
        p50, p95 = self.calculate_performance_metrics()
        if p50 and p95:
            p50_success = p50 <= 20000  # 20 seconds
            p95_success = p95 <= 30000  # 30 seconds
            
            self.log_test(
                "Performance Metrics - p50",
                p50_success,
                f"p50: {p50}ms ({'✓' if p50_success else '✗'} target: ≤20000ms)"
            )
            
            self.log_test(
                "Performance Metrics - p95", 
                p95_success,
                f"p95: {p95}ms ({'✓' if p95_success else '✗'} target: ≤30000ms)"
            )
            
            print(f"    All generation times: {self.generation_times}")
        else:
            self.log_test(
                "Performance Metrics",
                False,
                "No generation times recorded for metrics calculation"
            )
        
        # Test 3: Fallback mechanisms
        print("🔄 PHASE 3: Fallback mechanism testing")
        print("-" * 50)
        self.test_llm_fallback_mechanism()
        
        # Test 4: STRICT_ANCHORS setting
        print("⚙️ PHASE 4: STRICT_ANCHORS configuration testing")
        print("-" * 50)
        self.test_strict_anchors_setting()
        
        # Final summary
        print("=" * 80)
        print("FINAL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Dish generation summary
        successful_dishes = sum(1 for result in dish_results if result.get('success', False))
        print(f"Dish Generation Success: {successful_dishes}/{len(TEST_DISHES)} dishes")
        
        if p50 and p95:
            print(f"Performance: p50={p50}ms, p95={p95}ms")
        
        # Critical issues
        critical_failures = [
            result for result in self.test_results 
            if not result['success'] and 'Status Contract' in result['test']
        ]
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES:")
            for failure in critical_failures:
                print(f"  - {failure['test']}: {failure['details']}")
        
        print("\n" + "=" * 80)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "dish_success_rate": successful_dishes / len(TEST_DISHES) * 100,
            "performance_metrics": {"p50": p50, "p95": p95},
            "critical_failures": len(critical_failures)
        }

def main():
    """Main test execution"""
    tester = GX01StabilizationTester()
    
    try:
        results = tester.run_comprehensive_test()
        
        # Exit with appropriate code
        if results["success_rate"] >= 80 and results["critical_failures"] == 0:
            print("🎉 GX-01 STABILIZATION TESTS PASSED")
            sys.exit(0)
        else:
            print("🚨 GX-01 STABILIZATION TESTS FAILED")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    main()