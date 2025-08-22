from __future__ import annotations
import io
import json
import os
import traceback
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from typing import Optional
from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.techcards_v2.quality_validator import QualityValidator
from receptor_agent.exports.iiko_csv import techcard_to_csv
from receptor_agent.exports.xlsx import techcard_to_xlsx
from receptor_agent.exports.pdf import techcard_to_pdf
from receptor_agent.exports.zipper import make_zip
from receptor_agent.exports.iiko_exporter import export_techcard_to_iiko
from receptor_agent.exports.html import generate_print_html
from receptor_agent.exports.iiko_xlsx import (
    create_iiko_ttk_xlsx, 
    find_dish_in_iiko_rms, 
    generate_dish_codes, 
    create_dish_skeletons_xlsx
)

router = APIRouter()
logger = logging.getLogger(__name__)

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

@router.post("/techcards.v2/export/iiko.xlsx")
def export_tc_v2_to_iiko_ttk_xlsx(card: TechCardV2):
    """Экспорт техкарты в формат iiko XLSX (ТТК по шаблону iikoWeb)"""
    if not _flag():
        raise HTTPException(404, "feature disabled")
    
    try:
        from ..exports.iiko_xlsx import create_iiko_ttk_xlsx
        
        # Генерируем XLSX файл для импорта ТТК
        xlsx_buffer, issues = create_iiko_ttk_xlsx(card)
        
        # Создаем безопасное имя файла  
        import re
        safe_title = re.sub(r'[^\w\s-]', '', card.meta.title)  # Remove special chars
        safe_title = re.sub(r'[а-яё]', '', safe_title, flags=re.IGNORECASE)  # Remove Cyrillic  
        safe_title = re.sub(r'\s+', '_', safe_title.strip())  # Replace spaces with underscores
        if not safe_title:  # If title becomes empty, use default
            safe_title = "techcard"
        filename = f"iiko_ttk_{safe_title}.xlsx"
        
        # Логируем issues если есть (особенно noSku warnings)
        if issues:
            print(f"iiko TTK XLSX export issues: {issues}")
        
        xlsx_buffer.seek(0)
        return StreamingResponse(
            iter([xlsx_buffer.read()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        print(f"iiko TTK XLSX export error: {e}")
        raise HTTPException(500, f"Export failed: {str(e)}")

@router.post("/techcards.v2/export/iiko.csv")
def export_tc_v2_to_iiko_csv(card: TechCardV2):
    """Экспорт техкарты в формат iiko CSV (ZIP с products.csv и recipes.csv для импорта)"""
    if not _flag():
        raise HTTPException(404, "feature disabled")
    
    try:
        from ..exports.iiko_csv import generate_iiko_import_csv_zip
        
        # Генерируем ZIP с CSV файлами
        zip_buffer, issues = generate_iiko_import_csv_zip([card])
        
        # Создаем безопасное имя файла  
        import re
        safe_title = re.sub(r'[^\w\s-]', '', card.meta.title)  # Remove special chars
        safe_title = re.sub(r'[а-яё]', '', safe_title, flags=re.IGNORECASE)  # Remove Cyrillic  
        safe_title = re.sub(r'\s+', '_', safe_title.strip())  # Replace spaces with underscores
        if not safe_title:  # If title becomes empty, use default
            safe_title = "techcard"
        filename = f"iiko_export_{safe_title}.zip"
        
        # Логируем issues если есть (особенно noSku warnings)
        if issues:
            print(f"iiko CSV export issues: {issues}")
            # Добавляем issues в response headers для frontend
            issues_json = json.dumps([{"type": issue["type"], "name": issue["name"], "hint": issue["hint"]} for issue in issues])
        
        zip_buffer.seek(0)
        return StreamingResponse(
            iter([zip_buffer.read()]),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        print(f"iiko CSV export error: {e}")
        raise HTTPException(500, f"Export failed: {str(e)}")

@router.get("/techcards.v2/catalog-search")
def search_catalog(
    q: str = Query(..., description="Search query"), 
    limit: int = Query(10, ge=1, le=50),
    source: str = Query("iiko", description="Data source: iiko, usda, price, nutrition, rms, all"),
    orgId: Optional[str] = Query("default", description="Organization ID for iiko RMS search"),  # P0: Add orgId parameter
    search_by: Optional[str] = Query("name", description="Search type: name, article, id")  # FIX-A: Add search_by parameter
):
    """
    Поиск по объединенному каталогу цен, питания и USDA для маппинга ингредиентов.
    
    Parameters:
        - q: Search query (ingredient name)
        - limit: Maximum number of results (1-50)
        - source: Data source filter (usda, price, nutrition, all)
    
    Returns:
        JSON: {
            "status": "success",
            "items": [
                {
                    "name": "string",
                    "canonical_id": "string", 
                    "fdc_id": "int|null",
                    "sku_id": "string|null", 
                    "category": "string",
                    "unit": "kg|l|pcs",
                    "price": "float|null",
                    "has_nutrition": "boolean",
                    "nutrition_preview": "string|null",
                    "source": "usda|catalog|bootstrap|price|iiko|rms"
                }
            ]
        }
    """
    try:
        import json
        import os
        from pathlib import Path
        
        results = []
        query = q.lower().strip()
        
        # Инициализируем USDA провайдер если нужен
        usda_results = []
        if source in ("usda", "all"):
            try:
                from ..techcards_v2.nutrition_calculator import USDANutritionProvider
                usda_provider = USDANutritionProvider()
                
                # Поиск в USDA базе
                if usda_provider.canonical_map:
                    for key, data in usda_provider.canonical_map.items():
                        if 'fdc_id' in data:  # Это синоним
                            fdc_id = data['fdc_id']
                            canonical_id = data.get('canonical_id')
                            
                            # Проверяем совпадение с запросом
                            if (query in key.lower() or 
                                any(query in word for word in key.lower().split())):
                                
                                # Получаем полные данные из USDA
                                usda_nutrition = usda_provider.find_nutrition_data(key, canonical_id)
                                if usda_nutrition:
                                    kcal = usda_nutrition['per100g']['kcal']
                                    usda_results.append({
                                        "name": key,
                                        "canonical_id": canonical_id,
                                        "fdc_id": fdc_id,
                                        "sku_id": None,
                                        "category": usda_nutrition.get('food_category', 'USDA'),
                                        "unit": "g",
                                        "price": None,
                                        "has_nutrition": True,
                                        "nutrition_preview": f"{kcal} ккал/100г",
                                        "source": "usda"
                                    })
                        
                        # Ограничиваем результаты для производительности
                        if len(usda_results) >= limit:
                            break
                            
            except Exception as e:
                print(f"USDA search error: {e}")
        
        # Price search results (if needed)
        price_results = []
        if source in ("price", "all"):
            try:
                from ..techcards_v2.price_provider import PriceProvider
                price_provider = PriceProvider()
                
                # Use price provider search functionality
                price_candidates = price_provider.search_for_mapping(query, limit)
                
                for item in price_candidates:
                    price_results.append({
                        "name": item["name"],
                        "canonical_id": item.get("canonical_id"),
                        "fdc_id": None,
                        "sku_id": item.get("skuId"), 
                        "category": item.get("source", "price"),
                        "unit": item["unit"],
                        "price": item["price_per_unit"],
                        "has_nutrition": False,
                        "nutrition_preview": None,
                        "source": item["source"],
                        "currency": item.get("currency", "RUB"),
                        "asOf": item.get("asOf").isoformat() if hasattr(item.get("asOf"), 'isoformat') else str(item.get("asOf")) if item.get("asOf") else None
                    })
                    
            except Exception as e:
                print(f"Price search error: {e}")
        
        # iiko search results (if needed)
        iiko_results = []
        if source in ("iiko", "all"):
            try:
                from ..integrations.iiko_service import get_iiko_service
                iiko_service = get_iiko_service()
                
                # Get organizations from token record
                organizations = iiko_service.get_organizations()
                if organizations:
                    organization_id = organizations[0]["id"]  # Use first organization
                    
                    # Search products in iiko
                    iiko_products = iiko_service.search_products(organization_id, query, limit)
                    
                    for product in iiko_products:
                        iiko_results.append({
                            "name": product["name"],
                            "canonical_id": None,
                            "fdc_id": None,
                            "sku_id": product["sku_id"],
                            "category": product.get("group_name", "iiko"),
                            "unit": product["unit"],
                            "price": product["price_per_unit"],
                            "has_nutrition": False,
                            "nutrition_preview": None,
                            "source": "iiko",
                            "currency": product["currency"],
                            "asOf": product["asOf"].isoformat() if hasattr(product["asOf"], 'isoformat') else str(product["asOf"]),
                            "match_score": product["match_score"],
                            "article": product.get("article")
                        })
                        
            except Exception as e:
                print(f"iiko search error: {e}")
        
        # iiko RMS search results (if needed) with enhanced normalization
        rms_results = []
        if source in ("rms", "iiko", "all"):
            try:
                from ..integrations.iiko_rms_service import get_iiko_rms_service
                rms_service = get_iiko_rms_service()
                
                # P0: Use provided orgId parameter, fallback to connection status
                organization_id = orgId or "default"
                
                # Get RMS connection status to verify connectivity
                connection_status = rms_service.get_rms_connection_status()
                if connection_status.get("status") == "connected":
                    # Override orgId with actual connected organization if available
                    if connection_status.get("organization_id"):
                        organization_id = connection_status["organization_id"]
                    
                    # Enhanced search with RU-normalization
                    rms_products = rms_service.search_rms_products_enhanced(organization_id, query, limit)
                    
                    for product in rms_products:
                        rms_results.append({
                            "name": product["name"],
                            "canonical_id": None,
                            "fdc_id": None,
                            "sku_id": product["sku_id"],
                            "category": product.get("group_name", "iiko"),
                            "unit": product["unit"],
                            "price": product["price_per_unit"],
                            "has_nutrition": False,
                            "nutrition_preview": None,
                            "source": "iiko",  # Always show as "iiko" source to user
                            "currency": product["currency"],
                            "vat_pct": product.get("vat_pct", 0.0),
                            "asOf": product["asOf"].isoformat() if hasattr(product["asOf"], 'isoformat') else str(product["asOf"]),
                            "match_score": product["match_score"],
                            "article": product.get("article"),
                            "product_type": product.get("product_type", "product"),
                            "active": product.get("active", True)
                        })
                else:
                    logger.warning(f"RMS connection not active: {connection_status.get('status', 'unknown')}")
                        
            except Exception as e:
                logger.error(f"RMS search error: {str(e)}")
                print(f"RMS search error: {e}")
        
        # Каталоги цен и питания (если нужны)
        catalog_results = []
        if source in ("nutrition", "all"):
            current_dir = Path(__file__).parent.parent.parent
            
            # Загружаем каталог питания
            nutrition_data = {}
            if source in ("nutrition", "all"):
                nutrition_catalog_path = current_dir / "data" / "nutrition_catalog.dev.json"
                if nutrition_catalog_path.exists():
                    with open(nutrition_catalog_path, 'r', encoding='utf-8') as f:
                        nutrition_catalog = json.load(f)
                        for item in nutrition_catalog.get("items", []):
                            name = item.get("name", "").lower()
                            nutrition_data[name] = {
                                "canonical_id": item.get("canonical_id"),
                                "name": item.get("name"),
                                "nutrition": item.get("per100g", {})
                            }
            
            # Объединяем и ищем в каталогах
            all_items = {}
            
            # Добавляем из каталога питания
            for name_lower, nutrition_info in nutrition_data.items():
                if (query in name_lower or any(query in word for word in name_lower.split())):
                    all_items[name_lower] = {
                        "name": nutrition_info["name"],
                        "canonical_id": nutrition_info["canonical_id"],
                        "fdc_id": None,
                        "sku_id": None,
                        "category": "nutrition_only",
                        "unit": "g",
                        "price": None,
                        "has_nutrition": True,
                        "nutrition_preview": f"{nutrition_info['nutrition'].get('kcal', 0)} ккал/100г",
                        "source": "catalog"
                    }
            
            catalog_results = list(all_items.values())
        
        # Объединяем результаты с приоритетом: iiko/RMS → Price → USDA → остальные
        all_results = rms_results + price_results + usda_results + catalog_results
        
        # Сортируем по релевантности: iiko/RMS приоритет, затем точные совпадения
        def sort_key(x):
            source_priority = {
                "iiko": 0,                                  # iiko RMS (highest priority)
                "rms": 0,                                   # Also iiko RMS
                "catalog": 1, "bootstrap": 1, "user": 1,   # Price sources  
                "usda": 2,                                  # USDA
                "catalog": 3                               # Other catalog
            }.get(x.get("source", "unknown"), 4)
            
            # Boost exact matches
            name_match = 0 if query in x["name"].lower() else 1
            score_boost = x.get("match_score", 0.5)  # Use match score from RMS
            
            return (source_priority, -score_boost, name_match, -len(x["name"]), x["name"].lower())
        
        sorted_items = sorted(all_results, key=sort_key)[:limit]
        
        # Get iiko product count for badge display
        iiko_count = len(rms_results)
        last_sync = connection_status.get("last_connection") if connection_status else None
        if last_sync and hasattr(last_sync, 'isoformat'):
            last_sync = last_sync.isoformat()
        elif last_sync:
            last_sync = str(last_sync)
        
        return JSONResponse(content={
            "status": "success", 
            "items": sorted_items,
            "total_found": len(all_results),
            "price_count": len(price_results),
            "rms_count": len(rms_results),
            "iiko_count": iiko_count,  # For UI badge
            "usda_count": len(usda_results),
            "catalog_count": len(catalog_results),
            "default_source": "iiko",
            "iiko_badge": {
                "count": iiko_count,
                "last_sync": last_sync,
                "connection_status": connection_status.get("status") if connection_status else "not_connected",
                "orgId": organization_id  # P0: Include orgId in badge for debugging
            }
        }, headers={"Content-Type": "application/json; charset=utf-8"})
        
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "items": [],
            "message": f"Search failed: {str(e)}"
        }, headers={"Content-Type": "application/json; charset=utf-8"})


@router.post("/techcards.v2/recalc")
def recalc_tc_v2(techcard: TechCardV2):
    """
    Пересчитывает cost и nutrition для техкарты после обновления маппинга ингредиентов.
    
    Returns:
        JSON: {
            "status": "success" | "error",
            "card": TechCardV2,
            "message": "description"
        }
    """
    try:
        # Импортируем калькуляторы
        from ..techcards_v2.cost_calculator import calculate_cost_for_tech_card
        from ..techcards_v2.nutrition_calculator import calculate_nutrition_for_tech_card
        
        # Запускаем только калькуляторы (без LLM)
        updated_card = techcard
        
        # Пересчитываем стоимость
        try:
            updated_card = calculate_cost_for_tech_card(updated_card)
        except Exception as cost_error:
            print(f"Cost calculation warning: {cost_error}")
            # Продолжаем даже если стоимость не рассчиталась
        
        # Пересчитываем питание
        try:
            updated_card = calculate_nutrition_for_tech_card(updated_card)
        except Exception as nutrition_error:
            print(f"Nutrition calculation warning: {nutrition_error}")
            # Продолжаем даже если питание не рассчиталось
        
        response_data = {
            "status": "success",
            "card": updated_card.model_dump(by_alias=True, mode="json"),
            "message": "Tech card recalculated successfully"
        }
        return JSONResponse(content=response_data, headers={"Content-Type": "application/json; charset=utf-8"})
        
    except Exception as e:
        error_message = str(e)
        response_data = {
            "status": "error",
            "card": None,
            "message": f"Recalculation failed: {error_message}"
        }
        return JSONResponse(content=response_data, headers={"Content-Type": "application/json; charset=utf-8"})
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
def export_tc_v2(request: dict):
    """
    E. Operational Rounding v1: Экспорт техкарты с опциональным операционным округлением
    
    Body:
    {
        "card": TechCardV2,
        "options": {
            "operational_rounding": false
        }
    }
    """
    if not _flag():
        raise HTTPException(404, "feature disabled")
        
    # Извлекаем данные из запроса
    card_data = request.get('card')
    options = request.get('options', {})
    use_operational_rounding = options.get('operational_rounding', False)
    
    if not card_data:
        raise HTTPException(400, "card is required")
    
    # Валидируем техкарту
    try:
        card = TechCardV2.model_validate(card_data)
    except Exception as e:
        raise HTTPException(400, f"Invalid techcard: {str(e)}")
    
    # Валидация на всякий случай
    ok, issues = validate_card(card)
    if not ok:
        raise HTTPException(400, f"validation failed: {issues}")
        
    csv_str = techcard_to_csv(card).encode("utf-8")
    xlsx_bin = techcard_to_xlsx(card)
    
    # E. Operational Rounding v1: PDF с операционным округлением
    pdf_bin = techcard_to_pdf(card, use_operational_rounding=use_operational_rounding)
    
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


# GX-02: Quality Validation Endpoints
@router.post("/techcards.v2/validate/quality")
async def validate_techcard_quality(request: Request):
    """
    GX-02: Validate TechCard quality and get improvement suggestions
    """
    try:
        body = await request.json()
        techcard_data = body.get('techcard')
        
        if not techcard_data:
            raise HTTPException(400, "techcard data required")
        
        # Initialize quality validator
        validator = QualityValidator()
        
        # Validate and normalize
        normalized_card, issues = validator.validate_techcard(techcard_data)
        quality_score = validator.get_quality_score(issues)
        fix_banners = validator.generate_fix_banners(issues)
        
        return {
            "status": "success",
            "normalized_techcard": normalized_card,
            "quality_score": quality_score,
            "validation_issues": issues,
            "fix_banners": fix_banners,
            "is_production_ready": quality_score["is_production_ready"]
        }
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Quality validation error: {e}")
        raise HTTPException(500, f"Quality validation failed: {str(e)}")


@router.post("/techcards.v2/normalize")
async def normalize_techcard_ranges(request: Request):
    """
    GX-02: Normalize range values (0-4 → numbers) in TechCard
    """
    try:
        body = await request.json()
        techcard_data = body.get('techcard')
        
        if not techcard_data:
            raise HTTPException(400, "techcard data required")
        
        # Initialize quality validator
        validator = QualityValidator()
        
        # Only normalize ranges, skip other validations
        normalized_card, range_issues = validator._normalize_ranges(techcard_data)
        
        return {
            "status": "success",
            "normalized_techcard": normalized_card,
            "normalization_issues": range_issues
        }
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Normalization error: {e}")
        raise HTTPException(500, f"Normalization failed: {str(e)}")


@router.post("/techcards.v2/quality/score")
async def get_quality_score(request: Request):
    """
    GX-02: Get quality score without modifying TechCard
    """
    try:
        body = await request.json()
        techcard_data = body.get('techcard')
        
        if not techcard_data:
            raise HTTPException(400, "techcard data required")
        
        # Initialize quality validator
        validator = QualityValidator()
        
        # Run validation without normalization
        _, issues = validator.validate_techcard(techcard_data)
        quality_score = validator.get_quality_score(issues)
        fix_banners = validator.generate_fix_banners(issues)
        
        return {
            "status": "success",
            "quality_score": quality_score,
            "fix_banners": fix_banners,
            "validation_issues": issues
        }
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Quality score calculation error: {e}")
        raise HTTPException(500, f"Quality score calculation failed: {str(e)}")


# GX-02: Enhanced Auto-mapping Endpoints  
@router.post("/techcards.v2/mapping/enhanced")
async def enhanced_auto_mapping(request: Request):
    """
    GX-02: Enhanced auto-mapping with RU-synonyms and confidence scoring
    ≥0.90 автопринятие; 0.70–0.89 на проверку
    """
    try:
        body = await request.json()
        techcard_data = body.get('techcard')
        
        if not techcard_data:
            raise HTTPException(400, "techcard data required")
        
        ingredients = techcard_data.get('ingredients', [])
        if not ingredients:
            raise HTTPException(400, "no ingredients to map")
        
        # Get organization ID (defaulting for now)
        organization_id = body.get('organization_id', 'default')
        
        # Initialize enhanced mapping service
        from ..integrations.enhanced_mapping_service import get_enhanced_mapping_service
        mapping_service = get_enhanced_mapping_service()
        
        # Perform enhanced auto-mapping
        mapping_result = mapping_service.enhanced_auto_mapping(ingredients, organization_id)
        
        # Auto-apply high confidence mappings if requested
        auto_apply = body.get('auto_apply', False)
        if auto_apply and mapping_result["status"] == "success":
            updated_techcard = mapping_service.apply_auto_accepted_mappings(
                techcard_data, mapping_result["results"]
            )
            mapping_result["updated_techcard"] = updated_techcard
        
        return {
            "status": "success",
            "mapping_results": mapping_result,
            "auto_applied": auto_apply
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced auto-mapping error: {e}")
        raise HTTPException(500, f"Enhanced auto-mapping failed: {str(e)}")


@router.post("/techcards.v2/mapping/apply")
async def apply_mapping_changes(request: Request):
    """
    GX-02: Apply user-selected mapping changes to TechCard
    """
    try:
        body = await request.json()
        techcard_data = body.get('techcard')
        mapping_decisions = body.get('mapping_decisions', {})  # {ingredient_name: "accepted"/"rejected"}
        
        if not techcard_data:
            raise HTTPException(400, "techcard data required")
        
        if not mapping_decisions:
            raise HTTPException(400, "no mapping decisions provided")
        
        # Apply mapping changes
        updated_card = techcard_data.copy()
        ingredients = updated_card.get("ingredients", [])
        
        applied_count = 0
        for ingredient in ingredients:
            ingredient_name = ingredient.get("name", "").strip()
            decision = mapping_decisions.get(ingredient_name)
            
            if decision and isinstance(decision, dict) and decision.get("action") == "accept":
                suggestion = decision.get("suggestion", {})
                if suggestion.get("sku_id") and not ingredient.get("skuId"):
                    ingredient["skuId"] = suggestion["sku_id"]
                    applied_count += 1
        
        # Save user decisions for future learning
        organization_id = body.get('organization_id', 'default')
        
        # Note: This would be expanded to save to database for learning
        logger.info(f"Applied {applied_count} mapping changes for organization {organization_id}")
        
        return {
            "status": "success",
            "updated_techcard": updated_card,
            "applied_count": applied_count,
            "message": f"Применено {applied_count} изменений маппинга"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply mapping changes error: {e}")
        raise HTTPException(500, f"Apply mapping changes failed: {str(e)}")


@router.get("/techcards.v2/mapping/synonyms")
async def get_ru_synonyms():
    """
    GX-02: Get Russian synonyms dictionary for frontend preview
    """
    try:
        from ..integrations.enhanced_mapping_service import get_enhanced_mapping_service
        mapping_service = get_enhanced_mapping_service()
        
        # Return limited set for preview (don't expose all internal synonyms)
        preview_synonyms = {}
        count = 0
        for canonical, synonyms in mapping_service.ru_synonyms.items():
            if count < 10:  # Limit for API response size
                preview_synonyms[canonical] = synonyms[:5]  # Max 5 synonyms per item
                count += 1
            else:
                break
        
        return {
            "status": "success",
            "synonyms_preview": preview_synonyms,
            "total_groups": len(mapping_service.ru_synonyms),
            "message": f"Загружено {len(mapping_service.ru_synonyms)} групп синонимов"
        }
        
    except Exception as e:
        logger.error(f"Get synonyms error: {e}")
        raise HTTPException(500, f"Get synonyms failed: {str(e)}")


# Export Wizard v1: Enhanced Export Endpoints
@router.post("/techcards.v2/export/enhanced/iiko.xlsx")
async def enhanced_export_iiko_xlsx(request: Request):
    """
    Export Wizard v1: Enhanced export with validation and tracking
    """
    try:
        body = await request.json()
        logger.info(f"Enhanced export request body keys: {list(body.keys()) if isinstance(body, dict) else 'NOT_DICT'}")
        logger.info(f"Body type: {type(body)}")
        
        techcard_data = body.get('techcard')
        
        if not techcard_data:
            raise HTTPException(400, "techcard data required")
        
        # Step 1: Pre-export validation using GX-02 quality validator
        from ..techcards_v2.quality_validator import QualityValidator
        validator = QualityValidator()
        
        normalized_card, validation_issues = validator.validate_techcard(techcard_data)
        quality_score = validator.get_quality_score(validation_issues)
        
        # Check for blocking errors
        blocking_errors = [i for i in validation_issues if i.get('level') == 'error']
        
        if blocking_errors:
            # Block export due to critical validation errors
            return {
                "status": "blocked",
                "message": "Экспорт заблокирован из-за критических ошибок валидации",
                "blocking_errors": blocking_errors,
                "quality_score": quality_score,
                "can_auto_fix": len([e for e in blocking_errors if e.get('type') in ['rangeNormalized', 'yieldInconsistent']]) > 0
            }
        
        # Step 2: Export XLSX with Feature A & B support
        from ..exports.iiko_xlsx import create_iiko_ttk_xlsx
        from ..techcards_v2.schemas import TechCardV2
        
        # Создаем TechCardV2 объект из dict для экспорта
        try:
            techcard_obj = TechCardV2.model_validate(normalized_card)
        except Exception as e:
            logger.error(f"TechCardV2 validation error during export: {e}")
            # Используем исходные данные если нормализация не прошла
            techcard_obj = TechCardV2.model_validate(techcard_data)
        
        # Feature A & B: Подготовка опций экспорта
        export_options_input = body.get('export_options', {})
        export_options = {
            'use_product_codes': export_options_input.get('use_product_codes', True),  # Feature A: по умолчанию включен
            'dish_codes_mapping': export_options_input.get('dish_codes_mapping', {}),  # Feature B: коды блюд
            'operational_rounding': export_options_input.get('operational_rounding', True),  # Operational Rounding v1: по умолчанию включен
            'rms_service': None  # Будет установлен ниже
        }
        
        # Получаем RMS сервис для кодов продуктов
        try:
            from ..integrations.iiko_rms_service import get_iiko_rms_service
            rms_service = get_iiko_rms_service()
            export_options['rms_service'] = rms_service
        except Exception as e:
            logger.warning(f"Could not get RMS service for product codes: {e}")
        
        excel_buffer, export_issues = create_iiko_ttk_xlsx(techcard_obj, export_options)
        
        # Step 3: Track export
        organization_id = body.get('organization_id', 'default')
        user_email = body.get('user_email', 'unknown')
        techcard_id = body.get('techcard_id', 'temp')
        
        from ..integrations.export_tracking_service import get_export_tracking_service
        tracking_service = get_export_tracking_service()
        
        # Record successful export
        ingredients_count = len(techcard_data.get('ingredients', []))
        file_size = len(excel_buffer.getvalue())
        
        tracking_result = tracking_service.record_export(
            organization_id=organization_id,
            techcard_id=techcard_id,
            techcard_title=techcard_data.get('meta', {}).get('title', 'Untitled'),
            user_email=user_email,
            export_type="iiko_xlsx_enhanced",
            ingredients_count=ingredients_count,
            file_size_bytes=file_size,
            result="success"
        )
        
        # Return file
        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="techcard_{techcard_id}_export.xlsx"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced export error: {e}")
        import traceback
        logger.error(f"Enhanced export traceback: {traceback.format_exc()}")
        
        # Record failed export
        try:
            organization_id = body.get('organization_id', 'default')
            user_email = body.get('user_email', 'unknown')
            techcard_id = body.get('techcard_id', 'temp')
            
            tracking_service = get_export_tracking_service()
            tracking_service.record_export(
                organization_id=organization_id,
                techcard_id=techcard_id,
                techcard_title=techcard_data.get('meta', {}).get('title', 'Untitled') if techcard_data else 'Unknown',
                user_email=user_email,
                export_type="iiko_xlsx_enhanced",
                result="failed",
                error_message=str(e)
            )
        except:
            pass  # Don't let tracking errors break the main error response
            
        raise HTTPException(500, f"Enhanced export failed: {str(e)}")


@router.get("/techcards.v2/export/last")
async def get_last_export(organization_id: str = "default", techcard_id: Optional[str] = None):
    """
    Export Wizard v1: Get last export information
    """
    try:
        from ..integrations.export_tracking_service import get_export_tracking_service
        tracking_service = get_export_tracking_service()
        
        last_export = tracking_service.get_last_export(organization_id, techcard_id)
        
        return {
            "status": "success",
            "last_export": last_export
        }
        
    except Exception as e:
        logger.error(f"Get last export error: {e}")
        raise HTTPException(500, f"Get last export failed: {str(e)}")


@router.get("/techcards.v2/export/history")
async def get_export_history(organization_id: str = "default", limit: int = 10):
    """
    Export Wizard v1: Get export history
    """
    try:
        from ..integrations.export_tracking_service import get_export_tracking_service
        tracking_service = get_export_tracking_service()
        
        history = tracking_service.get_export_history(organization_id, limit)
        stats = tracking_service.export_stats(organization_id, days_back=7)
        
        return {
            "status": "success",
            "history": history,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Get export history error: {e}")
        raise HTTPException(500, f"Get export history failed: {str(e)}")


# ======================================
# Feature B: Dish Code Resolver & Skeletons
# ======================================

@router.post("/techcards.v2/dish-codes/find")
async def find_dish_codes(request: dict):
    """
    Feature B: Найти коды блюд в iiko RMS по названиям
    
    Body:
    {
        "dish_names": ["Салат Цезарь", "Стейк с овощами"],
        "organization_id": "default"
    }
    
    Returns:
    {
        "results": [
            {
                "dish_name": "Салат Цезарь", 
                "status": "found|not_found|error",
                "dish_code": "12345",
                "confidence": 0.9
            }
        ]
    }
    """
    try:
        dish_names = request.get('dish_names', [])
        organization_id = request.get('organization_id', 'default')
        
        if not dish_names:
            raise HTTPException(400, "dish_names required")
        
        # Получаем RMS сервис
        from ..integrations.iiko_rms_service import get_iiko_rms_service
        rms_service = get_iiko_rms_service()
        
        results = []
        for dish_name in dish_names:
            search_result = find_dish_in_iiko_rms(dish_name, rms_service)
            results.append({
                "dish_name": dish_name,
                **search_result
            })
        
        return {
            "status": "success",
            "results": results
        }
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Find dish codes error: {e}")
        raise HTTPException(500, f"Find dish codes failed: {str(e)}")


@router.post("/techcards.v2/dish-codes/generate")
async def generate_dish_codes_api(request: dict):
    """
    Feature B: Сгенерировать свободные коды для новых блюд
    
    Body:
    {
        "dish_names": ["Новое блюдо 1", "Новое блюдо 2"],
        "organization_id": "default",
        "width": 5
    }
    
    Returns:
    {
        "generated_codes": {
            "Новое блюдо 1": "10001",
            "Новое блюдо 2": "10002"
        }
    }
    """
    try:
        dish_names = request.get('dish_names', [])
        organization_id = request.get('organization_id', 'default')
        width = request.get('width', 5)
        
        if not dish_names:
            raise HTTPException(400, "dish_names required")
        
        # Получаем RMS сервис
        from ..integrations.iiko_rms_service import get_iiko_rms_service
        rms_service = get_iiko_rms_service()
        
        generated_codes = generate_dish_codes(dish_names, rms_service, width)
        
        return {
            "status": "success",
            "generated_codes": generated_codes
        }
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Generate dish codes error: {e}")
        raise HTTPException(500, f"Generate dish codes failed: {str(e)}")


@router.post("/techcards.v2/export/enhanced-dual/iiko.xlsx")
async def export_enhanced_dual_iiko_xlsx(request: dict):
    """
    Feature A & B: Enhanced export with product codes and dish skeletons
    
    Body:
    {
        "techcards": [TechCardV2, ...],
        "export_options": {
            "use_product_codes": true,
            "dish_codes_mapping": {"Салат Цезарь": "12345"}
        },
        "organization_id": "default",
        "user_email": "user@example.com"
    }
    
    Returns: ZIP file with 2 XLSX files:
    - Dish-Skeletons.xlsx
    - iiko_TTK.xlsx
    """
    try:
        techcards_data = request.get('techcards', [])
        export_options = request.get('export_options', {})
        organization_id = request.get('organization_id', 'default')
        user_email = request.get('user_email', 'system')
        
        if not techcards_data:
            raise HTTPException(400, "techcards required")
        
        # Валидируем техкарты
        cards = []
        for card_data in techcards_data:
            try:
                # Добавляем отсутствующие обязательные поля
                if 'nutrition' not in card_data:
                    card_data['nutrition'] = {'per100g': {}, 'perPortion': {}}
                if 'cost' not in card_data:
                    card_data['cost'] = {'per100g': {}, 'perPortion': {}}
                if 'process' not in card_data:
                    card_data['process'] = {'steps': []}
                    
                card = TechCardV2.model_validate(card_data)
                cards.append(card)
            except Exception as e:
                logger.warning(f"Invalid techcard skipped for enhanced dual export: {e}")
                # Skip invalid cards for enhanced dual export
                continue
        
        if not cards:
            raise HTTPException(400, "No valid techcards provided")
        
        # Получаем RMS сервис для кодов продуктов
        from ..integrations.iiko_rms_service import get_iiko_rms_service
        rms_service = get_iiko_rms_service()
        export_options['rms_service'] = rms_service
        
        # Создаем файлы
        files_data = {}
        
        # 1. Dish-Skeletons.xlsx
        dish_codes_mapping = export_options.get('dish_codes_mapping', {})
        if dish_codes_mapping:
            skeletons_buffer = create_dish_skeletons_xlsx(dish_codes_mapping, cards)
            files_data['Dish-Skeletons.xlsx'] = skeletons_buffer.getvalue()
        
        # 2. iiko TTK.xlsx (основной файл)
        main_files_data = []
        all_issues = []
        
        for card in cards:
            excel_buffer, issues = create_iiko_ttk_xlsx(card, export_options, rms_service)
            main_files_data.append(excel_buffer.getvalue())
            all_issues.extend(issues)
        
        # Объединяем все техкарты в один файл или создаем отдельные
        if len(main_files_data) == 1:
            files_data['iiko_TTK.xlsx'] = main_files_data[0]
        else:
            for i, file_data in enumerate(main_files_data):
                files_data[f'iiko_TTK_{i+1}.xlsx'] = file_data
        
        # Создаем ZIP архив
        from receptor_agent.exports.zipper import make_zip
        zip_buffer = make_zip(files_data)
        
        # Трекинг экспорта
        try:
            from ..integrations.export_tracking_service import get_export_tracking_service
            tracking_service = get_export_tracking_service()
            
            for card in cards:
                tracking_service.track_export(
                    techcard_id=card.meta.id,
                    organization_id=organization_id,
                    user_email=user_email,
                    export_type="iiko_xlsx_enhanced_dual",
                    issues=all_issues
                )
        except Exception as e:
            logger.warning(f"Export tracking failed: {e}")
        
        return StreamingResponse(
            io.BytesIO(zip_buffer),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=iiko_export_enhanced.zip"}
        )
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Enhanced dual export error: {e}")
        raise HTTPException(500, f"Enhanced dual export failed: {str(e)}")


@router.post("/techcards.v2/export/preflight-check")
async def export_preflight_check(request: dict):
    """
    Feature 3: Pre-flight warnings перед экспортом
    
    Body:
    {
        "techcards": [TechCardV2, ...],
        "export_options": {
            "use_product_codes": true,
            "dish_codes_mapping": {"Салат Цезарь": "12345"}
        },
        "organization_id": "default"
    }
    
    Returns:
    {
        "status": "ready|warnings",
        "warnings": [
            {
                "type": "missing_dish_codes|missing_product_codes",
                "items": ["Блюдо без кода", ...],
                "action": "Создать коды|Проверить маппинг"
            }
        ]
    }
    """
    try:
        techcards_data = request.get('techcards', [])
        export_options = request.get('export_options', {})
        organization_id = request.get('organization_id', 'default')
        
        if not techcards_data:
            raise HTTPException(400, "techcards required")
        
        # Валидируем техкарты
        cards = []
        for card_data in techcards_data:
            try:
                # Добавляем отсутствующие обязательные поля
                if 'nutrition' not in card_data:
                    card_data['nutrition'] = {'per100g': {}, 'perPortion': {}}
                if 'cost' not in card_data:
                    card_data['cost'] = {'per100g': {}, 'perPortion': {}}
                if 'process' not in card_data:
                    card_data['process'] = {'steps': []}
                    
                card = TechCardV2.model_validate(card_data)
                cards.append(card)
            except Exception as e:
                logger.warning(f"Invalid techcard skipped: {e}")
                # Продолжаем с частичной валидацией для preflight
                cards.append(type('MockCard', (), {
                    'meta': type('MockMeta', (), card_data.get('meta', {}))(),
                    'ingredients': card_data.get('ingredients', [])
                })())
        
        warnings = []
        
        # Проверка кодов блюд
        dish_codes_mapping = export_options.get('dish_codes_mapping', {})
        dishes_without_codes = []
        
        for card in cards:
            # Поддерживаем как объекты TechCardV2, так и mock объекты
            if hasattr(card, 'meta') and hasattr(card.meta, 'title'):
                dish_name = card.meta.title
            elif hasattr(card, 'meta') and isinstance(card.meta, dict):
                dish_name = card.meta.get('title', 'Unknown Dish')
            else:
                dish_name = 'Unknown Dish'
                
            if not dish_codes_mapping.get(dish_name):
                dishes_without_codes.append(dish_name)
        
        if dishes_without_codes:
            warnings.append({
                "type": "missing_dish_codes",
                "title": "Блюда без кода iiko",
                "items": dishes_without_codes,
                "action": "Найти в iiko или создать коды",
                "severity": "warning"
            })
        
        # Проверка кодов продуктов (если включен флаг use_product_codes)
        use_product_codes = export_options.get('use_product_codes', True)
        if use_product_codes:
            from ..integrations.iiko_rms_service import get_iiko_rms_service
            rms_service = get_iiko_rms_service()
            
            products_without_codes = []
            
            # Проверяем наличие кода продукта
            for card in cards:
                ingredients = getattr(card, 'ingredients', [])
                if not ingredients:
                    continue
                    
                for ingredient in ingredients:
                    # Поддерживаем как объекты, так и dict
                    if hasattr(ingredient, 'skuId'):
                        sku_id = ingredient.skuId
                        ingredient_name = ingredient.name
                    elif isinstance(ingredient, dict):
                        sku_id = ingredient.get('skuId')
                        ingredient_name = ingredient.get('name', 'Unknown')
                    else:
                        continue
                    
                    if sku_id:
                        # Проверяем наличие кода продукта
                        product = rms_service.products.find_one({"_id": sku_id})
                        if not product or not product.get('article'):
                            # Проверяем в prices
                            pricing = rms_service.prices.find_one({"skuId": sku_id})
                            if not pricing or not pricing.get('article'):
                                products_without_codes.append(ingredient_name)
            
            if products_without_codes:
                warnings.append({
                    "type": "missing_product_codes", 
                    "title": "Ингредиенты без кода товара",
                    "items": list(set(products_without_codes)),  # Убираем дубликаты
                    "action": "Проверить маппинг или каталог iiko",
                    "severity": "warning"
                })
        
        status = "warnings" if warnings else "ready"
        
        return {
            "status": status,
            "warnings": warnings,
            "cards_checked": len(cards),
            "export_ready": status == "ready"
        }
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Preflight check error: {e}")
        raise HTTPException(500, f"Preflight check failed: {str(e)}")


@router.post("/techcards.v2/product-codes/find-missing")
async def find_missing_product_codes(request: dict):
    """
    C. Product Skeletons: Найти ингредиенты без кода продукта
    
    Body:
    {
        "techcards": [TechCardV2, ...],
        "organization_id": "default"
    }
    
    Returns:
    {
        "status": "success",
        "missing_products": [
            {
                "name": "Куриное филе",
                "unit": "g",
                "skuId": "guid-123",
                "product_code": null
            }
        ],
        "total_missing": 5
    }
    """
    try:
        techcards_data = request.get('techcards', [])
        organization_id = request.get('organization_id', 'default')
        
        # Валидируем техкарты
        cards = []
        for card_data in techcards_data:
            try:
                card = TechCardV2.model_validate(card_data)
                cards.append(card)
            except Exception as e:
                logger.warning(f"Invalid techcard skipped: {e}")
        
        # Получаем RMS сервис
        from ..integrations.iiko_rms_service import get_iiko_rms_service
        rms_service = get_iiko_rms_service()
        
        # Находим ингредиенты без маппинга
        from ..exports.iiko_xlsx import find_missing_product_mappings
        missing_products = find_missing_product_mappings(cards, rms_service)
        
        return {
            "status": "success",
            "missing_products": missing_products,
            "total_missing": len(missing_products),
            "cards_analyzed": len(cards)
        }
        
    except Exception as e:
        logger.error(f"Find missing product codes error: {e}")
        raise HTTPException(500, f"Find missing product codes failed: {str(e)}")


@router.post("/techcards.v2/product-codes/generate")
async def generate_product_codes_api(request: dict):
    """
    C. Product Skeletons: Сгенерировать коды продуктов для ингредиентов
    
    Body:
    {
        "ingredient_names": ["Куриное филе", "Соль", "Перец"],
        "start_code": 10000,
        "code_width": 5,
        "organization_id": "default"
    }
    
    Returns:
    {
        "status": "success", 
        "generated_codes": {
            "Куриное филе": "10001",
            "Соль": "10002",
            "Перец": "10003"
        },
        "codes_generated": 3
    }
    """
    try:
        ingredient_names = request.get('ingredient_names', [])
        start_code = request.get('start_code', 10000)
        code_width = request.get('code_width', 5)
        organization_id = request.get('organization_id', 'default')
        
        if not ingredient_names:
            raise HTTPException(400, "ingredient_names list is required")
        
        # Получаем RMS сервис
        from ..integrations.iiko_rms_service import get_iiko_rms_service
        rms_service = get_iiko_rms_service()
        
        # Генерируем коды
        from ..exports.iiko_xlsx import generate_product_codes
        generated_codes = generate_product_codes(
            ingredient_names=ingredient_names,
            rms_service=rms_service,
            start_code=start_code,
            code_width=code_width
        )
        
        return {
            "status": "success",
            "generated_codes": generated_codes,
            "codes_generated": len(generated_codes),
            "start_code": start_code,
            "code_width": code_width
        }
        
    except Exception as e:
        logger.error(f"Generate product codes error: {e}")
        raise HTTPException(500, f"Generate product codes failed: {str(e)}")


@router.post("/techcards.v2/product-skeletons/export")
async def export_product_skeletons(request: dict):
    """
    C. Product Skeletons: Экспорт Product-Skeletons.xlsx для импорта в iiko
    
    Body:
    {
        "missing_ingredients": [
            {
                "name": "Куриное филе",
                "unit": "g"
            }
        ],
        "generated_codes": {
            "Куриное филе": "10001"
        }
    }
    
    Returns:
        XLSX файл Product-Skeletons.xlsx
    """
    try:
        missing_ingredients = request.get('missing_ingredients', [])
        generated_codes = request.get('generated_codes', {})
        
        if not missing_ingredients:
            raise HTTPException(400, "missing_ingredients list is required")
        
        # Создаем Product-Skeletons.xlsx
        from ..exports.iiko_xlsx import create_product_skeletons_xlsx
        excel_buffer = create_product_skeletons_xlsx(missing_ingredients, generated_codes)
        
        return StreamingResponse(
            iter([excel_buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="Product-Skeletons.xlsx"'}
        )
        
    except Exception as e:
        logger.error(f"Export product skeletons error: {e}")
        raise HTTPException(500, f"Export product skeletons failed: {str(e)}")


@router.post("/techcards.v2/debug/rms-product")
async def debug_rms_product(request: dict):
    """
    DEBUG: Проверить какие поля есть у продукта в iiko RMS
    
    Body:
    {
        "sku_id": "product-guid-from-iiko"
    }
    """
    try:
        sku_id = request.get('sku_id')
        if not sku_id:
            raise HTTPException(400, "sku_id is required")
        
        # Получаем RMS сервис
        from ..integrations.iiko_rms_service import get_iiko_rms_service
        rms_service = get_iiko_rms_service()
        
        result = {
            "sku_id": sku_id,
            "product_in_products": None,
            "product_in_prices": None,
            "extracted_article": None
        }
        
        # Поиск в коллекции products
        product = rms_service.products.find_one({"_id": sku_id})
        if product:
            result["product_in_products"] = {
                "found": True,
                "fields": list(product.keys()),
                "data": product
            }
        
        # Поиск в коллекции prices
        pricing = rms_service.prices.find_one({"skuId": sku_id})
        if pricing:
            result["product_in_prices"] = {
                "found": True,
                "fields": list(pricing.keys()),
                "data": pricing
            }
        
        # Пробуем извлечь артикул нашей функцией
        from ..exports.iiko_xlsx import get_product_code_from_rms
        extracted_article = get_product_code_from_rms(sku_id, rms_service)
        result["extracted_article"] = extracted_article
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Debug RMS product error: {e}")
        raise HTTPException(500, f"Debug failed: {str(e)}")


@router.post("/techcards.v2/export/auto-fix")
async def auto_fix_export_issues(request: Request):
    """
    Export Wizard v1: Auto-fix blocking export issues
    """
    try:
        body = await request.json()
        techcard_data = body.get('techcard')
        
        if not techcard_data:
            raise HTTPException(400, "techcard data required")
        
        # Apply quality validator with normalization
        from ..techcards_v2.quality_validator import QualityValidator
        validator = QualityValidator()
        
        normalized_card, validation_issues = validator.validate_techcard(techcard_data)
        
        # Count auto-fixes applied
        auto_fixes = len([i for i in validation_issues if i.get('type') == 'rangeNormalized'])
        
        # Re-validate after normalization
        _, post_fix_issues = validator.validate_techcard(normalized_card)
        remaining_errors = [i for i in post_fix_issues if i.get('level') == 'error']
        
        return {
            "status": "success",
            "fixed_techcard": normalized_card,
            "auto_fixes_applied": auto_fixes,
            "remaining_errors": remaining_errors,
            "is_export_ready": len(remaining_errors) == 0,
            "message": f"Применено {auto_fixes} автоисправлений. " + 
                      (f"Осталось {len(remaining_errors)} ошибок." if remaining_errors else "Готов к экспорту!")
        }
        
    except Exception as e:
        logger.error(f"Auto-fix export issues error: {e}")
        raise HTTPException(500, f"Auto-fix failed: {str(e)}")


@router.get("/techcards.v2/export/instructions")
async def get_export_instructions():
    """
    Export Wizard v1: Get iikoWeb import instructions
    """
    instructions = {
        "title": "Как импортировать в iikoWeb",
        "steps": [
            {
                "number": 1,
                "title": "Открыть iikoWeb",
                "description": "Войдите в административную панель iikoWeb под учетной записью с правами администратора",
                "details": "Убедитесь что у вас есть права на управление номенклатурой и техническими картами"
            },
            {
                "number": 2, 
                "title": "Перейти в раздел импорта ТТК",
                "description": "Найдите раздел 'Номенклатура' → 'Технические карты' → 'Импорт'",
                "details": "Обычно находится в главном меню под разделом управления номенклатурой"
            },
            {
                "number": 3,
                "title": "Загрузить файл и проверить протокол",
                "description": "Выберите скачанный XLSX файл, нажмите 'Импорт' и дождитесь обработки",
                "details": "После импорта обязательно проверьте протокол на наличие ошибок или предупреждений"
            }
        ],
        "tips": [
            "Файл должен быть в формате .xlsx (Excel)",
            "Не изменяйте структуру файла после экспорта", 
            "Проверьте что все SKU артикулы существуют в iiko",
            "При ошибках импорта обратитесь к протоколу импорта iikoWeb"
        ],
        "copyable_text": """Инструкция по импорту ТТК в iikoWeb:

1. Открыть iikoWeb
   Войдите в административную панель iikoWeb под учетной записью с правами администратора

2. Перейти в раздел импорта ТТК  
   Найдите раздел 'Номенклатура' → 'Технические карты' → 'Импорт'

3. Загрузить файл и проверить протокол
   Выберите скачанный XLSX файл, нажмите 'Импорт' и дождитесь обработки

Важно:
• Файл должен быть в формате .xlsx (Excel)
• Не изменяйте структуру файла после экспорта
• Проверьте что все SKU артикулы существуют в iiko
• При ошибках импорта обратитесь к протоколу импорта iikoWeb"""
    }
    
    return {
        "status": "success",
        "instructions": instructions
    }


# =============================================================================
# AA-01: ArticleAllocator API Endpoints
# =============================================================================

@router.post("/techcards.v2/articles/allocate")
async def allocate_articles_api(request: Request):
    """
    AA-01: Allocate unique article numbers with reservation
    
    Body:
    {
        "article_type": "dish" | "product", 
        "count": 5,
        "organization_id": "org-123",
        "entity_ids": ["dish-1", "dish-2", ...],  // Optional, for idempotency
        "entity_names": ["Борщ", "Солянка", ...], // Optional, for display
        "user_id": "user-456"                     // Optional, default "anonymous"
    }
    
    Returns:
    {
        "status": "success",
        "allocated_articles": ["10001", "10002", "10003", "10004", "10005"],
        "article_width": 5,
        "reservations": [
            {
                "article": "10001",
                "entity_id": "dish-1", 
                "entity_name": "Борщ",
                "status": "reserved",
                "expires_at": "2024-01-15T10:00:00Z"
            }
        ]
    }
    """
    try:
        body = await request.json()
        
        # Validate required fields
        article_type = body.get('article_type')
        if article_type not in ['dish', 'product']:
            raise HTTPException(400, "article_type must be 'dish' or 'product'")
        
        count = body.get('count', 1)
        if count <= 0 or count > 100:
            raise HTTPException(400, "count must be between 1 and 100")
        
        organization_id = body.get('organization_id', 'default')
        entity_ids = body.get('entity_ids')
        entity_names = body.get('entity_names')
        user_id = body.get('user_id', 'anonymous')
        
        # Validate entity arrays length if provided
        if entity_ids and len(entity_ids) != count:
            raise HTTPException(400, "entity_ids length must match count")
        if entity_names and len(entity_names) != count:
            raise HTTPException(400, "entity_names length must match count")
        
        # Get ArticleAllocator service
        from ..integrations.article_allocator import get_article_allocator, ArticleType
        allocator = get_article_allocator()
        
        # Convert string to enum
        article_type_enum = ArticleType.DISH if article_type == 'dish' else ArticleType.PRODUCT
        
        # Allocate articles
        allocated_articles = allocator.allocate_articles(
            article_type=article_type_enum,
            count=count,
            organization_id=organization_id,
            entity_ids=entity_ids,
            entity_names=entity_names,
            user_id=user_id
        )
        
        # Get width for response
        article_width = allocator.get_article_width(organization_id)
        
        # Build reservation details for response
        reservations = []
        for i, article in enumerate(allocated_articles):
            entity_id = entity_ids[i] if entity_ids else f"temp_{article_type}_{i}"
            entity_name = entity_names[i] if entity_names else f"Temporary {article_type} {i+1}"
            
            reservations.append({
                "article": article,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "status": "reserved",
                "expires_at": (datetime.utcnow() + timedelta(hours=48)).isoformat() + "Z"
            })
        
        return {
            "status": "success",
            "allocated_articles": allocated_articles,
            "article_width": article_width,
            "reservations": reservations,
            "total_allocated": len(allocated_articles),
            "organization_id": organization_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Article allocation error: {e}")
        raise HTTPException(500, f"Article allocation failed: {str(e)}")


@router.post("/techcards.v2/articles/claim")
async def claim_articles_api(request: Request):
    """
    AA-01: Claim reserved articles (make them permanent for skeleton export)
    
    Body:
    {
        "articles": ["10001", "10002", "10003"],
        "organization_id": "org-123"
    }
    
    Returns:
    {
        "status": "success",
        "claim_results": {
            "10001": true,
            "10002": true, 
            "10003": false
        },
        "claimed_count": 2,
        "failed_count": 1
    }
    """
    try:
        body = await request.json()
        
        articles = body.get('articles', [])
        if not articles:
            raise HTTPException(400, "articles list is required")
        
        if len(articles) > 100:
            raise HTTPException(400, "cannot claim more than 100 articles at once")
        
        organization_id = body.get('organization_id', 'default')
        
        # Get ArticleAllocator service
        from ..integrations.article_allocator import get_article_allocator
        allocator = get_article_allocator()
        
        # Claim articles
        claim_results = allocator.claim_articles(articles, organization_id)
        
        # Count successes and failures
        claimed_count = sum(1 for success in claim_results.values() if success)
        failed_count = len(articles) - claimed_count
        
        return {
            "status": "success",
            "claim_results": claim_results,
            "claimed_count": claimed_count,
            "failed_count": failed_count,
            "organization_id": organization_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Article claim error: {e}")
        raise HTTPException(500, f"Article claim failed: {str(e)}")


@router.post("/techcards.v2/articles/release")
async def release_articles_api(request: Request):
    """
    AA-01: Release reserved articles by entity_id (cancel reservation)
    
    Body:
    {
        "entity_ids": ["dish-1", "dish-2", "temp_product_0"],
        "organization_id": "org-123",
        "reason": "export_cancelled"  // Optional
    }
    
    Returns:
    {
        "status": "success",
        "release_results": {
            "dish-1": true,
            "dish-2": true,
            "temp_product_0": false
        },
        "released_count": 2,
        "failed_count": 1
    }
    """
    try:
        body = await request.json()
        
        entity_ids = body.get('entity_ids', [])
        if not entity_ids:
            raise HTTPException(400, "entity_ids list is required")
        
        if len(entity_ids) > 100:
            raise HTTPException(400, "cannot release more than 100 entities at once")
        
        organization_id = body.get('organization_id', 'default')
        reason = body.get('reason', 'manual_release')
        
        # Get ArticleAllocator service
        from ..integrations.article_allocator import get_article_allocator
        allocator = get_article_allocator()
        
        # Release articles
        release_results = allocator.release_articles(entity_ids, organization_id, reason)
        
        # Count successes and failures
        released_count = sum(1 for success in release_results.values() if success)
        failed_count = len(entity_ids) - released_count
        
        return {
            "status": "success",
            "release_results": release_results,
            "released_count": released_count,
            "failed_count": failed_count,
            "organization_id": organization_id,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Article release error: {e}")
        raise HTTPException(500, f"Article release failed: {str(e)}")


@router.get("/techcards.v2/articles/stats/{organization_id}")
async def get_article_stats(organization_id: str):
    """
    AA-01: Get article allocation statistics for organization
    
    Returns:
    {
        "status": "success",
        "organization_id": "org-123",
        "article_width": 5,
        "stats": {
            "total": 15,
            "by_status": {
                "reserved": 8,
                "claimed": 5,
                "released": 2
            }
        }
    }
    """
    try:
        # Get ArticleAllocator service
        from ..integrations.article_allocator import get_article_allocator
        allocator = get_article_allocator()
        
        # Get statistics
        stats = allocator.get_allocation_stats(organization_id)
        
        return {
            "status": "success",
            "organization_id": organization_id,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Article stats error: {e}")
        raise HTTPException(500, f"Article stats failed: {str(e)}")


@router.get("/techcards.v2/articles/width/{organization_id}")
async def get_article_width(organization_id: str):
    """
    AA-01: Get article width for organization (with caching)
    
    Returns:
    {
        "status": "success",
        "organization_id": "org-123", 
        "article_width": 5,
        "strategy": "org_max_or_default",
        "cached": true
    }
    """
    try:
        # Get ArticleAllocator service
        from ..integrations.article_allocator import get_article_allocator
        allocator = get_article_allocator()
        
        # Get width (utilizes caching internally)
        width = allocator.get_article_width(organization_id)
        
        # Check if it's cached
        cached_entry = allocator.width_cache.find_one({
            "organization_id": organization_id,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        return {
            "status": "success",
            "organization_id": organization_id,
            "article_width": width,
            "strategy": allocator.config["width_strategy"],
            "cached": cached_entry is not None,
            "config": {
                "default_width": allocator.config["default_width"],
                "min_width": allocator.config["min_width"], 
                "max_width": allocator.config["max_width"],
                "cache_ttl_hours": allocator.config["width_cache_ttl_hours"]
            }
        }
        
    except Exception as e:
        logger.error(f"Article width error: {e}")
        raise HTTPException(500, f"Article width failed: {str(e)}")