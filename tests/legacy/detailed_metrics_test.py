#!/usr/bin/env python3
"""
STANDARD PORTION BY DEFAULT - DETAILED METRICS TESTING
Get detailed metrics and validation data for the DoD implementation
"""

import requests
import json
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

def test_detailed_metrics():
    """Test with detailed metrics collection"""
    print("🔍 DETAILED METRICS TESTING FOR STANDARD PORTION BY DEFAULT")
    print("=" * 70)
    
    test_cases = [
        {"name": "Омлет с зеленью", "expected_archetype": "default", "expected_yield": 200},
        {"name": "Стейк с грибным соусом", "expected_archetype": "горячее", "expected_yield": 240},
        {"name": "Суп дня овощной", "expected_archetype": "суп", "expected_yield": 330}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 DETAILED TEST {i}: {test_case['name']}")
        print("-" * 50)
        
        # Generate TechCard
        payload = {"name": test_case["name"], "cuisine": "русская"}
        response = requests.post(f"{API_BASE}/techcards.v2/generate", json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Generation failed: {response.status_code}")
            continue
            
        data = response.json()
        techcard = data.get("card")
        
        if not techcard:
            print("❌ No techcard in response")
            continue
        
        # Extract detailed metrics
        print("📊 PORTION NORMALIZATION METRICS:")
        portions = techcard.get("portions", 0)
        yield_data = techcard.get("yield", {})
        per_portion_g = yield_data.get("perPortion_g", 0)
        per_batch_g = yield_data.get("perBatch_g", 0)
        
        print(f"   Portions: {portions}")
        print(f"   Yield per portion: {per_portion_g}g")
        print(f"   Yield per batch: {per_batch_g}g")
        print(f"   Expected yield: {test_case['expected_yield']}g")
        print(f"   Yield accuracy: {abs(per_portion_g - test_case['expected_yield']) <= 1}")
        
        print("\n🎯 ARCHETYPE DETECTION:")
        meta = techcard.get("meta", {})
        detected_archetype = meta.get("archetype")
        scale_factor = meta.get("scale_factor")
        original_sum_netto = meta.get("original_sum_netto")
        normalized = meta.get("normalized")
        
        print(f"   Detected archetype: {detected_archetype}")
        print(f"   Expected archetype: {test_case['expected_archetype']}")
        print(f"   Archetype correct: {detected_archetype == test_case['expected_archetype']}")
        print(f"   Scale factor: {scale_factor}")
        print(f"   Original sum netto: {original_sum_netto}g")
        print(f"   Normalized flag: {normalized}")
        
        print("\n⚖️ GX-02 COMPLIANCE:")
        ingredients = techcard.get("ingredients", [])
        sum_netto = 0
        units_normalized = True
        
        for ingredient in ingredients:
            netto = ingredient.get("netto_g") or ingredient.get("netto", 0)
            unit = ingredient.get("unit", "")
            if isinstance(netto, (int, float)):
                sum_netto += netto
            if unit != "g":
                units_normalized = False
        
        difference_pct = abs(sum_netto - per_portion_g) / per_portion_g * 100 if per_portion_g > 0 else 0
        gx02_compliant = difference_pct <= 5.0
        
        print(f"   Sum netto: {sum_netto:.1f}g")
        print(f"   Target yield: {per_portion_g}g")
        print(f"   Difference: {difference_pct:.2f}%")
        print(f"   GX-02 compliant (≤5%): {gx02_compliant}")
        print(f"   All units normalized to 'g': {units_normalized}")
        print(f"   Ingredients count: {len(ingredients)}")
        
        print("\n📊 XLSX EXPORT TEST:")
        export_response = requests.post(f"{API_BASE}/techcards.v2/export/iiko.xlsx", json=techcard, timeout=30)
        
        if export_response.status_code == 200:
            content_length = len(export_response.content)
            content_type = export_response.headers.get('content-type', '')
            print(f"   Export successful: ✅")
            print(f"   File size: {content_length} bytes")
            print(f"   Content type: {content_type}")
            print(f"   Expected output qty in export: {per_portion_g}g")
        else:
            print(f"   Export failed: ❌ ({export_response.status_code})")
        
        print("\n📋 AUDIT TRAIL:")
        print(f"   Scale factor in range (0.1-2.0): {0.1 <= scale_factor <= 2.0 if scale_factor else False}")
        print(f"   All audit fields present: {all([scale_factor, detected_archetype, original_sum_netto, normalized])}")
        
        # Performance metrics
        timings = meta.get("timings", {})
        if timings:
            print(f"\n⏱️ PERFORMANCE METRICS:")
            print(f"   Total generation time: {timings.get('total_ms', 0)}ms")
            print(f"   Portion normalization time: {timings.get('portion_normalize_ms', 0)}ms")
        
        print(f"\n✅ OVERALL RESULT: {'PASS' if all([portions == 1, abs(per_portion_g - test_case['expected_yield']) <= 1, detected_archetype == test_case['expected_archetype'], gx02_compliant, units_normalized, export_response.status_code == 200]) else 'FAIL'}")

if __name__ == "__main__":
    test_detailed_metrics()