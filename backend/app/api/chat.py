"""
Chat API для RECEPTOR CO-PILOT
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.llm.client import OpenAIClient
from app.services.rag.search import search_knowledge_base
from app.services.iiko.iiko_rms_service import get_iiko_rms_service
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


def build_venue_context(profile: Dict[str, Any]) -> str:
    """Построить контекст заведения для промпта"""
    if not profile:
        return ""
    
    parts = []
    
    if profile.get("venue_name"):
        parts.append(f"Название заведения: {profile['venue_name']}")
    
    if profile.get("venue_type"):
        parts.append(f"Тип: {profile['venue_type']}")
    
    if profile.get("cuisine_focus"):
        cuisines = ", ".join(profile["cuisine_focus"])
        parts.append(f"Кухня: {cuisines}")
    
    if profile.get("average_check"):
        parts.append(f"Средний чек: {profile['average_check']} руб.")
    
    if profile.get("city"):
        parts.append(f"Город: {profile['city']}")
    
    if profile.get("seating_capacity"):
        parts.append(f"Посадочных мест: {profile['seating_capacity']}")
    
    if profile.get("staff_count"):
        parts.append(f"Сотрудников: {profile['staff_count']}")
    
    if profile.get("staff_skill_level"):
        parts.append(f"Уровень персонала: {profile['staff_skill_level']}")
    
    if profile.get("special_requirements"):
        reqs = ", ".join(profile["special_requirements"])
        parts.append(f"Особые требования: {reqs}")
    
    if profile.get("venue_description"):
        parts.append(f"Описание: {profile['venue_description']}")
    
    if not parts:
        return ""
    
    return "ПРОФИЛЬ ЗАВЕДЕНИЯ ПОЛЬЗОВАТЕЛЯ:\n" + "\n".join(parts)


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
    
    # Загружаем профиль заведения
    venue_profile = get_venue_profile(user_id)
    venue_context = build_venue_context(venue_profile)
    
    # Simple Intent Detection
    intent = detect_intent(user_query)
    
    context = ""
    
    # Добавляем контекст заведения
    if venue_context:
        context += f"\n\n{venue_context}\n"
    
    if intent == "knowledge_base":
        print(f"🔍 Searching Knowledge Base for: {user_query}")
        results = search_knowledge_base(user_query, top_k=3)
        if results:
            context += "\n\nРЕЛЕВАНТНАЯ ИНФОРМАЦИЯ ИЗ БАЗЫ ЗНАНИЙ:\n"
            for res in results:
                context += f"- {res['content'][:500]}...\n"
                
    elif intent == "iiko_analytics":
        logger.info(f"📊 Querying iiko for: {user_query}")
        
        # Проверяем подключение iiko
        iiko_status = get_iiko_connection_status(user_id)
        
        if iiko_status.get("status") in ["connected", "restored"]:
            org_id = iiko_status.get("organization_id", "default")
            
            # Получаем сводку по номенклатуре
            summary = get_iiko_products_summary(org_id)
            context += f"\n\nСТАТУС IIKO:\n"
            context += f"- Подключено к: {iiko_status.get('organization_name', 'Организация')}\n"
            context += f"- Продуктов в базе: {summary['products_count']}\n"
            context += f"- Групп: {summary['groups_count']}\n"
            
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
        
        system_prompt = """Ты — RECEPTOR, экспертный AI-копайлот для ресторанного бизнеса.

Твоя цель — помогать рестораторам, шеф-поварам и менеджерам эффективно управлять бизнесом.

ТВОИ ВОЗМОЖНОСТИ:

1. БАЗА ЗНАНИЙ:
   - Стандарты HACCP и СанПиН (актуальные на 2025 год)
   - HR-практики для ресторанного бизнеса
   - Финансы и фудкост
   - Маркетинг и SMM

2. ИНТЕГРАЦИЯ С IIKO:
   - Поиск продуктов и ингредиентов в номенклатуре
   - Информация о ценах и артикулах
   - Аналитика по синхронизированным данным
   
3. ГЕНЕРАЦИЯ:
   - Технологические карты
   - Рекомендации по оптимизации

ВАЖНО:
- Отвечай всегда на русском языке
- Учитывай контекст заведения пользователя при ответах
- Если в контексте есть данные из iiko - используй их в ответе
- Если не знаешь ответа, честно скажи об этом
- Будь конкретным и практичным в советах
- Форматируй ответы для удобного чтения (списки, заголовки)"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context to the last user message
        final_user_message = request.messages[-1].content
        if context:
            final_user_message += f"\n\nКОНТЕКСТ:{context}"
            
        # Add history (excluding the last one which we just modified)
        for msg in request.messages[:-1]:
            messages.append({"role": msg.role, "content": msg.content})
            
        messages.append({"role": "user", "content": final_user_message})
        
        response = await client.chat_completion(
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        return {"role": "assistant", "content": response}
        
    except Exception as e:
        print(f"❌ Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def detect_intent(query: str) -> str:
    """Определение намерения пользователя"""
    query_lower = query.lower()
    
    # База знаний (HACCP, СанПиН, HR и т.д.)
    kb_keywords = ["haccp", "санпин", "норм", "правил", "закон", "hr", "найм", "зарплат", 
                   "маркетинг", "smm", "гигиен", "требован", "сертифик", "лицен"]
    if any(w in query_lower for w in kb_keywords):
        return "knowledge_base"
    
    # Категории/группы в iiko
    category_keywords = ["категори", "группы", "группа", "раздел", "все пив", "все бургер", 
                        "все напитк", "меню", "ассортимент", "покажи все"]
    if any(w in query_lower for w in category_keywords):
        return "iiko_categories"
    
    # Статистика номенклатуры
    stats_keywords = ["сколько позиций", "сколько товар", "статистик", "сколько продукт",
                     "сколько в номенклатуре", "топ групп", "топ категор"]
    if any(w in query_lower for w in stats_keywords):
        return "iiko_stats"
    
    # Поиск продуктов в iiko
    search_keywords = ["найди", "поищи", "есть ли", "ингредиент", "продукт", 
                      "сколько стоит", "какая цена", "артикул", "покажи"]
    if any(w in query_lower for w in search_keywords):
        return "iiko_products"
    
    # iiko общая аналитика
    iiko_keywords = ["выручк", "продаж", "фудкост", "iiko", "айко", "отчет", "аналитик", "синхрониз"]
    if any(w in query_lower for w in iiko_keywords):
        return "iiko_analytics"
    
    return "general"


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
