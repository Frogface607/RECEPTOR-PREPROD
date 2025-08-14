"""
Post-checking for TechCardV2 generation quality
Проверяет готовую техкарту на соответствие требованиям качества генерации
"""
import re
from typing import List, Dict, Any
from receptor_agent.techcards_v2.schemas import TechCardV2


# Запрещённые слова (маркетинговые эпитеты)
FORBIDDEN_WORDS = [
    'вкуснейш', 'невероятн', 'вау', 'идеальн', 'потрясающ', 'изумительн',
    'восхитительн', 'великолепн', 'шикарн', 'фантастическ', 'волшебн',
    'божественн', 'чудесн', 'превосходн', 'замечательн', 'отличн',
    'прекрасн', 'удивительн', 'сказочн', 'роскошн'
]

# Паттерны для поиска диапазонов
RANGE_PATTERNS = [
    r'\d+\s*[–-]\s*\d+',  # 10-15, 5–7
    r'~|≈|около|примерно'  # ~5, ≈10, около 15, примерно 20
]

# Допустимые единицы измерения
ALLOWED_UNITS = ['g', 'ml', 'pcs']

def postcheck_v2(tech_card: TechCardV2) -> List[Dict[str, Any]]:
    """
    Пост-проверка технологической карты V2
    
    Args:
        tech_card: Валидированная техкарта TechCardV2
        
    Returns:
        List[Dict]: Список issues с типом postcheck:<код> и описанием
    """
    issues = []
    card_dict = tech_card.model_dump()
    
    # 1. forbiddenWords - проверка на маркетинговые эпитеты
    card_text = str(card_dict).lower()
    found_words = []
    for word in FORBIDDEN_WORDS:
        if word in card_text:
            found_words.append(word)
    
    if found_words:
        issues.append({
            "type": "postcheck:forbiddenWords", 
            "hint": f"Найдены маркетинговые эпитеты: {', '.join(found_words)}"
        })
    
    # 2. ranges - проверка на диапазоны и примерные значения
    found_ranges = []
    for pattern in RANGE_PATTERNS:
        matches = re.findall(pattern, card_text)
        found_ranges.extend(matches)
    
    if found_ranges:
        issues.append({
            "type": "postcheck:ranges",
            "hint": f"Найдены диапазоны/приближения: {', '.join(found_ranges)}"
        })
    
    # 3. units - проверка единиц измерения
    wrong_units = []
    for ingredient in tech_card.ingredients:
        if ingredient.unit not in ALLOWED_UNITS:
            wrong_units.append(f"{ingredient.name}: {ingredient.unit}")
    
    if wrong_units:
        issues.append({
            "type": "postcheck:units",
            "hint": f"Недопустимые единицы: {', '.join(wrong_units)}"
        })
    
    # 4. processMin3 - минимум 3 шага процесса
    if len(tech_card.process) < 3:
        issues.append({
            "type": "postcheck:processMin3",
            "hint": f"Недостаточно шагов процесса: {len(tech_card.process)} (нужно ≥3)"
        })
    
    # 5. thermalInfo - проверка времени/температуры для термообработки
    thermal_keywords = ['жар', 'вар', 'туш', 'запек', 'обжар', 'кип', 'гриль', 'фри']
    missing_thermal = []
    
    for i, step in enumerate(tech_card.process):
        action_lower = step.action.lower()
        is_thermal = any(keyword in action_lower for keyword in thermal_keywords)
        
        if is_thermal and not step.time_min and not step.temp_c:
            missing_thermal.append(f"Шаг {step.n or i+1}: {step.action}")
    
    if missing_thermal:
        issues.append({
            "type": "postcheck:thermalInfo",
            "hint": f"Термошаги без времени/температуры: {'; '.join(missing_thermal)}"
        })
    
    # 6. yieldConsistency - согласованность выхода
    total_netto = sum(ing.netto_g for ing in tech_card.ingredients)
    target_batch = tech_card.yield_.perBatch_g
    
    if target_batch > 0:
        deviation = abs(total_netto - target_batch) / target_batch
        if deviation > 0.10:  # >10% отклонение
            issues.append({
                "type": "postcheck:yieldConsistency",
                "hint": f"Нетто {total_netto:.1f}г не соответствует выходу {target_batch:.1f}г (отклонение {deviation:.1%})"
            })
    
    # 7. lossBounds - проверка границ потерь
    wrong_losses = []
    for ingredient in tech_card.ingredients:
        if ingredient.loss_pct < 0 or ingredient.loss_pct > 40:
            wrong_losses.append(f"{ingredient.name}: {ingredient.loss_pct}%")
    
    if wrong_losses:
        issues.append({
            "type": "postcheck:lossBounds",
            "hint": f"Потери вне диапазона 0-40%: {', '.join(wrong_losses)}"
        })
    
    # 8. numbersFormat - не более 1 знака после запятой
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
            "type": "postcheck:numbersFormat",
            "hint": f"Числа с >1 знака после запятой: {', '.join(precision_issues[:5])}" + 
                   (f" и ещё {len(precision_issues)-5}" if len(precision_issues) > 5 else "")
        })
    
    return issues