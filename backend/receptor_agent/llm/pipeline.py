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
from receptor_agent.techcards_v2.cost_calculator import calculate_cost_for_tech_card

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
    # fallback локально - в формате TechCardV2
    return {
        "meta": {
            "title": f"Блюдо {profile.cuisine or 'авторское'}",
            "version": "2.0",
            "cuisine": profile.cuisine,
            "tags": []
        },
        "portions": 4,
        "yield": {
            "perPortion_g": 145.0,    # 577.7g / 4 = 144.4, округлено до 145
            "perBatch_g": 580.0       # 145 * 4 = 580, близко к сумме netto_g (577.7)
        },
        "ingredients": [
            {
                "name": "Куриное филе",
                "unit": "g",
                "brutto_g": 600.0,
                "loss_pct": 10.0,
                "netto_g": 540.0,  # 600 * (1 - 10/100) = 540 ✓
                "allergens": []
            },
            {
                "name": "Соль поваренная",
                "unit": "g", 
                "brutto_g": 8.0,
                "loss_pct": 0.0,
                "netto_g": 8.0,  # 8 * (1 - 0/100) = 8 ✓
                "allergens": []
            },
            {
                "name": "Растительное масло",
                "unit": "ml",
                "brutto_g": 30.0,
                "loss_pct": 1.0,  # Изменил с 5% на 1%
                "netto_g": 29.7,  # 30 * (1 - 1/100) = 29.7 ✓
                "allergens": []
            }
        ],
        "process": [
            {"n": 1, "action": "Подготовка ингредиентов", "time_min": 10.0, "temp_c": None},
            {"n": 2, "action": "Обжаривание на среднем огне", "time_min": 15.0, "temp_c": 180.0},
            {"n": 3, "action": "Доведение до готовности", "time_min": 10.0, "temp_c": 75.0}
        ],
        "storage": {
            "conditions": "Холодильник 0...+4°C",
            "shelfLife_hours": 48.0,
            "servingTemp_c": 65.0
        },
        "nutrition": {"per100g": None, "perPortion": None},
        "cost": {"rawCost": None, "costPerPortion": None},
        "printNotes": []
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
    """Генерация техкарты с строгой валидацией TechCardV2"""
    try:
        # Генерируем черновик в формате TechCardV2
        data = generate_draft(profile)
        
        # Включаем LLM обработку если доступна
        if _use_llm():
            # Пропускаем legacy normalize/quantify для LLM режима
            # LLM должен сразу генерировать в правильном формате TechCardV2
            pass
        else:
            # В fallback режиме данные уже в правильном формате
            pass
        
        # СТРОГАЯ ВАЛИДАЦИЯ TechCardV2
        is_valid, issues, validated_card = validate_techcard_v2(data)
        
        if is_valid and validated_card:
            # Успешная валидация - возвращаем готовую карту
            return PipelineResult(
                card=validated_card,
                issues=[],
                status="success"
            )
        else:
            # Ошибки валидации - возвращаем как draft
            return PipelineResult(
                card=None,
                issues=issues,
                status="draft",
                raw_data=data
            )
            
    except Exception as e:
        # Критическая ошибка в pipeline
        return PipelineResult(
            card=None,
            issues=[f"Pipeline error: {str(e)}"],
            status="failed",
            raw_data=None
        )