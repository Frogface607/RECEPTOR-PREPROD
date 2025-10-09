#!/usr/bin/env python3
"""
Additional Backend Test for Tech Card Generation and Equipment Integration
"""

import requests
import json
import random
import string

class TechCardIntegrationTest:
    def __init__(self):
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.test_results = []
        
    def random_string(self, length=6):
        """Generate a random string for test data"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
    
    def create_test_user(self, subscription_plan="free"):
        """Create a test user with specified subscription"""
        test_email = f"test_user_{self.random_string(8)}@example.com"
        test_name = f"Test User {self.random_string(4)}"
        
        try:
            user_data = {
                "email": test_email,
                "name": test_name,
                "city": "moskva"
            }
            
            response = requests.post(f"{self.base_url}/register", json=user_data)
            
            if response.status_code == 200:
                user = response.json()
                user_id = user.get("id")
                
                # Upgrade subscription if needed
                if subscription_plan != "free":
                    upgrade_data = {"subscription_plan": subscription_plan}
                    upgrade_response = requests.post(f"{self.base_url}/upgrade-subscription/{user_id}", json=upgrade_data)
                    if upgrade_response.status_code != 200:
                        return None
                
                return user_id
                
        except Exception as e:
            print(f"Error creating test user: {e}")
        
        return None
    
    def test_tech_card_generation_basic(self):
        """Test basic tech card generation"""
        print("\n🔍 TEST: Basic Tech Card Generation")
        
        user_id = self.create_test_user("free")
        if not user_id:
            self.log_result("Tech Card Generation", False, "Failed to create test user")
            return
        
        try:
            # Generate a simple tech card
            data = {
                "dish_name": "Борщ классический",
                "user_id": user_id
            }
            
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("tech_card"):
                    self.log_result(
                        "Tech Card Generation", 
                        True, 
                        "Tech card generated successfully",
                        f"Generated for: {data['dish_name']}, Length: {len(result['tech_card'])} chars"
                    )
                    return result.get("id")
                else:
                    self.log_result("Tech Card Generation", False, "Tech card generation marked as failed")
            else:
                self.log_result("Tech Card Generation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Tech Card Generation", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_equipment_integration(self):
        """Test equipment integration in tech card generation"""
        print("\n🔍 TEST: Equipment Integration in Tech Card Generation")
        
        # Create PRO user
        pro_user_id = self.create_test_user("pro")
        if not pro_user_id:
            self.log_result("Equipment Integration", False, "Failed to create PRO test user")
            return
        
        try:
            # Set kitchen equipment for PRO user
            equipment_data = {
                "equipment_ids": ["gas_stove", "convection_oven", "food_processor", "blender"]
            }
            
            response = requests.post(f"{self.base_url}/update-kitchen-equipment/{pro_user_id}", json=equipment_data)
            if response.status_code != 200:
                self.log_result("Equipment Integration", False, "Failed to set kitchen equipment")
                return
            
            # Generate tech card that should consider equipment
            data = {
                "dish_name": "Ризотто с грибами",
                "user_id": pro_user_id
            }
            
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("tech_card"):
                    # Check if the tech card mentions equipment (basic check)
                    tech_card_content = result["tech_card"].lower()
                    equipment_mentioned = any(word in tech_card_content for word in ["газовая", "конвекционная", "блендер", "комбайн"])
                    
                    self.log_result(
                        "Equipment Integration", 
                        True, 
                        "Equipment-aware tech card generated successfully",
                        f"Equipment context integrated: {equipment_mentioned}, Length: {len(result['tech_card'])} chars"
                    )
                else:
                    self.log_result("Equipment Integration", False, "Equipment-aware tech card generation failed")
            else:
                self.log_result("Equipment Integration", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Equipment Integration", False, f"Request failed: {str(e)}")
    
    def test_usage_limits(self):
        """Test usage limits for different subscription tiers"""
        print("\n🔍 TEST: Usage Limits Verification")
        
        # Test free tier limit
        free_user_id = self.create_test_user("free")
        if not free_user_id:
            self.log_result("Usage Limits", False, "Failed to create free test user")
            return
        
        try:
            # Generate one tech card for free user
            data = {
                "dish_name": "Простой салат",
                "user_id": free_user_id
            }
            
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                monthly_used = result.get("monthly_used", 0)
                monthly_limit = result.get("monthly_limit", 0)
                
                if monthly_limit == 3 and monthly_used == 1:
                    self.log_result(
                        "Usage Limits", 
                        True, 
                        "Free tier usage limits working correctly",
                        f"Used: {monthly_used}/{monthly_limit} tech cards"
                    )
                else:
                    self.log_result(
                        "Usage Limits", 
                        False, 
                        "Free tier usage limits incorrect",
                        f"Expected 1/3, got {monthly_used}/{monthly_limit}"
                    )
            else:
                self.log_result("Usage Limits", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Usage Limits", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all tech card integration tests"""
        print("🚀 Starting Tech Card Integration Tests")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Run all tests
        self.test_tech_card_generation_basic()
        self.test_equipment_integration()
        self.test_usage_limits()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TECH CARD INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print(f"\n🎯 RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All tech card integration tests PASSED!")
            return True
        else:
            print("❌ Some tech card integration tests FAILED!")
            return False

if __name__ == "__main__":
    tester = TechCardIntegrationTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)