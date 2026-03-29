#!/usr/bin/env python3
"""
V1 Recipe Generation Backend Testing
Протестировать новый endpoint генерации V1 рецептов

Test Plan:
1. Test V1 Recipe Generation Endpoint - POST /api/v1/generate-recipe
2. Verify Response Structure - recipe with formatted text, meta with id and version: "v1"
3. Check Recipe Content - detailed recipe with steps, tips, variations
4. Verify Database Storage - check that V1 recipe is saved in recipes_v1 collection
5. Find Saved Recipe in MongoDB - locate the saved recipe

Цель: убедиться что backend endpoint работает и генерирует красивые V1 рецепты для AI-кухни.
"""

import requests
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import pymongo
from pymongo import MongoClient

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')

# Test data
TEST_RECIPE_DATA = {
    "dish_name": "Паста карбонара",
    "cuisine": "итальянская", 
    "restaurant_type": "casual",
    "user_id": "demo_user"
}

class V1RecipeGenerationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'V1-Recipe-Generation-Tester/1.0'
        })
        self.test_results = []
        self.generated_recipe_id = None
        self.mongo_client = None
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
        
    def setup_mongodb_connection(self) -> bool:
        """Setup MongoDB connection for database verification"""
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            # Test connection
            self.mongo_client.admin.command('ping')
            
            self.log_test(
                "MongoDB Connection Setup",
                True,
                f"Successfully connected to MongoDB: {MONGO_URL}"
            )
            return True
            
        except Exception as e:
            self.log_test(
                "MongoDB Connection Setup",
                False,
                f"Failed to connect to MongoDB: {str(e)}"
            )
            return False
    
    def test_v1_recipe_generation(self) -> bool:
        """Test 1: V1 Recipe Generation Endpoint - POST /api/v1/generate-recipe"""
        try:
            url = f"{API_BASE}/v1/generate-recipe"
            
            print(f"   Generating V1 recipe: {TEST_RECIPE_DATA['dish_name']}")
            print(f"   Cuisine: {TEST_RECIPE_DATA['cuisine']}")
            print(f"   Restaurant type: {TEST_RECIPE_DATA['restaurant_type']}")
            
            response = self.session.post(url, json=TEST_RECIPE_DATA, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for successful generation
                if 'recipe' in data and 'meta' in data:
                    recipe = data['recipe']
                    meta = data['meta']
                    
                    # Store recipe ID for later tests
                    self.generated_recipe_id = meta.get('id')
                    
                    self.log_test(
                        "V1 Recipe Generation Endpoint",
                        True,
                        f"V1 recipe generated successfully. ID: {self.generated_recipe_id}",
                        {
                            'recipe_id': self.generated_recipe_id,
                            'has_recipe': bool(recipe),
                            'has_meta': bool(meta),
                            'recipe_length': len(str(recipe)) if recipe else 0
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "V1 Recipe Generation Endpoint",
                        False,
                        "Response missing required fields (recipe, meta)",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "V1 Recipe Generation Endpoint",
                    False,
                    f"Generation API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "V1 Recipe Generation Endpoint",
                False,
                f"Generation API request failed: {str(e)}"
            )
            return False
        except json.JSONDecodeError as e:
            self.log_test(
                "V1 Recipe Generation Endpoint",
                False,
                f"Invalid JSON response: {str(e)}"
            )
            return False
    
    def test_response_structure(self) -> bool:
        """Test 2: Verify Response Structure - recipe with formatted text, meta with id and version: "v1" """
        try:
            url = f"{API_BASE}/v1/generate-recipe"
            
            response = self.session.post(url, json=TEST_RECIPE_DATA, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                recipe = data.get('recipe')
                meta = data.get('meta')
                
                if not recipe or not meta:
                    self.log_test(
                        "Response Structure Verification",
                        False,
                        "Missing recipe or meta in response",
                        data
                    )
                    return False
                
                # Check meta structure
                recipe_id = meta.get('id')
                version = meta.get('version')
                
                if not recipe_id:
                    self.log_test(
                        "Response Structure Verification",
                        False,
                        "Missing id in meta",
                        meta
                    )
                    return False
                
                if version != "v1":
                    self.log_test(
                        "Response Structure Verification",
                        False,
                        f"Expected version 'v1', got '{version}'",
                        meta
                    )
                    return False
                
                # Check recipe content is formatted text
                if not isinstance(recipe, str) or len(recipe) < 100:
                    self.log_test(
                        "Response Structure Verification",
                        False,
                        f"Recipe should be formatted text string, got {type(recipe)} with length {len(str(recipe))}",
                        {'recipe_type': type(recipe), 'recipe_length': len(str(recipe))}
                    )
                    return False
                
                self.log_test(
                    "Response Structure Verification",
                    True,
                    f"Response structure correct: recipe text ({len(recipe)} chars), meta with id and version=v1",
                    {
                        'recipe_id': recipe_id,
                        'version': version,
                        'recipe_length': len(recipe),
                        'recipe_preview': recipe[:100] + "..." if len(recipe) > 100 else recipe
                    }
                )
                return True
            else:
                self.log_test(
                    "Response Structure Verification",
                    False,
                    f"API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Response Structure Verification",
                False,
                f"Structure verification failed: {str(e)}"
            )
            return False
    
    def test_recipe_content_quality(self) -> bool:
        """Test 3: Check Recipe Content - detailed recipe with steps, tips, variations"""
        try:
            url = f"{API_BASE}/v1/generate-recipe"
            
            response = self.session.post(url, json=TEST_RECIPE_DATA, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                recipe = data.get('recipe', '')
                
                if not recipe:
                    self.log_test(
                        "Recipe Content Quality Check",
                        False,
                        "No recipe content found"
                    )
                    return False
                
                # Check for key recipe components (case insensitive)
                recipe_lower = recipe.lower()
                
                # Check for steps/instructions
                has_steps = any(keyword in recipe_lower for keyword in [
                    'шаг', 'этап', 'приготовление', 'инструкция', 'способ', 'метод'
                ])
                
                # Check for ingredients
                has_ingredients = any(keyword in recipe_lower for keyword in [
                    'ингредиент', 'продукт', 'состав', 'нужно', 'требуется'
                ])
                
                # Check for tips or variations
                has_tips = any(keyword in recipe_lower for keyword in [
                    'совет', 'рекомендация', 'вариант', 'можно', 'лучше', 'важно'
                ])
                
                # Check recipe length (should be detailed)
                is_detailed = len(recipe) > 300
                
                # Check for pasta carbonara specific content
                has_carbonara_content = any(keyword in recipe_lower for keyword in [
                    'карбонара', 'паста', 'спагетти', 'бекон', 'яйц', 'сыр', 'пармезан'
                ])
                
                quality_score = sum([has_steps, has_ingredients, has_tips, is_detailed, has_carbonara_content])
                
                if quality_score >= 4:
                    self.log_test(
                        "Recipe Content Quality Check",
                        True,
                        f"Recipe content is detailed and comprehensive (quality score: {quality_score}/5)",
                        {
                            'has_steps': has_steps,
                            'has_ingredients': has_ingredients,
                            'has_tips': has_tips,
                            'is_detailed': is_detailed,
                            'has_specific_content': has_carbonara_content,
                            'recipe_length': len(recipe),
                            'quality_score': quality_score
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Recipe Content Quality Check",
                        False,
                        f"Recipe content lacks detail (quality score: {quality_score}/5)",
                        {
                            'has_steps': has_steps,
                            'has_ingredients': has_ingredients,
                            'has_tips': has_tips,
                            'is_detailed': is_detailed,
                            'has_specific_content': has_carbonara_content,
                            'recipe_length': len(recipe),
                            'quality_score': quality_score,
                            'recipe_preview': recipe[:200] + "..." if len(recipe) > 200 else recipe
                        }
                    )
                    return False
            else:
                self.log_test(
                    "Recipe Content Quality Check",
                    False,
                    f"API returned HTTP {response.status_code}",
                    response.text[:200]
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Recipe Content Quality Check",
                False,
                f"Content quality check failed: {str(e)}"
            )
            return False
    
    def test_database_storage(self) -> bool:
        """Test 4: Verify Database Storage - check that V1 recipe is saved in recipes_v1 collection"""
        try:
            if not self.mongo_client:
                self.log_test(
                    "Database Storage Verification",
                    False,
                    "MongoDB connection not available"
                )
                return False
            
            # Generate a recipe first to ensure we have something to check
            url = f"{API_BASE}/v1/generate-recipe"
            response = self.session.post(url, json=TEST_RECIPE_DATA, timeout=60)
            
            if response.status_code != 200:
                self.log_test(
                    "Database Storage Verification",
                    False,
                    f"Failed to generate recipe for storage test: HTTP {response.status_code}"
                )
                return False
            
            data = response.json()
            recipe_id = data.get('meta', {}).get('id')
            
            if not recipe_id:
                self.log_test(
                    "Database Storage Verification",
                    False,
                    "No recipe ID returned from generation"
                )
                return False
            
            # Wait a moment for database write
            time.sleep(2)
            
            # Check recipes_v1 collection
            db = self.mongo_client.get_database()
            recipes_v1_collection = db.recipes_v1
            
            # Find the recipe by ID (the correct field is 'id', not '_id')
            saved_recipe = recipes_v1_collection.find_one({"id": recipe_id})
            
            if saved_recipe:
                # Verify the structure matches V1 format
                has_content = 'content' in saved_recipe and len(saved_recipe['content']) > 100
                has_version = saved_recipe.get('version') == 'v1'
                has_type = saved_recipe.get('type') == 'recipe'
                has_dish_name = saved_recipe.get('name') == TEST_RECIPE_DATA['dish_name']
                
                self.log_test(
                    "Database Storage Verification",
                    True,
                    f"V1 recipe successfully saved in recipes_v1 collection with ID: {recipe_id}",
                    {
                        'recipe_id': recipe_id,
                        'collection': 'recipes_v1',
                        'has_content': has_content,
                        'content_length': len(saved_recipe.get('content', '')),
                        'version': saved_recipe.get('version'),
                        'type': saved_recipe.get('type'),
                        'dish_name': saved_recipe.get('name'),
                        'created_at': saved_recipe.get('created_at', 'unknown'),
                        'structure_valid': has_content and has_version and has_type and has_dish_name
                    }
                )
                return True
            else:
                # Check total count in collection and recent recipes
                total_recipes = recipes_v1_collection.count_documents({})
                recent_recipes = list(recipes_v1_collection.find({}).sort('_id', -1).limit(3))
                recent_ids = [r.get('id') for r in recent_recipes]
                
                self.log_test(
                    "Database Storage Verification",
                    False,
                    f"Recipe with ID {recipe_id} not found in recipes_v1 collection. Total recipes: {total_recipes}",
                    {
                        'recipe_id': recipe_id,
                        'collection': 'recipes_v1',
                        'total_recipes': total_recipes,
                        'recent_recipe_ids': recent_ids
                    }
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Database Storage Verification",
                False,
                f"Database storage verification failed: {str(e)}"
            )
            return False
    
    def test_find_saved_recipe(self) -> bool:
        """Test 5: Find Saved Recipe in MongoDB - locate the saved recipe"""
        try:
            if not self.mongo_client:
                self.log_test(
                    "Find Saved Recipe in MongoDB",
                    False,
                    "MongoDB connection not available"
                )
                return False
            
            db = self.mongo_client.get_database()
            recipes_v1_collection = db.recipes_v1
            
            # Try different query approaches based on the actual V1 recipe structure
            queries = [
                {"name": TEST_RECIPE_DATA["dish_name"]},  # Correct field name
                {"cuisine": TEST_RECIPE_DATA["cuisine"]},
                {"version": "v1"},
                {"type": "recipe"},
                {}  # Get any recent recipe
            ]
            
            found_recipe = None
            query_used = None
            
            for i, query in enumerate(queries):
                try:
                    recipes = list(recipes_v1_collection.find(query).sort('_id', -1).limit(5))
                    if recipes:
                        found_recipe = recipes[0]  # Take the most recent one
                        query_used = f"Query {i+1}: {query}"
                        break
                except Exception as e:
                    continue
            
            if found_recipe:
                recipe_id = found_recipe.get('id')  # Correct field for V1 recipes
                dish_name = found_recipe.get('name', 'Unknown')
                
                # Check recipe content (stored in 'content' field for V1)
                recipe_content = found_recipe.get('content', '')
                has_content = len(recipe_content) > 100 if recipe_content else False
                
                # Verify V1 structure
                version = found_recipe.get('version')
                recipe_type = found_recipe.get('type')
                cuisine = found_recipe.get('cuisine')
                
                self.log_test(
                    "Find Saved Recipe in MongoDB",
                    True,
                    f"Successfully found V1 recipe in MongoDB. ID: {recipe_id}, Dish: {dish_name}",
                    {
                        'recipe_id': recipe_id,
                        'dish_name': dish_name,
                        'cuisine': cuisine,
                        'version': version,
                        'type': recipe_type,
                        'query_used': query_used,
                        'has_recipe_content': has_content,
                        'content_length': len(recipe_content) if recipe_content else 0,
                        'collection': 'recipes_v1',
                        'content_preview': recipe_content[:100] + "..." if len(recipe_content) > 100 else recipe_content
                    }
                )
                return True
            else:
                # Check if collection exists and has any documents
                total_count = recipes_v1_collection.count_documents({})
                
                # Get sample document structure
                sample_doc = recipes_v1_collection.find_one({})
                sample_keys = list(sample_doc.keys()) if sample_doc else []
                
                self.log_test(
                    "Find Saved Recipe in MongoDB",
                    False,
                    f"No V1 recipes found in MongoDB. Total documents in recipes_v1: {total_count}",
                    {
                        'collection': 'recipes_v1',
                        'total_documents': total_count,
                        'queries_tried': len(queries),
                        'sample_document_keys': sample_keys
                    }
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Find Saved Recipe in MongoDB",
                False,
                f"MongoDB search failed: {str(e)}"
            )
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        if self.mongo_client:
            self.mongo_client.close()
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all V1 recipe generation tests"""
        print("🚀 STARTING V1 RECIPE GENERATION TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Recipe: {TEST_RECIPE_DATA['dish_name']}")
        print(f"Cuisine: {TEST_RECIPE_DATA['cuisine']}")
        print(f"Restaurant Type: {TEST_RECIPE_DATA['restaurant_type']}")
        print("=" * 60)
        print()
        
        # Setup MongoDB connection
        mongodb_available = self.setup_mongodb_connection()
        
        # Run tests in sequence
        tests = [
            self.test_v1_recipe_generation,
            self.test_response_structure,
            self.test_recipe_content_quality,
        ]
        
        # Add MongoDB tests only if connection is available
        if mongodb_available:
            tests.extend([
                self.test_database_storage,
                self.test_find_saved_recipe
            ])
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_func.__name__}: {str(e)}")
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("=" * 60)
        print("🎯 V1 RECIPE GENERATION TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['details']}")
        
        print()
        print(f"📊 RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 V1 RECIPE GENERATION: FULLY OPERATIONAL")
        elif success_rate >= 60:
            print("⚠️ V1 RECIPE GENERATION: PARTIALLY WORKING")
        else:
            print("🚨 V1 RECIPE GENERATION: CRITICAL ISSUES")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results,
            'generated_recipe_id': self.generated_recipe_id
        }

def main():
    """Main test execution"""
    print("V1 Recipe Generation Backend Testing")
    print("Протестировать новый endpoint генерации V1 рецептов")
    print()
    
    tester = V1RecipeGenerationTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results['success_rate'] >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()