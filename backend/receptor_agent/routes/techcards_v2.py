from __future__ import annotations
import io
import os
import traceback
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.exports.iiko_csv import techcard_to_csv
from receptor_agent.exports.xlsx import techcard_to_xlsx
from receptor_agent.exports.pdf import techcard_to_pdf
from receptor_agent.exports.zipper import make_zip
from receptor_agent.exports.iiko_exporter import export_techcard_to_iiko
from receptor_agent.exports.html import generate_print_html

router = APIRouter()

def _flag() -> bool:
    return os.getenv("FEATURE_TECHCARDS_V2", "false").lower() in ("1","true","yes","on")

def _llm_enabled() -> bool:
    return os.getenv("TECHCARDS_V2_USE_LLM","false").lower() in ("1","true","yes","on") and bool(os.getenv("OPENAI_API_KEY"))

@router.get("/techcards.v2/status")
def status_tc_v2():
    return {
        "feature_enabled": _flag(),
        "llm_enabled": _llm_enabled(),
        "model": os.getenv("TECHCARDS_V2_MODEL","gpt-4o-mini") if _llm_enabled() else None
    }

@router.post("/techcards.v2/generate")
def generate_tc_v2(profile: ProfileInput, use_llm: bool = Query(default=None, description="override env flag")):
    """
    Генерирует техкарту V2 с гарантированным JSON ответом.
    
    Returns:
        JSON: {
            "status": "success" | "draft" | "error",
            "card": TechCardV2 | null,
            "issues": [...],
            "message": "optional description"
        }
    """
    try:
        if not _flag():
            response_data = {
                "status": "error",
                "card": None,
                "issues": [{"type": "feature_disabled", "message": "TechCards V2 feature is disabled"}],
                "message": "Feature disabled"
            }
            return JSONResponse(content=response_data, headers={"Content-Type": "application/json; charset=utf-8"})
        
        # Set LLM override if provided
        if use_llm is not None:
            os.environ["TECHCARDS_V2_USE_LLM"] = "true" if use_llm else "false"
        
        # Run pipeline
        res = run_pipeline(profile)
        
        # Standard response contract with correct content type
        if res.status == "success":
            response_data = {
                "status": "success",
                "card": res.card.model_dump(by_alias=True, mode="json") if res.card else None,
                "issues": res.issues or [],
                "message": "Tech card generated successfully"
            }
            return JSONResponse(content=response_data, headers={"Content-Type": "application/json; charset=utf-8"})
        elif res.status == "draft":
            response_data = {
                "status": "draft", 
                "card": res.card.model_dump(by_alias=True, mode="json") if res.card else None,
                "issues": res.issues or [],
                "message": "Tech card generated with validation issues"
            }
            return JSONResponse(content=response_data, headers={"Content-Type": "application/json; charset=utf-8"})
        else:  # failed or any other status
            response_data = {
                "status": "error",
                "card": None,
                "issues": res.issues or [{"type": "pipeline_error", "message": "Pipeline execution failed"}],
                "message": f"Pipeline error: {res.status}"
            }
            return JSONResponse(content=response_data, headers={"Content-Type": "application/json; charset=utf-8"})
            
    except Exception as e:
        # Always return JSON even for exceptions
        error_message = str(e)
        stack_trace = traceback.format_exc()
        
        response_data = {
            "status": "error",
            "card": None,
            "issues": [
                {
                    "type": "exception",
                    "message": error_message,
                    "details": stack_trace if os.getenv("DEBUG", "false").lower() in ("1", "true") else None
                }
            ],
            "message": f"Server exception: {error_message}"
        }
        return JSONResponse(content=response_data, headers={"Content-Type": "application/json; charset=utf-8"})

@router.post("/techcards.v2/export/iiko")
def export_tc_v2_to_iiko(card: TechCardV2):
    """Экспорт техкарты в формат iiko (XLSX с листами Products и Recipes)"""
    if not _flag():
        raise HTTPException(404, "feature disabled")
    
    try:
        # Экспортируем в iiko формат
        xlsx_file, issues = export_techcard_to_iiko(card)
        
        # Создаем безопасное имя файла (только ASCII символы)
        import re
        safe_title = re.sub(r'[^\w\s-]', '', card.meta.title)  # Remove special chars
        safe_title = re.sub(r'[а-яё]', '', safe_title, flags=re.IGNORECASE)  # Remove Cyrillic
        safe_title = re.sub(r'\s+', '_', safe_title.strip())  # Replace spaces with underscores
        if not safe_title:  # If title becomes empty, use default
            safe_title = "techcard"
        filename = f"iiko_export_{safe_title}.xlsx"
        
        # Логируем issues если есть
        if issues:
            print(f"iiko export issues: {issues}")
        
        return StreamingResponse(
            io.BytesIO(xlsx_file.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        print(f"iiko export error: {e}")
        raise HTTPException(500, f"Export failed: {str(e)}")

@router.post("/techcards.v2/print")
def print_tc_v2(card: TechCardV2):
    """Генерация ГОСТ-печати A4 из TechCardV2"""
    if not _flag():
        raise HTTPException(404, "feature disabled")
    
    # Валидация техкарты
    ok, issues = validate_card(card)
    is_draft = not ok or len(issues) > 0
    
    # Определяем статус для водяного знака
    status = "draft" if is_draft else "success"
    
    # Генерируем HTML для печати
    html_content = generate_print_html(card, status, issues)
    
    return HTMLResponse(content=html_content, media_type="text/html")

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