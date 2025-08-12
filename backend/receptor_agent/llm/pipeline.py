from __future__ import annotations
import os, json
from typing import Dict, Any, List
from pydantic import BaseModel
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.techcards_v2.strict_validator import validate_techcard_v2, create_draft_response
from receptor_agent.techcards_v2.normalize import normalize_card
from receptor_agent.techcards_v2.quantify import rebalance
from receptor_agent.techcards_v2.haccp_templates import enrich_haccp

from .clients.openai_client import call_structured, get_client
from .prompts.templates import DRAFT_PROMPT, NORMALIZE_PROMPT, QUANTIFY_PROMPT, HACCP_PROMPT, CRITIC_PROMPT
from .prompts.schemas import TECHCARD_CORE_SCHEMA

def _use_llm() -> bool:
    return os.getenv("TECHCARDS_V2_USE_LLM", "false").lower() in ("1","true","yes","on") and get_client() is not None

class ProfileInput(BaseModel):
    name: str
    cuisine: str | None = None
    equipment: List[str] = []
    budget: float | None = None
    dietary: List[str] = []

class PipelineResult(BaseModel):
    card: TechCardV2 | None = None
    issues: List[str] = []
    status: str = "success"  # "success", "draft", "failed"
    raw_data: Dict[str, Any] | None = None

def _system() -> str:
    return "You return strictly JSON that matches the provided JSON Schema."

def _make_user(content: Dict[str, Any]) -> str:
    return json.dumps(content, ensure_ascii=False)

def generate_draft(profile: ProfileInput, courses: int = 1) -> Dict[str, Any]:
    if _use_llm():
        try:
            payload = {"profile": profile.model_dump()}
            return call_structured(_system()+"\n"+DRAFT_PROMPT, _make_user(payload), TECHCARD_CORE_SCHEMA)
        except Exception:
            # fallback на локальный режим при любой ошибке LLM
            pass
    # fallback локально
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
    if _use_llm():
        try:
            return call_structured(_system()+"\n"+NORMALIZE_PROMPT, _make_user({"draft": draft}), TECHCARD_CORE_SCHEMA)
        except Exception:
            pass
    return normalize_card(draft)

def quantify(norm: Dict[str, Any]) -> Dict[str, Any]:
    if _use_llm():
        try:
            return call_structured(_system()+"\n"+QUANTIFY_PROMPT, _make_user({"norm": norm}), TECHCARD_CORE_SCHEMA)
        except Exception:
            pass
    return rebalance(norm)

def build_haccp(data: Dict[str, Any]) -> Dict[str, Any]:
    if _use_llm():
        try:
            return call_structured(_system()+"\n"+HACCP_PROMPT, _make_user({"data": data}), TECHCARD_CORE_SCHEMA)
        except Exception:
            pass
    return enrich_haccp(data)

def critique(card: TechCardV2) -> List[str]:
    ok, issues = validate_card(card)
    if ok or not _use_llm():
        return issues
    # Позовем LLM для минимальных правок и re-validate
    try:
        fixed = call_structured(_system()+"\n"+CRITIC_PROMPT, _make_user({"card": card.model_dump(by_alias=True)}), TECHCARD_CORE_SCHEMA)
        new = TechCardV2.model_validate(fixed)
        ok2, issues2 = validate_card(new)
        if ok2: return []
        return issues2
    except Exception:
        return issues

def run_pipeline(profile: ProfileInput) -> PipelineResult:
    data = generate_draft(profile)
    data = normalize(data)
    data = quantify(data)
    data = build_haccp(data)
    card = TechCardV2.model_validate(data)
    ok, issues = validate_card(card)
    if not ok:
        issues = critique(card)
    return PipelineResult(card=card, issues=issues)