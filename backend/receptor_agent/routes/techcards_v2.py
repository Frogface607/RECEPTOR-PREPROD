from __future__ import annotations
import io
import json
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
    source: str = Query("all", description="Data source: usda, price, nutrition, iiko, all")
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
                    "source": "usda|catalog|bootstrap|price"
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
        
        # Объединяем результаты с приоритетом: Price → USDA → остальные
        all_results = price_results + usda_results + catalog_results
        
        # Сортируем по релевантности: Price → USDA → точные совпадения → остальные
        def sort_key(x):
            source_priority = {
                "user": 0, "catalog": 1, "bootstrap": 2,  # Price sources 
                "usda": 3,                                  # USDA
                "catalog": 4                               # Other catalog
            }.get(x.get("source", "unknown"), 5)
            name_match = 0 if query in x["name"].lower() else 1
            return (source_priority, name_match, -len(x["name"]), x["name"].lower())
        
        sorted_items = sorted(all_results, key=sort_key)[:limit]
        
        return JSONResponse(content={
            "status": "success", 
            "items": sorted_items,
            "total_found": len(all_results),
            "price_count": len(price_results),
            "usda_count": len(usda_results),
            "catalog_count": len(catalog_results)
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