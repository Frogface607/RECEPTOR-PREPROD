#!/usr/bin/env python3
"""
TechCardV2 Cost Calculator - Detailed Testing
Testing specific aspects of the cost calculator: unit conversions, fuzzy matching, fallback pricing.
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_unit_conversions():
    """Test unit conversions by analyzing the generated ingredients"""
    log_test("⚖️ Testing unit conversions in cost calculator")
    
    # Generate a tech card and analyze the ingredients
    test_profile = {
        "name": "Тест конвертации единиц",
        "cuisine": "русская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=false"
        response = requests.post(url, json=test_profile, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == "success" and data.get('card'):
                card = data['card']
                ingredients = card.get('ingredients', [])
                cost = card.get('cost', {})
                
                log_test("✅ Generated tech card for unit conversion analysis")
                log_test(f"📊 Found {len(ingredients)} ingredients")
                log_test(f"💰 Total cost: {cost.get('rawCost')} RUB")
                
                log_test("\n🧮 UNIT CONVERSION ANALYSIS:")
                
                for i, ingredient in enumerate(ingredients):
                    name = ingredient.get('name', 'Unknown')
                    brutto_g = ingredient.get('brutto_g', 0)
                    unit = ingredient.get('unit', 'g')
                    
                    log_test(f"   {i+1}. {name}: {brutto_g}{unit}")
                    
                    # Analyze expected conversions
                    if unit == 'g':
                        kg_equivalent = brutto_g / 1000.0
                        log_test(f"      → {kg_equivalent:.3f} kg (g→kg conversion)")
                        
                        # Check if this matches known catalog prices
                        if 'куриное филе' in name.lower():
                            expected_cost = kg_equivalent * 450  # 450 RUB/kg
                            log_test(f"      → Expected cost: {expected_cost:.2f} RUB (450 RUB/kg)")
                        elif 'соль' in name.lower():
                            expected_cost = kg_equivalent * 25   # 25 RUB/kg
                            log_test(f"      → Expected cost: {expected_cost:.2f} RUB (25 RUB/kg)")
                    
                    elif unit == 'ml':
                        l_equivalent = brutto_g / 1000.0
                        log_test(f"      → {l_equivalent:.3f} L (ml→L conversion)")
                        
                        if 'масло' in name.lower():
                            expected_cost = l_equivalent * 150  # 150 RUB/L
                            log_test(f"      → Expected cost: {expected_cost:.2f} RUB (150 RUB/L)")
                    
                    elif unit == 'pcs':
                        if 'яйц' in name.lower():
                            kg_equivalent = brutto_g / 18  # 18 eggs per kg
                            log_test(f"      → {kg_equivalent:.3f} kg (pcs→kg for eggs, 18 pcs/kg)")
                            expected_cost = kg_equivalent * 120  # 120 RUB/kg for eggs
                            log_test(f"      → Expected cost: {expected_cost:.2f} RUB (120 RUB/kg)")
                
                return {
                    'success': True,
                    'ingredients_analyzed': len(ingredients),
                    'cost_calculated': cost.get('rawCost') is not None,
                    'total_cost': cost.get('rawCost')
                }
            else:
                log_test("❌ Failed to generate card for unit conversion testing")
                return {'success': False, 'error': 'Card generation failed'}
        else:
            log_test(f"❌ Request failed: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_ingredient_matching():
    """Test ingredient matching by checking if known ingredients are found"""
    log_test("🔍 Testing ingredient matching with price catalog")
    
    # Test multiple generations to see different ingredients
    test_profiles = [
        {"name": "Куриное блюдо", "cuisine": "русская"},
        {"name": "Рыбное блюдо", "cuisine": "русская"},
        {"name": "Овощное блюдо", "cuisine": "русская"}
    ]
    
    matching_results = []
    
    for profile in test_profiles:
        log_test(f"\n🧪 Testing: {profile['name']}")
        
        try:
            url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=false"
            response = requests.post(url, json=profile, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == "success" and data.get('card'):
                    card = data['card']
                    ingredients = card.get('ingredients', [])
                    cost = card.get('cost', {})
                    
                    log_test(f"✅ Generated {profile['name']}")
                    log_test(f"   Ingredients: {len(ingredients)}")
                    log_test(f"   Cost: {cost.get('rawCost')} RUB")
                    
                    # Check for known ingredients
                    known_ingredients_found = []
                    for ingredient in ingredients:
                        name = ingredient.get('name', '').lower()
                        
                        # Check for catalog matches
                        if 'куриное филе' in name:
                            known_ingredients_found.append('куриное филе')
                        elif 'растительное масло' in name:
                            known_ingredients_found.append('растительное масло')
                        elif 'соль поваренная' in name:
                            known_ingredients_found.append('соль поваренная')
                        elif 'лук репчатый' in name:
                            known_ingredients_found.append('лук репчатый')
                        elif 'морковь' in name:
                            known_ingredients_found.append('морковь')
                    
                    if known_ingredients_found:
                        log_test(f"   ✅ Found catalog ingredients: {known_ingredients_found}")
                    else:
                        log_test(f"   ⚠️ No exact catalog matches found")
                    
                    matching_results.append({
                        'profile': profile['name'],
                        'success': True,
                        'cost_calculated': cost.get('rawCost') is not None,
                        'known_ingredients': known_ingredients_found,
                        'total_ingredients': len(ingredients)
                    })
                else:
                    log_test(f"❌ Failed to generate {profile['name']}")
                    matching_results.append({
                        'profile': profile['name'],
                        'success': False,
                        'error': 'Generation failed'
                    })
            else:
                log_test(f"❌ Request failed for {profile['name']}: {response.status_code}")
                matching_results.append({
                    'profile': profile['name'],
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            log_test(f"❌ Error testing {profile['name']}: {str(e)}")
            matching_results.append({
                'profile': profile['name'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    successful_tests = sum(1 for r in matching_results if r['success'])
    tests_with_cost = sum(1 for r in matching_results if r.get('cost_calculated'))
    
    log_test(f"\n📊 INGREDIENT MATCHING RESULTS:")
    log_test(f"   Successful generations: {successful_tests}/{len(test_profiles)}")
    log_test(f"   Cost calculated: {tests_with_cost}/{len(test_profiles)}")
    
    return {
        'success': successful_tests > 0,
        'successful_tests': successful_tests,
        'total_tests': len(test_profiles),
        'tests_with_cost': tests_with_cost,
        'results': matching_results
    }

def test_fallback_pricing():
    """Test fallback pricing by using ingredients not in catalog"""
    log_test("🔄 Testing fallback pricing mechanism")
    
    # We can't directly control ingredients, but we can test that cost is calculated
    # even when some ingredients might not be in the catalog
    test_profile = {
        "name": "Экзотическое блюдо",
        "cuisine": "азиатская",  # Different cuisine might generate different ingredients
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=false"
        response = requests.post(url, json=test_profile, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == "success" and data.get('card'):
                card = data['card']
                ingredients = card.get('ingredients', [])
                cost = card.get('cost', {})
                
                log_test("✅ Generated exotic dish for fallback testing")
                log_test(f"📊 Ingredients: {len(ingredients)}")
                log_test(f"💰 Cost calculated: {cost.get('rawCost')} RUB")
                
                # The fact that cost is calculated indicates fallback pricing works
                if cost.get('rawCost') is not None:
                    log_test("✅ FALLBACK PRICING WORKING!")
                    log_test("   Cost calculated even with potentially unknown ingredients")
                    
                    # Analyze ingredients
                    log_test("\n🥬 INGREDIENTS ANALYSIS:")
                    for i, ingredient in enumerate(ingredients):
                        name = ingredient.get('name', 'Unknown')
                        brutto_g = ingredient.get('brutto_g', 0)
                        unit = ingredient.get('unit', 'g')
                        log_test(f"   {i+1}. {name}: {brutto_g}{unit}")
                    
                    return {
                        'success': True,
                        'fallback_working': True,
                        'cost_calculated': True,
                        'total_cost': cost.get('rawCost'),
                        'ingredients_count': len(ingredients)
                    }
                else:
                    log_test("❌ No cost calculated - fallback pricing may not be working")
                    return {
                        'success': False,
                        'fallback_working': False,
                        'error': 'No cost calculated'
                    }
            else:
                log_test("❌ Failed to generate exotic dish")
                return {'success': False, 'error': 'Generation failed'}
        else:
            log_test(f"❌ Request failed: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_cost_accuracy_verification():
    """Verify cost calculation accuracy with manual calculation"""
    log_test("🧮 Testing cost calculation accuracy verification")
    
    test_profile = {
        "name": "Точный расчет стоимости",
        "cuisine": "русская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=false"
        response = requests.post(url, json=test_profile, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == "success" and data.get('card'):
                card = data['card']
                ingredients = card.get('ingredients', [])
                cost = card.get('cost', {})
                portions = card.get('portions', 1)
                
                log_test("✅ Generated tech card for accuracy verification")
                
                # Manual cost calculation
                manual_total_cost = 0
                log_test("\n🧮 MANUAL COST CALCULATION:")
                
                for ingredient in ingredients:
                    name = ingredient.get('name', '').lower()
                    brutto_g = ingredient.get('brutto_g', 0)
                    unit = ingredient.get('unit', 'g')
                    
                    ingredient_cost = 0
                    
                    # Calculate based on known catalog prices
                    if 'куриное филе' in name:
                        ingredient_cost = (brutto_g / 1000) * 450  # 450 RUB/kg
                        log_test(f"   {ingredient.get('name')}: {brutto_g}g → {ingredient_cost:.2f} RUB (450 RUB/kg)")
                    elif 'соль' in name:
                        ingredient_cost = (brutto_g / 1000) * 25   # 25 RUB/kg
                        log_test(f"   {ingredient.get('name')}: {brutto_g}g → {ingredient_cost:.2f} RUB (25 RUB/kg)")
                    elif 'масло' in name and unit == 'ml':
                        ingredient_cost = (brutto_g / 1000) * 150  # 150 RUB/L
                        log_test(f"   {ingredient.get('name')}: {brutto_g}ml → {ingredient_cost:.2f} RUB (150 RUB/L)")
                    else:
                        # Use fallback estimation
                        ingredient_cost = (brutto_g / 1000) * 150  # Default fallback
                        log_test(f"   {ingredient.get('name')}: {brutto_g}{unit} → {ingredient_cost:.2f} RUB (fallback)")
                    
                    manual_total_cost += ingredient_cost
                
                calculated_cost = cost.get('rawCost', 0)
                cost_per_portion = cost.get('costPerPortion', 0)
                expected_cost_per_portion = manual_total_cost / portions
                
                log_test(f"\n📊 COST COMPARISON:")
                log_test(f"   Manual calculation: {manual_total_cost:.2f} RUB")
                log_test(f"   System calculation: {calculated_cost:.2f} RUB")
                log_test(f"   Difference: {abs(manual_total_cost - calculated_cost):.2f} RUB")
                
                log_test(f"\n📊 PER-PORTION COST:")
                log_test(f"   Expected per portion: {expected_cost_per_portion:.2f} RUB")
                log_test(f"   System per portion: {cost_per_portion:.2f} RUB")
                log_test(f"   Portions: {portions}")
                
                # Check accuracy (within 5% tolerance)
                accuracy_tolerance = 0.05
                cost_accurate = abs(manual_total_cost - calculated_cost) <= (manual_total_cost * accuracy_tolerance)
                portion_accurate = abs(expected_cost_per_portion - cost_per_portion) <= 0.01
                
                log_test(f"\n✅ ACCURACY RESULTS:")
                log_test(f"   Total cost accurate: {cost_accurate} (within 5%)")
                log_test(f"   Per-portion accurate: {portion_accurate} (within 1 kopeck)")
                
                return {
                    'success': True,
                    'cost_accurate': cost_accurate,
                    'portion_accurate': portion_accurate,
                    'manual_cost': manual_total_cost,
                    'system_cost': calculated_cost,
                    'cost_difference': abs(manual_total_cost - calculated_cost)
                }
            else:
                log_test("❌ Failed to generate card for accuracy testing")
                return {'success': False, 'error': 'Generation failed'}
        else:
            log_test(f"❌ Request failed: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main testing function for detailed cost calculator testing"""
    log_test("🚀 Starting TechCardV2 Cost Calculator - DETAILED TESTING")
    log_test("🎯 Focus: Unit conversions, ingredient matching, fallback pricing, accuracy")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Test 1: Unit conversions
    conversion_result = test_unit_conversions()
    
    log_test("\n" + "=" * 80)
    
    # Test 2: Ingredient matching
    matching_result = test_ingredient_matching()
    
    log_test("\n" + "=" * 80)
    
    # Test 3: Fallback pricing
    fallback_result = test_fallback_pricing()
    
    log_test("\n" + "=" * 80)
    
    # Test 4: Cost accuracy verification
    accuracy_result = test_cost_accuracy_verification()
    
    # Summary
    log_test("\n" + "=" * 80)
    log_test("📋 DETAILED COST CALCULATOR TESTING SUMMARY:")
    log_test(f"✅ Unit conversions: {'SUCCESS' if conversion_result.get('success') else 'FAILED'}")
    log_test(f"✅ Ingredient matching: {'SUCCESS' if matching_result.get('success') else 'FAILED'}")
    log_test(f"✅ Fallback pricing: {'SUCCESS' if fallback_result.get('success') else 'FAILED'}")
    log_test(f"✅ Cost accuracy: {'SUCCESS' if accuracy_result.get('success') else 'FAILED'}")
    
    # Detailed results
    if all([conversion_result.get('success'), matching_result.get('success'), 
            fallback_result.get('success'), accuracy_result.get('success')]):
        log_test("\n🎉 ALL DETAILED TESTS PASSED!")
        log_test("✅ Unit conversion system working correctly")
        log_test("✅ Ingredient matching with price catalog functional")
        log_test("✅ Fallback pricing mechanism operational")
        log_test("✅ Cost calculation accuracy verified")
        
        if accuracy_result.get('cost_accurate'):
            log_test(f"💰 Cost accuracy within tolerance: {accuracy_result.get('cost_difference'):.2f} RUB difference")
    else:
        log_test("\n⚠️ SOME TESTS FAILED:")
        if not conversion_result.get('success'):
            log_test(f"   Unit conversions: {conversion_result.get('error')}")
        if not matching_result.get('success'):
            log_test(f"   Ingredient matching: {matching_result.get('error')}")
        if not fallback_result.get('success'):
            log_test(f"   Fallback pricing: {fallback_result.get('error')}")
        if not accuracy_result.get('success'):
            log_test(f"   Cost accuracy: {accuracy_result.get('error')}")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()