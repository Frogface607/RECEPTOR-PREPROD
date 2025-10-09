#!/usr/bin/env python3
"""
Additional PRO AI Functions Testing
Testing the 3 PRO AI endpoints mentioned in test_result.md:
- POST /api/generate-sales-script
- POST /api/generate-food-pairing  
- POST /api/generate-photo-tips
"""

import requests
import json
import time

def test_pro_ai_functions():
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    # First, register a PRO user for testing
    print("🔧 Setting up PRO user for testing...")
    
    # Register user
    user_data = {
        "email": "pro_test@example.com",
        "name": "PRO Test User",
        "city": "moskva"
    }
    
    response = requests.post(f"{base_url}/register", json=user_data)
    if response.status_code == 200:
        user = response.json()
        user_id = user["id"]
        print(f"✅ User registered: {user_id}")
    else:
        print(f"❌ Failed to register user: {response.status_code}")
        return False
    
    # Upgrade to PRO
    upgrade_data = {"subscription_plan": "pro"}
    response = requests.post(f"{base_url}/upgrade-subscription/{user_id}", json=upgrade_data)
    if response.status_code == 200:
        print("✅ User upgraded to PRO")
    else:
        print(f"❌ Failed to upgrade to PRO: {response.status_code}")
        return False
    
    # Generate a sample tech card first
    print("\n🔧 Generating sample tech card...")
    tech_card_data = {
        "dish_name": "Паста Карбонара",
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/generate-tech-card", json=tech_card_data, timeout=60)
    if response.status_code == 200:
        result = response.json()
        tech_card_content = result["tech_card"]
        print("✅ Sample tech card generated")
    else:
        print(f"❌ Failed to generate tech card: {response.status_code}")
        return False
    
    # Test PRO AI functions
    results = []
    
    # Test 1: Sales Script Generation
    print("\n🔍 Testing POST /api/generate-sales-script...")
    try:
        data = {
            "user_id": user_id,
            "tech_card": tech_card_content
        }
        
        response = requests.post(f"{base_url}/generate-sales-script", json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if "script" in result and len(result["script"]) > 200:
                print("✅ Sales script generated successfully")
                print(f"   Script length: {len(result['script'])} chars")
                results.append(("Sales Script", "PASS"))
            else:
                print("❌ Sales script too short or missing")
                results.append(("Sales Script", "FAIL"))
        elif response.status_code == 403:
            print("❌ PRO subscription validation failed")
            results.append(("Sales Script", "FAIL"))
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            results.append(("Sales Script", "FAIL"))
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results.append(("Sales Script", "FAIL"))
    
    # Test 2: Food Pairing Generation
    print("\n🔍 Testing POST /api/generate-food-pairing...")
    try:
        data = {
            "user_id": user_id,
            "tech_card": tech_card_content
        }
        
        response = requests.post(f"{base_url}/generate-food-pairing", json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if "pairing" in result and len(result["pairing"]) > 200:
                print("✅ Food pairing generated successfully")
                print(f"   Pairing length: {len(result['pairing'])} chars")
                results.append(("Food Pairing", "PASS"))
            else:
                print("❌ Food pairing too short or missing")
                results.append(("Food Pairing", "FAIL"))
        elif response.status_code == 403:
            print("❌ PRO subscription validation failed")
            results.append(("Food Pairing", "FAIL"))
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            results.append(("Food Pairing", "FAIL"))
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results.append(("Food Pairing", "FAIL"))
    
    # Test 3: Photo Tips Generation
    print("\n🔍 Testing POST /api/generate-photo-tips...")
    try:
        data = {
            "user_id": user_id,
            "tech_card": tech_card_content
        }
        
        response = requests.post(f"{base_url}/generate-photo-tips", json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if "tips" in result and len(result["tips"]) > 200:
                print("✅ Photo tips generated successfully")
                print(f"   Tips length: {len(result['tips'])} chars")
                results.append(("Photo Tips", "PASS"))
            else:
                print("❌ Photo tips too short or missing")
                results.append(("Photo Tips", "FAIL"))
        elif response.status_code == 403:
            print("❌ PRO subscription validation failed")
            results.append(("Photo Tips", "FAIL"))
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            results.append(("Photo Tips", "FAIL"))
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results.append(("Photo Tips", "FAIL"))
    
    # Test 4: Free user restriction
    print("\n🔍 Testing PRO feature restriction for free users...")
    
    # Register a free user
    free_user_data = {
        "email": "free_test@example.com",
        "name": "Free Test User",
        "city": "moskva"
    }
    
    response = requests.post(f"{base_url}/register", json=free_user_data)
    if response.status_code == 200:
        free_user = response.json()
        free_user_id = free_user["id"]
        
        # Try to use PRO function with free user (should fail)
        data = {
            "user_id": free_user_id,
            "tech_card": tech_card_content
        }
        
        response = requests.post(f"{base_url}/generate-sales-script", json=data, timeout=30)
        
        if response.status_code == 403:
            print("✅ Free user correctly blocked from PRO features")
            results.append(("PRO Restriction", "PASS"))
        else:
            print(f"❌ Free user not blocked (HTTP {response.status_code})")
            results.append(("PRO Restriction", "FAIL"))
    else:
        print("❌ Failed to register free user for restriction test")
        results.append(("PRO Restriction", "FAIL"))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PRO AI FUNCTIONS TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, status in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} {test_name}: {status}")
        if status == "PASS":
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL PRO AI FUNCTIONS WORKING CORRECTLY!")
        return True
    else:
        print("🚨 SOME PRO AI FUNCTIONS HAVE ISSUES!")
        return False

if __name__ == "__main__":
    success = test_pro_ai_functions()
    exit(0 if success else 1)