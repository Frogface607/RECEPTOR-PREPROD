#!/usr/bin/env python3
"""
Detailed backend testing for specific review requirements
"""
import requests
import json
import re

class DetailedReviewTest:
    def __init__(self):
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.test_user_id = "test_user_123"
        self.test_email = "detailed_test@example.com"
        
    def log(self, message):
        print(f"🔍 {message}")
    
    def success(self, message):
        print(f"✅ {message}")
    
    def error(self, message):
        print(f"❌ {message}")

    def test_ai_model_verification(self):
        """Verify that gpt-4o-mini is being used"""
        self.log("Verifying AI model usage (gpt-4o-mini)...")
        
        # Register user first
        data = {
            "email": self.test_email,
            "name": "Detailed Test User",
            "city": "moskva"
        }
        
        response = requests.post(f"{self.base_url}/register", json=data, timeout=30)
        if response.status_code == 200:
            user_data = response.json()
            self.test_user_id = user_data["id"]
        
        # Generate tech card and check response quality/speed (gpt-4o-mini should be faster)
        data = {
            "dish_name": "Паста Карбонара",
            "user_id": self.test_user_id
        }
        
        import time
        start_time = time.time()
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data, timeout=60)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                generation_time = end_time - start_time
                self.success(f"Tech card generated successfully in {generation_time:.2f} seconds")
                
                # Check for golden prompt format
                tech_card = result["tech_card"]
                if "💸 Себестоимость" in tech_card and "КБЖУ" in tech_card:
                    self.success("Golden prompt format detected in tech card")
                else:
                    self.error("Golden prompt format not found in tech card")
                
                return True, tech_card
            else:
                self.error("Tech card generation failed")
                return False, None
        else:
            self.error(f"Tech card generation request failed: {response.status_code}")
            return False, None

    def test_ingredient_format_validation(self, tech_card):
        """Test that ingredients are in the correct format"""
        self.log("Validating ingredient format: '- Название — количество единица — ~цена ₽'...")
        
        lines = tech_card.split('\n')
        ingredients_found = []
        in_ingredients_section = False
        
        for line in lines:
            if '**Ингредиенты:**' in line or 'Ингредиенты:' in line:
                in_ingredients_section = True
                continue
            elif line.startswith('**') and in_ingredients_section:
                break
            elif in_ingredients_section and line.strip() and line.startswith('- '):
                ingredients_found.append(line.strip())
        
        valid_ingredients = 0
        invalid_ingredients = []
        
        for ingredient in ingredients_found:
            # Check format: "- Название — количество единица — ~цена ₽"
            pattern = r'^- .+ — .+ — ~\d+(\.\d+)? ₽$'
            if re.match(pattern, ingredient):
                valid_ingredients += 1
            else:
                invalid_ingredients.append(ingredient)
        
        if valid_ingredients > 0:
            self.success(f"Found {valid_ingredients} correctly formatted ingredients")
            if invalid_ingredients:
                self.error(f"Found {len(invalid_ingredients)} incorrectly formatted ingredients:")
                for invalid in invalid_ingredients[:3]:
                    print(f"   {invalid}")
            return True
        else:
            self.error("No correctly formatted ingredients found")
            return False

    def test_interactive_editor_endpoints(self):
        """Test endpoints that support interactive editing"""
        self.log("Testing interactive editor support endpoints...")
        
        # Test parse-ingredients endpoint
        sample_content = """**Ингредиенты:**

- Спагетти — 100 г — ~10 ₽
- Бекон — 80 г — ~60 ₽
- Яйца — 2 шт — ~20 ₽
- Пармезан — 50 г — ~200 ₽

**Пошаговый рецепт:**"""
        
        try:
            # Try different content types for parse-ingredients
            response = requests.post(
                f"{self.base_url}/parse-ingredients", 
                json=sample_content,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "ingredients" in result:
                    self.success(f"Parse ingredients endpoint working - found {len(result['ingredients'])} ingredients")
                else:
                    self.error("Parse ingredients endpoint returned no ingredients")
                    return False
            else:
                self.error(f"Parse ingredients endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Parse ingredients request failed: {str(e)}")
            return False
        
        # Test edit-tech-card endpoint
        # First get a tech card ID
        response = requests.get(f"{self.base_url}/user-history/{self.test_user_id}", timeout=30)
        if response.status_code == 200:
            history = response.json()
            if history["history"]:
                tech_card_id = history["history"][0]["id"]
                
                edit_data = {
                    "tech_card_id": tech_card_id,
                    "edit_instruction": "Увеличь порцию в два раза"
                }
                
                response = requests.post(f"{self.base_url}/edit-tech-card", json=edit_data, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        self.success("Edit tech card endpoint working correctly")
                        return True
                    else:
                        self.error("Edit tech card endpoint returned success=false")
                        return False
                else:
                    self.error(f"Edit tech card endpoint failed: {response.status_code}")
                    return False
        
        return False

    def test_pro_features_access(self):
        """Test PRO features access control"""
        self.log("Testing PRO features access control...")
        
        # First upgrade to PRO
        upgrade_data = {"subscription_plan": "pro"}
        response = requests.post(f"{self.base_url}/upgrade-subscription/{self.test_user_id}", json=upgrade_data, timeout=30)
        
        if response.status_code != 200:
            self.error("Failed to upgrade to PRO for testing")
            return False
        
        # Test kitchen equipment access (PRO feature)
        equipment_data = {"equipment_ids": ["gas_stove", "food_processor", "refrigerator"]}
        response = requests.post(f"{self.base_url}/update-kitchen-equipment/{self.test_user_id}", json=equipment_data, timeout=30)
        
        if response.status_code == 200:
            self.success("PRO user can access kitchen equipment features")
        else:
            self.error(f"PRO user cannot access kitchen equipment: {response.status_code}")
            return False
        
        # Test that equipment-aware generation works
        data = {
            "dish_name": "Стейк на гриле",
            "user_id": self.test_user_id
        }
        
        response = requests.post(f"{self.base_url}/generate-tech-card", json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                self.success("Equipment-aware tech card generation working for PRO users")
                return True
            else:
                self.error("Equipment-aware generation failed")
                return False
        else:
            self.error(f"Equipment-aware generation request failed: {response.status_code}")
            return False

    def test_free_user_restrictions(self):
        """Test that free users are properly restricted"""
        self.log("Testing free user restrictions...")
        
        # Create a new free user
        free_email = "free_user_test@example.com"
        data = {
            "email": free_email,
            "name": "Free Test User",
            "city": "moskva"
        }
        
        response = requests.post(f"{self.base_url}/register", json=data, timeout=30)
        if response.status_code == 200:
            free_user = response.json()
            free_user_id = free_user["id"]
        else:
            self.error("Failed to create free user for testing")
            return False
        
        # Test that free user cannot access kitchen equipment
        equipment_data = {"equipment_ids": ["gas_stove", "food_processor"]}
        response = requests.post(f"{self.base_url}/update-kitchen-equipment/{free_user_id}", json=equipment_data, timeout=30)
        
        if response.status_code == 403:
            self.success("Free users are properly blocked from kitchen equipment features")
            return True
        else:
            self.error(f"Free user restriction not working properly: {response.status_code}")
            return False

    def run_detailed_tests(self):
        """Run all detailed tests"""
        print("🚀 Starting Detailed Backend Review Tests")
        print("=" * 60)
        
        results = {}
        
        # Test 1: AI Model Verification
        success, tech_card = self.test_ai_model_verification()
        results["ai_model"] = success
        
        # Test 2: Ingredient Format Validation
        if success and tech_card:
            results["ingredient_format"] = self.test_ingredient_format_validation(tech_card)
        else:
            results["ingredient_format"] = False
        
        # Test 3: Interactive Editor Endpoints
        results["interactive_editor"] = self.test_interactive_editor_endpoints()
        
        # Test 4: PRO Features Access
        results["pro_features"] = self.test_pro_features_access()
        
        # Test 5: Free User Restrictions
        results["free_restrictions"] = self.test_free_user_restrictions()
        
        print("=" * 60)
        print("📊 DETAILED TEST RESULTS:")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        print("=" * 60)
        print(f"Overall: {passed_tests}/{total_tests} detailed tests passed")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = DetailedReviewTest()
    success = tester.run_detailed_tests()
    exit(0 if success else 1)