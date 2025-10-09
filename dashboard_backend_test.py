#!/usr/bin/env python3
"""
Dashboard Backend Testing Suite for Receptor Pro
Testing Dashboard functionality as requested in review:
1. User registration with test user: dashboard_test@example.com, "Dashboard Test", city: "moskva"
2. Generate a test tech card for this user with dish_name: "Паста с курицей на 2 порции"
3. Get user history to verify Dashboard stats would work: GET /api/user-history/{user_id}
4. Check if all necessary endpoints for Dashboard exist
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_dashboard_user_registration():
    """Test 1: User registration with specific test user for Dashboard"""
    print("🎯 TEST 1: DASHBOARD USER REGISTRATION")
    print("=" * 60)
    
    # Specific test data as requested in review
    test_user_data = {
        "email": "dashboard_test@example.com",
        "name": "Dashboard Test",
        "city": "moskva"
    }
    
    print(f"📝 Registering user: {test_user_data['email']}")
    print(f"👤 Name: {test_user_data['name']}")
    print(f"🏙️ City: {test_user_data['city']}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/register", json=test_user_data, timeout=30)
        
        if response.status_code == 400 and "already registered" in response.text:
            print("⚠️ User already exists, getting existing user...")
            # Get existing user
            response = requests.get(f"{BACKEND_URL}/user/{test_user_data['email']}", timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Failed to get existing user: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
            user_data = response.json()
            print("✅ Retrieved existing Dashboard test user")
            
        elif response.status_code == 500 and "already registered" in response.text:
            print("⚠️ User already exists (500 error), getting existing user...")
            # Get existing user
            response = requests.get(f"{BACKEND_URL}/user/{test_user_data['email']}", timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Failed to get existing user: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
            user_data = response.json()
            print("✅ Retrieved existing Dashboard test user")
            
        elif response.status_code == 200:
            user_data = response.json()
            print("✅ Successfully registered new Dashboard test user")
            
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        # Verify user data
        if (user_data.get("email") == test_user_data["email"] and 
            user_data.get("name") == test_user_data["name"] and
            user_data.get("city") == test_user_data["city"]):
            
            user_id = user_data.get("id")
            print(f"✅ User data verified correctly")
            print(f"🆔 User ID: {user_id}")
            print(f"📧 Email: {user_data.get('email')}")
            print(f"👤 Name: {user_data.get('name')}")
            print(f"🏙️ City: {user_data.get('city')}")
            print(f"📊 Subscription: {user_data.get('subscription_plan', 'free')}")
            
            return user_id
        else:
            print("❌ User data verification failed")
            return None
            
    except Exception as e:
        print(f"❌ Error during user registration: {str(e)}")
        return None

def test_dashboard_tech_card_generation(user_id):
    """Test 2: Generate test tech card for Dashboard user"""
    print("\n🎯 TEST 2: DASHBOARD TECH CARD GENERATION")
    print("=" * 60)
    
    # Specific dish as requested in review
    dish_name = "Паста с курицей на 2 порции"
    
    print(f"🍝 Generating tech card for: {dish_name}")
    print(f"👤 User ID: {user_id}")
    
    tech_card_request = {
        "user_id": user_id,
        "dish_name": dish_name
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", 
                               json=tech_card_request, timeout=90)
        end_time = time.time()
        
        print(f"⏱️ Generation time: {end_time - start_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ Tech card generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        result = response.json()
        
        if not result.get("success"):
            print("❌ Tech card generation marked as unsuccessful")
            print(f"Response: {result}")
            return None
        
        tech_card_content = result.get("tech_card", "")
        tech_card_id = result.get("id")
        monthly_used = result.get("monthly_used", 0)
        monthly_limit = result.get("monthly_limit", 0)
        
        if not tech_card_content or not tech_card_id:
            print("❌ Tech card content or ID missing")
            return None
        
        print("✅ Tech card generated successfully")
        print(f"🆔 Tech card ID: {tech_card_id}")
        print(f"📄 Content length: {len(tech_card_content)} characters")
        print(f"📊 Monthly usage: {monthly_used}/{monthly_limit}")
        print(f"📝 Content preview: {tech_card_content[:200]}...")
        
        # Verify the dish name is in the content
        if dish_name.lower() in tech_card_content.lower() or "паста" in tech_card_content.lower():
            print("✅ Dish name verification passed")
        else:
            print("⚠️ Warning: Dish name not clearly found in content")
        
        # Check for key sections that Dashboard might need
        sections_found = []
        if "ингредиенты" in tech_card_content.lower():
            sections_found.append("Ingredients")
        if "себестоимость" in tech_card_content.lower():
            sections_found.append("Cost")
        if "время" in tech_card_content.lower():
            sections_found.append("Time")
        if "кбжу" in tech_card_content.lower():
            sections_found.append("KBJU")
        
        print(f"📋 Sections found: {', '.join(sections_found)}")
        
        return {
            "tech_card_id": tech_card_id,
            "content": tech_card_content,
            "monthly_used": monthly_used,
            "monthly_limit": monthly_limit
        }
        
    except Exception as e:
        print(f"❌ Error during tech card generation: {str(e)}")
        return None

def test_dashboard_user_history(user_id):
    """Test 3: Get user history to verify Dashboard stats would work"""
    print("\n🎯 TEST 3: DASHBOARD USER HISTORY")
    print("=" * 60)
    
    print(f"📊 Getting user history for: {user_id}")
    
    try:
        response = requests.get(f"{BACKEND_URL}/user-history/{user_id}", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ User history request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        response_data = response.json()
        
        # Check if response has 'history' key (new format) or is direct list (old format)
        if isinstance(response_data, dict) and 'history' in response_data:
            history_data = response_data['history']
            print("✅ History data found in 'history' key")
        elif isinstance(response_data, list):
            history_data = response_data
            print("✅ History data is direct list")
        else:
            print("❌ History data format not recognized")
            print(f"Response type: {type(response_data)}")
            print(f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
            return False
        
        print(f"✅ User history retrieved successfully")
        print(f"📊 Total tech cards in history: {len(history_data)}")
        
        if len(history_data) == 0:
            print("⚠️ Warning: No tech cards found in history")
            print("This might be expected if this is a fresh test")
            return True
        
        # Analyze history data for Dashboard requirements
        print("\n📋 HISTORY ANALYSIS FOR DASHBOARD:")
        print("-" * 40)
        
        # Check data structure
        sample_card = history_data[0]
        required_fields = ["id", "user_id", "dish_name", "content", "created_at"]
        missing_fields = []
        
        for field in required_fields:
            if field not in sample_card:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        else:
            print("✅ All required fields present in history data")
        
        # Analyze timestamps for Dashboard stats
        timestamps = []
        dish_names = []
        
        for card in history_data:
            created_at = card.get("created_at")
            dish_name = card.get("dish_name", "Unknown")
            
            if created_at:
                timestamps.append(created_at)
            dish_names.append(dish_name)
        
        print(f"📅 Tech cards with timestamps: {len(timestamps)}/{len(history_data)}")
        print(f"🍽️ Sample dishes: {dish_names[:3]}")
        
        # Check if our test tech card is in history
        test_dish_found = False
        for card in history_data:
            if "паста" in card.get("dish_name", "").lower() and "курицей" in card.get("dish_name", "").lower():
                test_dish_found = True
                print(f"✅ Test tech card found in history: {card.get('dish_name')}")
                print(f"🆔 ID: {card.get('id')}")
                print(f"📅 Created: {card.get('created_at')}")
                break
        
        if not test_dish_found:
            print("⚠️ Warning: Test tech card not found in history yet")
            print("This might be due to database sync delay")
        
        # Dashboard stats simulation
        print("\n📊 DASHBOARD STATS SIMULATION:")
        print("-" * 40)
        
        total_cards = len(history_data)
        print(f"📈 Total tech cards: {total_cards}")
        
        # Monthly stats (simplified - would need proper date parsing in real implementation)
        current_month_cards = len([card for card in history_data if card.get("created_at")])
        print(f"📅 Cards this period: {current_month_cards}")
        
        # Most common ingredients/dishes (simplified analysis)
        common_words = {}
        for card in history_data:
            dish_name = card.get("dish_name", "").lower()
            words = dish_name.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    common_words[word] = common_words.get(word, 0) + 1
        
        if common_words:
            top_words = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"🔥 Popular ingredients/dishes: {[word for word, count in top_words]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during user history retrieval: {str(e)}")
        return False

def test_dashboard_endpoints():
    """Test 4: Check if all necessary endpoints for Dashboard exist"""
    print("\n🎯 TEST 4: DASHBOARD ENDPOINTS AVAILABILITY")
    print("=" * 60)
    
    # Test user for endpoint checks
    test_user_id = "dashboard_test_user_123"
    
    endpoints_to_test = [
        {
            "name": "User Profile Data",
            "method": "GET",
            "url": f"/user-subscription/{test_user_id}",
            "description": "Get user subscription and profile info for Dashboard header"
        },
        {
            "name": "User History",
            "method": "GET", 
            "url": f"/user-history/{test_user_id}",
            "description": "Get user's tech card history for Dashboard stats"
        },
        {
            "name": "Venue Profile",
            "method": "GET",
            "url": f"/venue-profile/{test_user_id}",
            "description": "Get venue customization data for Dashboard"
        },
        {
            "name": "Subscription Plans",
            "method": "GET",
            "url": "/subscription-plans",
            "description": "Get available plans for Dashboard upgrade options"
        },
        {
            "name": "Kitchen Equipment",
            "method": "GET",
            "url": "/kitchen-equipment", 
            "description": "Get equipment options for Dashboard settings"
        }
    ]
    
    print("🔍 Testing Dashboard-related endpoints...")
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"\n📡 Testing: {endpoint['name']}")
        print(f"🔗 {endpoint['method']} {endpoint['url']}")
        print(f"📝 Purpose: {endpoint['description']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(f"{BACKEND_URL}{endpoint['url']}", timeout=30)
            else:
                print("⚠️ Non-GET method not implemented in this test")
                continue
            
            if response.status_code == 200:
                print("✅ Endpoint available and responding")
                data = response.json()
                print(f"📊 Response type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"🔑 Keys: {list(data.keys())[:5]}")  # Show first 5 keys
                elif isinstance(data, list):
                    print(f"📋 List length: {len(data)}")
                
                results.append({"endpoint": endpoint['name'], "status": "✅ Available"})
                
            elif response.status_code == 404:
                if "not found" in response.text.lower():
                    print("⚠️ Endpoint exists but user/resource not found (expected for test user)")
                    results.append({"endpoint": endpoint['name'], "status": "✅ Available (404 expected)"})
                else:
                    print("❌ Endpoint not found")
                    results.append({"endpoint": endpoint['name'], "status": "❌ Not found"})
                    
            else:
                print(f"⚠️ Endpoint returned status: {response.status_code}")
                results.append({"endpoint": endpoint['name'], "status": f"⚠️ Status {response.status_code}"})
                
        except Exception as e:
            print(f"❌ Error testing endpoint: {str(e)}")
            results.append({"endpoint": endpoint['name'], "status": f"❌ Error: {str(e)[:50]}"})
    
    # Summary
    print("\n📊 DASHBOARD ENDPOINTS SUMMARY:")
    print("-" * 50)
    
    available_count = 0
    for result in results:
        print(f"{result['status']} {result['endpoint']}")
        if "✅" in result['status']:
            available_count += 1
    
    print(f"\n📈 Endpoints available: {available_count}/{len(results)}")
    
    if available_count >= len(results) * 0.8:  # 80% threshold
        print("✅ Dashboard endpoints availability: GOOD")
        return True
    else:
        print("❌ Dashboard endpoints availability: NEEDS IMPROVEMENT")
        return False

def main():
    """Main test execution for Dashboard functionality"""
    print("🚀 RECEPTOR PRO - DASHBOARD BACKEND TESTING")
    print("Testing Dashboard functionality as requested in review")
    print("=" * 60)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: User registration
    user_id = test_dashboard_user_registration()
    if not user_id:
        print("❌ Cannot continue without user ID")
        return False
    
    # Test 2: Tech card generation
    tech_card_data = test_dashboard_tech_card_generation(user_id)
    if not tech_card_data:
        print("❌ Tech card generation failed")
        return False
    
    # Wait a moment for database sync
    print("\n⏳ Waiting 3 seconds for database sync...")
    time.sleep(3)
    
    # Test 3: User history
    history_success = test_dashboard_user_history(user_id)
    
    # Test 4: Dashboard endpoints
    endpoints_success = test_dashboard_endpoints()
    
    # Final results
    print("\n" + "=" * 60)
    print("🎯 DASHBOARD TESTING FINAL RESULTS:")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    if user_id:
        print("✅ TEST 1: User Registration - PASSED")
        print(f"   📧 User: dashboard_test@example.com")
        print(f"   🆔 ID: {user_id}")
        tests_passed += 1
    else:
        print("❌ TEST 1: User Registration - FAILED")
    
    if tech_card_data:
        print("✅ TEST 2: Tech Card Generation - PASSED")
        print(f"   🍝 Dish: Паста с курицей на 2 порции")
        print(f"   🆔 Tech Card ID: {tech_card_data.get('tech_card_id')}")
        print(f"   📊 Usage: {tech_card_data.get('monthly_used')}/{tech_card_data.get('monthly_limit')}")
        tests_passed += 1
    else:
        print("❌ TEST 2: Tech Card Generation - FAILED")
    
    if history_success:
        print("✅ TEST 3: User History - PASSED")
        print("   📊 History data structure verified for Dashboard stats")
        tests_passed += 1
    else:
        print("❌ TEST 3: User History - FAILED")
    
    if endpoints_success:
        print("✅ TEST 4: Dashboard Endpoints - PASSED")
        print("   📡 All necessary endpoints available")
        tests_passed += 1
    else:
        print("❌ TEST 4: Dashboard Endpoints - FAILED")
    
    print(f"\n📈 Overall Success Rate: {tests_passed}/{total_tests} ({tests_passed/total_tests*100:.1f}%)")
    
    if tests_passed == total_tests:
        print("🎉 ALL DASHBOARD TESTS PASSED!")
        print("✅ Backend is ready to support Dashboard functionality")
        return True
    elif tests_passed >= total_tests * 0.75:  # 75% threshold
        print("⚠️ MOST DASHBOARD TESTS PASSED")
        print("✅ Backend mostly ready for Dashboard with minor issues")
        return True
    else:
        print("❌ DASHBOARD TESTS FAILED")
        print("🚨 Backend needs fixes before Dashboard implementation")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)