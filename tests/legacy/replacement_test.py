#!/usr/bin/env python3
"""
Test dish replacement functionality
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

def test_dish_replacement():
    """Test dish replacement returns full object"""
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

if __name__ == "__main__":
    test_dish_replacement()