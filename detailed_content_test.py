#!/usr/bin/env python3
"""
Detailed content analysis to see what's actually in the tech cards
"""

import requests
import json
import re

BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_single_tech_card():
    """Generate a single tech card and analyze its full content"""
    
    request_data = {
        "dish_name": "Брускетта с помидорами и базиликом",
        "user_id": "test_user_detailed_12345"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-tech-card",
            json=request_data,
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return
        
        data = response.json()
        content = data.get("tech_card", "")
        
        print("🔍 FULL TECH CARD CONTENT:")
        print("=" * 80)
        print(content)
        print("=" * 80)
        
        # Look for specific sections
        print("\n🔍 SECTION ANALYSIS:")
        
        # Find storage section
        storage_match = re.search(r"\*\*заготовки и хранение:\*\*(.*?)(?=\*\*|$)", content, re.IGNORECASE | re.DOTALL)
        if storage_match:
            storage_content = storage_match.group(1).strip()
            print(f"\n📦 ЗАГОТОВКИ И ХРАНЕНИЕ section:")
            print(f"'{storage_content}'")
            print(f"Length: {len(storage_content)} characters")
        else:
            print("\n❌ ЗАГОТОВКИ И ХРАНЕНИЕ section not found")
        
        # Find chef tips section
        chef_match = re.search(r"\*\*особенности и советы от шефа:\*\*(.*?)(?=\*\*|$)", content, re.IGNORECASE | re.DOTALL)
        if not chef_match:
            chef_match = re.search(r"\*\*советы от шефа:\*\*(.*?)(?=\*\*|$)", content, re.IGNORECASE | re.DOTALL)
        
        if chef_match:
            chef_content = chef_match.group(1).strip()
            print(f"\n👨‍🍳 СОВЕТЫ ОТ ШЕФА section:")
            print(f"'{chef_content}'")
            print(f"Length: {len(chef_content)} characters")
        else:
            print("\n❌ СОВЕТЫ ОТ ШЕФА section not found")
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_single_tech_card()