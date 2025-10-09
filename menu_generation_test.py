#!/usr/bin/env python3
"""
Menu Generation Testing Suite
Testing menu generation functionality and data structure for beautiful display
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_generate_menu_endpoint():
    """Test POST /api/generate-menu endpoint structure and data"""
    print("🍽️ TESTING MENU GENERATION ENDPOINT")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Test 1: Generate menu with basic parameters as specified in review
    print("Test 1: POST /api/generate-menu with basic parameters")
    try:
        menu_request = {
            "user_id": user_id,
            "menu_profile": {
                "menuType": "restaurant",
                "dishCount": 10,  # 8-10 dishes as requested
                "averageCheck": "medium",
                "cuisineStyle": "european",
                "expectations": "Разнообразное меню для семейного ресторана",
                "targetAudience": "семьи с детьми",
                "useConstructor": False
            },
            "venue_profile": {
                "venue_name": "Семейный ресторан",
                "venue_type": "family_restaurant",
                "cuisine_type": "european",
                "average_check": "800"
            }
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/generate-menu",
            json=menu_request,
            timeout=180  # 3 minute timeout for menu generation
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                # Check for required structure
                menu_data = result.get("menu", {})
                categories = menu_data.get("categories", [])
                menu_id = result.get("menu_id")
                
                # Extract dishes from categories
                dishes = []
                for category in categories:
                    dishes.extend(category.get("dishes", []))
                
                log_test("Menu generation success", "PASS", 
                        f"Generated menu in {end_time - start_time:.2f}s")
                
                # Test structure requirements
                if categories:
                    log_test("Categories structure present", "PASS", 
                            f"Found {len(categories)} categories")
                    
                    # Print category details
                    for category in categories:
                        cat_name = category.get("category_name", "Unknown")
                        cat_dishes = category.get("dishes", [])
                        print(f"    Category '{cat_name}': {len(cat_dishes)} dishes")
                else:
                    log_test("Categories structure present", "FAIL", 
                            "No categories found in response")
                
                if dishes and len(dishes) >= 8:
                    log_test("Dishes count", "PASS", 
                            f"Generated {len(dishes)} dishes (requested 8-10)")
                else:
                    log_test("Dishes count", "FAIL", 
                            f"Generated {len(dishes)} dishes, expected 8-10")
                
                if menu_id:
                    log_test("Menu ID present", "PASS", 
                            f"Menu ID: {menu_id}")
                else:
                    log_test("Menu ID present", "FAIL", 
                            "No menu_id found for project linking")
                
                # Test dish structure for beautiful display
                print("    Analyzing dish structure for display requirements...")
                required_dish_fields = ["name", "description", "estimated_price", "estimated_cost"]
                optional_dish_fields = ["portion_size"]
                
                valid_dishes = 0
                missing_fields_summary = {}
                
                for i, dish in enumerate(dishes[:5]):  # Check first 5 dishes
                    dish_issues = []
                    
                    for field in required_dish_fields:
                        if field not in dish or not dish[field]:
                            dish_issues.append(field)
                            missing_fields_summary[field] = missing_fields_summary.get(field, 0) + 1
                    
                    if not dish_issues:
                        valid_dishes += 1
                    
                    print(f"    Dish {i+1}: {dish.get('name', 'NO NAME')}")
                    print(f"      - Description: {'✓' if dish.get('description') else '✗'}")
                    print(f"      - Estimated Price: {'✓' if dish.get('estimated_price') else '✗'}")
                    print(f"      - Estimated Cost: {'✓' if dish.get('estimated_cost') else '✗'}")
                    print(f"      - Portion Size: {'✓' if dish.get('portion_size') else '○'} (optional)")
                
                if valid_dishes == len(dishes[:5]):
                    log_test("Dish structure for display", "PASS", 
                            f"All checked dishes have required fields for beautiful display")
                else:
                    log_test("Dish structure for display", "FAIL", 
                            f"Only {valid_dishes}/{len(dishes[:5])} dishes have complete structure. Missing: {missing_fields_summary}")
                
                # Test family restaurant style
                family_keywords = ["семейн", "домашн", "традицион", "уютн", "детск"]
                menu_text = json.dumps(result, ensure_ascii=False).lower()
                found_keywords = [kw for kw in family_keywords if kw in menu_text]
                
                if found_keywords:
                    log_test("Family restaurant style verification", "PASS", 
                            f"Found family-style keywords: {found_keywords}")
                else:
                    log_test("Family restaurant style verification", "WARN", 
                            "No family restaurant keywords found in menu")
                
            else:
                log_test("Menu generation", "FAIL", 
                        f"Success=False: {result}")
        else:
            log_test("Menu generation", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("Menu generation", "FAIL", "Request timeout (>180s)")
    except Exception as e:
        log_test("Menu generation", "FAIL", f"Exception: {str(e)}")

def test_replace_dish_functionality():
    """Test /api/replace-dish functionality"""
    print("🔄 TESTING REPLACE DISH FUNCTIONALITY")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # First, we need to generate a menu to get dishes to replace
    print("Step 1: Generate a menu to get dishes for replacement")
    try:
        menu_request = {
            "user_id": user_id,
            "menu_profile": {
                "menuType": "restaurant",
                "dishCount": 8,
                "averageCheck": "medium",
                "cuisineStyle": "european",
                "expectations": "Разнообразное меню для семейного ресторана",
                "useConstructor": False
            },
            "venue_profile": {
                "venue_name": "Семейный ресторан",
                "venue_type": "family_restaurant"
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/generate-menu",
            json=menu_request,
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success") and result.get("menu"):
                menu_data = result.get("menu", {})
                categories = menu_data.get("categories", [])
                menu_id = result.get("menu_id")
                
                # Extract dishes from categories
                dishes = []
                for category in categories:
                    dishes.extend(category.get("dishes", []))
                
                if dishes:
                    # Pick the first dish to replace
                    dish_to_replace = dishes[0]
                    original_name = dish_to_replace.get("name", "Unknown")
                    
                    log_test("Menu generation for replacement test", "PASS", 
                            f"Generated menu with {len(dishes)} dishes, will replace: {original_name}")
                    
                    # Test 2: Replace dish functionality
                    print("Step 2: Test replace dish functionality")
                    
                    replace_request = {
                        "user_id": user_id,
                        "menu_id": menu_id,
                        "dish_name": original_name,  # Changed from dish_to_replace to dish_name
                        "replacement_prompt": "Замени это блюдо на что-то более легкое и диетическое для семейного ресторана"
                    }
                    
                    start_time = time.time()
                    replace_response = requests.post(
                        f"{BACKEND_URL}/replace-dish",
                        json=replace_request,
                        timeout=120
                    )
                    end_time = time.time()
                    
                    if replace_response.status_code == 200:
                        replace_result = replace_response.json()
                        
                        if replace_result.get("success"):
                            new_dish_name = replace_result.get("new_dish", "Unknown")
                            tech_card_content = replace_result.get("content", "")
                            
                            log_test("Replace dish functionality", "PASS", 
                                    f"Successfully replaced '{original_name}' with '{new_dish_name}' in {end_time - start_time:.2f}s")
                            
                            # Check if new dish has content (tech card)
                            if tech_card_content and len(tech_card_content) > 100:
                                log_test("Replaced dish content", "PASS", 
                                        f"New dish has tech card content ({len(tech_card_content)} chars)")
                            else:
                                log_test("Replaced dish content", "FAIL", 
                                        "New dish missing or insufficient tech card content")
                            
                            # Check if replacement is actually different
                            if new_dish_name.lower() != original_name.lower():
                                log_test("Dish replacement uniqueness", "PASS", 
                                        "New dish is different from original")
                            else:
                                log_test("Dish replacement uniqueness", "WARN", 
                                        "New dish has same name as original")
                            
                        else:
                            log_test("Replace dish functionality", "FAIL", 
                                    f"Replace failed: {replace_result}")
                    else:
                        log_test("Replace dish functionality", "FAIL", 
                                f"HTTP {replace_response.status_code}: {replace_response.text}")
                        
                else:
                    log_test("Menu generation for replacement test", "FAIL", 
                            "No dishes in generated menu")
            else:
                log_test("Menu generation for replacement test", "FAIL", 
                        "Menu generation failed or no dishes returned")
        else:
            log_test("Menu generation for replacement test", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Replace dish functionality test", "FAIL", f"Exception: {str(e)}")

def test_menu_data_completeness():
    """Test that menu data includes all fields needed for beautiful display"""
    print("🎨 TESTING MENU DATA COMPLETENESS FOR BEAUTIFUL DISPLAY")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    print("Test: Generate menu and verify all display data is present")
    try:
        menu_request = {
            "user_id": user_id,
            "menu_profile": {
                "menuType": "restaurant",
                "dishCount": 8,
                "averageCheck": "medium",
                "cuisineStyle": "european",
                "expectations": "Разнообразное меню для семейного ресторана с красивой подачей",
                "useConstructor": False
            },
            "venue_profile": {
                "venue_name": "Семейный ресторан",
                "venue_type": "family_restaurant"
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/generate-menu",
            json=menu_request,
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                menu_data = result.get("menu", {})
                categories = menu_data.get("categories", [])
                
                # Extract dishes from categories
                dishes = []
                for category in categories:
                    dishes.extend(category.get("dishes", []))
                
                print(f"    Analyzing {len(dishes)} dishes for display completeness...")
                
                # Detailed analysis of each dish
                complete_dishes = 0
                display_issues = []
                
                for i, dish in enumerate(dishes):
                    dish_name = dish.get("name", f"Dish {i+1}")
                    issues = []
                    
                    # Check required fields
                    if not dish.get("name"):
                        issues.append("missing name")
                    if not dish.get("description"):
                        issues.append("missing description")
                    if not dish.get("estimated_price"):
                        issues.append("missing estimated_price")
                    if not dish.get("estimated_cost"):
                        issues.append("missing estimated_cost")
                    
                    # Check data quality
                    if dish.get("description") and len(dish["description"]) < 20:
                        issues.append("description too short")
                    
                    if dish.get("estimated_price"):
                        try:
                            # Try to extract numeric value
                            price_str = str(dish["estimated_price"])
                            if not any(char.isdigit() for char in price_str):
                                issues.append("price not numeric")
                        except:
                            issues.append("price format error")
                    
                    if not issues:
                        complete_dishes += 1
                    else:
                        display_issues.append(f"{dish_name}: {', '.join(issues)}")
                    
                    print(f"    {i+1}. {dish_name}")
                    print(f"       Name: {'✓' if dish.get('name') else '✗'}")
                    print(f"       Description: {'✓' if dish.get('description') and len(dish['description']) >= 20 else '✗'}")
                    print(f"       Price: {'✓' if dish.get('estimated_price') else '✗'}")
                    print(f"       Cost: {'✓' if dish.get('estimated_cost') else '✗'}")
                    print(f"       Portion: {'✓' if dish.get('portion_size') else '○'}")
                    print(f"       Category: {'✓' if dish.get('category') else '○'}")
                
                completion_rate = (complete_dishes / len(dishes)) * 100 if dishes else 0
                
                if completion_rate >= 90:
                    log_test("Menu data completeness", "PASS", 
                            f"{completion_rate:.1f}% dishes complete ({complete_dishes}/{len(dishes)})")
                elif completion_rate >= 70:
                    log_test("Menu data completeness", "WARN", 
                            f"{completion_rate:.1f}% dishes complete ({complete_dishes}/{len(dishes)})")
                else:
                    log_test("Menu data completeness", "FAIL", 
                            f"Only {completion_rate:.1f}% dishes complete ({complete_dishes}/{len(dishes)})")
                
                if display_issues:
                    print("    Issues found:")
                    for issue in display_issues[:5]:  # Show first 5 issues
                        print(f"      - {issue}")
                
                # Test category organization
                if categories:
                    log_test("Category organization", "PASS", 
                            f"Menu organized into {len(categories)} categories")
                    
                    for category in categories:
                        cat_name = category.get("category_name", "Unknown")
                        cat_dishes = category.get("dishes", [])
                        print(f"    Category '{cat_name}': {len(cat_dishes)} dishes")
                else:
                    log_test("Category organization", "FAIL", 
                            "No category organization found")
                
            else:
                log_test("Menu data completeness test", "FAIL", 
                        f"Menu generation failed: {result}")
        else:
            log_test("Menu data completeness test", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Menu data completeness test", "FAIL", f"Exception: {str(e)}")

def main():
    """Run all menu generation tests"""
    print("🧪 MENU GENERATION TESTING SUITE")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User: test_user_12345")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: Generate Menu Endpoint
        test_generate_menu_endpoint()
        
        # Test 2: Replace Dish Functionality  
        test_replace_dish_functionality()
        
        # Test 3: Menu Data Completeness for Display
        test_menu_data_completeness()
        
        print("🏁 ALL MENU GENERATION TESTS COMPLETED")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()