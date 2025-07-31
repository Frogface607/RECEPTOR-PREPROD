#!/usr/bin/env python3
"""
Quick test to verify basic tech card generation works
"""

import requests
import json
import time

def test_basic_generation():
    base_url = "https://873f04ec-f2bd-4171-a6a9-6b8e246b3ab2.preview.emergentagent.com/api"
    
    # Create unique user
    test_email = f"test_user_{int(time.time())}@test.com"
    
    print("🔧 Registering test user...")
    user_data = {
        "email": test_email,
        "name": "Test User",
        "city": "moskva"
    }
    
    response = requests.post(f"{base_url}/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return False
    
    user_info = response.json()
    user_id = user_info["id"]
    print(f"✅ User registered with ID: {user_id}")
    
    # Test tech card generation
    print("🍳 Testing tech card generation...")
    dish_data = {
        "dish_name": "Паста Карбонара",
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/generate-tech-card", json=dish_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ Tech card generated successfully!")
            print(f"Preview: {result['tech_card'][:200]}...")
            return True
        else:
            print(f"❌ Generation failed: {result}")
            return False
    else:
        print(f"❌ API error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    success = test_basic_generation()
    if success:
        print("✅ Basic functionality works!")
    else:
        print("❌ Basic functionality failed!")