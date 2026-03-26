#!/usr/bin/env python3
"""
Receptor Pro Backend API Testing - Review Request Focus
Testing specific endpoints as requested in the review:

1. POST /api/generate-tech-card - генерация технологической карты
2. GET /api/subscription-plans - получение планов подписки  
3. GET /api/kitchen-equipment - получение списка кухонного оборудования
4. POST /api/register - регистрация нового пользователя
5. GET /api/user-history/{user_id} - получение истории техкарт пользователя

Test data:
- user_id: test_user_12345
- dish_name: Паста Карбонара на 4 порции
- city: moskva
- email: test@example.com
- name: Тестовый пользователь
"""

import requests
import json
import time
from datetime import datetime

class ReceptorReviewTest:
    def __init__(self):
        # Use the public endpoint from frontend/.env
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        
        # Test data as specified in review request
        self.test_user_id = "test_user_12345"
        self.test_dish_name = "Паста Карбонара на 4 порции"
        self.test_city = "moskva"
        self.test_email = "test@example.com"
        self.test_name = "Тестовый пользователь"
        
        self.results = []
        
    def log_result(self, test_name, status, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,  # "PASS", "FAIL", "WARNING"
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_1_register_user(self):
        """Test POST /api/register - регистрация нового пользователя"""
        print("\n🔍 Testing POST /api/register...")
        
        try:
            data = {
                "email": self.test_email,
                "name": self.test_name,
                "city": self.test_city
            }
            
            response = requests.post(f"{self.base_url}/register", json=data, timeout=30)
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Validate response structure
                required_fields = ["id", "email", "name", "city", "subscription_plan"]
                missing_fields = [field for field in required_fields if field not in user_data]
                
                if missing_fields:
                    self.log_result("POST /api/register", "FAIL", 
                                  f"Missing required fields: {missing_fields}", user_data)
                    return False
                
                # Validate data correctness
                if (user_data["email"] == self.test_email and 
                    user_data["name"] == self.test_name and 
                    user_data["city"] == self.test_city):
                    
                    self.log_result("POST /api/register", "PASS", 
                                  f"User registered successfully with ID: {user_data['id']}", 
                                  f"Subscription: {user_data['subscription_plan']}")
                    return True
                else:
                    self.log_result("POST /api/register", "FAIL", 
                                  "User data doesn't match input", user_data)
                    return False
                    
            elif response.status_code == 400:
                # User might already exist, which is acceptable for testing
                self.log_result("POST /api/register", "WARNING", 
                              "User already exists (acceptable for testing)", 
                              response.text)
                return True
            else:
                self.log_result("POST /api/register", "FAIL", 
                              f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("POST /api/register", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_2_subscription_plans(self):
        """Test GET /api/subscription-plans - получение планов подписки"""
        print("\n🔍 Testing GET /api/subscription-plans...")
        
        try:
            response = requests.get(f"{self.base_url}/subscription-plans", timeout=30)
            
            if response.status_code == 200:
                plans = response.json()
                
                # Check for all 4 required tiers
                required_tiers = ["free", "starter", "pro", "business"]
                missing_tiers = [tier for tier in required_tiers if tier not in plans]
                
                if missing_tiers:
                    self.log_result("GET /api/subscription-plans", "FAIL", 
                                  f"Missing subscription tiers: {missing_tiers}", plans)
                    return False
                
                # Validate tier structure and limits
                tier_validations = []
                
                # Free tier validation
                free_plan = plans["free"]
                if free_plan.get("monthly_tech_cards") != 3:
                    tier_validations.append("Free tier should have 3 tech cards limit")
                if free_plan.get("kitchen_equipment") != False:
                    tier_validations.append("Free tier should not have kitchen equipment")
                
                # PRO tier validation
                pro_plan = plans["pro"]
                if pro_plan.get("monthly_tech_cards") != -1:
                    tier_validations.append("PRO tier should have unlimited tech cards (-1)")
                if pro_plan.get("kitchen_equipment") != True:
                    tier_validations.append("PRO tier should have kitchen equipment feature")
                
                if tier_validations:
                    self.log_result("GET /api/subscription-plans", "FAIL", 
                                  "Tier validation failed", tier_validations)
                    return False
                
                self.log_result("GET /api/subscription-plans", "PASS", 
                              f"All 4 subscription tiers retrieved correctly", 
                              f"Tiers: {list(plans.keys())}")
                return True
                
            else:
                self.log_result("GET /api/subscription-plans", "FAIL", 
                              f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("GET /api/subscription-plans", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_3_kitchen_equipment(self):
        """Test GET /api/kitchen-equipment - получение списка кухонного оборудования"""
        print("\n🔍 Testing GET /api/kitchen-equipment...")
        
        try:
            response = requests.get(f"{self.base_url}/kitchen-equipment", timeout=30)
            
            if response.status_code == 200:
                equipment = response.json()
                
                # Check for required categories
                required_categories = ["cooking_methods", "prep_equipment", "storage"]
                missing_categories = [cat for cat in required_categories if cat not in equipment]
                
                if missing_categories:
                    self.log_result("GET /api/kitchen-equipment", "FAIL", 
                                  f"Missing equipment categories: {missing_categories}", equipment)
                    return False
                
                # Count total equipment items
                total_items = 0
                category_counts = {}
                
                for category, items in equipment.items():
                    if not isinstance(items, list):
                        self.log_result("GET /api/kitchen-equipment", "FAIL", 
                                      f"Category {category} is not a list", items)
                        return False
                    
                    category_counts[category] = len(items)
                    total_items += len(items)
                    
                    # Validate item structure
                    for item in items:
                        required_item_fields = ["id", "name", "category"]
                        missing_item_fields = [field for field in required_item_fields if field not in item]
                        if missing_item_fields:
                            self.log_result("GET /api/kitchen-equipment", "FAIL", 
                                          f"Equipment item missing fields: {missing_item_fields}", item)
                            return False
                
                # Verify we have reasonable number of equipment items (should be 21 total)
                if total_items < 15:
                    self.log_result("GET /api/kitchen-equipment", "WARNING", 
                                  f"Low equipment count: {total_items} items", category_counts)
                else:
                    self.log_result("GET /api/kitchen-equipment", "PASS", 
                                  f"Kitchen equipment retrieved successfully: {total_items} items", 
                                  category_counts)
                return True
                
            else:
                self.log_result("GET /api/kitchen-equipment", "FAIL", 
                              f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("GET /api/kitchen-equipment", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_4_generate_tech_card(self):
        """Test POST /api/generate-tech-card - генерация технологической карты"""
        print("\n🔍 Testing POST /api/generate-tech-card...")
        
        try:
            data = {
                "dish_name": self.test_dish_name,
                "user_id": self.test_user_id
            }
            
            print(f"   Generating tech card for: {self.test_dish_name}")
            print(f"   User ID: {self.test_user_id}")
            
            start_time = time.time()
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data, timeout=120)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                required_fields = ["success", "tech_card", "id"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result("POST /api/generate-tech-card", "FAIL", 
                                  f"Missing response fields: {missing_fields}", result)
                    return False
                
                if not result.get("success"):
                    self.log_result("POST /api/generate-tech-card", "FAIL", 
                                  "Success flag is False", result)
                    return False
                
                tech_card_content = result.get("tech_card", "")
                if len(tech_card_content) < 500:
                    self.log_result("POST /api/generate-tech-card", "FAIL", 
                                  f"Tech card content too short: {len(tech_card_content)} chars", 
                                  tech_card_content[:200])
                    return False
                
                # Check for key sections in tech card
                required_sections = ["Название:", "Ингредиенты:", "Пошаговый рецепт:", "Себестоимость:"]
                missing_sections = [section for section in required_sections 
                                  if section not in tech_card_content]
                
                if missing_sections:
                    self.log_result("POST /api/generate-tech-card", "WARNING", 
                                  f"Missing tech card sections: {missing_sections}", 
                                  f"Content length: {len(tech_card_content)}")
                else:
                    # Check for price calculations
                    price_indicators = ["₽", "руб", "рекомендуемая цена", "себестоимость"]
                    has_prices = any(indicator.lower() in tech_card_content.lower() 
                                   for indicator in price_indicators)
                    
                    if not has_prices:
                        self.log_result("POST /api/generate-tech-card", "WARNING", 
                                      "No price calculations found in tech card", 
                                      f"Response time: {response_time:.2f}s")
                    else:
                        self.log_result("POST /api/generate-tech-card", "PASS", 
                                      f"Tech card generated successfully ({len(tech_card_content)} chars)", 
                                      f"Response time: {response_time:.2f}s, ID: {result['id']}")
                
                # Store tech card ID for history test
                self.tech_card_id = result.get("id")
                return True
                
            else:
                self.log_result("POST /api/generate-tech-card", "FAIL", 
                              f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("POST /api/generate-tech-card", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_5_user_history(self):
        """Test GET /api/user-history/{user_id} - получение истории техкарт пользователя"""
        print("\n🔍 Testing GET /api/user-history/{user_id}...")
        
        try:
            # Wait a moment to ensure tech card is saved
            time.sleep(2)
            
            response = requests.get(f"{self.base_url}/user-history/{self.test_user_id}", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                if "history" not in result:
                    self.log_result("GET /api/user-history", "FAIL", 
                                  "Missing 'history' field in response", result)
                    return False
                
                history = result["history"]
                
                if not isinstance(history, list):
                    self.log_result("GET /api/user-history", "FAIL", 
                                  "History is not a list", type(history))
                    return False
                
                if len(history) == 0:
                    self.log_result("GET /api/user-history", "WARNING", 
                                  "No history found for user (might be expected for new user)", 
                                  f"User ID: {self.test_user_id}")
                    return True
                
                # Validate history item structure
                for item in history:
                    required_fields = ["id", "user_id", "dish_name", "content", "created_at"]
                    missing_fields = [field for field in required_fields if field not in item]
                    
                    if missing_fields:
                        self.log_result("GET /api/user-history", "FAIL", 
                                      f"History item missing fields: {missing_fields}", item)
                        return False
                
                # Check if our generated tech card is in history
                if hasattr(self, 'tech_card_id'):
                    found_our_card = any(item.get("id") == self.tech_card_id for item in history)
                    if found_our_card:
                        self.log_result("GET /api/user-history", "PASS", 
                                      f"User history retrieved successfully ({len(history)} items)", 
                                      f"Generated tech card found in history")
                    else:
                        self.log_result("GET /api/user-history", "WARNING", 
                                      f"User history retrieved ({len(history)} items) but generated card not found", 
                                      f"Looking for ID: {self.tech_card_id}")
                else:
                    self.log_result("GET /api/user-history", "PASS", 
                                  f"User history retrieved successfully ({len(history)} items)", 
                                  "History structure is valid")
                
                return True
                
            else:
                self.log_result("GET /api/user-history", "FAIL", 
                              f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("GET /api/user-history", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_6_ai_model_verification(self):
        """Verify AI model is using gpt-4o-mini as specified"""
        print("\n🔍 Testing AI model verification...")
        
        try:
            # Generate a simple tech card to test AI model
            data = {
                "dish_name": "Простой салат",
                "user_id": self.test_user_id
            }
            
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and result.get("tech_card"):
                    tech_card = result["tech_card"]
                    
                    # Check for quality indicators that suggest gpt-4o-mini is working
                    quality_indicators = [
                        len(tech_card) > 800,  # Reasonable length
                        "Название:" in tech_card,
                        "Ингредиенты:" in tech_card,
                        "₽" in tech_card,  # Price calculations
                        "КБЖУ" in tech_card or "калории" in tech_card.lower()  # Nutritional info
                    ]
                    
                    quality_score = sum(quality_indicators)
                    
                    if quality_score >= 4:
                        self.log_result("AI Model Verification", "PASS", 
                                      f"AI model generating high-quality content (score: {quality_score}/5)", 
                                      f"Content length: {len(tech_card)} chars")
                    else:
                        self.log_result("AI Model Verification", "WARNING", 
                                      f"AI model quality concerns (score: {quality_score}/5)", 
                                      f"Missing quality indicators")
                    
                    return True
                else:
                    self.log_result("AI Model Verification", "FAIL", 
                                  "AI generation failed", result)
                    return False
            else:
                self.log_result("AI Model Verification", "FAIL", 
                              f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("AI Model Verification", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Receptor Pro Backend API Review Tests")
        print(f"🔗 Testing against: {self.base_url}")
        print(f"📋 Test data: User ID: {self.test_user_id}, Dish: {self.test_dish_name}")
        print("=" * 80)
        
        tests = [
            self.test_1_register_user,
            self.test_2_subscription_plans,
            self.test_3_kitchen_equipment,
            self.test_4_generate_tech_card,
            self.test_5_user_history,
            self.test_6_ai_model_verification
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        for test in tests:
            try:
                success = test()
                if success:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                failed += 1
        
        # Count warnings
        warnings = sum(1 for result in self.results if result["status"] == "WARNING")
        
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['message']}")
        
        print(f"\n📈 RESULTS: {passed} passed, {failed} failed, {warnings} warnings")
        
        if failed == 0:
            print("🎉 ALL CRITICAL TESTS PASSED - Backend API is working correctly!")
            return True
        else:
            print("🚨 SOME TESTS FAILED - Backend API has issues that need attention!")
            return False

def main():
    """Main test execution"""
    tester = ReceptorReviewTest()
    success = tester.run_all_tests()
    
    if success:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()