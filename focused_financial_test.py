#!/usr/bin/env python3
"""
Focused Financial Analysis Test for Pasta Carbonara
Проверить успешность последней генерации техкарты и её финансовый анализ

Based on review request:
1. GET /api/v1/user/history?user_id=demo_user (find latest Pasta Carbonara)
2. Verify V2 structure with cost.rawCost and cost.costPerPortion
3. Check yield.perPortion_g for correct calculations
4. Verify financial logic (if portion=1, total cost ≈ cost per portion)
"""

import requests
import json
import time
import sys
from datetime import datetime

# Backend URL
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
TEST_USER_ID = "demo_user"

def test_user_history():
    """Test 1: Check user history for latest tech card"""
    print("🔍 Test 1: Checking user history for latest tech card")
    
    # Try the correct endpoint based on logs
    url = f"{API_BASE}/user-history/{TEST_USER_ID}"
    
    try:
        response = requests.get(url, timeout=15)
        print(f"   GET {url}")
        print(f"   Response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                latest = data[0]
                print(f"   ✅ Found {len(data)} tech cards")
                print(f"   Latest: '{latest.get('name', 'Unknown')}' (ID: {latest.get('id', 'Unknown')})")
                return True, latest
            else:
                print(f"   ⚠️ No tech cards found in history")
                return False, None
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None

def test_generate_pasta_carbonara():
    """Test 2: Generate Pasta Carbonara tech card"""
    print("🍝 Test 2: Generating Pasta Carbonara tech card")
    
    url = f"{API_BASE}/v1/techcards.v2/generate"
    payload = {
        "name": "Паста карбонара с беконом и пармезаном",
        "cuisine": "итальянская",
        "equipment": ["плита", "сковорода", "кастрюля"],
        "budget": 800.0,
        "dietary": [],
        "user_id": TEST_USER_ID
    }
    
    try:
        print(f"   POST {url}")
        print(f"   Dish: {payload['name']}")
        
        response = requests.post(url, json=payload, timeout=60)
        print(f"   Response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'card' in data:
                card = data['card']
                card_id = card.get('meta', {}).get('id', 'Unknown')
                print(f"   ✅ Generated successfully (ID: {card_id})")
                return True, card
            else:
                print(f"   ❌ No card in response")
                return False, None
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None

def test_financial_structure(card):
    """Test 3: Verify financial structure V2"""
    print("💰 Test 3: Verifying financial structure V2")
    
    if not card:
        print("   ❌ No card to test")
        return False
    
    # Check basic structure
    print(f"   Card fields: {list(card.keys())}")
    
    # Check cost data
    cost_data = card.get('cost', {})
    print(f"   Cost data: {cost_data}")
    
    # Check yield data
    yield_data = card.get('yield', {})
    print(f"   Yield data: {yield_data}")
    
    # Check portions
    portions = card.get('portions', 'Not found')
    print(f"   Portions: {portions}")
    
    # Verify required fields
    has_raw_cost = 'rawCost' in cost_data
    has_cost_per_portion = 'costPerPortion' in cost_data
    has_per_portion_g = 'perPortion_g' in yield_data
    
    print(f"   Has rawCost: {has_raw_cost}")
    print(f"   Has costPerPortion: {has_cost_per_portion}")
    print(f"   Has perPortion_g: {has_per_portion_g}")
    
    if has_raw_cost and has_cost_per_portion and has_per_portion_g:
        print("   ✅ All required financial fields present")
        return True
    else:
        print("   ❌ Missing required financial fields")
        return False

def test_financial_logic(card):
    """Test 4: Verify financial logic consistency"""
    print("🧮 Test 4: Verifying financial logic consistency")
    
    if not card:
        print("   ❌ No card to test")
        return False
    
    cost_data = card.get('cost', {})
    yield_data = card.get('yield', {})
    portions = card.get('portions', 1)
    
    raw_cost = cost_data.get('rawCost', 0)
    cost_per_portion = cost_data.get('costPerPortion', 0)
    per_portion_g = yield_data.get('perPortion_g', 0)
    
    print(f"   Raw cost: {raw_cost}")
    print(f"   Cost per portion: {cost_per_portion}")
    print(f"   Per portion (g): {per_portion_g}")
    print(f"   Portions: {portions}")
    
    # Logic check for single portion
    if portions == 1:
        if raw_cost > 0 and cost_per_portion > 0:
            ratio = abs(raw_cost - cost_per_portion) / max(raw_cost, cost_per_portion)
            print(f"   Cost difference ratio: {ratio:.2%}")
            
            if ratio <= 0.1:  # 10% tolerance
                print("   ✅ Financial logic consistent (single portion)")
                return True
            else:
                print("   ⚠️ Cost inconsistency detected")
                print(f"   Expected: rawCost ≈ costPerPortion for single portion")
                print(f"   Actual: {raw_cost} vs {cost_per_portion}")
                return False
        else:
            print("   ❌ Missing cost values")
            return False
    else:
        # Multiple portions logic
        expected_cost_per_portion = raw_cost / portions if portions > 0 else 0
        if abs(cost_per_portion - expected_cost_per_portion) / max(expected_cost_per_portion, 0.01) <= 0.1:
            print(f"   ✅ Financial logic consistent ({portions} portions)")
            return True
        else:
            print(f"   ❌ Cost calculation error for {portions} portions")
            return False

def main():
    """Main test execution"""
    print("🚀 PASTA CARBONARA FINANCIAL ANALYSIS TEST")
    print("=" * 60)
    print(f"Backend: {BACKEND_URL}")
    print(f"User: {TEST_USER_ID}")
    print("=" * 60)
    print()
    
    results = []
    card = None
    
    # Test 1: Check user history
    success, latest_card = test_user_history()
    results.append(("User History", success))
    if success and latest_card:
        card = latest_card
    print()
    
    # Test 2: Generate if no history found
    if not card:
        success, generated_card = test_generate_pasta_carbonara()
        results.append(("Generate Pasta Carbonara", success))
        if success:
            card = generated_card
        print()
    
    # Test 3: Verify financial structure
    if card:
        success = test_financial_structure(card)
        results.append(("Financial Structure V2", success))
        print()
        
        # Test 4: Verify financial logic
        success = test_financial_logic(card)
        results.append(("Financial Logic", success))
        print()
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print()
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 FINANCIAL ANALYSIS: OPERATIONAL")
        return 0
    else:
        print("🚨 FINANCIAL ANALYSIS: ISSUES DETECTED")
        return 1

if __name__ == "__main__":
    sys.exit(main())