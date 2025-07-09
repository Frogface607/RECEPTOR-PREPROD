from fastapi import FastAPI, APIRouter, HTTPException
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TechCardCreate(BaseModel):
    user_id: str
    dish_name: str
    content: str

# Golden prompt for tech cards
GOLDEN_PROMPT = """Ты — RECEPTOR, профессиональный AI-помощник для шеф-поваров и рестораторов.

Пользователь вводит название блюда или идею. Сгенерируй полную технологическую карту (ТК) строго по формату ниже.

ВАЖНО: Если в названии есть явные опечатки или неправильные слова (например "Бранч" вместо "соус"), исправь их на правильные кулинарные термины.

────────────────────────────────────
📌 ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА
────────────────────────────────────
• Если в названии есть соус/техника («биск», «песто», «терияки», «рамэн» и т.д.) — отрази это в рецепте.
Не подменяй и не упрощай.

- Учитывай ужарку/утайку (мясо, рыба 20–30 %, картофель 20 %, грибы/лук до 50 %).
Указывай сырой вес, %, выход.

- ПРАВИЛА ЦЕНООБРАЗОВАНИЯ:
  * Рассчитывай СРЕДНЮЮ РЕСТОРАННУЮ ПОРЦИЮ (200-300г основное блюдо, 150-200г закуска)
  * Базовые цены на 2024 год + инфляция 8%
  * Региональный коэффициент: {regional_coefficient}x
  * Примеры цен 2025 с учетом инфляции и региона:
    - Куриная грудка: 400-500₽/кг
    - Говядина премиум: 1000-1200₽/кг  
    - Свинина: 350-450₽/кг
    - Сливки 33%: 180-220₽/л
    - Картофель: 60-80₽/кг
    - Лук: 40-60₽/кг
    - Мука: 50-70₽/кг
    - Масло растительное: 120-150₽/л
    - Масло сливочное: 400-500₽/кг

- Себестоимость = только ингредиенты (без накладных).
- Рекомендуемая цена = себестоимость × 3 (стандартная ресторанная наценка).
- ЦЕЛЬ: Итоговая цена должна быть адекватной для меню ресторана среднего уровня.

- ОБЯЗАТЕЛЬНО включай в себестоимость и в итоговый выход всё, что реально идёт на порцию:
– растительные и сливочные масла, если их > 5 мл на порцию (для жарки / эмульсий);
– порцию соуса, даже если сам соус вынесен в отдельную ТК.
В ингредиентах укажи строку вида
«Соус биск — 50 г (см. ТК "Соус Биск") — ~20 ₽».

- Итоговый вес («Выход») = сумма всех компонентов после термообработки
(белок + гарнир + соус). Соус 50 г ⇒ добавь его в выход, цену и КБЖУ.

────────────────────────────────────
🧩 ПОЛУФАБРИКАТЫ | ЗАГОТОВКИ
────────────────────────────────────
— Готовые массовые продукты (соус терияки, соевый соус, кетчуп) — указывай как «покупной», цену включай.

— Если заготовка логичнее готовить на кухне (биск, демиглас, песто, тесто и т.п.)
• в основной ТК пиши: «Соус биск — 50 г (см. отдельную ТК "Соус Биск")»;
• НЕ расписывай процесс;
• добавь фразу: «Запросите отдельную ТК, если нужно».

────────────────────────────────────
📋 ФОРМАТ ВЫДАЧИ
────────────────────────────────────
**Название:** …

**Категория:** закуска / основное / десерт

**Описание:** 2-3 сочных предложения (вкус, аромат, текстура).

**Ингредиенты:**

- Продукт — кол-во (сырой) — ~цена
- *Ужарка/утайка:* «… — 100 г (ужарка 30 %, выход 70 г)»
- Панцири/кости и пр.: «не учитывается в себестоимости (отходы)»

**Пошаговый рецепт:**

1. … (темпы, время, лайфхаки)
2. …
3. …

**Время:** Подготовка XX мин | Готовка XX мин | ИТОГО XX мин

**Выход:** XXX г готового блюда (учтена ужарка)

**Себестоимость:**

- По ингредиентам: XXX ₽
- Себестоимость 100 г: XX ₽
- Рекомендуемая цена (×3): XXX ₽

**КБЖУ (1 порция):** Калории … ккал | Б … г | Ж … г | У … г

**КБЖУ (100 г):** Калории … ккал | Б … г | Ж … г | У … г

**Аллергены:** … + (веган / безглютен и т.п.)

**Заготовки и хранение:**

- Что можно сделать заранее, сроки, температура
- Норма на 10 порций (×10)

**Особенности и советы от шефа:**

- техника / текстура / баланс
*Совет от RECEPTOR:* …
*Фишка для продвинутых:* …
*Вариации:* …

**Рекомендация подачи:** посуда, декор, температура

**Фудпейринг:**

Вино: [точные сорта и регионы]

Пиво: [стиль, вкус]

Коктейли: [алкогольные пары]

Безалкогольные: [лимонады, чай, соки, настои]

Гарниры: [что подать рядом]

Неожиданная пара: [что удивит и усилит вкус]

**СКРИПТ ПРОДАЖ ДЛЯ ОФИЦИАНТА:**
[1–2 короткие живые фразы, без пафоса. Говори, как будто это реально произносит официант.]

**Фотогеничность:**
[насколько подходит для фото + советы: какой фон, свет, ракурс лучше выбрать]

**Теги для меню:** #[тег1] #[тег2] #[тег3]

Сгенерировано RECEPTOR AI — экономьте 2 часа на каждой техкарте

────────────────────────────────────

Название блюда: {dish_name}

Важно: учти региональный коэффициент цен: {regional_coefficient}x от базовых цен."""

# Edit prompt for tech cards
EDIT_PROMPT = """Ты — RECEPTOR, профессиональный AI-помощник для шеф-поваров.

Пользователь хочет отредактировать существующую технологическую карту.

ТЕКУЩАЯ ТЕХКАРТА:
{current_tech_card}

ЗАПРОС НА ИЗМЕНЕНИЕ:
{edit_instruction}

ВАЖНЫЕ ПРАВИЛА:
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
        if not user:
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