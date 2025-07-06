import requests
import unittest
import random
import string
import time
from datetime import datetime

class ReceptorAPITest(unittest.TestCase):
    def setUp(self):
        # Use the public endpoint for testing
        self.base_url = "https://70e992be-5c2a-46e3-970f-73b083abbf21.preview.emergentagent.com/api"
        self.user_id = None
        self.user_email = f"test_user_{self.random_string(6)}@example.com"
        self.user_name = f"Test User {self.random_string(4)}"
        
    def random_string(self, length=6):
        """Generate a random string for test data"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def test_01_get_cities(self):
        """Test getting the list of cities"""
        print("\n🔍 Testing GET /cities...")
        response = requests.get(f"{self.base_url}/cities")
        
        self.assertEqual(response.status_code, 200, "Failed to get cities list")
        cities = response.json()
        self.assertTrue(len(cities) > 0, "Cities list is empty")
        self.assertTrue(any(city["code"] == "moskva" for city in cities), "Moscow not found in cities list")
        print("✅ Successfully retrieved cities list")
        
    def test_02_register_user(self):
        """Test user registration"""
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
        
        # Save user ID for later tests
        self.user_id = user_data["id"]
        print(f"✅ Successfully registered user with ID: {self.user_id}")
        
    def test_03_get_user(self):
        """Test getting user by email"""
        print("\n🔍 Testing GET /user/{email}...")
        
        # First ensure we have a registered user
        if not hasattr(self, 'user_id') or not self.user_id:
            self.test_02_register_user()
            
        response = requests.get(f"{self.base_url}/user/{self.user_email}")
        
        self.assertEqual(response.status_code, 200, f"Failed to get user: {response.text}")
        user_data = response.json()
        self.assertEqual(user_data["email"], self.user_email)
        self.assertEqual(user_data["name"], self.user_name)
        print("✅ Successfully retrieved user by email")
        
    def test_04_generate_tech_card(self):
        """Test generating a tech card"""
        print("\n🔍 Testing POST /generate-tech-card...")
        
        # First ensure we have a registered user
        if not hasattr(self, 'user_id') or not self.user_id:
            self.test_02_register_user()
            
        data = {
            "dish_name": "Борщ классический",
            "user_id": self.user_id
        }
        
        print(f"Generating tech card for dish: {data['dish_name']}")
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
        
        self.assertEqual(response.status_code, 200, f"Failed to generate tech card: {response.text}")
        result = response.json()
        self.assertTrue(result["success"], "Tech card generation not marked as successful")
        self.assertIsNotNone(result["tech_card"], "Tech card content not returned")
        self.assertIsNotNone(result["id"], "Tech card ID not returned")
        
        # Save tech card ID for later tests
        self.tech_card_id = result["id"]
        print(f"✅ Successfully generated tech card with ID: {self.tech_card_id}")
        print(f"Tech card preview: {result['tech_card'][:100]}...")
        
    def test_05_get_user_tech_cards(self):
        """Test getting user's tech cards"""
        print("\n🔍 Testing GET /tech-cards/{user_id}...")
        
        # First ensure we have a registered user with a tech card
        if not hasattr(self, 'user_id') or not self.user_id:
            self.test_02_register_user()
        if not hasattr(self, 'tech_card_id'):
            self.test_04_generate_tech_card()
            
        # Wait a moment to ensure the tech card is saved
        time.sleep(1)
            
        response = requests.get(f"{self.base_url}/tech-cards/{self.user_id}")
        
        self.assertEqual(response.status_code, 200, f"Failed to get user tech cards: {response.text}")
        tech_cards = response.json()
        self.assertTrue(len(tech_cards) > 0, "No tech cards returned for user")
        
        # Verify the tech card we created is in the list
        found = False
        for card in tech_cards:
            if hasattr(self, 'tech_card_id') and card["id"] == self.tech_card_id:
                found = True
                break
                
        self.assertTrue(found, "Created tech card not found in user's tech cards")
        print(f"✅ Successfully retrieved {len(tech_cards)} tech cards for user")

def run_tests():
    """Run all tests in order"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(ReceptorAPITest('test_01_get_cities'))
    test_suite.addTest(ReceptorAPITest('test_02_register_user'))
    test_suite.addTest(ReceptorAPITest('test_03_get_user'))
    test_suite.addTest(ReceptorAPITest('test_04_generate_tech_card'))
    test_suite.addTest(ReceptorAPITest('test_05_get_user_tech_cards'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🚀 Starting RECEPTOR API Tests")
    print(f"🔗 Testing against: https://70e992be-5c2a-46e3-970f-73b083abbf21.preview.emergentagent.com/api")
    print("=" * 70)
    
    success = run_tests()
    
    print("=" * 70)
    if success:
        print("✅ All API tests passed successfully!")
        exit(0)
    else:
        print("❌ Some API tests failed!")
        exit(1)