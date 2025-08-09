from __future__ import annotations
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.exports.iiko_csv import techcard_to_csv
from receptor_agent.exports.xlsx import techcard_to_xlsx
from receptor_agent.exports.pdf import techcard_to_pdf
from receptor_agent.exports.zipper import make_zip

router = APIRouter()

def _flag() -> bool:
    return os.getenv("FEATURE_TECHCARDS_V2", "false").lower() in ("1","true","yes","on")

@router.post("/techcards.v2/generate", response_model=TechCardV2)
def generate_tc_v2(profile: ProfileInput):
    if not _flag():
        raise HTTPException(404, "feature disabled")
    res = run_pipeline(profile)
    ok, issues = validate_card(res.card)
    if not ok:
        raise HTTPException(400, f"validation failed: {issues}")
    return res.card

@router.post("/techcards.v2/export")
def export_tc_v2(card: TechCardV2):
    if not _flag():
        raise HTTPException(404, "feature disabled")
    # Валидация на всякий случай
    ok, issues = validate_card(card)
    if not ok:
        raise HTTPException(400, f"validation failed: {issues}")
    csv_str = techcard_to_csv(card).encode("utf-8")
    xlsx_bin = techcard_to_xlsx(card)
    pdf_bin = techcard_to_pdf(card)
    zip_bytes = make_zip({
        "techcard.csv": csv_str,
        "techcard.xlsx": xlsx_bin,
        "techcard.pdf": pdf_bin,
    })
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="techcard_v2_export.zip"'}
    )