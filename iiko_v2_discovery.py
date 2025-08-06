#!/usr/bin/env python3
"""
IIKo Office API v2 Endpoint Discovery
Testing v2 endpoints since we found one that works
"""

import requests
import hashlib
import json
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

def test_v2_endpoint(endpoint, session_key):
    """Test a v2 endpoint with the session key"""
    print(f"Testing: GET {endpoint}")
    
    try:
        params = {"key": session_key}
        response = requests.get(f"{IIKO_BASE_URL}{endpoint}", params=params, timeout=10)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ SUCCESS! JSON response with {len(data) if isinstance(data, list) else 'object'} items")
                
                # Show sample data structure
                if isinstance(data, list) and len(data) > 0:
                    sample = data[0]
                    print(f"  Sample keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
                elif isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")
                
                return True, data
            except:
                print(f"  ✅ SUCCESS! Non-JSON response: {response.text[:100]}...")
                return True, response.text
        else:
            print(f"  ❌ Failed: {response.text[:100]}...")
            return False, None
            
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        return False, None

def main():
    """Test various IIKo Office API v2 endpoints"""
    print("🔍 IIKO OFFICE API v2 ENDPOINT DISCOVERY")
    print("=" * 60)
    
    try:
        # Get session key
        print("Getting session key...")
        session_key = get_session_key()
        print(f"Session key: {session_key[:20]}...")
        print()
        
        # Test various v2 endpoints
        v2_endpoints = [
            "/resto/api/v2/entities/products/list",  # We know this works
            "/resto/api/v2/entities/organizations/list",
            "/resto/api/v2/entities/corporation/list",
            "/resto/api/v2/entities/departments/list",
            "/resto/api/v2/entities/stores/list",
            "/resto/api/v2/entities/terminals/list",
            "/resto/api/v2/entities/users/list",
            "/resto/api/v2/entities/groups/list",
            "/resto/api/v2/entities/categories/list",
            "/resto/api/v2/corporation/organizations",
            "/resto/api/v2/corporation",
            "/resto/api/v2/organizations",
            "/resto/api/v2/info",
            "/resto/api/v2/system/info"
        ]
        
        print("Testing v2 endpoints:")
        working_endpoints = []
        
        for endpoint in v2_endpoints:
            success, data = test_v2_endpoint(endpoint, session_key)
            if success:
                working_endpoints.append((endpoint, data))
            print()
        
        print("=" * 60)
        print("SUMMARY OF WORKING ENDPOINTS:")
        
        for endpoint, data in working_endpoints:
            print(f"✅ {endpoint}")
            
            # If it looks like organization data, show more details
            if 'organization' in endpoint.lower() or 'corporation' in endpoint.lower():
                print(f"   🏢 This might contain organization data!")
                if isinstance(data, list) and len(data) > 0:
                    sample = data[0]
                    if isinstance(sample, dict):
                        print(f"   Sample: {json.dumps(sample, indent=2, ensure_ascii=False)[:300]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()