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
    return {"status": "completed", "data": research}


async def run_deep_research_task(venue_name: str, city: str, user_id: str):
    """
    Фоновая задача для deep research
    """
    try:
        from app.services.venue_research import conduct_deep_research
        from app.services.web_search import web_search
        from app.services.llm.client import OpenAIClient
        from app.core.config import settings
        
        logger.info(f"🔬 Running deep research for {venue_name}...")
        
        # Создаём клиентов
        llm_client = OpenAIClient(api_key=settings.OPENAI_API_KEY)
        
        # Проводим исследование
        dossier = await conduct_deep_research(
            venue_name=venue_name,
            city=city,
            web_search_func=web_search,
            llm_client=llm_client
        )
        
        # Добавляем user_id
        dossier["user_id"] = user_id
        
        # Сохраняем в MongoDB
        collection = db.get_collection(RESEARCH_COLLECTION)
        collection.update_one(
            {"user_id": user_id},
            {"$set": dossier},
            upsert=True
        )
        
        logger.info(f"✅ Deep research completed and saved for {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Deep research failed: {e}", exc_info=True)

