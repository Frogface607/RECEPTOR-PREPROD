#!/usr/bin/env python3
"""
Simple test script for nutrition calculator
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

from receptor_agent.techcards_v2.nutrition_calculator import NutritionCalculator
from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, MetaV2, YieldV2, ProcessStepV2, StorageV2

def test_nutrition_calculator():
    """Test the nutrition calculator with a simple tech card"""
    
    # Create a test tech card with known ingredients
    test_card = TechCardV2(
        meta=MetaV2(title="Тестовая техкарта БЖУ"),
        portions=4,
        yield_=YieldV2(perPortion_g=150.0, perBatch_g=600.0),
        ingredients=[
            IngredientV2(
                name="куриное филе",
                unit="g",
                brutto_g=400.0,
                loss_pct=5.0,
                netto_g=380.0
            ),
            IngredientV2(
                name="растительное масло",
                unit="ml",
                brutto_g=30.0,
                loss_pct=0.0,
                netto_g=30.0
            ),
            IngredientV2(
                name="соль поваренная",
                unit="g", 
                brutto_g=10.0,
                loss_pct=0.0,
                netto_g=10.0
            ),
            IngredientV2(
                name="яйцо куриное",
                unit="pcs",
                brutto_g=2.0,  # 2 штуки
                loss_pct=5.0,
                netto_g=1.9
            ),
            IngredientV2(
                name="неизвестный продукт",
                unit="g",
                brutto_g=100.0,
                loss_pct=0.0,
                netto_g=100.0
            )
        ],
        process=[
            ProcessStepV2(n=1, action="Подготовка", time_min=10.0),
            ProcessStepV2(n=2, action="Готовка", time_min=15.0, temp_c=180.0),
            ProcessStepV2(n=3, action="Подача", time_min=5.0)
        ],
        storage=StorageV2(
            conditions="Холодильник 0...+4°C",
            shelfLife_hours=48.0
        )
    )
    
    # Test calculator
    calculator = NutritionCalculator()
    
    print("=== Тест калькулятора БЖУ ===")
    print()
    
    # Test individual ingredients
    for ingredient in test_card.ingredients:
        nutrition, status = calculator.calculate_ingredient_nutrition(ingredient)
        print(f"Ингредиент: {ingredient.name}")
        print(f"  Количество: {ingredient.netto_g}{ingredient.unit}")
        if nutrition:
            print(f"  Калории: {nutrition['kcal']:.1f} ккал")
            print(f"  Белки: {nutrition['proteins_g']:.1f} г")
            print(f"  Жиры: {nutrition['fats_g']:.1f} г")
            print(f"  Углеводы: {nutrition['carbs_g']:.1f} г")
        else:
            print(f"  Питательность: не найдена")
        print(f"  Статус: {status}")
        print()
    
    # Test full tech card nutrition
    nutrition, nutrition_meta, issues = calculator.calculate_tech_card_nutrition(test_card)
    print("=== Общая питательность техкарты ===")
    
    print("НА 100г готового блюда:")
    if nutrition.per100g:
        print(f"  Калории: {nutrition.per100g.kcal} ккал")
        print(f"  Белки: {nutrition.per100g.proteins_g} г")
        print(f"  Жиры: {nutrition.per100g.fats_g} г")
        print(f"  Углеводы: {nutrition.per100g.carbs_g} г")
    else:
        print("  Данные отсутствуют")
    
    print()
    print("НА 1 ПОРЦИЮ:")
    if nutrition.perPortion:
        print(f"  Калории: {nutrition.perPortion.kcal} ккал")
        print(f"  Белки: {nutrition.perPortion.proteins_g} г")
        print(f"  Жиры: {nutrition.perPortion.fats_g} г")
        print(f"  Углеводы: {nutrition.perPortion.carbs_g} г")
    else:
        print("  Данные отсутствуют")
    
    print()
    print("=== Метаданные питания ===")
    print(f"Источник: {nutrition_meta.source}")
    print(f"Покрытие: {nutrition_meta.coveragePct}%")
    
    if issues:
        print(f"\n=== Issues ({len(issues)}) ===")
        for issue in issues:
            print(f"  {issue}")
    
    # Verify formula: perPortion ≈ per100g × (yield.perPortion_g/100)
    if nutrition.per100g and nutrition.perPortion:
        print("\n=== Проверка формулы ===")
        expected_per_portion = {
            'kcal': nutrition.per100g.kcal * (test_card.yield_.perPortion_g / 100),
            'proteins_g': nutrition.per100g.proteins_g * (test_card.yield_.perPortion_g / 100),
            'fats_g': nutrition.per100g.fats_g * (test_card.yield_.perPortion_g / 100),
            'carbs_g': nutrition.per100g.carbs_g * (test_card.yield_.perPortion_g / 100)
        }
        
        print(f"perPortion ≈ per100g × ({test_card.yield_.perPortion_g}г/100)")
        
        for key in ['kcal', 'proteins_g', 'fats_g', 'carbs_g']:
            actual = getattr(nutrition.perPortion, key)
            expected = expected_per_portion[key]
            diff_pct = abs(actual - expected) / expected * 100 if expected > 0 else 0
            status = "✓" if diff_pct <= 3 else "✗"
            print(f"  {key}: {actual} ≈ {expected:.1f} ({diff_pct:.1f}% diff) {status}")
    
    print()
    print("=== Информация о каталоге ===")
    print(f"Версия каталога: {calculator.catalog.get('catalog_version', 'неизвестно')}")
    print(f"Источник: {calculator.catalog.get('source', 'неизвестно')}")
    print(f"Продуктов в каталоге: {len(calculator.catalog.get('items', []))}")
    print(f"Индекс питания: {len(calculator.nutrition_index)} элементов")
    print(f"Плотности: {len(calculator.densities)} жидкостей")
    
    return True

if __name__ == "__main__":
    try:
        test_nutrition_calculator()
        print("\n✅ Тест успешно завершен!")
    except Exception as e:
        print(f"\n❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)