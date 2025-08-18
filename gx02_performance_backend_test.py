#!/usr/bin/env python3
"""
GX-02 Enhanced Auto-mapping Performance and Mock Data Testing
Testing performance requirements and mock iiko RMS data creation
"""

import asyncio
import httpx
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class GX02PerformanceTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    async def run_all_tests(self):
        """Run all GX-02 performance and mock data tests"""
        print("🚀 GX-02 Performance and Mock Data Testing Started")
        print("=" * 60)
        
        # Test 1: Performance Test (<3 seconds requirement)
        await self.test_performance_requirements()
        
        # Test 2: Mock iiko RMS Data Creation
        await self.test_mock_rms_data_creation()
        
        # Test 3: Large Ingredient List Performance
        await self.test_large_ingredient_list()
        
        # Test 4: Concurrent Request Handling
        await self.test_concurrent_requests()
        
        # Summary
        self.print_summary()
        
    async def test_performance_requirements(self):
        """Test that enhanced mapping completes within 3 seconds"""
        print("\n⏱️ Test 1: Performance Requirements (<3 seconds)")
        print("-" * 40)
        
        # Create typical ingredient list (10-15 ingredients)
        typical_techcard = {
            "meta": {"title": "Performance Test Dish"},
            "ingredients": [
                {"name": "говядина", "brutto_g": 300, "unit": "г"},
                {"name": "лук репчатый", "brutto_g": 100, "unit": "г"},
                {"name": "морковь", "brutto_g": 80, "unit": "г"},
                {"name": "картофель", "brutto_g": 200, "unit": "г"},
                {"name": "масло растительное", "brutto_g": 30, "unit": "мл"},
                {"name": "соль", "brutto_g": 5, "unit": "г"},
                {"name": "перец черный", "brutto_g": 2, "unit": "г"},
                {"name": "лавровый лист", "brutto_g": 1, "unit": "г"},
                {"name": "томатная паста", "brutto_g": 20, "unit": "г"},
                {"name": "чеснок", "brutto_g": 10, "unit": "г"},
                {"name": "петрушка", "brutto_g": 15, "unit": "г"},
                {"name": "укроп", "brutto_g": 10, "unit": "г"}
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "techcard": typical_techcard,
                    "organization_id": "default"
                }
                
                # Measure performance
                start_time = time.time()
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                    json=payload
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                self.total_tests += 1
                test_id = "1.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success" and execution_time < 3.0:
                        mapping_results = data.get("mapping_results", {})
                        results = mapping_results.get("results", [])
                        
                        self.passed_tests += 1
                        print(f"✅ {test_id}: Performance requirements - PASSED")
                        print(f"   Execution time: {execution_time:.2f}s (< 3.0s required)")
                        print(f"   Ingredients processed: {len(typical_techcard['ingredients'])}")
                        print(f"   Matches found: {len(results)}")
                        print(f"   Products scanned: {mapping_results.get('products_scanned', 0)}")
                    else:
                        print(f"❌ {test_id}: Performance requirements - FAILED")
                        print(f"   Execution time: {execution_time:.2f}s (≥ 3.0s)")
                        print(f"   Status: {data.get('status')}")
                else:
                    print(f"❌ {test_id}: Performance test API error - {response.status_code}")
                    print(f"   Execution time: {execution_time:.2f}s")
                    
        except Exception as e:
            print(f"❌ {test_id}: Performance test exception - {str(e)}")
    
    async def test_mock_rms_data_creation(self):
        """Test mock iiko RMS data creation and format"""
        print("\n🏪 Test 2: Mock iiko RMS Data Creation")
        print("-" * 40)
        
        # Test with ingredients that should create mock RMS products
        test_techcard = {
            "meta": {"title": "Mock RMS Data Test"},
            "ingredients": [
                {"name": "яйцо куриное С1", "brutto_g": 50, "unit": "pcs"},
                {"name": "молоко 3.2%", "brutto_g": 200, "unit": "ml"},
                {"name": "говядина мраморная", "brutto_g": 300, "unit": "g"}
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "techcard": test_techcard,
                    "organization_id": "default"
                }
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                    json=payload
                )
                
                self.total_tests += 1
                test_id = "2.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        mapping_results = data.get("mapping_results", {})
                        results = mapping_results.get("results", [])
                        
                        # Check if results have expected mock RMS format
                        mock_data_valid = True
                        for result in results:
                            suggestion = result.get("suggestion", {})
                            
                            # Check required fields for mock iiko RMS data
                            required_fields = ["sku_id", "name", "article", "unit", "price_per_unit", "currency", "source"]
                            missing_fields = [field for field in required_fields if field not in suggestion]
                            
                            if missing_fields:
                                mock_data_valid = False
                                print(f"   Missing fields in {result['ingredient_name']}: {missing_fields}")
                            else:
                                # Verify field formats
                                if (suggestion["currency"] == "RUB" and
                                    suggestion["source"] == "rms_enhanced" and
                                    isinstance(suggestion["price_per_unit"], (int, float))):
                                    print(f"   ✓ {result['ingredient_name']}: {suggestion['name']} ({suggestion['price_per_unit']} {suggestion['currency']})")
                                else:
                                    mock_data_valid = False
                        
                        if mock_data_valid and len(results) > 0:
                            self.passed_tests += 1
                            print(f"✅ {test_id}: Mock RMS data creation - PASSED")
                            print(f"   Mock products created: {len(results)}")
                        else:
                            print(f"❌ {test_id}: Mock RMS data format invalid")
                    else:
                        print(f"❌ {test_id}: Mock RMS data test failed - {data.get('status')}")
                else:
                    print(f"❌ {test_id}: Mock RMS data API error - {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Mock RMS data exception - {str(e)}")
    
    async def test_large_ingredient_list(self):
        """Test performance with large ingredient list (20+ ingredients)"""
        print("\n📋 Test 3: Large Ingredient List Performance")
        print("-" * 40)
        
        # Create large ingredient list
        large_ingredient_list = []
        base_ingredients = [
            "говядина", "свинина", "курица", "рыба", "яйца", "молоко", "сметана", "творог",
            "лук", "морковь", "картофель", "капуста", "помидоры", "огурцы", "перец",
            "чеснок", "петрушка", "укроп", "базилик", "соль", "сахар", "мука", "рис",
            "масло растительное", "масло сливочное", "уксус", "лимон", "специи"
        ]
        
        for i, ingredient in enumerate(base_ingredients):
            large_ingredient_list.append({
                "name": ingredient,
                "brutto_g": 50 + (i * 10),
                "unit": "г"
            })
        
        large_techcard = {
            "meta": {"title": "Large Ingredient List Test"},
            "ingredients": large_ingredient_list
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "techcard": large_techcard,
                    "organization_id": "default"
                }
                
                start_time = time.time()
                
                response = await client.post(
                    f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                    json=payload
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                self.total_tests += 1
                test_id = "3.1"
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success" and execution_time < 5.0:  # Allow 5s for large lists
                        mapping_results = data.get("mapping_results", {})
                        results = mapping_results.get("results", [])
                        stats = mapping_results.get("stats", {})
                        
                        self.passed_tests += 1
                        print(f"✅ {test_id}: Large ingredient list performance - PASSED")
                        print(f"   Execution time: {execution_time:.2f}s (< 5.0s for large lists)")
                        print(f"   Ingredients processed: {len(large_ingredient_list)}")
                        print(f"   Matches found: {len(results)}")
                        print(f"   Auto-accept: {stats.get('auto_accept', 0)}")
                        print(f"   Review: {stats.get('review', 0)}")
                    else:
                        print(f"❌ {test_id}: Large ingredient list performance - FAILED")
                        print(f"   Execution time: {execution_time:.2f}s (≥ 5.0s)")
                        print(f"   Status: {data.get('status')}")
                else:
                    print(f"❌ {test_id}: Large ingredient list API error - {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Large ingredient list exception - {str(e)}")
    
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        print("\n🔄 Test 4: Concurrent Request Handling")
        print("-" * 40)
        
        # Create multiple test techcards
        test_techcards = []
        for i in range(3):  # Test 3 concurrent requests
            test_techcards.append({
                "meta": {"title": f"Concurrent Test {i+1}"},
                "ingredients": [
                    {"name": "говядина", "brutto_g": 200, "unit": "г"},
                    {"name": "лук", "brutto_g": 50, "unit": "г"},
                    {"name": "морковь", "brutto_g": 80, "unit": "г"}
                ]
            })
        
        async def make_request(client, techcard, request_id):
            """Make a single mapping request"""
            payload = {
                "techcard": techcard,
                "organization_id": "default"
            }
            
            start_time = time.time()
            response = await client.post(
                f"{API_BASE}/v1/techcards.v2/mapping/enhanced",
                json=payload
            )
            end_time = time.time()
            
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "execution_time": end_time - start_time,
                "success": response.status_code == 200 and response.json().get("status") == "success"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Make concurrent requests
                start_time = time.time()
                
                tasks = [
                    make_request(client, techcard, i+1) 
                    for i, techcard in enumerate(test_techcards)
                ]
                
                results = await asyncio.gather(*tasks)
                
                total_time = time.time() - start_time
                
                self.total_tests += 1
                test_id = "4.1"
                
                # Check if all requests succeeded
                successful_requests = [r for r in results if r["success"]]
                avg_execution_time = sum(r["execution_time"] for r in results) / len(results)
                
                if len(successful_requests) == len(test_techcards) and total_time < 10.0:
                    self.passed_tests += 1
                    print(f"✅ {test_id}: Concurrent request handling - PASSED")
                    print(f"   Total time: {total_time:.2f}s")
                    print(f"   Average execution time: {avg_execution_time:.2f}s")
                    print(f"   Successful requests: {len(successful_requests)}/{len(test_techcards)}")
                    
                    for result in results:
                        print(f"   Request {result['request_id']}: {result['execution_time']:.2f}s")
                else:
                    print(f"❌ {test_id}: Concurrent request handling - FAILED")
                    print(f"   Total time: {total_time:.2f}s")
                    print(f"   Successful requests: {len(successful_requests)}/{len(test_techcards)}")
                    
        except Exception as e:
            print(f"❌ {test_id}: Concurrent request exception - {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 GX-02 Performance and Mock Data Test Summary")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: GX-02 performance requirements met!")
        elif success_rate >= 75:
            print("✅ GOOD: Most performance requirements met")
        elif success_rate >= 50:
            print("⚠️ PARTIAL: Some performance issues detected")
        else:
            print("❌ CRITICAL: Performance requirements not met")
        
        print("\n🔍 Performance Validation Targets:")
        print("✓ Enhanced mapping completes <3 seconds for typical ingredient lists")
        print("✓ Mock iiko RMS data created in expected format")
        print("✓ Large ingredient lists (20+) handled efficiently")
        print("✓ Concurrent requests handled properly")
        
        return success_rate >= 75

async def main():
    """Main test execution"""
    tester = GX02PerformanceTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())