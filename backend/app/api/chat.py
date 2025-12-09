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
        return rms_service.get_rms_connection_status(user_id=user_id, auto_restore=False)
    except Exception as e:
        logger.error(f"Error checking iiko status: {e}")
        return {"status": "error"}


def search_iiko_products(query: str, organization_id: str = "default", limit: int = 5) -> List[Dict[str, Any]]:
    """Поиск продуктов в номенклатуре iiko"""
    try:
        rms_service = get_iiko_rms_service()
        results = rms_service.search_rms_products_enhanced(
            organization_id=organization_id,
            query=query,
            limit=limit
        )
        return results
    except Exception as e:
        logger.error(f"Error searching iiko products: {e}")
        return []


def get_iiko_products_summary(organization_id: str = "default") -> Dict[str, Any]:
    """Получить сводку по номенклатуре iiko"""
    try:
        rms_service = get_iiko_rms_service()
        
        # Подсчитать продукты
        products_count = rms_service.products.count_documents({"organization_id": organization_id})
        groups_count = rms_service.groups.count_documents({"organization_id": organization_id})
        
        # Получить последний статус синхронизации
        sync_status = rms_service.get_rms_sync_status(organization_id=organization_id)
        
        return {
            "products_count": products_count,
            "groups_count": groups_count,
            "last_sync": sync_status.get("completed_at"),
            "sync_status": sync_status.get("status", "never_synced")
        }
    except Exception as e:
        logger.error(f"Error getting iiko summary: {e}")
        return {"products_count": 0, "groups_count": 0}


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
                        price = p.get('price_per_unit', 0)
                        price_str = f"{price:.2f} руб/{p.get('unit', 'ед')}" if price else "цена не указана"
                        context += f"- {p['name']} | {price_str} | группа: {p.get('group_name', 'н/д')}\n"
                else:
                    context += f"\n\nПо запросу '{term}' ничего не найдено в номенклатуре.\n"
        else:
            context += "\n\nДля поиска продуктов нужно подключить iiko в разделе 'Интеграции'.\n"

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
    query = query.lower()
    
    # База знаний (HACCP, СанПиН, HR и т.д.)
    if any(w in query for w in ["haccp", "санпин", "норм", "правил", "закон", "hr", "найм", "зарплат", "маркетинг", "smm", "гигиен", "требован"]):
        return "knowledge_base"
    
    # Поиск продуктов в iiko
    if any(w in query for w in ["найди", "поищи", "есть ли", "ингредиент", "продукт", "номенклатур", "сколько стоит", "какая цена", "артикул"]):
        return "iiko_products"
    
    # iiko аналитика и статус
    if any(w in query for w in ["выручк", "продаж", "фудкост", "iiko", "айко", "отчет", "аналитик", "статистик", "синхрониз"]):
        return "iiko_analytics"
    
    return "general"
