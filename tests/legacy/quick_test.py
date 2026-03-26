#!/usr/bin/env python3
"""
Quick test for menu generation without placeholders
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

if __name__ == "__main__":
    test_menu_generation_no_placeholders()