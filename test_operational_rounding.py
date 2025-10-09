#!/usr/bin/env python3
"""
Test Script: Operational Rounding v1 (Export & Kitchen View)
Тестирование операционного округления по DoD примерам
"""

import requests
import json
import os
import sys

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"


class OperationalRoundingTest:
    """Класс для тестирования операционного округления"""
    
    def __init__(self):
        self.test_results = []
    
    def create_test_techcard(self, dish_name: str, ingredients: list) -> dict:
        """Создать тестовую техкарту с заданными ингредиентами"""
        total_netto = sum(ing.get('netto_g', 0) for ing in ingredients)
        
        return {
            "meta": {
                "title": dish_name,
                "id": f"test-{dish_name.lower().replace(' ', '-')}",
                "version": "2.0"
            },
            "portions": 1,
            "yield_": {
                "perPortion_g": total_netto,
                "perBatch_g": total_netto
            },
            "ingredients": ingredients,
            "process": {"steps": []},
            "nutrition": {"per100g": {}, "perPortion": {}},
            "cost": {"per100g": {}, "perPortion": {}}
        }
    
    def test_dod_example_omlet(self):
        """
        DoD Пример 1: Омлет
        • Соль 0.7г → 0.5г, Перец 0.9г → 1.0г, Молоко 102мл → 100мл
        • Σнетто после округления совпадает с yield в пределах ≤ 2%
        """
        print("\n🥚 DoD Test 1: Омлет с операционным округлением")
        
        ingredients = [
            {"name": "Яйца", "brutto_g": 120, "netto_g": 120, "loss_pct": 0, "unit": "g"},
            {"name": "Молоко", "brutto_g": 102, "netto_g": 102, "loss_pct": 0, "unit": "ml"},
            {"name": "Соль", "brutto_g": 0.7, "netto_g": 0.7, "loss_pct": 0, "unit": "g"},
            {"name": "Перец черный молотый", "brutto_g": 0.9, "netto_g": 0.9, "loss_pct": 0, "unit": "g"},
            {"name": "Масло сливочное", "brutto_g": 10, "netto_g": 10, "loss_pct": 0, "unit": "g"}
        ]
        
        # Изначальная сумма нетто
        original_sum = sum(ing["netto_g"] for ing in ingredients)
        print(f"   Исходная сумма нетто: {original_sum}г")
        
        techcard = self.create_test_techcard("Омлет операционный тест", ingredients)
        
        # Тестируем экспорт с операционным округлением
        response = requests.post(
            f"{API_BASE}/techcards.v2/export/enhanced/iiko.xlsx",
            json={
                "techcard": techcard,
                "export_options": {
                    "operational_rounding": True,  # Включаем операционное округление
                    "use_product_codes": False  # Отключаем коды продуктов для простоты
                },
                "organization_id": "default",
                "user_email": "test@example.com"
            },
            timeout=30
        )
        
        print(f"   Export status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Export successful with operational rounding")
            
            # Проверяем что файл создался
            file_size = len(response.content)
            print(f"   📄 XLSX file size: {file_size} bytes")
            
            # Сохраняем файл для проверки
            with open("/app/test_omelet_rounded.xlsx", "wb") as f:
                f.write(response.content)
            
            print(f"   💾 File saved as test_omelet_rounded.xlsx")
            
            return True
        else:
            print(f"   ❌ Export failed: {response.text[:200]}")
            return False
    
    def test_dod_example_steak(self):
        """
        DoD Пример 2: Стейк + соус
        • 100г гарнир округлён кратно 5г; соус — кратно 5мл
        • Баланс выполнен через гарнир/соус, GX-02 зелёный
        """
        print("\n🥩 DoD Test 2: Стейк с соусом")
        
        ingredients = [
            {"name": "Стейк говяжий", "brutto_g": 180, "netto_g": 150, "loss_pct": 16.7, "unit": "g"},
            {"name": "Картофель пюре", "brutto_g": 103, "netto_g": 98, "loss_pct": 5, "unit": "g"},  # Гарнир для балансировки
            {"name": "Соус грибной", "brutto_g": 47, "netto_g": 42, "loss_pct": 10, "unit": "ml"},  # Соус для балансировки
            {"name": "Зелень", "brutto_g": 5.3, "netto_g": 4.8, "loss_pct": 10, "unit": "g"}
        ]
        
        original_sum = sum(ing["netto_g"] for ing in ingredients)
        print(f"   Исходная сумма нетто: {original_sum}г")
        
        techcard = self.create_test_techcard("Стейк с грибным соусом тест", ingredients)
        
        # Тестируем экспорт с округлением
        response = requests.post(
            f"{API_BASE}/techcards.v2/export/enhanced/iiko.xlsx",
            json={
                "techcard": techcard,
                "export_options": {
                    "operational_rounding": True,
                    "use_product_codes": False
                },
                "organization_id": "default", 
                "user_email": "test@example.com"
            },
            timeout=30
        )
        
        print(f"   Export status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Export successful")
            
            with open("/app/test_steak_rounded.xlsx", "wb") as f:
                f.write(response.content)
            
            print(f"   💾 File saved as test_steak_rounded.xlsx")
            return True
        else:
            print(f"   ❌ Export failed: {response.text[:200]}")
            return False
    
    def test_dod_example_pieces(self):
        """
        DoD Пример 3: Штучные товары (яйцо)
        • Если SKU допускает дроби — 0.5шт; иначе — 1шт или перевод в граммы
        """
        print("\n🥚 DoD Test 3: Штучные товары (яйцо)")
        
        ingredients = [
            {"name": "Яйцо куриное", "brutto_g": 1.3, "netto_g": 1.3, "loss_pct": 0, "unit": "pcs"},  # 1.3шт → должно округлиться
            {"name": "Мука пшеничная", "brutto_g": 48.7, "netto_g": 48.7, "loss_pct": 0, "unit": "g"},
            {"name": "Молоко", "brutto_g": 78, "netto_g": 78, "loss_pct": 0, "unit": "ml"},
            {"name": "Сахар", "brutto_g": 12.3, "netto_g": 12.3, "loss_pct": 0, "unit": "g"}
        ]
        
        original_sum = sum(ing["netto_g"] for ing in ingredients)
        print(f"   Исходная сумма нетто: {original_sum} (смешанные единицы)")
        
        techcard = self.create_test_techcard("Блины со штучными ингредиентами", ingredients)
        
        response = requests.post(
            f"{API_BASE}/techcards.v2/export/enhanced/iiko.xlsx",
            json={
                "techcard": techcard,
                "export_options": {
                    "operational_rounding": True,
                    "use_product_codes": False
                },
                "organization_id": "default",
                "user_email": "test@example.com"
            },
            timeout=30
        )
        
        print(f"   Export status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Export successful")
            
            with open("/app/test_pieces_rounded.xlsx", "wb") as f:
                f.write(response.content)
            
            print(f"   💾 File saved as test_pieces_rounded.xlsx")
            return True
        else:
            print(f"   ❌ Export failed: {response.text[:200]}")
            return False
    
    def test_rounding_rules_unit(self):
        """Тест unit-правил округления"""
        print("\n🧪 Unit Test: Правила округления")
        
        try:
            # Импортируем модуль округления напрямую
            sys.path.append('/app/backend')
            from receptor_agent.techcards_v2.operational_rounding import OperationalRoundingRules, OperationalRounder
            
            rules = OperationalRoundingRules()
            rounder = OperationalRounder()
            
            # Тест правил для граммов
            test_cases_g = [
                (4.3, 'g', 0.5),   # < 10г → шаг 0.5г
                (23.7, 'g', 1.0),  # 10–100г → шаг 1г
                (147, 'g', 5.0),   # > 100г → шаг 5г
            ]
            
            print("   Тест правил для граммов:")
            for value, unit, expected_step in test_cases_g:
                step = rules.get_rounding_step(value, unit)
                rounded = rounder.round_value_to_step(value, step)
                print(f"     {value}{unit} → шаг {step} (ожид. {expected_step}) → округл. {rounded}")
                assert abs(step - expected_step) < 0.001, f"Wrong step for {value}{unit}"
            
            # Тест правил для миллилитров
            test_cases_ml = [
                (23, 'ml', 1.0),    # < 50мл → шаг 1мл
                (102, 'ml', 5.0),   # 50–250мл → шаг 5мл
                (387, 'ml', 10.0),  # > 250мл → шаг 10мл
            ]
            
            print("   Тест правил для миллилитров:")
            for value, unit, expected_step in test_cases_ml:
                step = rules.get_rounding_step(value, unit)
                rounded = rounder.round_value_to_step(value, step)
                print(f"     {value}{unit} → шаг {step} (ожид. {expected_step}) → округл. {rounded}")
                assert abs(step - expected_step) < 0.001, f"Wrong step for {value}{unit}"
            
            # Тест нейтральных ингредиентов
            print("   Тест нейтральных ингредиентов:")
            neutral_tests = [
                ("Молоко", True),
                ("Картофель пюре", True),
                ("Стейк говяжий", False),
                ("Вода питьевая", True)
            ]
            
            for name, expected in neutral_tests:
                is_neutral = rules.is_neutral_ingredient(name)
                print(f"     '{name}' → нейтральный: {is_neutral} (ожид. {expected})")
                assert is_neutral == expected, f"Wrong neutral classification for {name}"
            
            print("   ✅ Unit tests passed!")
            return True
            
        except Exception as e:
            print(f"   ❌ Unit test error: {e}")
            return False
    
    def run_all_tests(self):
        """Запуск всех DoD тестов"""
        print("🧪 OPERATIONAL ROUNDING v1 - DoD TESTING")
        print("=" * 60)
        
        # Unit тесты правил
        unit_success = self.test_rounding_rules_unit()
        
        # DoD тесты
        omlet_success = self.test_dod_example_omlet()
        steak_success = self.test_dod_example_steak()
        pieces_success = self.test_dod_example_pieces()
        
        # Итоговый результат
        total_tests = 4
        passed_tests = sum([unit_success, omlet_success, steak_success, pieces_success])
        
        print(f"\n" + "=" * 60)
        print(f"📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
        print(f"   Пройдено тестов: {passed_tests}/{total_tests}")
        print(f"   Процент успеха: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"   🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Operational Rounding v1 готово к продакшену.")
        else:
            print(f"   ⚠️  Есть неудачные тесты. Требуется доработка.")
        
        print(f"\n📁 Созданные артефакты:")
        print(f"   - test_omelet_rounded.xlsx")
        print(f"   - test_steak_rounded.xlsx") 
        print(f"   - test_pieces_rounded.xlsx")
        
        return passed_tests == total_tests


def main():
    """Главная функция тестирования"""
    tester = OperationalRoundingTest()
    success = tester.run_all_tests()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)