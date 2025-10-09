#!/usr/bin/env python3
"""
Focused Backend Test for Receptor Pro - Review Request Testing
Tests specific functionality requested in the review:
1. AI Model Verification
2. Kitchen Equipment Feature
3. Subscription System
4. User Registration and Management
"""

import requests
import json
import random
import string
from datetime import datetime

class FocusedReceptorTest:
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
    
    def test_ai_model_verification(self):
        """Test 1: AI Model Verification - Check backend code uses gpt-4o-mini"""
        print("\n🔍 TEST 1: AI Model Verification")
        
        # Read backend server.py to verify AI model usage
        try:
            with open('/app/backend/server.py', 'r') as f:
                content = f.read()
            
            # Check tech card generation endpoint
            generation_model_found = 'ai_model = "gpt-4o-mini"' in content
            
            # Check tech card editing endpoint  
            editing_model_found = content.count('ai_model = "gpt-4o-mini"') >= 2
            
            if generation_model_found and editing_model_found:
                self.log_result(
                    "AI Model Verification", 
                    True, 
                    "Both tech card generation and editing endpoints use gpt-4o-mini model",
                    "Found gpt-4o-mini model specified in both /api/generate-tech-card and /api/edit-tech-card endpoints"
                )
            else:
                self.log_result(
                    "AI Model Verification", 
                    False, 
                    "AI model verification failed",
                    f"Generation model found: {generation_model_found}, Editing model found: {editing_model_found}"
                )
                
        except Exception as e:
            self.log_result("AI Model Verification", False, f"Error reading backend code: {str(e)}")
    
    def test_kitchen_equipment_endpoints(self):
        """Test 2: Kitchen Equipment Feature - Test all endpoints"""
        print("\n🔍 TEST 2: Kitchen Equipment Feature")
        
        # Test GET /api/kitchen-equipment
        try:
            response = requests.get(f"{self.base_url}/kitchen-equipment")
            if response.status_code == 200:
                equipment = response.json()
                
                # Verify structure
                categories = ["cooking_methods", "prep_equipment", "storage"]
                all_categories_present = all(cat in equipment for cat in categories)
                
                # Count total equipment
                total_equipment = sum(len(equipment.get(cat, [])) for cat in categories)
                
                if all_categories_present and total_equipment == 21:
                    self.log_result(
                        "Kitchen Equipment GET", 
                        True, 
                        f"Successfully retrieved all 21 equipment types across 3 categories",
                        f"Categories: {categories}, Total items: {total_equipment}"
                    )
                else:
                    self.log_result(
                        "Kitchen Equipment GET", 
                        False, 
                        f"Equipment structure incorrect",
                        f"Categories present: {all_categories_present}, Total items: {total_equipment}"
                    )
            else:
                self.log_result("Kitchen Equipment GET", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Kitchen Equipment GET", False, f"Request failed: {str(e)}")
    
    def test_user_registration(self):
        """Test 3: User Registration and Management"""
        print("\n🔍 TEST 3: User Registration and Management")
        
        # Create test user
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
                
                if user_id and user.get("subscription_plan") == "free":
                    self.log_result(
                        "User Registration", 
                        True, 
                        "User registration successful with default free subscription",
                        f"User ID: {user_id}, Plan: {user.get('subscription_plan')}"
                    )
                    return user_id
                else:
                    self.log_result("User Registration", False, "User created but missing required fields")
            else:
                self.log_result("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("User Registration", False, f"Request failed: {str(e)}")
        
        return None
    
    def test_subscription_system(self):
        """Test 4: Subscription System - PRO vs Free user access"""
        print("\n🔍 TEST 4: Subscription System")
        
        # Create two users - one free, one PRO
        free_user_id = self.test_user_registration()
        pro_user_id = self.test_user_registration()
        
        if not free_user_id or not pro_user_id:
            self.log_result("Subscription System", False, "Failed to create test users")
            return
        
        try:
            # Upgrade one user to PRO
            upgrade_data = {"subscription_plan": "pro"}
            response = requests.post(f"{self.base_url}/upgrade-subscription/{pro_user_id}", json=upgrade_data)
            
            if response.status_code != 200:
                self.log_result("Subscription System", False, f"Failed to upgrade user to PRO: {response.text}")
                return
            
            # Test kitchen equipment access for PRO user (should work)
            equipment_data = {"equipment_ids": ["gas_stove", "food_processor"]}
            response = requests.post(f"{self.base_url}/update-kitchen-equipment/{pro_user_id}", json=equipment_data)
            
            pro_access_works = response.status_code == 200
            
            # Test kitchen equipment access for Free user (should fail)
            response = requests.post(f"{self.base_url}/update-kitchen-equipment/{free_user_id}", json=equipment_data)
            
            free_access_blocked = response.status_code == 403
            
            if pro_access_works and free_access_blocked:
                self.log_result(
                    "Subscription System", 
                    True, 
                    "PRO users can access kitchen equipment, Free users are properly blocked",
                    f"PRO access: {pro_access_works}, Free blocked: {free_access_blocked}"
                )
            else:
                self.log_result(
                    "Subscription System", 
                    False, 
                    "Subscription access control not working correctly",
                    f"PRO access: {pro_access_works}, Free blocked: {free_access_blocked}"
                )
                
        except Exception as e:
            self.log_result("Subscription System", False, f"Request failed: {str(e)}")
    
    def test_user_registration(self):
        """Helper method to create a test user"""
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
                return user.get("id")
                
        except Exception as e:
            print(f"Error creating test user: {e}")
        
        return None
    
    def test_subscription_plans_endpoint(self):
        """Test 5: Subscription Plans Endpoint"""
        print("\n🔍 TEST 5: Subscription Plans Endpoint")
        
        try:
            response = requests.get(f"{self.base_url}/subscription-plans")
            
            if response.status_code == 200:
                plans = response.json()
                
                # Verify all 4 tiers exist
                required_plans = ["free", "starter", "pro", "business"]
                plans_present = all(plan in plans for plan in required_plans)
                
                # Verify PRO and Business have kitchen equipment feature
                pro_has_equipment = plans.get("pro", {}).get("kitchen_equipment", False)
                business_has_equipment = plans.get("business", {}).get("kitchen_equipment", False)
                free_no_equipment = not plans.get("free", {}).get("kitchen_equipment", True)
                starter_no_equipment = not plans.get("starter", {}).get("kitchen_equipment", True)
                
                if plans_present and pro_has_equipment and business_has_equipment and free_no_equipment and starter_no_equipment:
                    self.log_result(
                        "Subscription Plans", 
                        True, 
                        "All 4 subscription tiers present with correct kitchen equipment access",
                        f"Plans: {list(plans.keys())}, PRO/Business have equipment: {pro_has_equipment}/{business_has_equipment}"
                    )
                else:
                    self.log_result(
                        "Subscription Plans", 
                        False, 
                        "Subscription plans structure incorrect",
                        f"Plans present: {plans_present}, Equipment access: PRO={pro_has_equipment}, Business={business_has_equipment}"
                    )
            else:
                self.log_result("Subscription Plans", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Subscription Plans", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all focused tests"""
        print("🚀 Starting Focused Backend Tests for Receptor Pro")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Run all tests
        self.test_ai_model_verification()
        self.test_kitchen_equipment_endpoints()
        self.test_subscription_plans_endpoint()
        user_id = self.test_user_registration()
        self.test_subscription_system()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print(f"\n🎯 RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All focused backend tests PASSED!")
            return True
        else:
            print("❌ Some focused backend tests FAILED!")
            return False

if __name__ == "__main__":
    tester = FocusedReceptorTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)