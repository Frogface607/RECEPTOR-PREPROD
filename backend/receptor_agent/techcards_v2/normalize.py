from __future__ import annotations
from typing import Dict, Any, Tuple

# Мини-словарь канонизации и единиц
SYNONYMS = {
    "кур бедро": "Куриное бедро без кожи",
    "бедро куриное": "Куриное бедро без кожи",
    "лайм": "Лайм свежий",
    "соль повара": "Соль",
}
UOM_MAP = {
    "гр": "g", "г": "g", "g": "g",
    "мл": "ml", "ml": "ml",
    "шт": "pcs", "pcs": "pcs",
}

def _canon_name(name: str) -> str:
    n = (name or "").strip()
    low = n.lower()
    for k, v in SYNONYMS.items():
        if k in low:
            return v
    return n

def _canon_uom(uom: str) -> str:
    return UOM_MAP.get((uom or "").lower(), "g")

def normalize_card(data: Dict[str, Any]) -> Dict[str, Any]:
    """Нормализует имена ингредиентов и единицы в g/ml/pcs, расставляет canonical."""
    data = {**data}
    ings = []
    for ing in data.get("ingredients", []):
        name = ing.get("name", "")
        uom = _canon_uom(ing.get("uom", "g"))
        canon = _canon_name(name)
        ings.append({
            **ing,
            "name": name,
            "uom": uom,
            "canonical": canon if canon != name else ing.get("canonical"),
        })
    data["ingredients"] = ings
    return data