#!/usr/bin/env python3
"""
Nutrition Calculator Issues Testing
Testing specific issue generation scenarios
"""

import sys
import os
sys.path.append('/app/backend')

from receptor_agent.techcards_v2.nutrition_calculator import NutritionCalculator
from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, YieldV2

def test_nutrition_issues():
    """Test specific nutrition calculator issue generation"""
    
    print("🎯 NUTRITION CALCULATOR ISSUES TESTING")
    print("=" * 60)
    
    calculator = NutritionCalculator()
    
    # Test 1: noMassForPcs issue
    print("\n1️⃣ TESTING noMassForPcs ISSUE")
    print("-" * 50)
    
    # Test with a known ingredient that doesn't have mass_per_piece_g
    test_ingredients_pcs = [
        IngredientV2(name="лук репчатый", unit="pcs", brutto_g=3, loss_pct=0, netto_g=3, allergens=[])  # Known ingredient but no mass_per_piece_g
    ]
    
    test_card_pcs = TechCardV2(
        meta={"title": "Test noMassForPcs", "version": "2.0"},
        portions=1,
        yield_=YieldV2(perPortion_g=100, perBatch_g=100),
        ingredients=test_ingredients_pcs,
        process=[
            {"n": 1, "action": "Подготовка", "time_min": 5, "temp_c": None},
            {"n": 2, "action": "Приготовление", "time_min": 10, "temp_c": 180},
            {"n": 3, "action": "Подача", "time_min": 2, "temp_c": 65}
        ],
        storage={"conditions": "test", "shelfLife_hours": 24, "servingTemp_c": 65}
    )
    
    nutrition_pcs, meta_pcs, issues_pcs = calculator.calculate_tech_card_nutrition(test_card_pcs)
    
    print(f"✅ noMassForPcs test completed")
    print(f"Coverage: {meta_pcs.coveragePct}%")
    print(f"Issues: {len(issues_pcs)}")
    
    for issue in issues_pcs:
        print(f"  - {issue['type']}: {issue['name']}")
        if issue['type'] == 'noMassForPcs':
            print(f"    ✅ noMassForPcs issue correctly generated")
    
    # Test 2: noNutrition issue
    print("\n2️⃣ TESTING noNutrition ISSUE")
    print("-" * 50)
    
    test_ingredients_unknown = [
        IngredientV2(name="совершенно неизвестный ингредиент", unit="g", brutto_g=100, loss_pct=0, netto_g=100, allergens=[])
    ]
    
    test_card_unknown = TechCardV2(
        meta={"title": "Test noNutrition", "version": "2.0"},
        portions=1,
        yield_=YieldV2(perPortion_g=100, perBatch_g=100),
        ingredients=test_ingredients_unknown,
        process=[
            {"n": 1, "action": "Подготовка", "time_min": 5, "temp_c": None},
            {"n": 2, "action": "Приготовление", "time_min": 10, "temp_c": 180},
            {"n": 3, "action": "Подача", "time_min": 2, "temp_c": 65}
        ],
        storage={"conditions": "test", "shelfLife_hours": 24, "servingTemp_c": 65}
    )
    
    nutrition_unknown, meta_unknown, issues_unknown = calculator.calculate_tech_card_nutrition(test_card_unknown)
    
    print(f"✅ noNutrition test completed")
    print(f"Coverage: {meta_unknown.coveragePct}%")
    print(f"Issues: {len(issues_unknown)}")
    
    for issue in issues_unknown:
        print(f"  - {issue['type']}: {issue['name']}")
        if issue['type'] == 'noNutrition':
            print(f"    ✅ noNutrition issue correctly generated")
    
    # Test 3: Mixed coverage scenario
    print("\n3️⃣ TESTING MIXED COVERAGE SCENARIO")
    print("-" * 50)
    
    mixed_ingredients = [
        IngredientV2(name="куриное филе", unit="g", brutto_g=200, loss_pct=0, netto_g=200, allergens=[]),  # Known
        IngredientV2(name="растительное масло", unit="ml", brutto_g=20, loss_pct=0, netto_g=20, allergens=[]),  # Known
        IngredientV2(name="экзотическая специя", unit="g", brutto_g=5, loss_pct=0, netto_g=5, allergens=[]),  # Unknown
        IngredientV2(name="лук репчатый", unit="pcs", brutto_g=2, loss_pct=0, netto_g=2, allergens=[])  # Known but no mass for pcs
    ]
    
    test_card_mixed = TechCardV2(
        meta={"title": "Test Mixed Coverage", "version": "2.0"},
        portions=1,
        yield_=YieldV2(perPortion_g=200, perBatch_g=200),
        ingredients=mixed_ingredients,
        process=[
            {"n": 1, "action": "Подготовка", "time_min": 5, "temp_c": None},
            {"n": 2, "action": "Приготовление", "time_min": 10, "temp_c": 180},
            {"n": 3, "action": "Подача", "time_min": 2, "temp_c": 65}
        ],
        storage={"conditions": "test", "shelfLife_hours": 24, "servingTemp_c": 65}
    )
    
    nutrition_mixed, meta_mixed, issues_mixed = calculator.calculate_tech_card_nutrition(test_card_mixed)
    
    print(f"✅ Mixed coverage test completed")
    print(f"Coverage: {meta_mixed.coveragePct}% (expected 50% - 2 out of 4 ingredients)")
    print(f"Issues: {len(issues_mixed)}")
    
    no_nutrition_count = 0
    no_mass_count = 0
    
    for issue in issues_mixed:
        print(f"  - {issue['type']}: {issue['name']}")
        if issue['type'] == 'noNutrition':
            no_nutrition_count += 1
        elif issue['type'] == 'noMassForPcs':
            no_mass_count += 1
    
    print(f"✅ noNutrition issues: {no_nutrition_count}")
    print(f"✅ noMassForPcs issues: {no_mass_count}")
    
    # Test 4: Fuzzy matching verification
    print("\n4️⃣ TESTING FUZZY MATCHING")
    print("-" * 50)
    
    fuzzy_test_names = [
        "куриное филе",  # Exact match
        "филе куриное",  # Different order
        "куриное мясо",  # Partial match
        "курица филе",   # Partial match
        "говядина"       # No match
    ]
    
    for name in fuzzy_test_names:
        nutrition_data = calculator.find_nutrition_data(name)
        if nutrition_data:
            print(f"✅ '{name}' → found: {nutrition_data['name']}")
        else:
            print(f"❌ '{name}' → not found")
    
    # Test 5: Catalog coverage verification
    print("\n5️⃣ TESTING CATALOG COVERAGE")
    print("-" * 50)
    
    print(f"Nutrition catalog loaded: {len(calculator.nutrition_index)} items")
    print(f"Densities available: {len(calculator.densities)} types")
    
    print("\nAvailable ingredients in catalog:")
    for name in list(calculator.nutrition_index.keys())[:10]:  # Show first 10
        print(f"  - {name}")
    
    print(f"\nDensity mappings:")
    for liquid, density in calculator.densities.items():
        print(f"  - {liquid}: {density}")
    
    print("\n" + "=" * 60)
    print("🎉 NUTRITION CALCULATOR ISSUES TESTING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_nutrition_issues()