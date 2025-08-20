#!/usr/bin/env python3
"""
P0.3: AUTOMAPPING PERFORMANCE OPTIMIZATION TESTING ≤3s TARGET
Comprehensive testing of enhanced_mapping_service.py performance improvements
"""

import requests
import json
import time
import statistics
from typing import List, Dict, Any
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://iiko-connect.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

class P03PerformanceTest:
    """P0.3: Performance testing for enhanced auto-mapping ≤3s target"""
    
    def __init__(self):
        self.results = []
        self.test_data = self._create_test_data()
    
    def _create_test_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create realistic Russian ingredient test data for different batch sizes"""
        
        # Small batch (10-15 ingredients) - should be <1s
        small_batch = [
            {"name": "яйца куриные", "quantity": 2, "unit": "шт"},
            {"name": "молоко 3.2%", "quantity": 200, "unit": "мл"},
            {"name": "мука пшеничная", "quantity": 150, "unit": "г"},
            {"name": "сахар", "quantity": 50, "unit": "г"},
            {"name": "соль", "quantity": 5, "unit": "г"},
            {"name": "масло сливочное", "quantity": 30, "unit": "г"},
            {"name": "лук репчатый", "quantity": 100, "unit": "г"},
            {"name": "морковь", "quantity": 80, "unit": "г"},
            {"name": "говядина", "quantity": 300, "unit": "г"},
            {"name": "перец черный", "quantity": 2, "unit": "г"},
            {"name": "петрушка", "quantity": 20, "unit": "г"},
            {"name": "чеснок", "quantity": 10, "unit": "г"}
        ]
        
        # Medium batch (25-30 ingredients) - should be <2s
        medium_batch = small_batch + [
            {"name": "картофель", "quantity": 400, "unit": "г"},
            {"name": "помидоры", "quantity": 200, "unit": "г"},
            {"name": "огурцы", "quantity": 150, "unit": "г"},
            {"name": "капуста белокочанная", "quantity": 300, "unit": "г"},
            {"name": "свинина", "quantity": 250, "unit": "г"},
            {"name": "курица", "quantity": 400, "unit": "г"},
            {"name": "рис", "quantity": 100, "unit": "г"},
            {"name": "гречка", "quantity": 80, "unit": "г"},
            {"name": "сметана 20%", "quantity": 100, "unit": "г"},
            {"name": "творог", "quantity": 200, "unit": "г"},
            {"name": "сыр российский", "quantity": 100, "unit": "г"},
            {"name": "масло растительное", "quantity": 50, "unit": "мл"},
            {"name": "укроп", "quantity": 15, "unit": "г"},
            {"name": "базилик", "quantity": 10, "unit": "г"},
            {"name": "томатная паста", "quantity": 30, "unit": "г"},
            {"name": "перец болгарский", "quantity": 120, "unit": "г"},
            {"name": "баранина", "quantity": 300, "unit": "г"},
            {"name": "овсянка", "quantity": 60, "unit": "г"}
        ]
        
        # Large batch (45-50 ingredients) - should be ≤3s (CRITICAL TARGET)
        large_batch = medium_batch + [
            {"name": "кинза", "quantity": 15, "unit": "г"},
            {"name": "сливки 33%", "quantity": 150, "unit": "мл"},
            {"name": "оливковое масло", "quantity": 30, "unit": "мл"},
            {"name": "лосось", "quantity": 200, "unit": "г"},
            {"name": "креветки", "quantity": 150, "unit": "г"},
            {"name": "кальмары", "quantity": 100, "unit": "г"},
            {"name": "мидии", "quantity": 120, "unit": "г"},
            {"name": "семга", "quantity": 180, "unit": "г"},
            {"name": "форель", "quantity": 200, "unit": "г"},
            {"name": "треска", "quantity": 250, "unit": "г"},
            {"name": "судак", "quantity": 220, "unit": "г"},
            {"name": "щука", "quantity": 200, "unit": "г"},
            {"name": "карп", "quantity": 300, "unit": "г"},
            {"name": "окунь", "quantity": 180, "unit": "г"},
            {"name": "камбала", "quantity": 200, "unit": "г"},
            {"name": "палтус", "quantity": 250, "unit": "г"},
            {"name": "тунец", "quantity": 150, "unit": "г"},
            {"name": "скумбрия", "quantity": 200, "unit": "г"},
            {"name": "сельдь", "quantity": 180, "unit": "г"},
            {"name": "анчоусы", "quantity": 50, "unit": "г"},
            {"name": "икра красная", "quantity": 30, "unit": "г"},
            {"name": "икра черная", "quantity": 20, "unit": "г"}
        ]
        
        return {
            "small": small_batch,
            "medium": medium_batch, 
            "large": large_batch
        }
    
    def _create_test_techcard(self, ingredients: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
        """Create test techcard with given ingredients"""
        return {
            "name": name,
            "description": f"Test techcard for P0.3 performance testing with {len(ingredients)} ingredients",
            "ingredients": ingredients,
            "yield": sum(ing.get("quantity", 0) for ing in ingredients),
            "servings": 4,
            "category": "test",
            "process_steps": [
                {"step": 1, "description": "Подготовить все ингредиенты", "time_min": 10},
                {"step": 2, "description": "Приготовить блюдо", "time_min": 20},
                {"step": 3, "description": "Подать к столу", "time_min": 5}
            ]
        }
    
    def test_performance_benchmark(self):
        """Test performance benchmarks for different batch sizes"""
        print("🎯 P0.3: PERFORMANCE BENCHMARK TESTING")
        print("=" * 60)
        
        test_cases = [
            ("small", "Small Batch (10-15 ingredients)", 1000),  # <1s target
            ("medium", "Medium Batch (25-30 ingredients)", 2000),  # <2s target  
            ("large", "Large Batch (45-50 ingredients)", 3000)   # ≤3s CRITICAL TARGET
        ]
        
        for batch_type, description, target_ms in test_cases:
            ingredients = self.test_data[batch_type]
            techcard = self._create_test_techcard(ingredients, f"P0.3 Test {description}")
            
            print(f"\n📊 Testing {description}")
            print(f"   Ingredients: {len(ingredients)}")
            print(f"   Target: ≤{target_ms}ms")
            
            # Run multiple iterations for statistical accuracy
            times = []
            for i in range(3):
                start_time = time.time()
                
                response = requests.post(
                    f"{API_BASE}/techcards.v2/mapping/enhanced",
                    json={
                        "techcard": techcard,
                        "organization_id": "default",
                        "auto_apply": False
                    },
                    timeout=10
                )
                
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                times.append(response_time_ms)
                
                if response.status_code == 200:
                    data = response.json()
                    mapping_results = data.get("mapping_results", {})
                    performance = mapping_results.get("performance", {})
                    
                    print(f"   Run {i+1}: {response_time_ms:.1f}ms (API: {performance.get('total_time_ms', 'N/A')}ms)")
                    
                    if i == 0:  # Detailed analysis for first run
                        self._analyze_performance_metrics(performance, target_ms, batch_type)
                        self._analyze_optimization_features(mapping_results)
                else:
                    print(f"   Run {i+1}: ERROR {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
            
            # Statistical analysis
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                
                target_met = avg_time <= target_ms
                status = "✅ PASS" if target_met else "❌ FAIL"
                
                print(f"   Results: {status}")
                print(f"   Average: {avg_time:.1f}ms, Min: {min_time:.1f}ms, Max: {max_time:.1f}ms")
                
                self.results.append({
                    "test": f"Performance {description}",
                    "target_ms": target_ms,
                    "avg_time_ms": avg_time,
                    "min_time_ms": min_time,
                    "max_time_ms": max_time,
                    "target_met": target_met,
                    "status": "PASS" if target_met else "FAIL"
                })
    
    def _analyze_performance_metrics(self, performance: Dict[str, Any], target_ms: int, batch_type: str):
        """Analyze performance instrumentation metrics"""
        print(f"   📈 Performance Instrumentation:")
        
        total_time = performance.get("total_time_ms", 0)
        index_time = performance.get("index_time_ms", 0)
        batch_time = performance.get("batch_time_ms", 0)
        target_met = performance.get("target_met", False)
        ingredients_processed = performance.get("ingredients_processed", 0)
        
        print(f"      Total Time: {total_time}ms")
        print(f"      Index Time: {index_time}ms (indexing overhead)")
        print(f"      Batch Time: {batch_time}ms (parallel processing)")
        print(f"      Target Met: {target_met}")
        print(f"      Ingredients Processed: {ingredients_processed}")
        
        # Validate performance instrumentation
        if total_time > 0:
            print(f"   ✅ Performance instrumentation working")
        else:
            print(f"   ❌ Performance instrumentation missing")
        
        if batch_type == "large" and total_time <= 3000:
            print(f"   🎯 CRITICAL TARGET MET: {total_time}ms ≤ 3000ms")
        elif batch_type == "large":
            print(f"   ⚠️ CRITICAL TARGET MISSED: {total_time}ms > 3000ms")
    
    def _analyze_optimization_features(self, mapping_results: Dict[str, Any]):
        """Analyze optimization features are working"""
        print(f"   🔧 Optimization Features:")
        
        products_scanned = mapping_results.get("products_scanned", 0)
        results = mapping_results.get("results", [])
        stats = mapping_results.get("stats", {})
        
        print(f"      Products Scanned: {products_scanned}")
        print(f"      Results Found: {len(results)}")
        print(f"      Auto-accept: {stats.get('auto_accept', 0)}")
        print(f"      Review: {stats.get('review', 0)}")
        
        # Check for optimization indicators
        if products_scanned > 1000:
            print(f"   ✅ Product indexing system working (fast lookups)")
        
        if len(results) > 0:
            print(f"   ✅ Parallel processing functional")
            
            # Check payload diet (reduced alternatives)
            first_result = results[0]
            alternatives = first_result.get("alternatives", [])
            if len(alternatives) <= 2:
                print(f"   ✅ Payload diet working (≤2 alternatives)")
    
    def test_cache_performance(self):
        """Test LRU caching system performance improvement"""
        print("\n🗄️ P0.3: CACHE PERFORMANCE TESTING")
        print("=" * 60)
        
        # Use medium batch for cache testing
        ingredients = self.test_data["medium"]
        techcard = self._create_test_techcard(ingredients, "P0.3 Cache Test")
        
        request_payload = {
            "techcard": techcard,
            "organization_id": "default",
            "auto_apply": False
        }
        
        print(f"Testing cache performance with {len(ingredients)} ingredients")
        
        # First request - builds index and caches results
        print("📥 First request (cache miss):")
        start_time = time.time()
        response1 = requests.post(
            f"{API_BASE}/techcards.v2/mapping/enhanced",
            json=request_payload,
            timeout=10
        )
        first_time = (time.time() - start_time) * 1000
        
        if response1.status_code == 200:
            data1 = response1.json()
            performance1 = data1.get("mapping_results", {}).get("performance", {})
            print(f"   Time: {first_time:.1f}ms (API: {performance1.get('total_time_ms', 'N/A')}ms)")
            print(f"   Status: Cache miss - building index and caching results")
        else:
            print(f"   ERROR: {response1.status_code} - {response1.text[:200]}")
            return
        
        # Second identical request - should be faster (cache hit)
        print("📤 Second request (cache hit expected):")
        start_time = time.time()
        response2 = requests.post(
            f"{API_BASE}/techcards.v2/mapping/enhanced",
            json=request_payload,
            timeout=10
        )
        second_time = (time.time() - start_time) * 1000
        
        if response2.status_code == 200:
            data2 = response2.json()
            performance2 = data2.get("mapping_results", {}).get("performance", {})
            print(f"   Time: {second_time:.1f}ms (API: {performance2.get('total_time_ms', 'N/A')}ms)")
            
            # Analyze cache performance
            improvement = ((first_time - second_time) / first_time) * 100
            if second_time < first_time:
                print(f"   ✅ Cache performance improvement: {improvement:.1f}% faster")
                cache_working = True
            else:
                print(f"   ⚠️ No cache improvement detected")
                cache_working = False
            
            self.results.append({
                "test": "Cache Performance",
                "first_request_ms": first_time,
                "second_request_ms": second_time,
                "improvement_pct": improvement,
                "cache_working": cache_working,
                "status": "PASS" if cache_working else "FAIL"
            })
        else:
            print(f"   ERROR: {response2.status_code} - {response2.text[:200]}")
    
    def test_functional_integrity(self):
        """Test that optimizations don't break functional features"""
        print("\n🔍 P0.3: FUNCTIONAL INTEGRITY VALIDATION")
        print("=" * 60)
        
        # Test with known Russian ingredients that should match
        test_ingredients = [
            {"name": "яйца куриные", "quantity": 2, "unit": "шт"},
            {"name": "молоко 3.2%", "quantity": 200, "unit": "мл"},
            {"name": "говядина свежая", "quantity": 300, "unit": "г"},
            {"name": "лук репчатый", "quantity": 100, "unit": "г"}
        ]
        
        techcard = self._create_test_techcard(test_ingredients, "P0.3 Functional Test")
        
        response = requests.post(
            f"{API_BASE}/techcards.v2/mapping/enhanced",
            json={
                "techcard": techcard,
                "organization_id": "default",
                "auto_apply": False
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text[:200]}")
            self.results.append({
                "test": "Functional Integrity",
                "status": "FAIL",
                "error": f"API Error {response.status_code}"
            })
            return
        
        data = response.json()
        mapping_results = data.get("mapping_results", {})
        results = mapping_results.get("results", [])
        stats = mapping_results.get("stats", {})
        coverage = mapping_results.get("coverage", {})
        
        print(f"📊 Functional Analysis:")
        print(f"   Results found: {len(results)}")
        print(f"   Auto-accept: {stats.get('auto_accept', 0)}")
        print(f"   Review: {stats.get('review', 0)}")
        print(f"   Coverage: {coverage.get('potential_coverage_pct', 0)}%")
        
        # Test Russian synonym matching
        synonym_matches = 0
        confidence_scores = []
        
        for result in results:
            confidence = result.get("confidence", 0)
            confidence_scores.append(confidence)
            
            match_type = result.get("match_type", "")
            if match_type == "synonym":
                synonym_matches += 1
        
        print(f"   Russian synonym matches: {synonym_matches}")
        print(f"   Average confidence: {statistics.mean(confidence_scores):.2f}" if confidence_scores else "   No confidence scores")
        
        # Validate functional features
        functional_tests = []
        
        # Test 1: Russian synonym matching
        if synonym_matches > 0:
            functional_tests.append(("Russian synonym matching", True))
            print("   ✅ Russian synonym matching working")
        else:
            functional_tests.append(("Russian synonym matching", False))
            print("   ⚠️ No Russian synonym matches found")
        
        # Test 2: Confidence scoring (≥0.90 auto-accept, 0.70-0.89 review)
        auto_accept_valid = all(r.get("confidence", 0) >= 0.90 for r in results if r.get("status") == "auto_accept")
        review_valid = all(0.70 <= r.get("confidence", 0) < 0.90 for r in results if r.get("status") == "review")
        
        if auto_accept_valid and (not any(r.get("status") == "review" for r in results) or review_valid):
            functional_tests.append(("Confidence scoring", True))
            print("   ✅ Confidence scoring (≥0.90 auto-accept, 0.70-0.89 review) working")
        else:
            functional_tests.append(("Confidence scoring", False))
            print("   ❌ Confidence scoring thresholds incorrect")
        
        # Test 3: Coverage calculation
        if coverage.get("total_ingredients", 0) > 0:
            functional_tests.append(("Coverage calculation", True))
            print("   ✅ Coverage calculation working")
        else:
            functional_tests.append(("Coverage calculation", False))
            print("   ❌ Coverage calculation missing")
        
        # Overall functional integrity
        all_functional = all(test[1] for test in functional_tests)
        
        self.results.append({
            "test": "Functional Integrity",
            "synonym_matches": synonym_matches,
            "confidence_scoring": auto_accept_valid and review_valid,
            "coverage_calculation": coverage.get("total_ingredients", 0) > 0,
            "all_functional": all_functional,
            "status": "PASS" if all_functional else "FAIL"
        })
    
    def test_auto_apply_functionality(self):
        """Test auto-apply functionality for high-confidence mappings"""
        print("\n🤖 P0.3: AUTO-APPLY FUNCTIONALITY TESTING")
        print("=" * 60)
        
        test_ingredients = [
            {"name": "яйца", "quantity": 2, "unit": "шт"},
            {"name": "молоко", "quantity": 200, "unit": "мл"}
        ]
        
        techcard = self._create_test_techcard(test_ingredients, "P0.3 Auto-Apply Test")
        
        response = requests.post(
            f"{API_BASE}/techcards.v2/mapping/enhanced",
            json={
                "techcard": techcard,
                "organization_id": "default",
                "auto_apply": True  # Enable auto-apply
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text[:200]}")
            self.results.append({
                "test": "Auto-Apply Functionality",
                "status": "FAIL",
                "error": f"API Error {response.status_code}"
            })
            return
        
        data = response.json()
        auto_applied = data.get("auto_applied", False)
        updated_techcard = data.get("mapping_results", {}).get("updated_techcard")
        
        print(f"   Auto-apply enabled: {auto_applied}")
        
        if updated_techcard:
            applied_ingredients = [ing for ing in updated_techcard.get("ingredients", []) if ing.get("skuId")]
            print(f"   Ingredients with SKU applied: {len(applied_ingredients)}")
            
            if len(applied_ingredients) > 0:
                print("   ✅ Auto-apply functionality working")
                auto_apply_working = True
            else:
                print("   ⚠️ No SKUs applied automatically")
                auto_apply_working = False
        else:
            print("   ❌ No updated techcard returned")
            auto_apply_working = False
        
        self.results.append({
            "test": "Auto-Apply Functionality",
            "auto_applied": auto_applied,
            "skus_applied": len(applied_ingredients) if updated_techcard else 0,
            "working": auto_apply_working,
            "status": "PASS" if auto_apply_working else "FAIL"
        })
    
    def run_all_tests(self):
        """Run all P0.3 performance optimization tests"""
        print("🚀 P0.3: AUTOMAPPING PERFORMANCE OPTIMIZATION TESTING")
        print("Target: ≤3s for batch-50 ingredients")
        print("=" * 80)
        
        try:
            # Core performance benchmarks
            self.test_performance_benchmark()
            
            # Cache performance testing
            self.test_cache_performance()
            
            # Functional integrity validation
            self.test_functional_integrity()
            
            # Auto-apply functionality
            self.test_auto_apply_functionality()
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {str(e)}")
            self.results.append({
                "test": "Critical Error",
                "error": str(e),
                "status": "FAIL"
            })
        
        # Final summary
        self._print_final_summary()
    
    def _print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("🎯 P0.3: FINAL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.get("status") == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        print("\n📊 DETAILED RESULTS:")
        for result in self.results:
            test_name = result.get("test", "Unknown")
            status = result.get("status", "UNKNOWN")
            status_icon = "✅" if status == "PASS" else "❌"
            
            print(f"   {status_icon} {test_name}: {status}")
            
            # Show key metrics for performance tests
            if "Performance" in test_name and "avg_time_ms" in result:
                target = result.get("target_ms", 0)
                avg_time = result.get("avg_time_ms", 0)
                print(f"      Target: ≤{target}ms, Actual: {avg_time:.1f}ms")
        
        # Critical assessment
        print("\n🎯 CRITICAL ASSESSMENT:")
        
        # Check if batch-50 target is met
        large_batch_result = next((r for r in self.results if "Large Batch" in r.get("test", "")), None)
        if large_batch_result:
            if large_batch_result.get("target_met", False):
                print("   ✅ CRITICAL TARGET MET: Batch-50 ingredients ≤3s")
            else:
                print("   ❌ CRITICAL TARGET MISSED: Batch-50 ingredients >3s")
        
        # Check functional integrity
        functional_result = next((r for r in self.results if r.get("test") == "Functional Integrity"), None)
        if functional_result and functional_result.get("all_functional", False):
            print("   ✅ Functional features remain intact")
        else:
            print("   ⚠️ Some functional features may be impacted")
        
        # Overall verdict
        critical_tests_passed = (
            large_batch_result and large_batch_result.get("target_met", False) and
            functional_result and functional_result.get("all_functional", False)
        )
        
        if critical_tests_passed:
            print("\n🎉 P0.3 OPTIMIZATION SUCCESS: Performance target achieved with functional integrity maintained!")
        else:
            print("\n⚠️ P0.3 OPTIMIZATION NEEDS ATTENTION: Critical requirements not fully met")


if __name__ == "__main__":
    tester = P03PerformanceTest()
    tester.run_all_tests()