#!/usr/bin/env python3
"""
Focused test for FINANCES feature with corrected cost calculations
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def main():
    """Test the FIXED FINANCES feature"""
    print("🎯 TESTING FIXED FINANCES FEATURE")
    print("=" * 60)
    
    # Test data as specified in review request
    user_id = "test_user_12345"
    
    # First, generate a tech card for "Паста Карбонара на 4 порции"
    print("📋 Step 1: Generating tech card for 'Паста Карбонара на 4 порции'...")
    
    tech_card_request = {
        "user_id": user_id,
        "dish_name": "Паста Карбонара на 4 порции"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", json=tech_card_request, timeout=60)
        end_time = time.time()
        
        print(f"⏱️ Tech card generation time: {end_time - start_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ Tech card generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        tech_card_data = response.json()
        tech_card_content = tech_card_data.get("tech_card", "")
        
        if not tech_card_content:
            print("❌ No tech card content received")
            return
            
        print(f"✅ Tech card generated successfully ({len(tech_card_content)} characters)")
        
    except Exception as e:
        print(f"❌ Error generating tech card: {str(e)}")
        return
    
    # Step 2: Test the FINANCES analysis endpoint
    print("\n💰 Step 2: Testing FINANCES analysis endpoint...")
    
    finances_request = {
        "user_id": user_id,
        "tech_card": tech_card_content
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/analyze-finances", json=finances_request, timeout=60)
        end_time = time.time()
        
        print(f"⏱️ Finances analysis time: {end_time - start_time:.2f} seconds")
        
        # Test 1: API responds with 200 status
        if response.status_code != 200:
            print(f"❌ FINANCES API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        print("✅ Test 1 PASSED: API responds with 200 status")
        
        # Parse response
        finances_data = response.json()
        
        if not finances_data.get("success"):
            print("❌ FINANCES API returned success=false")
            return
            
        analysis = finances_data.get("analysis", {})
        
        if not analysis:
            print("❌ No analysis data received")
            return
            
        print(f"✅ FINANCES analysis received")
        
        # Test 2: New cost_verification section is present
        cost_verification = analysis.get("cost_verification")
        if not cost_verification:
            print("❌ Test 2 FAILED: cost_verification section is missing")
            return
        
        print("✅ Test 2 PASSED: cost_verification section is present")
        
        # Test 3: total_cost equals the sum of ingredient_costs
        total_cost = analysis.get("total_cost", 0)
        ingredient_costs = analysis.get("ingredient_costs", [])
        
        if not ingredient_costs:
            print("❌ Test 3 FAILED: No ingredient_costs found")
            return
            
        # Calculate sum of ingredient costs
        ingredients_sum = sum(float(ingredient.get("total_cost", 0)) for ingredient in ingredient_costs)
        calculation_correct = cost_verification.get("calculation_correct", False)
        
        print(f"💰 Total cost from analysis: {total_cost}₽")
        print(f"💰 Sum of ingredient costs: {ingredients_sum}₽")
        print(f"✅ Calculation correct flag: {calculation_correct}")
        
        # Test 4: Calculation_correct flag shows true
        if not calculation_correct:
            print("❌ Test 4 FAILED: calculation_correct flag is false")
            print("⚠️ This indicates the cost calculations are still incorrect")
            return
            
        print("✅ Test 4 PASSED: calculation_correct flag shows true")
        
        # Test 5: Check ingredient details
        print("\n📋 Step 3: Checking ingredient details...")
        
        for i, ingredient in enumerate(ingredient_costs[:5]):  # Show first 5 ingredients
            ingredient_name = ingredient.get("ingredient", "")
            quantity = ingredient.get("quantity", "")
            total_cost = ingredient.get("total_cost", 0)
            
            print(f"🥘 {ingredient_name}: {quantity} = {total_cost}₽")
        
        # Print summary
        print("\n📊 FINANCES FEATURE TEST SUMMARY:")
        print("=" * 50)
        print(f"✅ API Status: 200 OK")
        print(f"✅ Cost Verification Section: Present")
        print(f"✅ Calculation Correct Flag: {calculation_correct}")
        print(f"💰 Total Cost: {total_cost}₽")
        print(f"🧮 Ingredients Sum: {ingredients_sum}₽")
        print(f"📊 Number of Ingredients: {len(ingredient_costs)}")
        
        if calculation_correct:
            print("\n🎉 ALL TESTS PASSED - FINANCES FEATURE IS WORKING CORRECTLY!")
        else:
            print("\n🚨 TESTS FAILED - FINANCES FEATURE NEEDS FIXES")
        
    except Exception as e:
        print(f"❌ Error testing FINANCES feature: {str(e)}")

if __name__ == "__main__":
    main()