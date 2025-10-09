#!/usr/bin/env python3
"""
Check tech card content format
"""
import requests
import json

def test_tech_card_content():
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    # Register user
    data = {
        "email": "format_test@example.com",
        "name": "Format Test User",
        "city": "moskva"
    }
    
    response = requests.post(f"{base_url}/register", json=data, timeout=30)
    if response.status_code == 200:
        user_data = response.json()
        user_id = user_data["id"]
        print(f"✅ User registered: {user_id}")
    else:
        print(f"❌ Registration failed: {response.status_code}")
        return
    
    # Generate tech card
    data = {
        "dish_name": "Паста Карбонара",
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/generate-tech-card", json=data, timeout=60)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            tech_card = result["tech_card"]
            print("✅ Tech card generated successfully")
            print("=" * 80)
            print("TECH CARD CONTENT:")
            print("=" * 80)
            print(tech_card)
            print("=" * 80)
            
            # Check for golden prompt elements
            golden_elements = [
                "💸 Себестоимость",
                "КБЖУ",
                "**Название:**",
                "**Ингредиенты:**",
                "**Пошаговый рецепт:**"
            ]
            
            print("\nGOLDEN PROMPT ELEMENTS CHECK:")
            for element in golden_elements:
                if element in tech_card:
                    print(f"✅ Found: {element}")
                else:
                    print(f"❌ Missing: {element}")
        else:
            print("❌ Tech card generation failed")
    else:
        print(f"❌ Tech card generation request failed: {response.status_code}")

if __name__ == "__main__":
    test_tech_card_content()