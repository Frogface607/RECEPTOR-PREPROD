import requests
import unittest
import random
import string
import time
from datetime import datetime

class SubscriptionAPITest(unittest.TestCase):
    def setUp(self):
        # Use the public endpoint for testing
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.user_id = None
        self.user_email = f"test_user_{self.random_string(6)}@example.com"
        self.user_name = f"Test User {self.random_string(4)}"
        
    def random_string(self, length=6):
        """Generate a random string for test data"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def test_01_get_subscription_plans(self):
        """Test retrieving subscription plans"""
        print("\n🔍 Testing GET /subscription-plans...")
        
        response = requests.get(f"{self.base_url}/subscription-plans")
        
        self.assertEqual(response.status_code, 200, "Failed to get subscription plans")
        plans = response.json()
        
        # Verify all subscription tiers exist
        self.assertTrue("free" in plans, "Free plan not found")
        self.assertTrue("starter" in plans, "Starter plan not found")
        self.assertTrue("pro" in plans, "PRO plan not found")
        self.assertTrue("business" in plans, "Business plan not found")
        
        # Verify plan details
        self.assertEqual(plans["free"]["monthly_tech_cards"], 3, "Free plan should have 3 tech cards")
        self.assertEqual(plans["starter"]["monthly_tech_cards"], 25, "Starter plan should have 25 tech cards")
        self.assertEqual(plans["pro"]["monthly_tech_cards"], -1, "PRO plan should have unlimited tech cards")
        self.assertEqual(plans["business"]["monthly_tech_cards"], -1, "Business plan should have unlimited tech cards")
        
        # Verify kitchen equipment feature
        self.assertFalse(plans["free"]["kitchen_equipment"], "Free plan should not have kitchen equipment feature")
        self.assertFalse(plans["starter"]["kitchen_equipment"], "Starter plan should not have kitchen equipment feature")
        self.assertTrue(plans["pro"]["kitchen_equipment"], "PRO plan should have kitchen equipment feature")
        self.assertTrue(plans["business"]["kitchen_equipment"], "Business plan should have kitchen equipment feature")
        
        print("✅ Successfully retrieved subscription plans")
        return plans
    
    def test_02_get_kitchen_equipment(self):
        """Test retrieving kitchen equipment list"""
        print("\n🔍 Testing GET /kitchen-equipment...")
        
        response = requests.get(f"{self.base_url}/kitchen-equipment")
        
        self.assertEqual(response.status_code, 200, "Failed to get kitchen equipment list")
        equipment = response.json()
        
        # Verify equipment categories
        self.assertTrue("cooking_methods" in equipment, "Cooking methods category not found")
        self.assertTrue("prep_equipment" in equipment, "Prep equipment category not found")
        self.assertTrue("storage" in equipment, "Storage category not found")
        
        # Verify equipment items
        self.assertTrue(len(equipment["cooking_methods"]) > 0, "No cooking methods found")
        self.assertTrue(len(equipment["prep_equipment"]) > 0, "No prep equipment found")
        self.assertTrue(len(equipment["storage"]) > 0, "No storage equipment found")
        
        # Verify equipment item structure
        sample_item = equipment["cooking_methods"][0]
        self.assertTrue("id" in sample_item, "Equipment item missing ID")
        self.assertTrue("name" in sample_item, "Equipment item missing name")
        self.assertTrue("category" in sample_item, "Equipment item missing category")
        
        print(f"✅ Successfully retrieved kitchen equipment with {len(equipment['cooking_methods']) + len(equipment['prep_equipment']) + len(equipment['storage'])} items")
        return equipment
    
    def test_03_register_user(self):
        """Test user registration with subscription fields"""
        print("\n🔍 Testing POST /register...")
        data = {
            "email": self.user_email,
            "name": self.user_name,
            "city": "moskva"  # Using Moscow as the test city
        }
        
        response = requests.post(f"{self.base_url}/register", json=data)
        
        self.assertEqual(response.status_code, 200, f"Failed to register user: {response.text}")
        user_data = response.json()
        self.assertEqual(user_data["email"], self.user_email)
        self.assertEqual(user_data["name"], self.user_name)
        self.assertEqual(user_data["city"], "moskva")
        self.assertIsNotNone(user_data["id"], "User ID not returned")
        
        # Verify subscription fields
        self.assertEqual(user_data["subscription_plan"], "free", "New user should start with free plan")
        self.assertEqual(user_data["monthly_tech_cards_used"], 0, "New user should have 0 tech cards used")
        self.assertIsNotNone(user_data["monthly_reset_date"], "Monthly reset date not set")
        self.assertEqual(user_data["kitchen_equipment"], [], "New user should have empty kitchen equipment")
        
        # Save user ID for later tests
        self.user_id = user_data["id"]
        print(f"✅ Successfully registered user with ID: {self.user_id}")
        return user_data
    
    def test_04_get_user_subscription(self):
        """Test getting user's subscription details"""
        print("\n🔍 Testing GET /user-subscription/{user_id}...")
        
        # First ensure we have a registered user
        if not hasattr(self, 'user_id') or not self.user_id:
            self.test_03_register_user()
            
        response = requests.get(f"{self.base_url}/user-subscription/{self.user_id}")
        
        self.assertEqual(response.status_code, 200, f"Failed to get user subscription: {response.text}")
        subscription = response.json()
        
        # Verify subscription data structure
        self.assertTrue("subscription_plan" in subscription, "Subscription plan not in response")
        self.assertTrue("plan_info" in subscription, "Plan info not in response")
        self.assertTrue("monthly_tech_cards_used" in subscription, "Monthly tech cards used not in response")
        self.assertTrue("monthly_reset_date" in subscription, "Monthly reset date not in response")
        self.assertTrue("kitchen_equipment" in subscription, "Kitchen equipment not in response")
        
        # New users should start with free plan
        self.assertEqual(subscription["subscription_plan"], "free", "New user should start with free plan")
        self.assertEqual(subscription["monthly_tech_cards_used"], 0, "New user should have 0 tech cards used")
        
        print(f"✅ Successfully retrieved user subscription: {subscription['subscription_plan']} plan")
        return subscription
    
    def test_05_free_tier_usage_limits(self):
        """Test usage limits for free tier"""
        print("\n🔍 Testing free tier usage limits...")
        
        # Create a new user with free plan
        free_email = f"free_user_{self.random_string(6)}@example.com"
        free_name = f"Free User {self.random_string(4)}"
        
        data = {
            "email": free_email,
            "name": free_name,
            "city": "moskva"
        }
        
        response = requests.post(f"{self.base_url}/register", json=data)
        self.assertEqual(response.status_code, 200, "Failed to register free tier user")
        free_user = response.json()
        free_user_id = free_user["id"]
        
        # Generate tech cards up to the limit (3 for free tier)
        results = []
        for i in range(4):  # Try to generate 4 (one over the limit)
            data = {
                "dish_name": f"Test Dish {i+1}",
                "user_id": free_user_id
            }
            
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
            
            if i < 3:  # First 3 should succeed
                self.assertEqual(response.status_code, 200, f"Failed to generate tech card {i+1}")
                result = response.json()
                self.assertEqual(result["monthly_used"], i+1, f"Monthly usage count incorrect after generating card {i+1}")
                self.assertEqual(result["monthly_limit"], 3, "Free tier should have 3 tech cards limit")
                results.append(result)
            else:  # 4th should fail with 403
                self.assertEqual(response.status_code, 403, "Should not be able to exceed free tier limit")
                error = response.json()
                self.assertTrue("detail" in error, "Error detail not in response")
                self.assertTrue("лимит" in error["detail"], "Error should mention limit")
                results.append(error)
        
        print("✅ Successfully tested free tier usage limits")
        return results
    
    def test_06_upgrade_subscription(self):
        """Test upgrading user's subscription"""
        print("\n🔍 Testing POST /upgrade-subscription/{user_id}...")
        
        # First ensure we have a registered user
        if not hasattr(self, 'user_id') or not self.user_id:
            self.test_03_register_user()
            
        # Upgrade to PRO plan
        data = {
            "subscription_plan": "pro"
        }
        
        response = requests.post(f"{self.base_url}/upgrade-subscription/{self.user_id}", json=data)
        
        self.assertEqual(response.status_code, 200, f"Failed to upgrade subscription: {response.text}")
        result = response.json()
        self.assertTrue("success" in result, "Success flag not in response")
        self.assertTrue(result["success"], "Subscription upgrade not marked as successful")
        
        # Verify the upgrade was applied
        response = requests.get(f"{self.base_url}/user-subscription/{self.user_id}")
        self.assertEqual(response.status_code, 200, "Failed to get updated subscription")
        subscription = response.json()
        self.assertEqual(subscription["subscription_plan"], "pro", "Subscription not upgraded to PRO")
        
        print("✅ Successfully upgraded user to PRO subscription")
        return subscription
    
    def test_07_update_kitchen_equipment(self):
        """Test updating user's kitchen equipment (PRO feature)"""
        print("\n🔍 Testing POST /update-kitchen-equipment/{user_id}...")
        
        # First ensure we have a registered user with PRO subscription
        if not hasattr(self, 'user_id') or not self.user_id:
            self.test_03_register_user()
            self.test_06_upgrade_subscription()  # Upgrade to PRO
            
        # Get available equipment to select valid IDs
        equipment = self.test_02_get_kitchen_equipment()
        
        # Select a few equipment items
        equipment_ids = [
            equipment["cooking_methods"][0]["id"],
            equipment["cooking_methods"][2]["id"],
            equipment["prep_equipment"][0]["id"],
            equipment["storage"][0]["id"]
        ]
        
        data = {
            "equipment_ids": equipment_ids
        }
        
        response = requests.post(f"{self.base_url}/update-kitchen-equipment/{self.user_id}", json=data)
        
        self.assertEqual(response.status_code, 200, f"Failed to update kitchen equipment: {response.text}")
        result = response.json()
        self.assertTrue("success" in result, "Success flag not in response")
        self.assertTrue(result["success"], "Kitchen equipment update not marked as successful")
        
        # Verify the equipment was updated
        response = requests.get(f"{self.base_url}/user-subscription/{self.user_id}")
        self.assertEqual(response.status_code, 200, "Failed to get updated subscription")
        subscription = response.json()
        self.assertEqual(set(subscription["kitchen_equipment"]), set(equipment_ids), "Kitchen equipment not updated correctly")
        
        print(f"✅ Successfully updated kitchen equipment with {len(equipment_ids)} items")
        return subscription
    
    def test_08_equipment_aware_generation(self):
        """Test equipment-aware recipe generation for PRO users"""
        print("\n🔍 Testing equipment-aware recipe generation...")
        
        # First ensure we have a registered user with PRO subscription and equipment
        if not hasattr(self, 'user_id') or not self.user_id:
            self.test_03_register_user()
            self.test_06_upgrade_subscription()  # Upgrade to PRO
            self.test_07_update_kitchen_equipment()  # Set equipment
        
        # Generate a tech card that should consider equipment
        data = {
            "dish_name": "Ризотто с белыми грибами",
            "user_id": self.user_id
        }
        
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
        self.assertEqual(response.status_code, 200, "Failed to generate equipment-aware tech card")
        
        result = response.json()
        self.assertTrue(result["success"], "Tech card generation not marked as successful")
        self.assertIsNotNone(result["tech_card"], "Tech card content not returned")
        
        # Check if the tech card mentions equipment
        tech_card_content = result["tech_card"].lower()
        equipment_mentioned = False
        
        # Check for equipment-related terms in the content
        equipment_terms = ["оборудование", "плита", "печь", "блендер", "комбайн", "холодильник"]
        for term in equipment_terms:
            if term in tech_card_content:
                equipment_mentioned = True
                break
        
        self.assertTrue(equipment_mentioned, "Tech card doesn't seem to mention equipment")
        
        print("✅ Successfully tested equipment-aware recipe generation")
        return result
    
    def test_09_non_pro_equipment_restriction(self):
        """Test that non-PRO users cannot update kitchen equipment"""
        print("\n🔍 Testing kitchen equipment restriction for non-PRO users...")
        
        # Create a new user with free plan
        free_email = f"free_user_{self.random_string(6)}@example.com"
        free_name = f"Free User {self.random_string(4)}"
        
        data = {
            "email": free_email,
            "name": free_name,
            "city": "moskva"
        }
        
        response = requests.post(f"{self.base_url}/register", json=data)
        self.assertEqual(response.status_code, 200, "Failed to register free tier user")
        free_user = response.json()
        free_user_id = free_user["id"]
        
        # Get available equipment
        equipment = self.test_02_get_kitchen_equipment()
        
        # Select a few equipment items
        equipment_ids = [
            equipment["cooking_methods"][0]["id"],
            equipment["prep_equipment"][0]["id"]
        ]
        
        data = {
            "equipment_ids": equipment_ids
        }
        
        # Try to update equipment (should fail for free tier)
        response = requests.post(f"{self.base_url}/update-kitchen-equipment/{free_user_id}", json=data)
        self.assertEqual(response.status_code, 403, "Free tier user should not be able to update kitchen equipment")
        
        print("✅ Successfully verified kitchen equipment restriction for non-PRO users")
        return response.json()

def run_tests():
    """Run all tests in order"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(SubscriptionAPITest('test_01_get_subscription_plans'))
    test_suite.addTest(SubscriptionAPITest('test_02_get_kitchen_equipment'))
    test_suite.addTest(SubscriptionAPITest('test_03_register_user'))
    test_suite.addTest(SubscriptionAPITest('test_04_get_user_subscription'))
    test_suite.addTest(SubscriptionAPITest('test_05_free_tier_usage_limits'))
    test_suite.addTest(SubscriptionAPITest('test_06_upgrade_subscription'))
    test_suite.addTest(SubscriptionAPITest('test_07_update_kitchen_equipment'))
    test_suite.addTest(SubscriptionAPITest('test_08_equipment_aware_generation'))
    test_suite.addTest(SubscriptionAPITest('test_09_non_pro_equipment_restriction'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🚀 Starting RECEPTOR Subscription API Tests")
    print(f"🔗 Testing against: https://cursor-push.preview.emergentagent.com/api")
    print("=" * 70)
    
    success = run_tests()
    
    print("=" * 70)
    if success:
        print("✅ All subscription API tests passed successfully!")
        exit(0)
    else:
        print("❌ Some subscription API tests failed!")
        exit(1)