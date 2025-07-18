from fastapi import FastAPI, APIRouter, HTTPException, File, Form, UploadFile
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import openai
from openai import OpenAI
import json
import re
import tempfile
import pandas as pd

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "monthly_tech_cards": 3,
        "features": [
            "3 техкарты в месяц",
            "Базовые рецепты",
            "Экспорт в PDF",
            "Поддержка email"
        ],
        "kitchen_equipment": False,
        "ai_editing": True,
        "voice_input": True,
        "price_calculation": True
    },
    "starter": {
        "name": "Starter",
        "price": 990,
        "monthly_tech_cards": 25,
        "features": [
            "25 техкарт в месяц",
            "Все возможности Free",
            "Расширенные рецепты",
            "Приоритетная поддержка",
            "История техкарт"
        ],
        "kitchen_equipment": False,
        "ai_editing": True,
        "voice_input": True,
        "price_calculation": True
    },
    "pro": {
        "name": "PRO",
        "price": 2990,
        "monthly_tech_cards": -1,  # unlimited
        "features": [
            "Неограниченные техкарты",
            "Все возможности Starter",
            "🔥 Адаптация под оборудование",
            "Премиум AI-алгоритмы",
            "Расширенная аналитика",
            "Персональный менеджер"
        ],
        "kitchen_equipment": True,
        "ai_editing": True,
        "voice_input": True,
        "price_calculation": True
    },
    "business": {
        "name": "Business",
        "price": 7990,
        "monthly_tech_cards": -1,  # unlimited
        "features": [
            "Все возможности PRO",
            "Командная работа",
            "Интеграция с POS",
            "Корпоративная поддержка",
            "Индивидуальные настройки",
            "Обучение персонала"
        ],
        "kitchen_equipment": True,
        "ai_editing": True,
        "voice_input": True,
        "price_calculation": True,
        "team_features": True
    }
}

# Kitchen Equipment Types
KITCHEN_EQUIPMENT = {
    "cooking_methods": [
        {"id": "gas_stove", "name": "Газовая плита", "category": "cooking"},
        {"id": "electric_stove", "name": "Электрическая плита", "category": "cooking"},
        {"id": "induction_stove", "name": "Индукционная плита", "category": "cooking"},
        {"id": "convection_oven", "name": "Конвекционная печь", "category": "cooking"},
        {"id": "steam_oven", "name": "Пароконвектомат", "category": "cooking"},
        {"id": "grill", "name": "Гриль", "category": "cooking"},
        {"id": "fryer", "name": "Фритюрница", "category": "cooking"},
        {"id": "salamander", "name": "Саламандра", "category": "cooking"},
        {"id": "plancha", "name": "Планча", "category": "cooking"},
        {"id": "wok", "name": "Вок-плита", "category": "cooking"}
    ],
    "prep_equipment": [
        {"id": "food_processor", "name": "Кухонный комбайн", "category": "prep"},
        {"id": "blender", "name": "Блендер", "category": "prep"},
        {"id": "meat_grinder", "name": "Мясорубка", "category": "prep"},
        {"id": "slicer", "name": "Слайсер", "category": "prep"},
        {"id": "vacuum_sealer", "name": "Вакуумный упаковщик", "category": "prep"},
        {"id": "sous_vide", "name": "Су-вид", "category": "prep"},
        {"id": "immersion_blender", "name": "Погружной блендер", "category": "prep"}
    ],
    "storage": [
        {"id": "blast_chiller", "name": "Шокзаморозка", "category": "storage"},
        {"id": "proofer", "name": "Расстоечный шкаф", "category": "storage"},
        {"id": "refrigerator", "name": "Холодильник", "category": "storage"},
        {"id": "freezer", "name": "Морозильник", "category": "storage"}
    ]
}

# Regional price coefficients
REGIONAL_COEFFICIENTS = {
    "moskva": 1.25,
    "spb": 1.25,
    "ekaterinburg": 1.0,
    "novosibirsk": 1.0,
    "irkutsk": 1.0,
    "nizhniy_novgorod": 1.0,
    "kazan": 1.0,
    "chelyabinsk": 1.0,
    "omsk": 1.0,
    "samara": 1.0,
    "rostov": 1.0,
    "ufa": 1.0,
    "krasnoyarsk": 1.0,
    "perm": 1.0,
    "voronezh": 1.0,
    "volgograd": 1.0,
    "krasnodar": 1.0,
    "saratov": 1.0,
    "tyumen": 1.0,
    "tolyatti": 1.0,
    "other": 0.8  # Малые города
}

# Define Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    city: str
    subscription_plan: str = "free"  # free, starter, pro, business
    subscription_start_date: datetime = Field(default_factory=datetime.utcnow)
    monthly_tech_cards_used: int = 0
    monthly_reset_date: datetime = Field(default_factory=datetime.utcnow)
    kitchen_equipment: List[str] = []  # List of equipment IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    name: str
    city: str

class UserSubscription(BaseModel):
    subscription_plan: str
    
class KitchenEquipmentUpdate(BaseModel):
    equipment_ids: List[str]

class DishRequest(BaseModel):
    dish_name: str
    user_id: str

class EditRequest(BaseModel):
    tech_card_id: str
    edit_instruction: str

class IngredientUpdate(BaseModel):
    tech_card_id: str
    ingredient_updates: dict  # {"ingredient_name": {"quantity": 100, "price": 50}}

class TechCard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    dish_name: str
    content: str
    city: Optional[str] = None
    is_inspiration: Optional[bool] = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class TechCardCreate(BaseModel):
    user_id: str
    dish_name: str
    content: str

# Golden prompt for tech cards
GOLDEN_PROMPT = """Ты — RECEPTOR, профессиональный AI-помощник для шеф-поваров и рестораторов.

Пользователь вводит название блюда или идею. Сгенерируй полную технологическую карту (ТК) строго по формату ниже.

ВАЖНО: 
- Если в названии есть явные опечатки или неправильные слова (например "Бранч" вместо "соус"), исправь их на правильные кулинарные термины.
- НЕ МЕНЯЙ основные ингредиенты при редактировании! Если пользователь пишет "морж", НЕ заменяй на "морской гребешок".

────────────────────────────────────
📌 ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА
────────────────────────────────────
• Если в названии есть соус/техника («песто», «терияки», «рамэн» и т.д.) — отрази это в рецепте.
Не подменяй и не упрощай.

- Учитывай ужарку/утайку (мясо, рыба 20–30 %, картофель 20 %, грибы/лук до 50 %).
Указывай сырой вес, %, выход.

- ПРАВИЛА ЦЕНООБРАЗОВАНИЯ:
  * Рассчитывай ПРАВИЛЬНЫЕ РЕСТОРАННЫЕ ПОРЦИИ:
    • Основное блюдо: 200-300г
    • Закуска: 150-200г  
    • Десерт: 80-120г (2-3 пряника, 1 кусочек торта)
    • Суп: 250-300мл
  * Ингредиенты указывай сразу на одну порцию, не на килограммы!
  * Примеры правильных количеств ингредиентов на одну порцию:
    - Мясо/рыба основное: 150-200г
    - Гарнир (картофель, рис): 100-150г  
    - Овощи для салата: 80-120г
    - Соус: 30-50мл
    - Специи: 1-5г
  * Базовые цены: средние рыночные цены по России на 2024 год + инфляция 12%
  * Региональный коэффициент: {regional_coefficient}x
  * Формула расчета: (Базовая цена 2024 год × 1.12 × региональный коэффициент)
  * Учитывай сезонность и качество продукта, но основывайся на формуле выше
    
  * Будь реалистичен в ценах - это обычный ресторан среднего уровня, не элитный!

- Себестоимость = только ингредиенты (без накладных).
- Рекомендуемая цена = себестоимость × 3 (стандартная ресторанная наценка).
- ЦЕЛЬ: Итоговая цена должна быть адекватной для меню ресторана среднего уровня.

ВАЖНО ПО РАСЧЕТАМ:
- ТОЧНО рассчитывай цены: 100г сливочного масла при 450₽/кг = 45₽ (НЕ 450₽!)
- ПРОВЕРЯЙ математику: если мука 60₽/кг, то 300г = 18₽
- Общая себестоимость десерта 80-120г должна быть 40-80₽
- Основного блюда 200-300г должна быть 100-200₽

- ОБЯЗАТЕЛЬНО включай в себестоимость и в итоговый выход всё, что реально идёт на порцию:
– растительные и сливочные масла, если их > 5 мл на порцию (для жарки / эмульсий);
– порцию соуса, даже если сам соус вынесен в отдельную ТК.
В ингредиентах укажи строку вида
«Соус [название] — [количество] г (см. ТК "Соус [название]") — ~[цена] ₽».
НО: используй только ПРОСТЫЕ соусы (томатный, сливочный, грибной), избегай сложных французских соусов типа демигляс, эспаньол, велюте для простых блюд.

- Итоговый вес («Выход») = сумма всех компонентов после термообработки
(белок + гарнир + соус). Соус 50 г ⇒ добавь его в выход, цену и КБЖУ.

────────────────────────────────────
🧩 ПОЛУФАБРИКАТЫ | ЗАГОТОВКИ
────────────────────────────────────
— Готовые массовые продукты (соус терияки, соевый соус, кетчуп) — указывай как «покупной», цену включай.

— Для большинства блюд используй ПРОСТЫЕ ингредиенты (соль, перец, масло, базовые продукты).
— Избегай сложных французских соусов (демигляс, эспаньол, велюте) для простых блюд.
— Если действительно нужен сложный соус, укажи: «Соус [название] — [количество] г (см. отдельную ТК)»;
— НЕ расписывай процесс сложных соусов;
— добавь фразу: «Запросите отдельную ТК, если нужно».

────────────────────────────────────
📋 ФОРМАТ ВЫДАЧИ
────────────────────────────────────
**Название:** …

**Категория:** закуска / основное / десерт

**Описание:** 2-3 сочных предложения (вкус, аромат, текстура).

**Ингредиенты:** (указывай НА ОДНУ ПОРЦИЮ!)

- Продукт — кол-во (сырой) — ~цена
- *Ужарка/утайка:* «… — 100 г (ужарка 30 %, выход 70 г)»

**Пошаговый рецепт:**

1. … (темпы, время, лайфхаки)
2. …
3. …

**Время:** Подготовка XX мин | Готовка XX мин | ИТОГО XX мин

**Выход:** XXX г готового блюда (учтена ужарка)

**Порция:** XX г (одна порция)

**Себестоимость:**

- По ингредиентам: XXX ₽
- Себестоимость 1 порции: XX ₽
- Рекомендуемая цена (×3): XXX ₽

**КБЖУ на 1 порцию:** Калории … ккал | Б … г | Ж … г | У … г

**КБЖУ на 100 г:** Калории … ккал | Б … г | Ж … г | У … г

**Аллергены:** … + (веган / безглютен и т.п.)

**Заготовки и хранение:**

- Что можно подготовить заранее с указанием сроков и условий
- Температурные режимы хранения (+2°C, +18°C, комнатная)
- Сроки годности каждого компонента
- Профессиональные лайфхаки для сохранения качества
- Особенности заморозки и разморозки (если применимо)
- Контейнеры и упаковка для хранения

**Особенности и советы от шефа:**

- техника / текстура / баланс
*Совет от RECEPTOR:* …
*Фишка для продвинутых:* …
*Вариации:* …

**Рекомендация подачи:** посуда, декор, температура

**Теги для меню:** #[тег1] #[тег2] #[тег3]

Сгенерировано RECEPTOR AI — экономьте 2 часа на каждой техкарте

────────────────────────────────────

Название блюда: {dish_name}

Важно: учти региональный коэффициент цен: {regional_coefficient}x от базовых цен."""

# Edit prompt for tech cards
EDIT_PROMPT = """Ты — RECEPTOR, профессиональный AI-помощник для шеф-поваров.

Пользователь просит отредактировать существующую техкарту. Вот текущая техкарта:

{current_tech_card}

Инструкция по редактированию: {edit_instruction}

ПРАВИЛА РЕДАКТИРОВАНИЯ:
- Сохрани весь оригинальный формат техкарты
- Внеси только запрошенные изменения
- Пересчитай все цены и количества корректно
- Учти региональный коэффициент: {regional_coefficient}x
- Обнови себестоимость и рекомендуемую цену
- Если изменяется количество ингредиентов, пересчитай КБЖУ и выход
- Сохрани все разделы: ингредиенты, рецепт, время, КБЖУ, советы и т.д.

Верни отредактированную техкарту в том же формате."""

# Utility functions
def reset_monthly_usage_if_needed(user_data):
    """Reset monthly usage if a month has passed"""
    current_date = datetime.utcnow()
    reset_date = user_data.get("monthly_reset_date", current_date)
    
    if isinstance(reset_date, str):
        reset_date = datetime.fromisoformat(reset_date.replace('Z', '+00:00'))
    
    if current_date >= reset_date:
        # Reset monthly usage
        next_reset = current_date.replace(day=1)
        if next_reset.month == 12:
            next_reset = next_reset.replace(year=next_reset.year + 1, month=1)
        else:
            next_reset = next_reset.replace(month=next_reset.month + 1)
        
        return {
            "monthly_tech_cards_used": 0,
            "monthly_reset_date": next_reset
        }
    
    return {}

def check_tech_card_limit(user_data):
    """Check if user can create another tech card"""
    subscription_plan = user_data.get("subscription_plan", "free")
    plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
    
    # Unlimited plans
    if plan_info["monthly_tech_cards"] == -1:
        return True, ""
    
    # Check monthly limit
    monthly_used = user_data.get("monthly_tech_cards_used", 0)
    monthly_limit = plan_info["monthly_tech_cards"]
    
    if monthly_used >= monthly_limit:
        return False, f"Достигнут лимит {monthly_limit} техкарт в месяц. Обновите подписку для продолжения."
    
    return True, ""

# Routes
@api_router.get("/subscription-plans")
async def get_subscription_plans():
    """Get all available subscription plans"""
    return SUBSCRIPTION_PLANS

@api_router.get("/kitchen-equipment")
async def get_kitchen_equipment():
    """Get all available kitchen equipment"""
    return KITCHEN_EQUIPMENT

@api_router.get("/user-subscription/{user_id}")
async def get_user_subscription(user_id: str):
    """Get user's current subscription details"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Reset monthly usage if needed
    reset_data = reset_monthly_usage_if_needed(user)
    if reset_data:
        await db.users.update_one(
            {"id": user_id},
            {"$set": reset_data}
        )
        user.update(reset_data)
    
    subscription_plan = user.get("subscription_plan", "free")
    plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
    
    return {
        "subscription_plan": subscription_plan,
        "plan_info": plan_info,
        "monthly_tech_cards_used": user.get("monthly_tech_cards_used", 0),
        "monthly_reset_date": user.get("monthly_reset_date"),
        "kitchen_equipment": user.get("kitchen_equipment", [])
    }

@api_router.post("/upgrade-subscription/{user_id}")
async def upgrade_subscription(user_id: str, subscription_data: UserSubscription):
    """Upgrade user's subscription plan"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_plan = subscription_data.subscription_plan
    if new_plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    # In a real implementation, this would integrate with payment processing
    # For now, we'll just update the subscription
    
    update_data = {
        "subscription_plan": new_plan,
        "subscription_start_date": datetime.utcnow()
    }
    
    # Reset monthly usage when upgrading
    if new_plan != user.get("subscription_plan", "free"):
        update_data["monthly_tech_cards_used"] = 0
        current_date = datetime.utcnow()
        next_reset = current_date.replace(day=1)
        if next_reset.month == 12:
            next_reset = next_reset.replace(year=next_reset.year + 1, month=1)
        else:
            next_reset = next_reset.replace(month=next_reset.month + 1)
        update_data["monthly_reset_date"] = next_reset
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": f"Подписка обновлена до {SUBSCRIPTION_PLANS[new_plan]['name']}"}

@api_router.post("/update-kitchen-equipment/{user_id}")
async def update_kitchen_equipment(user_id: str, equipment_data: KitchenEquipmentUpdate):
    """Update user's kitchen equipment (PRO feature)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has PRO subscription
    subscription_plan = user.get("subscription_plan", "free")
    plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
    
    if not plan_info.get("kitchen_equipment", False):
        raise HTTPException(status_code=403, detail="Kitchen equipment feature requires PRO subscription")
    
    # Validate equipment IDs
    all_equipment_ids = []
    for category in KITCHEN_EQUIPMENT.values():
        all_equipment_ids.extend([eq["id"] for eq in category])
    
    invalid_ids = [eq_id for eq_id in equipment_data.equipment_ids if eq_id not in all_equipment_ids]
    if invalid_ids:
        raise HTTPException(status_code=400, detail=f"Invalid equipment IDs: {invalid_ids}")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"kitchen_equipment": equipment_data.equipment_ids}}
    )
    
    return {"success": True, "message": "Kitchen equipment updated successfully"}

# Routes
@api_router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    try:
        print(f"Received registration data: {user_data}")
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            print(f"User already exists: {user_data.email}")
            raise HTTPException(status_code=400, detail="User already registered")
        
        user_dict = user_data.dict()
        print(f"User dict: {user_dict}")
        
        # Initialize subscription fields
        current_date = datetime.utcnow()
        next_reset = current_date.replace(day=1)
        if next_reset.month == 12:
            next_reset = next_reset.replace(year=next_reset.year + 1, month=1)
        else:
            next_reset = next_reset.replace(month=next_reset.month + 1)
        
        user_dict.update({
            "subscription_plan": "free",
            "subscription_start_date": current_date,
            "monthly_tech_cards_used": 0,
            "monthly_reset_date": next_reset,
            "kitchen_equipment": []
        })
        
        user_obj = User(**user_dict)
        await db.users.insert_one(user_obj.dict())
        return user_obj
        
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

@api_router.get("/user/{email}")
async def get_user(email: str):
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.post("/generate-tech-card")
async def generate_tech_card(request: DishRequest):
    try:
        # Get user to determine regional coefficient and subscription
        user = await db.users.find_one({"id": request.user_id})
        
        # Если пользователь не найден и это тестовый ID, создаем временного пользователя
        if not user and request.user_id.startswith("test_user_"):
            user = {
                "id": request.user_id,
                "email": "test@example.com",
                "name": "Test User",
                "city": request.city if hasattr(request, 'city') else "moscow",
                "subscription_plan": "pro",
                "subscription_status": "active",
                "monthly_tech_cards_used": 0,
                "monthly_reset_date": datetime.utcnow().isoformat(),
                "kitchen_equipment": [],
                "created_at": datetime.utcnow().isoformat()
            }
        elif not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Reset monthly usage if needed
        reset_data = reset_monthly_usage_if_needed(user)
        if reset_data:
            await db.users.update_one(
                {"id": request.user_id},
                {"$set": reset_data}
            )
            user.update(reset_data)
        
        # Check tech card limit
        can_create, limit_message = check_tech_card_limit(user)
        if not can_create:
            raise HTTPException(status_code=403, detail=limit_message)
        
        # Get regional coefficient
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user["city"].lower(), 1.0)
        
        # Get user's kitchen equipment if PRO user
        subscription_plan = user.get("subscription_plan", "free")
        plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
        
        # Prepare equipment context for PRO users
        equipment_context = ""
        if plan_info.get("kitchen_equipment", False):
            user_equipment = user.get("kitchen_equipment", [])
            if user_equipment:
                equipment_names = []
                for category in KITCHEN_EQUIPMENT.values():
                    for equipment in category:
                        if equipment["id"] in user_equipment:
                            equipment_names.append(equipment["name"])
                
                if equipment_names:
                    equipment_context = f"""
                    
ДОСТУПНОЕ ОБОРУДОВАНИЕ:
{', '.join(equipment_names)}

ВАЖНО: Адаптируй рецепт под указанное оборудование. Если есть более эффективные способы приготовления с этим оборудованием, предложи их. Укажи оптимальные температуры и время для каждого вида оборудования."""
        
        # Prepare the prompt with equipment context
        prompt = GOLDEN_PROMPT.format(
            dish_name=request.dish_name,
            regional_coefficient=regional_coefficient
        ) + equipment_context
        
        # Temporarily use GPT-4o-mini for all users to test
        ai_model = "gpt-4o-mini"  # was: "gpt-4o" if user['subscription_plan'] in ['pro', 'business'] else "gpt-4o-mini"
        max_tokens = 3000  # was: 4000 if user['subscription_plan'] in ['pro', 'business'] else 3000
        
        print(f"Using AI model: {ai_model} for user subscription: {user['subscription_plan']}")
        
        # Generate tech card using OpenAI
        response = openai_client.chat.completions.create(
            model=ai_model,
            messages=[
                {"role": "system", "content": "Ты профессиональный AI-помощник для шеф-поваров. Создаешь детальные технологические карты блюд."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        tech_card_content = response.choices[0].message.content
        
        # Save tech card to database
        tech_card = TechCard(
            user_id=request.user_id,
            dish_name=request.dish_name,
            content=tech_card_content
        )
        
        await db.tech_cards.insert_one(tech_card.dict())
        
        # Update user's monthly usage
        await db.users.update_one(
            {"id": request.user_id},
            {"$inc": {"monthly_tech_cards_used": 1}}
        )
        
        return {
            "success": True,
            "tech_card": tech_card_content,
            "id": tech_card.id,
            "monthly_used": user.get("monthly_tech_cards_used", 0) + 1,
            "monthly_limit": plan_info["monthly_tech_cards"]
        }
        
    except Exception as e:
        logger.error(f"Error generating tech card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating tech card: {str(e)}")

@api_router.get("/tech-cards/{user_id}")
async def get_user_tech_cards(user_id: str):
    tech_cards = await db.tech_cards.find({"user_id": user_id}).to_list(100)
    return [TechCard(**card) for card in tech_cards]

@api_router.put("/tech-card/{tech_card_id}")
async def update_tech_card(tech_card_id: str, update_data: dict):
    try:
        content = update_data.get("content", "")
        result = await db.tech_cards.update_one(
            {"id": tech_card_id},
            {"$set": {"content": content, "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Tech card not found")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error updating tech card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating tech card: {str(e)}")

@api_router.post("/edit-tech-card")
async def edit_tech_card(request: EditRequest):
    try:
        # Get the current tech card
        tech_card = await db.tech_cards.find_one({"id": request.tech_card_id})
        if not tech_card:
            raise HTTPException(status_code=404, detail="Tech card not found")
        
        # Get user to determine regional coefficient
        user = await db.users.find_one({"id": tech_card["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get regional coefficient
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user["city"].lower(), 1.0)
        
        # Prepare the edit prompt
        prompt = EDIT_PROMPT.format(
            current_tech_card=tech_card["content"],
            edit_instruction=request.edit_instruction,
            regional_coefficient=regional_coefficient
        )
        
        # Temporarily use GPT-4o-mini for all users to test
        ai_model = "gpt-4o-mini"  # was: "gpt-4o" if user['subscription_plan'] in ['pro', 'business'] else "gpt-4o-mini"
        max_tokens = 3000  # was: 4000 if user['subscription_plan'] in ['pro', 'business'] else 3000
        
        # Generate edited tech card using OpenAI
        response = openai_client.chat.completions.create(
            model=ai_model,
            messages=[
                {"role": "system", "content": "Ты профессиональный AI-помощник для шеф-поваров. Редактируешь технологические карты согласно запросам пользователей."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        edited_content = response.choices[0].message.content
        
        # Update tech card in database
        await db.tech_cards.update_one(
            {"id": request.tech_card_id},
            {"$set": {"content": edited_content, "updated_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "tech_card": edited_content
        }
        
    except Exception as e:
        logger.error(f"Error editing tech card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error editing tech card: {str(e)}")

@api_router.post("/parse-ingredients")
async def parse_ingredients(content: str):
    """Parse ingredients from tech card content for editing"""
    try:
        lines = content.split('\n')
        ingredients = []
        in_ingredients_section = False
        
        for line in lines:
            if line.startswith('**Ингредиенты:**'):
                in_ingredients_section = True
                continue
            elif line.startswith('**') and in_ingredients_section:
                break
            elif in_ingredients_section and line.strip() and line.startswith('- '):
                # Parse ingredient line like "- Мука — 100 г — ~50 ₽"
                parts = line.replace('- ', '').split(' — ')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    quantity = parts[1].strip()
                    price_str = parts[2].replace('~', '').replace('₽', '').strip()
                    try:
                        price = float(price_str)
                        ingredients.append({
                            "name": name,
                            "quantity": quantity,
                            "price": price
                        })
                    except:
                        pass
        
        return {"ingredients": ingredients}
        
    except Exception as e:
        logger.error(f"Error parsing ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error parsing ingredients: {str(e)}")

@api_router.get("/cities")
async def get_cities():
    cities = [
        {"code": "moskva", "name": "Москва", "coefficient": 1.25},
        {"code": "spb", "name": "Санкт-Петербург", "coefficient": 1.25},
        {"code": "ekaterinburg", "name": "Екатеринбург", "coefficient": 1.0},
        {"code": "novosibirsk", "name": "Новосибирск", "coefficient": 1.0},
        {"code": "irkutsk", "name": "Иркутск", "coefficient": 1.0},
        {"code": "nizhniy_novgorod", "name": "Нижний Новгород", "coefficient": 1.0},
        {"code": "kazan", "name": "Казань", "coefficient": 1.0},
        {"code": "chelyabinsk", "name": "Челябинск", "coefficient": 1.0},
        {"code": "omsk", "name": "Омск", "coefficient": 1.0},
        {"code": "samara", "name": "Самара", "coefficient": 1.0},
        {"code": "rostov", "name": "Ростов-на-Дону", "coefficient": 1.0},
        {"code": "ufa", "name": "Уфа", "coefficient": 1.0},
        {"code": "krasnoyarsk", "name": "Красноярск", "coefficient": 1.0},
        {"code": "perm", "name": "Пермь", "coefficient": 1.0},
        {"code": "voronezh", "name": "Воронеж", "coefficient": 1.0},
        {"code": "volgograd", "name": "Волгоград", "coefficient": 1.0},
        {"code": "krasnodar", "name": "Краснодар", "coefficient": 1.0},
        {"code": "saratov", "name": "Саратов", "coefficient": 1.0},
        {"code": "tyumen", "name": "Тюмень", "coefficient": 1.0},
        {"code": "tolyatti", "name": "Тольятти", "coefficient": 1.0},
        {"code": "other", "name": "Другой город", "coefficient": 0.8}
    ]
    return cities

@app.post("/api/upload-prices")
async def upload_prices(file: UploadFile = File(...), user_id: str = Form(...)):
    # Auto-create test user with PRO subscription if needed
    if user_id.startswith("test_user_"):
        user = await db.users.find_one({"id": user_id})
        if not user:
            # Create test user with PRO subscription
            test_user = {
                "id": user_id,
                "email": f"{user_id}@example.com",
                "name": "Test User",
                "city": "moskva",
                "subscription_plan": "pro",
                "monthly_tech_cards_used": 0,
                "created_at": datetime.now()
            }
            await db.users.insert_one(test_user)
    
    # Validate user subscription (PRO only)
    user = await db.users.find_one({"id": user_id})
    if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
        raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    try:
        # Read file
        content = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process with pandas - support both Excel and CSV
        try:
            # Try Excel first
            if file.filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(temp_file_path, engine='openpyxl')
            elif file.filename.lower().endswith('.csv'):
                # For CSV, recreate temp file with .csv extension
                os.unlink(temp_file_path)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
                    temp_csv.write(content)
                    temp_csv_path = temp_csv.name
                df = pd.read_csv(temp_csv_path, encoding='utf-8')
                temp_file_path = temp_csv_path
            else:
                # Try reading as CSV as fallback
                os.unlink(temp_file_path)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
                    temp_csv.write(content)
                    temp_csv_path = temp_csv.name
                df = pd.read_csv(temp_csv_path, encoding='utf-8')
                temp_file_path = temp_csv_path
        except Exception as e:
            # If all fails, try different encodings for CSV
            try:
                os.unlink(temp_file_path)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
                    temp_csv.write(content)
                    temp_csv_path = temp_csv.name
                df = pd.read_csv(temp_csv_path, encoding='windows-1251')
                temp_file_path = temp_csv_path
            except Exception as e2:
                raise HTTPException(status_code=400, detail=f"Не удалось прочитать файл: {str(e2)}")
        
        
        processed_prices = []
        for _, row in df.iterrows():
            try:
                # Try to extract price data from row
                price_data = {
                    "name": str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else "",
                    "price": 0,
                    "unit": "кг",
                    "category": "other",
                    "source": file.filename,
                    "user_id": user_id,
                    "created_at": datetime.now()
                }
                
                # Try to parse price from any column
                for col_value in row.values:
                    if pd.notna(col_value):
                        price_match = re.search(r'(\d+(?:[.,]\d+)?)', str(col_value))
                        if price_match and float(price_match.group(1).replace(',', '.')) > 0:
                            price_data["price"] = float(price_match.group(1).replace(',', '.'))
                            break
                
                if price_data["name"] and price_data["price"] > 0:
                    processed_prices.append(price_data)
                    
            except Exception as e:
                continue
        
        # Save to database
        if processed_prices:
            await db.user_prices.insert_many(processed_prices)
        
        # Cleanup
        os.unlink(temp_file_path)
        
        # Create serializable version for response (remove datetime and other non-serializable fields)
        preview_prices = []
        for price in processed_prices[:10]:
            preview_prices.append({
                "name": price["name"],
                "price": price["price"],
                "unit": price["unit"],
                "category": price["category"],
                "source": price["source"]
            })
        
        return {
            "success": True,
            "count": len(processed_prices),
            "message": f"Обработано {len(processed_prices)} позиций",
            "prices": preview_prices
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.get("/user-prices/{user_id}")
async def get_user_prices(user_id: str):
    try:
        prices = await db.user_prices.find({"user_id": user_id}).to_list(1000)
        return {"prices": [{"name": p["name"], "price": p["price"], "unit": p["unit"]} for p in prices]}
    except Exception as e:
        logger.error(f"Error fetching user prices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching prices: {str(e)}")

@api_router.get("/user-history/{user_id}")
async def get_user_history(user_id: str):
    try:
        # Get user's tech cards history sorted by creation date (newest first)
        history_docs = await db.tech_cards.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(20).to_list(20)
        
        # Convert to serializable format by removing MongoDB ObjectId
        history = []
        for doc in history_docs:
            # Remove the MongoDB _id field to avoid serialization issues
            if "_id" in doc:
                del doc["_id"]
            history.append(doc)
        
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Error fetching user history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.post("/api/generate-sales-script")
async def generate_sales_script(request: dict):
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    # Validate user subscription (PRO only)
    user = await db.users.find_one({"id": user_id})
    if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
        raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    # Extract dish name from tech card
    dish_name = "блюдо"
    for line in tech_card.split('\n'):
        if 'Название:' in line:
            dish_name = line.split('Название:')[1].strip().replace('**', '')
            break
    
    prompt = f"""Ты — эксперт по продажам в ресторанном бизнесе. 

Создай профессиональный скрипт продаж для официантов для блюда "{dish_name}".

Техкарта блюда:
{tech_card}

Создай 3 варианта скриптов:

🎭 КЛАССИЧЕСКИЙ СКРИПТ:
[2-3 предложения для обычной презентации блюда]

🔥 АКТИВНЫЕ ПРОДАЖИ:
[агрессивный скрипт для увеличения среднего чека]

💫 ПРЕМИУМ ПОДАЧА:
[скрипт для VIP гостей и особых случаев]

Дополнительно:
• 5 ключевых преимуществ блюда
• Возражения клиентов и ответы на них
• Техники up-sell и cross-sell
• Невербальные приемы подачи

Пиши живо, как будто это реально говорит опытный официант."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.8
        )
        
        return {"script": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

@app.post("/api/generate-food-pairing")
async def generate_food_pairing(request: dict):
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    # Validate user subscription (PRO only)
    user = await db.users.find_one({"id": user_id})
    if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
        raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    # Extract dish name from tech card
    dish_name = "блюдо"
    for line in tech_card.split('\n'):
        if 'Название:' in line:
            dish_name = line.split('Название:')[1].strip().replace('**', '')
            break
    
    prompt = f"""Ты — сомелье и эксперт по фудпейрингу. 

Создай профессиональное руководство по сочетаниям для блюда "{dish_name}".

Техкарта блюда:
{tech_card}

Создай детальные рекомендации:

🍷 ВИННЫЕ ПАРЫ:
• Идеальные вина (3-4 варианта с регионами и характеристиками)
• Альтернативные варианты для разного бюджета
• Почему именно эти вина подходят

🍺 ПИВНЫЕ ПАРЫ:
• Подходящие стили пива
• Конкретные бренды и производители
• Температура подачи

🍹 КОКТЕЙЛИ:
• Алкогольные коктейли (2-3 варианта)
• Безалкогольные напитки
• Авторские миксы

🍽 ГАРНИРЫ И ДОПОЛНЕНИЯ:
• Идеальные гарниры
• Соусы и заправки
• Закуски для комплекта

🎯 НЕОЖИДАННЫЕ ПАРЫ:
• Креативные сочетания
• Сезонные варианты
• Эксклюзивные предложения

Для каждой категории объясни ПОЧЕМУ это сочетание работает (вкусовые профили, баланс, контрасты)."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        return {"pairing": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

@app.post("/api/generate-photo-tips")
async def generate_photo_tips(request: dict):
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    # Validate user subscription (PRO only)
    user = await db.users.find_one({"id": user_id})
    if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
        raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    # Extract dish name from tech card
    dish_name = "блюдо"
    for line in tech_card.split('\n'):
        if 'Название:' in line:
            dish_name = line.split('Название:')[1].strip().replace('**', '')
            break
    
    prompt = f"""Ты — фуд-фотограф и эксперт по визуальной подаче блюд.

Создай профессиональное руководство по фотографии для блюда "{dish_name}".

Техкарта блюда:
{tech_card}

Создай детальные рекомендации:

📸 ТЕХНИЧЕСКИЕ НАСТРОЙКИ:
• Оптимальные настройки камеры/телефона
• Освещение (естественное vs искусственное)
• Углы съемки и композиция

🎨 СТИЛИНГ И ПОДАЧА:
• Идеальная посуда и сервировка
• Цветовая палитра фона
• Декоративные элементы и пропсы

✨ КОМПОЗИЦИЯ:
• Лучшие ракурсы для данного блюда
• Правило третей и другие техники
• Как показать текстуру и аппетитность

🌅 ОСВЕЩЕНИЕ:
• Время суток для съемки
• Использование естественного света
• Искусственное освещение и софтбоксы

📱 ДЛЯ СОЦСЕТЕЙ:
• Адаптация для Instagram/TikTok
• Размеры и форматы
• Хештеги и подписи

🎭 ПОСТОБРАБОТКА:
• Основные правки (яркость, контраст, насыщенность)
• Фильтры и пресеты
• Приложения для обработки

💡 PRO СОВЕТЫ:
• Как подчеркнуть уникальность блюда
• Создание серии фото
• Съемка процесса приготовления

Для каждого совета объясни ПОЧЕМУ это важно для данного конкретного блюда."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        return {"tips": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

@app.post("/api/generate-inspiration")
async def generate_inspiration(request: dict):
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    inspiration_prompt = request.get("inspiration_prompt", "Создай креативный и жизнеспособный твист на это блюдо")
    
    if not user_id or not tech_card:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    # Проверяем подписку пользователя
    user = await db.users.find_one({"id": user_id})
    
    # Если пользователь не найден и это тестовый ID, создаем временного пользователя
    if not user and user_id.startswith("test_user_"):
        user = {
            "id": user_id,
            "email": "test@example.com",
            "name": "Test User",
            "city": "moscow",
            "subscription_plan": "pro",
            "subscription_status": "active",
            "monthly_tech_cards_used": 0,
            "monthly_reset_date": datetime.utcnow().isoformat(),
            "kitchen_equipment": [],
            "created_at": datetime.utcnow().isoformat()
        }
    elif not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.get("subscription_plan") not in ["pro", "business"]:
        raise HTTPException(status_code=403, detail="Функция доступна только для PRO пользователей")
    
    # Извлекаем название блюда из техкарты
    dish_name = "блюдо"
    title_match = re.search(r'\*\*Название:\*\*\s*(.*?)(?=\n|$)', tech_card)
    if title_match:
        dish_name = title_match.group(1).strip()
    
    # Специальный промт для создания вдохновения
    prompt = f"""Ты - креативный шеф-повар высшего класса, который создает неожиданные но жизнеспособные твисты на классические блюда.

ИСХОДНОЕ БЛЮДО:
{tech_card}

ЗАДАНИЕ: Создай креативный и оригинальный твист на блюдо "{dish_name}" учитывая такие идеи: {inspiration_prompt}

ТРЕБОВАНИЯ К ТВИСТУ:
• Сохрани базовую структуру оригинального блюда, но добавь неожиданные элементы
• Используй международные кулинарные традиции для вдохновения
• Предложи замену 2-3 ингредиентов на более интересные
• Добавь новые техники приготовления или подачи
• Сохрани жизнеспособность для ресторанной кухни
• Учитывай себестоимость и время приготовления

СТРУКТУРА ОТВЕТА:
**Название:** [Новое креативное название с указанием твиста]

**Категория:** [та же категория]

**Описание:** [Опиши концепцию твиста, его особенности и почему это интересно]

**Ингредиенты:** (порция как в оригинале)
[Список ингредиентов с новыми элементами, количеством и ценами в рублях]

**Пошаговый рецепт:**
[Пошаговый рецепт с новыми техниками]

**Время:** [Время приготовления]

**Выход:** [Выход готового блюда]

**💸 Себестоимость:**
[Расчет себестоимости новых ингредиентов]

**КБЖУ на 1 порцию:** [Примерное КБЖУ]

**Аллергены:** [Аллергены]

**🌟 Особенности твиста:**
• В чем креативность
• Какие новые вкусы
• Как это меняет восприятие блюда
• Подача и презентация

**Заготовки и хранение:**
[Советы по заготовкам для новых ингредиентов]

Создай действительно интересный и жизнеспособный твист, который удивит, но останется вкусным и выполнимым!"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.8
        )
        
        return {"inspiration": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

@app.post("/api/save-tech-card")
async def save_tech_card(request: dict):
    user_id = request.get("user_id")
    content = request.get("content")
    dish_name = request.get("dish_name", "Техкарта")
    city = request.get("city", "moscow")
    is_inspiration = request.get("is_inspiration", False)
    
    if not user_id or not content:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    # Auto-create test user if needed
    if user_id.startswith("test_user_"):
        user = await db.users.find_one({"id": user_id})
        if not user:
            test_user = {
                "id": user_id,
                "email": f"{user_id}@example.com",
                "name": "Test User",
                "city": city,
                "subscription_plan": "pro",
                "monthly_tech_cards_used": 0,
                "created_at": datetime.now()
            }
            await db.users.insert_one(test_user)
    
    try:
        # Create tech card object
        tech_card = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "dish_name": dish_name,
            "content": content,
            "city": city,
            "is_inspiration": is_inspiration,
            "created_at": datetime.now()
        }
        
        # Save to database
        await db.tech_cards.insert_one(tech_card)
        
        return {
            "id": tech_card["id"],
            "message": "Техкарта сохранена успешно"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

@app.post("/api/analyze-finances")
async def analyze_finances(request: dict):
    """Анализ финансов блюда для PRO пользователей"""
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    if not user_id or not tech_card:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    # Проверяем подписку пользователя (PRO only)
    user = await db.users.find_one({"id": user_id})
    
    # Автоматически создаем тестового пользователя
    if not user and user_id.startswith("test_user_"):
        user = {
            "id": user_id,
            "email": "test@example.com",
            "name": "Test User",
            "city": "moscow",
            "subscription_plan": "pro",
            "subscription_status": "active",
            "created_at": datetime.now()
        }
    elif not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.get("subscription_plan") not in ["pro", "business"]:
        raise HTTPException(status_code=403, detail="Функция доступна только для PRO пользователей")
    
    # Извлекаем название блюда
    dish_name = "блюдо"
    title_match = re.search(r'\*\*Название:\*\*\s*(.*?)(?=\n|$)', tech_card)
    if title_match:
        dish_name = title_match.group(1).strip()
    
    # Извлекаем ингредиенты и цены
    ingredients_match = re.search(r'\*\*Ингредиенты:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)', tech_card, re.DOTALL)
    ingredients_text = ingredients_match.group(1) if ingredients_match else ""
    
    # Получаем региональный коэффициент
    regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
    
    # Создаем промпт для финансового анализа
    prompt = f"""Ты — топовый финансовый аналитик ресторанного бизнеса с 15-летним опытом работы с премиум-заведениями.Проанализируй финансовые показатели блюда "{dish_name}" максимально ДЕТАЛЬНО и ПРОФЕССИОНАЛЬНО.

ТЕХКАРТА:
{tech_card}

ИНГРЕДИЕНТЫ:
{ingredients_text}

РЕГИОНАЛЬНЫЙ КОЭФФИЦИЕНТ: {regional_coefficient}x

Создай МАКСИМАЛЬНО ПОДРОБНЫЙ финансовый анализ в формате JSON с КОНКРЕТНЫМИ ЦИФРАМИ:

{{
    "dish_name": "{dish_name}",
    "total_cost": [точная себестоимость с копейками],
    "recommended_price": [рекомендуемая цена продажи],
    "margin_percent": [маржинальность в процентах],
    "profitability_rating": [рейтинг от 1 до 5],
    "detailed_cost_breakdown": [
        {{"ingredient": "Конкретный ингредиент", "quantity": "количество", "unit_price": "цена за единицу", "total_cost": "общая стоимость", "percent_of_total": "процент от общей себестоимости"}},
        {{"ingredient": "Другой ингредиент", "quantity": "количество", "unit_price": "цена за единицу", "total_cost": "общая стоимость", "percent_of_total": "процент"}}
    ],
    "cost_breakdown": [
        {{"category": "Белки", "amount": [сумма], "percent": [процент], "items": ["список ингредиентов"]}},
        {{"category": "Углеводы", "amount": [сумма], "percent": [процент], "items": ["список ингредиентов"]}},
        {{"category": "Жиры", "amount": [сумма], "percent": [процент], "items": ["список ингредиентов"]}},
        {{"category": "Овощи", "amount": [сумма], "percent": [процент], "items": ["список ингредиентов"]}},
        {{"category": "Специи/Соусы", "amount": [сумма], "percent": [процент], "items": ["список ингредиентов"]}}
    ],
    "optimization_tips": [
        {{"tip": "Конкретный совет с цифрами", "current_cost": "текущая стоимость", "optimized_cost": "оптимизированная стоимость", "savings": "экономия в рублях", "impact": "влияние на качество: минимальное/среднее/высокое"}},
        {{"tip": "Другой детальный совет", "current_cost": "текущая стоимость", "optimized_cost": "оптимизированная стоимость", "savings": "экономия в рублях", "impact": "влияние на качество"}}
    ],
    "supplier_recommendations": [
        {{"category": "Категория продуктов", "current_supplier": "текущий поставщик", "recommended_supplier": "рекомендуемый поставщик", "savings_percent": "процент экономии", "quality_impact": "влияние на качество"}},
        {{"category": "Другая категория", "current_supplier": "текущий поставщик", "recommended_supplier": "рекомендуемый поставщик", "savings_percent": "процент экономии", "quality_impact": "влияние на качество"}}
    ],
    "price_comparison": {{
        "competitor_analysis": [
            {{"competitor": "Конкурент 1", "price": "цена", "position": "позиция"}},
            {{"competitor": "Конкурент 2", "price": "цена", "position": "позиция"}}
        ],
        "market_average": [средняя цена],
        "market_position": "выше/ниже/в среднем",
        "price_positioning": "премиум/средний/эконом",
        "recommendation": "детальная рекомендация по ценообразованию"
    }},
    "seasonal_analysis": {{
        "current_season": "текущий сезон",
        "seasonal_ingredients": [
            {{"ingredient": "ингредиент", "season_impact": "влияние сезона", "price_change": "изменение цены", "recommendation": "рекомендация"}}
        ],
        "best_seasons": ["лучшие сезоны для блюда"],
        "worst_seasons": ["худшие сезоны для блюда"],
        "seasonal_tips": "детальные советы по сезонности"
    }},
    "financial_metrics": {{
        "break_even_portions": [количество порций для окупаемости],
        "daily_break_even": [сколько порций в день нужно продать],
        "monthly_potential": [потенциал в месяц],
        "profit_per_portion": [прибыль с одной порции],
        "cost_per_100g": [себестоимость на 100г],
        "roi_percent": [ROI в процентах],
        "payback_period": [срок окупаемости в днях],
        "gross_margin": [валовая маржа],
        "contribution_margin": [маржинальная прибыль]
    }},
    "business_intelligence": {{
        "target_customers": ["целевая аудитория"],
        "optimal_pricing_strategy": "стратегия ценообразования",
        "upsell_opportunities": ["возможности для допродаж"],
        "menu_positioning": "позиционирование в меню",
        "profitability_rank": "ранг прибыльности от 1 до 10"
    }},
    "strategic_recommendations": [
        {{"category": "Ценообразование", "recommendation": "конкретная рекомендация", "expected_impact": "ожидаемый эффект"}},
        {{"category": "Закупки", "recommendation": "конкретная рекомендация", "expected_impact": "ожидаемый эффект"}},
        {{"category": "Меню", "recommendation": "конкретная рекомендация", "expected_impact": "ожидаемый эффект"}}
    ],
    "risk_analysis": {{
        "price_volatility": [
            {{"ingredient": "ингредиент", "volatility_level": "уровень волатильности", "risk_factor": "фактор риска", "mitigation": "способ снижения риска"}}
        ],
        "supply_chain_risks": ["риски цепочки поставок"],
        "market_risks": ["рыночные риски"],
        "recommendations": ["рекомендации по снижению рисков"]
    }},
    "kpi_dashboard": {{
        "food_cost_percentage": [процент фудкоста],
        "labor_cost_estimate": [оценка затрат на труд],
        "total_variable_cost": [общие переменные затраты],
        "contribution_to_fixed_costs": [вклад в покрытие постоянных затрат],
        "menu_mix_impact": [влияние на menu mix],
        "velocity_score": [скорость продаж от 1 до 10]
    }},
}}

ВАЖНО: 
- Все расчеты должны быть точными и реалистичными
- Учитывай региональный коэффициент {regional_coefficient}x
- Базируйся на российских ценах 2024 года + инфляция 12%
- Давай практические советы для реального ресторана
- Проверяй математику в расчетах
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты профессиональный финансовый аналитик ресторанного бизнеса с 10-летним опытом. Всегда возвращай корректный JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        analysis_text = response.choices[0].message.content
        
        # Пробуем распарсить JSON
        try:
            import json
            analysis_data = json.loads(analysis_text)
        except json.JSONDecodeError:
            # Если JSON некорректный, возвращаем базовый анализ
            analysis_data = {
                "dish_name": dish_name,
                "total_cost": 150,
                "recommended_price": 450,
                "margin_percent": 67,
                "profitability_rating": 4,
                "raw_analysis": analysis_text
            }
        
        return {
            "success": True,
            "analysis": analysis_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")