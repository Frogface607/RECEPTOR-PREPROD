from __future__ import annotations
import io
import json
import os
import traceback
import logging
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
    source: str = Query("all", description="Data source: usda, price, nutrition, iiko, rms, all")
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
                        "asOf": item.get("asOf")
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
                
                # Get RMS connection status
                connection_status = rms_service.get_rms_connection_status()
                if connection_status.get("status") == "connected" and connection_status.get("organization_id"):
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
                        
            except Exception as e:
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
                "connection_status": connection_status.get("status") if connection_status else "not_connected"
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
        
        # Step 2: Export XLSX
        from ..exports.iiko_xlsx import create_iiko_ttk_xlsx
        excel_buffer, export_issues = create_iiko_ttk_xlsx(normalized_card)
        
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