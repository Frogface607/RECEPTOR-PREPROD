"""
Юнит-тесты для правил шефа (chef_rules.py)
"""
import pytest
from receptor_agent.techcards_v2.schemas import TechCardV2, IngredientV2, ProcessStepV2, YieldV2, MetaV2, StorageV2
from receptor_agent.techcards_v2.chef_rules import (
    _check_yield_consistency, _check_loss_bounds, _check_salt_upper_bound,
    _check_fry_oil_per_portion, _check_steps_min3, _check_units_strict,
    has_critical_rule_errors
)


def create_test_techcard() -> TechCardV2:
    """Создает базовую тестовую техкарту"""
    return TechCardV2(
        meta=MetaV2(
            id="test-card",
            title="Тест блюдо", 
            version="2.0",
            createdAt="2025-01-18T12:00:00",
            cuisine="тестовая",
            tags=[]
        ),
        portions=4,
        yield_=YieldV2(perPortion_g=200.0, perBatch_g=800.0),
        ingredients=[
            IngredientV2(name="говядина", unit="g", brutto_g=600.0, loss_pct=10.0, netto_g=540.0),
            IngredientV2(name="соль поваренная", unit="g", brutto_g=8.0, loss_pct=0.0, netto_g=8.0),
            IngredientV2(name="растительное масло", unit="ml", brutto_g=20.0, loss_pct=0.0, netto_g=20.0)
        ],
        process=[
            ProcessStepV2(n=1, action="Подготовка", time_min=10.0),
            ProcessStepV2(n=2, action="Обжаривание", time_min=15.0, temp_c=180.0),
            ProcessStepV2(n=3, action="Доведение до готовности", time_min=10.0)
        ],
        storage=StorageV2(
            conditions="Холодильник 0...+4°C",
            shelfLife_hours=48.0,
            servingTemp_c=65.0
        ),
        allergens=[],
        notes=[]
    )


class TestYieldConsistency:
    """Тесты правила yieldConsistency"""
    
    def test_yield_consistency_ok(self):
        """Тест: выход сходится (в пределах 15%)"""
        card = create_test_techcard()
        # Нетто: 540 + 8 + 20 = 568г, заявлено 800г
        # Отклонение: |568-800|/800 = 29% > 15% → ошибка
        issues = _check_yield_consistency(card)
        assert len(issues) == 1
        assert issues[0]["type"] == "ruleError:yieldConsistency"
    
    def test_yield_consistency_good(self):
        """Тест: выход сходится идеально"""
        card = create_test_techcard()
        card.yield_.perBatch_g = 568.0  # Точно равно сумме нетто
        issues = _check_yield_consistency(card)
        assert len(issues) == 0


class TestLossBounds:
    """Тесты правила lossBounds"""
    
    def test_loss_bounds_negative(self):
        """Тест: отрицательные потери"""
        card = create_test_techcard()
        card.ingredients[0].loss_pct = -5.0
        issues = _check_loss_bounds(card)
        assert len(issues) == 1
        assert issues[0]["type"] == "ruleError:lossBounds"
        assert "говядина" in issues[0]["hint"]
    
    def test_loss_bounds_excessive(self):
        """Тест: чрезмерные потери"""
        card = create_test_techcard()
        card.ingredients[0].loss_pct = 70.0
        issues = _check_loss_bounds(card)
        assert len(issues) == 1
        assert issues[0]["type"] == "ruleError:lossBounds"
    
    def test_loss_bounds_ok(self):
        """Тест: нормальные потери"""
        card = create_test_techcard()
        card.ingredients[0].loss_pct = 15.0  # В норме
        issues = _check_loss_bounds(card)
        assert len(issues) == 0


class TestSaltUpperBound:
    """Тесты правила saltUpperBound"""
    
    def test_salt_excessive(self):
        """Тест: избыток соли"""
        card = create_test_techcard()
        # Соль: 8г из 568г общей массы = 1.4% (норма)
        # Увеличим соль до 20г = 3.5% > 2.2%
        card.ingredients[1].brutto_g = 20.0
        card.ingredients[1].netto_g = 20.0
        issues = _check_salt_upper_bound(card)
        assert len(issues) == 1
        assert issues[0]["type"] == "ruleWarning:saltUpperBound"
    
    def test_salt_normal(self):
        """Тест: нормальное количество соли"""
        card = create_test_techcard()
        issues = _check_salt_upper_bound(card)
        assert len(issues) == 0


class TestFryOilPerPortion:
    """Тесты правила fryOilPerPortion"""
    
    def test_oil_too_little(self):
        """Тест: мало масла для жарки"""
        card = create_test_techcard()
        # 20мл на 4 порции = 5 мл/порц (граница)
        card.ingredients[2].netto_g = 16.0  # 4 мл/порц < 5
        issues = _check_fry_oil_per_portion(card)
        assert len(issues) == 1
        assert issues[0]["type"] == "ruleWarning:fryOilPerPortion"
        assert "Мало масла" in issues[0]["hint"]
    
    def test_oil_too_much(self):
        """Тест: много масла для жарки"""
        card = create_test_techcard()
        # 140мл на 4 порции = 35 мл/порц > 30
        card.ingredients[2].netto_g = 140.0
        issues = _check_fry_oil_per_portion(card)
        assert len(issues) == 1
        assert issues[0]["type"] == "ruleWarning:fryOilPerPortion"
        assert "Много масла" in issues[0]["hint"]
    
    def test_oil_normal(self):
        """Тест: нормальное количество масла"""
        card = create_test_techcard()
        issues = _check_fry_oil_per_portion(card)
        assert len(issues) == 0


class TestStepsMin3:
    """Тесты правила stepsMin3"""
    
    def test_steps_insufficient(self):
        """Тест: недостаточно шагов"""
        card = create_test_techcard()
        card.process = card.process[:2]  # Оставляем только 2 шага
        issues = _check_steps_min3(card)
        assert len(issues) == 1
        assert issues[0]["type"] == "ruleError:stepsMin3"
    
    def test_steps_sufficient(self):
        """Тест: достаточно шагов"""
        card = create_test_techcard()
        issues = _check_steps_min3(card)
        assert len(issues) == 0


class TestUnitsStrict:
    """Тесты правила unitsStrict"""
    
    def test_wrong_units(self):
        """Тест: неправильные единицы"""
        card = create_test_techcard()
        card.ingredients[0].unit = "кг"  # Неправильная единица
        issues = _check_units_strict(card)
        assert len(issues) == 1
        assert issues[0]["type"] == "ruleError:unitsStrict"
        assert "кг" in issues[0]["hint"]
    
    def test_correct_units(self):
        """Тест: правильные единицы"""
        card = create_test_techcard()
        issues = _check_units_strict(card)
        assert len(issues) == 0


class TestCriticalRuleErrors:
    """Тесты функции has_critical_rule_errors"""
    
    def test_has_critical_errors(self):
        """Тест: есть критические ошибки"""
        issues = [
            {"type": "ruleWarning:saltUpperBound", "hint": "Warning"},
            {"type": "ruleError:lossBounds", "hint": "Critical error"},
            {"type": "ruleWarning:fryOilPerPortion", "hint": "Another warning"}
        ]
        assert has_critical_rule_errors(issues) == True
    
    def test_no_critical_errors(self):
        """Тест: нет критических ошибок"""
        issues = [
            {"type": "ruleWarning:saltUpperBound", "hint": "Warning"},
            {"type": "ruleWarning:fryOilPerPortion", "hint": "Another warning"}
        ]
        assert has_critical_rule_errors(issues) == False
    
    def test_empty_issues(self):
        """Тест: пустой список issues"""
        issues = []
        assert has_critical_rule_errors(issues) == False