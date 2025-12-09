"""
Модель профиля заведения
Содержит информацию о ресторане пользователя для персонализации ответов ассистента
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class VenueProfile(BaseModel):
    """Полный профиль заведения"""
    
    # Идентификаторы
    user_id: str
    
    # Базовая информация о заведении
    venue_name: Optional[str] = Field(None, description="Название заведения")
    venue_type: Optional[str] = Field(None, description="Тип заведения: restaurant, cafe, bar, fastfood, canteen, catering")
    venue_concept: Optional[str] = Field(None, description="Концепция заведения")
    
    # Кухня и меню
    cuisine_focus: List[str] = Field(default_factory=list, description="Направления кухни: russian, european, asian, etc.")
    cuisine_style: Optional[str] = Field(None, description="Стиль кухни: classic, modern, fusion, street")
    average_check: Optional[int] = Field(None, description="Средний чек в рублях")
    
    # Аудитория
    target_audience: Optional[str] = Field(None, description="Целевая аудитория")
    
    # Локация
    city: Optional[str] = Field(None, description="Город")
    region: Optional[str] = Field("moskva", description="Регион: moskva, spb, etc.")
    
    # Кухонные возможности
    kitchen_equipment: List[str] = Field(default_factory=list, description="Оборудование кухни")
    staff_skill_level: Optional[str] = Field("medium", description="Уровень персонала: novice, medium, advanced, expert")
    
    # Бизнес-требования
    special_requirements: List[str] = Field(default_factory=list, description="Особые требования: halal, kosher, vegan_friendly")
    dietary_options: List[str] = Field(default_factory=list, description="Диетические опции: vegetarian, vegan, gluten_free")
    
    # Дополнительно
    venue_description: Optional[str] = Field(None, description="Описание заведения своими словами")
    seating_capacity: Optional[int] = Field(None, description="Количество посадочных мест")
    staff_count: Optional[int] = Field(None, description="Количество сотрудников")
    
    # Метаданные
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class VenueProfileUpdate(BaseModel):
    """Модель для обновления профиля (все поля опциональные)"""
    
    venue_name: Optional[str] = None
    venue_type: Optional[str] = None
    venue_concept: Optional[str] = None
    cuisine_focus: Optional[List[str]] = None
    cuisine_style: Optional[str] = None
    average_check: Optional[int] = None
    target_audience: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    kitchen_equipment: Optional[List[str]] = None
    staff_skill_level: Optional[str] = None
    special_requirements: Optional[List[str]] = None
    dietary_options: Optional[List[str]] = None
    venue_description: Optional[str] = None
    seating_capacity: Optional[int] = None
    staff_count: Optional[int] = None


# Справочники для UI
VENUE_TYPES = {
    "restaurant": "Ресторан",
    "cafe": "Кафе",
    "bar": "Бар",
    "fastfood": "Фастфуд",
    "canteen": "Столовая",
    "catering": "Кейтеринг",
    "coffeeshop": "Кофейня",
    "bakery": "Пекарня",
    "pizzeria": "Пиццерия",
}

CUISINE_TYPES = {
    "russian": "Русская",
    "european": "Европейская",
    "italian": "Итальянская",
    "asian": "Азиатская",
    "japanese": "Японская",
    "chinese": "Китайская",
    "georgian": "Грузинская",
    "uzbek": "Узбекская",
    "american": "Американская",
    "mexican": "Мексиканская",
    "french": "Французская",
    "mediterranean": "Средиземноморская",
    "fusion": "Фьюжн",
    "pan_asian": "Паназиатская",
}

SKILL_LEVELS = {
    "novice": "Начинающий",
    "medium": "Средний",
    "advanced": "Продвинутый",
    "expert": "Эксперт",
}

REGIONS = {
    "moskva": "Москва",
    "spb": "Санкт-Петербург",
    "krasnodar": "Краснодар",
    "sochi": "Сочи",
    "kazan": "Казань",
    "novosibirsk": "Новосибирск",
    "ekaterinburg": "Екатеринбург",
    "other": "Другой регион",
}

