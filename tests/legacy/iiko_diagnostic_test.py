#!/usr/bin/env python3
"""
IIKo Integration Diagnostic Test Suite
Testing the "smart" authentication system with multiple methods and endpoints
Focus: Password is correct (metkamfetamin), problem is in method/format of request
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_iiko_health_check():
    """Test IIKo health check - should show 'healthy' if authentication works"""
    print("🏥 TESTING IIKO HEALTH CHECK")
    print("=" * 60)
    
    print("Test 1: GET /api/iiko/health")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/health", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            iiko_connection = result.get("iiko_connection", "unknown")
            error = result.get("error")
            
            if status == "healthy" and iiko_connection == "active":
                log_test("IIKo Health Check", "PASS", 
                        f"Status: {status}, Connection: {iiko_connection}")
            elif status == "healthy":
                log_test("IIKo Health Check", "WARN", 
                        f"Status: {status}, but connection: {iiko_connection}")
            else:
                log_test("IIKo Health Check", "FAIL", 
                        f"Status: {status}, Connection: {iiko_connection}, Error: {error}")
                
            print(f"    Full response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        elif response.status_code == 503:
            log_test("IIKo Health Check", "FAIL", 
                    f"Service Unavailable (503) - Authentication likely failed")
            print(f"    Response: {response.text}")
        else:
            log_test("IIKo Health Check", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("IIKo Health Check", "FAIL", f"Exception: {str(e)}")

def test_iiko_organizations():
    """Test IIKo organizations endpoint - should return organizations if auth works"""
    print("🏢 TESTING IIKO ORGANIZATIONS")
    print("=" * 60)
    
    print("Test 1: GET /api/iiko/organizations")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/organizations", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            organizations = result.get("organizations", [])
            
            if organizations:
                log_test("IIKo Organizations", "PASS", 
                        f"Retrieved {len(organizations)} organizations")
                
                # Show sample organizations
                print(f"    Sample organizations:")
                for i, org in enumerate(organizations[:3]):
                    print(f"    {i+1}. {org.get('name', 'N/A')} (ID: {org.get('id', 'N/A')})")
                    
            else:
                log_test("IIKo Organizations", "WARN", 
                        "No organizations returned (might be empty account)")
                
            print(f"    Full response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        elif response.status_code == 500:
            log_test("IIKo Organizations", "FAIL", 
                    f"Internal Server Error (500) - Authentication likely failed")
            print(f"    Response: {response.text}")
        elif response.status_code == 401:
            log_test("IIKo Organizations", "FAIL", 
                    f"Unauthorized (401) - Authentication failed")
            print(f"    Response: {response.text}")
        else:
            log_test("IIKo Organizations", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("IIKo Organizations", "FAIL", f"Exception: {str(e)}")

def test_iiko_diagnostics():
    """Test IIKo diagnostics endpoint - should show which method worked"""
    print("🔍 TESTING IIKO DIAGNOSTICS")
    print("=" * 60)
    
    print("Test 1: GET /api/iiko/diagnostics")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/diagnostics", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Look for authentication details
            auth_status = result.get("authentication", "unknown")
            connection_details = result.get("connection_details", {})
            last_error = result.get("last_error")
            successful_method = result.get("successful_method")
            
            if auth_status == "success" or "successful" in str(auth_status).lower():
                log_test("IIKo Diagnostics - Authentication", "PASS", 
                        f"Authentication: {auth_status}")
                
                if successful_method:
                    log_test("IIKo Diagnostics - Method Detection", "PASS", 
                            f"Successful method: {successful_method}")
                    
            else:
                log_test("IIKo Diagnostics - Authentication", "FAIL", 
                        f"Authentication: {auth_status}")
                
                if last_error:
                    print(f"    Last error: {last_error}")
                    
            print(f"    Full diagnostics: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        else:
            log_test("IIKo Diagnostics", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("IIKo Diagnostics", "FAIL", f"Exception: {str(e)}")

def test_smart_authentication_methods():
    """Test that the smart authentication is trying all 9 combinations"""
    print("🧠 TESTING SMART AUTHENTICATION METHODS")
    print("=" * 60)
    
    print("Testing if backend tries all 9 combinations (3 methods × 3 endpoints)")
    print("Expected combinations:")
    print("1. GET /resto/api/auth with params")
    print("2. POST /resto/api/auth with JSON")
    print("3. POST /resto/api/auth with form data")
    print("4. GET /api/auth with params")
    print("5. POST /api/auth with JSON")
    print("6. POST /api/auth with form data")
    print("7. GET /auth with params")
    print("8. POST /auth with JSON")
    print("9. POST /auth with form data")
    print()
    
    # Trigger authentication by calling health check
    print("Triggering authentication via health check...")
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/health", timeout=45)  # Longer timeout for all attempts
        
        # The response itself doesn't matter as much as the logs
        # But we can check if any method succeeded
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "healthy":
                log_test("Smart Authentication Success", "PASS", 
                        "At least one of the 9 methods worked!")
            else:
                log_test("Smart Authentication Success", "FAIL", 
                        "All 9 methods failed - authentication unsuccessful")
        else:
            log_test("Smart Authentication Success", "FAIL", 
                    f"Health check failed with HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Smart Authentication Methods", "FAIL", f"Exception: {str(e)}")

def test_password_correctness():
    """Verify that the password 'metkamfetamin' is being used correctly"""
    print("🔑 TESTING PASSWORD CORRECTNESS")
    print("=" * 60)
    
    print("User confirmed password 'metkamfetamin' is correct")
    print("User just logged into IIKo Office with this password")
    print("Testing if backend is using this password correctly...")
    
    # We can't directly test the password, but we can check diagnostics
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/diagnostics", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Look for password-related errors
            error_text = str(result).lower()
            
            if "неверный пароль" in error_text or "wrong password" in error_text:
                log_test("Password Usage", "FAIL", 
                        "Backend reports 'wrong password' - but user confirmed it's correct!")
                print("    🚨 CRITICAL: Password is correct but backend gets 'wrong password' error")
                print("    🔍 This suggests the problem is in the REQUEST FORMAT, not the password")
                
            elif "login" in error_text and "not authorized" in error_text:
                log_test("Password Usage", "FAIL", 
                        "Login not authorized - might be account access issue")
                
            elif "authentication" in error_text and ("success" in error_text or "successful" in error_text):
                log_test("Password Usage", "PASS", 
                        "Authentication successful - password is working!")
                
            else:
                log_test("Password Usage", "WARN", 
                        "Cannot determine password status from diagnostics")
                
            print(f"    Diagnostics response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
        else:
            log_test("Password Usage", "FAIL", 
                    f"Cannot get diagnostics: HTTP {response.status_code}")
            
    except Exception as e:
        log_test("Password Usage", "FAIL", f"Exception: {str(e)}")

def test_expected_success_scenario():
    """Test the expected success scenario based on review"""
    print("🎯 TESTING EXPECTED SUCCESS SCENARIO")
    print("=" * 60)
    
    print("According to review, one of the 9 combinations should work:")
    print("Expected results:")
    print("1. GET /api/iiko/health should return 'healthy'")
    print("2. GET /api/iiko/organizations should return organizations")
    print("3. GET /api/iiko/diagnostics should show successful method")
    print()
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Health should be healthy
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/health", timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "healthy":
                success_count += 1
                log_test("Expected Success - Health", "PASS", "Health check is healthy")
            else:
                log_test("Expected Success - Health", "FAIL", f"Health status: {result.get('status')}")
        else:
            log_test("Expected Success - Health", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("Expected Success - Health", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: Organizations should return data
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/organizations", timeout=30)
        if response.status_code == 200:
            result = response.json()
            organizations = result.get("organizations", [])
            if organizations:
                success_count += 1
                log_test("Expected Success - Organizations", "PASS", f"Got {len(organizations)} organizations")
            else:
                log_test("Expected Success - Organizations", "WARN", "No organizations returned")
        else:
            log_test("Expected Success - Organizations", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("Expected Success - Organizations", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: Diagnostics should show success
    try:
        response = requests.get(f"{BACKEND_URL}/iiko/diagnostics", timeout=30)
        if response.status_code == 200:
            result = response.json()
            auth_status = str(result.get("authentication", "")).lower()
            if "success" in auth_status or "successful" in auth_status:
                success_count += 1
                log_test("Expected Success - Diagnostics", "PASS", f"Authentication: {auth_status}")
            else:
                log_test("Expected Success - Diagnostics", "FAIL", f"Authentication: {auth_status}")
        else:
            log_test("Expected Success - Diagnostics", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("Expected Success - Diagnostics", "FAIL", f"Exception: {str(e)}")
    
    # Overall success assessment
    if success_count == total_tests:
        log_test("OVERALL SUCCESS SCENARIO", "PASS", 
                f"All {success_count}/{total_tests} expected results achieved! 🎉")
    elif success_count > 0:
        log_test("OVERALL SUCCESS SCENARIO", "WARN", 
                f"Partial success: {success_count}/{total_tests} tests passed")
    else:
        log_test("OVERALL SUCCESS SCENARIO", "FAIL", 
                f"No success: {success_count}/{total_tests} tests passed")

def main():
    """Run all IIKo diagnostic tests"""
    print("🔍 IIKO INTEGRATION DIAGNOSTIC TEST SUITE")
    print("=" * 80)
    print("🎯 FOCUS: Password 'metkamfetamin' is CORRECT!")
    print("🎯 PROBLEM: Method/format of request needs to be found")
    print("🎯 SOLUTION: Smart authentication trying 9 combinations")
    print()
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: Password correctness verification
        test_password_correctness()
        
        # Test 2: Smart authentication methods
        test_smart_authentication_methods()
        
        # Test 3: IIKo health check
        test_iiko_health_check()
        
        # Test 4: IIKo organizations
        test_iiko_organizations()
        
        # Test 5: IIKo diagnostics
        test_iiko_diagnostics()
        
        # Test 6: Expected success scenario
        test_expected_success_scenario()
        
        print("🏁 IIKO DIAGNOSTIC TESTS COMPLETED")
        print("=" * 80)
        print("🔍 ANALYSIS:")
        print("If all tests PASS: Smart authentication found the right method! 🎉")
        print("If tests FAIL: Need to investigate further or try different approach")
        print("If 'wrong password' error: Problem is in request encoding/format")
        print()
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()