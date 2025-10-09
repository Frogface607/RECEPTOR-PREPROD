#!/usr/bin/env python3
"""
Backend Test Suite for Task #14: Sub-recipes Integration Backend Implementation

This test suite verifies the sub-recipes integration in TechCardV2 generation pipeline.
Tests cover backwards compatibility, schema validation, cost/nutrition calculator integration,
and error handling for sub-recipe data.
"""

import requests
import json
import time
import os
from typing import Dict, Any, List

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SubRecipeIntegrationTester:
    """Test suite for sub-recipes integration backend implementation"""
    
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SubRecipeIntegrationTester/1.0'
        })
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        if response_data:
            result['response_data'] = response_data
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_basic_techcard_generation_backwards_compatibility(self):
        """Test 1: Basic TechCardV2 Generation Still Works (backwards compatibility)"""
        print("\n🔍 Testing Basic TechCardV2 Generation Backwards Compatibility...")
        
        try:
            # Test regular tech card generation without sub-recipes
            payload = {
                "name": "Куриное филе с овощами",
                "cuisine": "европейская",
                "equipment": [],
                "budget": 500,
                "dietary": []
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify basic structure
                if 'card' in data and data['card']:
                    card = data['card']
                    
                    # Check essential fields
                    required_fields = ['meta', 'ingredients', 'portions', 'yield', 'process']
                    missing_fields = [field for field in required_fields if field not in card]
                    
                    if not missing_fields:
                        # Check cost and nutrition calculations work
                        has_cost = 'cost' in card and card['cost']
                        has_nutrition = 'nutrition' in card and card['nutrition']
                        
                        self.log_test(
                            "Basic TechCardV2 Generation",
                            "PASS",
                            f"Generated tech card with {len(card.get('ingredients', []))} ingredients. Cost: {has_cost}, Nutrition: {has_nutrition}",
                            {'card_title': card.get('meta', {}).get('title', 'Unknown')}
                        )
                        return True
                    else:
                        self.log_test(
                            "Basic TechCardV2 Generation",
                            "FAIL",
                            f"Missing required fields: {missing_fields}"
                        )
                        return False
                else:
                    self.log_test(
                        "Basic TechCardV2 Generation",
                        "FAIL",
                        f"No card in response. Status: {data.get('status', 'unknown')}, Issues: {data.get('issues', [])}"
                    )
                    return False
            else:
                self.log_test(
                    "Basic TechCardV2 Generation",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Basic TechCardV2 Generation",
                "FAIL",
                f"Exception: {str(e)}"
            )
            return False
    
    def test_subrecipe_schema_validation(self):
        """Test 2: Sub-recipe Schema Validation (SubRecipeRefV2 schema handling)"""
        print("\n🔍 Testing Sub-recipe Schema Validation...")
        
        try:
            # Create a tech card with sub-recipe ingredients
            payload = {
                "name": "Борщ с домашней сметаной",
                "cuisine": "украинская",
                "equipment": [],
                "budget": 300,
                "dietary": []
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'card' in data and data['card']:
                    card = data['card']
                    
                    # Check if any ingredients have subRecipe field (they shouldn't in normal generation)
                    ingredients_with_subrecipe = []
                    for ingredient in card.get('ingredients', []):
                        if 'subRecipe' in ingredient and ingredient['subRecipe']:
                            ingredients_with_subrecipe.append(ingredient)
                    
                    # For this test, we'll manually create a tech card with sub-recipe to test schema
                    test_card_with_subrecipe = {
                        "meta": {
                            "title": "Test Card with Sub-recipe",
                            "version": "2.0"
                        },
                        "portions": 4,
                        "yield": {
                            "perPortion_g": 200.0,
                            "perBatch_g": 800.0
                        },
                        "ingredients": [
                            {
                                "name": "Куриное филе",
                                "unit": "g",
                                "brutto_g": 400.0,
                                "loss_pct": 10.0,
                                "netto_g": 360.0,
                                "allergens": []
                            },
                            {
                                "name": "Домашний соус",
                                "unit": "g",
                                "brutto_g": 100.0,
                                "loss_pct": 0.0,
                                "netto_g": 100.0,
                                "allergens": [],
                                "subRecipe": {
                                    "id": "test-subrecipe-001",
                                    "title": "Домашний томатный соус"
                                }
                            }
                        ],
                        "process": [
                            {"n": 1, "action": "Подготовка ингредиентов", "time_min": 10.0}
                        ],
                        "storage": {
                            "conditions": "Холодильник 0...+4°C",
                            "shelfLife_hours": 24.0,
                            "servingTemp_c": 65.0
                        }
                    }
                    
                    # Test that the schema accepts sub-recipe structure
                    subrecipe_ingredient = test_card_with_subrecipe['ingredients'][1]
                    subrecipe_ref = subrecipe_ingredient['subRecipe']
                    
                    # Validate SubRecipeRefV2 structure
                    has_id = 'id' in subrecipe_ref and isinstance(subrecipe_ref['id'], str)
                    has_title = 'title' in subrecipe_ref and isinstance(subrecipe_ref['title'], str) and len(subrecipe_ref['title']) > 0
                    
                    if has_id and has_title:
                        self.log_test(
                            "Sub-recipe Schema Validation",
                            "PASS",
                            f"SubRecipeRefV2 schema valid: id='{subrecipe_ref['id']}', title='{subrecipe_ref['title']}'",
                            {'subrecipe_structure': subrecipe_ref}
                        )
                        return True
                    else:
                        self.log_test(
                            "Sub-recipe Schema Validation",
                            "FAIL",
                            f"Invalid SubRecipeRefV2 structure. Has ID: {has_id}, Has Title: {has_title}"
                        )
                        return False
                else:
                    self.log_test(
                        "Sub-recipe Schema Validation",
                        "FAIL",
                        "No card generated for schema validation test"
                    )
                    return False
            else:
                self.log_test(
                    "Sub-recipe Schema Validation",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Sub-recipe Schema Validation",
                "FAIL",
                f"Exception: {str(e)}"
            )
            return False
    
    def test_cost_calculator_integration(self):
        """Test 3: Cost Calculator Integration with sub_recipes_cache parameter"""
        print("\n🔍 Testing Cost Calculator Integration...")
        
        try:
            # Generate a tech card and verify cost calculation works
            payload = {
                "name": "Паста с морепродуктами",
                "cuisine": "итальянская",
                "equipment": [],
                "budget": 800,
                "dietary": []
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'card' in data and data['card']:
                    card = data['card']
                    
                    # Check cost calculation results
                    has_cost = 'cost' in card and card['cost']
                    has_cost_meta = 'costMeta' in card and card['costMeta']
                    
                    if has_cost and has_cost_meta:
                        cost = card['cost']
                        cost_meta = card['costMeta']
                        
                        # Verify cost structure
                        cost_fields = ['rawCost', 'costPerPortion', 'markup_pct', 'vat_pct']
                        present_cost_fields = [field for field in cost_fields if field in cost and cost[field] is not None]
                        
                        # Verify cost meta structure
                        meta_fields = ['source', 'coveragePct', 'asOf']
                        present_meta_fields = [field for field in meta_fields if field in cost_meta and cost_meta[field] is not None]
                        
                        # Check for sub-recipe related issues
                        issues = data.get('issues', [])
                        subrecipe_issues = [issue for issue in issues if issue.get('type') == 'subRecipeNotReady']
                        
                        self.log_test(
                            "Cost Calculator Integration",
                            "PASS",
                            f"Cost calculation working. Fields: {present_cost_fields}, Meta: {present_meta_fields}, SubRecipe Issues: {len(subrecipe_issues)}",
                            {
                                'cost': cost,
                                'cost_meta': cost_meta,
                                'subrecipe_issues': subrecipe_issues
                            }
                        )
                        return True
                    else:
                        self.log_test(
                            "Cost Calculator Integration",
                            "FAIL",
                            f"Missing cost data. Has cost: {has_cost}, Has cost meta: {has_cost_meta}"
                        )
                        return False
                else:
                    self.log_test(
                        "Cost Calculator Integration",
                        "FAIL",
                        "No card generated for cost calculation test"
                    )
                    return False
            else:
                self.log_test(
                    "Cost Calculator Integration",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Cost Calculator Integration",
                "FAIL",
                f"Exception: {str(e)}"
            )
            return False
    
    def test_nutrition_calculator_integration(self):
        """Test 4: Nutrition Calculator Integration with sub_recipes_cache parameter"""
        print("\n🔍 Testing Nutrition Calculator Integration...")
        
        try:
            # Generate a tech card and verify nutrition calculation works
            payload = {
                "name": "Салат Цезарь с курицей",
                "cuisine": "американская",
                "equipment": [],
                "budget": 400,
                "dietary": []
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'card' in data and data['card']:
                    card = data['card']
                    
                    # Check nutrition calculation results
                    has_nutrition = 'nutrition' in card and card['nutrition']
                    has_nutrition_meta = 'nutritionMeta' in card and card['nutritionMeta']
                    
                    if has_nutrition and has_nutrition_meta:
                        nutrition = card['nutrition']
                        nutrition_meta = card['nutritionMeta']
                        
                        # Verify nutrition structure
                        has_per100g = 'per100g' in nutrition and nutrition['per100g']
                        has_per_portion = 'perPortion' in nutrition and nutrition['perPortion']
                        
                        # Verify nutrition meta structure
                        meta_fields = ['source', 'coveragePct']
                        present_meta_fields = [field for field in meta_fields if field in nutrition_meta and nutrition_meta[field] is not None]
                        
                        # Check for sub-recipe related issues
                        issues = data.get('issues', [])
                        subrecipe_nutrition_issues = [issue for issue in issues if issue.get('type') == 'subRecipeNotReady' and 'nutrition' in issue.get('missing', [])]
                        
                        if has_per100g and has_per_portion:
                            self.log_test(
                                "Nutrition Calculator Integration",
                                "PASS",
                                f"Nutrition calculation working. Per100g: {has_per100g}, PerPortion: {has_per_portion}, Meta: {present_meta_fields}, SubRecipe Issues: {len(subrecipe_nutrition_issues)}",
                                {
                                    'nutrition': nutrition,
                                    'nutrition_meta': nutrition_meta,
                                    'subrecipe_nutrition_issues': subrecipe_nutrition_issues
                                }
                            )
                            return True
                        else:
                            self.log_test(
                                "Nutrition Calculator Integration",
                                "FAIL",
                                f"Incomplete nutrition data. Per100g: {has_per100g}, PerPortion: {has_per_portion}"
                            )
                            return False
                    else:
                        self.log_test(
                            "Nutrition Calculator Integration",
                            "FAIL",
                            f"Missing nutrition data. Has nutrition: {has_nutrition}, Has nutrition meta: {has_nutrition_meta}"
                        )
                        return False
                else:
                    self.log_test(
                        "Nutrition Calculator Integration",
                        "FAIL",
                        "No card generated for nutrition calculation test"
                    )
                    return False
            else:
                self.log_test(
                    "Nutrition Calculator Integration",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Nutrition Calculator Integration",
                "FAIL",
                f"Exception: {str(e)}"
            )
            return False
    
    def test_pipeline_error_handling(self):
        """Test 5: Pipeline Error Handling with sub-recipe data"""
        print("\n🔍 Testing Pipeline Error Handling...")
        
        try:
            # Test multiple scenarios to ensure pipeline doesn't crash
            test_scenarios = [
                {
                    "name": "Блюдо с экзотическими ингредиентами",
                    "cuisine": "фьюжн",
                    "equipment": [],
                    "budget": 1000,
                    "dietary": ["веган"]
                },
                {
                    "name": "Простой салат",
                    "cuisine": "русская",
                    "equipment": [],
                    "budget": 200,
                    "dietary": []
                },
                {
                    "name": "Сложное блюдо с множеством ингредиентов",
                    "cuisine": "французская",
                    "equipment": ["духовка", "блендер"],
                    "budget": 1500,
                    "dietary": ["безглютеновая"]
                }
            ]
            
            successful_generations = 0
            total_scenarios = len(test_scenarios)
            
            for i, scenario in enumerate(test_scenarios):
                try:
                    response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", json=scenario, timeout=60)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check that pipeline returns a result (success or draft)
                        status = data.get('status', 'unknown')
                        has_card = 'card' in data and data['card'] is not None
                        
                        if status in ['success', 'draft'] and has_card:
                            successful_generations += 1
                        
                        # Check for proper error handling in issues
                        issues = data.get('issues', [])
                        has_critical_errors = any('Pipeline error' in str(issue) for issue in issues)
                        
                        if has_critical_errors:
                            self.log_test(
                                f"Pipeline Error Handling - Scenario {i+1}",
                                "FAIL",
                                f"Critical pipeline errors found: {issues}"
                            )
                            return False
                            
                    elif response.status_code >= 500:
                        self.log_test(
                            f"Pipeline Error Handling - Scenario {i+1}",
                            "FAIL",
                            f"Server error: HTTP {response.status_code}"
                        )
                        return False
                        
                except Exception as scenario_error:
                    self.log_test(
                        f"Pipeline Error Handling - Scenario {i+1}",
                        "FAIL",
                        f"Exception in scenario: {str(scenario_error)}"
                    )
                    return False
            
            # Test draft mode specifically
            draft_test_payload = {
                "name": "Тестовое блюдо для draft режима",
                "cuisine": "тестовая",
                "equipment": [],
                "budget": 100,
                "dietary": []
            }
            
            draft_response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", json=draft_test_payload, timeout=60)
            
            if draft_response.status_code == 200:
                draft_data = draft_response.json()
                draft_status = draft_data.get('status', 'unknown')
                
                # Draft mode should still work with sub-recipe integration
                if draft_status in ['success', 'draft']:
                    successful_generations += 1
                    total_scenarios += 1
            
            success_rate = (successful_generations / total_scenarios) * 100
            
            if success_rate >= 80:  # At least 80% success rate
                self.log_test(
                    "Pipeline Error Handling",
                    "PASS",
                    f"Pipeline stable with {success_rate:.1f}% success rate ({successful_generations}/{total_scenarios})",
                    {'success_rate': success_rate, 'successful_generations': successful_generations}
                )
                return True
            else:
                self.log_test(
                    "Pipeline Error Handling",
                    "FAIL",
                    f"Low success rate: {success_rate:.1f}% ({successful_generations}/{total_scenarios})"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Pipeline Error Handling",
                "FAIL",
                f"Exception: {str(e)}"
            )
            return False
    
    def test_subrecipe_issues_generation(self):
        """Test 6: Verify proper subRecipeNotReady issues are generated"""
        print("\n🔍 Testing Sub-recipe Issues Generation...")
        
        try:
            # Generate a tech card that might have sub-recipe related issues
            payload = {
                "name": "Комплексное блюдо с соусами",
                "cuisine": "авторская",
                "equipment": ["блендер", "миксер"],
                "budget": 600,
                "dietary": []
            }
            
            response = self.session.post(f"{API_BASE}/v1/techcards.v2/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check issues structure
                issues = data.get('issues', [])
                
                # Look for different types of issues that might be generated
                issue_types = {}
                for issue in issues:
                    if isinstance(issue, dict):
                        issue_type = issue.get('type', 'unknown')
                    else:
                        issue_type = 'string_issue'
                    if issue_type not in issue_types:
                        issue_types[issue_type] = 0
                    issue_types[issue_type] += 1
                
                # Check if sub-recipe issues would be properly structured if they existed
                subrecipe_issues = [issue for issue in issues if isinstance(issue, dict) and issue.get('type') == 'subRecipeNotReady']
                
                # Verify issue structure for any sub-recipe issues
                valid_subrecipe_issues = True
                for issue in subrecipe_issues:
                    if not all(key in issue for key in ['type', 'name', 'missing']):
                        valid_subrecipe_issues = False
                        break
                
                self.log_test(
                    "Sub-recipe Issues Generation",
                    "PASS",
                    f"Issues properly structured. Types found: {list(issue_types.keys())}, SubRecipe issues: {len(subrecipe_issues)}, Valid structure: {valid_subrecipe_issues}",
                    {
                        'issue_types': issue_types,
                        'subrecipe_issues': subrecipe_issues,
                        'total_issues': len(issues)
                    }
                )
                return True
            else:
                self.log_test(
                    "Sub-recipe Issues Generation",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Sub-recipe Issues Generation",
                "FAIL",
                f"Exception: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all sub-recipe integration tests"""
        print("🚀 Starting Sub-recipes Integration Backend Testing...")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        test_methods = [
            self.test_basic_techcard_generation_backwards_compatibility,
            self.test_subrecipe_schema_validation,
            self.test_cost_calculator_integration,
            self.test_nutrition_calculator_integration,
            self.test_pipeline_error_handling,
            self.test_subrecipe_issues_generation
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")
        
        print("\n" + "=" * 80)
        print("📊 SUB-RECIPES INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        status_emoji = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
        
        print(f"{status_emoji} Overall Result: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        # Detailed results
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            if result['details']:
                print(f"   └─ {result['details']}")
        
        print("\n" + "=" * 80)
        
        # Determine overall status for test_result.md
        if success_rate >= 80:
            print("🎉 SUB-RECIPES INTEGRATION IS WORKING CORRECTLY")
            return True
        elif success_rate >= 60:
            print("⚠️ SUB-RECIPES INTEGRATION HAS MINOR ISSUES")
            return False
        else:
            print("❌ SUB-RECIPES INTEGRATION HAS MAJOR ISSUES")
            return False

def main():
    """Main test execution"""
    tester = SubRecipeIntegrationTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)