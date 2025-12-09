from __future__ import annotations
from typing import Iterable, Set

# минимальный словарь → можно расширять
ALLERGEN_MAP = {
    "пшеница": "gluten",
    "мука": "gluten",
    "сливки": "milk",
    "молоко": "milk",
    "сыр": "milk",
    "арахис": "peanut",
    "грецкий орех": "tree_nut",
    "миндаль": "tree_nut",
    "фундук": "tree_nut",
    "креветка": "shellfish",
    "креветки": "shellfish",
    "краб": "shellfish",
    "яйцо": "egg",
    "яйца": "egg",
    "соевый соус": "soy",
    "соевые бобы": "soy",
    "рыба": "fish",
}

def detect_allergens(ingredient_names: Iterable[str]) -> Set[str]:
    found: Set[str] = set()
    for n in ingredient_names:
        key = (n or "").strip().lower()
        for k, tag in ALLERGEN_MAP.items():
            if k in key:
                found.add(tag)
    return found