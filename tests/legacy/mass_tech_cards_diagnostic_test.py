#!/usr/bin/env python3
"""
CRITICAL BUG DIAGNOSIS: Mass Tech Card Generation - Always Error
Testing the POST /api/generate-mass-tech-cards endpoint to identify the root cause
of the reported issue where mass tech card generation always fails.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_mass_tech_card_generation_critical_bug():
    """
    CRITICAL BUG DIAGNOSIS: Test mass tech card generation with real scenarios
    to identify why users are experiencing "всегда возникает ошибка"
    """
    print("🚨 CRITICAL BUG DIAGNOSIS: Mass Tech Card Generation")
    print("=" * 70)
    print("Testing POST /api/generate-mass-tech-cards endpoint")
    print("User Report: 'всегда возникает ошибка при массовой генерации техкарт'")
    print("=" * 70)
    
    # Test user setup
    test_user_id = "constructor_test"
    
    # Step 1: Create/verify PRO user
    print("\n🔧 STEP 1: Setting up PRO test user...")
    try:
        # Try to get user first
        user_response = requests.get(f"{BACKEND_URL}/user-subscription/{test_user_id}", timeout=30)
        
        if user_response.status_code == 404:
            # Create test user with unique email
            import random
            unique_id = random.randint(1000, 9999)
            print(f"Creating new test user with ID: {test_user_id}_{unique_id}...")
            register_data = {
                "email": f"{test_user_id}_{unique_id}@example.com",
                "name": "Constructor Test User",
                "city": "moskva"
            }
            
            register_response = requests.post(f"{BACKEND_URL}/register", json=register_data, timeout=30)
            if register_response.status_code != 200:
                print(f"❌ Failed to create user: {register_response.status_code}")
                print(f"Response: {register_response.text}")
                # Try to use existing user instead
                print("🔄 Trying to use existing test user...")
            else:
                # Update test_user_id to the new one
                user_data = register_response.json()
                test_user_id = user_data.get("id", test_user_id)
                print(f"✅ Test user created with ID: {test_user_id}")
            
            # Upgrade to PRO
            upgrade_data = {"subscription_plan": "pro"}
            upgrade_response = requests.post(f"{BACKEND_URL}/upgrade-subscription/{test_user_id}", json=upgrade_data, timeout=30)
            if upgrade_response.status_code != 200:
                print(f"❌ Failed to upgrade to PRO: {upgrade_response.status_code}")
                print(f"Response: {upgrade_response.text}")
                # Continue anyway - might already be PRO
            else:
                print("✅ User upgraded to PRO")
        else:
            print("✅ Test user already exists")
            # Check if already PRO
            user_data = user_response.json()
            if user_data.get("subscription_plan") != "pro":
                # Upgrade to PRO
                upgrade_data = {"subscription_plan": "pro"}
                upgrade_response = requests.post(f"{BACKEND_URL}/upgrade-subscription/{test_user_id}", json=upgrade_data, timeout=30)
                if upgrade_response.status_code == 200:
                    print("✅ User upgraded to PRO")
            
    except Exception as e:
        print(f"❌ Error setting up test user: {str(e)}")
        print("🔄 Continuing with existing test user...")
        # Continue anyway
    
    # Step 2: Generate a test menu first
    print("\n🍽️ STEP 2: Generating test menu...")
    try:
        menu_request = {
            "user_id": test_user_id,
            "menu_profile": {
                "menuType": "restaurant",
                "dishCount": 6,
                "averageCheck": "medium",
                "cuisineStyle": "russian",
                "specialRequirements": ["local", "seasonal"]
            },
            "venue_profile": {
                "venue_name": "Тест Ресторан Диагностика",
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
            print(f"Response: {json.dumps(menu_data, indent=2, ensure_ascii=False)}")
            return False
        
        print(f"✅ Menu generated successfully in {menu_time:.2f}s")
        print(f"📋 Menu ID: {menu_id}")
        print(f"🍽️ Dishes in menu: {menu_data.get('menu', {}).get('total_dishes', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error generating menu: {str(e)}")
        return False
    
    # Step 3: Test mass tech card generation - THE CRITICAL TEST
    print("\n🎯 STEP 3: CRITICAL TEST - Mass Tech Card Generation...")
    try:
        mass_request = {
            "user_id": test_user_id,
            "menu_id": menu_id
        }
        
        print(f"📤 Request data: {json.dumps(mass_request, indent=2, ensure_ascii=False)}")
        print("⏳ Starting mass tech card generation (this may take 60-120 seconds)...")
        
        start_time = time.time()
        mass_response = requests.post(f"{BACKEND_URL}/generate-mass-tech-cards", json=mass_request, timeout=180)
        mass_time = time.time() - start_time
        
        print(f"⏱️ Response time: {mass_time:.2f} seconds")
        print(f"📊 HTTP Status: {mass_response.status_code}")
        
        if mass_response.status_code != 200:
            print(f"🚨 CRITICAL BUG CONFIRMED: Mass tech card generation failed!")
            print(f"❌ Status Code: {mass_response.status_code}")
            print(f"❌ Error Response: {mass_response.text}")
            
            # Try to parse error details
            try:
                error_data = mass_response.json()
                print(f"❌ Error Details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print("❌ Could not parse error response as JSON")
            
            return False
        
        # Parse successful response
        mass_data = mass_response.json()
        print(f"✅ Mass tech card generation completed!")
        print(f"📊 Generated: {mass_data.get('generated_count', 0)} tech cards")
        print(f"📊 Failed: {mass_data.get('failed_count', 0)} tech cards")
        print(f"📊 Success Rate: {(mass_data.get('generated_count', 0) / (mass_data.get('generated_count', 0) + mass_data.get('failed_count', 0)) * 100):.1f}%")
        
        # Check for failures
        if mass_data.get('failed_count', 0) > 0:
            print("⚠️ Some tech cards failed to generate:")
            for failure in mass_data.get('failed_generations', []):
                print(f"  ❌ {failure.get('dish_name')}: {failure.get('error')}")
        
        # Verify tech card content
        tech_cards = mass_data.get('tech_cards', [])
        if tech_cards:
            sample_card = tech_cards[0]
            print(f"\n📋 Sample tech card: {sample_card.get('dish_name')}")
            print(f"📏 Content length: {len(sample_card.get('content', ''))} characters")
            
            # Check for essential sections
            content = sample_card.get('content', '')
            essential_sections = ['Ингредиенты', 'Пошаговый рецепт', 'Себестоимость', 'КБЖУ']
            missing_sections = []
            for section in essential_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"⚠️ Missing sections in tech card: {missing_sections}")
            else:
                print("✅ All essential sections present in tech card")
        
        print(f"\n🎉 MASS TECH CARD GENERATION TEST PASSED!")
        print(f"✅ No critical bug found in this test scenario")
        return True
        
    except requests.exceptions.Timeout:
        print("🚨 CRITICAL BUG: Request timeout!")
        print("❌ Mass tech card generation timed out after 180 seconds")
        print("💡 This could be the source of user errors - timeout issues")
        return False
        
    except Exception as e:
        print(f"🚨 CRITICAL BUG: Exception during mass tech card generation!")
        print(f"❌ Error: {str(e)}")
        print(f"💡 This could be the source of user errors - exception handling")
        return False

def test_edge_cases_and_error_scenarios():
    """Test edge cases that might cause the reported errors"""
    print("\n🔍 TESTING EDGE CASES AND ERROR SCENARIOS")
    print("=" * 50)
    
    # Test 1: Invalid user_id
    print("\n🧪 Test 1: Invalid user_id...")
    try:
        invalid_request = {
            "user_id": "nonexistent_user",
            "menu_id": "some_menu_id"
        }
        
        response = requests.post(f"{BACKEND_URL}/generate-mass-tech-cards", json=invalid_request, timeout=30)
        
        if response.status_code == 404:
            print("✅ Correctly handles invalid user_id with 404")
        else:
            print(f"⚠️ Unexpected response for invalid user_id: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing invalid user_id: {str(e)}")
    
    # Test 2: Invalid menu_id
    print("\n🧪 Test 2: Invalid menu_id...")
    try:
        invalid_request = {
            "user_id": "constructor_test",
            "menu_id": "nonexistent_menu"
        }
        
        response = requests.post(f"{BACKEND_URL}/generate-mass-tech-cards", json=invalid_request, timeout=30)
        
        if response.status_code == 404:
            print("✅ Correctly handles invalid menu_id with 404")
        else:
            print(f"⚠️ Unexpected response for invalid menu_id: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing invalid menu_id: {str(e)}")
    
    # Test 3: FREE user (should be blocked)
    print("\n🧪 Test 3: FREE user access...")
    try:
        # Create a FREE user
        free_user_id = "free_user_test"
        register_data = {
            "email": f"{free_user_id}@example.com",
            "name": "Free User Test",
            "city": "moskva"
        }
        
        requests.post(f"{BACKEND_URL}/register", json=register_data, timeout=30)
        
        free_request = {
            "user_id": free_user_id,
            "menu_id": "some_menu_id"
        }
        
        response = requests.post(f"{BACKEND_URL}/generate-mass-tech-cards", json=free_request, timeout=30)
        
        if response.status_code == 403:
            print("✅ Correctly blocks FREE users with 403")
        else:
            print(f"⚠️ Unexpected response for FREE user: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing FREE user access: {str(e)}")
    
    # Test 4: Missing parameters
    print("\n🧪 Test 4: Missing parameters...")
    try:
        # Missing menu_id
        incomplete_request = {
            "user_id": "constructor_test"
        }
        
        response = requests.post(f"{BACKEND_URL}/generate-mass-tech-cards", json=incomplete_request, timeout=30)
        
        if response.status_code == 400:
            print("✅ Correctly handles missing menu_id with 400")
        else:
            print(f"⚠️ Unexpected response for missing menu_id: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing missing parameters: {str(e)}")

def main():
    """Main diagnostic function"""
    print("🚨 CRITICAL BUG DIAGNOSIS: Mass Tech Card Generation")
    print("=" * 70)
    print("Investigating user report: 'всегда возникает ошибка при массовой генерации техкарт'")
    print("=" * 70)
    
    # Run main test
    main_test_passed = test_mass_tech_card_generation_critical_bug()
    
    # Run edge case tests
    test_edge_cases_and_error_scenarios()
    
    # Final diagnosis
    print("\n" + "=" * 70)
    print("🔬 DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    if main_test_passed:
        print("✅ Main functionality test PASSED")
        print("💡 Mass tech card generation works correctly in test environment")
        print("🤔 Possible causes of user errors:")
        print("   - Network timeout issues (180+ second requests)")
        print("   - Frontend timeout handling")
        print("   - Specific menu data causing failures")
        print("   - User environment or browser issues")
        print("   - Rate limiting or API quota issues")
    else:
        print("❌ Main functionality test FAILED")
        print("🚨 CRITICAL BUG CONFIRMED in mass tech card generation")
        print("🔧 Immediate investigation and fix required")
    
    print("\n📋 RECOMMENDATIONS:")
    print("1. Check frontend timeout settings")
    print("2. Add better error handling and user feedback")
    print("3. Implement progress indicators for long operations")
    print("4. Add retry mechanisms for failed generations")
    print("5. Monitor API response times and optimize if needed")

if __name__ == "__main__":
    main()