#!/usr/bin/env python3
"""
Quick test for replace dish functionality after bug fix
"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def log_test(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_replace_dish_fix():
    """Test the replace dish endpoint after fixing the regex bug"""
    log_test("🔧 TESTING REPLACE DISH FIX")
    
    user_id = "test_user_12345"
    
    # Create a simple menu first
    log_test("Creating test menu...")
    menu_request = {
        "user_id": user_id,
        "menu_profile": {
            "menuType": "restaurant",
            "dishCount": 2,
            "averageCheck": "medium",
            "cuisineStyle": "italian"
        },
        "venue_profile": {
            "venue_name": "Test Fix Restaurant",
            "venue_type": "family_restaurant",
            "average_check": 800
        }
    }
    
    menu_response = requests.post(f"{BACKEND_URL}/generate-menu", json=menu_request, timeout=60)
    if menu_response.status_code != 200:
        log_test(f"❌ Menu creation failed: {menu_response.status_code}")
        return False
        
    menu_id = menu_response.json().get("menu_id")
    log_test(f"✅ Menu created: {menu_id}")
    
    # Test replace dish
    log_test("Testing dish replacement...")
    replace_request = {
        "user_id": user_id,
        "menu_id": menu_id,
        "dish_name": "Паста Карбонара",
        "category": "Основные блюда",
        "replacement_prompt": "Make it vegetarian and spicier"
    }
    
    start_time = time.time()
    replace_response = requests.post(f"{BACKEND_URL}/replace-dish", json=replace_request, timeout=120)
    replace_time = time.time() - start_time
    
    log_test(f"Replace response: {replace_response.status_code} (took {replace_time:.2f}s)")
    
    if replace_response.status_code != 200:
        log_test(f"❌ Replace failed: {replace_response.text}")
        return False
    
    replace_data = replace_response.json()
    log_test(f"✅ Original dish: {replace_data.get('original_dish')}")
    log_test(f"✅ New dish: {replace_data.get('new_dish')}")
    log_test(f"✅ Content length: {len(replace_data.get('content', ''))} characters")
    
    return True

if __name__ == "__main__":
    success = test_replace_dish_fix()
    print(f"\n🎯 RESULT: {'PASSED' if success else 'FAILED'}")