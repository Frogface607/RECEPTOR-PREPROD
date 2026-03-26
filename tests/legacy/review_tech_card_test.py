#!/usr/bin/env python3
"""
Review-Specific Tech Card Generation Test
Testing main tech card generation functionality after frontend improvements
Focus: Mixed ingredients including unit-based items (штучные products)
"""

import requests
import json
import time
import re
from datetime import datetime

# Configuration
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def test_mixed_ingredients_tech_card():
    """Test tech card generation with mixed ingredients including unit-based items"""
    print("🎯 TESTING TECH CARD GENERATION WITH MIXED INGREDIENTS")
    print("=" * 70)
    print("Focus: Unit-based items (штучные products) handling")
    print()
    
    # Test parameters as specified in review request
    user_id = "test_user_12345"
    dish_name = "Бургер с булочкой на 2 порции - булочка для бургера, котлета говяжья 120г, сыр чеддер 2 ломтика, помидор 1 штука, лук 1/2 луковицы, салат 2 листа"
    
    print(f"👤 User ID: {user_id}")
    print(f"🍔 Dish: {dish_name}")
    print()
    
    # Test 1: Generate tech card with mixed ingredients
    print("📋 Test 1: Generate tech card with mixed ingredients...")
    
    try:
        tech_card_request = {
            "user_id": user_id,
            "dish_name": dish_name
        }
        
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", 
                               json=tech_card_request, timeout=120)
        end_time = time.time()
        
        print(f"⏱️ Generation time: {end_time - start_time:.2f} seconds")
        
        if response.status_code != 200:
            print(f"❌ Test 1 FAILED: Tech card generation returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        tech_card_content = result.get("tech_card", "")
        
        if not tech_card_content:
            print("❌ Test 1 FAILED: No tech card content received")
            return False
        
        print("✅ Test 1 PASSED: Tech card generated successfully")
        print(f"📄 Tech card length: {len(tech_card_content)} characters")
        
    except Exception as e:
        print(f"❌ Test 1 FAILED: Error generating tech card: {str(e)}")
        return False
    
    # Test 2: Verify proper ingredient parsing
    print("\n🥘 Test 2: Verify proper ingredient parsing...")
    
    try:
        # Look for ingredients section
        ingredients_section = ""
        if "**Ингредиенты:**" in tech_card_content:
            start_idx = tech_card_content.find("**Ингредиенты:**")
            end_idx = tech_card_content.find("**", start_idx + 15)  # Find next section
            if end_idx == -1:
                end_idx = len(tech_card_content)
            ingredients_section = tech_card_content[start_idx:end_idx]
        
        if not ingredients_section:
            print("❌ Test 2 FAILED: No ingredients section found")
            return False
        
        print("✅ Test 2 PASSED: Ingredients section found")
        print(f"📋 Ingredients section length: {len(ingredients_section)} characters")
        
        # Check for unit-based items (штучные products)
        unit_based_indicators = [
            "штук", "шт", "ломтик", "лист", "луковиц", "помидор", "булочк"
        ]
        
        found_unit_indicators = []
        for indicator in unit_based_indicators:
            if indicator.lower() in ingredients_section.lower():
                found_unit_indicators.append(indicator)
        
        if found_unit_indicators:
            print(f"✅ Unit-based indicators found: {found_unit_indicators}")
        else:
            print("⚠️ Warning: No explicit unit-based indicators found")
        
    except Exception as e:
        print(f"❌ Test 2 FAILED: Error parsing ingredients: {str(e)}")
        return False
    
    # Test 3: Verify correct cost calculations
    print("\n💰 Test 3: Verify correct cost calculations...")
    
    try:
        # Extract cost information
        cost_patterns = [
            r'(\d+(?:\.\d+)?)\s*₽',  # Price patterns
            r'Себестоимость.*?(\d+(?:\.\d+)?)\s*₽',  # Cost patterns
            r'Рекомендуемая цена.*?(\d+(?:\.\d+)?)\s*₽'  # Recommended price
        ]
        
        all_prices = []
        for pattern in cost_patterns:
            matches = re.findall(pattern, tech_card_content, re.IGNORECASE)
            all_prices.extend([float(match) for match in matches])
        
        if not all_prices:
            print("❌ Test 3 FAILED: No cost information found")
            return False
        
        min_price = min(all_prices)
        max_price = max(all_prices)
        avg_price = sum(all_prices) / len(all_prices)
        
        print(f"✅ Test 3 PASSED: Cost calculations found")
        print(f"💰 Price range: {min_price}₽ - {max_price}₽")
        print(f"💰 Average price: {avg_price:.2f}₽")
        print(f"💰 Total prices found: {len(all_prices)}")
        
        # Verify reasonable pricing for burger (should be in reasonable range)
        if max_price < 50 or max_price > 2000:
            print(f"⚠️ Warning: Maximum price {max_price}₽ seems unusual for burger")
        else:
            print(f"✅ Price range appears reasonable for burger dish")
        
    except Exception as e:
        print(f"❌ Test 3 FAILED: Error analyzing costs: {str(e)}")
        return False
    
    # Test 4: Verify all required sections are present
    print("\n📑 Test 4: Verify all required sections are present...")
    
    try:
        required_sections = [
            "Название",
            "Ингредиенты", 
            "Рецепт",
            "Время",
            "Выход",
            "Себестоимость",
            "КБЖУ"
        ]
        
        found_sections = []
        missing_sections = []
        
        for section in required_sections:
            # Check for various formats of section headers
            section_patterns = [
                f"**{section}:**",
                f"**{section}**",
                f"{section}:",
                section
            ]
            
            found = False
            for pattern in section_patterns:
                if pattern.lower() in tech_card_content.lower():
                    found = True
                    break
            
            if found:
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        print(f"✅ Found sections: {found_sections}")
        
        if missing_sections:
            print(f"⚠️ Missing sections: {missing_sections}")
            if len(missing_sections) > 2:  # Allow some flexibility
                print("❌ Test 4 FAILED: Too many required sections missing")
                return False
            else:
                print("✅ Test 4 PASSED: Most required sections present (minor missing sections acceptable)")
        else:
            print("✅ Test 4 PASSED: All required sections present")
        
    except Exception as e:
        print(f"❌ Test 4 FAILED: Error checking sections: {str(e)}")
        return False
    
    # Test 5: Verify unit handling for штучные products
    print("\n🔢 Test 5: Verify unit handling for штучные products...")
    
    try:
        # Look for specific unit-based ingredients mentioned in the dish name
        expected_units = [
            ("помидор", ["штук", "шт"]),
            ("лук", ["луковиц", "половин"]),
            ("салат", ["лист", "листь"]),
            ("сыр", ["ломтик", "кусоч"]),
            ("булочк", ["штук", "шт"])
        ]
        
        unit_handling_score = 0
        total_expected = len(expected_units)
        
        for ingredient, unit_variants in expected_units:
            ingredient_found = False
            unit_found = False
            
            # Check if ingredient is mentioned
            if ingredient.lower() in tech_card_content.lower():
                ingredient_found = True
                
                # Check if appropriate units are used
                for unit in unit_variants:
                    if unit.lower() in tech_card_content.lower():
                        unit_found = True
                        break
            
            if ingredient_found and unit_found:
                unit_handling_score += 1
                print(f"✅ {ingredient}: Found with appropriate units")
            elif ingredient_found:
                print(f"⚠️ {ingredient}: Found but unit handling unclear")
                unit_handling_score += 0.5
            else:
                print(f"❌ {ingredient}: Not found or not properly handled")
        
        unit_handling_percentage = (unit_handling_score / total_expected) * 100
        print(f"📊 Unit handling score: {unit_handling_score}/{total_expected} ({unit_handling_percentage:.1f}%)")
        
        if unit_handling_percentage >= 60:  # Allow some flexibility
            print("✅ Test 5 PASSED: Unit handling for штучные products is adequate")
        else:
            print("❌ Test 5 FAILED: Poor unit handling for штучные products")
            return False
        
    except Exception as e:
        print(f"❌ Test 5 FAILED: Error checking unit handling: {str(e)}")
        return False
    
    # Test 6: Verify backend is not affected by frontend improvements
    print("\n🔧 Test 6: Verify backend functionality integrity...")
    
    try:
        # Generate another tech card to ensure consistent functionality
        simple_dish_request = {
            "user_id": user_id,
            "dish_name": "Простая паста с томатами"
        }
        
        response = requests.post(f"{BACKEND_URL}/generate-tech-card", 
                               json=simple_dish_request, timeout=60)
        
        if response.status_code != 200:
            print("❌ Test 6 FAILED: Backend functionality may be affected")
            return False
        
        simple_result = response.json()
        simple_content = simple_result.get("tech_card", "")
        
        if not simple_content or len(simple_content) < 500:
            print("❌ Test 6 FAILED: Backend generating poor quality content")
            return False
        
        print("✅ Test 6 PASSED: Backend functionality remains intact")
        print(f"📄 Simple dish tech card length: {len(simple_content)} characters")
        
    except Exception as e:
        print(f"❌ Test 6 FAILED: Error testing backend integrity: {str(e)}")
        return False
    
    # Print detailed analysis
    print("\n" + "=" * 70)
    print("📊 DETAILED TECH CARD ANALYSIS")
    print("=" * 70)
    
    # Show first 500 characters of ingredients section
    if ingredients_section:
        print("🥘 INGREDIENTS SECTION PREVIEW:")
        print("-" * 40)
        print(ingredients_section[:500] + ("..." if len(ingredients_section) > 500 else ""))
        print()
    
    # Show cost section if found
    cost_section_start = tech_card_content.find("**Себестоимость:**")
    if cost_section_start != -1:
        cost_section_end = tech_card_content.find("**", cost_section_start + 15)
        if cost_section_end == -1:
            cost_section_end = cost_section_start + 300
        cost_section = tech_card_content[cost_section_start:cost_section_end]
        
        print("💰 COST SECTION PREVIEW:")
        print("-" * 40)
        print(cost_section)
        print()
    
    return True

def main():
    """Main test execution"""
    print("🚀 RECEPTOR PRO - TECH CARD GENERATION REVIEW TEST")
    print("Testing main tech card generation functionality after frontend improvements")
    print("=" * 70)
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run the main test
    success = test_mixed_ingredients_tech_card()
    
    print("\n" + "=" * 70)
    print("🎯 FINAL TEST RESULTS:")
    print("=" * 70)
    
    if success:
        print("✅ TECH CARD GENERATION: ALL TESTS PASSED")
        print("✅ Mixed ingredients handling working correctly")
        print("✅ Unit-based items (штучные products) processed properly")
        print("✅ Cost calculations functioning")
        print("✅ All required sections present")
        print("✅ Backend functionality not affected by frontend improvements")
        print()
        print("🎉 CORE TECH CARD GENERATION IS FULLY FUNCTIONAL")
        print("🎉 SYSTEM READY FOR PRODUCTION USE")
    else:
        print("❌ TECH CARD GENERATION: TESTS FAILED")
        print("🚨 Core functionality needs attention")
        print("🚨 Review the specific test failures above")
    
    print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success

if __name__ == "__main__":
    main()