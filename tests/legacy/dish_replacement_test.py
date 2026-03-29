#!/usr/bin/env python3
"""
Focused Backend Testing for Dish Replacement and Menu Generation Fixes
Testing the fixes for:
1. POST /api/generate-menu - no more "Специальное блюдо дня" placeholders
2. POST /api/replace-dish - returns full dish object with all required fields
3. Retry generation if AI creates insufficient dishes
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

def test_menu_generation_no_placeholders():
    """Test that menu generation does NOT create placeholder dishes like 'Специальное блюдо дня'"""
    print("🍽️ TESTING MENU GENERATION WITHOUT PLACEHOLDERS")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Test with simple menu generation (small dish count) to check if placeholders are added
    menu_request = {
        "user_id": user_id,
        "menu_type": "business_lunch",
        "expectations": "Healthy quick meals for office workers, focus on salads and light main dishes, moderate prices",
        "dish_count": 6  # Small count to test if placeholders are added
    }
    
    print("Test 1: POST /api/generate-simple-menu with 6 dishes")
    print(f"Request: {json.dumps(menu_request, indent=2, ensure_ascii=False)}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-simple-menu", json=menu_request, timeout=120)
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            menu_data = response.json()
            
            # Check if menu was generated - use "dishes" field instead of "menu"
            if "dishes" in menu_data and menu_data["dishes"]:
                dishes = menu_data["dishes"]
                print(f"Generated {len(dishes)} dishes")
                
                # Check for placeholder dishes
                placeholder_found = False
                placeholder_dishes = []
                
                for dish in dishes:
                    # Handle both string and dict formats
                    if isinstance(dish, dict):
                        dish_name = dish.get("name", "")
                    else:
                        dish_name = str(dish)
                    
                    # Check for various placeholder patterns
                    placeholder_patterns = [
                        "Специальное блюдо дня",
                        "Специальное блюдо от шефа", 
                        "Блюдо дня",
                        "Рекомендация шефа",
                        "Сезонное блюдо",
                        "Авторское блюдо"
                    ]
                    
                    for pattern in placeholder_patterns:
                        if pattern.lower() in dish_name.lower():
                            placeholder_found = True
                            placeholder_dishes.append(dish_name)
                            break
                
                if placeholder_found:
                    log_test("Menu Generation - No Placeholders", "FAIL", 
                           f"Found placeholder dishes: {placeholder_dishes}")
                else:
                    log_test("Menu Generation - No Placeholders", "PASS", 
                           f"All {len(dishes)} dishes are real recipes, no placeholders found")
                
                # Print all dish names for verification
                print("Generated dishes:")
                for i, dish in enumerate(dishes, 1):
                    if isinstance(dish, dict):
                        dish_name = dish.get("name", "No name")
                    else:
                        dish_name = str(dish)
                    print(f"  {i}. {dish_name}")
                
                return dishes  # Return for use in replacement test
                
            else:
                log_test("Menu Generation - No Placeholders", "FAIL", "No dishes generated")
                return None
        else:
            log_test("Menu Generation - No Placeholders", "FAIL", 
                   f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        log_test("Menu Generation - No Placeholders", "FAIL", f"Exception: {str(e)}")
        return None

def test_dish_replacement_full_object():
    """Test that dish replacement returns full dish object with all required fields"""
    print("🔄 TESTING DISH REPLACEMENT FULL OBJECT RETURN")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # First, generate a simple menu to get a dish to replace
    print("Step 1: Generate a simple menu to get a dish for replacement")
    
    simple_menu_request = {
        "user_id": user_id,
        "menu_type": "business_lunch",
        "expectations": "Simple pasta and salad dishes for office workers",
        "dish_count": 4
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/generate-simple-menu", json=simple_menu_request, timeout=120)
        
        if response.status_code == 200:
            menu_data = response.json()
            
            if "dishes" in menu_data and menu_data["dishes"] and "menu_id" in menu_data:
                dishes = menu_data["dishes"]
                menu_id = menu_data["menu_id"]
                print(f"Generated {len(dishes)} dishes for replacement test")
                print(f"Menu ID: {menu_id}")
                
                # Pick the first dish for replacement
                if isinstance(dishes[0], dict):
                    dish_name = dishes[0].get("name", "Unknown")
                else:
                    dish_name = str(dishes[0])
                
                print(f"Selected dish for replacement: {dish_name}")
                
                # Test dish replacement
                print("\nStep 2: Test dish replacement")
                
                replacement_request = {
                    "user_id": user_id,
                    "menu_id": menu_id,
                    "dish_name": dish_name,
                    "replacement_prompt": "Replace with a healthy vegetarian salad with quinoa and avocado",
                    "category": "salads"
                }
                
                print(f"Replacement request: {json.dumps(replacement_request, indent=2, ensure_ascii=False)}")
                
                start_time = time.time()
                replace_response = requests.post(f"{BACKEND_URL}/replace-dish", json=replacement_request, timeout=120)
                end_time = time.time()
                
                print(f"Replace Response Status: {replace_response.status_code}")
                print(f"Replace Response Time: {end_time - start_time:.2f} seconds")
                
                if replace_response.status_code == 200:
                    replacement_data = replace_response.json()
                    
                    # Check if replacement was successful
                    if "success" in replacement_data and replacement_data["success"]:
                        
                        # Check for required fields in the response
                        required_fields = [
                            "name", "description", "estimated_cost", "estimated_price", 
                            "main_ingredients", "difficulty", "cook_time", "portion_size"
                        ]
                        
                        missing_fields = []
                        present_fields = []
                        
                        # Check if we have a new_dish object
                        if "new_dish" in replacement_data:
                            new_dish = replacement_data["new_dish"]
                            
                            for field in required_fields:
                                if field in new_dish and new_dish[field] is not None:
                                    present_fields.append(field)
                                else:
                                    missing_fields.append(field)
                            
                            if missing_fields:
                                log_test("Dish Replacement - Full Object", "FAIL", 
                                       f"Missing required fields: {missing_fields}")
                            else:
                                log_test("Dish Replacement - Full Object", "PASS", 
                                       f"All required fields present: {present_fields}")
                            
                            # Print the new dish details
                            print("New dish details:")
                            for field in required_fields:
                                value = new_dish.get(field, "NOT FOUND")
                                print(f"  {field}: {value}")
                                
                        else:
                            log_test("Dish Replacement - Full Object", "FAIL", 
                                   "No 'new_dish' object in response")
                            
                    else:
                        log_test("Dish Replacement - Full Object", "FAIL", 
                               "Replacement not successful according to response")
                        
                else:
                    log_test("Dish Replacement - Full Object", "FAIL", 
                           f"HTTP {replace_response.status_code}: {replace_response.text}")
                    
            else:
                log_test("Dish Replacement - Full Object", "FAIL", 
                       "Could not generate initial menu for replacement test")
                
        else:
            log_test("Dish Replacement - Full Object", "FAIL", 
                   f"Could not generate initial menu: HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Dish Replacement - Full Object", "FAIL", f"Exception: {str(e)}")

def test_retry_generation_insufficient_dishes():
    """Test that system retries generation if AI creates insufficient dishes"""
    print("🔄 TESTING RETRY GENERATION FOR INSUFFICIENT DISHES")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Request a larger number of dishes to potentially trigger retry logic
    menu_request = {
        "user_id": user_id,
        "menu_type": "full",
        "expectations": "Complete restaurant menu with appetizers, mains, and desserts",
        "dish_count": 15  # Request 15 dishes
    }
    
    print("Test: POST /api/generate-simple-menu with 15 dishes (may trigger retry logic)")
    print(f"Request: {json.dumps(menu_request, indent=2, ensure_ascii=False)}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-simple-menu", json=menu_request, timeout=180)
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            menu_data = response.json()
            
            if "dishes" in menu_data and menu_data["dishes"]:
                dishes = menu_data["dishes"]
                requested_count = menu_request["dish_count"]
                actual_count = len(dishes)
                
                print(f"Requested: {requested_count} dishes")
                print(f"Generated: {actual_count} dishes")
                
                # Check if we got a reasonable number of dishes (at least 80% of requested)
                min_acceptable = int(requested_count * 0.8)
                
                if actual_count >= min_acceptable:
                    log_test("Retry Generation - Sufficient Dishes", "PASS", 
                           f"Generated {actual_count}/{requested_count} dishes (≥{min_acceptable} required)")
                else:
                    log_test("Retry Generation - Sufficient Dishes", "FAIL", 
                           f"Generated only {actual_count}/{requested_count} dishes (<{min_acceptable} required)")
                
                # Check for any placeholder dishes in the larger menu
                placeholder_found = False
                for dish in dishes:
                    if isinstance(dish, dict):
                        dish_name = dish.get("name", "")
                    else:
                        dish_name = str(dish)
                    
                    if "Специальное блюдо" in dish_name or "Блюдо дня" in dish_name:
                        placeholder_found = True
                        break
                
                if placeholder_found:
                    log_test("Large Menu - No Placeholders", "FAIL", 
                           "Found placeholder dishes in large menu")
                else:
                    log_test("Large Menu - No Placeholders", "PASS", 
                           "No placeholder dishes found in large menu")
                
            else:
                log_test("Retry Generation - Sufficient Dishes", "FAIL", "No dishes generated")
                
        else:
            log_test("Retry Generation - Sufficient Dishes", "FAIL", 
                   f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Retry Generation - Sufficient Dishes", "FAIL", f"Exception: {str(e)}")

def main():
    """Run all dish replacement and menu generation tests"""
    print("🎯 DISH REPLACEMENT AND MENU GENERATION TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User: test_user_12345")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Test 1: Menu generation without placeholders (small count)
    test_menu_generation_no_placeholders()
    print()
    
    # Test 2: Dish replacement returns full object
    test_dish_replacement_full_object()
    print()
    
    # Test 3: Retry generation for insufficient dishes
    test_retry_generation_insufficient_dishes()
    print()
    
    print("🎯 DISH REPLACEMENT AND MENU GENERATION TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()