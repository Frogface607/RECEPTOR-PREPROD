from __future__ import annotations
from typing import Tuple, List
from .schemas import TechCardV2
from .allergens import detect_allergens

class ValidationError(Exception):
    pass

def validate_yield_balance(card: TechCardV2) -> Tuple[bool, str]:
    total_net_ingredients = round(sum(i.netto_g for i in card.ingredients), 2)
    expected_total = float(card.yield_.perBatch_g)
    if abs(total_net_ingredients - expected_total) > 0.01 * max(1.0, expected_total):
        return (False, f"perBatch_g mismatch: ingredients={total_net_ingredients}, yield.perBatch_g={expected_total}")
    # per_portion check
    calc_total_from_portions = card.portions * card.yield_.perPortion_g
    if abs(calc_total_from_portions - expected_total) > 0.01 * max(1.0, expected_total):
        return (False, f"yield per_portion mismatch: portions*perPortion_g={calc_total_from_portions}, perBatch_g={expected_total}")
    return (True, "ok")

def validate_loss_bounds(card: TechCardV2) -> Tuple[bool, str]:
    for ing in card.ingredients:
        if ing.netto_g > ing.brutto_g + 1e-6:
            return (False, f"netto_g > brutto_g for '{ing.name}'")
        if not (0 <= ing.loss_pct <= 95):
            return (False, f"loss_pct out of bounds for '{ing.name}'")
    return (True, "ok")

def recompute_allergens(card: TechCardV2) -> List[str]:
    names = [i.name for i in card.ingredients]
    return sorted(detect_allergens(names))

def validate_card(card: TechCardV2) -> Tuple[bool, List[str]]:
    ok1, m1 = validate_yield_balance(card)
    ok2, m2 = validate_loss_bounds(card)
    issues = []
    if not ok1: issues.append(m1)
    if not ok2: issues.append(m2)
    # Note: allergens validation removed as it's per-ingredient in TechCardV2
    return (len(issues) == 0, issues)