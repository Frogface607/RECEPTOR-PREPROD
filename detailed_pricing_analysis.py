#!/usr/bin/env python3
"""
Detailed Pricing Analysis - July 2025
Analyzing the specific pricing issues found in tech cards
"""

import requests
import json
import re

BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def analyze_tech_card_pricing(dish_name):
    """Analyze pricing in a specific tech card"""
    print(f"\n🔍 DETAILED ANALYSIS: {dish_name}")
    print("=" * 60)
    
    test_user_id = "test_user_12345"
    
    try:
        tech_card_request = {
            "user_id": test_user_id,
            "dish_name": dish_name
        }
        
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", 
                               json=tech_card_request, timeout=90)
        
        if response.status_code != 200:
            print(f"❌ Failed to generate tech card: {response.status_code}")
            return
        
        result = response.json()
        tech_card_content = result.get("tech_card", "")
        
        print(f"📄 Tech card length: {len(tech_card_content)} characters")
        
        # Extract ingredients section
        ingredients_match = re.search(r'\*\*Ингредиенты:\*\*(.*?)\*\*', tech_card_content, re.DOTALL)
        if ingredients_match:
            ingredients_section = ingredients_match.group(1)
            print("\n📋 INGREDIENTS SECTION:")
            print(ingredients_section.strip())
        
        # Extract cost section
        cost_match = re.search(r'\*\*Себестоимость:\*\*(.*?)(?:\*\*|$)', tech_card_content, re.DOTALL)
        if cost_match:
            cost_section = cost_match.group(1)
            print("\n💰 COST SECTION:")
            print(cost_section.strip())
        
        # Find all prices in the content
        all_prices = re.findall(r'(\d+(?:\.\d+)?)\s*₽', tech_card_content)
        prices = [float(p) for p in all_prices]
        
        print(f"\n📊 ALL PRICES FOUND: {sorted(prices)}")
        print(f"💰 Price range: {min(prices):.2f}₽ - {max(prices):.2f}₽")
        
        # Categorize prices
        very_low = [p for p in prices if p < 1]
        low = [p for p in prices if 1 <= p < 10]
        medium = [p for p in prices if 10 <= p < 100]
        high = [p for p in prices if p >= 100]
        
        print(f"🔴 Very low prices (<1₽): {very_low}")
        print(f"🟡 Low prices (1-10₽): {low}")
        print(f"🟢 Medium prices (10-100₽): {medium}")
        print(f"🔵 High prices (≥100₽): {high}")
        
    except Exception as e:
        print(f"❌ Error analyzing {dish_name}: {str(e)}")

def main():
    """Analyze pricing for the test dishes"""
    print("🔍 DETAILED PRICING ANALYSIS - JULY 2025")
    print("Analyzing specific pricing issues in tech cards")
    print("=" * 70)
    
    test_dishes = [
        "Семга на гриле",
        "Курица в сливках",
        "Картофельное пюре"
    ]
    
    for dish in test_dishes:
        analyze_tech_card_pricing(dish)
    
    print("\n" + "=" * 70)
    print("🎯 ANALYSIS COMPLETE")
    print("Check the ingredients and cost sections above for pricing details")

if __name__ == "__main__":
    main()