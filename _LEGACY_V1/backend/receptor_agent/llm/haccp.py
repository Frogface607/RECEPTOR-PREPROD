from __future__ import annotations
import json, os
from typing import Dict, Any, List
from pydantic import ValidationError
from .clients.openai_client import call_structured, get_client
from .prompts.haccp_templates import HACCP_SYSTEM, HACCP_GENERATE_PROMPT, HACCP_AUDIT_PROMPT
from .prompts.haccp_schemas import HACCP_ONLY_SCHEMA, HACCP_AUDIT_SCHEMA
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.techcards_v2.haccp_templates import enrich_haccp

def _use_llm() -> bool:
    return os.getenv("TECHCARDS_V2_USE_LLM","false").lower() in ("1","true","yes","on") and get_client() is not None

def generate_haccp(card_json: Dict[str, Any]) -> Dict[str, Any]:
    # если LLM выключен — обогатим нашими шаблонами и вернём базовый вариант
    if not _use_llm():
        data = enrich_haccp(card_json)
        tc = TechCardV2.model_validate(data)
        ok, issues = validate_card(tc)
        return tc.model_dump(by_alias=True)
    payload = {"card": card_json}
    out = call_structured(HACCP_SYSTEM, json.dumps({"instruction": HACCP_GENERATE_PROMPT, "input": payload}, ensure_ascii=False), HACCP_ONLY_SCHEMA)
    # сшиваем с исходной картой
    merged = {**card_json, **{"haccp": out["haccp"], "allergens": out.get("allergens", card_json.get("allergens", []))}}
    tc = TechCardV2.model_validate(merged)
    return tc.model_dump(by_alias=True)

def audit_haccp(card_json: Dict[str, Any]) -> Dict[str, Any]:
    if not _use_llm():
        # локальная проверка валидаторами
        tc = TechCardV2.model_validate(card_json)
        ok, issues = validate_card(tc)
        return {"issues": issues, "patch": tc.model_dump(by_alias=True)}
    payload = {"card": card_json}
    out = call_structured(HACCP_SYSTEM, json.dumps({"instruction": HACCP_AUDIT_PROMPT, "input": payload}, ensure_ascii=False), HACCP_AUDIT_SCHEMA)
    # пытаемся провалидировать patch
    try:
        tc = TechCardV2.model_validate(out["patch"])
        return {"issues": out.get("issues", []), "patch": tc.model_dump(by_alias=True)}
    except ValidationError as e:
        # если патч сломал схему — возвращаем исходник с найденными issues
        return {"issues": out.get("issues", []) + [f"patch invalid: {e}"], "patch": card_json}