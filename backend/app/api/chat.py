"""
Chat API для RECEPTOR CO-PILOT
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.llm.unified_client import UnifiedLLMClient
from app.services.rag.search import search_knowledge_base
from app.services.iiko.iiko_rms_service import get_iiko_rms_service
from app.services.web_search import web_search, format_search_results_for_context, should_use_web_search
from app.core.config import settings
from app.core.database import db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

VENUE_PROFILES_COLLECTION = "venue_profiles"


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = "default_user"  # Временно, пока нет авторизации


def get_venue_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Загрузить профиль заведения из MongoDB"""
    try:
        collection = db.get_collection(VENUE_PROFILES_COLLECTION)
        profile = collection.find_one({"user_id": user_id})
        if profile:
            profile.pop("_id", None)
            return profile
    except Exception as e:
        print(f"⚠️ Error loading venue profile: {e}")
    return None


def get_venue_research(user_id: str) -> Optional[Dict[str, Any]]:
    """Загрузить результаты deep research из MongoDB"""
    try:
        collection = db.get_collection("venue_research_context")
        research = collection.find_one({"user_id": user_id})
        if research:
            research.pop("_id", None)
            return research
    except Exception as e:
        print(f"⚠️ Error loading venue research: {e}")
    return None


def build_venue_context(profile: Dict[str, Any]) -> str:
    """
    Построить контекст заведения для промпта.
    ВАЖНО: Это фоновая информация, НЕ для цитирования в каждом ответе!
    """
    if not profile:
        return ""
    
    # Собираем только ключевую информацию компактно
    info = []
    
    name = profile.get("venue_name", "")
    vtype = profile.get("venue_type", "")
    if name or vtype:
        info.append(f"{name} ({vtype})" if name and vtype else name or vtype)
    
    if profile.get("cuisine_focus"):
        info.append(f"кухня: {', '.join(profile['cuisine_focus'])}")
    
    if profile.get("city"):
        info.append(profile["city"])
    
    if profile.get("average_check"):
        info.append(f"чек ~{profile['average_check']}₽")
    
    if not info:
        return ""
    
    return "ПРОФИЛЬ ЗАВЕДЕНИЯ (внутренняя инфо, НЕ упоминай в ответе):\n" + ", ".join(info)


def get_iiko_connection_status(user_id: str) -> Dict[str, Any]:
    """Проверить статус подключения iiko для пользователя (Cloud или RMS)"""
    try:
        # Сначала проверяем Cloud API
        from app.core.database import db
        cloud_collection = db.get_collection("iiko_cloud_credentials")
        if cloud_collection is not None:
            try:
                cloud_creds = cloud_collection.find_one({"user_id": user_id})
                if cloud_creds and cloud_creds.get("status") == "connected":
                    org_id = cloud_creds.get("selected_organization_id")
                    if org_id:  # Проверяем что организация выбрана
                        logger.info(f"✅ Cloud API connected for user {user_id}, org: {org_id}")
                        return {
                            "status": "connected",
                            "type": "cloud",
                            "organization_id": org_id,
                            "organization_name": cloud_creds.get("selected_organization_name", "Организация"),
                            "api_key": cloud_creds.get("api_key"),  # Для использования в клиенте
                            "organizations": cloud_creds.get("organizations", [])
                        }
                    else:
                        logger.warning(f"⚠️ Cloud API connected but no organization selected for user {user_id}")
            except Exception as e:
                logger.error(f"Error checking Cloud credentials: {e}", exc_info=True)
        
        # Если Cloud не подключен, проверяем RMS
        try:
            rms_service = get_iiko_rms_service()
            if rms_service is None:
                logger.warning("iiko RMS service not initialized")
                return {"status": "not_connected", "type": None}
            
            rms_status = rms_service.get_rms_connection_status(user_id=user_id, auto_restore=False)
            if rms_status.get("status") in ["connected", "restored"]:
                rms_status["type"] = "rms"
                logger.info(f"✅ RMS connected for user {user_id}")
            return rms_status
        except Exception as e:
            logger.error(f"Error checking RMS status: {e}", exc_info=True)
            return {"status": "error", "type": None, "error": str(e)}
            
    except Exception as e:
        logger.error(f"❌ Critical error checking iiko status: {e}", exc_info=True)
        return {"status": "error", "type": None, "error": str(e)}


def search_iiko_products(query: str, organization_id: str = "default", limit: int = 10, iiko_type: str = "rms") -> List[Dict[str, Any]]:
    """Поиск продуктов в номенклатуре iiko (RMS или Cloud) с улучшенной точностью"""
    try:
        if iiko_type == "cloud":
            # Используем Cloud API
            from app.services.iiko.iiko_client import IikoClient
            from app.core.database import db
            
            # Получаем API ключ из контекста (должен быть передан)
            # Для Cloud API нужно получать номенклатуру и искать в ней
            logger.info(f"Searching in iikoCloud for: {query}")
            # TODO: Реализовать поиск через Cloud API
            return []
        else:
            # Используем RMS
            rms_service = get_iiko_rms_service()
            if rms_service is None:
                logger.warning("iiko RMS service not initialized")
                return []
            results = rms_service.search_rms_products_enhanced(
                organization_id=organization_id,
                query=query,
                limit=limit,
                min_score=0.75  # Повышенный порог для точности
            )
            return results
    except Exception as e:
        logger.error(f"Error searching iiko products: {e}", exc_info=True)
        return []


def get_iiko_nomenclature_stats(organization_id: str = "default") -> Dict[str, Any]:
    """Получить полную статистику по номенклатуре iiko"""
    try:
        rms_service = get_iiko_rms_service()
        if rms_service is None:
            return {"total_products": 0, "total_groups": 0, "error": "service_not_initialized"}
        return rms_service.get_nomenclature_stats(organization_id=organization_id)
    except Exception as e:
        logger.error(f"Error getting iiko stats: {e}", exc_info=True)
        return {"total_products": 0, "total_groups": 0, "error": str(e)}


def get_iiko_groups(organization_id: str = "default") -> List[Dict[str, Any]]:
    """Получить список групп/категорий"""
    try:
        rms_service = get_iiko_rms_service()
        if rms_service is None:
            return []
        return rms_service.get_all_groups(organization_id=organization_id)
    except Exception as e:
        logger.error(f"Error getting iiko groups: {e}", exc_info=True)
        return []


def get_products_by_group(group_name: str, organization_id: str = "default", limit: int = 20) -> Dict[str, Any]:
    """Получить продукты из определенной группы/категории"""
    try:
        rms_service = get_iiko_rms_service()
        if rms_service is None:
            return {"products": [], "count": 0, "error": "service_not_initialized"}
        return rms_service.get_products_by_group(
            organization_id=organization_id,
            group_name=group_name,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting products by group: {e}", exc_info=True)
        return {"products": [], "count": 0, "error": str(e)}


def extract_search_terms(query: str) -> List[str]:
    """Извлечь потенциальные поисковые термины из запроса"""
    # Слова-маркеры для поиска продуктов
    markers = ["найди", "поищи", "есть ли", "покажи", "какая цена", "сколько стоит", "ингредиент", "продукт"]
    
    query_lower = query.lower()
    
    # Если есть маркер, извлекаем то, что идет после
    for marker in markers:
        if marker in query_lower:
            # Берем все после маркера
            idx = query_lower.find(marker)
            after = query[idx + len(marker):].strip()
            # Убираем знаки препинания
            after = after.strip('?.,!')
            if after:
                return [after]
    
    return []


@router.post("/message")
async def chat_message(request: ChatRequest):
    """
    Main chat endpoint for Receptor Copilot.
    """
    user_query = request.messages[-1].content
    user_id = request.user_id or "default_user"
    
    # Загружаем профиль заведения и deep research
    venue_profile = get_venue_profile(user_id)
    venue_research = get_venue_research(user_id)
    
    logger.info(f"👤 User: {user_id}, Profile: {venue_profile is not None}, Research: {venue_research is not None}")
    
    venue_context = build_venue_context(venue_profile)
    
    # Добавляем результаты deep research если есть
    if venue_research:
        logger.info(f"📊 Found research data for {venue_research.get('venue_name')}: {len(venue_research.get('strengths', []))} strengths, {len(venue_research.get('weaknesses', []))} weaknesses")
        from app.services.venue_research import format_dossier_for_context
        research_context = format_dossier_for_context(venue_research)
        venue_context += research_context
        logger.info(f"✅ Added {len(research_context)} chars of research context")
    else:
        logger.warning(f"⚠️ No research data found for user {user_id}")
    
    # Simple Intent Detection
    intent = detect_intent(user_query)
    
    context = ""
    
    # Добавляем контекст заведения
    if venue_context:
        context += f"\n\n{venue_context}\n"
    
    # 🌐 Web Search для актуальных запросов (тренды, новости, цены)
    should_search = should_use_web_search(user_query)
    logger.info(f"🌐 Web search check: {should_search} for query: {user_query[:100]}")
    
    if should_search:
        logger.info(f"🌐 Web search triggered!")
        try:
            search_result = await web_search(user_query, max_results=5)
            
            if search_result.get("error"):
                logger.error(f"⚠️ Web search error: {search_result['error']}")
            else:
                web_context = format_search_results_for_context(search_result)
                if web_context:
                    context += web_context
                    logger.info(f"🌐 Added {len(search_result.get('results', []))} web results to context")
                else:
                    logger.warning("⚠️ Web search returned empty context")
        except Exception as e:
            logger.error(f"⚠️ Web search failed: {e}", exc_info=True)
    
    if intent == "knowledge_base":
        logger.info(f"🔍 Searching Knowledge Base for: {user_query}")
        results = []
        
        # Определяем категорию на основе запроса для фильтрации
        query_lower = user_query.lower()
        search_categories = None
        if any(kw in query_lower for kw in ["iiko", "server api", "olap", "техкарт", "номенклатур", "endpoint", "api", "авторизац"]):
            search_categories = ["iiko"]
            logger.info(f"📂 Filtering by category: iiko")
        elif any(kw in query_lower for kw in ["haccp", "санпин", "гигиен", "безопасность пищ"]):
            search_categories = ["haccp"]
            logger.info(f"📂 Filtering by category: haccp")
        elif any(kw in query_lower for kw in ["маркетинг", "smm", "продвижение", "реклам"]):
            search_categories = ["marketing"]
            logger.info(f"📂 Filtering by category: marketing")
        elif any(kw in query_lower for kw in ["персонал", "hr", "сотрудник", "найм", "обучение"]):
            search_categories = ["hr"]
            logger.info(f"📂 Filtering by category: hr")
        
        # Подключаем коллекцию с проиндексированными чанками
        try:
            from pymongo import MongoClient
            mongo_client = MongoClient(settings.mongo_connection_string)
            kb_collection = mongo_client[settings.DB_NAME]["knowledge_base_chunks"]
            
            # Диагностика
            total_chunks = kb_collection.count_documents({"indexed": True, "type": {"$ne": "metadata"}})
            logger.info(f"📊 Total indexed chunks in DB: {total_chunks}")
            
            # Пробуем векторный поиск с категорией
            results = search_knowledge_base(user_query, top_k=10, categories=search_categories, db_collection=kb_collection)
            logger.info(f"📊 Vector search returned {len(results)} results")
            
            # Если категория слишком узкая и результатов мало - расширяем поиск
            if len(results) < 3 and search_categories:
                logger.info("📊 Expanding search without category filter")
                more_results = search_knowledge_base(user_query, top_k=10, db_collection=kb_collection)
                # Добавляем уникальные результаты
                seen_sources = {r.get('content', '')[:100] for r in results}
                for r in more_results:
                    if r.get('content', '')[:100] not in seen_sources:
                        results.append(r)
                        if len(results) >= 10:
                            break
            
            mongo_client.close()
        except Exception as e:
            logger.error(f"MongoDB error: {e}", exc_info=True)
        
        # Если векторный поиск не дал результатов - используем текстовый fallback
        if not results:
            logger.warning("⚠️ No results from vector search, trying text fallback")
            results = search_knowledge_base(user_query, top_k=10, db_collection=None)
            logger.info(f"📊 Text fallback returned {len(results)} results")
        
        if results:
            context += "\n\n### РЕЛЕВАНТНАЯ ИНФОРМАЦИЯ ИЗ БАЗЫ ЗНАНИЙ ###\n"
            for i, res in enumerate(results, 1):
                source = res.get('source', 'unknown')
                category = res.get('category', 'general')
                score = res.get('score', 0)
                content = res.get('content', '')[:1200]  # Увеличили до 1200 символов
                
                context += f"""
📄 ДОКУМЕНТ {i} [{source}] (категория: {category}, релевантность: {score:.1%})
────────────────────────────────────────
{content}
────────────────────────────────────────
"""
            logger.info(f"✅ Found {len(results)} relevant chunks from knowledge base")
        else:
            logger.warning(f"⚠️ No results from knowledge base for: {user_query}")
                
    elif intent == "iiko_analytics" or intent == "iiko_products":
        logger.info(f"📊 Querying iiko for: {user_query}")
        
        try:
            # Проверяем подключение iiko (Cloud или RMS)
            iiko_status = get_iiko_connection_status(user_id)
            iiko_type = iiko_status.get("type")
            status = iiko_status.get("status")
            
            if status not in ["connected", "restored"]:
                error_msg = iiko_status.get("error", "Неизвестная ошибка")
                context += f"\n\n⚠️ IIKO: Не подключено (статус: {status})\n"
                context += f"Ошибка: {error_msg}\n"
                context += "Попросите пользователя подключить iiko в разделе 'Интеграции'.\n"
                logger.warning(f"⚠️ iiko not connected for user {user_id}: {status}")
            else:
                org_id = iiko_status.get("organization_id")
                org_name = iiko_status.get("organization_name", "Организация")
                
                if not org_id:
                    context += "\n\n⚠️ IIKO: Организация не выбрана. Выберите организацию в разделе 'Интеграции'.\n"
                    logger.warning(f"⚠️ No organization selected for user {user_id}")
                else:
                    # Добавляем инструкции по работе с iiko из документации
                    context += """
═══════════════════════════════════════════════════════════════
📚 ИНСТРУКЦИИ ПО РАБОТЕ С IIKO:
═══════════════════════════════════════════════════════════════
1. iikoCloud API предоставляет доступ к номенклатуре через метод fetch_nomenclature(organization_id)
2. Номенклатура содержит:
   - products: список продуктов с полями id, name, description, size_prices, group_id, tags
   - groups: список групп/категорий с полями id, name, parent_group
3. Для поиска продуктов используй поиск по полю "name" (регистронезависимо)
4. Цены находятся в size_prices[0].price
5. Если продуктов нет в базе - это нормально, возможно они еще не добавлены
6. Всегда проверяй реальные данные из номенклатуры, не выдумывай!
═══════════════════════════════════════════════════════════════
"""
                    
                    context += f"\n\nСТАТУС IIKO ({iiko_type.upper() if iiko_type else 'UNKNOWN'}):\n"
                    context += f"- Подключено к: {org_name}\n"
                    context += f"- Тип подключения: {'iikoCloud API' if iiko_type == 'cloud' else 'iiko RMS Server' if iiko_type == 'rms' else 'Unknown'}\n"
                    context += f"- Organization ID: {org_id}\n"
                    
                    if iiko_type == "cloud":
                        # Для Cloud API сначала пытаемся использовать синхронизированные данные
                        try:
                            from app.core.database import db
                            sync_collection = db.get_collection("iiko_cloud_nomenclature")
                            nomenclature_data = None
                            
                            if sync_collection is not None:
                                try:
                                    # Пытаемся получить синхронизированные данные
                                    sync_data = sync_collection.find_one({
                                        "user_id": user_id,
                                        "organization_id": org_id
                                    })
                                    
                                    if sync_data and sync_data.get("nomenclature"):
                                        nomenclature_data = sync_data.get("nomenclature")
                                        logger.info(f"✅ Using synced Cloud nomenclature: {len(nomenclature_data.get('products', []))} products")
                                except Exception as e:
                                    logger.error(f"Error reading synced data: {e}", exc_info=True)
                            
                            # Если синхронизированных данных нет - получаем через API
                            if not nomenclature_data:
                                logger.info(f"📡 Synced data not found, fetching from API...")
                                try:
                                    from app.services.iiko.iiko_client import IikoClient
                                    api_key = iiko_status.get("api_key")
                                    if api_key:
                                        client = IikoClient(api_login=api_key)
                                        nomenclature_data = client.fetch_nomenclature(org_id)
                                        logger.info(f"✅ Fetched from API: {len(nomenclature_data.get('products', []))} products")
                                    else:
                                        logger.error("API key not found in iiko_status")
                                        context += "\n\n⚠️ API ключ не найден. Проверьте подключение в разделе 'Интеграции'.\n"
                                except Exception as e:
                                    logger.error(f"Error fetching from Cloud API: {e}", exc_info=True)
                                    context += f"\n\n⚠️ Ошибка получения данных из iikoCloud API: {str(e)}\n"
                                    context += "Попробуйте выполнить синхронизацию в разделе 'Интеграции'.\n"
                            
                            if nomenclature_data:
                                products = nomenclature_data.get("products", [])
                                groups = nomenclature_data.get("groups", [])
                                products_count = len(products) if products else 0
                                groups_count = len(groups) if groups else 0
                                
                                context += f"- Продуктов в базе: {products_count}\n"
                                context += f"- Групп: {groups_count}\n"
                                
                                # Поиск продуктов
                                search_terms = extract_search_terms(user_query)
                                if search_terms:
                                    for term in search_terms:
                                        # Более гибкий поиск
                                        found = []
                                        term_lower = term.lower()
                                        for p in products:
                                            name = p.get("name", "").lower() if p.get("name") else ""
                                            if term_lower in name:
                                                found.append(p)
                                        
                                        if found:
                                            context += f"\n\nНАЙДЕНЫ ПРОДУКТЫ ПО ЗАПРОСУ '{term}':\n"
                                            for p in found[:10]:  # Показываем до 10
                                                price = 0
                                                if p.get("size_prices") and len(p.get("size_prices", [])) > 0:
                                                    price = p.get("size_prices", [{}])[0].get("price", 0)
                                                price_info = f", цена: {price:.2f} руб" if price else ""
                                                context += f"- {p.get('name', 'н/д')}{price_info}\n"
                                        else:
                                            context += f"\n\nПо запросу '{term}' продукты не найдены в номенклатуре iiko.\n"
                                else:
                                    # Если нет поисковых терминов, показываем общую статистику
                                    if products_count > 0:
                                        context += f"\n\nПримеры продуктов в базе:\n"
                                        for p in products[:5]:
                                            context += f"- {p.get('name', 'н/д')}\n"
                            else:
                                context += "\n\n⚠️ Данные номенклатуры не найдены. Выполните синхронизацию в разделе 'Интеграции'.\n"
                                
                        except Exception as e:
                            logger.error(f"❌ Critical error in Cloud API processing: {e}", exc_info=True)
                            context += f"\n\n❌ Критическая ошибка при работе с iikoCloud: {str(e)}\n"
                            context += "Попробуйте выполнить синхронизацию в разделе 'Интеграции'.\n"
            else:
                # Для RMS используем существующую логику
                summary = get_iiko_nomenclature_stats(org_id)
                context += f"- Продуктов в базе: {summary.get('total_products', 0)}\n"
                context += f"- Групп: {summary.get('total_groups', 0)}\n"
                
                # Если есть поисковый запрос - ищем продукты
                search_terms = extract_search_terms(user_query)
                if search_terms:
                    for term in search_terms:
                        products = search_iiko_products(term, org_id, limit=5, iiko_type="rms")
                        if products:
                            context += f"\n\nНАЙДЕНЫ ПРОДУКТЫ ПО ЗАПРОСУ '{term}':\n"
                            for p in products:
                                price_info = f", цена: {p.get('price_per_unit', 0):.2f} руб/{p.get('unit', 'ед')}" if p.get('price_per_unit') else ""
                                context += f"- {p['name']} (артикул: {p.get('article', 'н/д')}{price_info})\n"
                        else:
                            context += f"\n\nПо запросу '{term}' продукты не найдены в номенклатуре iiko.\n"
        else:
            context += "\n\nIIKO: Не подключено. Попросите пользователя подключить iiko в разделе 'Интеграции'.\n"
    
    elif intent == "iiko_products":
        logger.info(f"🔍 Searching iiko products for: {user_query}")
        
        iiko_status = get_iiko_connection_status(user_id)
        
        if iiko_status.get("status") in ["connected", "restored"]:
            org_id = iiko_status.get("organization_id", "default")
            
            # Извлекаем что искать
            search_terms = extract_search_terms(user_query)
            if not search_terms:
                # Пробуем искать по всему запросу
                search_terms = [user_query]
            
            for term in search_terms:
                products = search_iiko_products(term, org_id, limit=10)
                if products:
                    context += f"\n\nРЕЗУЛЬТАТЫ ПОИСКА В IIKO ПО '{term}':\n"
                    for p in products:
                        price = p.get('price_per_unit', 0) or p.get('price', 0)
                        price_str = f"{price:.2f} руб/{p.get('unit', 'шт')}" if price else "цена не указана"
                        group = p.get('group_name') or 'Без группы'
                        match_info = f" (точность: {p.get('match_score', 0)*100:.0f}%)" if p.get('match_score') else ""
                        context += f"- {p['name']} | {price_str} | {group}{match_info}\n"
                else:
                    context += f"\n\nПо запросу '{term}' ничего не найдено в номенклатуре.\n"
        else:
            context += "\n\nДля поиска продуктов нужно подключить iiko в разделе 'Интеграции'.\n"
    
    elif intent == "iiko_categories":
        logger.info(f"📂 Getting iiko categories for: {user_query}")
        
        iiko_status = get_iiko_connection_status(user_id)
        
        if iiko_status.get("status") in ["connected", "restored"]:
            org_id = iiko_status.get("organization_id", "default")
            
            # Проверяем, запрашивает ли конкретную категорию
            category_name = extract_category_name(user_query)
            
            if category_name:
                # Показываем продукты из конкретной категории
                result = get_products_by_group(category_name, org_id, limit=20)
                if result.get("products"):
                    context += f"\n\nПРОДУКТЫ В КАТЕГОРИИ '{result.get('group_name', category_name)}':\n"
                    context += f"Всего: {result.get('total_count', 0)} позиций\n\n"
                    for p in result["products"]:
                        price = p.get('price_per_unit', 0) or p.get('price', 0)
                        price_str = f"{price:.2f} руб" if price else ""
                        context += f"- {p['name']} {price_str}\n"
                else:
                    context += f"\n\nКатегория '{category_name}' не найдена или пуста.\n"
            else:
                # Показываем список всех категорий
                groups = get_iiko_groups(org_id)
                if groups:
                    context += f"\n\nКАТЕГОРИИ/ГРУППЫ В НОМЕНКЛАТУРЕ ({len(groups)} шт.):\n"
                    for g in groups[:15]:  # Ограничим до 15
                        context += f"- {g['name']} ({g['products_count']} позиций)\n"
                    if len(groups) > 15:
                        context += f"... и ещё {len(groups) - 15} категорий\n"
                else:
                    context += "\n\nКатегории не найдены в номенклатуре.\n"
        else:
            context += "\n\nДля просмотра категорий нужно подключить iiko в разделе 'Интеграции'.\n"
    
    elif intent == "iiko_stats":
        logger.info(f"📊 Getting iiko stats for: {user_query}")
        
        iiko_status = get_iiko_connection_status(user_id)
        
        if iiko_status.get("status") in ["connected", "restored"]:
            org_id = iiko_status.get("organization_id", "default")
            stats = get_iiko_nomenclature_stats(org_id)
            
            context += f"\n\nСТАТИСТИКА НОМЕНКЛАТУРЫ IIKO:\n"
            context += f"- Всего позиций: {stats.get('total_products', 0)}\n"
            context += f"- Активных: {stats.get('active_products', 0)}\n"
            context += f"- Групп/категорий: {stats.get('total_groups', 0)}\n"
            context += f"- С указанной ценой: {stats.get('products_with_price', 0)}\n"
            context += f"- Без цены: {stats.get('products_without_price', 0)}\n"
            
            if stats.get('top_groups'):
                context += f"\nТОП-5 КАТЕГОРИЙ ПО КОЛИЧЕСТВУ ПОЗИЦИЙ:\n"
                for i, g in enumerate(stats['top_groups'][:5], 1):
                    context += f"{i}. {g['name']} — {g['count']} позиций\n"
            
            if stats.get('last_sync'):
                context += f"\nПоследняя синхронизация: {stats['last_sync']}\n"
        else:
            context += "\n\nДля просмотра статистики нужно подключить iiko в разделе 'Интеграции'.\n"

    # Call LLM
    try:
        client = UnifiedLLMClient(
            openrouter_key=settings.OPENROUTER_API_KEY,
            openai_key=settings.OPENAI_API_KEY
        )
        
        from datetime import datetime
        current_date = datetime.now().strftime("%d %B %Y")
        
        # Определяем, нужен ли специальный промпт для рецептов
        is_recipe_request = any(keyword in user_query.lower() for keyword in [
            'рецепт', 'создай блюдо', 'техкарт', 'технологическ', 'ингредиент', 
            'приготов', 'блюдо', 'recipe', 'dish'
        ])
        
        if is_recipe_request:
            # Золотой промпт для рецептов V1
            system_prompt = f"""Ты — шеф-повар мирового уровня и кулинарный писатель. 

СЕГОДНЯ: {current_date}

Создай КРАСИВЫЙ и ПОДРОБНЫЙ рецепт для ресторанного бизнеса.

ФОРМАТ РЕЦЕПТА V1 (для творчества и экспериментов):

**Название блюда**

📝 **ОПИСАНИЕ**
Вдохновляющее описание блюда с историей, традициями и особенностями

⏱️ **ВРЕМЕННЫЕ РАМКИ**
Подготовка: X минут
Приготовление: X минут
Общее время: X минут

🍽️ **ПОРЦИИ**
На X порций

🛒 **ИНГРЕДИЕНТЫ**
Основные ингредиенты:
• Ингредиент 1 — количество (подробное описание, зачем нужен)
• Ингредиент 2 — количество (подробное описание, зачем нужен)
...

Специи и приправы:
• Специя 1 — количество (влияние на вкус)
• Специя 2 — количество (влияние на вкус)
...

👨‍🍳 **ПОШАГОВОЕ ПРИГОТОВЛЕНИЕ**

**Шаг 1: Подготовка ингредиентов**
Детальное описание подготовительного этапа с советами

**Шаг 2: [Название этапа]**  
Подробные инструкции с температурами, временем, техниками

**Шаг 3: [Название этапа]**
Ещё более детальные инструкции...

[Продолжить до завершения - обычно 5-8 шагов]

💡👨‍🍳 **СЕКРЕТЫ ШЕФА**
• Профессиональный совет 1
• Профессиональный совет 2
• Секретная техника 3

🍽️ **ПОДАЧА И ПРЕЗЕНТАЦИЯ**
Как красиво подать блюдо, украшения, посуда

🔄 **ВАРИАЦИИ И ЭКСПЕРИМЕНТЫ**
• Интересная вариация 1
• Креативная замена ингредиентов 2
• Сезонная адаптация 3

💾 **ПОЛЕЗНЫЕ СОВЕТЫ**
• Как сохранить
• Что делать если что-то пошло не так
• Как заранее подготовить

Сделай рецепт МАКСИМАЛЬНО ПОДРОБНЫМ, ВДОХНОВЛЯЮЩИМ и КРАСИВЫМ для чтения!

ПРЕДЛОЖЕНИЯ СЛЕДУЮЩИХ ШАГОВ:
В самом конце ответа добавь:
[SUGGESTIONS]
1. Создать техкарту для этого блюда
2. Рассчитать себестоимость
3. Найти похожие рецепты
[/SUGGESTIONS]"""
        else:
            system_prompt = f"""Ты — RECEPTOR, экспертный AI-копайлот для ресторанного бизнеса.

СЕГОДНЯ: {current_date}

ПРАВИЛА:
1. Профиль заведения — внутренний контекст. Не упоминай его в каждом ответе.
2. Используй предоставленный контекст, но не цитируй [Источник] если это не техническая документация.
3. Нет информации — скажи прямо, предложи поискать в интернете.
4. По делу, без воды.

ЭКСПЕРТИЗА: Ресторанный бизнес, HACCP, финансы, маркетинг, iiko.

ФОРМАТ: Русский, структурно, лаконично.

ПРЕДЛОЖЕНИЯ СЛЕДУЮЩИХ ШАГОВ:
В конце ответа добавь 2-3 связанных вопроса/действия, которые могут быть полезны пользователю. 
Формат:
[SUGGESTIONS]
1. Краткий вопрос или действие (максимум 6-8 слов)
2. Ещё один связанный вопрос
3. Третий вопрос (опционально)
[/SUGGESTIONS]

Примеры хороших предложений:
- "Создать техкарту для этого блюда"
- "Показать статистику продаж за месяц"
- "Как оптимизировать себестоимость?"
- "Найти похожие рецепты в базе"
- "Рассчитать точку безубыточности"

Предложения должны быть конкретными, связанными с текущим контекстом и полезными для ресторанного бизнеса."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context to the last user message with clear markers
        final_user_message = request.messages[-1].content
        if context:
            final_user_message += f"""

═══════════════════════════════════════════════════════════════
📚 КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ (ИСПОЛЬЗУЙ ЭТУ ИНФОРМАЦИЮ ДЛЯ ОТВЕТА):
═══════════════════════════════════════════════════════════════
{context}
═══════════════════════════════════════════════════════════════
⚠️ ВАЖНО: Отвечай ТОЛЬКО на основе информации выше. Не выдумывай!
═══════════════════════════════════════════════════════════════"""
            
        # Add history (excluding the last one which we just modified)
        for msg in request.messages[:-1]:
            messages.append({"role": msg.role, "content": msg.content})
            
        messages.append({"role": "user", "content": final_user_message})
        
        # Автоматический роутинг модели по сложности запроса
        response, usage_info = await client.chat_completion(
            messages=messages,
            auto_route=True,  # Умный выбор модели
            temperature=0.7
        )
        
        model_used = usage_info.get('model', 'unknown')
        complexity = usage_info.get('complexity', 'standard')
        cost = usage_info.get('cost_usd', 0)
        
        logger.info(f"🤖 Model: {model_used} | Complexity: {complexity} | Cost: ${cost:.4f}")
        
        # Извлекаем предложения следующих шагов из ответа
        # Сначала удаляем, потом извлекаем, чтобы не было конфликтов
        suggestions = extract_suggestions(response)
        clean_response = remove_suggestions_from_content(response)
        
        # Логируем для отладки
        if suggestions:
            logger.info(f"💡 Extracted {len(suggestions)} suggestions: {suggestions}")
        else:
            # Проверяем, есть ли вообще блок SUGGESTIONS в ответе
            if '[SUGGESTIONS]' in response.upper() or 'SUGGESTIONS' in response.upper():
                logger.warning(f"⚠️ SUGGESTIONS keyword found but not parsed. Trying fallback extraction...")
                # Попытка извлечь вручную из конца ответа
                lines = response.split('\n')
                suggestions_start = -1
                for i, line in enumerate(lines):
                    if '[SUGGESTIONS]' in line.upper() or (i > 0 and 'SUGGESTIONS' in line.upper() and lines[i-1].strip() == ''):
                        suggestions_start = i + 1
                        break
                
                if suggestions_start > 0:
                    # Извлекаем следующие строки с нумерацией
                    fallback_suggestions = []
                    for line in lines[suggestions_start:suggestions_start+5]:
                        line = line.strip()
                        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                            # Убираем нумерацию
                            line = re.sub(r'^\d+[\.\)]\s*', '', line)
                            line = re.sub(r'^[-•*]\s*', '', line)
                            if line and len(line) > 3:
                                fallback_suggestions.append(line)
                    
                    if fallback_suggestions:
                        suggestions = fallback_suggestions[:3]
                        logger.info(f"✅ Fallback extraction successful: {suggestions}")
        
        return {
            "role": "assistant", 
            "content": clean_response,
            "model": model_used,  # Показываем какая модель ответила
            "usage": usage_info,
            "suggestions": suggestions  # Предложения следующих шагов
        }
        
    except Exception as e:
        print(f"❌ Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def extract_suggestions(content: str) -> List[str]:
    """Извлекает предложения следующих шагов из ответа LLM"""
    import re
    suggestions = []
    suggestions_text = None
    
    # Вариант 1: Ищем блок [SUGGESTIONS]...[/SUGGESTIONS] (самый надежный)
    pattern1 = r'\[SUGGESTIONS\](.*?)\[/SUGGESTIONS\]'
    match = re.search(pattern1, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        suggestions_text = match.group(1).strip()
        logger.info("✅ Found suggestions with [SUGGESTIONS]...[/SUGGESTIONS] tags")
    else:
        # Вариант 1.5: Ищем [SUGGESTIONS] без закрывающего тега (LLM забыл закрыть)
        pattern1_5 = r'\[SUGGESTIONS\](.*?)(?=\n\n|\n[A-ZА-Я][A-ZА-Я\s]{2,}:|$)'
        match = re.search(pattern1_5, content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            suggestions_text = match.group(1).strip()
            logger.info("✅ Found suggestions with [SUGGESTIONS] (no closing tag)")
        else:
            # Вариант 2: Ищем блок SUGGESTIONS (без скобок) с последующими пунктами
            pattern2 = r'(?:^|\n)\s*SUGGESTIONS\s*\n(.*?)(?=\n\n|\n[A-ZА-Я][A-ZА-Я\s]{2,}:|$)'
            match = re.search(pattern2, content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
            if match:
                suggestions_text = match.group(1).strip()
                logger.info("✅ Found suggestions without brackets")
            else:
                # Вариант 3: Ищем "Следующие шаги" на русском
                pattern3 = r'(?:^|\n)\s*[Сс]ледующие\s+шаги[:\s]*\n(.*?)(?=\n\n|\n[A-ZА-Я][A-ZА-Я\s]{2,}:|$)'
                match = re.search(pattern3, content, re.DOTALL | re.MULTILINE)
                if match:
                    suggestions_text = match.group(1).strip()
                    logger.info("✅ Found suggestions with 'Следующие шаги'")
                else:
                    # Вариант 4: Ищем просто "SUGGESTIONS" и берём следующие 3-5 строк с нумерацией
                    pattern4 = r'(?:^|\n)\s*SUGGESTIONS\s*\n((?:\s*\d+[\.\)]\s*.*\n?){1,5})'
                    match = re.search(pattern4, content, re.IGNORECASE | re.MULTILINE)
                    if match:
                        suggestions_text = match.group(1).strip()
                        logger.info("✅ Found suggestions with numbered list")
    
    if not suggestions_text:
        logger.debug("❌ No suggestions block found in content")
        return []
    
    # Разбиваем на строки и извлекаем предложения
    lines = suggestions_text.split('\n')
    for line in lines:
        line = line.strip()
        # Пропускаем пустые строки
        if not line:
            continue
        # Пропускаем заголовки типа "SUGGESTIONS", "Следующие шаги"
        if line.upper() in ['SUGGESTIONS', 'СЛЕДУЮЩИЕ ШАГИ', 'РЕКОМЕНДАЦИИ', 'СЛЕДУЮЩИЕ ШАГИ:']:
            continue
        # Пропускаем разделители
        if line.startswith('---') or line.startswith('===') or line.startswith('___'):
            continue
        # Убираем нумерацию (1., 2., и т.д.)
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        # Убираем дефисы и маркеры списка
        line = re.sub(r'^[-•*]\s*', '', line)
        # Убираем знаки вопроса в конце (они будут добавлены при необходимости)
        line = re.sub(r'\?+\s*$', '', line)
        # Убираем лишние пробелы
        line = line.strip()
        if line and len(line) > 3:  # Минимум 3 символа
            suggestions.append(line)
    
    # Ограничиваем до 3 предложений
    result = suggestions[:3]
    if result:
        logger.debug(f"✅ Parsed {len(result)} suggestions: {result}")
    return result


def remove_suggestions_from_content(content: str) -> str:
    """Удаляет блок предложений из контента ответа"""
    import re
    
    original_length = len(content)
    original_content = content
    
    # Вариант 1: Удаляем блок [SUGGESTIONS]...[/SUGGESTIONS] (самый надежный)
    # Используем более жадный паттерн, который захватывает всё до закрывающего тега
    pattern1 = r'\[SUGGESTIONS\].*?\[/SUGGESTIONS\]'
    content = re.sub(pattern1, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Вариант 1.5: Удаляем экранированные скобки \[SUGGESTIONS\]...\[/SUGGESTIONS\]
    pattern1_escaped = r'\\?\[SUGGESTIONS\\?\].*?\\?\[/SUGGESTIONS\\?\]'
    content = re.sub(pattern1_escaped, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Вариант 2: Удаляем блок SUGGESTIONS с последующими пунктами (до конца или до следующего заголовка)
    pattern2 = r'(?:^|\n)\s*SUGGESTIONS\s*\n.*?(?=\n\n|\n[A-ZА-Я][A-ZА-Я\s]{2,}:|$)'
    content = re.sub(pattern2, '', content, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
    
    # Вариант 3: Удаляем "Следующие шаги" на русском
    pattern3 = r'(?:^|\n)\s*[Сс]ледующие\s+шаги[:\s]*\n.*?(?=\n\n|\n[A-ZА-Я][A-ZА-Я\s]{2,}:|$)'
    content = re.sub(pattern3, '', content, flags=re.DOTALL | re.MULTILINE)
    
    # Вариант 4: Удаляем просто "SUGGESTIONS" и следующие 3-5 строк с нумерацией
    pattern4 = r'(?:^|\n)\s*SUGGESTIONS\s*\n(?:\s*\d+[\.\)]\s*.*\n?){1,5}'
    content = re.sub(pattern4, '', content, flags=re.IGNORECASE | re.MULTILINE)
    
    # Вариант 5: Удаляем если остались строки с нумерацией после ключевых слов
    # Это для случаев, когда LLM забыл закрывающий тег
    if '[SUGGESTIONS]' in content.upper() or 'SUGGESTIONS' in content.upper():
        # Ищем от [SUGGESTIONS] до конца или до следующего параграфа
        pattern5 = r'(?:^|\n)\s*\\?\[?SUGGESTIONS\\?\]?\s*\n.*'
        content = re.sub(pattern5, '', content, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
    
    # Убираем лишние пустые строки в конце
    content = re.sub(r'\n{3,}', '\n\n', content)
    # Убираем пустые строки в самом конце
    content = re.sub(r'\n+$', '', content)
    # Убираем пробелы в конце
    content = content.rstrip()
    
    removed_chars = original_length - len(content)
    if removed_chars > 0:
        logger.info(f"✅ Removed {removed_chars} chars of suggestions from content")
    elif '[SUGGESTIONS]' in original_content.upper() or 'SUGGESTIONS' in original_content.upper():
        logger.warning(f"⚠️ SUGGESTIONS found but not removed. Trying fallback...")
        # Финальная попытка - просто удаляем всё после [SUGGESTIONS]
        content = re.sub(r'\[SUGGESTIONS\].*$', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = content.rstrip()
        logger.info(f"✅ Fallback removal applied. New length: {len(content)}")
    
    return content


def detect_intent(query: str) -> str:
    """Определение намерения пользователя"""
    query_lower = query.lower()
    
    # СНАЧАЛА проверяем технические вопросы про API/документацию
    # Это приоритетнее чем живые данные iiko
    api_doc_keywords = ["api", "endpoint", "olap", "техкарт", "технологическ", 
                        "rest api", "метод", "запрос", "авторизац", "токен",
                        "номенклатур", "справочник", "документац", "интеграц",
                        "как получить", "как использ", "можешь делать"]
    if any(w in query_lower for w in api_doc_keywords):
        return "knowledge_base"
    
    # База знаний (HACCP, СанПиН, HR и т.д.)
    kb_keywords = ["haccp", "санпин", "норм", "правил", "закон", "hr", "найм", "зарплат", 
                   "маркетинг", "smm", "гигиен", "требован", "сертифик", "лицен",
                   "фудкост расчет", "рентабельн", "roi", "кбжу", "калор"]
    if any(w in query_lower for w in kb_keywords):
        return "knowledge_base"
    
    # Категории/группы в iiko (живые данные)
    category_keywords = ["категори", "группы", "группа", "раздел", "все пив", "все бургер", 
                        "все напитк", "меню", "ассортимент", "покажи все"]
    if any(w in query_lower for w in category_keywords):
        return "iiko_categories"
    
    # Статистика номенклатуры (живые данные)
    stats_keywords = ["сколько позиций", "сколько товар", "статистик", "сколько продукт",
                     "сколько в номенклатуре", "топ групп", "топ категор"]
    if any(w in query_lower for w in stats_keywords):
        return "iiko_stats"
    
    # Поиск продуктов в iiko (живые данные)
    search_keywords = ["найди", "поищи", "есть ли", "ингредиент", "продукт", 
                      "сколько стоит", "какая цена", "артикул", "покажи"]
    if any(w in query_lower for w in search_keywords):
        return "iiko_products"
    
    # iiko общая аналитика (живые данные)
    iiko_keywords = ["выручк", "продаж", "iiko", "айко", "отчет", "аналитик", "синхрониз"]
    if any(w in query_lower for w in iiko_keywords):
        return "iiko_analytics"
    
    # По умолчанию — всегда ищем в базе знаний (RAG first!)
    return "knowledge_base"


def extract_category_name(query: str) -> Optional[str]:
    """Извлечь название категории из запроса"""
    query_lower = query.lower()
    
    # Паттерны для извлечения категории
    patterns = [
        ("покажи все ", ""),
        ("покажи категорию ", ""),
        ("покажи группу ", ""),
        ("все ", ""),
        ("категория ", ""),
        ("группа ", ""),
    ]
    
    for prefix, suffix in patterns:
        if prefix in query_lower:
            idx = query_lower.find(prefix)
            extracted = query[idx + len(prefix):].strip()
            extracted = extracted.strip('?.,!')
            if extracted:
                return extracted
    
    return None
