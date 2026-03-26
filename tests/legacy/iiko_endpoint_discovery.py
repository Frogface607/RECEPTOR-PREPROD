#!/usr/bin/env python3
"""
IIKo Office API Endpoint Discovery
Testing various endpoints to find the correct organizations endpoint
"""

import requests
import hashlib
from datetime import datetime

# IIKo server details
IIKO_BASE_URL = "https://edison-bar.iiko.it"
LOGIN = "Sergey"
PASSWORD = "metkamfetamin"

def get_session_key():
    """Get session key using SHA1 hash"""
    password_hash = hashlib.sha1(PASSWORD.encode()).hexdigest()
    
    params = {
        "login": LOGIN,
        "pass": password_hash
    }
    
    response = requests.get(f"{IIKO_BASE_URL}/resto/api/auth", params=params, timeout=10)
    
    if response.status_code == 200:
        return response.text.strip()
    else:
        raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

def test_endpoint(endpoint, session_key, method="GET", params=None):
    """Test an endpoint with the session key"""
    print(f"Testing: {method} {endpoint}")
    
    try:
        if params is None:
            params = {"key": session_key}
        
        if method == "GET":
            response = requests.get(f"{IIKO_BASE_URL}{endpoint}", params=params, timeout=10)
        elif method == "POST":
            response = requests.post(f"{IIKO_BASE_URL}{endpoint}", data=params, timeout=10)
        
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print(f"  ✅ SUCCESS!")
            return True
        else:
            print(f"  ❌ Failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        return False

def main():
    """Test various IIKo Office API endpoints"""
    print("🔍 IIKO OFFICE API ENDPOINT DISCOVERY")
    print("=" * 60)
    
    try:
        # Get session key
        print("Getting session key...")
        session_key = get_session_key()
        print(f"Session key: {session_key[:20]}...")
        print()
        
        # Test various organization endpoints
        organization_endpoints = [
            "/resto/api/corporation/organizations",
            "/resto/api/organizations",
            "/resto/api/corporation",
            "/resto/api/v2/organizations",
            "/resto/api/v1/organizations",
            "/api/organizations",
            "/api/v1/organizations",
            "/api/v2/organizations",
            "/resto/organizations",
            "/organizations"
        ]
        
        print("Testing organization endpoints:")
        success_found = False
        
        for endpoint in organization_endpoints:
            if test_endpoint(endpoint, session_key):
                success_found = True
                print(f"🎉 FOUND WORKING ORGANIZATIONS ENDPOINT: {endpoint}")
                break
            print()
        
        if not success_found:
            print("❌ No working organizations endpoint found")
            
            # Try some menu/nomenclature endpoints as they might give us clues
            print("\nTesting menu/nomenclature endpoints for clues:")
            menu_endpoints = [
                "/resto/api/v2/entities/products/list",
                "/resto/api/products",
                "/resto/api/nomenclature",
                "/resto/api/menu",
                "/api/nomenclature",
                "/api/menu"
            ]
            
            for endpoint in menu_endpoints:
                if test_endpoint(endpoint, session_key):
                    print(f"🎉 FOUND WORKING MENU ENDPOINT: {endpoint}")
                    break
                print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()