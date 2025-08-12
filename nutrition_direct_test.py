#!/usr/bin/env python3
"""
Direct Nutrition Calculator Testing
Testing the nutrition calculator directly with controlled data
"""

import sys
import os
sys.path.append('/app/backend')

from receptor_agent.techcards_v2.nutrition_calculator import NutritionCalculator, calculate_nutrition_for_tech_card
from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, YieldV2

def test_direct_nutrition_calculator():
    """Test the nutrition calculator directly with controlled data"""
    
    print("🎯 DIRECT NUTRITION CALCULATOR TESTING")
    print("=" * 60)
    
    # Test 1: Known ingredients with different units
    print("\n1️⃣ TESTING KNOWN INGREDIENTS WITH DIFFERENT UNITS")
    print("-" * 50)
    
    # Create test tech card with known ingredients
    test_ingredients = [
        IngredientV2(name="куриное филе", unit="g", brutto_g=400, loss_pct=5, netto_g=380, allergens=[]),
        IngredientV2(name="растительное масло", unit="ml", brutto_g=30, loss_pct=0, netto_g=30, allergens=[]),
        IngredientV2(name="яйцо куриное", unit="pcs", brutto_g=2, loss_pct=0, netto_g=2, allergens=[]),
        IngredientV2(name="соль поваренная", unit="g", brutto_g=5, loss_pct=0, netto_g=5, allergens=[])
    ]
    
    test_yield = YieldV2(perPortion_g=150, perBatch_g=600)
    
    test_card = TechCardV2(
        meta={"title": "Test Card", "version": "2.0"},
        portions=4,
        yield_=test_yield,
        ingredients=test_ingredients,
        process=[
            {"n": 1, "action": "Подготовка ингредиентов", "time_min": 10, "temp_c": None},
            {"n": 2, "action": "Приготовление", "time_min": 20, "temp_c": 180},
            {"n": 3, "action": "Подача", "time_min": 5, "temp_c": 65}
        ],
        storage={"conditions": "test", "shelfLife_hours": 24, "servingTemp_c": 65}
    )
    
    # Calculate nutrition
    calculator = NutritionCalculator()
    nutrition, nutrition_meta, issues = calculator.calculate_tech_card_nutrition(test_card)
    
    print(f"✅ Nutrition calculation completed")
    print(f"Coverage: {nutrition_meta.coveragePct}%")
    print(f"Source: {nutrition_meta.source}")
    print(f"Issues: {len(issues)}")
    
    print(f"\n📊 NUTRITION RESULTS:")
    print(f"Per 100g: kcal={nutrition.per100g.kcal}, proteins={nutrition.per100g.proteins_g}g, fats={nutrition.per100g.fats_g}g, carbs={nutrition.per100g.carbs_g}g")
    print(f"Per portion: kcal={nutrition.perPortion.kcal}, proteins={nutrition.perPortion.proteins_g}g, fats={nutrition.perPortion.fats_g}g, carbs={nutrition.perPortion.carbs_g}g")
    
    # Test 2: Unit conversions verification
    print("\n2️⃣ TESTING UNIT CONVERSIONS")
    print("-" * 50)
    
    for ingredient in test_ingredients:
        ingredient_nutrition, status = calculator.calculate_ingredient_nutrition(ingredient)
        if ingredient_nutrition:
            print(f"✅ {ingredient.name} ({ingredient.netto_g} {ingredient.unit}): {ingredient_nutrition['kcal']:.1f} kcal - {status}")
        else:
            print(f"❌ {ingredient.name}: {status}")
    
    # Test 3: Unknown ingredients (issues generation)
    print("\n3️⃣ TESTING UNKNOWN INGREDIENTS")
    print("-" * 50)
    
    unknown_ingredients = [
        IngredientV2(name="экзотическая специя", unit="g", brutto_g=5, loss_pct=0, netto_g=5, allergens=[]),
        IngredientV2(name="неизвестный продукт в штуках", unit="pcs", brutto_g=3, loss_pct=0, netto_g=3, allergens=[])
    ]
    
    test_card_unknown = TechCardV2(
        meta={"title": "Test Unknown", "version": "2.0"},
        portions=1,
        yield_=YieldV2(perPortion_g=100, perBatch_g=100),
        ingredients=unknown_ingredients,
        process=[
            {"n": 1, "action": "Подготовка", "time_min": 5, "temp_c": None},
            {"n": 2, "action": "Приготовление", "time_min": 10, "temp_c": 180},
            {"n": 3, "action": "Подача", "time_min": 2, "temp_c": 65}
        ],
        storage={"conditions": "test", "shelfLife_hours": 24, "servingTemp_c": 65}
    )
    
    nutrition_unknown, meta_unknown, issues_unknown = calculator.calculate_tech_card_nutrition(test_card_unknown)
    
    print(f"✅ Unknown ingredients test completed")
    print(f"Coverage: {meta_unknown.coveragePct}%")
    print(f"Issues: {len(issues_unknown)}")
    
    for issue in issues_unknown:
        print(f"  - {issue['type']}: {issue['name']}")
    
    # Test 4: Formula verification
    print("\n4️⃣ TESTING FORMULA VERIFICATION")
    print("-" * 50)
    
    per100g = nutrition.per100g
    per_portion = nutrition.perPortion
    yield_per_portion_g = test_yield.perPortion_g
    
    multiplier = yield_per_portion_g / 100.0
    print(f"Formula: perPortion = per100g × (yield.perPortion_g/100)")
    print(f"Multiplier: {multiplier}")
    
    for field in ['kcal', 'proteins_g', 'fats_g', 'carbs_g']:
        expected = getattr(per100g, field) * multiplier
        actual = getattr(per_portion, field)
        
        if expected > 0:
            diff_pct = abs(actual - expected) / expected * 100
            tolerance_ok = diff_pct <= 3.0
            print(f"{field}: expected={expected:.1f}, actual={actual}, diff={diff_pct:.1f}% {'✅' if tolerance_ok else '❌'}")
        else:
            print(f"{field}: expected={expected:.1f}, actual={actual} ✅")
    
    # Test 5: Density conversions
    print("\n5️⃣ TESTING DENSITY CONVERSIONS")
    print("-" * 50)
    
    density_tests = [
        ("растительное масло", 100, "ml"),
        ("молоко", 200, "ml"),
        ("масло оливковое", 50, "ml")
    ]
    
    for name, amount, unit in density_tests:
        mass_grams, status = calculator._convert_to_grams(amount, unit, name)
        print(f"✅ {name}: {amount}{unit} → {mass_grams}g ({status})")
    
    # Test 6: Piece to grams conversion
    print("\n6️⃣ TESTING PIECE TO GRAMS CONVERSION")
    print("-" * 50)
    
    egg_mass, egg_status = calculator._convert_to_grams(3, "pcs", "яйцо куриное")
    print(f"✅ яйцо куриное: 3 pcs → {egg_mass}g ({egg_status})")
    
    unknown_pcs_mass, unknown_pcs_status = calculator._convert_to_grams(2, "pcs", "неизвестный продукт")
    print(f"❌ неизвестный продукт: 2 pcs → {unknown_pcs_mass}g ({unknown_pcs_status})")
    
    print("\n" + "=" * 60)
    print("🎉 DIRECT NUTRITION CALCULATOR TESTING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_direct_nutrition_calculator()