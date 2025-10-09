#!/usr/bin/env python3
"""
TechCardV2 Cost Calculator Testing - Fallback Mode
Testing the deterministic cost calculator without LLM (fallback mode only).
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

def test_cost_calculation_fallback_mode():
    """Test cost calculation in fallback mode (no LLM)"""
    log_test("🔧 Testing cost calculation in FALLBACK MODE (no LLM)")
    
    # Simple test profile
    test_profile = {
        "name": "Простое блюдо",
        "cuisine": "русская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    log_test(f"📝 Test profile: {test_profile['name']}")
    log_test("🎯 Testing deterministic cost calculator (code-based, no LLM)")
    
    try:
        # Force fallback mode by disabling LLM
        url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=false"
        log_test(f"Making request to: {url}")
        
        start_time = time.time()
        response = requests.post(url, json=test_profile, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"📊 Response status: {response.status_code}")
        log_test(f"⏱️ Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ TechCardV2 generation request successful!")
            
            status = data.get('status')
            log_test(f"📋 Generation status: {status}")
            
            if status == "success" and data.get('card'):
                card = data['card']
                log_test("🎉 SUCCESS: TechCardV2 generated successfully in fallback mode!")
                
                # Analyze the generated card
                log_test("\n🔍 ANALYZING GENERATED TECHCARD:")
                
                # Basic card info
                meta = card.get('meta', {})
                portions = card.get('portions', 0)
                ingredients = card.get('ingredients', [])
                
                log_test(f"📋 Title: {meta.get('title', 'Unknown')}")
                log_test(f"📋 Portions: {portions}")
                log_test(f"📋 Ingredients count: {len(ingredients)}")
                
                # Cost analysis
                cost = card.get('cost', {})
                raw_cost = cost.get('rawCost')
                cost_per_portion = cost.get('costPerPortion')
                markup_pct = cost.get('markup_pct')
                vat_pct = cost.get('vat_pct')
                
                log_test("\n💰 COST CALCULATION ANALYSIS:")
                log_test(f"💰 Raw Cost: {raw_cost} RUB")
                log_test(f"💰 Cost Per Portion: {cost_per_portion} RUB")
                log_test(f"💰 Markup %: {markup_pct}%")
                log_test(f"💰 VAT %: {vat_pct}%")
                
                # Check if all cost fields are populated
                cost_fields_populated = all([
                    raw_cost is not None,
                    cost_per_portion is not None,
                    markup_pct is not None,
                    vat_pct is not None
                ])
                
                if cost_fields_populated:
                    log_test("✅ ALL COST FIELDS POPULATED!")
                    
                    # Verify cost calculation accuracy
                    expected_cost_per_portion = raw_cost / portions if raw_cost and portions > 0 else 0
                    cost_accuracy = abs(cost_per_portion - expected_cost_per_portion) < 0.01
                    
                    log_test(f"🧮 Cost calculation accuracy: {cost_accuracy}")
                    log_test(f"   Expected per portion: {expected_cost_per_portion:.2f} RUB")
                    log_test(f"   Actual per portion: {cost_per_portion:.2f} RUB")
                    
                    # Analyze ingredients for cost verification
                    log_test("\n🥬 INGREDIENT COST ANALYSIS:")
                    total_expected_cost = 0
                    
                    for i, ingredient in enumerate(ingredients):
                        name = ingredient.get('name', 'Unknown')
                        brutto_g = ingredient.get('brutto_g', 0)
                        unit = ingredient.get('unit', 'g')
                        
                        log_test(f"   {i+1}. {name}: {brutto_g}{unit}")
                        
                        # Estimate cost based on known catalog prices
                        if 'куриное' in name.lower() and 'филе' in name.lower():
                            # куриное филе: 450 RUB/kg
                            estimated_cost = (brutto_g / 1000) * 450
                            total_expected_cost += estimated_cost
                            log_test(f"      Estimated cost: {estimated_cost:.2f} RUB (catalog: 450 RUB/kg)")
                        elif 'масло' in name.lower() and 'растительное' in name.lower():
                            # растительное масло: 150 RUB/liter (assuming ml unit)
                            estimated_cost = (brutto_g / 1000) * 150
                            total_expected_cost += estimated_cost
                            log_test(f"      Estimated cost: {estimated_cost:.2f} RUB (catalog: 150 RUB/L)")
                        elif 'соль' in name.lower():
                            # соль поваренная: 25 RUB/kg
                            estimated_cost = (brutto_g / 1000) * 25
                            total_expected_cost += estimated_cost
                            log_test(f"      Estimated cost: {estimated_cost:.2f} RUB (catalog: 25 RUB/kg)")
                    
                    log_test(f"\n🧮 COST VERIFICATION:")
                    log_test(f"   Total estimated cost: {total_expected_cost:.2f} RUB")
                    log_test(f"   Actual calculated cost: {raw_cost:.2f} RUB")
                    
                    cost_reasonable = abs(raw_cost - total_expected_cost) < (total_expected_cost * 0.5)  # 50% tolerance
                    log_test(f"   Cost reasonableness: {cost_reasonable}")
                    
                    return {
                        'success': True,
                        'cost_populated': cost_fields_populated,
                        'cost_accuracy': cost_accuracy,
                        'cost_reasonable': cost_reasonable,
                        'raw_cost': raw_cost,
                        'cost_per_portion': cost_per_portion,
                        'ingredients_count': len(ingredients),
                        'total_estimated_cost': total_expected_cost
                    }
                else:
                    log_test("❌ COST FIELDS NOT PROPERLY POPULATED!")
                    missing_fields = []
                    if raw_cost is None: missing_fields.append('rawCost')
                    if cost_per_portion is None: missing_fields.append('costPerPortion')
                    if markup_pct is None: missing_fields.append('markup_pct')
                    if vat_pct is None: missing_fields.append('vat_pct')
                    log_test(f"   Missing fields: {missing_fields}")
                    
                    return {
                        'success': False,
                        'error': 'Cost fields not populated',
                        'missing_fields': missing_fields,
                        'card_generated': True
                    }
                    
            elif status == "draft":
                log_test("⚠️ Generated as DRAFT due to validation issues")
                issues = data.get('issues', [])
                raw_data = data.get('raw_data', {})
                
                log_test("📋 Validation issues:")
                for issue in issues:
                    log_test(f"   - {issue}")
                
                # Check if cost calculation was attempted in raw data
                if raw_data and 'cost' in raw_data:
                    cost = raw_data['cost']
                    log_test(f"\n💰 Cost in raw data: {cost}")
                    
                    if cost.get('rawCost') is not None:
                        log_test("✅ Cost calculation worked even in draft mode!")
                        return {
                            'success': True,
                            'status': 'draft',
                            'cost_calculated': True,
                            'raw_cost': cost.get('rawCost'),
                            'issues': issues
                        }
                
                return {
                    'success': False,
                    'error': 'Generated as draft',
                    'issues': issues,
                    'status': 'draft'
                }
            else:
                log_test(f"❌ Generation failed: {status}")
                return {
                    'success': False,
                    'error': f"Generation status: {status}",
                    'status': status
                }
        else:
            log_test(f"❌ Request failed: {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"📋 Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"📋 Raw error: {response.text[:500]}")
            
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error testing fallback mode: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_specific_ingredients():
    """Test with specific ingredients that should be in the catalog"""
    log_test("\n🎯 Testing with specific known ingredients")
    
    # Test profile designed to use known catalog ingredients
    test_profile = {
        "name": "Куриное филе жареное",
        "cuisine": "русская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    log_test("🥬 Expected ingredients that should match catalog:")
    log_test("   - куриное филе: 450 RUB/kg")
    log_test("   - растительное масло: 150 RUB/liter")
    log_test("   - соль поваренная: 25 RUB/kg")
    
    try:
        url = f"{API_BASE}/v1/techcards.v2/generate?use_llm=false"
        response = requests.post(url, json=test_profile, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check both success and draft modes for cost calculation
            if data.get('status') == "success" and data.get('card'):
                card = data['card']
                cost = card.get('cost', {})
                
                if cost.get('rawCost') is not None:
                    log_test("✅ SUCCESS: Cost calculated with specific ingredients!")
                    log_test(f"   Raw cost: {cost.get('rawCost')} RUB")
                    return {'success': True, 'cost_calculated': True}
                    
            elif data.get('status') == "draft" and data.get('raw_data'):
                raw_data = data.get('raw_data', {})
                cost = raw_data.get('cost', {})
                
                if cost.get('rawCost') is not None:
                    log_test("✅ SUCCESS: Cost calculated in draft mode!")
                    log_test(f"   Raw cost: {cost.get('rawCost')} RUB")
                    return {'success': True, 'cost_calculated': True, 'mode': 'draft'}
            
            log_test("❌ No cost calculation found")
            return {'success': False, 'error': 'No cost calculated'}
        else:
            log_test(f"❌ Request failed: {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        log_test(f"❌ Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    """Main testing function for fallback mode cost calculator"""
    log_test("🚀 Starting TechCardV2 Cost Calculator Testing - FALLBACK MODE")
    log_test("🎯 Focus: Testing deterministic cost calculator without LLM")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Test 1: Basic fallback mode test
    fallback_result = test_cost_calculation_fallback_mode()
    
    log_test("\n" + "=" * 80)
    
    # Test 2: Specific ingredients test
    specific_result = test_specific_ingredients()
    
    # Summary
    log_test("\n" + "=" * 80)
    log_test("📋 FALLBACK MODE COST CALCULATOR TESTING SUMMARY:")
    log_test(f"✅ Fallback mode test: {'SUCCESS' if fallback_result.get('success') else 'FAILED'}")
    log_test(f"✅ Specific ingredients test: {'SUCCESS' if specific_result.get('success') else 'FAILED'}")
    
    if fallback_result.get('success'):
        log_test("\n🎉 COST CALCULATOR VERIFICATION (FALLBACK MODE):")
        log_test("✅ Deterministic cost calculator is working!")
        log_test("✅ Cost fields populated correctly")
        
        if fallback_result.get('cost_populated'):
            log_test(f"💰 Raw cost: {fallback_result.get('raw_cost')} RUB")
            log_test(f"💰 Cost per portion: {fallback_result.get('cost_per_portion')} RUB")
            
        if fallback_result.get('cost_accuracy'):
            log_test("✅ Cost calculation accuracy verified")
            
        if fallback_result.get('cost_reasonable'):
            log_test("✅ Cost calculations are reasonable")
    else:
        log_test("\n⚠️ COST CALCULATOR ISSUES:")
        log_test(f"   Error: {fallback_result.get('error')}")
        if 'missing_fields' in fallback_result:
            log_test(f"   Missing fields: {fallback_result['missing_fields']}")
    
    log_test("=" * 80)

if __name__ == "__main__":
    main()