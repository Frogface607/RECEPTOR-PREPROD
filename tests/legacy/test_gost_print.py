#!/usr/bin/env python3
"""
Simple test script for GOST print functionality
"""

import sys
import os
import json

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, MetaV2, YieldV2, ProcessStepV2, StorageV2, NutritionV2, NutritionPer, CostV2
from receptor_agent.exports.html import generate_print_html

def test_gost_print():
    """Test the GOST print HTML generation"""
    
    # Create a test tech card
    test_card = TechCardV2(
        meta=MetaV2(title="Борщ украинский", cuisine="украинская"),
        portions=4,
        yield_=YieldV2(perPortion_g=200.0, perBatch_g=800.0),
        ingredients=[
            IngredientV2(
                name="Говядина",
                unit="g",
                brutto_g=400.0,
                loss_pct=15.0,
                netto_g=340.0,
                skuId="BEEF001"
            ),
            IngredientV2(
                name="Свекла",
                unit="g",
                brutto_g=200.0,
                loss_pct=20.0,
                netto_g=160.0
            ),
            IngredientV2(
                name="Морковь",
                unit="g",
                brutto_g=100.0,
                loss_pct=15.0,
                netto_g=85.0
            ),
            IngredientV2(
                name="Яйца куриные",
                unit="pcs",
                brutto_g=2.0,
                loss_pct=5.0,
                netto_g=1.9
            )
        ],
        process=[
            ProcessStepV2(n=1, action="Подготовка мяса и овощей", time_min=20.0),
            ProcessStepV2(n=2, action="Варка бульона", time_min=90.0, temp_c=95.0, ccp=True),
            ProcessStepV2(n=3, action="Добавление овощей", time_min=30.0, temp_c=85.0),
            ProcessStepV2(n=4, action="Финальная готовка", time_min=10.0)
        ],
        storage=StorageV2(
            conditions="Холодильник 0...+4°C",
            shelfLife_hours=48.0,
            servingTemp_c=65.0
        ),
        nutrition=NutritionV2(
            per100g=NutritionPer(kcal=55.0, proteins_g=3.5, fats_g=2.1, carbs_g=6.2),
            perPortion=NutritionPer(kcal=110.0, proteins_g=7.0, fats_g=4.2, carbs_g=12.4)
        ),
        cost=CostV2(
            rawCost=180.50,
            costPerPortion=45.13,
            markup_pct=300.0,
            vat_pct=20.0
        ),
        printNotes=["Подавать с сметаной", "Украсить зеленью"]
    )
    
    print("=== Тест ГОСТ-печати ===")
    
    # Test success status
    html_success = generate_print_html(test_card, "success", [])
    print(f"✅ HTML для успешной карты сгенерирован: {len(html_success)} символов")
    
    # Test draft status with issues
    html_draft = generate_print_html(test_card, "draft", ["Недостаточно ингредиентов", "Отсутствует CCP для мяса"])
    print(f"✅ HTML для черновика сгенерирован: {len(html_draft)} символов")
    
    # Save to files for manual inspection
    with open('/app/test_gost_success.html', 'w', encoding='utf-8') as f:
        f.write(html_success)
    print("✅ Файл test_gost_success.html сохранен")
    
    with open('/app/test_gost_draft.html', 'w', encoding='utf-8') as f:
        f.write(html_draft)
    print("✅ Файл test_gost_draft.html сохранен")
    
    # Test key elements are present
    key_elements = [
        "ТЕХНОЛОГИЧЕСКАЯ КАРТА",
        "СОСТАВ И РАСХОД СЫРЬЯ",
        "ТЕХНОЛОГИЧЕСКИЙ ПРОЦЕСС", 
        "УСЛОВИЯ И СРОКИ ХРАНЕНИЯ",
        "ПИЩЕВАЯ ЦЕННОСТЬ",
        "ЭКОНОМИЧЕСКИЕ ПОКАЗАТЕЛИ"
    ]
    
    print("\n=== Проверка ключевых элементов ===")
    for element in key_elements:
        if element in html_success:
            print(f"✅ {element} - присутствует")
        else:
            print(f"❌ {element} - отсутствует")
    
    # Check watermark
    if "ЧЕРНОВИК" in html_draft:
        print("✅ Водяной знак ЧЕРНОВИК присутствует в draft")
    else:
        print("❌ Водяной знак ЧЕРНОВИК отсутствует")
    
    # Check ingredients table
    ingredient_checks = ["Говядина", "400.0", "15.0", "340.0", "g"]
    ingredients_ok = all(check in html_success for check in ingredient_checks)
    print(f"✅ Таблица ингредиентов: {'корректная' if ingredients_ok else 'некорректная'}")
    
    # Check process table  
    process_checks = ["Варка бульона", "90", "95", "✓"]
    process_ok = all(check in html_success for check in process_checks)
    print(f"✅ Таблица процессов: {'корректная' if process_ok else 'некорректная'}")
    
    # Check nutrition
    nutrition_checks = ["55.0", "3.5", "2.1", "6.2", "110.0", "7.0", "4.2", "12.4"]
    nutrition_ok = all(check in html_success for check in nutrition_checks)
    print(f"✅ Пищевая ценность: {'корректная' if nutrition_ok else 'некорректная'}")
    
    # Check cost
    cost_checks = ["180.50", "45.13", "300", "20"]
    cost_ok = all(check in html_success for check in cost_checks)
    print(f"✅ Стоимость: {'корректная' if cost_ok else 'некорректная'}")
    
    return True

if __name__ == "__main__":
    try:
        test_gost_print()
        print("\n✅ Тест ГОСТ-печати успешно завершен!")
        print("📄 Откройте test_gost_success.html и test_gost_draft.html для проверки")
    except Exception as e:
        print(f"\n❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)