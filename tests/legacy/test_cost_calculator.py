#!/usr/bin/env python3
"""
Simple test script for cost calculator
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

from receptor_agent.techcards_v2.cost_calculator import CostCalculator
from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, MetaV2, YieldV2, ProcessStepV2, StorageV2

def test_cost_calculator():
    """Test the cost calculator with a simple tech card"""
    
    # Create a test tech card
    test_card = TechCardV2(
        meta=MetaV2(title="Тестовая техкарта"),
        portions=4,
        yield_=YieldV2(perPortion_g=150.0, perBatch_g=600.0),
        ingredients=[
            IngredientV2(
                name="куриное филе",
                unit="g",
                brutto_g=400.0,
                loss_pct=10.0,
                netto_g=360.0
            ),
            IngredientV2(
                name="соль поваренная",
                unit="g", 
                brutto_g=10.0,
                loss_pct=0.0,
                netto_g=10.0
            ),
            IngredientV2(
                name="растительное масло",
                unit="ml",
                brutto_g=30.0,
                loss_pct=0.0,
                netto_g=30.0
            ),
            IngredientV2(
                name="неизвестный ингредиент",  # для тестирования fallback
                unit="g",
                brutto_g=100.0,
                loss_pct=0.0,
                netto_g=100.0
            )
        ],
        process=[
            ProcessStepV2(n=1, action="Подготовка", time_min=10.0),
            ProcessStepV2(n=2, action="Жарка", time_min=15.0, temp_c=180.0),
            ProcessStepV2(n=3, action="Подача", time_min=5.0)
        ],
        storage=StorageV2(
            conditions="Холодильник 0...+4°C",
            shelfLife_hours=48.0
        )
    )
    
    # Test calculator
    calculator = CostCalculator()
    
    print("=== Тест калькулятора себестоимости ===")
    print()
    
    # Test individual ingredients
    for ingredient in test_card.ingredients:
        # Проверим флаг для отладки
        use_llm_for_prices = os.getenv("PRICE_VIA_LLM", "false").lower() in ("true", "1", "yes", "on") 
        cost, status = calculator.calculate_ingredient_cost(ingredient, use_llm_fallback=use_llm_for_prices)
        print(f"Ингредиент: {ingredient.name}")
        print(f"  Количество: {ingredient.brutto_g}{ingredient.unit}")
        print(f"  Стоимость: {cost:.2f} RUB")
        print(f"  Статус: {status}")
        print(f"  use_llm_fallback: {use_llm_for_prices}")
        print()
    
    # Test full tech card cost
    cost_obj, cost_meta, issues = calculator.calculate_tech_card_cost(test_card)
    print("=== Общая стоимость техкарты ===")
    print(f"PRICE_VIA_LLM={os.getenv('PRICE_VIA_LLM', 'not_set')}")
    print(f"Общая стоимость сырья: {cost_obj.rawCost} RUB")
    print(f"Стоимость на порцию: {cost_obj.costPerPortion} RUB")
    print(f"Наценка: {cost_obj.markup_pct}%")
    print(f"НДС: {cost_obj.vat_pct}%")
    
    print("\n=== Метаданные стоимости ===")
    print(f"Источник: {cost_meta.source}")
    print(f"Покрытие: {cost_meta.coveragePct}%")
    print(f"Дата каталога: {cost_meta.asOf}")
    
    if issues:
        print(f"\n=== Issues ({len(issues)}) ===")
        for issue in issues:
            print(f"  {issue}")
    
    # Test catalog loading
    print()
    print("=== Информация о каталоге ===")
    print(f"Версия каталога: {calculator.catalog.get('catalog_version', 'неизвестно')}")
    print(f"Валюта: {calculator.catalog.get('currency', 'неизвестно')}")
    print(f"Категорий ингредиентов: {len(calculator.catalog.get('ingredients', {}))}")
    print(f"Индекс ингредиентов: {len(calculator.ingredient_index)} элементов")
    
    return True

if __name__ == "__main__":
    try:
        test_cost_calculator()
        print("\n✅ Тест успешно завершен!")
    except Exception as e:
        print(f"\n❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)