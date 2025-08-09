from __future__ import annotations
import os, uuid
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
from receptor_agent.menu_v2.schemas import MenuV2
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.exports.iiko_csv import techcard_to_csv
from receptor_agent.exports.xlsx import techcard_to_xlsx
from receptor_agent.exports.pdf import techcard_to_pdf
from receptor_agent.exports.zipper import make_zip

router = APIRouter()
MENUS_V2: Dict[str, MenuV2] = {}

def _flag() -> bool:
    return os.getenv("FEATURE_TECHCARDS_V2", "false").lower() in ("1","true","yes","on")

@router.post("/menus.v2/generate", response_model=MenuV2)
def generate_menu_v2(profile: ProfileInput, courses: int = 6):
    if not _flag():
        raise HTTPException(404, "feature disabled")
    items: list[TechCardV2] = []
    for _ in range(max(1, courses)):
        res = run_pipeline(profile)
        ok, issues = validate_card(res.card)
        if not ok:
            raise HTTPException(400, f"validation failed: {issues}")
        items.append(res.card)
    mid = uuid.uuid4().hex[:12]
    menu = MenuV2(menuId=mid, items=items)
    MENUS_V2[mid] = menu
    return menu

@router.post("/menus.v2/{menuId}/replace", response_model=TechCardV2)
def replace_item_v2(menuId: str, index: int, profile: ProfileInput):
    if not _flag():
        raise HTTPException(404, "feature disabled")
    menu = MENUS_V2.get(menuId)
    if not menu:
        raise HTTPException(404, "menu not found")
    if not (0 <= index < len(menu.items)):
        raise HTTPException(400, "index out of range")
    res = run_pipeline(profile)
    ok, issues = validate_card(res.card)
    if not ok:
        raise HTTPException(400, f"validation failed: {issues}")
    menu.items[index] = res.card
    MENUS_V2[menuId] = menu
    return res.card

@router.get("/menus.v2/{menuId}/export")
def export_menu_v2(menuId: str):
    if not _flag():
        raise HTTPException(404, "feature disabled")
    menu = MENUS_V2.get(menuId)
    if not menu:
        raise HTTPException(404, "menu not found")
    files: dict[str, bytes] = {}
    # Добавляем по блюду три формата
    for idx, card in enumerate(menu.items, start=1):
        base = f"{idx:02d}_{card.meta.name}".replace("/", "_")
        files[f"{base}/techcard.csv"]  = techcard_to_csv(card).encode("utf-8")
        files[f"{base}/techcard.xlsx"] = techcard_to_xlsx(card)
        files[f"{base}/techcard.pdf"]  = techcard_to_pdf(card)
    # Индекс JSON меню
    from pydantic import TypeAdapter
    ta = TypeAdapter(MenuV2)
    files["menu.json"] = ta.dump_json(menu, indent=2)
    zip_bytes = make_zip(files)
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="menu_v2_{menuId}.zip"'}
    )