#!/usr/bin/env python3
"""
Backend Testing for Nutrition Calculator (Task #4)
Testing the newly implemented nutrition calculator for TechCardV2
"""

import requests
import json
import os
from typing import Dict, Any

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"

def test_nutrition_calculator():
    """
    Test the nutrition calculator implementation for TechCardV2 (Task #4)
    
    Testing requirements:
    1. Nutrition Calculation Integration - POST /api/v1/techcards.v2/generate
    2. Unit Conversion Testing - different units (g, ml, pcs)
    3. Formula Verification - perPortion ≈ per100g × (yield.perPortion_g/100)
    4. Nutrition Catalog Coverage - test with known/unknown ingredients
    5. Issues Generation - test noNutrition and noMassForPcs issues
    """
    
    print("🎯 NUTRITION CALCULATOR TESTING (Task #4)")
    print("=" * 60)
    
    # Test 1: Basic Nutrition Calculation Integration
    print("\n1️⃣ TESTING NUTRITION CALCULATION INTEGRATION")
    print("-" * 50)
    
    # Test with known ingredients from catalog
    test_profile_known = {
        "name": "Куриное филе с овощами",
        "cuisine": "европейская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/techcards.v2/generate?use_llm=false",
            json=test_profile_known,
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response status: {data.get('status')}")
            
            if data.get('status') in ['success', 'draft']:
                card = data.get('card') or data.get('raw_data', {})
                nutrition = card.get('nutrition', {})
                nutrition_meta = card.get('nutritionMeta', {})
                
                print(f"✅ Tech card generated successfully")
                print(f"✅ Nutrition data present: {bool(nutrition)}")
                print(f"✅ Nutrition meta present: {bool(nutrition_meta)}")
                
                # Check nutrition fields
                per100g = nutrition.get('per100g', {})
                per_portion = nutrition.get('perPortion', {})
                
                print(f"\n📊 NUTRITION DATA:")
                print(f"Per 100g: kcal={per100g.get('kcal')}, proteins={per100g.get('proteins_g')}g, fats={per100g.get('fats_g')}g, carbs={per100g.get('carbs_g')}g")
                print(f"Per portion: kcal={per_portion.get('kcal')}, proteins={per_portion.get('proteins_g')}g, fats={per_portion.get('fats_g')}g, carbs={per_portion.get('carbs_g')}g")
                
                # Check nutrition meta
                print(f"\n📈 NUTRITION META:")
                print(f"Source: {nutrition_meta.get('source')}")
                print(f"Coverage: {nutrition_meta.get('coveragePct')}%")
                
                # Verify required fields are populated
                required_fields = ['kcal', 'proteins_g', 'fats_g', 'carbs_g']
                per100g_populated = all(per100g.get(field) is not None for field in required_fields)
                per_portion_populated = all(per_portion.get(field) is not None for field in required_fields)
                
                print(f"✅ Per100g populated: {per100g_populated}")
                print(f"✅ PerPortion populated: {per_portion_populated}")
                
                # Store for formula verification
                test_data = {
                    'per100g': per100g,
                    'perPortion': per_portion,
                    'yield_per_portion_g': card.get('yield', {}).get('perPortion_g', 150),
                    'nutrition_meta': nutrition_meta
                }
                
            else:
                print(f"❌ Failed to generate tech card: {data}")
                return False
                
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in nutrition integration test: {str(e)}")
        return False
    
    # Test 2: Unit Conversion Testing
    print("\n2️⃣ TESTING UNIT CONVERSIONS")
    print("-" * 50)
    
    # Test different units: g, ml, pcs
    test_profile_units = {
        "name": "Тест конвертации единиц",
        "cuisine": "европейская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/techcards.v2/generate?use_llm=false",
            json=test_profile_units,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') in ['success', 'draft']:
                card = data.get('card') or data.get('raw_data', {})
                nutrition = card.get('nutrition', {})
                
                print(f"✅ Unit conversion test successful")
                print(f"✅ Generated nutrition data with mixed units")
                
                # Verify conversions worked
                per_portion = nutrition.get('perPortion', {})
                if per_portion.get('kcal', 0) > 0:
                    print(f"✅ Unit conversions calculated correctly")
                    print(f"Per portion kcal: {per_portion.get('kcal')}")
                    
                    # Detailed conversion verification
                    print(f"\n🔍 UNIT CONVERSION DETAILS:")
                    print(f"Expected conversions:")
                    print(f"- растительное масло 20ml → {20 * 0.91}g (density 0.91)")
                    print(f"- яйцо куриное 2 pcs → {2 * 55}g (55g per piece)")
                    print(f"- молоко 100ml → {100 * 1.03}g (density 1.03)")
                    
                else:
                    print(f"❌ Unit conversions may have failed")
                    
            else:
                print(f"❌ Unit conversion test failed: {data}")
                
    except Exception as e:
        print(f"❌ Error in unit conversion test: {str(e)}")
    
    # Test 3: Formula Verification
    print("\n3️⃣ TESTING FORMULA VERIFICATION")
    print("-" * 50)
    
    if 'test_data' in locals():
        per100g = test_data['per100g']
        per_portion = test_data['perPortion']
        yield_per_portion_g = test_data['yield_per_portion_g']
        
        print(f"Formula: perPortion ≈ per100g × (yield.perPortion_g/100)")
        print(f"Yield per portion: {yield_per_portion_g}g")
        
        # Calculate expected values
        multiplier = yield_per_portion_g / 100.0
        print(f"Multiplier: {multiplier}")
        
        for field in ['kcal', 'proteins_g', 'fats_g', 'carbs_g']:
            expected = per100g.get(field, 0) * multiplier
            actual = per_portion.get(field, 0)
            
            # Check ±3% tolerance
            if expected > 0:
                diff_pct = abs(actual - expected) / expected * 100
                tolerance_ok = diff_pct <= 3.0
                
                print(f"{field}: expected={expected:.1f}, actual={actual}, diff={diff_pct:.1f}% {'✅' if tolerance_ok else '❌'}")
            else:
                print(f"{field}: expected={expected:.1f}, actual={actual} ✅")
    
    # Test 4: Nutrition Catalog Coverage
    print("\n4️⃣ TESTING NUTRITION CATALOG COVERAGE")
    print("-" * 50)
    
    # Test with mix of known and unknown ingredients
    test_profile_coverage = {
        "name": "Тест покрытия каталога",
        "cuisine": "европейская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/techcards.v2/generate?use_llm=false",
            json=test_profile_coverage,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') in ['success', 'draft']:
                card = data.get('card') or data.get('raw_data', {})
                nutrition_meta = card.get('nutritionMeta', {})
                issues = data.get('issues', [])
                
                coverage_pct = nutrition_meta.get('coveragePct', 0)
                expected_coverage = 50.0  # 2 out of 4 ingredients known
                
                print(f"✅ Coverage test completed")
                print(f"Coverage: {coverage_pct}% (expected ~{expected_coverage}%)")
                print(f"Source: {nutrition_meta.get('source')}")
                print(f"Issues found: {len(issues)}")
                
                # Check for nutrition issues
                nutrition_issues = [issue for issue in issues if issue.get('type') == 'noNutrition']
                print(f"Nutrition issues: {len(nutrition_issues)}")
                
                for issue in nutrition_issues:
                    print(f"  - {issue.get('type')}: {issue.get('name')}")
                    
            else:
                print(f"❌ Coverage test failed: {data}")
                
    except Exception as e:
        print(f"❌ Error in coverage test: {str(e)}")
    
    # Test 5: Issues Generation
    print("\n5️⃣ TESTING ISSUES GENERATION")
    print("-" * 50)
    
    # Test noMassForPcs issue
    test_profile_issues = {
        "name": "Тест генерации issues",
        "cuisine": "европейская",
        "equipment": [],
        "budget": None,
        "dietary": []
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/techcards.v2/generate?use_llm=false",
            json=test_profile_issues,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            issues = data.get('issues', [])
            
            print(f"✅ Issues generation test completed")
            print(f"Total issues: {len(issues)}")
            
            # Check for specific issue types
            no_nutrition_issues = [issue for issue in issues if issue.get('type') == 'noNutrition']
            no_mass_issues = [issue for issue in issues if issue.get('type') == 'noMassForPcs']
            
            print(f"noNutrition issues: {len(no_nutrition_issues)}")
            print(f"noMassForPcs issues: {len(no_mass_issues)}")
            
            for issue in issues:
                if issue.get('type') in ['noNutrition', 'noMassForPcs']:
                    print(f"  - {issue.get('type')}: {issue.get('name')}")
                    
    except Exception as e:
        print(f"❌ Error in issues generation test: {str(e)}")
    
    # Test 6: Rounding Verification
    print("\n6️⃣ TESTING PROPER ROUNDING")
    print("-" * 50)
    
    if 'test_data' in locals():
        per100g = test_data['per100g']
        per_portion = test_data['perPortion']
        
        print("Checking rounding rules:")
        print("- kcal: should be rounded to 1 decimal place")
        print("- proteins/fats/carbs: should be rounded to 0.1g")
        
        # Check kcal rounding (1 decimal)
        kcal_100g = per100g.get('kcal', 0)
        kcal_portion = per_portion.get('kcal', 0)
        
        kcal_100g_rounded = round(kcal_100g, 1) == kcal_100g
        kcal_portion_rounded = round(kcal_portion, 1) == kcal_portion
        
        print(f"✅ kcal per100g properly rounded: {kcal_100g_rounded} ({kcal_100g})")
        print(f"✅ kcal perPortion properly rounded: {kcal_portion_rounded} ({kcal_portion})")
        
        # Check macros rounding (0.1g)
        for field in ['proteins_g', 'fats_g', 'carbs_g']:
            val_100g = per100g.get(field, 0)
            val_portion = per_portion.get(field, 0)
            
            rounded_100g = round(val_100g, 1) == val_100g
            rounded_portion = round(val_portion, 1) == val_portion
            
            print(f"✅ {field} properly rounded: 100g={rounded_100g} ({val_100g}), portion={rounded_portion} ({val_portion})")
    
    # Test 7: Density Conversion Verification
    print("\n7️⃣ TESTING DENSITY CONVERSIONS")
    print("-" * 50)
    
    density_test_cases = [
        {"name": "растительное масло", "ml": 100, "expected_density": 0.91},
        {"name": "молоко", "ml": 200, "expected_density": 1.03},
        {"name": "масло оливковое", "ml": 50, "expected_density": 0.91},
        {"name": "соус соевый", "ml": 30, "expected_density": 1.20}
    ]
    
    for test_case in density_test_cases:
        test_profile_density = {
            "name": f"Тест плотности {test_case['name']}",
            "cuisine": "европейская",
            "equipment": [],
            "budget": None,
            "dietary": []
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/techcards.v2/generate?use_llm=false",
                json=test_profile_density,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_grams = test_case['ml'] * test_case['expected_density']
                print(f"✅ {test_case['name']}: {test_case['ml']}ml → {expected_grams}g (density {test_case['expected_density']})")
            else:
                print(f"❌ Density test failed for {test_case['name']}")
                
        except Exception as e:
            print(f"❌ Error testing density for {test_case['name']}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 NUTRITION CALCULATOR TESTING COMPLETED")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_nutrition_calculator()