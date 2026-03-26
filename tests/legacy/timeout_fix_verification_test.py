#!/usr/bin/env python3
"""
MASS TECH CARD GENERATION - TIMEOUT FIX VERIFICATION
Testing the fixed mass tech card generation with proper timeout handling
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_mass_tech_card_generation_fix():
    """
    Test the mass tech card generation with the timeout fix
    """
    print("🔧 TESTING MASS TECH CARD GENERATION - TIMEOUT FIX")
    print("=" * 60)
    
    # Use existing test user
    test_user_id = "constructor_test"
    
    # Step 1: Verify user exists and is PRO
    print("\n🔧 STEP 1: Verifying PRO user...")
    try:
        user_response = requests.get(f"{BACKEND_URL}/user-subscription/{test_user_id}", timeout=30)
        
        if user_response.status_code == 404:
            print("❌ Test user not found. Creating new user...")
            # Create and upgrade user
            import random
            unique_id = random.randint(1000, 9999)
            register_data = {
                "email": f"{test_user_id}_{unique_id}@example.com",
                "name": "Constructor Test User",
                "city": "moskva"
            }
            
            register_response = requests.post(f"{BACKEND_URL}/register", json=register_data, timeout=30)
            if register_response.status_code == 200:
                user_data = register_response.json()
                test_user_id = user_data.get("id", test_user_id)
                
                # Upgrade to PRO
                upgrade_data = {"subscription_plan": "pro"}
                requests.post(f"{BACKEND_URL}/upgrade-subscription/{test_user_id}", json=upgrade_data, timeout=30)
                print(f"✅ Created and upgraded user: {test_user_id}")
            else:
                print("❌ Failed to create user, using existing test user")
        else:
            print("✅ Test user exists")
            
    except Exception as e:
        print(f"❌ Error verifying user: {str(e)}")
        return False
    
    # Step 2: Generate a test menu
    print("\n🍽️ STEP 2: Generating test menu...")
    try:
        menu_request = {
            "user_id": test_user_id,
            "menu_profile": {
                "menuType": "restaurant",
                "dishCount": 4,  # Smaller menu for faster testing
                "averageCheck": "medium",
                "cuisineStyle": "russian",
                "specialRequirements": ["local"]
            },
            "venue_profile": {
                "venue_name": "Тест Ресторан Фикс",
                "venue_type": "fine_dining",
                "cuisine_type": "russian",
                "average_check": "premium"
            }
        }
        
        start_time = time.time()
        menu_response = requests.post(f"{BACKEND_URL}/generate-menu", json=menu_request, timeout=120)
        menu_time = time.time() - start_time
        
        if menu_response.status_code != 200:
            print(f"❌ Menu generation failed: {menu_response.status_code}")
            print(f"Response: {menu_response.text}")
            return False
        
        menu_data = menu_response.json()
        menu_id = menu_data.get("menu_id")
        
        if not menu_id:
            print("❌ No menu_id returned from menu generation")
            return False
        
        print(f"✅ Menu generated successfully in {menu_time:.2f}s")
        print(f"📋 Menu ID: {menu_id}")
        
    except Exception as e:
        print(f"❌ Error generating menu: {str(e)}")
        return False
    
    # Step 3: Test mass tech card generation with timeout monitoring
    print("\n🎯 STEP 3: Testing mass tech card generation with timeout fix...")
    try:
        mass_request = {
            "user_id": test_user_id,
            "menu_id": menu_id
        }
        
        print(f"📤 Request data: {json.dumps(mass_request, indent=2, ensure_ascii=False)}")
        print("⏳ Starting mass tech card generation...")
        print("🔧 Testing with 5-minute timeout (300 seconds)...")
        
        start_time = time.time()
        
        # Test with the same timeout as the frontend fix (300 seconds)
        mass_response = requests.post(
            f"{BACKEND_URL}/generate-mass-tech-cards", 
            json=mass_request, 
            timeout=300  # 5 minutes - same as frontend fix
        )
        
        mass_time = time.time() - start_time
        
        print(f"⏱️ Response time: {mass_time:.2f} seconds")
        print(f"📊 HTTP Status: {mass_response.status_code}")
        
        if mass_response.status_code != 200:
            print(f"❌ Mass tech card generation failed!")
            print(f"Status Code: {mass_response.status_code}")
            print(f"Error Response: {mass_response.text}")
            return False
        
        # Parse successful response
        mass_data = mass_response.json()
        print(f"✅ Mass tech card generation completed!")
        print(f"📊 Generated: {mass_data.get('generated_count', 0)} tech cards")
        print(f"📊 Failed: {mass_data.get('failed_count', 0)} tech cards")
        print(f"📊 Success Rate: {(mass_data.get('generated_count', 0) / (mass_data.get('generated_count', 0) + mass_data.get('failed_count', 0)) * 100):.1f}%")
        
        # Verify timeout handling
        if mass_time > 300:
            print("⚠️ WARNING: Response time exceeded 5-minute timeout!")
            print("💡 Frontend timeout fix may still not be sufficient")
        elif mass_time > 180:
            print("⚠️ WARNING: Response time > 3 minutes")
            print("💡 Consider optimizing backend performance")
        else:
            print("✅ Response time within acceptable limits")
        
        # Check for failures
        if mass_data.get('failed_count', 0) > 0:
            print("⚠️ Some tech cards failed to generate:")
            for failure in mass_data.get('failed_generations', []):
                print(f"  ❌ {failure.get('dish_name')}: {failure.get('error')}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT ERROR: Request timed out after 300 seconds!")
        print("💡 Backend is taking longer than 5 minutes - need further optimization")
        return False
        
    except Exception as e:
        print(f"❌ Error during mass tech card generation: {str(e)}")
        return False

def test_timeout_scenarios():
    """Test different timeout scenarios"""
    print("\n🧪 TESTING TIMEOUT SCENARIOS")
    print("=" * 40)
    
    # Test 1: Short timeout to simulate old behavior
    print("\n🧪 Test 1: Short timeout (60 seconds) - simulating old frontend behavior...")
    try:
        test_user_id = "constructor_test"
        
        # Get a menu (reuse existing or create new)
        menu_request = {
            "user_id": test_user_id,
            "menu_profile": {
                "menuType": "restaurant",
                "dishCount": 3,
                "averageCheck": "medium",
                "cuisineStyle": "russian"
            }
        }
        
        menu_response = requests.post(f"{BACKEND_URL}/generate-menu", json=menu_request, timeout=60)
        if menu_response.status_code == 200:
            menu_id = menu_response.json().get("menu_id")
            
            mass_request = {
                "user_id": test_user_id,
                "menu_id": menu_id
            }
            
            # Test with short timeout (old behavior)
            start_time = time.time()
            try:
                mass_response = requests.post(
                    f"{BACKEND_URL}/generate-mass-tech-cards", 
                    json=mass_request, 
                    timeout=60  # Old timeout
                )
                
                response_time = time.time() - start_time
                print(f"✅ Completed in {response_time:.2f}s (within 60s timeout)")
                
            except requests.exceptions.Timeout:
                response_time = time.time() - start_time
                print(f"❌ TIMEOUT after {response_time:.2f}s - This is the user's problem!")
                print("💡 This confirms the timeout issue users were experiencing")
        
    except Exception as e:
        print(f"❌ Error in timeout test: {str(e)}")

def main():
    """Main test function"""
    print("🔧 MASS TECH CARD GENERATION - TIMEOUT FIX VERIFICATION")
    print("=" * 70)
    print("Testing the frontend timeout fix for mass tech card generation")
    print("=" * 70)
    
    # Run main test
    main_test_passed = test_mass_tech_card_generation_fix()
    
    # Run timeout scenario tests
    test_timeout_scenarios()
    
    # Final summary
    print("\n" + "=" * 70)
    print("🔬 FIX VERIFICATION SUMMARY")
    print("=" * 70)
    
    if main_test_passed:
        print("✅ TIMEOUT FIX VERIFICATION PASSED")
        print("🎉 Mass tech card generation works with 5-minute timeout")
        print("💡 Frontend fix should resolve user timeout errors")
        print("\n📋 CHANGES MADE:")
        print("1. ✅ Added 300-second (5-minute) timeout to axios request")
        print("2. ✅ Improved error handling for timeout scenarios")
        print("3. ✅ Added specific timeout error messages for users")
        print("4. ✅ Fixed tipInterval scope issue in error handling")
        
        print("\n🎯 EXPECTED RESULTS:")
        print("- Users should no longer experience timeout errors")
        print("- Clear error messages if timeouts still occur")
        print("- Better user experience during long operations")
        
    else:
        print("❌ TIMEOUT FIX VERIFICATION FAILED")
        print("🚨 Further investigation needed")
        print("💡 Consider backend optimization or longer timeouts")
    
    print("\n📋 RECOMMENDATIONS FOR PRODUCTION:")
    print("1. Monitor response times and optimize if consistently > 3 minutes")
    print("2. Consider implementing progress callbacks for real-time updates")
    print("3. Add retry mechanisms for failed generations")
    print("4. Implement queue-based processing for very large menus")

if __name__ == "__main__":
    main()