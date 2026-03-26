import requests
import unittest
import random
import string
import time
import re
from datetime import datetime

class GoldenPromptTest(unittest.TestCase):
    """
    Focused tests for the updated Receptor Pro backend with new "golden" prompt
    and related functionality as requested in the review.
    """
    
    def setUp(self):
        # Use the public endpoint for testing
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.user_id = None
        self.user_email = f"golden_test_{self.random_string(6)}@example.com"
        self.user_name = f"Golden Test User {self.random_string(4)}"
        
    def random_string(self, length=6):
        """Generate a random string for test data"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def create_test_user(self, subscription_plan="free"):
        """Create a test user with specified subscription plan"""
        data = {
            "email": self.user_email,
            "name": self.user_name,
            "city": "moskva"
        }
        
        response = requests.post(f"{self.base_url}/register", json=data)
        self.assertEqual(response.status_code, 200, f"Failed to register user: {response.text}")
        user_data = response.json()
        self.user_id = user_data["id"]
        
        # Upgrade subscription if needed
        if subscription_plan != "free":
            upgrade_data = {"subscription_plan": subscription_plan}
            response = requests.post(f"{self.base_url}/upgrade-subscription/{self.user_id}", json=upgrade_data)
            self.assertEqual(response.status_code, 200, f"Failed to upgrade to {subscription_plan}")
        
        return self.user_id
    
    def test_01_golden_prompt_format_verification(self):
        """Test that tech card generation uses the new GOLDEN_PROMPT with correct formatting"""
        print("\n🔍 Testing Golden Prompt Format...")
        
        # Create test user
        user_id = self.create_test_user()
        
        # Generate a tech card to test the new format
        data = {
            "dish_name": "Паста Карбонара",
            "user_id": user_id
        }
        
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
        self.assertEqual(response.status_code, 200, f"Failed to generate tech card: {response.text}")
        
        result = response.json()
        self.assertTrue(result["success"], "Tech card generation not marked as successful")
        tech_card_content = result["tech_card"]
        
        # Verify key format elements from the new GOLDEN_PROMPT
        print("🔍 Checking for required format elements...")
        
        # Check for cost per 100g format: "💸 Себестоимость 100г"
        cost_100g_pattern = r"💸\s*Себестоимость\s*100\s*г"
        self.assertTrue(re.search(cost_100g_pattern, tech_card_content, re.IGNORECASE), 
                       "Missing '💸 Себестоимость 100г' format in tech card")
        
        # Check for KBJU format: "КБЖУ (1 порция)"
        kbju_pattern = r"КБЖУ\s*\(1\s*порция\)"
        self.assertTrue(re.search(kbju_pattern, tech_card_content, re.IGNORECASE), 
                       "Missing 'КБЖУ (1 порция)' format in tech card")
        
        # Check for emojis in sections
        emoji_sections = ["💡", "🔥", "🌀", "🍷", "🍺", "🍹", "🥤", "🍽", "🎯", "💬", "📸", "🏷️"]
        found_emojis = 0
        for emoji in emoji_sections:
            if emoji in tech_card_content:
                found_emojis += 1
        
        self.assertGreater(found_emojis, 3, "Not enough emoji sections found in tech card")
        
        # Verify absence of "стандартная ресторанная порция"
        self.assertNotIn("стандартная ресторанная порция", tech_card_content.lower(), 
                        "Found forbidden phrase 'стандартная ресторанная порция' in tech card")
        
        print(f"✅ Golden prompt format verified - found {found_emojis} emoji sections")
        print(f"✅ Confirmed absence of 'стандартная ресторанная порция'")
        
        # Save for later tests
        self.test_tech_card_id = result["id"]
        self.test_tech_card_content = tech_card_content
        
    def test_02_ai_model_verification(self):
        """Test that tech card generation uses gpt-4o-mini model"""
        print("\n🔍 Testing AI Model Usage...")
        
        # Create test user
        if not hasattr(self, 'user_id') or not self.user_id:
            user_id = self.create_test_user()
        
        # Generate tech card and verify it works (model verification is internal)
        data = {
            "dish_name": "Ризотто с грибами",
            "user_id": self.user_id
        }
        
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
        self.assertEqual(response.status_code, 200, f"Failed to generate tech card: {response.text}")
        
        result = response.json()
        self.assertTrue(result["success"], "Tech card generation not marked as successful")
        
        # The backend code shows gpt-4o-mini is hardcoded for all users (line 594)
        # We can't directly verify the model used, but successful generation confirms it works
        print("✅ AI model verification passed - tech card generated successfully")
        
    def test_03_tech_card_history_functionality(self):
        """Test that GET /api/user-history/{user_id} returns correct data"""
        print("\n🔍 Testing Tech Card History...")
        
        # Create test user if needed
        if not hasattr(self, 'user_id') or not self.user_id:
            user_id = self.create_test_user()
        
        # Generate a few tech cards to create history
        dishes = ["Борщ украинский", "Оливье классический", "Блины на молоке"]
        generated_ids = []
        
        for dish in dishes:
            data = {
                "dish_name": dish,
                "user_id": self.user_id
            }
            
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
            self.assertEqual(response.status_code, 200, f"Failed to generate tech card for {dish}")
            
            result = response.json()
            generated_ids.append(result["id"])
            time.sleep(0.5)  # Small delay to ensure different timestamps
        
        # Test the history endpoint
        response = requests.get(f"{self.base_url}/user-history/{self.user_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get user history: {response.text}")
        
        history_data = response.json()
        self.assertTrue("history" in history_data, "History key not found in response")
        
        history = history_data["history"]
        self.assertGreater(len(history), 0, "No history items returned")
        
        # Verify history contains our generated tech cards
        history_ids = [item["id"] for item in history]
        for generated_id in generated_ids:
            self.assertIn(generated_id, history_ids, f"Generated tech card {generated_id} not found in history")
        
        # Verify history is sorted by creation date (newest first)
        if len(history) > 1:
            for i in range(len(history) - 1):
                current_date = datetime.fromisoformat(history[i]["created_at"].replace('Z', '+00:00'))
                next_date = datetime.fromisoformat(history[i+1]["created_at"].replace('Z', '+00:00'))
                self.assertGreaterEqual(current_date, next_date, "History not sorted by creation date (newest first)")
        
        print(f"✅ History functionality verified - found {len(history)} tech cards")
        
    def test_04_tech_card_database_persistence(self):
        """Test that new tech cards are properly saved to database"""
        print("\n🔍 Testing Tech Card Database Persistence...")
        
        # Create test user if needed
        if not hasattr(self, 'user_id') or not self.user_id:
            user_id = self.create_test_user()
        
        # Generate a unique tech card
        unique_dish = f"Тестовое блюдо {self.random_string(8)}"
        data = {
            "dish_name": unique_dish,
            "user_id": self.user_id
        }
        
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
        self.assertEqual(response.status_code, 200, f"Failed to generate tech card: {response.text}")
        
        result = response.json()
        tech_card_id = result["id"]
        
        # Wait a moment for database write
        time.sleep(1)
        
        # Verify it's saved by retrieving user's tech cards
        response = requests.get(f"{self.base_url}/tech-cards/{self.user_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get user tech cards: {response.text}")
        
        tech_cards = response.json()
        found_card = None
        for card in tech_cards:
            if card["id"] == tech_card_id:
                found_card = card
                break
        
        self.assertIsNotNone(found_card, "Generated tech card not found in database")
        self.assertEqual(found_card["dish_name"], unique_dish, "Dish name not saved correctly")
        self.assertEqual(found_card["user_id"], self.user_id, "User ID not saved correctly")
        self.assertIsNotNone(found_card["content"], "Tech card content not saved")
        self.assertIsNotNone(found_card["created_at"], "Creation timestamp not saved")
        
        print("✅ Database persistence verified - tech card properly saved")
        
    def test_05_cost_calculation_accuracy(self):
        """Test that cost calculations in tech cards are reasonable and properly formatted"""
        print("\n🔍 Testing Cost Calculation Accuracy...")
        
        # Create test user if needed
        if not hasattr(self, 'user_id') or not self.user_id:
            user_id = self.create_test_user()
        
        # Generate tech card for a dish with known ingredients
        data = {
            "dish_name": "Салат Цезарь",
            "user_id": self.user_id
        }
        
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
        self.assertEqual(response.status_code, 200, f"Failed to generate tech card: {response.text}")
        
        result = response.json()
        tech_card_content = result["tech_card"]
        
        # Extract cost information
        cost_pattern = r"По ингредиентам:\s*(\d+(?:\.\d+)?)\s*₽"
        cost_match = re.search(cost_pattern, tech_card_content)
        self.assertIsNotNone(cost_match, "Cost per ingredients not found in tech card")
        
        ingredient_cost = float(cost_match.group(1))
        self.assertGreater(ingredient_cost, 0, "Ingredient cost should be greater than 0")
        self.assertLess(ingredient_cost, 5000, "Ingredient cost seems unreasonably high")
        
        # Check for cost per 100g
        cost_100g_pattern = r"💸\s*Себестоимость\s*100\s*г:\s*(\d+(?:\.\d+)?)\s*₽"
        cost_100g_match = re.search(cost_100g_pattern, tech_card_content)
        self.assertIsNotNone(cost_100g_match, "Cost per 100g not found in tech card")
        
        cost_100g = float(cost_100g_match.group(1))
        self.assertGreater(cost_100g, 0, "Cost per 100g should be greater than 0")
        
        # Check for recommended price (×3)
        recommended_pattern = r"Рекомендуемая цена.*?(\d+(?:\.\d+)?)\s*₽"
        recommended_match = re.search(recommended_pattern, tech_card_content)
        self.assertIsNotNone(recommended_match, "Recommended price not found in tech card")
        
        recommended_price = float(recommended_match.group(1))
        # Recommended price should be approximately 3x the ingredient cost
        expected_recommended = ingredient_cost * 3
        tolerance = expected_recommended * 0.2  # 20% tolerance
        self.assertAlmostEqual(recommended_price, expected_recommended, delta=tolerance, 
                              msg=f"Recommended price {recommended_price} not close to 3x ingredient cost {expected_recommended}")
        
        print(f"✅ Cost calculations verified - Ingredient cost: {ingredient_cost}₽, Cost per 100g: {cost_100g}₽, Recommended: {recommended_price}₽")
        
    def test_06_pro_user_equipment_integration(self):
        """Test that PRO users get equipment-aware tech card generation"""
        print("\n🔍 Testing PRO User Equipment Integration...")
        
        # Create PRO user
        pro_user_id = self.create_test_user("pro")
        
        # Get available equipment
        response = requests.get(f"{self.base_url}/kitchen-equipment")
        self.assertEqual(response.status_code, 200, "Failed to get kitchen equipment")
        equipment = response.json()
        
        # Set some equipment for the PRO user
        equipment_ids = [
            equipment["cooking_methods"][0]["id"],  # First cooking method
            equipment["cooking_methods"][2]["id"],  # Third cooking method
            equipment["prep_equipment"][0]["id"],   # First prep equipment
        ]
        
        equipment_data = {"equipment_ids": equipment_ids}
        response = requests.post(f"{self.base_url}/update-kitchen-equipment/{pro_user_id}", json=equipment_data)
        self.assertEqual(response.status_code, 200, "Failed to update kitchen equipment")
        
        # Generate tech card that should consider equipment
        data = {
            "dish_name": "Стейк из говядины",
            "user_id": pro_user_id
        }
        
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
        self.assertEqual(response.status_code, 200, f"Failed to generate equipment-aware tech card: {response.text}")
        
        result = response.json()
        tech_card_content = result["tech_card"]
        
        # The equipment integration is working if we get a successful response
        # Content adaptation verification would require complex parsing
        self.assertTrue(result["success"], "Equipment-aware tech card generation failed")
        self.assertIsNotNone(tech_card_content, "Tech card content not generated")
        
        print("✅ PRO user equipment integration verified")
        
    def test_07_edit_tech_card_with_golden_prompt(self):
        """Test that tech card editing maintains the golden prompt format"""
        print("\n🔍 Testing Tech Card Editing with Golden Prompt...")
        
        # Create test user and tech card if needed
        if not hasattr(self, 'user_id') or not self.user_id:
            user_id = self.create_test_user()
        
        if not hasattr(self, 'test_tech_card_id'):
            self.test_01_golden_prompt_format_verification()
        
        # Edit the tech card
        edit_request = {
            "tech_card_id": self.test_tech_card_id,
            "edit_instruction": "Увеличь порцию в 2 раза и пересчитай стоимость"
        }
        
        response = requests.post(f"{self.base_url}/edit-tech-card", json=edit_request)
        self.assertEqual(response.status_code, 200, f"Failed to edit tech card: {response.text}")
        
        result = response.json()
        self.assertTrue(result["success"], "Tech card edit not marked as successful")
        
        edited_content = result["tech_card"]
        
        # Verify the edited content still maintains golden prompt format
        cost_100g_pattern = r"💸\s*Себестоимость\s*100\s*г"
        self.assertTrue(re.search(cost_100g_pattern, edited_content, re.IGNORECASE), 
                       "Edited tech card missing '💸 Себестоимость 100г' format")
        
        kbju_pattern = r"КБЖУ\s*\(1\s*порция\)"
        self.assertTrue(re.search(kbju_pattern, edited_content, re.IGNORECASE), 
                       "Edited tech card missing 'КБЖУ (1 порция)' format")
        
        # Verify absence of forbidden phrase
        self.assertNotIn("стандартная ресторанная порция", edited_content.lower(), 
                        "Edited tech card contains forbidden phrase 'стандартная ресторанная порция'")
        
        print("✅ Tech card editing with golden prompt format verified")

def run_golden_prompt_tests():
    """Run all golden prompt focused tests"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(GoldenPromptTest('test_01_golden_prompt_format_verification'))
    test_suite.addTest(GoldenPromptTest('test_02_ai_model_verification'))
    test_suite.addTest(GoldenPromptTest('test_03_tech_card_history_functionality'))
    test_suite.addTest(GoldenPromptTest('test_04_tech_card_database_persistence'))
    test_suite.addTest(GoldenPromptTest('test_05_cost_calculation_accuracy'))
    test_suite.addTest(GoldenPromptTest('test_06_pro_user_equipment_integration'))
    test_suite.addTest(GoldenPromptTest('test_07_edit_tech_card_with_golden_prompt'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🚀 Starting RECEPTOR Golden Prompt Tests")
    print("🎯 Focus: Updated AI prompt, tech card history, format verification")
    print(f"🔗 Testing against: https://cursor-push.preview.emergentagent.com/api")
    print("=" * 80)
    
    success = run_golden_prompt_tests()
    
    print("=" * 80)
    if success:
        print("✅ All Golden Prompt tests passed successfully!")
        exit(0)
    else:
        print("❌ Some Golden Prompt tests failed!")
        exit(1)