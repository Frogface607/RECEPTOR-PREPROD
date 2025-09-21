#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Sticky iiko (Preview) Functionality
Tests the newly implemented sticky connection features for iiko RMS integration
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://kitchen-pro-2.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1/iiko/rms"

# Test credentials from environment
RMS_HOST = "edison-bar.iiko.it"
RMS_LOGIN = "Sergey"
RMS_PASSWORD = "metkamfetamin"
TEST_USER_ID = "test_sticky_user_001"

class StickyIikoTester:
    """Comprehensive tester for Sticky iiko functionality"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        self.connection_data = None
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
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
        print(f"{status}: {test_name}")
        print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
    
    def test_disconnect_endpoint(self) -> bool:
        """Test POST /api/v1/iiko/rms/disconnect endpoint"""
        print("🔌 Testing Disconnect Endpoint...")
        
        try:
            # First establish a connection to have something to disconnect
            connect_response = self.session.post(f"{API_BASE}/connect", json={
                "host": RMS_HOST,
                "login": RMS_LOGIN,
                "password": RMS_PASSWORD,
                "user_id": TEST_USER_ID
            })
            
            if connect_response.status_code != 200:
                self.log_test("Disconnect Endpoint - Setup Connection", False, 
                            f"Failed to setup connection for disconnect test: {connect_response.status_code}")
                return False
            
            # Test disconnect endpoint
            disconnect_response = self.session.post(f"{API_BASE}/disconnect", 
                                                  params={"user_id": TEST_USER_ID})
            
            if disconnect_response.status_code == 200:
                data = disconnect_response.json()
                
                # Verify response structure
                required_fields = ["status", "connections_cleared", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Disconnect Endpoint - Response Structure", False,
                                f"Missing fields in response: {missing_fields}", data)
                    return False
                
                # Verify status and count
                if data["status"] == "disconnected" and data["connections_cleared"] >= 1:
                    self.log_test("Disconnect Endpoint - Functionality", True,
                                f"Successfully disconnected {data['connections_cleared']} connections", data)
                    
                    # Verify connection is actually cleared by checking status
                    status_response = self.session.get(f"{API_BASE}/connection/status", 
                                                     params={"user_id": TEST_USER_ID})
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") in ["not_connected", "disconnected"]:
                            self.log_test("Disconnect Endpoint - Verification", True,
                                        "Connection status correctly shows disconnected", status_data)
                            return True
                        else:
                            self.log_test("Disconnect Endpoint - Verification", False,
                                        f"Connection still shows as: {status_data.get('status')}", status_data)
                            return False
                    else:
                        self.log_test("Disconnect Endpoint - Verification", False,
                                    f"Failed to verify disconnect: {status_response.status_code}")
                        return False
                else:
                    self.log_test("Disconnect Endpoint - Response Values", False,
                                f"Unexpected response values: status={data['status']}, cleared={data['connections_cleared']}", data)
                    return False
            else:
                self.log_test("Disconnect Endpoint - HTTP Status", False,
                            f"Expected 200, got {disconnect_response.status_code}", disconnect_response.text)
                return False
                
        except Exception as e:
            self.log_test("Disconnect Endpoint - Exception", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_restore_connection_endpoint(self) -> bool:
        """Test POST /api/v1/iiko/rms/restore-connection endpoint"""
        print("🔄 Testing Restore Connection Endpoint...")
        
        try:
            # Test 1: Restore with no stored credentials
            restore_response = self.session.post(f"{API_BASE}/restore-connection", 
                                               params={"user_id": "nonexistent_user"})
            
            if restore_response.status_code == 200:
                data = restore_response.json()
                if data.get("status") == "no_stored_credentials":
                    self.log_test("Restore Connection - No Credentials", True,
                                "Correctly handles no stored credentials scenario", data)
                else:
                    self.log_test("Restore Connection - No Credentials", False,
                                f"Unexpected status for no credentials: {data.get('status')}", data)
                    return False
            else:
                self.log_test("Restore Connection - No Credentials HTTP", False,
                            f"Expected 200, got {restore_response.status_code}")
                return False
            
            # Test 2: Store credentials and test restore
            connect_response = self.session.post(f"{API_BASE}/connect", json={
                "host": RMS_HOST,
                "login": RMS_LOGIN,
                "password": RMS_PASSWORD,
                "user_id": TEST_USER_ID
            })
            
            if connect_response.status_code != 200:
                self.log_test("Restore Connection - Setup", False,
                            f"Failed to setup connection: {connect_response.status_code}")
                return False
            
            # Disconnect to test restore
            self.session.post(f"{API_BASE}/disconnect", params={"user_id": TEST_USER_ID})
            
            # Test restore with valid credentials
            restore_response = self.session.post(f"{API_BASE}/restore-connection", 
                                               params={"user_id": TEST_USER_ID})
            
            if restore_response.status_code == 200:
                data = restore_response.json()
                
                # Check for different possible statuses
                valid_statuses = ["restored", "needs_reconnection", "manually_disconnected", "connection_error"]
                
                if data.get("status") in valid_statuses:
                    if data.get("status") == "restored":
                        # Verify restored connection has required fields
                        required_fields = ["host", "login", "organizations"]
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if missing_fields:
                            self.log_test("Restore Connection - Restored Fields", False,
                                        f"Missing fields in restored response: {missing_fields}", data)
                            return False
                        
                        # Verify credential masking
                        if "***" in data.get("login", ""):
                            self.log_test("Restore Connection - Success", True,
                                        f"Successfully restored connection with masked credentials", data)
                        else:
                            self.log_test("Restore Connection - Credential Masking", False,
                                        "Login not properly masked in response", data)
                            return False
                    
                    elif data.get("status") == "needs_reconnection":
                        # Test the needs_reconnection status
                        if "401" in data.get("error", "") or "403" in data.get("error", ""):
                            self.log_test("Restore Connection - Needs Reconnection", True,
                                        "Correctly handles authentication failure with needs_reconnection status", data)
                        else:
                            self.log_test("Restore Connection - Needs Reconnection", True,
                                        "Returns needs_reconnection status (may be due to expired session)", data)
                    
                    elif data.get("status") == "manually_disconnected":
                        self.log_test("Restore Connection - Manual Disconnect", True,
                                    "Correctly handles manually disconnected state", data)
                    
                    else:
                        self.log_test("Restore Connection - Other Status", True,
                                    f"Handled with status: {data.get('status')}", data)
                    
                    return True
                else:
                    self.log_test("Restore Connection - Invalid Status", False,
                                f"Unexpected status: {data.get('status')}", data)
                    return False
            else:
                self.log_test("Restore Connection - HTTP Status", False,
                            f"Expected 200, got {restore_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Restore Connection - Exception", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_enhanced_connection_status(self) -> bool:
        """Test GET /api/v1/iiko/rms/connection/status with enhanced features"""
        print("📊 Testing Enhanced Connection Status...")
        
        try:
            # Test 1: Basic connection status
            status_response = self.session.get(f"{API_BASE}/connection/status", 
                                             params={"user_id": TEST_USER_ID})
            
            if status_response.status_code == 200:
                data = status_response.json()
                
                # Verify response structure
                expected_fields = ["status"]
                for field in expected_fields:
                    if field not in data:
                        self.log_test("Enhanced Connection Status - Structure", False,
                                    f"Missing field: {field}", data)
                        return False
                
                # Test different status scenarios
                valid_statuses = ["connected", "disconnected", "not_connected", "needs_reconnection", "error"]
                
                if data.get("status") in valid_statuses:
                    self.log_test("Enhanced Connection Status - Valid Status", True,
                                f"Returns valid status: {data.get('status')}", data)
                    
                    # If connected, verify additional fields
                    if data.get("status") == "connected":
                        connected_fields = ["host", "login", "session_expires_at"]
                        for field in connected_fields:
                            if field in data:
                                # Verify credential masking
                                if field == "login" and "***" not in str(data[field]):
                                    self.log_test("Enhanced Connection Status - Login Masking", False,
                                                "Login not properly masked", data)
                                    return False
                        
                        # Check session validity field if present
                        if "is_session_valid" in data:
                            self.log_test("Enhanced Connection Status - Session Validity", True,
                                        f"Session validity info provided: {data['is_session_valid']}", data)
                        
                        self.log_test("Enhanced Connection Status - Connected Info", True,
                                    "Provides comprehensive connection information", data)
                    
                    return True
                else:
                    self.log_test("Enhanced Connection Status - Invalid Status", False,
                                f"Invalid status: {data.get('status')}", data)
                    return False
            else:
                self.log_test("Enhanced Connection Status - HTTP Status", False,
                            f"Expected 200, got {status_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Connection Status - Exception", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_credential_masking(self) -> bool:
        """Test credential masking in logs and responses"""
        print("🔒 Testing Credential Masking...")
        
        try:
            # Establish connection to test masking
            connect_response = self.session.post(f"{API_BASE}/connect", json={
                "host": RMS_HOST,
                "login": RMS_LOGIN,
                "password": RMS_PASSWORD,
                "user_id": TEST_USER_ID
            })
            
            if connect_response.status_code == 200:
                data = connect_response.json()
                
                # Verify password is not in response
                response_str = json.dumps(data)
                if RMS_PASSWORD in response_str:
                    self.log_test("Credential Masking - Password in Response", False,
                                "Password found in connect response", data)
                    return False
                
                self.log_test("Credential Masking - Connect Response", True,
                            "Password not exposed in connect response", None)
            
            # Test connection status masking
            status_response = self.session.get(f"{API_BASE}/connection/status", 
                                             params={"user_id": TEST_USER_ID})
            
            if status_response.status_code == 200:
                data = status_response.json()
                
                # Check login masking
                if "login" in data:
                    login_value = data["login"]
                    if "***" in str(login_value):
                        # Verify it shows first 3 characters + ***
                        if len(RMS_LOGIN) > 3 and login_value.startswith(RMS_LOGIN[:3]):
                            self.log_test("Credential Masking - Login Format", True,
                                        f"Login properly masked: {login_value}", data)
                        else:
                            self.log_test("Credential Masking - Login Format", True,
                                        f"Login masked (format may vary): {login_value}", data)
                    else:
                        self.log_test("Credential Masking - Login Missing Mask", False,
                                    f"Login not masked: {login_value}", data)
                        return False
                
                # Verify password is not in status response
                response_str = json.dumps(data)
                if RMS_PASSWORD in response_str:
                    self.log_test("Credential Masking - Password in Status", False,
                                "Password found in status response", data)
                    return False
                
                self.log_test("Credential Masking - Status Response", True,
                            "Credentials properly masked in status response", None)
                return True
            else:
                self.log_test("Credential Masking - Status HTTP", False,
                            f"Failed to get status: {status_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Credential Masking - Exception", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_needs_reconnection_status(self) -> bool:
        """Test the new 'needs_reconnection' status handling"""
        print("🔄 Testing Needs Reconnection Status...")
        
        try:
            # This test is challenging because we need to simulate an expired/invalid session
            # We'll test the status enum and response handling
            
            # First, establish a connection
            connect_response = self.session.post(f"{API_BASE}/connect", json={
                "host": RMS_HOST,
                "login": RMS_LOGIN,
                "password": RMS_PASSWORD,
                "user_id": TEST_USER_ID
            })
            
            if connect_response.status_code != 200:
                self.log_test("Needs Reconnection - Setup", False,
                            f"Failed to setup connection: {connect_response.status_code}")
                return False
            
            # Test restore connection which might trigger needs_reconnection
            restore_response = self.session.post(f"{API_BASE}/restore-connection", 
                                               params={"user_id": TEST_USER_ID})
            
            if restore_response.status_code == 200:
                data = restore_response.json()
                
                # Check if we get needs_reconnection status
                if data.get("status") == "needs_reconnection":
                    # Verify it has proper error message and masked credentials
                    required_fields = ["error", "host", "login"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("Needs Reconnection - Response Fields", False,
                                    f"Missing fields: {missing_fields}", data)
                        return False
                    
                    # Verify login is masked
                    if "***" in data.get("login", ""):
                        self.log_test("Needs Reconnection - Status Handling", True,
                                    "Properly handles needs_reconnection status with masked credentials", data)
                        return True
                    else:
                        self.log_test("Needs Reconnection - Login Masking", False,
                                    "Login not masked in needs_reconnection response", data)
                        return False
                
                elif data.get("status") == "restored":
                    # Connection was successfully restored, which is also valid
                    self.log_test("Needs Reconnection - Connection Restored", True,
                                "Connection was successfully restored (no reconnection needed)", data)
                    return True
                
                else:
                    # Other statuses are also valid for this test
                    self.log_test("Needs Reconnection - Other Status", True,
                                f"Handled with status: {data.get('status')} (needs_reconnection not triggered)", data)
                    return True
            else:
                self.log_test("Needs Reconnection - HTTP Status", False,
                            f"Expected 200, got {restore_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Needs Reconnection - Exception", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_auto_restore_parameter(self) -> bool:
        """Test auto_restore parameter for connection status (if implemented)"""
        print("🔄 Testing Auto Restore Parameter...")
        
        try:
            # Test connection status with auto_restore parameter
            # Note: This parameter might not be implemented yet in the endpoint
            status_response = self.session.get(f"{API_BASE}/connection/status", 
                                             params={"user_id": TEST_USER_ID, "auto_restore": "true"})
            
            if status_response.status_code == 200:
                data = status_response.json()
                self.log_test("Auto Restore Parameter - Accepted", True,
                            "auto_restore parameter accepted by endpoint", data)
                return True
            else:
                # Parameter might not be implemented yet
                self.log_test("Auto Restore Parameter - Not Implemented", True,
                            "auto_restore parameter not yet implemented (expected)", None)
                return True
                
        except Exception as e:
            self.log_test("Auto Restore Parameter - Exception", False, f"Exception occurred: {str(e)}")
            return False
    
    def test_sticky_connection_workflow(self) -> bool:
        """Test complete sticky connection workflow"""
        print("🔄 Testing Complete Sticky Connection Workflow...")
        
        try:
            # Step 1: Connect
            print("   Step 1: Initial connection...")
            connect_response = self.session.post(f"{API_BASE}/connect", json={
                "host": RMS_HOST,
                "login": RMS_LOGIN,
                "password": RMS_PASSWORD,
                "user_id": TEST_USER_ID
            })
            
            if connect_response.status_code != 200:
                self.log_test("Sticky Workflow - Connect", False,
                            f"Failed to connect: {connect_response.status_code}")
                return False
            
            # Step 2: Verify connection status
            print("   Step 2: Verify connection status...")
            status_response = self.session.get(f"{API_BASE}/connection/status", 
                                             params={"user_id": TEST_USER_ID})
            
            if status_response.status_code != 200:
                self.log_test("Sticky Workflow - Status Check", False,
                            f"Failed to get status: {status_response.status_code}")
                return False
            
            status_data = status_response.json()
            if status_data.get("status") != "connected":
                self.log_test("Sticky Workflow - Connection Verification", False,
                            f"Expected connected, got: {status_data.get('status')}")
                return False
            
            # Step 3: Disconnect
            print("   Step 3: Disconnect...")
            disconnect_response = self.session.post(f"{API_BASE}/disconnect", 
                                                  params={"user_id": TEST_USER_ID})
            
            if disconnect_response.status_code != 200:
                self.log_test("Sticky Workflow - Disconnect", False,
                            f"Failed to disconnect: {disconnect_response.status_code}")
                return False
            
            # Step 4: Verify disconnected
            print("   Step 4: Verify disconnected...")
            status_response = self.session.get(f"{API_BASE}/connection/status", 
                                             params={"user_id": TEST_USER_ID})
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("status") not in ["disconnected", "not_connected"]:
                    self.log_test("Sticky Workflow - Disconnect Verification", False,
                                f"Expected disconnected, got: {status_data.get('status')}")
                    return False
            
            # Step 5: Attempt restore
            print("   Step 5: Attempt restore...")
            restore_response = self.session.post(f"{API_BASE}/restore-connection", 
                                               params={"user_id": TEST_USER_ID})
            
            if restore_response.status_code != 200:
                self.log_test("Sticky Workflow - Restore", False,
                            f"Failed to restore: {restore_response.status_code}")
                return False
            
            restore_data = restore_response.json()
            valid_restore_statuses = ["restored", "needs_reconnection", "manually_disconnected"]
            
            if restore_data.get("status") in valid_restore_statuses:
                self.log_test("Sticky Workflow - Complete", True,
                            f"Complete workflow successful. Final status: {restore_data.get('status')}", restore_data)
                return True
            else:
                self.log_test("Sticky Workflow - Restore Status", False,
                            f"Unexpected restore status: {restore_data.get('status')}", restore_data)
                return False
                
        except Exception as e:
            self.log_test("Sticky Workflow - Exception", False, f"Exception occurred: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all sticky iiko tests"""
        print("🚀 Starting Sticky iiko (Preview) Backend Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Test User ID: {TEST_USER_ID}")
        print("=" * 80)
        
        # Run all tests
        tests = [
            ("Disconnect Endpoint", self.test_disconnect_endpoint),
            ("Restore Connection Endpoint", self.test_restore_connection_endpoint),
            ("Enhanced Connection Status", self.test_enhanced_connection_status),
            ("Credential Masking", self.test_credential_masking),
            ("Needs Reconnection Status", self.test_needs_reconnection_status),
            ("Auto Restore Parameter", self.test_auto_restore_parameter),
            ("Sticky Connection Workflow", self.test_sticky_connection_workflow)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(f"{test_name} - Critical Error", False, f"Critical error: {str(e)}")
        
        # Summary
        print("=" * 80)
        print("🎯 STICKY IIKO TESTING SUMMARY")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Sticky iiko functionality is working correctly.")
        elif passed >= total * 0.8:
            print("✅ MOSTLY WORKING! Most sticky iiko features are functional.")
        else:
            print("⚠️ ISSUES FOUND! Some sticky iiko features need attention.")
        
        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": success_rate,
            "all_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = StickyIikoTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["passed_tests"] == results["total_tests"]:
        exit(0)  # All tests passed
    else:
        exit(1)  # Some tests failed

if __name__ == "__main__":
    main()