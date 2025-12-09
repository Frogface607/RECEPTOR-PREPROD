from __future__ import annotations
import os
from fastapi import APIRouter, HTTPException
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.llm.haccp import generate_haccp, audit_haccp

router = APIRouter()

def _flag() -> bool:
    return os.getenv("FEATURE_TECHCARDS_V2","false").lower() in ("1","true","yes","on")

@router.post("/haccp.v2/generate", response_model=TechCardV2)
def haccp_generate(card: TechCardV2):
    if not _flag():
        raise HTTPException(404, "feature disabled")
    out = generate_haccp(card.model_dump(by_alias=True))
    tc = TechCardV2.model_validate(out)
    ok, issues = validate_card(tc)
    if not ok:
        raise HTTPException(400, f"validation failed: {issues}")
    return tc

@router.post("/haccp.v2/audit")
def haccp_audit(card: TechCardV2):
    if not _flag():
        raise HTTPException(404, "feature disabled")
    result = audit_haccp(card.model_dump(by_alias=True))
    # patch может быть невалидным, но мы его не навязываем
    return result