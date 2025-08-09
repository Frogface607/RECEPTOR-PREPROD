from __future__ import annotations
from typing import Dict, Any, List

TEMPLATES: Dict[str, Dict[str, Any]] = {
    "poultry": {
        "hazards": ["bio: Salmonella/Campylobacter", "phys: кости"],
        "ccp": [
            {"name":"Internal temp", "limit":"≥75°C", "monitoring":"термометр ядро", "corrective":"доготовить/утилизировать"},
            {"name":"Cold storage", "limit":"0…+4°C", "monitoring":"термометр", "corrective":"утилизировать"},
        ],
        "storage": "Готовая продукция 0…+4°C ≤48ч",
    },
    "fish": {
        "hazards": ["bio: паразиты/гистамин", "phys: кости"],
        "ccp": [
            {"name":"Internal temp", "limit":"≥63°C", "monitoring":"термометр", "corrective":"доготовить/утилизировать"},
        ],
        "storage": "0…+2°C ≤24ч",
    },
    "veg": {
        "hazards": ["bio: кросс-контаминация"],
        "ccp": [],
        "storage": "+2…+6°C ≤24ч",
    },
    "other": {
        "hazards": [],
        "ccp": [],
        "storage": "+2…+6°C",
    }
}

def _guess_family(name: str) -> str:
    n = (name or "").lower()
    if "кур" in n or "птиц" in n: return "poultry"
    if "рыб" in n or "лосос" in n or "тунец" in n: return "fish"
    if "лук" in n or "перец" in n or "огур" in n or "тома" in n or "карто" in n: return "veg"
    return "other"

def enrich_haccp(card: Dict[str, Any]) -> Dict[str, Any]:
    fam = _guess_family(" ".join([i.get("canonical") or i.get("name","") for i in card.get("ingredients", [])]))
    tpl = TEMPLATES.get(fam, TEMPLATES["other"])
    base = card.get("haccp") or {}
    haz = sorted(set((base.get("hazards") or []) + tpl["hazards"]))
    ccp = (base.get("ccp") or []) + tpl["ccp"]
    storage = base.get("storage") or tpl["storage"]
    return {**card, "haccp": {"hazards": haz, "ccp": ccp, "storage": storage}}