"""
Chat API для RECEPTOR CO-PILOT
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.llm.client import OpenAIClient
from app.services.rag.search import search_knowledge_base
from app.core.config import settings
from app.core.database import db

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
        print(f"📊 Querying iiko for: {user_query}")
        context += "\n\nДАННЫЕ IIKO: [Интеграция с iiko будет добавлена]\n"

    # Call LLM
    try:
        client = OpenAIClient(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = """Ты — RECEPTOR, экспертный AI-копайлот для ресторанного бизнеса.

Твоя цель — помогать рестораторам, шеф-поварам и менеджерам эффективно управлять бизнесом.

У тебя есть доступ к глубокой базе знаний:
- Стандарты HACCP и СанПиН (актуальные на 2025 год)
- HR-практики для ресторанного бизнеса
- Финансы и фудкост
- Маркетинг и SMM

Ты также можешь:
- Генерировать технологические карты
- Анализировать данные iiko
- Давать рекомендации по оптимизации бизнеса

ВАЖНО:
- Отвечай всегда на русском языке
- Учитывай контекст заведения пользователя при ответах
- Если не знаешь ответа, честно скажи об этом и предложи, как можно найти информацию
- Будь конкретным и практичным в советах"""

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
    
    # База знаний
    if any(w in query for w in ["haccp", "санпин", "норм", "правил", "закон", "hr", "найм", "зарплат", "маркетинг", "smm", "гигиен", "требован"]):
        return "knowledge_base"
    
    # iiko аналитика
    if any(w in query for w in ["выручк", "продаж", "фудкост", "iiko", "айко", "отчет", "аналитик", "статистик"]):
        return "iiko_analytics"
    
    return "general"
