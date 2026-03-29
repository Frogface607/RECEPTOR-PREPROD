#!/usr/bin/env python3
"""
Debug Menu Generation API Response
"""

import requests
import json
import time
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def debug_menu_generation():
    """Debug what's actually returned by the menu generation API"""
    print("🔍 DEBUGGING MENU GENERATION API")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    menu_request = {
        "user_id": user_id,
        "menu_type": "business_lunch",
        "expectations": "Simple pasta and salad dishes for office workers",
        "dish_count": 4
    }
    
    print(f"Request: {json.dumps(menu_request, indent=2, ensure_ascii=False)}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-simple-menu", json=menu_request, timeout=120)
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"Response JSON Keys: {list(response_data.keys())}")
                print(f"Full Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print(f"Response Text (not JSON): {response.text}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    debug_menu_generation()