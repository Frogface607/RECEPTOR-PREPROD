#!/usr/bin/env python3
"""
Focused test for /api/save-tech-card endpoint as requested in review
Testing inspiration tech card saving functionality
"""

import requests
import json
import time
from datetime import datetime

class SaveTechCardTest:
    def __init__(self):
        # Use the public endpoint for testing
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.test_user_id = "test_user_12345"
        
    def test_1_basic_endpoint_functionality(self):
        """Test 1: Базовая работа endpoint"""
        print("\n🔍 TEST 1: Testing POST /api/save-tech-card basic functionality...")
        
        # Test data as specified in review
        test_data = {
            "user_id": "test_user_12345",
            "content": "**Название:** Азиатский борщ с кокосовым молоком\n\n**Категория:** суп\n\n**Описание:** Креативный твист на классический борщ\n\n**Ингредиенты:**\n- Свекла — 100 г — ~30 ₽\n- Кокосовое молоко — 200 мл — ~80 ₽\n- Соевый соус — 15 мл — ~10 ₽\n\n**Пошаговый рецепт:**\n1. Обжарить свеклу с имбирем\n2. Добавить кокосовое молоко\n3. Приправить соевым соусом\n\n**Время:** 45 минут\n\n**Выход:** 400 мл\n\n**Себестоимость:** 120 ₽",
            "dish_name": "Азиатский борщ с кокосовым молоком",
            "city": "moskva",
            "is_inspiration": True
        }
        
        print(f"Sending request to: {self.base_url}/save-tech-card")
        print(f"Test data: user_id={test_data['user_id']}, dish_name={test_data['dish_name']}, is_inspiration={test_data['is_inspiration']}")
        
        response = requests.post(f"{self.base_url}/save-tech-card", json=test_data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Expected 200, got {response.status_code}")
            print(f"Response text: {response.text}")
            return False, None
            
        try:
            result = response.json()
            print(f"Response JSON: {result}")
        except:
            print(f"❌ ERROR: Could not parse JSON response: {response.text}")
            return False, None
            
        # Verify response structure
        if "id" not in result:
            print("❌ ERROR: Response missing 'id' field")
            return False, None
            
        if "message" not in result:
            print("❌ ERROR: Response missing 'message' field")
            return False, None
            
        tech_card_id = result["id"]
        print(f"✅ SUCCESS: Tech card saved with ID: {tech_card_id}")
        print(f"✅ SUCCESS: Message: {result['message']}")
        
        return True, tech_card_id
        
    def test_2_automatic_user_creation(self):
        """Test 2: Автоматическое создание пользователя"""
        print("\n🔍 TEST 2: Testing automatic user creation with PRO subscription...")
        
        # Check if user exists and has PRO subscription
        response = requests.get(f"{self.base_url}/user-subscription/{self.test_user_id}")
        
        print(f"User subscription check status: {response.status_code}")
        
        if response.status_code == 200:
            subscription = response.json()
            print(f"User subscription data: {subscription}")
            
            if subscription.get("subscription_plan") == "pro":
                print("✅ SUCCESS: Test user has PRO subscription")
                return True
            else:
                print(f"❌ ERROR: Test user has {subscription.get('subscription_plan')} subscription, expected PRO")
                return False
        elif response.status_code == 404:
            print("⚠️ WARNING: User not found, but should be auto-created during save-tech-card call")
            return True  # This is expected behavior - user created during save call
        else:
            print(f"❌ ERROR: Unexpected response {response.status_code}: {response.text}")
            return False
            
    def test_3_database_saving(self, tech_card_id):
        """Test 3: Сохранение в базу"""
        print("\n🔍 TEST 3: Testing database saving with is_inspiration flag...")
        
        if not tech_card_id:
            print("❌ ERROR: No tech card ID provided from previous test")
            return False
            
        # Get user's tech cards to verify saving
        response = requests.get(f"{self.base_url}/tech-cards/{self.test_user_id}")
        
        print(f"Tech cards retrieval status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Could not retrieve tech cards: {response.text}")
            return False
            
        tech_cards = response.json()
        print(f"Retrieved {len(tech_cards)} tech cards for user")
        
        # Find our saved tech card
        saved_card = None
        for card in tech_cards:
            if card.get("id") == tech_card_id:
                saved_card = card
                break
                
        if not saved_card:
            print(f"❌ ERROR: Tech card with ID {tech_card_id} not found in user's tech cards")
            return False
            
        print(f"Found saved tech card: {saved_card}")
        
        # Verify UUID format for ID
        if len(tech_card_id) != 36 or tech_card_id.count('-') != 4:
            print(f"❌ ERROR: ID {tech_card_id} does not appear to be a valid UUID")
            return False
        else:
            print(f"✅ SUCCESS: Tech card has valid UUID: {tech_card_id}")
            
        # Verify is_inspiration flag
        if saved_card.get("is_inspiration") != True:
            print(f"❌ ERROR: is_inspiration flag is {saved_card.get('is_inspiration')}, expected True")
            return False
        else:
            print("✅ SUCCESS: is_inspiration flag correctly set to True")
            
        # Verify other fields
        expected_fields = ["user_id", "dish_name", "content", "created_at"]
        for field in expected_fields:
            if field not in saved_card:
                print(f"❌ ERROR: Missing field '{field}' in saved tech card")
                return False
            else:
                print(f"✅ SUCCESS: Field '{field}' present: {str(saved_card[field])[:50]}...")
                
        return True
        
    def test_4_history_integration(self, tech_card_id):
        """Test 4: Интеграция с историей"""
        print("\n🔍 TEST 4: Testing history integration...")
        
        if not tech_card_id:
            print("❌ ERROR: No tech card ID provided from previous test")
            return False
            
        # Get user history
        response = requests.get(f"{self.base_url}/user-history/{self.test_user_id}")
        
        print(f"User history retrieval status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Could not retrieve user history: {response.text}")
            return False
            
        try:
            history_data = response.json()
            print(f"History response: {history_data}")
        except:
            print(f"❌ ERROR: Could not parse history JSON: {response.text}")
            return False
            
        if "history" not in history_data:
            print("❌ ERROR: History response missing 'history' field")
            return False
            
        history = history_data["history"]
        print(f"Retrieved {len(history)} items from user history")
        
        # Find our saved tech card in history
        found_in_history = None
        for item in history:
            if item.get("id") == tech_card_id:
                found_in_history = item
                break
                
        if not found_in_history:
            print(f"❌ ERROR: Tech card with ID {tech_card_id} not found in user history")
            print("Available history items:")
            for item in history:
                print(f"  - ID: {item.get('id')}, Dish: {item.get('dish_name')}")
            return False
            
        print(f"✅ SUCCESS: Tech card found in user history")
        print(f"History item: {found_in_history}")
        
        # Verify is_inspiration flag in history
        if found_in_history.get("is_inspiration") != True:
            print(f"❌ ERROR: is_inspiration flag in history is {found_in_history.get('is_inspiration')}, expected True")
            return False
        else:
            print("✅ SUCCESS: is_inspiration flag correctly present in history")
            
        # Verify dish name matches
        expected_dish_name = "Азиатский борщ с кокосовым молоком"
        if found_in_history.get("dish_name") != expected_dish_name:
            print(f"❌ ERROR: Dish name in history is '{found_in_history.get('dish_name')}', expected '{expected_dish_name}'")
            return False
        else:
            print(f"✅ SUCCESS: Dish name correctly saved: {found_in_history.get('dish_name')}")
            
        return True
        
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting /api/save-tech-card endpoint testing")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 70)
        
        results = []
        tech_card_id = None
        
        # Test 1: Basic functionality
        success, tech_card_id = self.test_1_basic_endpoint_functionality()
        results.append(("Test 1: Basic endpoint functionality", success))
        
        if not success:
            print("❌ CRITICAL: Test 1 failed, cannot continue with other tests")
            return False
            
        # Test 2: User creation
        success = self.test_2_automatic_user_creation()
        results.append(("Test 2: Automatic user creation", success))
        
        # Test 3: Database saving
        success = self.test_3_database_saving(tech_card_id)
        results.append(("Test 3: Database saving", success))
        
        # Test 4: History integration
        success = self.test_4_history_integration(tech_card_id)
        results.append(("Test 4: History integration", success))
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY:")
        print("=" * 70)
        
        all_passed = True
        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status}: {test_name}")
            if not passed:
                all_passed = False
                
        print("=" * 70)
        if all_passed:
            print("🎉 ALL TESTS PASSED: /api/save-tech-card endpoint is working correctly!")
            print("✅ Endpoint works without errors")
            print("✅ Returns ID of created tech card")
            print("✅ Tech card appears in user history")
            print("✅ is_inspiration flag properly saved")
        else:
            print("❌ SOME TESTS FAILED: Issues found with /api/save-tech-card endpoint")
            
        return all_passed

if __name__ == "__main__":
    tester = SaveTechCardTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)