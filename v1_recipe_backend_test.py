#!/usr/bin/env python3
"""
V1 Recipe Endpoint Testing for "Recipes-first" Approach
Testing the new endpoint `/api/v1/generate-recipe` for V1 recipe generation

Test Cases:
1. Check endpoint availability `/api/v1/generate-recipe`
2. Test recipe generation with "Паста Карбонара"
3. Verify correct request format:
   - dish_name: "Паста Карбонара"
   - cuisine: "европейская"
   - restaurant_type: "casual"
   - user_id: "demo_user"
4. Check response structure:
   - Should contain "recipe" field with content
   - Should contain "meta" field with ID and version: "v1"
5. Verify recipe is saved to database in "recipes_v1" collection

Special Checks:
- Endpoint should use OpenAI API
- Check response time (should be reasonable)
- Verify recipe content has proper V1 format with beautiful description

Expected Result: V1 recipe successfully generated and saved, ready for interface display.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from pymongo import MongoClient
from typing import Dict, Any, List, Optional

# Configuration
API_BASE = 'http://localhost:8001'  # Use local backend for testing
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')

class V1RecipeEndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'V1-Recipe-Endpoint-Tester/1.0'
        })
        self.test_results = []
        self.generated_recipe_id = None
        
        # MongoDB connection
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client.get_default_database()
            print(f"✅ Connected to MongoDB: {MONGO_URL}")
        except Exception as e:
            print(f"⚠️ MongoDB connection failed: {e}")
            self.mongo_client = None
            self.db = None

    def log_result(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}: {message}")
        if details:
            for key, value in details.items():
                print(f"      {key}: {value}")

    def test_endpoint_availability(self) -> bool:
        """Test 1: Check endpoint availability `/api/v1/generate-recipe`"""
        try:
            # Test with minimal payload to check if endpoint exists
            url = f"{API_BASE}/api/v1/generate-recipe"
            payload = {
                "dish_name": "Test Dish",
                "user_id": "test_user"
            }
            
            print(f"🔍 Testing endpoint availability: {url}")
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 404:
                self.log_result(
                    "Endpoint Availability",
                    False,
                    f"Endpoint not found (HTTP 404)",
                    {"url": url, "status_code": response.status_code}
                )
                return False
            elif response.status_code in [200, 400, 500]:
                # Endpoint exists (even if request fails due to validation/processing)
                self.log_result(
                    "Endpoint Availability",
                    True,
                    f"Endpoint is available (HTTP {response.status_code})",
                    {"url": url, "status_code": response.status_code}
                )
                return True
            else:
                self.log_result(
                    "Endpoint Availability",
                    False,
                    f"Unexpected response (HTTP {response.status_code})",
                    {"url": url, "status_code": response.status_code, "response": response.text[:200]}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result(
                "Endpoint Availability",
                False,
                f"Request failed: {str(e)}",
                {"url": url, "error": str(e)}
            )
            return False

    def test_pasta_carbonara_generation(self) -> bool:
        """Test 2: Test recipe generation with "Паста Карбонара" """
        try:
            url = f"{API_BASE}/api/v1/generate-recipe"
            payload = {
                "dish_name": "Паста Карбонара",
                "cuisine": "европейская", 
                "restaurant_type": "casual",
                "user_id": "demo_user"
            }
            
            print(f"🍝 Generating V1 recipe: {payload['dish_name']}")
            start_time = time.time()
            
            response = self.session.post(url, json=payload, timeout=60)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check response structure
                    if "recipe" in data and "meta" in data:
                        recipe_content = data["recipe"]
                        meta = data["meta"]
                        
                        # Verify meta structure
                        recipe_id = meta.get("id")
                        version = meta.get("version")
                        
                        if recipe_id and version == "v1":
                            self.generated_recipe_id = recipe_id
                            
                            # Analyze recipe content quality
                            content_score = self.analyze_v1_content_quality(recipe_content)
                            
                            self.log_result(
                                "Pasta Carbonara Generation",
                                True,
                                f"V1 recipe generated successfully. ID: {recipe_id}, Version: {version}, Content quality: {content_score}/8 sections",
                                {
                                    "recipe_id": recipe_id,
                                    "version": version,
                                    "response_time": f"{response_time:.2f}s",
                                    "content_length": len(recipe_content),
                                    "content_score": content_score,
                                    "dish_name": payload['dish_name']
                                }
                            )
                            return True
                        else:
                            self.log_result(
                                "Pasta Carbonara Generation",
                                False,
                                f"Invalid meta structure. ID: {recipe_id}, Version: {version}",
                                {"meta": meta, "expected_version": "v1"}
                            )
                            return False
                    else:
                        self.log_result(
                            "Pasta Carbonara Generation",
                            False,
                            "Response missing required fields (recipe, meta)",
                            {"response_keys": list(data.keys()), "expected": ["recipe", "meta"]}
                        )
                        return False
                        
                except json.JSONDecodeError as e:
                    self.log_result(
                        "Pasta Carbonara Generation",
                        False,
                        f"Invalid JSON response: {str(e)}",
                        {"response_text": response.text[:500]}
                    )
                    return False
            else:
                self.log_result(
                    "Pasta Carbonara Generation",
                    False,
                    f"Recipe generation failed with HTTP {response.status_code}",
                    {"status_code": response.status_code, "response": response.text[:500]}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result(
                "Pasta Carbonara Generation",
                False,
                f"Request failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def analyze_v1_content_quality(self, content: str) -> int:
        """Analyze V1 recipe content quality by checking for expected sections"""
        expected_sections = [
            "ОПИСАНИЕ",
            "ВРЕМЕННЫЕ РАМКИ", 
            "ИНГРЕДИЕНТЫ",
            "ПОШАГОВОЕ ПРИГОТОВЛЕНИЕ",
            "СЕКРЕТЫ ШЕФА",
            "ПОДАЧА И ПРЕЗЕНТАЦИЯ",
            "ВАРИАЦИИ И ЭКСПЕРИМЕНТЫ",
            "ПОЛЕЗНЫЕ СОВЕТЫ"
        ]
        
        score = 0
        for section in expected_sections:
            if section in content:
                score += 1
                
        return score

    def test_request_format_validation(self) -> bool:
        """Test 3: Verify correct request format validation"""
        test_cases = [
            {
                "name": "Complete Valid Request",
                "payload": {
                    "dish_name": "Паста Карбонара",
                    "cuisine": "европейская",
                    "restaurant_type": "casual", 
                    "user_id": "demo_user"
                },
                "should_succeed": True
            },
            {
                "name": "Missing dish_name",
                "payload": {
                    "cuisine": "европейская",
                    "restaurant_type": "casual",
                    "user_id": "demo_user"
                },
                "should_succeed": False
            },
            {
                "name": "Missing user_id",
                "payload": {
                    "dish_name": "Паста Карбонара",
                    "cuisine": "европейская",
                    "restaurant_type": "casual"
                },
                "should_succeed": False
            },
            {
                "name": "Default values test",
                "payload": {
                    "dish_name": "Паста Карбонара",
                    "user_id": "demo_user"
                    # cuisine and restaurant_type should default
                },
                "should_succeed": True
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            try:
                url = f"{API_BASE}/api/v1/generate-recipe"
                response = self.session.post(url, json=test_case["payload"], timeout=30)
                
                if test_case["should_succeed"]:
                    if response.status_code == 200:
                        self.log_result(
                            f"Request Format - {test_case['name']}",
                            True,
                            "Valid request accepted",
                            {"status_code": response.status_code}
                        )
                    else:
                        self.log_result(
                            f"Request Format - {test_case['name']}",
                            False,
                            f"Valid request rejected with HTTP {response.status_code}",
                            {"status_code": response.status_code, "response": response.text[:200]}
                        )
                        all_passed = False
                else:
                    if response.status_code == 400:
                        self.log_result(
                            f"Request Format - {test_case['name']}",
                            True,
                            "Invalid request properly rejected",
                            {"status_code": response.status_code}
                        )
                    else:
                        self.log_result(
                            f"Request Format - {test_case['name']}",
                            False,
                            f"Invalid request not properly rejected (HTTP {response.status_code})",
                            {"status_code": response.status_code, "response": response.text[:200]}
                        )
                        all_passed = False
                        
            except requests.exceptions.RequestException as e:
                self.log_result(
                    f"Request Format - {test_case['name']}",
                    False,
                    f"Request failed: {str(e)}",
                    {"error": str(e)}
                )
                all_passed = False
                
        return all_passed

    def test_response_structure(self) -> bool:
        """Test 4: Check response structure requirements"""
        if not self.generated_recipe_id:
            # Generate a recipe first
            if not self.test_pasta_carbonara_generation():
                self.log_result(
                    "Response Structure",
                    False,
                    "Cannot test response structure - no recipe generated",
                    {}
                )
                return False
        
        try:
            url = f"{API_BASE}/api/v1/generate-recipe"
            payload = {
                "dish_name": "Тестовое блюдо для структуры",
                "cuisine": "европейская",
                "restaurant_type": "casual",
                "user_id": "demo_user"
            }
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["recipe", "meta"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Response Structure",
                        False,
                        f"Missing required fields: {missing_fields}",
                        {"response_keys": list(data.keys()), "missing": missing_fields}
                    )
                    return False
                
                # Check meta structure
                meta = data["meta"]
                required_meta_fields = ["id", "version"]
                missing_meta_fields = [field for field in required_meta_fields if field not in meta]
                
                if missing_meta_fields:
                    self.log_result(
                        "Response Structure",
                        False,
                        f"Missing required meta fields: {missing_meta_fields}",
                        {"meta_keys": list(meta.keys()), "missing": missing_meta_fields}
                    )
                    return False
                
                # Check version is "v1"
                if meta.get("version") != "v1":
                    self.log_result(
                        "Response Structure",
                        False,
                        f"Incorrect version: {meta.get('version')}, expected 'v1'",
                        {"version": meta.get("version")}
                    )
                    return False
                
                # Check recipe content exists and is not empty
                recipe_content = data["recipe"]
                if not recipe_content or len(recipe_content.strip()) < 100:
                    self.log_result(
                        "Response Structure",
                        False,
                        f"Recipe content too short or empty: {len(recipe_content)} chars",
                        {"content_length": len(recipe_content)}
                    )
                    return False
                
                self.log_result(
                    "Response Structure",
                    True,
                    "Response structure is correct",
                    {
                        "recipe_length": len(recipe_content),
                        "meta_id": meta.get("id"),
                        "meta_version": meta.get("version")
                    }
                )
                return True
                
            else:
                self.log_result(
                    "Response Structure",
                    False,
                    f"Failed to generate recipe for structure test (HTTP {response.status_code})",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Response Structure",
                False,
                f"Response structure test failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_mongodb_storage(self) -> bool:
        """Test 5: Verify recipe is saved to database in 'recipes_v1' collection"""
        if not self.db:
            self.log_result(
                "MongoDB Storage",
                False,
                "Cannot test MongoDB storage - no database connection",
                {}
            )
            return False
            
        if not self.generated_recipe_id:
            self.log_result(
                "MongoDB Storage",
                False,
                "Cannot test MongoDB storage - no recipe ID available",
                {}
            )
            return False
        
        try:
            # Check if recipes_v1 collection exists and contains our recipe
            collection = self.db.recipes_v1
            
            # Find the recipe by ID
            recipe = collection.find_one({"id": self.generated_recipe_id})
            
            if recipe:
                # Verify required fields
                required_fields = ["id", "name", "cuisine", "restaurant_type", "content", "version", "type", "created_at", "user_id"]
                missing_fields = [field for field in required_fields if field not in recipe]
                
                if missing_fields:
                    self.log_result(
                        "MongoDB Storage",
                        False,
                        f"Recipe found but missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "available_fields": list(recipe.keys())}
                    )
                    return False
                
                # Verify field values
                if recipe.get("version") != "v1":
                    self.log_result(
                        "MongoDB Storage",
                        False,
                        f"Incorrect version in database: {recipe.get('version')}",
                        {"version": recipe.get("version")}
                    )
                    return False
                
                if recipe.get("type") != "recipe":
                    self.log_result(
                        "MongoDB Storage",
                        False,
                        f"Incorrect type in database: {recipe.get('type')}",
                        {"type": recipe.get("type")}
                    )
                    return False
                
                self.log_result(
                    "MongoDB Storage",
                    True,
                    "Recipe properly saved to recipes_v1 collection",
                    {
                        "recipe_id": recipe.get("id"),
                        "name": recipe.get("name"),
                        "version": recipe.get("version"),
                        "type": recipe.get("type"),
                        "user_id": recipe.get("user_id"),
                        "content_length": len(recipe.get("content", ""))
                    }
                )
                return True
            else:
                self.log_result(
                    "MongoDB Storage",
                    False,
                    f"Recipe not found in recipes_v1 collection",
                    {"recipe_id": self.generated_recipe_id}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "MongoDB Storage",
                False,
                f"MongoDB storage test failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_openai_integration(self) -> bool:
        """Test 6: Verify OpenAI API integration and response time"""
        try:
            url = f"{API_BASE}/api/v1/generate-recipe"
            payload = {
                "dish_name": "Тестовое блюдо для OpenAI",
                "cuisine": "европейская",
                "restaurant_type": "casual",
                "user_id": "demo_user"
            }
            
            print(f"🤖 Testing OpenAI integration...")
            start_time = time.time()
            
            response = self.session.post(url, json=payload, timeout=120)  # Longer timeout for AI
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                recipe_content = data.get("recipe", "")
                
                # Check if content looks AI-generated (has proper structure and length)
                if len(recipe_content) > 500 and "ОПИСАНИЕ" in recipe_content:
                    # Check response time is reasonable (under 60 seconds)
                    if response_time < 60:
                        self.log_result(
                            "OpenAI Integration",
                            True,
                            f"OpenAI integration working, response time: {response_time:.2f}s",
                            {
                                "response_time": f"{response_time:.2f}s",
                                "content_length": len(recipe_content),
                                "has_structure": "ОПИСАНИЕ" in recipe_content
                            }
                        )
                        return True
                    else:
                        self.log_result(
                            "OpenAI Integration",
                            False,
                            f"Response time too slow: {response_time:.2f}s (>60s)",
                            {"response_time": f"{response_time:.2f}s"}
                        )
                        return False
                else:
                    self.log_result(
                        "OpenAI Integration",
                        False,
                        "Generated content appears invalid or too short",
                        {"content_length": len(recipe_content), "has_structure": "ОПИСАНИЕ" in recipe_content}
                    )
                    return False
            else:
                self.log_result(
                    "OpenAI Integration",
                    False,
                    f"OpenAI integration failed (HTTP {response.status_code})",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_result(
                "OpenAI Integration",
                False,
                "Request timed out (>120s)",
                {"timeout": "120s"}
            )
            return False
        except Exception as e:
            self.log_result(
                "OpenAI Integration",
                False,
                f"OpenAI integration test failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def test_v1_format_quality(self) -> bool:
        """Test 7: Verify V1 format has beautiful description and proper structure"""
        if not self.generated_recipe_id:
            # Generate a recipe first
            if not self.test_pasta_carbonara_generation():
                self.log_result(
                    "V1 Format Quality",
                    False,
                    "Cannot test V1 format - no recipe generated",
                    {}
                )
                return False
        
        try:
            # Get the recipe from database to analyze content
            if self.db:
                collection = self.db.recipes_v1
                recipe = collection.find_one({"id": self.generated_recipe_id})
                
                if recipe:
                    content = recipe.get("content", "")
                    
                    # Analyze V1 format quality
                    quality_checks = {
                        "has_description": "ОПИСАНИЕ" in content,
                        "has_time_frames": "ВРЕМЕННЫЕ РАМКИ" in content,
                        "has_ingredients": "ИНГРЕДИЕНТЫ" in content,
                        "has_steps": "ПОШАГОВОЕ ПРИГОТОВЛЕНИЕ" in content,
                        "has_chef_secrets": "СЕКРЕТЫ ШЕФА" in content,
                        "has_presentation": "ПОДАЧА И ПРЕЗЕНТАЦИЯ" in content,
                        "sufficient_length": len(content) > 1000,
                        "has_emojis": any(emoji in content for emoji in ["🎯", "⏱️", "🛒", "🔥", "👨‍🍳", "🎨"])
                    }
                    
                    passed_checks = sum(quality_checks.values())
                    total_checks = len(quality_checks)
                    
                    if passed_checks >= 6:  # At least 75% of checks should pass
                        self.log_result(
                            "V1 Format Quality",
                            True,
                            f"V1 format quality is good ({passed_checks}/{total_checks} checks passed)",
                            {
                                "quality_score": f"{passed_checks}/{total_checks}",
                                "content_length": len(content),
                                "checks": quality_checks
                            }
                        )
                        return True
                    else:
                        self.log_result(
                            "V1 Format Quality",
                            False,
                            f"V1 format quality is poor ({passed_checks}/{total_checks} checks passed)",
                            {
                                "quality_score": f"{passed_checks}/{total_checks}",
                                "content_length": len(content),
                                "failed_checks": [k for k, v in quality_checks.items() if not v]
                            }
                        )
                        return False
                else:
                    self.log_result(
                        "V1 Format Quality",
                        False,
                        "Recipe not found in database for quality analysis",
                        {"recipe_id": self.generated_recipe_id}
                    )
                    return False
            else:
                self.log_result(
                    "V1 Format Quality",
                    False,
                    "Cannot analyze V1 format quality - no database connection",
                    {}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "V1 Format Quality",
                False,
                f"V1 format quality test failed: {str(e)}",
                {"error": str(e)}
            )
            return False

    def run_all_tests(self):
        """Run all V1 recipe endpoint tests"""
        print("🚀 Starting V1 Recipe Endpoint Testing for 'Recipes-first' Approach")
        print("=" * 80)
        
        tests = [
            ("Endpoint Availability", self.test_endpoint_availability),
            ("Pasta Carbonara Generation", self.test_pasta_carbonara_generation),
            ("Request Format Validation", self.test_request_format_validation),
            ("Response Structure", self.test_response_structure),
            ("MongoDB Storage", self.test_mongodb_storage),
            ("OpenAI Integration", self.test_openai_integration),
            ("V1 Format Quality", self.test_v1_format_quality)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test_name} crashed: {e}")
                self.log_result(test_name, False, f"Test crashed: {str(e)}", {"error": str(e)})
        
        print("\n" + "=" * 80)
        print(f"🎯 V1 Recipe Endpoint Testing Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL TESTS PASSED - V1 Recipe endpoint is fully operational!")
        elif passed >= total * 0.8:
            print("⚠️ MOSTLY WORKING - Minor issues detected")
        else:
            print("❌ CRITICAL ISSUES - V1 Recipe endpoint needs attention")
        
        # Summary of key findings
        print("\n📊 Key Findings:")
        for result in self.test_results:
            if not result['success']:
                print(f"   ❌ {result['test']}: {result['message']}")
        
        if self.generated_recipe_id:
            print(f"\n🆔 Generated Recipe ID: {self.generated_recipe_id}")
        
        return passed, total

if __name__ == "__main__":
    tester = V1RecipeEndpointTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        sys.exit(0)  # All tests passed
    else:
        sys.exit(1)  # Some tests failed