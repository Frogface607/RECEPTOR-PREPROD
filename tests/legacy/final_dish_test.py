#!/usr/bin/env python3
"""
Final comprehensive test for dish replacement and menu generation fixes
"""

import requests
import json
import time
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

def main():
    """Run comprehensive tests for the review requirements"""
    print("🎯 COMPREHENSIVE DISH REPLACEMENT AND MENU GENERATION TESTING")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User: test_user_12345")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    user_id = "test_user_12345"
    
    # Test 1: Menu generation with small count - no placeholders
    print("🍽️ TEST 1: MENU GENERATION WITHOUT PLACEHOLDERS (SMALL COUNT)")
    print("=" * 60)
    
    menu_request = {
        "user_id": user_id,
        "menu_type": "business_lunch",
        "expectations": "Healthy quick meals for office workers, focus on salads and light main dishes, moderate prices",
        "dish_count": 6  # Small count to test if placeholders are added
    }
    
    print(f"Request: {json.dumps(menu_request, indent=2, ensure_ascii=False)}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-simple-menu", json=menu_request, timeout=120)
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            menu_data = response.json()
            
            if "dishes" in menu_data and menu_data["dishes"]:
                dishes = menu_data["dishes"]
                print(f"Generated {len(dishes)} dishes")
                
                # Check for placeholder dishes
                placeholder_found = False
                placeholder_dishes = []
                
                for dish in dishes:
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
                    log_test("Small Menu - No Placeholders", "FAIL", 
                           f"Found placeholder dishes: {placeholder_dishes}")
                else:
                    log_test("Small Menu - No Placeholders", "PASS", 
                           f"All {len(dishes)} dishes are real recipes, no placeholders found")
                
                # Print first few dish names for verification
                print("Sample generated dishes:")
                for i, dish in enumerate(dishes[:5], 1):
                    if isinstance(dish, dict):
                        dish_name = dish.get("name", "No name")
                    else:
                        dish_name = str(dish)
                    print(f"  {i}. {dish_name}")
                
                # Use this menu for replacement test
                menu_id = menu_data.get("menu_id")
                first_dish = dishes[0]
                
                if menu_id and first_dish:
                    # Test 2: Dish replacement with full object return
                    print("\n🔄 TEST 2: DISH REPLACEMENT FULL OBJECT RETURN")
                    print("=" * 60)
                    
                    if isinstance(first_dish, dict):
                        dish_name = first_dish.get("name", "Unknown")
                    else:
                        dish_name = str(first_dish)
                    
                    print(f"Selected dish for replacement: {dish_name}")
                    
                    replacement_request = {
                        "user_id": user_id,
                        "menu_id": menu_id,
                        "dish_name": dish_name,
                        "replacement_prompt": "Replace with a healthy vegetarian salad with quinoa and avocado",
                        "category": "salads"
                    }
                    
                    print(f"Replacement request: {json.dumps(replacement_request, indent=2, ensure_ascii=False)}")
                    
                    try:
                        start_time = time.time()
                        replace_response = requests.post(f"{BACKEND_URL}/replace-dish", json=replacement_request, timeout=120)
                        end_time = time.time()
                        
                        print(f"Replace Response Status: {replace_response.status_code}")
                        print(f"Replace Response Time: {end_time - start_time:.2f} seconds")
                        
                        if replace_response.status_code == 200:
                            replacement_data = replace_response.json()
                            
                            if "success" in replacement_data and replacement_data["success"]:
                                
                                # Check for required fields in the response
                                required_fields = [
                                    "name", "description", "estimated_cost", "estimated_price", 
                                    "main_ingredients", "difficulty", "cook_time", "portion_size"
                                ]
                                
                                missing_fields = []
                                present_fields = []
                                
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
                                    
                                    # Print key new dish details
                                    print("New dish details:")
                                    print(f"  name: {new_dish.get('name', 'NOT FOUND')}")
                                    print(f"  description: {new_dish.get('description', 'NOT FOUND')[:100]}...")
                                    print(f"  estimated_cost: {new_dish.get('estimated_cost', 'NOT FOUND')}")
                                    print(f"  estimated_price: {new_dish.get('estimated_price', 'NOT FOUND')}")
                                    print(f"  main_ingredients: {new_dish.get('main_ingredients', 'NOT FOUND')}")
                                    print(f"  difficulty: {new_dish.get('difficulty', 'NOT FOUND')}")
                                    print(f"  cook_time: {new_dish.get('cook_time', 'NOT FOUND')}")
                                    print(f"  portion_size: {new_dish.get('portion_size', 'NOT FOUND')}")
                                        
                                else:
                                    log_test("Dish Replacement - Full Object", "FAIL", 
                                           "No 'new_dish' object in response")
                                    
                            else:
                                log_test("Dish Replacement - Full Object", "FAIL", 
                                       "Replacement not successful according to response")
                                
                        else:
                            log_test("Dish Replacement - Full Object", "FAIL", 
                                   f"HTTP {replace_response.status_code}: {replace_response.text}")
                            
                    except Exception as e:
                        log_test("Dish Replacement - Full Object", "FAIL", f"Exception: {str(e)}")
                
            else:
                log_test("Small Menu - No Placeholders", "FAIL", "No dishes generated")
                
        else:
            log_test("Small Menu - No Placeholders", "FAIL", 
                   f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Small Menu - No Placeholders", "FAIL", f"Exception: {str(e)}")
    
    # Test 3: Larger menu generation to test retry logic
    print("\n🔄 TEST 3: LARGER MENU GENERATION (RETRY LOGIC)")
    print("=" * 60)
    
    large_menu_request = {
        "user_id": user_id,
        "menu_type": "full",
        "expectations": "Complete restaurant menu with appetizers, mains, and desserts",
        "dish_count": 15  # Request 15 dishes
    }
    
    print(f"Request: {json.dumps(large_menu_request, indent=2, ensure_ascii=False)}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-simple-menu", json=large_menu_request, timeout=180)
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            menu_data = response.json()
            
            if "dishes" in menu_data and menu_data["dishes"]:
                dishes = menu_data["dishes"]
                requested_count = large_menu_request["dish_count"]
                actual_count = len(dishes)
                
                print(f"Requested: {requested_count} dishes")
                print(f"Generated: {actual_count} dishes")
                
                # Check if we got a reasonable number of dishes (at least 80% of requested)
                min_acceptable = int(requested_count * 0.8)
                
                if actual_count >= min_acceptable:
                    log_test("Large Menu - Sufficient Dishes", "PASS", 
                           f"Generated {actual_count}/{requested_count} dishes (≥{min_acceptable} required)")
                else:
                    log_test("Large Menu - Sufficient Dishes", "FAIL", 
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
                log_test("Large Menu - Sufficient Dishes", "FAIL", "No dishes generated")
                
        else:
            log_test("Large Menu - Sufficient Dishes", "FAIL", 
                   f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        log_test("Large Menu - Sufficient Dishes", "FAIL", f"Exception: {str(e)}")
    
    print("\n🎯 COMPREHENSIVE TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()