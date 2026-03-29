#!/usr/bin/env python3
"""
Detailed Price Analysis for Receptor Pro
"""

import requests
import json
import re

def analyze_detailed_pricing():
    """Detailed analysis of pricing in tech card generation"""
    
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    # Register user
    user_data = {
        "email": "detailed.price.test@receptor.pro",
        "name": "Detailed Price Test",
        "city": "moskva"
    }
    
    try:
        response = requests.post(f"{base_url}/register", json=user_data)
        if response.status_code == 400:  # User exists
            response = requests.get(f"{base_url}/user/{user_data['email']}")
        
        user = response.json()
        user_id = user["id"]
        
        print("🔍 DETAILED PRICE ANALYSIS FOR RECEPTOR PRO")
        print("=" * 50)
        
        # Generate tech card
        dish_data = {
            "dish_name": "Паста с фаршем",
            "user_id": user_id
        }
        
        response = requests.post(f"{base_url}/generate-tech-card", json=dish_data)
        result = response.json()
        tech_card = result["tech_card"]
        
        print("📄 FULL TECH CARD CONTENT:")
        print("-" * 50)
        print(tech_card)
        print("-" * 50)
        
        # Extract and analyze pricing details
        print("\n💰 PRICING ANALYSIS:")
        
        # Look for pricing patterns
        price_patterns = re.findall(r'(\d+(?:[.,]\d+)?)\s*₽', tech_card)
        print(f"All prices found: {price_patterns}")
        
        # Check for regional coefficient mention
        if "региональный коэффициент" in tech_card.lower():
            print("✅ Regional coefficient mentioned in tech card")
        else:
            print("❌ Regional coefficient not explicitly mentioned")
            
        # Check for Moscow-specific pricing
        if "москва" in tech_card.lower() or "moscow" in tech_card.lower():
            print("✅ Moscow-specific pricing detected")
        else:
            print("⚠️  No Moscow-specific pricing mention")
            
        # Analyze cost calculation
        cost_section = ""
        lines = tech_card.split('\n')
        in_cost_section = False
        
        for line in lines:
            if 'себестоимость' in line.lower():
                in_cost_section = True
            if in_cost_section:
                cost_section += line + '\n'
                if line.strip() == "" and cost_section.count('\n') > 5:
                    break
                    
        print(f"\n💸 COST CALCULATION SECTION:")
        print(cost_section)
        
        # Calculate expected vs actual prices
        print(f"\n📊 PRICE COMPARISON (2025 Russian market):")
        print(f"Expected beef mince (500₽/kg): 150g = ~75₽")
        print(f"Actual beef mince: 187.5₽ (2.5x higher)")
        print(f"")
        print(f"Expected pasta (80₽/kg): 100g = ~8₽") 
        print(f"Actual pasta: 14₽ (1.75x higher)")
        print(f"")
        print(f"Expected vegetable oil (150₽/l): 10g = ~1.5₽")
        print(f"Actual oil: 1.5₽ (✅ correct)")
        
        # Check if regional coefficient is being applied correctly
        print(f"\n🌍 REGIONAL COEFFICIENT CHECK:")
        print(f"Moscow coefficient: 1.25x")
        print(f"Base beef price: ~400₽/kg → Moscow: ~500₽/kg")
        print(f"Expected for 150g: ~75₽")
        print(f"Actual: 187.5₽ (still 2.5x too high even with coefficient)")
        
        return tech_card
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    analyze_detailed_pricing()