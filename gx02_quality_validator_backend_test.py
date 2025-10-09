#!/usr/bin/env python3
"""
GX-02 Quality Validator API Backend Testing
Tests the newly implemented Quality Validator API endpoints
"""

import requests
import json
import sys
from typing import Dict, Any

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2"

def test_quality_validation_endpoint():
    """Test POST /api/v1/techcards.v2/validate/quality"""
    print("🧪 Testing Quality Validation Endpoint...")
    
    # Test with valid TechCard data
    valid_techcard = {
        "meta": {
            "title": "Говядина тушеная с овощами",
            "description": "Классическое блюдо русской кухни"
        },
        "ingredients": [
            {
                "name": "говядина",
                "brutto_g": 150.0,
                "netto_g": 120.0,
                "loss_pct": 20.0,
                "unit": "g"
            },
            {
                "name": "морковь",
                "brutto_g": 80.0,
                "netto_g": 64.0,
                "loss_pct": 20.0,
                "unit": "g"
            },
            {
                "name": "лук репчатый",
                "brutto_g": 60.0,
                "netto_g": 48.0,
                "loss_pct": 20.0,
                "unit": "g"
            }
        ],
        "process": [
            {
                "n": 1,
                "action": "Нарезать говядину кубиками",
                "time_min": 5.0,
                "temp_c": 20.0,
                "equipment": "нож"
            },
            {
                "n": 2,
                "action": "Обжарить мясо до золотистой корочки",
                "time_min": 10.0,
                "temp_c": 180.0,
                "equipment": "сковорода"
            },
            {
                "n": 3,
                "action": "Добавить овощи и тушить",
                "time_min": 30.0,
                "temp_c": 160.0,
                "equipment": "сковорода"
            }
        ],
        "yield": {
            "perPortion_g": 232.0,
            "perBatch_g": 232.0
        },
        "portions": 1
    }
    
    # Test 1: Valid TechCard
    print("  📋 Test 1: Valid TechCard validation...")
    response = requests.post(
        f"{BACKEND_URL}/validate/quality",
        json={"techcard": valid_techcard},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"    ✅ Status: {response.status_code}")
        print(f"    ✅ Quality Score: {data.get('quality_score', {}).get('score', 'N/A')}%")
        print(f"    ✅ Quality Level: {data.get('quality_score', {}).get('level', 'N/A')}")
        print(f"    ✅ Production Ready: {data.get('is_production_ready', False)}")
        print(f"    ✅ Issues Count: {len(data.get('validation_issues', []))}")
        print(f"    ✅ Fix Banners: {len(data.get('fix_banners', []))}")
        
        # Verify response structure
        required_fields = ['normalized_techcard', 'quality_score', 'validation_issues', 'fix_banners', 'is_production_ready']
        for field in required_fields:
            if field not in data:
                print(f"    ❌ Missing required field: {field}")
                return False
        print("    ✅ Response structure valid")
    else:
        print(f"    ❌ Failed with status {response.status_code}: {response.text}")
        return False
    
    # Test 2: Invalid TechCard (missing yield)
    print("  📋 Test 2: Missing yield validation...")
    invalid_techcard = valid_techcard.copy()
    del invalid_techcard['yield']
    
    response = requests.post(
        f"{BACKEND_URL}/validate/quality",
        json={"techcard": invalid_techcard},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        issues = data.get('validation_issues', [])
        yield_missing = any(issue.get('type') == 'yieldMissing' for issue in issues)
        
        if yield_missing:
            print("    ✅ Correctly detected missing yield")
            print(f"    ✅ Quality Score: {data.get('quality_score', {}).get('score', 'N/A')}% (should be lower)")
            print(f"    ✅ Production Ready: {data.get('is_production_ready', True)} (should be False)")
        else:
            print("    ❌ Failed to detect missing yield")
            return False
    else:
        print(f"    ❌ Failed with status {response.status_code}: {response.text}")
        return False
    
    # Test 3: Netto sum mismatch
    print("  📋 Test 3: Netto sum mismatch validation...")
    mismatch_techcard = valid_techcard.copy()
    mismatch_techcard['yield']['perBatch_g'] = 500.0  # Much higher than netto sum
    
    response = requests.post(
        f"{BACKEND_URL}/validate/quality",
        json={"techcard": mismatch_techcard},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        issues = data.get('validation_issues', [])
        netto_mismatch = any(issue.get('type') == 'nettoSumMismatch' for issue in issues)
        
        if netto_mismatch:
            print("    ✅ Correctly detected netto sum mismatch")
        else:
            print("    ❌ Failed to detect netto sum mismatch")
            return False
    else:
        print(f"    ❌ Failed with status {response.status_code}: {response.text}")
        return False
    
    # Test 4: Range values normalization
    print("  📋 Test 4: Range values normalization...")
    range_techcard = valid_techcard.copy()
    range_techcard['ingredients'][0]['brutto_g'] = "100-120"
    range_techcard['process'][0]['time_min'] = "5-8"
    range_techcard['process'][1]['temp_c'] = "180-200"
    
    response = requests.post(
        f"{BACKEND_URL}/validate/quality",
        json={"techcard": range_techcard},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        normalized_card = data.get('normalized_techcard', {})
        issues = data.get('validation_issues', [])
        
        # Check if ranges were normalized
        range_normalized = any(issue.get('type') == 'rangeNormalized' for issue in issues)
        
        if range_normalized:
            print("    ✅ Correctly normalized range values")
            # Check specific normalized values
            brutto_normalized = normalized_card.get('ingredients', [{}])[0].get('brutto_g')
            if brutto_normalized == 110.0:  # (100+120)/2
                print(f"    ✅ Brutto range '100-120' normalized to {brutto_normalized}")
            else:
                print(f"    ⚠️ Brutto normalization unexpected: {brutto_normalized}")
        else:
            print("    ❌ Failed to normalize range values")
            return False
    else:
        print(f"    ❌ Failed with status {response.status_code}: {response.text}")
        return False
    
    # Test 5: Error handling - invalid JSON
    print("  📋 Test 5: Error handling...")
    response = requests.post(
        f"{BACKEND_URL}/validate/quality",
        json={},  # Missing techcard
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 400:
        print("    ✅ Correctly handled missing techcard data")
    else:
        print(f"    ❌ Expected 400, got {response.status_code}")
        return False
    
    print("✅ Quality Validation Endpoint: ALL TESTS PASSED")
    return True


def test_range_normalization_endpoint():
    """Test POST /api/v1/techcards.v2/normalize"""
    print("🧪 Testing Range Normalization Endpoint...")
    
    # Test with TechCard containing range values
    range_techcard = {
        "meta": {
            "title": "Test Dish with Ranges"
        },
        "ingredients": [
            {
                "name": "ingredient1",
                "brutto_g": "100-120",
                "netto_g": "80-100",
                "loss_pct": "15-20",
                "unit": "g"
            },
            {
                "name": "ingredient2",
                "brutto_g": "50-60",
                "netto_g": "45-55",
                "loss_pct": "5-10",
                "unit": "ml"
            }
        ],
        "process": [
            {
                "n": 1,
                "action": "Test step",
                "time_min": "5-8",
                "temp_c": "180-200",
                "equipment": "pan"
            }
        ],
        "yield": {
            "perPortion_g": "150-180",
            "perBatch_g": "150-180"
        }
    }
    
    print("  📋 Test 1: Range normalization...")
    response = requests.post(
        f"{BACKEND_URL}/normalize",
        json={"techcard": range_techcard},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"    ✅ Status: {response.status_code}")
        
        # Verify response structure
        if 'normalized_techcard' not in data or 'normalization_issues' not in data:
            print("    ❌ Missing required response fields")
            return False
        
        normalized_card = data['normalized_techcard']
        issues = data['normalization_issues']
        
        # Check if ranges were normalized to numbers
        ing1_brutto = normalized_card.get('ingredients', [{}])[0].get('brutto_g')
        if ing1_brutto == 110.0:  # (100+120)/2
            print(f"    ✅ Range '100-120' normalized to {ing1_brutto}")
        else:
            print(f"    ❌ Unexpected normalization: {ing1_brutto}")
            return False
        
        # Check process step normalization
        step1_time = normalized_card.get('process', [{}])[0].get('time_min')
        if step1_time == 6.5:  # (5+8)/2
            print(f"    ✅ Time range '5-8' normalized to {step1_time}")
        else:
            print(f"    ❌ Unexpected time normalization: {step1_time}")
            return False
        
        # Check yield normalization
        yield_portion = normalized_card.get('yield', {}).get('perPortion_g')
        if yield_portion == 165.0:  # (150+180)/2
            print(f"    ✅ Yield range '150-180' normalized to {yield_portion}")
        else:
            print(f"    ❌ Unexpected yield normalization: {yield_portion}")
            return False
        
        # Check normalization issues
        range_issues = [i for i in issues if i.get('type') == 'rangeNormalized']
        if len(range_issues) >= 5:  # Should have multiple range normalizations
            print(f"    ✅ Generated {len(range_issues)} normalization issues")
        else:
            print(f"    ⚠️ Expected more normalization issues, got {len(range_issues)}")
        
        print("    ✅ Range normalization working correctly")
    else:
        print(f"    ❌ Failed with status {response.status_code}: {response.text}")
        return False
    
    # Test 2: Error handling
    print("  📋 Test 2: Error handling...")
    response = requests.post(
        f"{BACKEND_URL}/normalize",
        json={},  # Missing techcard
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 400:
        print("    ✅ Correctly handled missing techcard data")
    else:
        print(f"    ❌ Expected 400, got {response.status_code}")
        return False
    
    print("✅ Range Normalization Endpoint: ALL TESTS PASSED")
    return True


def test_quality_score_endpoint():
    """Test POST /api/v1/techcards.v2/quality/score"""
    print("🧪 Testing Quality Score Endpoint...")
    
    # Test 1: Perfect TechCard (should get 100% score)
    perfect_techcard = {
        "meta": {
            "title": "Perfect Dish",
            "description": "Well-formed tech card"
        },
        "ingredients": [
            {
                "name": "ingredient1",
                "brutto_g": 100.0,
                "netto_g": 80.0,
                "loss_pct": 20.0,
                "unit": "g"
            },
            {
                "name": "ingredient2",
                "brutto_g": 50.0,
                "netto_g": 40.0,
                "loss_pct": 20.0,
                "unit": "g"
            }
        ],
        "process": [
            {
                "n": 1,
                "action": "Step 1",
                "time_min": 5.0,
                "temp_c": 20.0,
                "equipment": "knife"
            },
            {
                "n": 2,
                "action": "Step 2",
                "time_min": 10.0,
                "temp_c": 180.0,
                "equipment": "pan"
            },
            {
                "n": 3,
                "action": "Step 3",
                "time_min": 15.0,
                "temp_c": 160.0,
                "equipment": "oven"
            }
        ],
        "yield": {
            "perPortion_g": 120.0,
            "perBatch_g": 120.0
        },
        "portions": 1
    }
    
    print("  📋 Test 1: Perfect TechCard scoring...")
    response = requests.post(
        f"{BACKEND_URL}/quality/score",
        json={"techcard": perfect_techcard},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        quality_score = data.get('quality_score', {})
        
        print(f"    ✅ Status: {response.status_code}")
        print(f"    ✅ Quality Score: {quality_score.get('score', 'N/A')}%")
        print(f"    ✅ Quality Level: {quality_score.get('level', 'N/A')}")
        print(f"    ✅ Error Count: {quality_score.get('error_count', 'N/A')}")
        print(f"    ✅ Warning Count: {quality_score.get('warning_count', 'N/A')}")
        print(f"    ✅ Info Count: {quality_score.get('info_count', 'N/A')}")
        print(f"    ✅ Production Ready: {quality_score.get('is_production_ready', False)}")
        
        # Verify high score for perfect card
        score = quality_score.get('score', 0)
        if score >= 95:
            print(f"    ✅ Perfect card scored {score}% (excellent)")
        else:
            print(f"    ⚠️ Perfect card scored only {score}% (expected ≥95%)")
        
        # Verify response structure
        required_fields = ['quality_score', 'fix_banners', 'validation_issues']
        for field in required_fields:
            if field not in data:
                print(f"    ❌ Missing required field: {field}")
                return False
        
    else:
        print(f"    ❌ Failed with status {response.status_code}: {response.text}")
        return False
    
    # Test 2: Poor TechCard (should get low score)
    poor_techcard = {
        "meta": {
            "title": "Poor Dish"
        },
        "ingredients": [
            {
                "name": "ingredient1",
                "brutto_g": 100.0,
                "netto_g": 80.0,
                "loss_pct": 20.0,
                "unit": "invalid_unit"  # Invalid unit
            }
        ],
        "process": [
            {
                "n": 1,
                "action": "Only one step",
                "time_min": 5.0,
                "temp_c": 20.0,
                "equipment": "knife"
            }
        ],
        # Missing yield - critical error
        "portions": 1
    }
    
    print("  📋 Test 2: Poor TechCard scoring...")
    response = requests.post(
        f"{BACKEND_URL}/quality/score",
        json={"techcard": poor_techcard},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        quality_score = data.get('quality_score', {})
        
        score = quality_score.get('score', 100)
        error_count = quality_score.get('error_count', 0)
        level = quality_score.get('level', 'excellent')
        is_production_ready = quality_score.get('is_production_ready', True)
        
        print(f"    ✅ Poor card scored {score}% (level: {level})")
        print(f"    ✅ Error count: {error_count}")
        print(f"    ✅ Production ready: {is_production_ready}")
        
        # Verify low score for poor card
        if score < 80 and error_count > 0 and not is_production_ready:
            print("    ✅ Correctly identified poor quality card")
        else:
            print(f"    ❌ Poor card assessment incorrect: score={score}, errors={error_count}, ready={is_production_ready}")
            return False
        
    else:
        print(f"    ❌ Failed with status {response.status_code}: {response.text}")
        return False
    
    # Test 3: Error handling
    print("  📋 Test 3: Error handling...")
    response = requests.post(
        f"{BACKEND_URL}/quality/score",
        json={},  # Missing techcard
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 400:
        print("    ✅ Correctly handled missing techcard data")
    else:
        print(f"    ❌ Expected 400, got {response.status_code}")
        return False
    
    print("✅ Quality Score Endpoint: ALL TESTS PASSED")
    return True


def test_integration_scenarios():
    """Test comprehensive integration scenarios"""
    print("🧪 Testing Integration Scenarios...")
    
    # Test 1: Missing Yield Test
    print("  📋 Test 1: Missing Yield Detection...")
    no_yield_card = {
        "meta": {"title": "No Yield Card"},
        "ingredients": [{"name": "test", "brutto_g": 100, "netto_g": 80, "loss_pct": 20, "unit": "g"}],
        "process": [
            {"n": 1, "action": "Step 1", "time_min": 5, "temp_c": 20, "equipment": "knife"},
            {"n": 2, "action": "Step 2", "time_min": 10, "temp_c": 180, "equipment": "pan"},
            {"n": 3, "action": "Step 3", "time_min": 15, "temp_c": 160, "equipment": "oven"}
        ]
        # Missing yield
    }
    
    response = requests.post(f"{BACKEND_URL}/validate/quality", json={"techcard": no_yield_card})
    if response.status_code == 200:
        data = response.json()
        issues = data.get('validation_issues', [])
        yield_error = any(issue.get('type') == 'yieldMissing' for issue in issues)
        banners = data.get('fix_banners', [])
        error_banner = any(banner.get('type') == 'error' for banner in banners)
        
        if yield_error and error_banner:
            print("    ✅ Missing yield correctly detected with error banner")
        else:
            print("    ❌ Missing yield detection failed")
            return False
    else:
        print(f"    ❌ Request failed: {response.status_code}")
        return False
    
    # Test 2: Netto Sum Mismatch Test
    print("  📋 Test 2: Netto Sum Mismatch Detection...")
    mismatch_card = {
        "meta": {"title": "Mismatch Card"},
        "ingredients": [
            {"name": "ing1", "brutto_g": 100, "netto_g": 80, "loss_pct": 20, "unit": "g"},
            {"name": "ing2", "brutto_g": 50, "netto_g": 40, "loss_pct": 20, "unit": "g"}
        ],
        "process": [
            {"n": 1, "action": "Step 1", "time_min": 5, "temp_c": 20, "equipment": "knife"},
            {"n": 2, "action": "Step 2", "time_min": 10, "temp_c": 180, "equipment": "pan"},
            {"n": 3, "action": "Step 3", "time_min": 15, "temp_c": 160, "equipment": "oven"}
        ],
        "yield": {
            "perPortion_g": 200.0,  # Total netto is 120, this is 200 - significant mismatch
            "perBatch_g": 200.0
        }
    }
    
    response = requests.post(f"{BACKEND_URL}/validate/quality", json={"techcard": mismatch_card})
    if response.status_code == 200:
        data = response.json()
        issues = data.get('validation_issues', [])
        netto_error = any(issue.get('type') == 'nettoSumMismatch' for issue in issues)
        
        if netto_error:
            print("    ✅ Netto sum mismatch correctly detected")
        else:
            print("    ❌ Netto sum mismatch detection failed")
            return False
    else:
        print(f"    ❌ Request failed: {response.status_code}")
        return False
    
    # Test 3: Range Normalization Test
    print("  📋 Test 3: Range Normalization...")
    range_card = {
        "meta": {"title": "Range Card"},
        "ingredients": [{"name": "ing1", "brutto_g": "100-120", "netto_g": "80-100", "loss_pct": 20, "unit": "g"}],
        "process": [
            {"n": 1, "action": "Step 1", "time_min": "5-8", "temp_c": "180-200", "equipment": "pan"},
            {"n": 2, "action": "Step 2", "time_min": 10, "temp_c": 160, "equipment": "oven"},
            {"n": 3, "action": "Step 3", "time_min": 15, "temp_c": 140, "equipment": "plate"}
        ],
        "yield": {"perPortion_g": 90, "perBatch_g": 90}
    }
    
    response = requests.post(f"{BACKEND_URL}/normalize", json={"techcard": range_card})
    if response.status_code == 200:
        data = response.json()
        normalized = data.get('normalized_techcard', {})
        issues = data.get('normalization_issues', [])
        
        # Check if "100-120" became 110.0
        brutto_normalized = normalized.get('ingredients', [{}])[0].get('brutto_g')
        time_normalized = normalized.get('process', [{}])[0].get('time_min')
        temp_normalized = normalized.get('process', [{}])[0].get('temp_c')
        
        if (brutto_normalized == 110.0 and time_normalized == 6.5 and temp_normalized == 190.0):
            print("    ✅ Range normalization working correctly")
            print(f"      - '100-120' → {brutto_normalized}")
            print(f"      - '5-8' → {time_normalized}")
            print(f"      - '180-200' → {temp_normalized}")
        else:
            print(f"    ❌ Range normalization failed: {brutto_normalized}, {time_normalized}, {temp_normalized}")
            return False
    else:
        print(f"    ❌ Request failed: {response.status_code}")
        return False
    
    # Test 4: Process Steps Test
    print("  📋 Test 4: Process Steps Validation...")
    few_steps_card = {
        "meta": {"title": "Few Steps Card"},
        "ingredients": [{"name": "ing1", "brutto_g": 100, "netto_g": 80, "loss_pct": 20, "unit": "g"}],
        "process": [
            {"n": 1, "action": "Only step", "time_min": 5, "temp_c": 20, "equipment": "knife"}
        ],  # Less than 3 steps
        "yield": {"perPortion_g": 80, "perBatch_g": 80}
    }
    
    response = requests.post(f"{BACKEND_URL}/validate/quality", json={"techcard": few_steps_card})
    if response.status_code == 200:
        data = response.json()
        issues = data.get('validation_issues', [])
        steps_error = any(issue.get('type') == 'processStepsInsufficient' for issue in issues)
        
        if steps_error:
            print("    ✅ Insufficient process steps correctly detected")
        else:
            print("    ❌ Process steps validation failed")
            return False
    else:
        print(f"    ❌ Request failed: {response.status_code}")
        return False
    
    print("✅ Integration Scenarios: ALL TESTS PASSED")
    return True


def test_performance():
    """Test API performance"""
    print("🧪 Testing API Performance...")
    
    import time
    
    test_card = {
        "meta": {"title": "Performance Test Card"},
        "ingredients": [
            {"name": f"ingredient_{i}", "brutto_g": 100, "netto_g": 80, "loss_pct": 20, "unit": "g"}
            for i in range(10)  # 10 ingredients
        ],
        "process": [
            {"n": i+1, "action": f"Step {i+1}", "time_min": 5, "temp_c": 180, "equipment": "pan"}
            for i in range(5)  # 5 process steps
        ],
        "yield": {"perPortion_g": 800, "perBatch_g": 800}
    }
    
    # Test validation endpoint performance
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/validate/quality", json={"techcard": test_card})
    end_time = time.time()
    
    validation_time = end_time - start_time
    
    if response.status_code == 200 and validation_time < 2.0:
        print(f"    ✅ Quality validation completed in {validation_time:.2f}s (< 2s requirement)")
    else:
        print(f"    ❌ Quality validation took {validation_time:.2f}s (≥ 2s) or failed")
        return False
    
    # Test normalization endpoint performance
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/normalize", json={"techcard": test_card})
    end_time = time.time()
    
    normalize_time = end_time - start_time
    
    if response.status_code == 200 and normalize_time < 2.0:
        print(f"    ✅ Range normalization completed in {normalize_time:.2f}s (< 2s requirement)")
    else:
        print(f"    ❌ Range normalization took {normalize_time:.2f}s (≥ 2s) or failed")
        return False
    
    # Test quality score endpoint performance
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/quality/score", json={"techcard": test_card})
    end_time = time.time()
    
    score_time = end_time - start_time
    
    if response.status_code == 200 and score_time < 2.0:
        print(f"    ✅ Quality scoring completed in {score_time:.2f}s (< 2s requirement)")
    else:
        print(f"    ❌ Quality scoring took {score_time:.2f}s (≥ 2s) or failed")
        return False
    
    print("✅ Performance Tests: ALL TESTS PASSED")
    return True


def main():
    """Run all GX-02 Quality Validator API tests"""
    print("🚀 Starting GX-02 Quality Validator API Testing")
    print("=" * 60)
    
    test_results = []
    
    # Run all test suites
    test_suites = [
        ("Quality Validation Endpoint", test_quality_validation_endpoint),
        ("Range Normalization Endpoint", test_range_normalization_endpoint),
        ("Quality Score Endpoint", test_quality_score_endpoint),
        ("Integration Scenarios", test_integration_scenarios),
        ("Performance Tests", test_performance)
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n📊 Running {suite_name}...")
        try:
            result = test_func()
            test_results.append((suite_name, result))
            if result:
                print(f"✅ {suite_name}: PASSED")
            else:
                print(f"❌ {suite_name}: FAILED")
        except Exception as e:
            print(f"❌ {suite_name}: ERROR - {str(e)}")
            test_results.append((suite_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 GX-02 Quality Validator API Test Summary:")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for suite_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {suite_name}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 ALL GX-02 QUALITY VALIDATOR API TESTS PASSED!")
        print("\n✅ Key Achievements:")
        print("  • Quality validation endpoint working correctly")
        print("  • Range normalization (0-4 → numbers) functional")
        print("  • Quality scoring with proper levels (excellent/good/needs_improvement/poor)")
        print("  • Error detection for missing yield, netto sum mismatch, insufficient process steps")
        print("  • Fix banners generation for user-friendly error display")
        print("  • Performance under 2 seconds for all endpoints")
        print("  • Proper error handling for invalid requests")
        return True
    else:
        print("❌ SOME TESTS FAILED - GX-02 Quality Validator API needs attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)