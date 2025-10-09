#!/usr/bin/env python3
"""
Setup test user with PRO subscription for menu generation testing
"""

import requests
import json

BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def setup_test_user():
    """Setup test user with PRO subscription"""
    user_id = "test_user_12345"
    
    print("Setting up test user with PRO subscription...")
    
    # Try to upgrade subscription to PRO
    try:
        upgrade_request = {
            "subscription_plan": "pro"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/upgrade-subscription/{user_id}",
            json=upgrade_request
        )
        
        if response.status_code == 200:
            print("✅ Test user upgraded to PRO subscription")
            return True
        elif response.status_code == 404:
            print("⚠️ Test user not found, will be auto-created during testing")
            return True
        else:
            print(f"❌ Failed to upgrade subscription: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up test user: {str(e)}")
        return False

if __name__ == "__main__":
    setup_test_user()