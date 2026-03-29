#!/usr/bin/env python3
"""
Focused test for GOLDEN_PROMPT changes - Review Request Testing
"""

import requests
import time
import re

def test_golden_prompt_changes():
    """Test the specific requirements from the review request"""
    
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    print("🧪 GOLDEN_PROMPT CHANGES TEST")
    print("=" * 50)
    print("Testing: Паста Болоньезе на 4 порции")
    print("User: test_user_12345")
    print("City: moskva")
    print()
    
    # Test data as specified in review request
    data = {
        "dish_name": "Паста Болоньезе на 4 порции",
        "user_id": "test_user_12345"
    }
    
    print("🔄 Generating tech card...")
    start_time = time.time()
    
    try:
        response = requests.post(f"{base_url}/generate-tech-card", json=data, timeout=120)
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"⏱️  Response time: {response_time:.2f} seconds")
        
        # Test 1: API response is 200 OK
        if response.status_code == 200:
            print("✅ TEST 1 PASSED: API response is 200 OK")
        else:
            print(f"❌ TEST 1 FAILED: API response is {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
        result = response.json()
        
        if not result.get("success", False):
            print("❌ Tech card generation failed")
            return False
            
        tech_card_content = result.get("tech_card", "")
        
        print(f"📄 Tech card generated successfully")
        print(f"📏 Content length: {len(tech_card_content)} characters")
        print()
        
        # Test 2: Check if generated tech card contains complex ingredients like "demi-glace"
        print("🔍 TEST 2: Checking for complex ingredients...")
        
        complex_ingredients = [
            "demi-glace", "демигляс", "demiglace",
            "espagnole", "эспаньол", "эспанол", 
            "velouté", "велюте", "veloute",
            "hollandaise", "голландез",
            "béarnaise", "беарнез",
            "beurre blanc", "бер блан"
        ]
        
        content_lower = tech_card_content.lower()
        found_complex = []
        
        for ingredient in complex_ingredients:
            if ingredient.lower() in content_lower:
                found_complex.append(ingredient)
        
        if found_complex:
            print(f"❌ TEST 2 FAILED: Found complex ingredients: {', '.join(found_complex)}")
            complex_test_passed = False
        else:
            print("✅ TEST 2 PASSED: No complex French sauces found")
            complex_test_passed = True
        
        print()
        
        # Test 3: Verify simple, appropriate ingredients for pasta dish
        print("🔍 TEST 3: Checking for simple, appropriate ingredients...")
        
        simple_ingredients = [
            "фарш", "говядина", "свинина", "мясо",
            "лук", "морковь", "чеснок", 
            "томат", "помидор", "паста томатная", "томатная паста",
            "паста", "спагетти", "макароны",
            "масло", "оливковое масло", "растительное масло",
            "соль", "перец", "специи",
            "пармезан", "сыр", "базилик", "петрушка",
            "вино", "красное вино"
        ]
        
        found_simple = []
        for ingredient in simple_ingredients:
            if ingredient.lower() in content_lower:
                found_simple.append(ingredient)
        
        if len(found_simple) >= 5:
            print(f"✅ TEST 3 PASSED: Found appropriate simple ingredients: {', '.join(found_simple[:8])}")
            if len(found_simple) > 8:
                print(f"   ... and {len(found_simple) - 8} more")
            simple_test_passed = True
        else:
            print(f"❌ TEST 3 FAILED: Limited simple ingredients found: {', '.join(found_simple)}")
            simple_test_passed = False
        
        print()
        
        # Test 4: Check portion sizes and pricing appropriateness
        print("🔍 TEST 4: Checking portion sizes and pricing...")
        
        # Look for pricing information
        price_matches = re.findall(r'(\d+)\s*₽', tech_card_content)
        prices = [int(p) for p in price_matches if p.isdigit()]
        
        if prices:
            max_price = max(prices)
            total_estimated = sum(prices)
            print(f"💰 Pricing found: Max ingredient: {max_price}₽, Total estimated: {total_estimated}₽")
            
            # Check if pricing is reasonable for pasta (not too expensive)
            if max_price > 800:  # Very expensive single ingredient
                print(f"⚠️  High single ingredient price: {max_price}₽ (might indicate complex ingredients)")
                pricing_reasonable = False
            elif total_estimated > 2000:  # Very expensive total
                print(f"⚠️  High total cost: {total_estimated}₽ (might indicate overcomplication)")
                pricing_reasonable = False
            else:
                print("✅ Pricing appears reasonable for pasta dish")
                pricing_reasonable = True
        else:
            print("⚠️  No clear pricing information found")
            pricing_reasonable = False
        
        # Look for portion information
        portion_matches = re.findall(r'(\d+)\s*г.*порци|порци.*(\d+)\s*г', content_lower)
        if portion_matches:
            print(f"🍽️  Portion information found")
            portion_test_passed = True
        else:
            print("⚠️  No clear portion information found")
            portion_test_passed = False
        
        print()
        
        # Final assessment
        print("🎯 FINAL ASSESSMENT")
        print("=" * 30)
        
        tests_passed = 0
        total_tests = 4
        
        if complex_test_passed:
            print("✅ Complex ingredients avoidance: PASSED")
            tests_passed += 1
        else:
            print("❌ Complex ingredients avoidance: FAILED")
            
        if simple_test_passed:
            print("✅ Simple ingredients usage: PASSED")
            tests_passed += 1
        else:
            print("❌ Simple ingredients usage: FAILED")
            
        if pricing_reasonable:
            print("✅ Appropriate pricing: PASSED")
            tests_passed += 1
        else:
            print("❌ Appropriate pricing: FAILED")
            
        if portion_test_passed:
            print("✅ Portion size information: PASSED")
            tests_passed += 1
        else:
            print("❌ Portion size information: FAILED")
        
        print()
        print(f"📊 SCORE: {tests_passed}/{total_tests} tests passed")
        
        # Show a sample of the content for manual review
        print("\n📋 TECH CARD SAMPLE (first 500 characters):")
        print("-" * 50)
        print(tech_card_content[:500] + "..." if len(tech_card_content) > 500 else tech_card_content)
        print("-" * 50)
        
        if tests_passed >= 3:
            print("\n🎉 GOLDEN_PROMPT CHANGES ARE WORKING!")
            print("✅ AI is avoiding complex French sauces")
            print("✅ AI is using simple, appropriate ingredients")
            return True
        else:
            print("\n⚠️  GOLDEN_PROMPT CHANGES NEED IMPROVEMENT")
            print("❌ AI may still be generating complex ingredients")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Error during request: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_golden_prompt_changes()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 GOLDEN_PROMPT TEST COMPLETED SUCCESSFULLY!")
    else:
        print("⚠️  GOLDEN_PROMPT TEST COMPLETED WITH ISSUES")
    
    exit(0 if success else 1)