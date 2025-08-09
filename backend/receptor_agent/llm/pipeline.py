from __future__ import annotations
from typing import Dict, Any, List
from pydantic import BaseModel
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.techcards_v2.normalize import normalize_card
from receptor_agent.techcards_v2.quantify import rebalance
from receptor_agent.techcards_v2.haccp_templates import enrich_haccp

class ProfileInput(BaseModel):
    name: str
    cuisine: str | None = None
    equipment: List[str] = []
    budget: float | None = None
    dietary: List[str] = []

class PipelineResult(BaseModel):
    card: TechCardV2
    issues: List[str] = []

def generate_draft(profile: ProfileInput, courses: int = 1) -> Dict[str, Any]:
    # как было — минимальный черновик
    return {
        "meta": {"name": f"Блюдо {profile.cuisine or 'авторское'}", "category": "Горячее", "cuisine": profile.cuisine},
        "yield": {"portions": 10, "per_portion_g": 250, "total_net_g": 2500},
        "ingredients": [
            {"name": "Куриное бедро без кожи", "uom": "g", "gross_g": 3000, "net_g": 2500, "loss_pct": 16.7},
            {"name": "Соль", "uom": "g", "gross_g": 20, "net_g": 20, "loss_pct": 0},
        ],
        "process": [{"step": 1, "desc": "Маринование 60 мин", "temp_c": 4, "time_min": 60}],
        "haccp": {"hazards": ["bio"], "ccp": [{"name": "Internal temp", "limit": "≥75°C", "monitoring": "термометр", "corrective": "доготовить"}]},
        "allergens": [],
    }

def normalize(draft: Dict[str, Any]) -> Dict[str, Any]:
    return normalize_card(draft)

def quantify(norm: Dict[str, Any]) -> Dict[str, Any]:
    return rebalance(norm)

def build_haccp(data: Dict[str, Any]) -> Dict[str, Any]:
    return enrich_haccp(data)

def critique(card: TechCardV2) -> List[str]:
    # простая самопроверка — всё в validators.validate_card
    ok, issues = validate_card(card)
    return issues if not ok else []

def run_pipeline(profile: ProfileInput) -> PipelineResult:
    draft = generate_draft(profile)
    norm = normalize(draft)
    quant = quantify(norm)
    final = build_haccp(quant)
    card = TechCardV2.model_validate(final)
    ok, issues = validate_card(card)
    # авто-фикс 1 проход: если расходится только total_net → пересчёт уже делает quantify()
    if not ok:
        # второй прогон re-validate без изменений, если остались — отдаём issues
        pass
    return PipelineResult(card=card, issues=issues)