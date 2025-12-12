"""
API эндпоинты для профиля заведения + Deep Research
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import logging

from app.core.database import db
from app.models.venue_profile import (
    VenueProfile, 
    VenueProfileUpdate,
    VENUE_TYPES,
    CUISINE_TYPES,
    SKILL_LEVELS,
    REGIONS,
)

logger = logging.getLogger(__name__)
router = APIRouter()

COLLECTION_NAME = "venue_profiles"
RESEARCH_COLLECTION = "venue_research_context"


class DeepResearchRequest(BaseModel):
    venue_name: str
    city: str
    user_id: str


@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_venue_profile(user_id: str):
    """
    Получить профиль заведения пользователя
    """
    collection = db.get_collection(COLLECTION_NAME)
    profile = collection.find_one({"user_id": user_id})
    
    if not profile:
        # Возвращаем пустой профиль с дефолтами
        return {
            "user_id": user_id,
            "venue_name": None,
            "venue_type": None,
            "venue_concept": None,
            "cuisine_focus": [],
            "cuisine_style": None,
            "average_check": None,
            "target_audience": None,
            "city": None,
            "region": "moskva",
            "kitchen_equipment": [],
            "staff_skill_level": "medium",
            "special_requirements": [],
            "dietary_options": [],
            "venue_description": None,
            "seating_capacity": None,
            "staff_count": None,
            "created_at": None,
            "updated_at": None,
        }
    
    # Убираем MongoDB _id
    profile.pop("_id", None)
    return profile


@router.post("/{user_id}", response_model=Dict[str, Any])
async def update_venue_profile(user_id: str, profile_data: VenueProfileUpdate):
    """
    Создать или обновить профиль заведения
    """
    collection = db.get_collection(COLLECTION_NAME)
    
    # Получаем существующий профиль или создаём новый
    existing = collection.find_one({"user_id": user_id})
    
    now = datetime.utcnow()
    
    if existing:
        # Обновляем только переданные поля
        update_data = {k: v for k, v in profile_data.model_dump().items() if v is not None}
        update_data["updated_at"] = now
        
        collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        # Возвращаем обновлённый профиль
        updated = collection.find_one({"user_id": user_id})
        updated.pop("_id", None)
        return updated
    else:
        # Создаём новый профиль
        new_profile = {
            "user_id": user_id,
            **profile_data.model_dump(),
            "created_at": now,
            "updated_at": now,
        }
        
        collection.insert_one(new_profile)
        new_profile.pop("_id", None)
        return new_profile


@router.get("/dictionaries/all", response_model=Dict[str, Any])
async def get_dictionaries():
    """
    Получить справочники для UI (типы заведений, кухонь и т.д.)
    """
    return {
        "venue_types": VENUE_TYPES,
        "cuisine_types": CUISINE_TYPES,
        "skill_levels": SKILL_LEVELS,
        "regions": REGIONS,
    }


@router.post("/research/start")
async def start_deep_research(request: DeepResearchRequest, background_tasks: BackgroundTasks):
    """
    Запускает глубокое исследование заведения в фоне
    """
    logger.info(f"🔬 Deep research requested: {request.venue_name}, {request.city}")
    
    # Запускаем в фоне
    background_tasks.add_task(
        run_deep_research_task,
        request.venue_name,
        request.city,
        request.user_id
    )
    
    return {
        "status": "started",
        "message": f"Исследование заведения '{request.venue_name}' запущено. Это займёт 1-2 минуты.",
        "venue_name": request.venue_name,
        "city": request.city,
        "user_id": request.user_id
    }


@router.get("/research/status/{user_id}")
async def get_deep_research(user_id: str):
    """
    Получить результаты deep research для пользователя
    """
    collection = db.get_collection(RESEARCH_COLLECTION)
    research = collection.find_one({"user_id": user_id})
    
    if not research:
        return {"status": "not_found", "message": "Исследование не найдено"}
    
    research.pop("_id", None)
    
    # Форматируем данные для удобного отображения
    formatted_research = format_research_for_display(research)
    
    return {"status": "completed", "data": formatted_research}


def format_research_for_display(research: Dict[str, Any]) -> Dict[str, Any]:
    """
    Форматирует данные исследования для красивого отображения
    """
    # Убедимся, что все списки существуют
    formatted = {
        "venue_name": research.get("venue_name", ""),
        "city": research.get("city", ""),
        "research_date": research.get("research_date", datetime.utcnow().isoformat()),
        "status": research.get("status", "completed"),
        
        # Основная информация
        "summary": research.get("summary", "Информация о заведении собирается..."),
        "positioning": research.get("positioning", ""),
        
        # Метрики
        "price_segment": research.get("price_segment", "unknown"),
        "avg_check_estimate": research.get("avg_check_estimate", "unknown"),
        "rating_estimate": research.get("rating_estimate", "unknown"),
        
        # SWOT анализ - убеждаемся, что это списки
        "strengths": research.get("strengths") or [],
        "weaknesses": research.get("weaknesses") or [],
        "opportunities": research.get("opportunities") or [],
        "threats": research.get("threats") or [],
        
        # Дополнительная информация
        "popular_items": research.get("popular_items") or [],
        "competitors": research.get("competitors") or [],
        
        # Статистика источников
        "raw_sources": research.get("raw_sources", {})
    }
    
    # Убедимся, что все списки действительно списки
    for key in ["strengths", "weaknesses", "opportunities", "threats", "popular_items", "competitors"]:
        if not isinstance(formatted[key], list):
            formatted[key] = []
    
    return formatted


async def run_deep_research_task(venue_name: str, city: str, user_id: str):
    """
    Фоновая задача для deep research
    """
    try:
        from app.services.venue_research import conduct_deep_research
        from app.services.web_search import web_search
        from app.services.llm.unified_client import UnifiedLLMClient
        from app.core.config import settings
        
        logger.info(f"🔬 Running deep research for {venue_name} (user: {user_id})...")
        
        # Создаём клиентов (OpenRouter приоритет, OpenAI fallback)
        llm_client = UnifiedLLMClient(
            openrouter_key=settings.OPENROUTER_API_KEY,
            openai_key=settings.OPENAI_API_KEY
        )
        
        # Проводим исследование
        dossier = await conduct_deep_research(
            venue_name=venue_name,
            city=city,
            web_search_func=web_search,
            llm_client=llm_client
        )
        
        logger.info(f"✅ Research data collected, saving to DB...")
        
        # Добавляем user_id и статус
        dossier["user_id"] = user_id
        dossier["status"] = "completed"
        
        # Сохраняем в MongoDB
        collection = db.get_collection(RESEARCH_COLLECTION)
        result = collection.update_one(
            {"user_id": user_id},
            {"$set": dossier},
            upsert=True
        )
        
        logger.info(f"✅ Deep research saved: matched={result.matched_count}, modified={result.modified_count}, upserted_id={result.upserted_id}")
        logger.info(f"📊 Dossier summary: {dossier.get('summary', 'N/A')[:100]}")
        
    except Exception as e:
        logger.error(f"❌ Deep research failed for {user_id}: {e}", exc_info=True)
        
        # Сохраняем хотя бы ошибку
        try:
            collection = db.get_collection(RESEARCH_COLLECTION)
            collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "venue_name": venue_name,
                    "city": city,
                    "status": "failed",
                    "error": str(e),
                    "research_date": datetime.utcnow().isoformat()
                }},
                upsert=True
            )
        except Exception as save_err:
            logger.error(f"❌ Failed to save error state: {save_err}")

