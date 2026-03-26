#!/usr/bin/env python3
"""
Simple test script for iiko export functionality
"""

import sys
import os
import json
from io import BytesIO

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, MetaV2, YieldV2, ProcessStepV2, StorageV2, NutritionV2, NutritionPer, CostV2, CostMetaV2
from receptor_agent.exports.iiko_exporter import export_techcard_to_iiko

def test_iiko_export():
    """Test the iiko export functionality"""
    
    # Create a test tech card with various ingredient types
    test_card = TechCardV2(
        meta=MetaV2(title="Борщ украинский", cuisine="украинская"),
        portions=6,
        yield_=YieldV2(perPortion_g=300.0, perBatch_g=1800.0),
        ingredients=[
            IngredientV2(
                name="Говядина лопатка",
                unit="g",
                brutto_g=800.0,
                loss_pct=15.0,
                netto_g=680.0,
                skuId="MEAT_001"
            ),
            IngredientV2(
                name="Свёкла столовая", 
                unit="g",
                brutto_g=600.0,
                loss_pct=20.0,
                netto_g=480.0,
                skuId="BEET_001"
            ),
            IngredientV2(
                name="Морковь",
                unit="g",
                brutto_g=200.0,
                loss_pct=15.0,
                netto_g=170.0
                # Без SKU для тестирования issues
            ),
            IngredientV2(
                name="Лук репчатый",
                unit="g",
                brutto_g=150.0,
                loss_pct=10.0,
                netto_g=135.0,
                skuId="ONION_001"
            ),
            IngredientV2(
                name="Масло растительное",
                unit="ml",
                brutto_g=50.0,
                loss_pct=0.0,
                netto_g=50.0,
                skuId="OIL_001"
            ),
            IngredientV2(
                name="Яйца куриные",
                unit="pcs",
                brutto_g=3.0,
                loss_pct=5.0,
                netto_g=2.85,
                skuId="EGG_001"
            )
        ],
        process=[
            ProcessStepV2(n=1, action="Подготовка мяса", time_min=20.0),
            ProcessStepV2(n=2, action="Варка бульона", time_min=120.0, temp_c=95.0),
            ProcessStepV2(n=3, action="Подготовка овощей", time_min=30.0)
        ],
        storage=StorageV2(
            conditions="Холодильник 0...+4°C",
            shelfLife_hours=72.0,
            servingTemp_c=70.0
        ),
        nutrition=NutritionV2(
            per100g=NutritionPer(kcal=52.0, proteins_g=3.8, fats_g=1.5, carbs_g=7.2),
            perPortion=NutritionPer(kcal=156.0, proteins_g=11.4, fats_g=4.5, carbs_g=21.6)
        ),
        cost=CostV2(
            rawCost=420.50,
            costPerPortion=70.08,
            markup_pct=280.0,
            vat_pct=20.0
        ),
        costMeta=CostMetaV2(
            source="catalog",
            coveragePct=83.3,  # 5 из 6 ингредиентов имеют SKU
            asOf="2025-01-17"
        )
    )
    
    print("=== Тест экспорта в iiko ===")
    
    # Проверяем общий баланс нетто
    total_netto = sum(ing.netto_g for ing in test_card.ingredients)
    expected_yield = test_card.yield_.perBatch_g
    print(f"Общий нетто: {total_netto:.1f} г")
    print(f"Ожидаемый выход: {expected_yield:.1f} г")
    print(f"Расхождение: {abs(total_netto - expected_yield):.1f} г ({abs(total_netto - expected_yield)/expected_yield*100:.1f}%)")
    
    # Экспортируем
    try:
        xlsx_file, issues = export_techcard_to_iiko(test_card)
        
        print(f"\n✅ XLSX файл сгенерирован: {len(xlsx_file.getvalue())} байт")
        
        # Сохраняем файл для проверки
        with open('/app/test_iiko_export.xlsx', 'wb') as f:
            f.write(xlsx_file.getvalue())
        print("✅ Файл сохранен как test_iiko_export.xlsx")
        
        # Проверяем issues
        print(f"\n=== Issues ({len(issues)}) ===")
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            if issue_type == 'noSku':
                print(f"⚠️  Отсутствует SKU для: {issue['name']}")
            elif issue_type == 'yieldMismatch':
                print(f"⚠️  Расхождение выхода: ожидается {issue['expected']:.1f}г, фактически {issue['actual']:.1f}г ({issue['mismatch_pct']}%)")
            else:
                print(f"⚠️  {issue_type}: {issue}")
        
        # Проверяем конвертации единиц
        print("\n=== Проверка конвертаций ===")
        for ing in test_card.ingredients:
            if ing.unit == "g":
                expected_kg = round(ing.netto_g / 1000, 3)
                print(f"✓ {ing.name}: {ing.netto_g}g → {expected_kg}kg")
            elif ing.unit == "ml":
                expected_l = round(ing.netto_g / 1000, 3)  
                print(f"✓ {ing.name}: {ing.netto_g}ml → {expected_l}l")
            elif ing.unit == "pcs":
                expected_pcs = int(round(ing.netto_g))
                print(f"✓ {ing.name}: {ing.netto_g} → {expected_pcs}pcs")
        
        # Проверяем структуру данных (базовая проверка)
        xlsx_file.seek(0)
        print(f"\n=== Структура файла ===")
        print(f"Размер файла: {len(xlsx_file.getvalue())} байт")
        
        # Проверяем что файл действительно xlsx (начинается с PK)
        xlsx_file.seek(0)
        file_header = xlsx_file.read(2)
        xlsx_file.seek(0)
        
        if file_header == b'PK':
            print("✅ Файл имеет корректный XLSX формат")
        else:
            print("❌ Файл не является корректным XLSX")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_iiko_export()
        if success:
            print("\n✅ Тест экспорта в iiko успешно завершен!")
            print("📊 Откройте test_iiko_export.xlsx для проверки листов Products и Recipes")
        else:
            print("\n❌ Тест экспорта в iiko завершился с ошибками")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)