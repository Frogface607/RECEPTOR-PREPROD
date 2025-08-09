from __future__ import annotations
from typing import Dict, Any, List

# Базовые усушки по типам (проценты, по умолчанию)
LOSS_DEFAULTS = {
    "poultry": 0.15,  # птица
    "meat": 0.18,
    "fish": 0.12,
    "veg": 0.08,
    "other": 0.05,
}

def _guess_family(name: str) -> str:
    n = (name or "").lower()
    if "кур" in n or "птиц" in n: return "poultry"
    if "говя" in n or "свини" in n or "барани" in n: return "meat"
    if "рыб" in n or "лосос" in n or "тунец" in n: return "fish"
    if "лук" in n or "перец" in n or "огур" in n or "тома" in n or "карто" in n: return "veg"
    return "other"

def _safe_pct(v: float) -> float:
    return max(0.0, min(0.95, v))

def rebalance(card: Dict[str, Any]) -> Dict[str, Any]:
    """Приводит нетто, брутто и общий выход к консистентным значениям.
       Если loss_pct отсутствует, ставит дефолт по семейству. Если gross < net — дорасчитывает gross."""
    c = {**card}
    ings = []
    for ing in c.get("ingredients", []):
        loss = ing.get("loss_pct", None)
        if loss is None:
            fam = _guess_family(ing.get("canonical") or ing.get("name", ""))
            loss = LOSS_DEFAULTS.get(fam, 0.05) * 100
        loss = _safe_pct(float(loss))
        net = float(ing.get("net_g", 0))
        gross = float(ing.get("gross_g", 0))
        if net > 0 and (gross <= 0 or gross < net):
            # gross = net / (1 - loss)
            gross = round(net / (1 - loss/100), 2)
        ings.append({**ing, "loss_pct": loss, "net_g": net, "gross_g": gross})
    c["ingredients"] = ings

    # Выравниваем суммарный нетто к yield.total_net_g и per_portion_g
    y = c.get("yield") or {}
    portions = int(y.get("portions", 1))
    per_portion = int(y.get("per_portion_g", 250))
    target_total = float(y.get("total_net_g", portions * per_portion))
    if target_total <= 0:
        target_total = portions * per_portion

    current_total = sum(i["net_g"] for i in ings) or 1.0
    scale = target_total / current_total
    if abs(scale - 1.0) > 0.01:
        for i in ings:
            i["net_g"] = round(i["net_g"] * scale, 2)
            i["gross_g"] = round(i["gross_g"] * scale, 2)

    c["ingredients"] = ings
    c["yield"] = {
        "portions": portions,
        "per_portion_g": per_portion,
        "total_net_g": int(round(sum(i["net_g"] for i in ings))),
    }
    return c