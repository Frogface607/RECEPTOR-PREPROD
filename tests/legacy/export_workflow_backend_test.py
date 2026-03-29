#!/usr/bin/env python3
"""
IK-02B-FE/03 One-Click Export Workflow Backend Integration Testing
Comprehensive testing of the complete 4-step export wizard backend endpoints
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

# Test configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ExportWorkflowTester:
    """Comprehensive tester for IK-02B-FE/03 one-click export workflow"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.test_techcard = None
        self.organization_id = None
        
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
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
            print(f"    Data: {json.dumps(data, indent=2)[:500]}...")
        print()
    
    def test_tech_card_generation(self) -> bool:
        """Test POST /api/v1/techcards.v2/generate - Step 1 of export workflow"""
        try:
            # Test with a sample dish like "Говядина тушеная с овощами"
            payload = {
                "name": "Говядина тушеная с овощами",
                "cuisine": "русская",
                "equipment": [],
                "budget": None,
                "dietary": []
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", 
                                       json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["status", "card", "issues"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Tech Card Generation API", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check if generation was successful or draft
                if data.get("status") in ["success", "draft"]:
                    card = data.get("card")
                    if card:
                        # Verify TechCardV2 structure
                        required_card_fields = ["meta", "ingredients", "process", "cost", "nutrition"]
                        missing_card_fields = [field for field in required_card_fields if field not in card]
                        
                        if missing_card_fields:
                            self.log_test("Tech Card Generation API", False, 
                                        f"Missing card fields: {missing_card_fields}", card)
                            return False
                        
                        # Store for later tests
                        self.test_techcard = card
                        
                        # Check ingredients structure
                        ingredients = card.get("ingredients", [])
                        if len(ingredients) > 0:
                            ingredient = ingredients[0]
                            required_ingredient_fields = ["name", "brutto_g", "unit"]
                            missing_ingredient_fields = [field for field in required_ingredient_fields 
                                                       if field not in ingredient]
                            
                            if missing_ingredient_fields:
                                self.log_test("Tech Card Generation API", False, 
                                            f"Missing ingredient fields: {missing_ingredient_fields}", ingredient)
                                return False
                        
                        self.log_test("Tech Card Generation API", True, 
                                    f"Generated {data['status']} tech card with {len(ingredients)} ingredients", 
                                    {"status": data["status"], "ingredients_count": len(ingredients)})
                        return True
                    else:
                        self.log_test("Tech Card Generation API", False, 
                                    f"No card generated, status: {data.get('status')}", data)
                        return False
                else:
                    self.log_test("Tech Card Generation API", False, 
                                f"Generation failed: {data.get('status')}", data)
                    return False
            else:
                self.log_test("Tech Card Generation API", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Tech Card Generation API", False, f"Exception: {str(e)}")
            return False
    
    def test_iiko_rms_connection_status(self) -> bool:
        """Test GET /api/v1/iiko/rms/connection/status - Step 2 pre-check"""
        try:
            response = self.session.get(f"{API_BASE}/v1/iiko/rms/connection/status", 
                                      timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("iiko RMS Connection Status", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                status = data.get("status")
                if status == "connected":
                    # Store organization info for later tests
                    self.organization_id = data.get("organization_id")
                    org_name = data.get("organization_name", "Unknown")
                    host = data.get("host", "Unknown")
                    
                    self.log_test("iiko RMS Connection Status", True, 
                                f"RMS connected to {host}, organization: {org_name}", 
                                {"host": host, "organization": org_name, "organization_id": self.organization_id})
                    return True
                elif status in ["not_connected", "disconnected"]:
                    self.log_test("iiko RMS Connection Status", True, 
                                f"RMS not connected (status: {status}) - this is expected if not configured", 
                                {"status": status})
                    return True  # Not connected is a valid state for testing
                else:
                    self.log_test("iiko RMS Connection Status", False, 
                                f"Unknown connection status: {status}", data)
                    return False
            else:
                self.log_test("iiko RMS Connection Status", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("iiko RMS Connection Status", False, f"Exception: {str(e)}")
            return False
    
    def test_auto_mapping_integration(self) -> bool:
        """Test auto-mapping system - Step 3 of export workflow"""
        try:
            # First test nomenclature sync if we have organization
            if self.organization_id:
                # Test sync endpoint
                payload = {"force": False}
                response = self.session.post(
                    f"{API_BASE}/v1/iiko/rms/sync/nomenclature?organization_id={self.organization_id}", 
                    json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") in ["completed", "already_running", "running"]:
                        stats = data.get("stats", {})
                        products_processed = stats.get("products_processed", 0)
                        
                        self.log_test("Auto-mapping Integration (Sync)", True, 
                                    f"Nomenclature sync {data['status']}, {products_processed} products", 
                                    {"sync_status": data["status"], "stats": stats})
                        
                        # Test auto-mapping search functionality
                        return self.test_auto_mapping_search()
                    else:
                        self.log_test("Auto-mapping Integration (Sync)", False, 
                                    f"Sync failed: {data.get('status')}", data)
                        return False
                else:
                    self.log_test("Auto-mapping Integration (Sync)", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    return False
            else:
                # No organization, test search functionality only
                return self.test_auto_mapping_search()
                
        except Exception as e:
            self.log_test("Auto-mapping Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_auto_mapping_search(self) -> bool:
        """Test auto-mapping search functionality"""
        try:
            # Test catalog search with RMS source
            test_queries = ["мясо", "говядина", "курица"]
            
            for query in test_queries:
                response = self.session.get(
                    f"{API_BASE}/v1/techcards.v2/catalog-search?q={query}&source=rms&limit=5", 
                    timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        items = data.get("items", [])
                        rms_count = data.get("rms_count", 0)
                        
                        if rms_count > 0:
                            # Verify RMS item structure
                            rms_items = [item for item in items if item.get("source") == "rms"]
                            if rms_items:
                                item = rms_items[0]
                                required_fields = ["name", "sku_id", "unit", "source", "match_score"]
                                missing_fields = [field for field in required_fields if field not in item]
                                
                                if missing_fields:
                                    self.log_test("Auto-mapping Search", False, 
                                                f"Missing fields in RMS item: {missing_fields}", item)
                                    return False
                                
                                self.log_test("Auto-mapping Search", True, 
                                            f"Query '{query}': {rms_count} RMS items found, sample: {item['name']}", 
                                            {"query": query, "rms_count": rms_count, "sample_item": item})
                                return True
                        else:
                            # No RMS items for this query, try next
                            continue
                    else:
                        self.log_test("Auto-mapping Search", False, 
                                    f"Search failed for query '{query}': {data.get('status')}", data)
                        return False
                else:
                    self.log_test("Auto-mapping Search", False, 
                                f"HTTP {response.status_code} for query '{query}': {response.text}")
                    return False
            
            # If no RMS results found, test general catalog search
            response = self.session.get(
                f"{API_BASE}/v1/techcards.v2/catalog-search?q=мясо&source=all&limit=5", 
                timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    items = data.get("items", [])
                    self.log_test("Auto-mapping Search", True, 
                                f"Catalog search working, {len(items)} items found (no RMS results for test queries)", 
                                {"total_items": len(items)})
                    return True
            
            self.log_test("Auto-mapping Search", False, "No search results found for any queries")
            return False
                
        except Exception as e:
            self.log_test("Auto-mapping Search", False, f"Exception: {str(e)}")
            return False
    
    def test_gost_export_endpoint(self) -> bool:
        """Test POST /api/v1/techcards.v2/export/gost - Step 4 GOST preview"""
        if not self.test_techcard:
            self.log_test("GOST Export Endpoint", False, "No tech card available from generation test")
            return False
        
        try:
            # Test GOST export (print endpoint)
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/print", 
                                       json=self.test_techcard, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'text/html' in content_type:
                    html_content = response.text
                    
                    # Verify HTML contains expected GOST elements
                    gost_indicators = [
                        "ТЕХНОЛОГИЧЕСКАЯ КАРТА",
                        "Говядина тушеная с овощами",
                        "СОСТАВ И РАСХОД СЫРЬЯ",
                        "ТЕХНОЛОГИЧЕСКИЙ ПРОЦЕСС"
                    ]
                    
                    missing_indicators = [indicator for indicator in gost_indicators 
                                        if indicator not in html_content]
                    
                    if missing_indicators:
                        self.log_test("GOST Export Endpoint", False, 
                                    f"Missing GOST elements: {missing_indicators}")
                        return False
                    
                    self.log_test("GOST Export Endpoint", True, 
                                f"GOST HTML generated successfully, size: {len(html_content)} chars", 
                                {"content_type": content_type, "size": len(html_content)})
                    return True
                else:
                    self.log_test("GOST Export Endpoint", False, 
                                f"Unexpected content type: {content_type}")
                    return False
            else:
                self.log_test("GOST Export Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GOST Export Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_iiko_xlsx_export_endpoint(self) -> bool:
        """Test POST /api/v1/techcards.v2/export/iiko.xlsx - Step 5 final export"""
        if not self.test_techcard:
            self.log_test("iiko XLSX Export Endpoint", False, "No tech card available from generation test")
            return False
        
        try:
            # Test iiko XLSX export
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/export/iiko.xlsx", 
                                       json=self.test_techcard, timeout=30)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                # Verify it's an Excel file
                if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                    file_size = len(response.content)
                    
                    # Verify reasonable file size (should be > 1KB for a valid Excel file)
                    if file_size > 1000:
                        # Verify filename in content disposition
                        if 'filename=' in content_disposition and '.xlsx' in content_disposition:
                            self.log_test("iiko XLSX Export Endpoint", True, 
                                        f"iiko XLSX file generated successfully, size: {file_size} bytes", 
                                        {"content_type": content_type, "file_size": file_size, 
                                         "content_disposition": content_disposition})
                            return True
                        else:
                            self.log_test("iiko XLSX Export Endpoint", False, 
                                        f"Invalid content disposition: {content_disposition}")
                            return False
                    else:
                        self.log_test("iiko XLSX Export Endpoint", False, 
                                    f"File too small: {file_size} bytes")
                        return False
                else:
                    self.log_test("iiko XLSX Export Endpoint", False, 
                                f"Unexpected content type: {content_type}")
                    return False
            else:
                self.log_test("iiko XLSX Export Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("iiko XLSX Export Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_techcard_recalculation(self) -> bool:
        """Test POST /api/v1/techcards.v2/recalc - Step 6 recalculation after SKU updates"""
        if not self.test_techcard:
            self.log_test("TechCard Recalculation", False, "No tech card available from generation test")
            return False
        
        try:
            # Test recalculation endpoint
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/recalc", 
                                       json=self.test_techcard, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["status", "card", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("TechCard Recalculation", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                if data.get("status") == "success":
                    recalc_card = data.get("card")
                    if recalc_card:
                        # Verify recalculated card has cost and nutrition
                        cost = recalc_card.get("cost")
                        nutrition = recalc_card.get("nutrition")
                        
                        cost_valid = cost and isinstance(cost, dict) and "rawCost" in cost
                        nutrition_valid = nutrition and isinstance(nutrition, dict) and "per100g" in nutrition
                        
                        if cost_valid and nutrition_valid:
                            raw_cost = cost.get("rawCost", 0)
                            kcal_per_100g = nutrition.get("per100g", {}).get("kcal", 0)
                            
                            self.log_test("TechCard Recalculation", True, 
                                        f"Recalculation successful, cost: {raw_cost} RUB, nutrition: {kcal_per_100g} kcal/100g", 
                                        {"raw_cost": raw_cost, "kcal_per_100g": kcal_per_100g})
                            return True
                        else:
                            self.log_test("TechCard Recalculation", False, 
                                        f"Invalid cost or nutrition data, cost_valid: {cost_valid}, nutrition_valid: {nutrition_valid}")
                            return False
                    else:
                        self.log_test("TechCard Recalculation", False, 
                                    "No recalculated card returned")
                        return False
                else:
                    self.log_test("TechCard Recalculation", False, 
                                f"Recalculation failed: {data.get('status')}", data)
                    return False
            else:
                self.log_test("TechCard Recalculation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("TechCard Recalculation", False, f"Exception: {str(e)}")
            return False
    
    def test_complete_workflow_integration(self) -> bool:
        """Test complete workflow integration - all steps working together"""
        try:
            # Count successful tests for each workflow step
            workflow_tests = [
                "Tech Card Generation API",
                "iiko RMS Connection Status", 
                "Auto-mapping Integration (Sync)",
                "Auto-mapping Search",
                "GOST Export Endpoint",
                "iiko XLSX Export Endpoint",
                "TechCard Recalculation"
            ]
            
            successful_tests = []
            failed_tests = []
            
            for test_name in workflow_tests:
                test_results = [result for result in self.test_results if result["test"] == test_name]
                if test_results and test_results[-1]["success"]:  # Get latest result
                    successful_tests.append(test_name)
                else:
                    failed_tests.append(test_name)
            
            # Core workflow steps that must work
            core_steps = [
                "Tech Card Generation API",
                "iiko RMS Connection Status",
                "GOST Export Endpoint", 
                "iiko XLSX Export Endpoint",
                "TechCard Recalculation"
            ]
            
            core_successful = [test for test in core_steps if test in successful_tests]
            
            if len(core_successful) >= 4:  # At least 4 out of 5 core steps
                self.log_test("Complete Workflow Integration", True, 
                            f"Core workflow functional: {len(core_successful)}/5 core steps working", 
                            {"successful_tests": successful_tests, "failed_tests": failed_tests})
                return True
            else:
                self.log_test("Complete Workflow Integration", False, 
                            f"Core workflow incomplete: only {len(core_successful)}/5 core steps working", 
                            {"successful_tests": successful_tests, "failed_tests": failed_tests})
                return False
                
        except Exception as e:
            self.log_test("Complete Workflow Integration", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all export workflow tests"""
        print("🧪 Starting IK-02B-FE/03 One-Click Export Workflow Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Test sequence - order matters for dependencies
        tests = [
            ("Tech Card Generation API", self.test_tech_card_generation),
            ("iiko RMS Connection Status", self.test_iiko_rms_connection_status),
            ("Auto-mapping Integration", self.test_auto_mapping_integration),
            ("GOST Export Endpoint", self.test_gost_export_endpoint),
            ("iiko XLSX Export Endpoint", self.test_iiko_xlsx_export_endpoint),
            ("TechCard Recalculation", self.test_techcard_recalculation),
            ("Complete Workflow Integration", self.test_complete_workflow_integration),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                if success:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
                failed += 1
        
        # Summary
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print("=" * 70)
        print(f"🎯 EXPORT WORKFLOW TEST SUMMARY")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Critical tests that must pass for export workflow
        critical_tests = [
            "Tech Card Generation API",
            "iiko XLSX Export Endpoint",
            "TechCard Recalculation"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result["test"] in critical_tests and result["success"])
        
        if critical_passed == len(critical_tests):
            print("✅ All critical export workflow tests passed - One-click export ready")
        else:
            print("❌ Some critical export workflow tests failed - Export may not work properly")
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "critical_tests_passed": critical_passed,
            "critical_tests_total": len(critical_tests),
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = ExportWorkflowTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["critical_tests_passed"] == results["critical_tests_total"]:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()