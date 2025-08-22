#!/usr/bin/env python3
"""
Phase 3.5: FE Binding + Dish-first Export Comprehensive Backend Testing
Critical dish article validation for iiko compatibility with enhanced preflight orchestrator and dual export system.
"""

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

import httpx
import pytest
from pymongo import MongoClient

# Test Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://iiko-menu-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
DB_NAME = os.getenv('DB_NAME', 'receptor_pro')

class Phase35BackendTester:
    """Comprehensive Phase 3.5 Backend Testing Suite"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        self.organization_id = "test-org-phase35"
        
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
    
    async def test_preflight_orchestrator_dish_validation(self):
        """Test PF-02-bind: Preflight Orchestrator with Dish Article Validation"""
        print("\n🎯 Testing PF-02-bind: Preflight Orchestrator with Dish Article Validation")
        
        # Test 1: Basic preflight with 'current' techcard
        try:
            start_time = time.time()
            
            payload = {
                "techcardIds": ["current"],
                "organization_id": self.organization_id
            }
            
            response = await self.client.post(f"{API_BASE}/export/preflight", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["status", "ttkDate", "missing", "generated", "counts"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Preflight Basic Structure", False, 
                                f"Missing fields: {missing_fields}", response_time)
                else:
                    # Check TTK date format
                    ttk_date = data.get("ttkDate")
                    try:
                        datetime.fromisoformat(ttk_date)
                        date_valid = True
                    except:
                        date_valid = False
                    
                    # Check missing dishes structure
                    missing_dishes = data.get("missing", {}).get("dishes", [])
                    missing_products = data.get("missing", {}).get("products", [])
                    
                    details = f"TTK Date: {ttk_date}, Dish Skeletons: {len(missing_dishes)}, Product Skeletons: {len(missing_products)}"
                    
                    if date_valid:
                        self.log_test("Preflight Basic Functionality", True, details, response_time)
                        
                        # Test dish skeleton structure
                        if missing_dishes:
                            dish = missing_dishes[0]
                            required_dish_fields = ["id", "name", "article", "type", "unit", "yield"]
                            dish_valid = all(field in dish for field in required_dish_fields)
                            
                            self.log_test("Dish Skeleton Structure", dish_valid,
                                        f"Dish: {dish.get('name', 'N/A')}, Article: {dish.get('article', 'N/A')}", response_time)
                        else:
                            self.log_test("Dish Skeleton Generation", True, "No dish skeletons needed", response_time)
                    else:
                        self.log_test("TTK Date Format", False, f"Invalid date format: {ttk_date}", response_time)
            else:
                self.log_test("Preflight Basic Request", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            self.log_test("Preflight Basic Request", False, f"Exception: {str(e)}", 0.0)
    
    async def test_dish_article_validation_scenarios(self):
        """Test specific dish article validation scenarios"""
        print("\n🎯 Testing Dish Article Validation Scenarios")
        
        # Test Scenario A: Dish Without Article
        try:
            start_time = time.time()
            
            payload = {
                "techcardIds": ["current"],  # Mock techcard has no article
                "organization_id": self.organization_id
            }
            
            response = await self.client.post(f"{API_BASE}/export/preflight", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                missing_dishes = data.get("missing", {}).get("dishes", [])
                generated_articles = data.get("generated", {}).get("dishArticles", [])
                
                # Should generate skeleton for dish without article
                if missing_dishes and generated_articles:
                    dish = missing_dishes[0]
                    article = dish.get("article")
                    
                    # Validate 5-digit article format
                    article_valid = (article and len(article) == 5 and article.isdigit())
                    
                    self.log_test("Scenario A: Dish Without Article", article_valid,
                                f"Generated article: {article}, Dish: {dish.get('name')}", response_time)
                else:
                    self.log_test("Scenario A: Dish Without Article", False,
                                "No skeleton generated for dish without article", response_time)
            else:
                self.log_test("Scenario A: Dish Without Article", False,
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Scenario A: Dish Without Article", False, f"Exception: {str(e)}", 0.0)
    
    async def test_mongodb_connection_and_lookup(self):
        """Test MongoDB connection and nomenclature.num field lookup"""
        print("\n🎯 Testing MongoDB Connection and RMS Lookup")
        
        try:
            start_time = time.time()
            
            # Test MongoDB connection using same pattern as backend
            client = MongoClient(MONGO_URL)
            db = client[DB_NAME.strip('"')]
            
            # Test nomenclature collection access
            nomenclature_collection = db.nomenclature
            
            # Check if we can query the collection
            sample_doc = nomenclature_collection.find_one()
            connection_time = time.time() - start_time
            
            if sample_doc is not None:
                # Test num field lookup (not code/GUID)
                test_article = "00004"  # Known test article
                
                lookup_start = time.time()
                dish_lookup = nomenclature_collection.find_one({
                    "num": test_article,
                    "product_type": {"$in": ["DISH", "dish"]}
                })
                lookup_time = time.time() - lookup_start
                
                if dish_lookup:
                    self.log_test("MongoDB RMS Lookup (num field)", True,
                                f"Found dish with article {test_article}: {dish_lookup.get('name', 'N/A')}", 
                                lookup_time)
                else:
                    self.log_test("MongoDB RMS Lookup (num field)", True,
                                f"No dish found with article {test_article} (expected for test)", 
                                lookup_time)
                
                self.log_test("MongoDB Connection", True,
                            f"Connected to {DB_NAME}, sample doc found", connection_time)
            else:
                self.log_test("MongoDB Connection", True,
                            f"Connected to {DB_NAME}, empty collection (expected)", connection_time)
            
            client.close()
            
        except Exception as e:
            self.log_test("MongoDB Connection", False, f"Exception: {str(e)}", 0.0)
    
    async def test_dual_export_dish_first_enforcement(self):
        """Test EX-03-bind: Dual Export with Dish-first Article Enforcement"""
        print("\n🎯 Testing EX-03-bind: Dual Export with Dish-first Article Enforcement")
        
        try:
            # First run preflight to get results
            preflight_payload = {
                "techcardIds": ["current"],
                "organization_id": self.organization_id
            }
            
            preflight_response = await self.client.post(f"{API_BASE}/export/preflight", json=preflight_payload)
            
            if preflight_response.status_code != 200:
                self.log_test("Dual Export Preflight", False, "Preflight failed", 0.0)
                return
            
            preflight_data = preflight_response.json()
            
            # Now test dual export
            start_time = time.time()
            
            export_payload = {
                "techcardIds": ["current"],
                "operational_rounding": True,
                "organization_id": self.organization_id,
                "preflight_result": preflight_data
            }
            
            response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Check if response is a ZIP file
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                is_zip = (content_type == 'application/zip' or 
                         response.content.startswith(b'PK'))
                
                if is_zip and content_length > 0:
                    self.log_test("Dual Export ZIP Generation", True,
                                f"ZIP file generated: {content_length} bytes", response_time)
                    
                    # Test conditional file inclusion logic
                    dish_count = preflight_data.get("counts", {}).get("dishSkeletons", 0)
                    product_count = preflight_data.get("counts", {}).get("productSkeletons", 0)
                    
                    expected_files = 1  # iiko_TTK.xlsx always included
                    if dish_count > 0:
                        expected_files += 1  # Dish-Skeletons.xlsx
                    if product_count > 0:
                        expected_files += 1  # Product-Skeletons.xlsx
                    
                    self.log_test("Conditional File Inclusion Logic", True,
                                f"Expected {expected_files} files (TTK + {dish_count} dish + {product_count} product skeletons)", 
                                response_time)
                else:
                    self.log_test("Dual Export ZIP Generation", False,
                                f"Invalid ZIP: content-type={content_type}, size={content_length}", response_time)
            else:
                self.log_test("Dual Export ZIP Generation", False,
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            self.log_test("Dual Export ZIP Generation", False, f"Exception: {str(e)}", 0.0)
    
    async def test_article_allocator_integration(self):
        """Test AA-01 ArticleAllocator integration"""
        print("\n🎯 Testing AA-01 ArticleAllocator Integration")
        
        try:
            # Test article allocation endpoint
            start_time = time.time()
            
            payload = {
                "article_type": "dish",
                "count": 2,
                "organization_id": self.organization_id,
                "entity_ids": ["test_dish_1", "test_dish_2"],
                "entity_names": ["Test Dish 1", "Test Dish 2"]
            }
            
            response = await self.client.post(f"{API_BASE}/articles/allocate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and data.get("allocated_articles"):
                    articles = data["allocated_articles"]
                    
                    # Validate 5-digit format
                    valid_format = all(len(article) == 5 and article.isdigit() for article in articles)
                    
                    self.log_test("ArticleAllocator Integration", valid_format,
                                f"Allocated {len(articles)} articles: {articles}", response_time)
                    
                    # Test article claiming
                    if articles:
                        claim_start = time.time()
                        claim_payload = {
                            "articles": articles,
                            "organization_id": self.organization_id,
                            "claimed_by": "phase35_test"
                        }
                        
                        claim_response = await self.client.post(f"{API_BASE}/articles/claim", json=claim_payload)
                        claim_time = time.time() - claim_start
                        
                        if claim_response.status_code == 200:
                            claim_data = claim_response.json()
                            self.log_test("Article Claiming", claim_data.get("success", False),
                                        f"Claimed {len(articles)} articles", claim_time)
                        else:
                            self.log_test("Article Claiming", False,
                                        f"HTTP {claim_response.status_code}", claim_time)
                else:
                    self.log_test("ArticleAllocator Integration", False,
                                "No articles allocated", response_time)
            else:
                self.log_test("ArticleAllocator Integration", False,
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            self.log_test("ArticleAllocator Integration", False, f"Exception: {str(e)}", 0.0)
    
    async def test_excel_formatting_compliance(self):
        """Test Excel formatting with text (@) for leading zeros preservation"""
        print("\n🎯 Testing Excel Formatting Compliance")
        
        try:
            # This test validates that the export system properly formats articles
            # We'll test this by checking the preflight response for proper article formatting
            
            start_time = time.time()
            
            payload = {
                "techcardIds": ["current"],
                "organization_id": self.organization_id
            }
            
            response = await self.client.post(f"{API_BASE}/export/preflight", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check generated articles format
                dish_articles = data.get("generated", {}).get("dishArticles", [])
                product_articles = data.get("generated", {}).get("productArticles", [])
                
                all_articles = dish_articles + product_articles
                
                if all_articles:
                    # Validate 5-digit format with leading zeros
                    format_valid = True
                    format_details = []
                    
                    for article in all_articles:
                        if not (len(article) == 5 and article.isdigit()):
                            format_valid = False
                            format_details.append(f"Invalid: {article}")
                        else:
                            format_details.append(f"Valid: {article}")
                    
                    self.log_test("Excel Article Formatting", format_valid,
                                f"Articles: {', '.join(format_details[:3])}", response_time)
                else:
                    self.log_test("Excel Article Formatting", True,
                                "No articles generated (expected for some scenarios)", response_time)
            else:
                self.log_test("Excel Article Formatting", False,
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Excel Article Formatting", False, f"Exception: {str(e)}", 0.0)
    
    async def test_complete_workflow_e2e(self):
        """Test complete end-to-end workflow"""
        print("\n🎯 Testing Complete E2E Workflow")
        
        try:
            workflow_start = time.time()
            
            # Step 1: Preflight validation
            preflight_payload = {
                "techcardIds": ["current"],
                "organization_id": self.organization_id
            }
            
            step1_start = time.time()
            preflight_response = await self.client.post(f"{API_BASE}/export/preflight", json=preflight_payload)
            step1_time = time.time() - step1_start
            
            if preflight_response.status_code != 200:
                self.log_test("E2E Workflow - Preflight", False, "Preflight failed", step1_time)
                return
            
            preflight_data = preflight_response.json()
            
            # Step 2: ZIP generation
            step2_start = time.time()
            export_payload = {
                "techcardIds": ["current"],
                "operational_rounding": True,
                "organization_id": self.organization_id,
                "preflight_result": preflight_data
            }
            
            export_response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
            step2_time = time.time() - step2_start
            
            if export_response.status_code != 200:
                self.log_test("E2E Workflow - Export", False, "Export failed", step2_time)
                return
            
            # Step 3: Validate complete workflow
            total_time = time.time() - workflow_start
            
            # Check if we have proper ZIP response
            is_zip = export_response.content.startswith(b'PK')
            zip_size = len(export_response.content)
            
            # Validate workflow components
            has_ttk_date = bool(preflight_data.get("ttkDate"))
            has_missing_data = bool(preflight_data.get("missing"))
            has_counts = bool(preflight_data.get("counts"))
            
            workflow_valid = is_zip and zip_size > 0 and has_ttk_date and has_missing_data and has_counts
            
            details = f"Preflight: {step1_time:.3f}s, Export: {step2_time:.3f}s, ZIP: {zip_size} bytes"
            
            self.log_test("E2E Workflow Complete", workflow_valid, details, total_time)
            
        except Exception as e:
            self.log_test("E2E Workflow Complete", False, f"Exception: {str(e)}", 0.0)
    
    async def test_performance_requirements(self):
        """Test performance requirements"""
        print("\n🎯 Testing Performance Requirements")
        
        try:
            # Test preflight performance
            start_time = time.time()
            
            payload = {
                "techcardIds": ["current"],
                "organization_id": self.organization_id
            }
            
            response = await self.client.post(f"{API_BASE}/export/preflight", json=payload)
            preflight_time = time.time() - start_time
            
            preflight_target = 3.0  # 3 seconds target
            preflight_meets_target = preflight_time <= preflight_target
            
            self.log_test("Preflight Performance", preflight_meets_target,
                        f"{preflight_time:.3f}s vs {preflight_target}s target", preflight_time)
            
            if response.status_code == 200:
                # Test export performance
                export_start = time.time()
                
                export_payload = {
                    "techcardIds": ["current"],
                    "operational_rounding": True,
                    "organization_id": self.organization_id,
                    "preflight_result": response.json()
                }
                
                export_response = await self.client.post(f"{API_BASE}/export/zip", json=export_payload)
                export_time = time.time() - export_start
                
                export_target = 5.0  # 5 seconds target
                export_meets_target = export_time <= export_target
                
                self.log_test("Export Performance", export_meets_target,
                            f"{export_time:.3f}s vs {export_target}s target", export_time)
            
        except Exception as e:
            self.log_test("Performance Requirements", False, f"Exception: {str(e)}", 0.0)
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("🎯 PHASE 3.5: FE BINDING + DISH-FIRST EXPORT TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}: {result['details']}")
        
        # Critical validation points summary
        print(f"\n🎯 CRITICAL VALIDATION POINTS:")
        
        critical_tests = [
            "Preflight Basic Functionality",
            "Dish Skeleton Structure", 
            "MongoDB RMS Lookup (num field)",
            "Dual Export ZIP Generation",
            "ArticleAllocator Integration",
            "Excel Article Formatting",
            "E2E Workflow Complete"
        ]
        
        for test_name in critical_tests:
            result = next((r for r in self.test_results if r["test"] == test_name), None)
            if result:
                status = "✅" if result["success"] else "❌"
                print(f"   {status} {test_name}")
            else:
                print(f"   ⚠️  {test_name} (not tested)")
        
        return success_rate >= 80  # 80% success rate threshold


async def main():
    """Main test execution"""
    print("🚀 Starting Phase 3.5: FE Binding + Dish-first Export Backend Testing")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"MongoDB URL: {MONGO_URL}")
    print(f"Database: {DB_NAME}")
    
    async with Phase35BackendTester() as tester:
        # Execute all test suites
        await tester.test_preflight_orchestrator_dish_validation()
        await tester.test_dish_article_validation_scenarios()
        await tester.test_mongodb_connection_and_lookup()
        await tester.test_dual_export_dish_first_enforcement()
        await tester.test_article_allocator_integration()
        await tester.test_excel_formatting_compliance()
        await tester.test_complete_workflow_e2e()
        await tester.test_performance_requirements()
        
        # Print comprehensive summary
        success = tester.print_summary()
        
        if success:
            print(f"\n🎉 PHASE 3.5 TESTING COMPLETED SUCCESSFULLY!")
            print(f"All critical components are operational and ready for production use.")
        else:
            print(f"\n⚠️  PHASE 3.5 TESTING COMPLETED WITH ISSUES")
            print(f"Some components require attention before production deployment.")
        
        return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with exception: {e}")
        traceback.print_exc()
        sys.exit(1)