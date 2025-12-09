"""
Правила шефа (rule-based sanity checks) для TechCardV2
Автоматически выявляет "кухонный бред" после LLM генерации
"""
import re
from typing import List, Dict, Any
from receptor_agent.techcards_v2.schemas import TechCardV2
from .chef_rules_consts import (
    MAX_LOSS_PCT, YIELD_TOLERANCE, SALT_PCT_MAX,
    OIL_ML_PER_PORTION_MIN, OIL_ML_PER_PORTION_MAX,
    MIN_PROCESS_STEPS, ALLOWED_UNITS, THERMAL_KEYWORDS,
    OIL_INGREDIENTS, SALT_INGREDIENTS
)


def run_chef_rules(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """
    Запуск всех правил шефа для выявления кухонного бреда
    
    Args:
        tech_card: Валидированная техкарта TechCardV2
        
    Returns:
        List[Dict]: Список issues с типами ruleError/ruleWarning
    """
    issues = []
    
    # 1. yieldConsistency (error) - отклонение выхода >15%
    issues.extend(_check_yield_consistency(tech_card))
    
    # 2. lossBounds (error) - потери <0 или >60%
    issues.extend(_check_loss_bounds(tech_card))
    
    # 3. saltUpperBound (warning) - соль >2.2% от общей массы
    issues.extend(_check_salt_upper_bound(tech_card))
    
    # 4. fryOilPerPortion (warning) - масло <5 или >30 мл/порцию
    issues.extend(_check_fry_oil_per_portion(tech_card))
    
    # 5. thermalInfoMissing (warning) - нет времени И температуры у термошагов
    issues.extend(_check_thermal_info_missing(tech_card))
    
    # 6. stepsMin3 (error) - <3 шагов процесса
    issues.extend(_check_steps_min3(tech_card))
    
    # 7. unitsStrict (error) - неправильные единицы
    issues.extend(_check_units_strict(tech_card))
    
    # 8. numbersFormat (warning) - >1 знака после запятой
    issues.extend(_check_numbers_format(tech_card))
    
    # 9. rangePhrases (warning) - диапазоны/приближения
    issues.extend(_check_range_phrases(tech_card))
    
    return issues


def _check_yield_consistency(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка согласованности выхода"""
    issues = []
    
    total_netto = sum(ing.netto_g for ing in tech_card.ingredients)
    target_batch = tech_card.yield_.perBatch_g
    
    if target_batch > 0:
        deviation = abs(total_netto - target_batch) / target_batch
        if deviation > YIELD_TOLERANCE:
            issues.append({
                "type": "ruleError:yieldConsistency",
                "hint": f"Выход не сходится: нетто {total_netto:.1f}г, заявлено {target_batch:.1f}г (отклонение {deviation:.1%})",
                "meta": {
                    "total_netto_g": total_netto,
                    "target_batch_g": target_batch,
                    "deviation_pct": deviation
                }
            })
    
    return issues


def _check_loss_bounds(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка границ потерь"""
    issues = []
    
    for ingredient in tech_card.ingredients:
        if ingredient.loss_pct < 0 or ingredient.loss_pct > MAX_LOSS_PCT:
            issues.append({
                "type": "ruleError:lossBounds",
                "hint": f"Неадекватные потери у '{ingredient.name}': {ingredient.loss_pct}% (норма 0-{MAX_LOSS_PCT}%)",
                "meta": {
                    "ingredient_name": ingredient.name,
                    "loss_pct": ingredient.loss_pct,
                    "max_allowed": MAX_LOSS_PCT
                }
            })
    
    return issues


def _check_salt_upper_bound(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка избыточности соли"""
    issues = []
    
    total_netto = sum(ing.netto_g for ing in tech_card.ingredients)
    salt_mass = 0
    
    # Суммируем массу всех видов соли
    for ingredient in tech_card.ingredients:
        ingredient_name = ingredient.name.lower()
        if any(salt_name in ingredient_name for salt_name in SALT_INGREDIENTS):
            salt_mass += ingredient.netto_g
    
    if total_netto > 0:
        salt_pct = salt_mass / total_netto
        if salt_pct > SALT_PCT_MAX:
            issues.append({
                "type": "ruleWarning:saltUpperBound",
                "hint": f"Избыток соли: {salt_pct:.1%} от общей массы (рекомендуемо ≤{SALT_PCT_MAX:.1%})",
                "meta": {
                    "salt_mass_g": salt_mass,
                    "total_mass_g": total_netto,
                    "salt_pct": salt_pct,
                    "max_recommended": SALT_PCT_MAX
                }
            })
    
    return issues


def _check_fry_oil_per_portion(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка количества масла для жарки на порцию"""
    issues = []
    
    oil_mass = 0
    portions = tech_card.portions or 1
    
    # Суммируем массу всех видов масла
    for ingredient in tech_card.ingredients:
        ingredient_name = ingredient.name.lower()
        if any(oil_name in ingredient_name for oil_name in OIL_INGREDIENTS):
            # Конвертируем в мл (считаем что 1г масла ≈ 1мл)
            oil_volume = ingredient.netto_g
            oil_mass += oil_volume
    
    oil_per_portion = oil_mass / portions
    
    if oil_mass > 0:  # Есть масло в рецепте
        if oil_per_portion < OIL_ML_PER_PORTION_MIN:
            issues.append({
                "type": "ruleWarning:fryOilPerPortion",
                "hint": f"Мало масла для жарки: {oil_per_portion:.1f} мл/порц (рекомендуемо ≥{OIL_ML_PER_PORTION_MIN} мл/порц)",
                "meta": {
                    "oil_per_portion_ml": oil_per_portion,
                    "total_oil_ml": oil_mass,
                    "portions": portions,
                    "min_recommended": OIL_ML_PER_PORTION_MIN
                }
            })
        elif oil_per_portion > OIL_ML_PER_PORTION_MAX:
            issues.append({
                "type": "ruleWarning:fryOilPerPortion", 
                "hint": f"Много масла для жарки: {oil_per_portion:.1f} мл/порц (рекомендуемо ≤{OIL_ML_PER_PORTION_MAX} мл/порц)",
                "meta": {
                    "oil_per_portion_ml": oil_per_portion,
                    "total_oil_ml": oil_mass,
                    "portions": portions,
                    "max_recommended": OIL_ML_PER_PORTION_MAX
                }
            })
    
    return issues


def _check_thermal_info_missing(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка отсутствия времени/температуры у термических шагов"""
    issues = []
    
    missing_thermal = []
    
    for step in tech_card.process:
        action_lower = step.action.lower()
        is_thermal = any(keyword in action_lower for keyword in THERMAL_KEYWORDS)
        
        if is_thermal and not step.time_min and not step.temp_c:
            missing_thermal.append(f"Шаг {step.n or len(missing_thermal)+1}: {step.action}")
    
    if missing_thermal:
        issues.append({
            "type": "ruleWarning:thermalInfoMissing",
            "hint": f"Термошаги без времени/температуры: {'; '.join(missing_thermal)}",
            "meta": {
                "missing_steps": missing_thermal,
                "count": len(missing_thermal)
            }
        })
    
    return issues


def _check_steps_min3(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка минимального количества шагов"""
    issues = []
    
    steps_count = len(tech_card.process)
    if steps_count < MIN_PROCESS_STEPS:
        issues.append({
            "type": "ruleError:stepsMin3",
            "hint": f"Слишком мало шагов процесса: {steps_count} (минимум {MIN_PROCESS_STEPS})",
            "meta": {
                "actual_steps": steps_count,
                "min_required": MIN_PROCESS_STEPS
            }
        })
    
    return issues


def _check_units_strict(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка строгих единиц измерения"""
    issues = []
    
    wrong_units = []
    
    # Проверяем единицы у ингредиентов
    for ingredient in tech_card.ingredients:
        if ingredient.unit not in ALLOWED_UNITS:
            wrong_units.append(f"{ingredient.name}: {ingredient.unit}")
    
    if wrong_units:
        issues.append({
            "type": "ruleError:unitsStrict",
            "hint": f"Недопустимые единицы измерения: {'; '.join(wrong_units)} (разрешены: {', '.join(ALLOWED_UNITS)})",
            "meta": {
                "wrong_units": wrong_units,
                "allowed_units": ALLOWED_UNITS
            }
        })
    
    return issues


def _check_numbers_format(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка формата чисел (не более 1 знака после запятой)"""
    issues = []
    
    precision_issues = []
    
    # Проверяем ингредиенты
    for ingredient in tech_card.ingredients:
        for field_name, value in [
            ('brutto_g', ingredient.brutto_g),
            ('loss_pct', ingredient.loss_pct),
            ('netto_g', ingredient.netto_g)
        ]:
            if isinstance(value, float):
                decimal_part = str(value).split('.')
                if len(decimal_part) > 1 and len(decimal_part[1]) > 1:
                    precision_issues.append(f"{ingredient.name}.{field_name}: {value}")
    
    # Проверяем выход
    for field_name, value in [
        ('perPortion_g', tech_card.yield_.perPortion_g),
        ('perBatch_g', tech_card.yield_.perBatch_g)
    ]:
        if isinstance(value, float):
            decimal_part = str(value).split('.')
            if len(decimal_part) > 1 and len(decimal_part[1]) > 1:
                precision_issues.append(f"yield.{field_name}: {value}")
    
    # Проверяем процесс
    for step in tech_card.process:
        if step.time_min is not None and isinstance(step.time_min, float):
            decimal_part = str(step.time_min).split('.')
            if len(decimal_part) > 1 and len(decimal_part[1]) > 1:
                precision_issues.append(f"process[{step.n}].time_min: {step.time_min}")
        
        if step.temp_c is not None and isinstance(step.temp_c, float):
            decimal_part = str(step.temp_c).split('.')
            if len(decimal_part) > 1 and len(decimal_part[1]) > 1:
                precision_issues.append(f"process[{step.n}].temp_c: {step.temp_c}")
    
    if precision_issues:
        issues.append({
            "type": "ruleWarning:numbersFormat",
            "hint": f"Числа с >1 знака после запятой: {', '.join(precision_issues[:3])}" + 
                   (f" и ещё {len(precision_issues)-3}" if len(precision_issues) > 3 else ""),
            "meta": {
                "precision_issues": precision_issues,
                "count": len(precision_issues)
            }
        })
    
    return issues


def _check_range_phrases(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """Проверка диапазонов и приближений (на случай прорыва LLM)"""
    issues = []
    
    card_text = str(tech_card.model_dump()).lower()
    
    range_patterns = [
        r'\d+\s*[–-]\s*\d+',  # 10-15, 5–7
        r'~|≈|около|примерно'  # ~5, ≈10, около 15, примерно 20
    ]
    
    found_ranges = []
    for pattern in range_patterns:
        matches = re.findall(pattern, card_text)
        found_ranges.extend(matches)
    
    if found_ranges:
        issues.append({
            "type": "ruleWarning:rangePhrases",
            "hint": f"Найдены диапазоны/приближения: {', '.join(set(found_ranges))}",
            "meta": {
                "found_ranges": found_ranges,
                "count": len(found_ranges)
            }
        })
    
    return issues


def has_critical_rule_errors(issues: List[Dict[str, Any]]) -> bool:
    """
    Проверяет наличие критических ошибок правил (ruleError)
    При наличии таких ошибок карта должна получить статус 'draft'
    """
    return any(
        issue.get("type", "").startswith("ruleError:")
        for issue in issues
    )