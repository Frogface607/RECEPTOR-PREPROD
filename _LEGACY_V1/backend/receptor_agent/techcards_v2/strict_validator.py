"""
Строгий валидатор TechCardV2 с детальными issues
"""
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError
from .schemas import TechCardV2
import re

def validate_techcard_v2(data: Dict[str, Any]) -> Tuple[bool, List[str], TechCardV2 | None]:
    """
    Строгая валидация TechCardV2 с детальными issues.
    
    Returns:
        (is_valid, issues, validated_card_or_none)
    """
    issues = []
    
    try:
        # Попытка создать объект
        card = TechCardV2.model_validate(data)
        
        # Дополнительные проверки бизнес-правил
        issues.extend(_validate_business_rules(card))
        
        # Проверка на числа vs диапазоны/текст
        issues.extend(_validate_no_ranges_or_text(data))
        
        is_valid = len(issues) == 0
        return is_valid, issues, card if is_valid else None
        
    except ValidationError as e:
        # Конвертируем pydantic ошибки в понятные issues
        for error in e.errors():
            field_path = " → ".join(str(p) for p in error['loc'])
            message = error['msg']
            issues.append(f"Field '{field_path}': {message}")
        
        return False, issues, None
    except Exception as e:
        issues.append(f"Unexpected validation error: {str(e)}")
        return False, issues, None

def _validate_business_rules(card: TechCardV2) -> List[str]:
    """Проверка бизнес-правил"""
    issues = []
    
    # Проверка соответствия netto_g формуле
    for i, ing in enumerate(card.ingredients):
        expected_netto = ing.brutto_g * (1 - ing.loss_pct / 100)
        if abs(ing.netto_g - expected_netto) > 1.0:
            issues.append(f"Ingredient {i+1} '{ing.name}': netto_g ({ing.netto_g}g) doesn't match brutto_g * (1 - loss_pct/100) = {expected_netto:.1f}g")
    
    # Проверка баланса: сумма netto ≈ perBatch_g
    total_netto = sum(ing.netto_g for ing in card.ingredients)
    expected_batch = card.yield_.perPortion_g * card.portions
    if abs(total_netto - expected_batch) > expected_batch * 0.05:
        issues.append(f"Ingredient balance: sum of netto_g ({total_netto:.1f}g) doesn't match yield.perBatch_g ({expected_batch:.1f}g) within 5%")
    
    # Проверка термообработки: должны быть time_min ИЛИ temp_c
    thermal_keywords = ['жарить', 'варить', 'готовить', 'тушить', 'запекать', 'кипятить', 'обжарить', 'пассеровать']
    for step in card.process:
        if any(keyword in step.action.lower() for keyword in thermal_keywords):
            if step.time_min is None and step.temp_c is None:
                issues.append(f"Process step {step.n} '{step.action}': thermal step must have time_min or temp_c")
    
    # Проверка единиц измерения
    for i, ing in enumerate(card.ingredients):
        if ing.unit not in ['g', 'ml', 'pcs']:
            issues.append(f"Ingredient {i+1} '{ing.name}': invalid unit '{ing.unit}', allowed: g, ml, pcs")
    
    return issues

def _validate_no_ranges_or_text(data: Dict[str, Any]) -> List[str]:
    """Проверка отсутствия диапазонов и текстовых значений в числовых полях"""
    issues = []
    
    def check_numeric_fields(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Проверяем числовые поля на диапазоны
                if key in ['brutto_g', 'netto_g', 'loss_pct', 'time_min', 'temp_c', 'perPortion_g', 'perBatch_g', 'shelfLife_hours', 'portions']:
                    if isinstance(value, str):
                        # Ищем диапазоны типа "5-7", "5–7", "5 - 7"
                        if re.search(r'\d+\s*[-–—]\s*\d+', value):
                            issues.append(f"Field '{current_path}': contains range '{value}', only exact numbers allowed")
                        # Ищем текстовые значения типа "по вкусу"
                        elif not value.replace('.', '').replace(',', '').replace('-', '').isdigit():
                            issues.append(f"Field '{current_path}': contains text '{value}', only numbers allowed")
                
                check_numeric_fields(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_numeric_fields(item, f"{path}[{i}]")
    
    check_numeric_fields(data)
    return issues

def create_draft_response(issues: List[str], raw_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Создает ответ для техкарты с ошибками валидации"""
    return {
        "status": "draft",
        "validation_status": "failed",
        "issues": issues,
        "raw_data": raw_data,
        "message": "Validation failed: tech card saved as draft with issues"
    }