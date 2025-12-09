"""
API эндпоинты для профиля заведения
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

from app.core.database import db
from app.models.venue_profile import (
    VenueProfile, 
    VenueProfileUpdate,
    VENUE_TYPES,
    CUISINE_TYPES,
    SKILL_LEVELS,
    REGIONS,
)

router = APIRouter()

COLLECTION_NAME = "venue_profiles"


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

