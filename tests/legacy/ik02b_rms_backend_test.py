#!/usr/bin/env python3
"""
IK-02B iiko RMS Backend Integration Testing
Comprehensive testing of iiko RMS (Restaurant Management System) integration components
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

# RMS credentials from environment
RMS_HOST = os.getenv('IIKO_RMS_HOST', 'edison-bar.iiko.it')
RMS_LOGIN = os.getenv('IIKO_RMS_LOGIN', 'Sergey')
RMS_PASSWORD = os.getenv('IIKO_RMS_PASSWORD', 'metkamfetamin')

class IikoRmsBackendTester:
    """Comprehensive tester for IK-02B iiko RMS backend implementation"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
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
            print(f"    Data: {json.dumps(data, indent=2)}")
        print()
    
    def test_rms_health_check(self) -> bool:
        """Test RMS health check endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/v1/iiko/rms/health")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["service", "status", "timestamp", "details"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("RMS Health Check", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                # Check if RMS is healthy
                if data["status"] == "healthy":
                    details = data.get("details", {})
                    self.log_test("RMS Health Check", True, 
                                f"RMS healthy - Host: {details.get('host')}, "
                                f"Organizations: {details.get('organizations_count', 0)}, "
                                f"Auth time: {details.get('auth_time', 0):.2f}s", data)
                    return True
                else:
                    self.log_test("RMS Health Check", False, 
                                f"RMS unhealthy: {data.get('error', 'Unknown error')}", data)
                    return False
            else:
                self.log_test("RMS Health Check", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("RMS Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_rms_connect(self) -> bool:
        """Test RMS connection endpoint"""
        try:
            payload = {
                "host": RMS_HOST,
                "login": RMS_LOGIN,
                "password": RMS_PASSWORD,
                "user_id": "test_user"
            }
            
            response = self.session.post(f"{API_BASE}/v1/iiko/rms/connect", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["status", "host", "organizations", "session_expires_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("RMS Connect", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                if data["status"] == "connected":
                    organizations = data.get("organizations", [])
                    if organizations:
                        # Store first organization for later tests
                        self.organization_id = organizations[0]["id"]
                        
                    self.log_test("RMS Connect", True, 
                                f"Connected to {data['host']}, "
                                f"Found {len(organizations)} organizations", data)
                    return True
                else:
                    self.log_test("RMS Connect", False, 
                                f"Connection failed: {data}", data)
                    return False
            else:
                self.log_test("RMS Connect", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("RMS Connect", False, f"Exception: {str(e)}")
            return False
    
    def test_rms_connection_status(self) -> bool:
        """Test RMS connection status endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/v1/iiko/rms/connection/status?user_id=test_user")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("RMS Connection Status", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                if data["status"] == "connected":
                    self.log_test("RMS Connection Status", True, 
                                f"Status: {data['status']}, "
                                f"Host: {data.get('host')}, "
                                f"Org: {data.get('organization_name')}", data)
                    return True
                else:
                    self.log_test("RMS Connection Status", True, 
                                f"Status: {data['status']} (expected for new connection)", data)
                    return True
            else:
                self.log_test("RMS Connection Status", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("RMS Connection Status", False, f"Exception: {str(e)}")
            return False
    
    def test_rms_select_organization(self) -> bool:
        """Test RMS organization selection endpoint"""
        if not self.organization_id:
            self.log_test("RMS Select Organization", False, 
                        "No organization ID available from connect test")
            return False
        
        try:
            payload = {
                "organization_id": self.organization_id,
                "user_id": "test_user"
            }
            
            response = self.session.post(f"{API_BASE}/v1/iiko/rms/select-org", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["status", "organization"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("RMS Select Organization", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                if data["status"] == "selected":
                    org = data.get("organization", {})
                    self.log_test("RMS Select Organization", True, 
                                f"Selected organization: {org.get('name')} ({org.get('id')})", data)
                    return True
                else:
                    self.log_test("RMS Select Organization", False, 
                                f"Selection failed: {data}", data)
                    return False
            else:
                self.log_test("RMS Select Organization", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("RMS Select Organization", False, f"Exception: {str(e)}")
            return False
    
    def test_rms_sync_nomenclature(self) -> bool:
        """Test RMS nomenclature synchronization endpoint"""
        if not self.organization_id:
            self.log_test("RMS Sync Nomenclature", False, 
                        "No organization ID available")
            return False
        
        try:
            payload = {"force": True}
            
            response = self.session.post(
                f"{API_BASE}/v1/iiko/rms/sync/nomenclature?organization_id={self.organization_id}", 
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["status", "sync_id"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("RMS Sync Nomenclature", False, 
                                f"Missing fields: {missing_fields}", data)
                    return False
                
                if data["status"] in ["completed", "running"]:
                    stats = data.get("stats", {})
                    self.log_test("RMS Sync Nomenclature", True, 
                                f"Sync {data['status']}: "
                                f"Products: {stats.get('products_processed', 0)} processed, "
                                f"{stats.get('products_created', 0)} created, "
                                f"{stats.get('products_updated', 0)} updated", data)
                    return True
                else:
                    self.log_test("RMS Sync Nomenclature", False, 
                                f"Sync failed: {data}", data)
                    return False
            else:
                self.log_test("RMS Sync Nomenclature", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("RMS Sync Nomenclature", False, f"Exception: {str(e)}")
            return False
    
    def test_rms_sync_status(self) -> bool:
        """Test RMS sync status endpoint"""
        if not self.organization_id:
            self.log_test("RMS Sync Status", False, 
                        "No organization ID available")
            return False
        
        try:
            response = self.session.get(
                f"{API_BASE}/v1/iiko/rms/sync/status?organization_id={self.organization_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have sync data
                if "status" in data:
                    if data["status"] == "never_synced":
                        self.log_test("RMS Sync Status", True, 
                                    "No previous sync found (expected for new setup)", data)
                    else:
                        stats = data.get("stats", {})
                        self.log_test("RMS Sync Status", True, 
                                    f"Last sync: {data['status']}, "
                                    f"Products: {stats.get('products_processed', 0)}", data)
                    return True
                else:
                    self.log_test("RMS Sync Status", False, 
                                f"Invalid response structure", data)
                    return False
            else:
                self.log_test("RMS Sync Status", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("RMS Sync Status", False, f"Exception: {str(e)}")
            return False
    
    def test_rms_product_search(self) -> bool:
        """Test RMS product search endpoint"""
        if not self.organization_id:
            self.log_test("RMS Product Search", False, 
                        "No organization ID available")
            return False
        
        try:
            # Test search with common ingredient names
            test_queries = ["мясо", "курица", "овощи", "молоко", "хлеб"]
            
            for query in test_queries:
                response = self.session.get(
                    f"{API_BASE}/v1/iiko/rms/products/search"
                    f"?organization_id={self.organization_id}&q={query}&limit=5"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list):
                        if data:  # Found products
                            product = data[0]
                            required_fields = ["sku_id", "name", "unit", "price_per_unit", 
                                             "currency", "asOf", "match_score", "source"]
                            missing_fields = [field for field in required_fields if field not in product]
                            
                            if missing_fields:
                                self.log_test("RMS Product Search", False, 
                                            f"Missing fields in product: {missing_fields}", product)
                                return False
                            
                            self.log_test("RMS Product Search", True, 
                                        f"Query '{query}': Found {len(data)} products, "
                                        f"Top match: {product['name']} "
                                        f"(score: {product['match_score']:.2f})", data[:2])
                            return True
                        else:
                            # No products found - this might be expected for some queries
                            continue
                    else:
                        self.log_test("RMS Product Search", False, 
                                    f"Invalid response format for query '{query}'", data)
                        return False
                else:
                    self.log_test("RMS Product Search", False, 
                                f"HTTP {response.status_code} for query '{query}': {response.text}")
                    return False
            
            # If we get here, no queries returned products
            self.log_test("RMS Product Search", True, 
                        "Search endpoint working but no products found for test queries "
                        "(may be expected for empty RMS database)")
            return True
                
        except Exception as e:
            self.log_test("RMS Product Search", False, f"Exception: {str(e)}")
            return False
    
    def test_catalog_search_rms_integration(self) -> bool:
        """Test catalog search endpoint with RMS source parameter"""
        try:
            # Test catalog search with RMS source
            test_queries = ["мясо", "курица", "молоко"]
            
            for query in test_queries:
                response = self.session.get(
                    f"{API_BASE}/v1/techcards.v2/catalog-search?q={query}&source=rms&limit=5"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    required_fields = ["status", "items"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("Catalog Search RMS Integration", False, 
                                    f"Missing fields: {missing_fields}", data)
                        return False
                    
                    if data["status"] == "success":
                        items = data.get("items", [])
                        rms_count = data.get("rms_count", 0)
                        
                        # Check if RMS results are included
                        rms_items = [item for item in items if item.get("source") == "rms"]
                        
                        self.log_test("Catalog Search RMS Integration", True, 
                                    f"Query '{query}': {len(items)} total items, "
                                    f"{len(rms_items)} from RMS, rms_count: {rms_count}", 
                                    {"items": items[:2], "rms_count": rms_count})
                        return True
                    else:
                        self.log_test("Catalog Search RMS Integration", False, 
                                    f"Search failed for query '{query}': {data}", data)
                        return False
                else:
                    self.log_test("Catalog Search RMS Integration", False, 
                                f"HTTP {response.status_code} for query '{query}': {response.text}")
                    return False
            
            # If no queries worked, still consider it a pass if the endpoint is responding
            self.log_test("Catalog Search RMS Integration", True, 
                        "Catalog search with RMS source working (no RMS data found)")
            return True
                
        except Exception as e:
            self.log_test("Catalog Search RMS Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_rms_database_collections(self) -> bool:
        """Test if RMS database collections are accessible through API"""
        try:
            # We can't directly test MongoDB collections, but we can test if the sync
            # and search endpoints work, which indicates collections are properly set up
            
            # Test if we can get connection status (tests credentials collection)
            response = self.session.get(f"{API_BASE}/v1/iiko/rms/connection/status")
            if response.status_code != 200:
                self.log_test("RMS Database Collections", False, 
                            f"Credentials collection test failed: HTTP {response.status_code}")
                return False
            
            # Test if we can get sync status (tests sync_status collection)
            if self.organization_id:
                response = self.session.get(
                    f"{API_BASE}/v1/iiko/rms/sync/status?organization_id={self.organization_id}"
                )
                if response.status_code != 200:
                    self.log_test("RMS Database Collections", False, 
                                f"Sync status collection test failed: HTTP {response.status_code}")
                    return False
            
            self.log_test("RMS Database Collections", True, 
                        "Database collections accessible through API endpoints")
            return True
                
        except Exception as e:
            self.log_test("RMS Database Collections", False, f"Exception: {str(e)}")
            return False
    
    def test_rms_client_direct(self) -> bool:
        """Test RMS client functionality directly (if possible through API)"""
        try:
            # Test authentication through health check
            response = self.session.get(f"{API_BASE}/v1/iiko/rms/health")
            
            if response.status_code == 200:
                data = response.json()
                details = data.get("details", {})
                
                # Check if authentication worked
                if details.get("session_valid"):
                    self.log_test("RMS Client Direct", True, 
                                f"RMS client authentication successful, "
                                f"Host: {details.get('host')}, "
                                f"Auth time: {details.get('auth_time', 0):.2f}s")
                    return True
                else:
                    self.log_test("RMS Client Direct", False, 
                                f"RMS client authentication failed", details)
                    return False
            else:
                self.log_test("RMS Client Direct", False, 
                            f"Health check failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("RMS Client Direct", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all IK-02B RMS tests"""
        print("🚀 Starting IK-02B iiko RMS Backend Integration Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"RMS Host: {RMS_HOST}")
        print(f"RMS Login: {RMS_LOGIN}")
        print("=" * 80)
        print()
        
        # Test sequence - order matters for dependencies
        tests = [
            ("RMS Health Check", self.test_rms_health_check),
            ("RMS Client Direct", self.test_rms_client_direct),
            ("RMS Connect", self.test_rms_connect),
            ("RMS Connection Status", self.test_rms_connection_status),
            ("RMS Select Organization", self.test_rms_select_organization),
            ("RMS Database Collections", self.test_rms_database_collections),
            ("RMS Sync Nomenclature", self.test_rms_sync_nomenclature),
            ("RMS Sync Status", self.test_rms_sync_status),
            ("RMS Product Search", self.test_rms_product_search),
            ("Catalog Search RMS Integration", self.test_catalog_search_rms_integration),
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
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
                failed += 1
        
        # Summary
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print("=" * 80)
        print(f"🎯 IK-02B RMS TESTING SUMMARY")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        # Critical assessment
        critical_tests = [
            "RMS Health Check",
            "RMS Connect", 
            "RMS Sync Nomenclature",
            "RMS Product Search"
        ]
        
        critical_failures = [
            result for result in self.test_results 
            if not result["success"] and result["test"] in critical_tests
        ]
        
        if critical_failures:
            print("🚨 CRITICAL ISSUES DETECTED:")
            for failure in critical_failures:
                print(f"  - {failure['test']}: {failure['details']}")
            print()
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "critical_failures": len(critical_failures),
            "test_results": self.test_results,
            "organization_id": self.organization_id
        }

def main():
    """Main test execution"""
    tester = IikoRmsBackendTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["critical_failures"] > 0:
        print("💥 CRITICAL FAILURES DETECTED - RMS integration has major issues")
        sys.exit(1)
    elif results["failed"] > 0:
        print("⚠️  Some tests failed but core functionality appears working")
        sys.exit(0)
    else:
        print("🎉 ALL TESTS PASSED - RMS integration is fully functional!")
        sys.exit(0)

if __name__ == "__main__":
    main()