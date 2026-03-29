#!/usr/bin/env python3
"""
Detailed test for FINANCES feature to examine the full response
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def main():
    """Test the FINANCES feature with detailed output"""
    print("🔍 DETAILED FINANCES FEATURE ANALYSIS")
    print("=" * 60)
    
    user_id = "test_user_12345"
    
    # Generate tech card
    tech_card_request = {
        "user_id": user_id,
        "dish_name": "Паста Карбонара на 4 порции"
    }
    
    print("📋 Generating tech card...")
    response = requests.post(f"{BACKEND_URL}/generate-tech-card", json=tech_card_request, timeout=60)
    
    if response.status_code != 200:
        print(f"❌ Tech card generation failed: {response.status_code}")
        return
        
    tech_card_content = response.json().get("tech_card", "")
    print(f"✅ Tech card generated ({len(tech_card_content)} chars)")
    
    # Test FINANCES analysis
    finances_request = {
        "user_id": user_id,
        "tech_card": tech_card_content
    }
    
    print("\n💰 Testing FINANCES analysis...")
    response = requests.post(f"{BACKEND_URL}/analyze-finances", json=finances_request, timeout=60)
    
    if response.status_code != 200:
        print(f"❌ FINANCES API failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    finances_data = response.json()
    analysis = finances_data.get("analysis", {})
    
    print("\n📊 FULL ANALYSIS RESPONSE:")
    print("=" * 50)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    # Detailed verification
    print("\n🔍 DETAILED VERIFICATION:")
    print("=" * 50)
    
    total_cost = analysis.get("total_cost", 0)
    ingredient_costs = analysis.get("ingredient_costs", [])
    cost_verification = analysis.get("cost_verification", {})
    
    print(f"📊 Total Cost: {total_cost}₽")
    print(f"📊 Number of Ingredients: {len(ingredient_costs)}")
    
    # Calculate sum manually
    manual_sum = 0
    print("\n🥘 INGREDIENT BREAKDOWN:")
    for ingredient in ingredient_costs:
        name = ingredient.get("ingredient", "")
        quantity = ingredient.get("quantity", "")
        cost = float(ingredient.get("total_cost", 0))
        manual_sum += cost
        print(f"   {name}: {quantity} = {cost}₽")
    
    print(f"\n🧮 Manual Sum: {manual_sum}₽")
    print(f"🧮 Reported Total: {total_cost}₽")
    print(f"🧮 Cost Verification: {cost_verification}")
    
    # Check if calculations match
    if abs(manual_sum - total_cost) < 0.01:
        print("✅ CALCULATIONS MATCH - FEATURE IS WORKING CORRECTLY!")
    else:
        print("❌ CALCULATION MISMATCH - THERE'S STILL AN ISSUE")
        print(f"   Difference: {abs(manual_sum - total_cost):.2f}₽")

if __name__ == "__main__":
    main()