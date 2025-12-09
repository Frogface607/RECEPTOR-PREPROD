"""
Chat API для RECEPTOR CO-PILOT
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.llm.client import OpenAIClient
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
    """Проверить статус подключения iiko для пользователя"""
    try:
        rms_service = get_iiko_rms_service()
        if rms_service is None:
            return {"status": "not_initialized"}
        return rms_service.get_rms_connection_status(user_id=user_id, auto_restore=False)
    except Exception as e:
        logger.error(f"Error checking iiko status: {e}")
        return {"status": "error", "error": str(e)}


def search_iiko_products(query: str, organization_id: str = "default", limit: int = 10) -> List[Dict[str, Any]]:
    """Поиск продуктов в номенклатуре iiko с улучшенной точностью"""
    try:
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
                
    elif intent == "iiko_analytics":
        logger.info(f"📊 Querying iiko for: {user_query}")
        
        # Проверяем подключение iiko
        iiko_status = get_iiko_connection_status(user_id)
        
        if iiko_status.get("status") in ["connected", "restored"]:
            org_id = iiko_status.get("organization_id", "default")
            
            # Получаем сводку по номенклатуре
            summary = get_iiko_nomenclature_stats(org_id)
            context += f"\n\nСТАТУС IIKO:\n"
            context += f"- Подключено к: {iiko_status.get('organization_name', 'Организация')}\n"
            context += f"- Продуктов в базе: {summary.get('total_products', 0)}\n"
            context += f"- Групп: {summary.get('total_groups', 0)}\n"
            
            # Если есть поисковый запрос - ищем продукты
            search_terms = extract_search_terms(user_query)
            if search_terms:
                for term in search_terms:
                    products = search_iiko_products(term, org_id, limit=5)
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
        client = OpenAIClient(api_key=settings.OPENAI_API_KEY)
        
        from datetime import datetime
        current_date = datetime.now().strftime("%d %B %Y")
        
        system_prompt = f"""Ты — RECEPTOR, экспертный AI-копайлот для ресторанного бизнеса.

СЕГОДНЯ: {current_date}

ПРАВИЛА:
1. Профиль заведения — внутренний контекст. Не упоминай его в каждом ответе.
2. Используй предоставленный контекст, но не цитируй [Источник] если это не техническая документация.
3. Нет информации — скажи прямо, предложи поискать в интернете.
4. По делу, без воды.

ЭКСПЕРТИЗА: Ресторанный бизнес, HACCP, финансы, маркетинг, iiko.

ФОРМАТ: Русский, структурно, лаконично."""

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
        
        return {
            "role": "assistant", 
            "content": response,
            "model": model_used,  # Показываем какая модель ответила
            "usage": usage_info
        }
        
    except Exception as e:
        print(f"❌ Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
