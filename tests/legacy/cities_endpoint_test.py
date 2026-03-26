#!/usr/bin/env python3
"""
Cities Endpoint Test - Quick diagnostic test for registration form city dropdown issue
Testing GET /api/cities endpoint to verify it returns proper city data format
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"

def test_cities_endpoint():
    """Test GET /api/cities endpoint"""
    print("🎯 CITIES ENDPOINT TESTING STARTED")
    print("=" * 60)
    
    try:
        # Test GET /api/cities endpoint
        print("📡 Testing GET /api/cities endpoint...")
        
        url = f"{BACKEND_URL}/api/cities"
        print(f"Request URL: {url}")
        
        response = requests.get(url, timeout=30)
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"✅ Response Time: {response.elapsed.total_seconds():.2f} seconds")
        
        if response.status_code == 200:
            cities_data = response.json()
            print(f"✅ Response Type: {type(cities_data)}")
            print(f"✅ Cities Count: {len(cities_data)}")
            
            # Verify response format
            if isinstance(cities_data, list) and len(cities_data) > 0:
                print("\n📋 CITIES DATA FORMAT VERIFICATION:")
                
                # Check first few cities for proper format
                for i, city in enumerate(cities_data[:3]):
                    print(f"City {i+1}: {city}")
                    
                    # Verify required fields
                    required_fields = ['code', 'name']
                    missing_fields = [field for field in required_fields if field not in city]
                    
                    if missing_fields:
                        print(f"❌ Missing fields in city {i+1}: {missing_fields}")
                        return False
                    else:
                        print(f"✅ City {i+1} has required fields: code='{city['code']}', name='{city['name']}'")
                
                # Check for specific cities mentioned in the issue
                moscow_found = any(city['code'] == 'moskva' and city['name'] == 'Москва' for city in cities_data)
                spb_found = any(city['code'] == 'spb' and city['name'] == 'Санкт-Петербург' for city in cities_data)
                
                print(f"\n🔍 SPECIFIC CITIES VERIFICATION:")
                print(f"✅ Moscow found: {moscow_found}")
                print(f"✅ Saint Petersburg found: {spb_found}")
                
                # Show all available cities
                print(f"\n📋 ALL AVAILABLE CITIES:")
                for city in cities_data:
                    print(f"  - {city['code']}: {city['name']}")
                
                print(f"\n🎉 CITIES ENDPOINT TEST RESULT: SUCCESS")
                print(f"✅ Endpoint exists and returns proper city data format")
                print(f"✅ Array format: [{{'code': 'moskva', 'name': 'Москва'}}, ...]")
                print(f"✅ Total cities available: {len(cities_data)}")
                print(f"✅ Registration form should be able to use this data")
                
                return True
                
            else:
                print(f"❌ Invalid response format. Expected array, got: {type(cities_data)}")
                return False
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout after 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - backend may be down")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main test execution"""
    print("🚀 CITIES ENDPOINT DIAGNOSTIC TEST")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = test_cities_endpoint()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 CITIES ENDPOINT TEST COMPLETED SUCCESSFULLY")
        print("✅ Backend /api/cities endpoint is working correctly")
        print("✅ Frontend can use this endpoint for city dropdown")
        print("✅ No need for frontend fallback cities")
    else:
        print("❌ CITIES ENDPOINT TEST FAILED")
        print("❌ Backend /api/cities endpoint has issues")
        print("⚠️  Frontend fallback cities will be used")
    
    return success

if __name__ == "__main__":
    main()