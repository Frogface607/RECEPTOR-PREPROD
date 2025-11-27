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
    # Принудительно включаем V2 для локальной разработки
    return True

def _llm_enabled() -> bool:
    return os.getenv("TECHCARDS_V2_USE_LLM","false").lower() in ("1","true","yes","on") and bool(os.getenv("OPENAI_API_KEY"))

@router.get("/techcards.v2/status")
def status_tc_v2():
    return {
        "feature_enabled": _flag(),
        "llm_enabled": _llm_enabled(),
        "model": os.getenv("TECHCARDS_V2_MODEL","gpt-5-mini") if _llm_enabled() else None
    }

@router.get("/techcards.v2/test")
def test_endpoint():
    """Test endpoint to verify router is working"""
    return {"message": "TechCards V2 router is working!", "timestamp": datetime.now().isoformat()}

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
            import os
            os.environ["TECHCARDS_V2_USE_LLM"] = "true" if use_llm else "false"
        
        # Run pipeline
        res = run_pipeline(profile)
        
        # Save tech card to database if generation was successful
        if res.status in ["success", "draft", "READY"] and res.card:
            try:
                # Connect to MongoDB and save the tech card
                import os
                from pymongo import MongoClient
                import uuid
                
                mongo_url = os.getenv('MONGODB_URI') or os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
                db_name = os.getenv('DB_NAME', 'receptor_pro')
                
                client = MongoClient(mongo_url)
                db = client[db_name.strip('"')]
                techcards_collection = db.techcards_v2
                
                # Generate ID if not present
                if not hasattr(res.card.meta, 'id') or not res.card.meta.id:
                    # Generate UUID for the tech card
                    tech_card_id = str(uuid.uuid4())
                    # Update meta with ID
                    meta_dict = res.card.meta.model_dump()
                    meta_dict['id'] = tech_card_id
                    
                    # Recreate the card with the ID
                    from ..techcards_v2.schemas import MetaV2
                    new_meta = MetaV2.model_validate(meta_dict)
                    card_data = res.card.model_dump()
                    card_data['meta'] = new_meta.model_dump()
                    from ..techcards_v2.schemas import TechCardV2
                    res.card = TechCardV2.model_validate(card_data)
                else:
                    tech_card_id = res.card.meta.id
                
                # CLEANUP TECH CARD DATA & UI: Сохранение с user_id для связи с аккаунтом
                # Prepare document for user_history (совместимость с существующей системой)
                card_doc = {
                    "id": tech_card_id,
                    "user_id": profile.user_id or 'anonymous',
                    "dish_name": profile.name,
                    "content": res.card.model_dump_json(),  # Сохраняем как JSON строку для совместимости
                    "created_at": datetime.utcnow().isoformat(),
                    "is_menu": False,
                    "status": res.status,
                    "techcard_v2_data": res.card.model_dump()  # Полные данные V2
                }
                
                # Save to user_history collection (совместимость с существующим UI)
                db = client[db_name]
                user_history_collection = db.user_history
                user_history_collection.insert_one(card_doc)
                client.close()
                
                logger.info(f"Tech card saved to database with ID: {tech_card_id}")
                
            except Exception as save_error:
                logger.error(f"Failed to save tech card to database: {save_error}")
                # Continue without failing the response
        
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
        elif res.status == "READY":
            # CLEANUP TECH CARD DATA & UI: Все техкарты теперь READY
            response_data = {
                "status": "READY",
                "card": res.card.model_dump(by_alias=True, mode="json") if res.card else None,
                "issues": res.issues or [],
                "message": "Tech card generated and ready for production"
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
        import os
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
    """Экспорт техкарты в формат iiko XLSX (ТТК по шаблону iikoWeb) с добавлением DISH артикула + ALT Cleanup"""
    if not _flag():
        raise HTTPException(404, "feature disabled")
    
    try:
        from ..exports.iiko_xlsx import create_iiko_ttk_xlsx
        from ..exports.alt_export_cleanup import get_alt_export_validator
        
        # Создаем preflight для получения DISH артикула
        preflight_result = None
        try:
            # Импортируем PreflightOrchestrator для генерации артикулов
            from ..routes.export_v2 import PreflightOrchestrator
            import asyncio
            
            # Запускаем preflight для получения артикулов блюда
            async def get_dish_article():
                preflight_orchestrator = PreflightOrchestrator()
                return await preflight_orchestrator.run_preflight([card.meta.id], "default")
            
            # Выполняем асинхронную операцию в синхронном контексте
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                preflight_result = loop.run_until_complete(get_dish_article())
            finally:
                loop.close()
                
        except Exception as e:
            print(f"Preflight for ALT export failed: {e}")
            # Продолжаем без preflight (как было раньше)
        
        # Создаем export_options с preflight данными для получения DISH артикула
        export_options = {
            "use_product_codes": True
        }
        
        if preflight_result:
            export_options["preflight_result"] = preflight_result
            print(f"ALT export: Added preflight result with dish articles")
        
        # Генерируем XLSX файл для импорта ТТК с DISH артикулом
        xlsx_buffer, issues = create_iiko_ttk_xlsx(card, export_options)
        
        # ALT Export Cleanup: Валидация единичного TTK файла
        validator = get_alt_export_validator()
        xlsx_content = xlsx_buffer.getvalue()
        
        validation_result = validator.validate_single_ttk(
            xlsx_content, 
            filename=f"iiko_ttk_{card.meta.title}.xlsx"
        )
        
        if not validation_result["valid"]:
            print(f"ALT Export Warning: TTK validation issues - {validation_result['issues']}")
            # Логируем проблемы, но не блокируем экспорт (может быть legacy данные)
        else:
            print(f"ALT Export: TTK validation passed - {validation_result['metadata']}")
        
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
    search_by: Optional[str] = Query("name", description="Search type: name, article, id"),  # FIX-A: Add search_by parameter
    user_id: Optional[str] = Query(None, description="User ID for RMS connection isolation")  # CRITICAL FIX: Add user_id parameter
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
        organization_id = orgId or "default"  # Initialize organization_id at function level
        
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
        
        # iiko search results (if needed) - SECURITY: Only for authenticated users
        iiko_results = []
        if source in ("iiko", "all") and user_id and user_id != 'demo_user':
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
                
                # Get RMS connection status to verify connectivity (CRITICAL FIX: Pass user_id)
                connection_status = rms_service.get_rms_connection_status(user_id=user_id)
                if connection_status.get("status") == "connected":
                    # Override orgId with actual connected organization if available
                    if connection_status.get("organization_id"):
                        organization_id = connection_status["organization_id"]
                    
                    # FIX-A: Enhanced search based on search_by parameter
                    if search_by == "article":
                        # SRCH-02: Exact search by article
                        rms_products = rms_service.search_rms_products_by_article(organization_id, q, limit)
                    elif search_by == "id":
                        # MAP-01: Search by ID for article lookup
                        rms_products = rms_service.search_rms_products_by_id(organization_id, q, limit)
                    else:
                        # Default: Enhanced name search
                        rms_products = rms_service.search_rms_products_enhanced(organization_id, q, limit)
                    
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
        last_sync = None
        connection_status_for_badge = None
        
        # Get connection status for badge (if we have RMS results)
        if source in ("rms", "iiko", "all"):
            try:
                from ..integrations.iiko_rms_service import get_iiko_rms_service
                rms_service = get_iiko_rms_service()
                connection_status_for_badge = rms_service.get_rms_connection_status(user_id=user_id)
                last_sync = connection_status_for_badge.get("last_connection") if connection_status_for_badge else None
            except Exception as e:
                logger.error(f"Error getting connection status for badge: {e}")
                last_sync = None
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
                "connection_status": connection_status_for_badge.get("status") if connection_status_for_badge else "not_connected",
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
        
        # ПЕРЕСЧИТЫВАЕМ ВЫХОД (YIELD) на основе суммы netto_g
        if updated_card.ingredients:
            total_net_weight = sum(float(ing.netto_g or 0) for ing in updated_card.ingredients)
            portions = updated_card.portions or 1
            
            if portions > 0:
                # Обновляем yield
                if hasattr(updated_card, 'yield_') and updated_card.yield_:
                    updated_card.yield_.perPortion_g = round(total_net_weight / portions, 1)
                    updated_card.yield_.perBatch_g = round(total_net_weight, 1)
        
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

@router.post("/techcards.v2/save")
async def save_techcard_v2_to_history(request: Request):
    """
    Сохраняет TechCardV2 в user_history коллекцию MongoDB.
    
    Expects:
        {
            "techcard_id": str,
            "techcard": TechCardV2
        }
    
    Returns:
        {"status": "success" | "error", "message": str}
    """
    try:
        body = await request.json()
        techcard_data = body.get('techcard')
        techcard_id = body.get('techcard_id')
        
        logger.info(f"💾 Saving techcard: id={techcard_id}")
        
        if not techcard_data or not techcard_id:
            raise HTTPException(400, "Missing techcard or techcard_id")
        
        # Получаем MongoDB клиент из окружения (как в server.py)
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        mongo_url = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'receptor_pro')]
        
        # Обновляем техкарту в истории
        result = await db.user_history.update_one(
            {"id": techcard_id},
            {"$set": {
                "techcard_v2_data": techcard_data,
                "updated_at": datetime.now().isoformat()
            }}
        )
        
        logger.info(f"✅ Save result: matched={result.matched_count}, modified={result.modified_count}")
        
        if result.matched_count == 0:
            raise HTTPException(404, f"Techcard with id {techcard_id} not found in history")
        
        return {"status": "success", "message": "Techcard saved successfully"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Error saving techcard: {str(e)}")
        raise HTTPException(500, f"Error saving techcard: {str(e)}")

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
        user_id = body.get('user_id', 'demo_user')
        
        if not techcard_data:
            raise HTTPException(400, "techcard data required")
        
        ingredients = techcard_data.get('ingredients', [])
        if not ingredients:
            raise HTTPException(400, "no ingredients to map")
        
        # SECURITY: Check user access to IIKO data
        if user_id == 'demo_user':
            # Demo users get mock/limited mapping data
            return {
                "status": "demo_mode",
                "message": "Автомаппинг недоступен для демо-пользователей. Зарегистрируйтесь и подключите IIKO RMS для полного функционала.",
                "results": [],
                "coverage": {"mapped": 0, "total": len(ingredients), "percentage": 0.0}
            }
        
        # Get organization ID (defaulting for now)
        organization_id = body.get('organization_id', 'default')
        
        # Initialize enhanced mapping service with user isolation
        from ..integrations.enhanced_mapping_service import get_enhanced_mapping_service
        mapping_service = get_enhanced_mapping_service()
        
        # Perform enhanced auto-mapping (only for authenticated users)
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
        "product_codes": [
            {"name": "Куриное филе", "code": "10001"},
            {"name": "Соль", "code": "10002"}
        ],
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
        
        # Generate product codes for ingredients
        product_codes = []
        current_code = start_code
        
        for name in ingredient_names:
            code_str = str(current_code).zfill(code_width)
            product_codes.append({
                "name": name,
                "code": code_str
            })
            current_code += 1
        
        return {
            "status": "success",
            "product_codes": product_codes,
            "codes_generated": len(product_codes),
            "next_available_code": current_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate product codes error: {e}")
        raise HTTPException(500, f"Generate product codes failed: {str(e)}")


@router.put("/techcards.v2/{techcard_id}")
async def update_techcard_v2(techcard_id: str, request: Request):
    """
    Update existing TechCard V2 in MongoDB
    Used for persisting SKU mappings, edits, and other changes
    
    Body: TechCard V2 object (JSON)
    Returns: Success status with update info
    """
    try:
        body = await request.json()
        
        if not techcard_id:
            raise HTTPException(400, "techcard_id required")
        
        # Get MongoDB connection
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        client = AsyncIOMotorClient(mongo_url)
        db_name = os.environ.get('DB_NAME', 'receptor_pro').strip('"')
        
        # Validate DB name length (MongoDB fix)
        if len(db_name) > 63:
            logger.warning(f"DB name too long ({len(db_name)}), truncating to 63 chars")
            db_name = db_name[:63]
        
        db = client[db_name]
        
        # Update техкарты в MongoDB
        # Remove _id from body if present (can't update _id field)
        if '_id' in body:
            del body['_id']
        if 'id' in body:
            del body['id']
        
        # Add updated_at timestamp
        from datetime import datetime
        body['updated_at'] = datetime.now()
        
        # 🔥 FIX: Try multiple ID lookup strategies
        # Techncards can be saved with _id (MongoDB ObjectId) or meta.id (UUID string)
        # Try to find by different ID fields
        query = {"$or": [
            {"_id": techcard_id},
            {"meta.id": techcard_id},
            {"id": techcard_id}
        ]}
        
        result = await db.techcards_v2.update_one(
            query,
            {"$set": body}
        )
        
        # If not found by $or, try individual lookups
        if result.matched_count == 0:
            # Try by meta.id first (most common case)
            result = await db.techcards_v2.update_one(
                {"meta.id": techcard_id},
                {"$set": body}
            )
        
        if result.matched_count == 0:
            # Try by _id as ObjectId (if techcard_id is string representation)
            try:
                from bson import ObjectId
                if ObjectId.is_valid(techcard_id):
                    result = await db.techcards_v2.update_one(
                        {"_id": ObjectId(techcard_id)},
                        {"$set": body}
                    )
            except Exception:
                pass
        
        client.close()
        
        if result.matched_count == 0:
            raise HTTPException(404, f"Techcard {techcard_id} not found (tried _id, meta.id, id)")
        
        logger.info(f"✅ Updated techcard {techcard_id} in MongoDB (modified: {result.modified_count})")
        
        return {
            "status": "success",
            "techcard_id": techcard_id,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "message": "Techcard updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update techcard error: {e}")
        raise HTTPException(500, f"Update failed: {str(e)}")