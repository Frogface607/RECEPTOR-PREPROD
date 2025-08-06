#!/usr/bin/env python3
"""
IIKo Authentication Method Testing
Testing different parameter names and encoding methods for the password 'metkamfetamin'
"""

import requests
import json
import urllib.parse
import base64
from datetime import datetime

# IIKo server details from logs
IIKO_BASE_URL = "https://edison-bar.iiko.it"
LOGIN = "Sergey"
PASSWORD = "metkamfetamin"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_direct_iiko_auth():
    """Test direct authentication with IIKo Office API"""
    print("🔐 TESTING DIRECT IIKO OFFICE AUTHENTICATION")
    print("=" * 60)
    print(f"Server: {IIKO_BASE_URL}")
    print(f"Login: {LOGIN}")
    print(f"Password: {'*' * len(PASSWORD)}")
    print()
    
    # Test 1: GET with 'pass' parameter (current method)
    print("Test 1: GET /resto/api/auth with 'pass' parameter")
    try:
        params = {
            "login": LOGIN,
            "pass": PASSWORD
        }
        
        response = requests.get(f"{IIKO_BASE_URL}/resto/api/auth", params=params, timeout=10)
        
        if response.status_code == 200:
            log_test("GET with 'pass' parameter", "PASS", f"Session key: {response.text[:50]}...")
        elif response.status_code == 401:
            log_test("GET with 'pass' parameter", "FAIL", f"401: {response.text}")
        else:
            log_test("GET with 'pass' parameter", "FAIL", f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("GET with 'pass' parameter", "FAIL", f"Exception: {str(e)}")
    
    # Test 2: GET with 'password' parameter
    print("Test 2: GET /resto/api/auth with 'password' parameter")
    try:
        params = {
            "login": LOGIN,
            "password": PASSWORD
        }
        
        response = requests.get(f"{IIKO_BASE_URL}/resto/api/auth", params=params, timeout=10)
        
        if response.status_code == 200:
            log_test("GET with 'password' parameter", "PASS", f"Session key: {response.text[:50]}...")
        elif response.status_code == 401:
            log_test("GET with 'password' parameter", "FAIL", f"401: {response.text}")
        else:
            log_test("GET with 'password' parameter", "FAIL", f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("GET with 'password' parameter", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: POST with form data using 'pass'
    print("Test 3: POST /resto/api/auth with form data ('pass')")
    try:
        data = {
            "login": LOGIN,
            "pass": PASSWORD
        }
        
        response = requests.post(f"{IIKO_BASE_URL}/resto/api/auth", data=data, timeout=10)
        
        if response.status_code == 200:
            log_test("POST form data with 'pass'", "PASS", f"Session key: {response.text[:50]}...")
        elif response.status_code == 401:
            log_test("POST form data with 'pass'", "FAIL", f"401: {response.text}")
        else:
            log_test("POST form data with 'pass'", "FAIL", f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("POST form data with 'pass'", "FAIL", f"Exception: {str(e)}")
    
    # Test 4: POST with form data using 'password'
    print("Test 4: POST /resto/api/auth with form data ('password')")
    try:
        data = {
            "login": LOGIN,
            "password": PASSWORD
        }
        
        response = requests.post(f"{IIKO_BASE_URL}/resto/api/auth", data=data, timeout=10)
        
        if response.status_code == 200:
            log_test("POST form data with 'password'", "PASS", f"Session key: {response.text[:50]}...")
        elif response.status_code == 401:
            log_test("POST form data with 'password'", "FAIL", f"401: {response.text}")
        else:
            log_test("POST form data with 'password'", "FAIL", f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("POST form data with 'password'", "FAIL", f"Exception: {str(e)}")
    
    # Test 5: POST with JSON
    print("Test 5: POST /resto/api/auth with JSON")
    try:
        headers = {"Content-Type": "application/json"}
        data = {
            "login": LOGIN,
            "password": PASSWORD
        }
        
        response = requests.post(f"{IIKO_BASE_URL}/resto/api/auth", json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            log_test("POST JSON", "PASS", f"Session key: {response.text[:50]}...")
        elif response.status_code == 401:
            log_test("POST JSON", "FAIL", f"401: {response.text}")
        elif response.status_code == 500:
            log_test("POST JSON", "FAIL", f"500: {response.text[:100]}...")
        else:
            log_test("POST JSON", "FAIL", f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("POST JSON", "FAIL", f"Exception: {str(e)}")

def test_password_encoding():
    """Test different password encoding methods"""
    print("🔤 TESTING PASSWORD ENCODING METHODS")
    print("=" * 60)
    
    # Test different encodings of the password
    encodings = {
        "original": PASSWORD,
        "url_encoded": urllib.parse.quote(PASSWORD),
        "url_encoded_plus": urllib.parse.quote_plus(PASSWORD),
        "base64": base64.b64encode(PASSWORD.encode()).decode(),
    }
    
    print(f"Password encodings:")
    for name, encoded in encodings.items():
        print(f"  {name}: {encoded}")
    print()
    
    # Test each encoding with GET method
    for encoding_name, encoded_password in encodings.items():
        print(f"Test: GET /resto/api/auth with {encoding_name} encoding")
        try:
            params = {
                "login": LOGIN,
                "pass": encoded_password
            }
            
            response = requests.get(f"{IIKO_BASE_URL}/resto/api/auth", params=params, timeout=10)
            
            if response.status_code == 200:
                log_test(f"GET with {encoding_name} encoding", "PASS", f"Session key: {response.text[:50]}...")
                print(f"🎉 SUCCESS! {encoding_name} encoding worked!")
                return True
            elif response.status_code == 401:
                log_test(f"GET with {encoding_name} encoding", "FAIL", f"401: {response.text}")
            else:
                log_test(f"GET with {encoding_name} encoding", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            log_test(f"GET with {encoding_name} encoding", "FAIL", f"Exception: {str(e)}")
    
    return False

def test_case_sensitivity():
    """Test case sensitivity in login"""
    print("🔠 TESTING CASE SENSITIVITY")
    print("=" * 60)
    
    login_variants = [
        "Sergey",      # Original
        "sergey",      # lowercase
        "SERGEY",      # uppercase
        "Sergey ",     # with trailing space
        " Sergey",     # with leading space
    ]
    
    for login_variant in login_variants:
        print(f"Test: Login variant '{login_variant}'")
        try:
            params = {
                "login": login_variant,
                "pass": PASSWORD
            }
            
            response = requests.get(f"{IIKO_BASE_URL}/resto/api/auth", params=params, timeout=10)
            
            if response.status_code == 200:
                log_test(f"Login '{login_variant}'", "PASS", f"Session key: {response.text[:50]}...")
                print(f"🎉 SUCCESS! Login '{login_variant}' worked!")
                return True
            elif response.status_code == 401:
                log_test(f"Login '{login_variant}'", "FAIL", f"401: {response.text}")
            else:
                log_test(f"Login '{login_variant}'", "FAIL", f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            log_test(f"Login '{login_variant}'", "FAIL", f"Exception: {str(e)}")
    
    return False

def main():
    """Run all authentication tests"""
    print("🔍 IIKO OFFICE DIRECT AUTHENTICATION TESTING")
    print("=" * 80)
    print("🎯 GOAL: Find the correct authentication method for IIKo Office")
    print("🔑 CREDENTIALS: Sergey / metkamfetamin (user confirmed correct)")
    print()
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = False
    
    try:
        # Test 1: Direct authentication methods
        test_direct_iiko_auth()
        
        # Test 2: Password encoding methods
        if not success:
            success = test_password_encoding()
        
        # Test 3: Case sensitivity
        if not success:
            success = test_case_sensitivity()
        
        print("🏁 AUTHENTICATION TESTING COMPLETED")
        print("=" * 80)
        
        if success:
            print("🎉 SUCCESS: Found working authentication method!")
        else:
            print("❌ FAILURE: No authentication method worked")
            print("💡 RECOMMENDATIONS:")
            print("   1. Verify the password is exactly 'metkamfetamin'")
            print("   2. Check if the user account is locked or expired")
            print("   3. Verify the IIKo Office server URL is correct")
            print("   4. Check if there are any special authentication requirements")
        
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")

if __name__ == "__main__":
    main()