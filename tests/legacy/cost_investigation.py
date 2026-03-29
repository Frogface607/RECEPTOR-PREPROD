#!/usr/bin/env python3
"""
Detailed Financial Analysis Investigation
Investigate the cost calculation issue in detail
"""

import requests
import json
import time

BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
TEST_USER_ID = "demo_user"

def investigate_cost_calculation():
    """Generate a tech card and analyze the cost calculation in detail"""
    print("🔍 INVESTIGATING COST CALCULATION ISSUE")
    print("=" * 60)
    
    # Generate a simple dish to understand the cost calculation
    url = f"{API_BASE}/v1/techcards.v2/generate"
    payload = {
        "name": "Паста карбонара с беконом и пармезаном",
        "cuisine": "итальянская", 
        "equipment": ["плита", "сковорода"],
        "budget": 800.0,
        "dietary": [],
        "user_id": TEST_USER_ID
    }
    
    print(f"Generating: {payload['name']}")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            card = data.get('card', {})
            
            print("\n📊 DETAILED ANALYSIS:")
            print("-" * 40)
            
            # Basic info
            portions = card.get('portions', 'N/A')
            print(f"Portions: {portions}")
            
            # Cost breakdown
            cost_data = card.get('cost', {})
            print(f"\nCost Data:")
            for key, value in cost_data.items():
                print(f"  {key}: {value}")
            
            # Yield breakdown
            yield_data = card.get('yield', {})
            print(f"\nYield Data:")
            for key, value in yield_data.items():
                print(f"  {key}: {value}")
            
            # Ingredients analysis
            ingredients = card.get('ingredients', [])
            print(f"\nIngredients ({len(ingredients)}):")
            total_ingredient_cost = 0
            
            for i, ing in enumerate(ingredients):
                name = ing.get('name', 'Unknown')
                quantity = ing.get('quantity', 0)
                unit = ing.get('unit', 'N/A')
                price = ing.get('price', 0)
                cost = ing.get('cost', 0)
                
                print(f"  {i+1}. {name}: {quantity} {unit} @ {price} = {cost}")
                total_ingredient_cost += cost
            
            print(f"\nCalculated total ingredient cost: {total_ingredient_cost}")
            
            # Analysis
            raw_cost = cost_data.get('rawCost', 0)
            cost_per_portion = cost_data.get('costPerPortion', 0)
            
            print(f"\n🧮 COST ANALYSIS:")
            print(f"Raw Cost: {raw_cost}")
            print(f"Cost Per Portion: {cost_per_portion}")
            print(f"Portions: {portions}")
            
            if portions == 1:
                print(f"Expected for 1 portion: rawCost ≈ costPerPortion")
                print(f"Actual ratio: {raw_cost / max(cost_per_portion, 0.01):.2f}")
                
                if abs(raw_cost - cost_per_portion) / max(raw_cost, cost_per_portion) > 0.1:
                    print("❌ ISSUE: Cost inconsistency detected!")
                    print("This suggests the cost calculation is not properly normalized")
                    
                    # Hypothesis: rawCost might be the original cost before normalization
                    # while costPerPortion is the normalized cost
                    if raw_cost > cost_per_portion:
                        scale_factor = cost_per_portion / raw_cost
                        print(f"Implied scale factor: {scale_factor:.3f}")
                        print("This suggests rawCost is pre-normalization, costPerPortion is post-normalization")
                else:
                    print("✅ Cost calculation appears consistent")
            
            # Check meta information
            meta = card.get('meta', {})
            print(f"\nMeta information:")
            for key, value in meta.items():
                if 'cost' in key.lower() or 'scale' in key.lower() or 'normal' in key.lower():
                    print(f"  {key}: {value}")
            
            return True
            
        else:
            print(f"❌ Generation failed: HTTP {response.status_code}")
            print(response.text[:200])
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    investigate_cost_calculation()

if __name__ == "__main__":
    main()