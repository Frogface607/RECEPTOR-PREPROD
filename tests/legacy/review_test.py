#!/usr/bin/env python3
"""
Focused backend testing for Receptor Pro review requirements
"""
import requests
import json
import time
import random
import string

class ReceptorReviewTest:
    def __init__(self):
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.test_user_id = "test_user_123"
        self.test_email = f"test_{self.random_string(6)}@example.com"
        self.test_name = "Test User Review"
        self.test_city = "moskva"
        
    def random_string(self, length=6):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def log(self, message):
        print(f"🔍 {message}")
    
    def success(self, message):
        print(f"✅ {message}")
    
    def error(self, message):
        print(f"❌ {message}")
    
    def warning(self, message):
        print(f"⚠️ {message}")

    def test_user_registration(self):
        """Test user registration endpoint"""
        self.log("Testing user registration...")
        
        data = {
            "email": self.test_email,
            "name": self.test_name,
            "city": self.test_city
        }
        
        try:
            response = requests.post(f"{self.base_url}/register", json=data, timeout=30)
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data["id"]
                self.success(f"User registration successful. User ID: {self.test_user_id}")
                return True
            else:
                self.error(f"Registration failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Registration request failed: {str(e)}")
            return False

    def test_tech_card_generation(self):
        """Test tech card generation with specific dish"""
        self.log("Testing tech card generation for 'Паста Карбонара'...")
        
        data = {
            "dish_name": "Паста Карбонара",
            "user_id": self.test_user_id
        }
        
        try:
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("tech_card"):
                    tech_card = result["tech_card"]
                    self.success("Tech card generation successful")
                    
                    # Test ingredient parsing
                    self.test_ingredient_parsing(tech_card)
                    
                    return True, result["id"], tech_card
                else:
                    self.error("Tech card generation returned success=false or no content")
                    return False, None, None
            else:
                self.error(f"Tech card generation failed with status {response.status_code}: {response.text}")
                return False, None, None
                
        except Exception as e:
            self.error(f"Tech card generation request failed: {str(e)}")
            return False, None, None

    def test_ingredient_parsing(self, tech_card_content):
        """Test ingredient parsing from tech card content"""
        self.log("Testing ingredient parsing...")
        
        # Look for ingredients in the expected format
        lines = tech_card_content.split('\n')
        ingredients_found = []
        in_ingredients_section = False
        
        for line in lines:
            if '**Ингредиенты:**' in line or 'Ингредиенты:' in line:
                in_ingredients_section = True
                continue
            elif line.startswith('**') and in_ingredients_section:
                break
            elif in_ingredients_section and line.strip() and line.startswith('- '):
                # Check if ingredient follows format "- Название — количество единица — ~цена ₽"
                if '—' in line and '₽' in line:
                    ingredients_found.append(line.strip())
        
        if ingredients_found:
            self.success(f"Found {len(ingredients_found)} properly formatted ingredients:")
            for ingredient in ingredients_found[:3]:  # Show first 3
                print(f"   {ingredient}")
            if len(ingredients_found) > 3:
                print(f"   ... and {len(ingredients_found) - 3} more")
            return True
        else:
            self.error("No properly formatted ingredients found in tech card")
            return False

    def test_subscription_endpoints(self):
        """Test subscription-related endpoints"""
        self.log("Testing subscription endpoints...")
        
        # Test get subscription plans
        try:
            response = requests.get(f"{self.base_url}/subscription-plans", timeout=30)
            if response.status_code == 200:
                plans = response.json()
                if all(tier in plans for tier in ["free", "starter", "pro", "business"]):
                    self.success("Subscription plans endpoint working correctly")
                else:
                    self.error("Missing subscription tiers in plans response")
                    return False
            else:
                self.error(f"Subscription plans failed with status {response.status_code}")
                return False
        except Exception as e:
            self.error(f"Subscription plans request failed: {str(e)}")
            return False
        
        # Test get user subscription
        try:
            response = requests.get(f"{self.base_url}/user-subscription/{self.test_user_id}", timeout=30)
            if response.status_code == 200:
                subscription = response.json()
                if "subscription_plan" in subscription and "plan_info" in subscription:
                    self.success(f"User subscription endpoint working. Plan: {subscription['subscription_plan']}")
                else:
                    self.error("Missing required fields in subscription response")
                    return False
            else:
                self.error(f"User subscription failed with status {response.status_code}")
                return False
        except Exception as e:
            self.error(f"User subscription request failed: {str(e)}")
            return False
        
        # Test upgrade subscription to PRO
        try:
            data = {"subscription_plan": "pro"}
            response = requests.post(f"{self.base_url}/upgrade-subscription/{self.test_user_id}", json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.success("Subscription upgrade to PRO successful")
                    return True
                else:
                    self.error("Subscription upgrade returned success=false")
                    return False
            else:
                self.error(f"Subscription upgrade failed with status {response.status_code}")
                return False
        except Exception as e:
            self.error(f"Subscription upgrade request failed: {str(e)}")
            return False

    def test_kitchen_equipment(self):
        """Test kitchen equipment endpoints"""
        self.log("Testing kitchen equipment endpoints...")
        
        # Test get kitchen equipment
        try:
            response = requests.get(f"{self.base_url}/kitchen-equipment", timeout=30)
            if response.status_code == 200:
                equipment = response.json()
                if all(category in equipment for category in ["cooking_methods", "prep_equipment", "storage"]):
                    total_items = sum(len(equipment[cat]) for cat in equipment)
                    self.success(f"Kitchen equipment endpoint working. Total items: {total_items}")
                else:
                    self.error("Missing equipment categories in response")
                    return False
            else:
                self.error(f"Kitchen equipment failed with status {response.status_code}")
                return False
        except Exception as e:
            self.error(f"Kitchen equipment request failed: {str(e)}")
            return False
        
        # Test update kitchen equipment (should work for PRO user)
        try:
            # Get some equipment IDs
            response = requests.get(f"{self.base_url}/kitchen-equipment", timeout=30)
            equipment = response.json()
            
            equipment_ids = [
                equipment["cooking_methods"][0]["id"],
                equipment["prep_equipment"][0]["id"],
                equipment["storage"][0]["id"]
            ]
            
            data = {"equipment_ids": equipment_ids}
            response = requests.post(f"{self.base_url}/update-kitchen-equipment/{self.test_user_id}", json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.success(f"Kitchen equipment update successful for PRO user")
                    return True
                else:
                    self.error("Kitchen equipment update returned success=false")
                    return False
            else:
                self.error(f"Kitchen equipment update failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.error(f"Kitchen equipment update request failed: {str(e)}")
            return False

    def test_history_endpoint(self):
        """Test user history endpoint"""
        self.log("Testing user history endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/user-history/{self.test_user_id}", timeout=30)
            if response.status_code == 200:
                history = response.json()
                if "history" in history:
                    history_count = len(history["history"])
                    self.success(f"User history endpoint working. Found {history_count} tech cards")
                    return True
                else:
                    self.error("Missing 'history' field in response")
                    return False
            else:
                self.error(f"User history failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.error(f"User history request failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all review tests"""
        print("🚀 Starting Receptor Pro Backend Review Tests")
        print("=" * 60)
        
        results = {}
        
        # Test 1: User Registration
        results["registration"] = self.test_user_registration()
        
        # Test 2: Tech Card Generation and Ingredient Parsing
        if results["registration"]:
            success, tech_card_id, tech_card = self.test_tech_card_generation()
            results["tech_card_generation"] = success
        else:
            results["tech_card_generation"] = False
        
        # Test 3: Subscription Endpoints
        if results["registration"]:
            results["subscription"] = self.test_subscription_endpoints()
        else:
            results["subscription"] = False
        
        # Test 4: Kitchen Equipment (PRO feature)
        if results["subscription"]:
            results["kitchen_equipment"] = self.test_kitchen_equipment()
        else:
            results["kitchen_equipment"] = False
        
        # Test 5: History Endpoint
        if results["registration"]:
            results["history"] = self.test_history_endpoint()
        else:
            results["history"] = False
        
        print("=" * 60)
        print("📊 TEST RESULTS SUMMARY:")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        print("=" * 60)
        print(f"Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print("⚠️ Some tests failed. Check details above.")
            return False

if __name__ == "__main__":
    tester = ReceptorReviewTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)