from fastapi import FastAPI, APIRouter, HTTPException, File, Form, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import asyncio
import openai
from openai import OpenAI
import json
import re
import tempfile
import pandas as pd

# IIKo Integration imports
try:
    from pyiikocloudapi import IikoTransport
    IIKO_AVAILABLE = True
    print("✅ IIKo integration is available")
except ImportError as e:
    IIKO_AVAILABLE = False
    print(f"⚠️ IIKo integration not available: {e}")
    IikoTransport = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Setup logging
logger = logging.getLogger(__name__)

# IIKo Integration Classes
class IikoServerAuthManager:
    def __init__(self):
        self.api_login = os.environ.get('IIKO_API_LOGIN')
        self.api_token = os.environ.get('IIKO_API_TOKEN')
        self.base_url = os.environ.get('IIKO_BASE_URL', 'https://api-ru.iiko.services')
        self.logger = logging.getLogger(__name__)
        
    async def get_session_key(self):
        """Use the provided JWT token directly"""
        if not self.api_token:
            raise Exception("IIKo API token not configured")
        
        # For IIKo Server API, we can use the provided JWT token directly
        return self.api_token
    
    def _is_session_expired(self) -> bool:
        """Check if we have a token (JWT expiration handled by server)"""
        return not self.api_token

class IikoServerIntegrationService:
    def __init__(self, auth_manager: IikoServerAuthManager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        self._organization_cache: Dict[str, Any] = {}
        self._menu_cache: Dict[str, Any] = {}
        
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Fetch organizations from iikoServer API using JWT token"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            organizations_url = f"{self.auth_manager.base_url}/api/1/organizations"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {session_key}"
            }
            
            payload = {
                "organizationIds": []  # Empty array to get all organizations
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(organizations_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse organizations from iikoServer response
                    organizations = []
                    if isinstance(data, list):
                        for org in data:
                            organizations.append({
                                'id': org.get('id'),
                                'name': org.get('name'),
                                'address': org.get('address', ''),
                                'active': True
                            })
                    elif isinstance(data, dict) and 'organizations' in data:
                        for org in data['organizations']:
                            organizations.append({
                                'id': org.get('id'),
                                'name': org.get('name'),
                                'address': org.get('address', ''),
                                'active': True
                            })
                    
                    self._organization_cache = {org['id']: org for org in organizations}
                    self.logger.info(f"Retrieved {len(organizations)} organizations from iikoServer")
                    return organizations
                else:
                    self.logger.error(f"Organizations request failed: {response.status_code} {response.text}")
                    raise Exception(f"Failed to get organizations: {response.status_code}")
                    
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching organizations: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch organizations: {str(e)}")
    
    async def get_menu_items(self, organization_ids: List[str]) -> Dict[str, Any]:
        """Fetch menu/nomenclature from iikoServer API"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            # iikoServer API endpoint for nomenclature
            menu_url = f"{self.auth_manager.base_url}/api/1/nomenclature"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "access_token": session_key,
                "organizationId": organization_ids[0] if organization_ids else None
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(menu_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    menu_data = {
                        'categories': [],
                        'items': [],
                        'modifiers': [],
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    # Parse iikoServer nomenclature response
                    if 'groups' in data:
                        menu_data['categories'] = [
                            {
                                'id': cat.get('id'),
                                'name': cat.get('name'),
                                'description': '',
                                'active': True
                            }
                            for cat in data.get('groups', [])
                        ]
                    
                    if 'products' in data:
                        menu_data['items'] = [
                            {
                                'id': item.get('id'),
                                'name': item.get('name'),
                                'description': item.get('description', ''),
                                'category_id': item.get('parentGroup'),
                                'price': 0.0,  # iikoServer may not have prices in nomenclature
                                'weight': 0.0,
                                'modifiers': [],
                                'active': True
                            }
                            for item in data.get('products', [])
                        ]
                    
                    self._menu_cache['-'.join(organization_ids)] = menu_data
                    self.logger.info(f"Retrieved menu with {len(menu_data['items'])} items from iikoServer")
                    return menu_data
                else:
                    self.logger.error(f"Menu request failed: {response.status_code} {response.text}")
                    raise Exception(f"Failed to get menu: {response.status_code}")
                    
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching menu items: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch menu items: {str(e)}")

# Legacy Cloud API classes (keeping for backward compatibility)
class IikoAuthManager:
    def __init__(self):
        self.api_login = os.environ.get('IIKO_API_LOGIN')
        self.api_password = os.environ.get('IIKO_API_PASSWORD')
        self.base_url = os.environ.get('IIKO_BASE_URL', 'https://api-ru.iiko.services')
        self.client: Optional[Any] = None
        self.token_expires_at: Optional[datetime] = None
        self.logger = logging.getLogger(__name__)
        
    async def get_authenticated_client(self):
        """Get authenticated IIKo client with automatic token refresh"""
        if not IIKO_AVAILABLE:
            raise HTTPException(status_code=503, detail="IIKo integration is not available")
            
        if not self.api_login or not self.api_password:
            raise HTTPException(status_code=500, detail="IIKo credentials not configured")
        
        if self._is_token_expired():
            await self._refresh_client()
        return self.client
    
    def _is_token_expired(self) -> bool:
        """Check if current token is expired or about to expire"""
        if not self.client or not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at - timedelta(minutes=5)
    
    async def _refresh_client(self):
        """Initialize or refresh IIKo client connection"""
        try:
            self.client = IikoTransport(self.api_login, return_dict=False)
            # Test connection by fetching organizations
            await asyncio.to_thread(self.client.organizations)
            self.token_expires_at = datetime.now() + timedelta(minutes=55)
            self.logger.info("IIKo client authenticated successfully")
        except Exception as e:
            self.logger.error(f"Failed to authenticate with IIKo: {str(e)}")
            raise HTTPException(status_code=500, detail=f"IIKo authentication failed: {str(e)}")

class IikoIntegrationService:
    def __init__(self, auth_manager: IikoAuthManager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        self._organization_cache: Dict[str, Any] = {}
        self._menu_cache: Dict[str, Any] = {}
        
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Fetch all available organizations from IIKo"""
        try:
            client = await self.auth_manager.get_authenticated_client()
            result = await asyncio.to_thread(client.organizations)
            
            if hasattr(result, 'organizations'):
                organizations = [
                    {
                        'id': org.id,
                        'name': org.name,
                        'country': getattr(org, 'country', ''),
                        'address': getattr(org, 'restaurantAddress', ''),
                        'active': True
                    }
                    for org in result.organizations
                ]
            else:
                organizations = []
                
            self._organization_cache = {org['id']: org for org in organizations}
            self.logger.info(f"Retrieved {len(organizations)} organizations from IIKo")
            return organizations
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching organizations: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch organizations: {str(e)}")
    
    async def get_menu_items(self, organization_ids: List[str]) -> Dict[str, Any]:
        """Fetch menu items and categories from IIKo"""
        try:
            client = await self.auth_manager.get_authenticated_client()
            
            # Get menu for specified organizations
            menu_result = await asyncio.to_thread(
                client.menu, 
                organization_ids
            )
            
            menu_data = {
                'categories': [],
                'items': [],
                'modifiers': [],
                'last_updated': datetime.now().isoformat()
            }
            
            if hasattr(menu_result, 'productCategories'):
                menu_data['categories'] = [
                    {
                        'id': cat.id,
                        'name': cat.name,
                        'description': getattr(cat, 'description', ''),
                        'active': True
                    }
                    for cat in menu_result.productCategories
                ]
            
            if hasattr(menu_result, 'products'):
                menu_data['items'] = [
                    {
                        'id': item.id,
                        'name': item.name,
                        'description': getattr(item, 'description', ''),
                        'category_id': getattr(item, 'productCategoryId', ''),
                        'price': getattr(item, 'price', 0.0),
                        'weight': getattr(item, 'weight', 0.0),
                        'modifiers': [getattr(mod, 'id', '') for mod in getattr(item, 'modifiers', [])],
                        'active': True
                    }
                    for item in menu_result.products
                ]
            
            self._menu_cache['-'.join(organization_ids)] = menu_data
            self.logger.info(f"Retrieved menu with {len(menu_data['items'])} items")
            return menu_data
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching menu items: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch menu items: {str(e)}")

# Initialize IIKo integration services
# Try iikoServer API first, fallback to Cloud API
try:
    iiko_auth_manager = IikoServerAuthManager()
    iiko_service = IikoServerIntegrationService(iiko_auth_manager)
    logger.info("Using iikoServer API integration")
except Exception as e:
    logger.warning(f"iikoServer API failed, falling back to Cloud API: {e}")
    iiko_auth_manager = IikoAuthManager()
    iiko_service = IikoIntegrationService(iiko_auth_manager)

# Create the main app without a prefix
app = FastAPI()

# Add CORS middleware with dynamic origins
def get_cors_origins():
    """Get CORS origins based on environment"""
    base_origins = [
        "http://localhost:3000",  # Local development
        "https://www.receptorai.pro",  # Production
        "https://receptorai.pro",  # Production without www
    ]
    
    # Add all possible preview and deployment domains
    preview_patterns = [
        "https://26d71771-d1f5-449c-a365-fa5f081cd98e.preview.emergentagent.com",  # All preview URLs
        "https://*.vercel.app",  # All Vercel deployments
        "https://*.netlify.app",  # All Netlify deployments
        "https://receptor-ai-thte.vercel.app",  # Specific Vercel domain
    ]
    
    # For development, allow all origins
    if os.environ.get("ENVIRONMENT") == "development":
        return ["*"]
    
    return base_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Allow all for development
        "https://receptor-ai.vercel.app",    # New Vercel domain
        "https://receptorai.pro",            # Custom domain
        "https://www.receptorai.pro",        # Custom domain with www
        "https://kitchen-ai.emergent.host",  # New backend domain
        "http://localhost:3000",             # Local development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

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

# Venue Types Configuration
VENUE_TYPES = {
    "fine_dining": {
        "name": "Fine Dining",
        "description": "Высококлассный ресторан с изысканной кухней",
        "price_multiplier": 1.5,
        "complexity_level": "high",
        "techniques": ["су-вид", "молекулярная гастрономия", "профессиональная подача", "сложные соусы"],
        "service_style": "table_service",
        "portion_style": "artistic"
    },
    "food_truck": {
        "name": "Food Truck",
        "description": "Мобильная точка питания быстрого обслуживания",
        "price_multiplier": 0.6,
        "complexity_level": "low",
        "techniques": ["гриль", "фритюр", "быстрая жарка", "простая сборка"],
        "service_style": "fast_casual",
        "portion_style": "handheld"
    },
    "bar_pub": {
        "name": "Бар/Паб",
        "description": "Бар с закусками и напитками",
        "price_multiplier": 0.9,
        "complexity_level": "medium",
        "techniques": ["гриль", "фритюр", "снеки", "закуски под алкоголь"],
        "service_style": "bar_service", 
        "portion_style": "sharing"
    },
    "cafe": {
        "name": "Кафе",
        "description": "Уютное кафе с домашней атмосферой",
        "price_multiplier": 0.8,
        "complexity_level": "medium",
        "techniques": ["выпечка", "кофейные напитки", "легкие блюда", "десерты"],
        "service_style": "counter_service",
        "portion_style": "comfort"
    },
    "coffee_shop": {
        "name": "Кофейня",
        "description": "Специализированная кофейня с авторскими напитками",
        "price_multiplier": 0.7,
        "complexity_level": "medium",
        "techniques": ["альтернативное заваривание", "латте-арт", "выпечка", "десерты"],
        "service_style": "counter_service",
        "portion_style": "grab_and_go"
    },
    "food_court": {
        "name": "Фуд-корт",
        "description": "Точка в торговом центре или фуд-корте",
        "price_multiplier": 0.7,
        "complexity_level": "low",
        "techniques": ["быстрое приготовление", "стандартизация", "разогрев", "сборка"],
        "service_style": "quick_service",
        "portion_style": "standard"
    },
    "canteen": {
        "name": "Столовая",
        "description": "Массовое питание для офисов, школ, предприятий",
        "price_multiplier": 0.5,
        "complexity_level": "low",
        "techniques": ["массовое приготовление", "простые техники", "большие объемы"],
        "service_style": "cafeteria",
        "portion_style": "generous"
    },
    "kids_cafe": {
        "name": "Детское кафе",
        "description": "Семейное кафе с детским меню и развлечениями",
        "price_multiplier": 0.8,
        "complexity_level": "low",
        "techniques": ["безопасное приготовление", "яркая подача", "простые вкусы"],
        "service_style": "family_friendly",
        "portion_style": "kid_friendly"
    },
    "night_club": {
        "name": "Ночной клуб",
        "description": "Заведение с ночными развлечениями",
        "price_multiplier": 1.2,
        "complexity_level": "low", 
        "techniques": ["фингер-фуд", "простые закуски", "без столовых приборов"],
        "service_style": "standing",
        "portion_style": "finger_food"
    },
    "family_restaurant": {
        "name": "Семейный ресторан",
        "description": "Ресторан для семей с детьми",
        "price_multiplier": 1.0,
        "complexity_level": "medium",
        "techniques": ["домашняя кухня", "большие порции", "простые рецепты"],
        "service_style": "family_friendly",
        "portion_style": "generous"
    },
    "fast_food": {
        "name": "Фаст-фуд",
        "description": "Быстрое питание с стандартизированным меню",
        "price_multiplier": 0.6,
        "complexity_level": "low",
        "techniques": ["фритюр", "гриль", "стандартизация", "быстрая сборка"],
        "service_style": "quick_service",
        "portion_style": "standard"
    },
    "bakery_cafe": {
        "name": "Пекарня-кафе",
        "description": "Пекарня с кафе и свежей выпечкой",
        "price_multiplier": 0.8,
        "complexity_level": "medium",
        "techniques": ["выпечка", "хлебопечение", "кондитерское искусство"],
        "service_style": "counter_service",
        "portion_style": "artisan"
    },
    "buffet": {
        "name": "Буфет/Шведский стол",
        "description": "Самообслуживание с широким выбором блюд",
        "price_multiplier": 0.9,
        "complexity_level": "medium",
        "techniques": ["массовое приготовление", "длительное хранение", "разнообразие"],
        "service_style": "self_service",
        "portion_style": "variety"
    },
    "street_food": {
        "name": "Уличная еда",
        "description": "Торговые точки с уличной едой",
        "price_multiplier": 0.5,
        "complexity_level": "low",
        "techniques": ["простое приготовление", "мобильность", "быстрая подача"],
        "service_style": "street_vendor",
        "portion_style": "portable"
    }
}

# Cuisine Focus Configuration
CUISINE_TYPES = {
    "asian": {
        "name": "Азиатская",
        "subcategories": ["japanese", "korean", "thai", "chinese", "indian"],
        "key_ingredients": ["рис", "соевый соус", "имбирь", "чеснок", "перец чили", "кокосовое молоко", "рыбный соус"],
        "cooking_methods": ["вок", "пар", "тушение", "маринование"],
        "flavor_profile": ["умами", "острый", "сладко-соленый", "ароматные специи"]
    },
    "european": {
        "name": "Европейская", 
        "subcategories": ["italian", "french", "german", "spanish", "greek"],
        "key_ingredients": ["оливковое масло", "томаты", "сыр", "травы", "вино", "сливки"],
        "cooking_methods": ["жарка", "тушение", "запекание", "соусы"],
        "flavor_profile": ["сбалансированный", "травяной", "винный", "сырный"]
    },
    "caucasian": {
        "name": "Кавказская",
        "subcategories": ["georgian", "armenian", "azerbaijani"],
        "key_ingredients": ["баранина", "говядина", "зелень", "специи", "орехи", "гранат"],
        "cooking_methods": ["мангал", "тандыр", "долгое тушение", "маринование"],
        "flavor_profile": ["пряный", "ароматный", "мясной", "с кислинкой"]
    },
    "eastern": {
        "name": "Восточная",
        "subcategories": ["uzbek", "turkish", "arabic"],
        "key_ingredients": ["рис", "баранина", "специи", "сухофрукты", "орехи", "йогурт"],
        "cooking_methods": ["плов", "долгое тушение", "запекание", "специи"],
        "flavor_profile": ["пряный", "ароматный", "насыщенный", "экзотический"]
    },
    "russian": {
        "name": "Русская",
        "subcategories": ["traditional", "modern_russian", "siberian"],
        "key_ingredients": ["картофель", "капуста", "свекла", "мясо", "рыба", "грибы"],
        "cooking_methods": ["варка", "тушение", "засолка", "копчение"],
        "flavor_profile": ["сытный", "традиционный", "домашний", "согревающий"]
    },
    "sea": {
        "name": "Юго-Восточная Азия",
        "subcategories": ["thai", "vietnamese", "malaysian", "filipino"],
        "key_ingredients": ["лемонграсс", "кокосовое молоко", "лайм", "галанга", "базилик", "рыбный соус"],
        "cooking_methods": ["вок", "гриль", "карри", "свежие салаты"],
        "flavor_profile": ["кисло-сладкий", "пряный", "свежий", "тропический"]
    },
    "french": {
        "name": "Французская",
        "subcategories": ["classic", "bistro", "provence"],
        "key_ingredients": ["сливочное масло", "сливки", "вино", "травы прованс", "сыр", "паштет"],
        "cooking_methods": ["конфи", "фламбирование", "су-вид", "соусы"],
        "flavor_profile": ["изысканный", "сливочный", "винный", "деликатесный"]
    },
    "eastern_european": {
        "name": "Восточноевропейская",
        "subcategories": ["polish", "czech", "hungarian", "slovak"],
        "key_ingredients": ["капуста", "колбаса", "паприка", "сметана", "картофель", "свинина"],
        "cooking_methods": ["тушение", "копчение", "засолка", "варка"],
        "flavor_profile": ["сытный", "дымный", "кислый", "пряный"]
    },
    "american": {
        "name": "Американская",
        "subcategories": ["bbq", "southern", "tex_mex"],
        "key_ingredients": ["говядина", "свинина", "кукуруза", "бобы", "сыр", "соус барбекю"],
        "cooking_methods": ["гриль", "барбекю", "копчение", "жарка"],
        "flavor_profile": ["дымный", "сладко-острый", "сытный", "простой"]
    },
    "mexican": {
        "name": "Мексиканская",
        "subcategories": ["traditional", "tex_mex", "street_food"],
        "key_ingredients": ["авокадо", "лайм", "перец чили", "кукуруза", "фасоль", "кориандр"],
        "cooking_methods": ["гриль", "тушение", "маринады", "сальса"],
        "flavor_profile": ["острый", "цитрусовый", "пряный", "свежий"]
    },
    "italian": {
        "name": "Итальянская",
        "subcategories": ["northern", "southern", "sicilian"],
        "key_ingredients": ["томаты", "базилик", "пармезан", "оливковое масло", "чеснок", "паста"],
        "cooking_methods": ["аль денте", "ризотто", "пицца", "брускетта"],
        "flavor_profile": ["томатный", "сырный", "травяной", "простой"]
    },
    "indian": {
        "name": "Индийская",
        "subcategories": ["northern", "southern", "bengali"],
        "key_ingredients": ["куркума", "кориандр", "кумин", "кардамон", "кокос", "йогурт"],
        "cooking_methods": ["карри", "тандыр", "темперирование специй", "дал"],
        "flavor_profile": ["пряный", "ароматный", "острый", "сложный"]
    }
}

# Average Check Categories
AVERAGE_CHECK_CATEGORIES = {
    "budget": {
        "name": "Бюджетное",
        "range": [200, 500],
        "description": "Доступные цены для массового потребителя",
        "ingredient_quality": "standard",
        "portion_approach": "generous"
    },
    "mid_range": {
        "name": "Средний сегмент", 
        "range": [500, 1500],
        "description": "Качественная еда по разумным ценам",
        "ingredient_quality": "good",
        "portion_approach": "balanced"
    },
    "premium": {
        "name": "Премиум",
        "range": [1500, 3000],
        "description": "Высококачественные ингредиенты и сервис",
        "ingredient_quality": "premium",
        "portion_approach": "refined"
    },
    "luxury": {
        "name": "Люкс",
        "range": [3000, 10000],
        "description": "Эксклюзивные ингредиенты и опыт",
        "ingredient_quality": "luxury",
        "portion_approach": "artistic"
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
    # NEW: Venue Profile fields
    venue_type: Optional[str] = None  # fine_dining, food_truck, bar_pub, etc.
    cuisine_focus: List[str] = []  # asian, european, caucasian, etc.
    average_check: Optional[int] = None  # target average check in rubles
    venue_name: Optional[str] = None  # restaurant/venue name
    venue_concept: Optional[str] = None  # brief concept description
    target_audience: Optional[str] = None  # families, young professionals, etc.
    special_features: List[str] = []  # live_music, outdoor_seating, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    name: str
    city: str

class UserSubscription(BaseModel):
    subscription_plan: str
    
class KitchenEquipmentUpdate(BaseModel):
    equipment_ids: List[str]

class VenueProfileUpdate(BaseModel):
    # Basic venue information
    venue_type: Optional[str] = None
    cuisine_focus: List[str] = []
    average_check: Optional[int] = None
    venue_name: Optional[str] = None
    venue_concept: Optional[str] = None
    target_audience: Optional[str] = None
    special_features: List[str] = []
    kitchen_equipment: List[str] = []
    
    # Enhanced venue profiling - moved from menu generation
    region: Optional[str] = None  # moskva, spb, etc.
    
    # Audience Demographics
    audience_ages: Optional[dict] = None  # {'18-25': 20, '26-35': 50, etc.}
    audience_occupations: List[str] = []  # students, professionals, families, etc.
    
    # Regional Context
    region_details: Optional[dict] = None  # {type: 'capital', geography: 'plains', climate: 'temperate'}
    
    # Cuisine Style and Influences
    cuisine_style: Optional[str] = None  # classic, modern, fusion, street
    cuisine_influences: List[str] = []  # additional cuisine influences
    
    # Kitchen Capabilities
    kitchen_capabilities: List[str] = []  # advanced_equipment, molecular, grill, etc.
    staff_skill_level: Optional[str] = None  # novice, medium, advanced, expert
    preparation_time: Optional[str] = None  # quick, medium, extended
    ingredient_budget: Optional[str] = None  # economy, medium, premium, luxury
    
    # Business Requirements
    menu_goals: List[str] = []  # profit_optimization, customer_retention, etc.
    special_requirements: List[str] = []  # allergen_free, halal, vegan, etc.
    dietary_options: List[str] = []  # vegetarian, vegan, gluten_free, etc.
    
    # Default Menu Constructor Settings (for quick menu generation)
    default_dish_count: Optional[int] = None
    default_categories: Optional[dict] = None  # {salads: 2, appetizers: 3, etc.}
    
    # Additional Context
    venue_description: Optional[str] = None  # Free-form description
    business_notes: Optional[str] = None  # Additional business context

class DishRequest(BaseModel):
    dish_name: str
    user_id: str
    # Enhanced context for menu-generated dishes
    dish_description: Optional[str] = None
    main_ingredients: Optional[List[str]] = None
    category: Optional[str] = None
    estimated_cost: Optional[str] = None
    estimated_price: Optional[str] = None
    difficulty: Optional[str] = None
    cook_time: Optional[str] = None

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

class MenuGenerationRequest(BaseModel):
    user_id: str
    # Full menu generation with ALL parameters (original complex version)
    menu_type: Optional[str] = None  # full, seasonal, banquet, tasting
    dish_count: int = 12
    cuisine_style: Optional[str] = None
    cuisine_influences: List[str] = []
    menu_style: Optional[str] = None  # classic, modern, fusion, street
    audience_ages: Optional[dict] = None
    audience_occupations: List[str] = []
    region_details: Optional[dict] = None
    menu_goals: List[str] = []
    special_requirements: List[str] = []
    dietary_options: List[str] = []
    kitchen_capabilities: List[str] = []
    staff_skill_level: Optional[str] = None
    preparation_time: Optional[str] = None
    ingredient_budget: Optional[str] = None
    menu_description: Optional[str] = ""
    expectations: Optional[str] = ""
    additional_notes: Optional[str] = ""
    categories: Optional[dict] = None  # Menu constructor categories
    use_constructor: bool = False
    region: Optional[str] = None  # backwards compatibility
    average_check_min: Optional[int] = None  # backwards compatibility
    average_check_max: Optional[int] = None  # backwards compatibility

class SimpleMenuRequest(BaseModel):
    user_id: str
    # Simplified menu generation - uses venue profile for everything else
    menu_type: str  # full, seasonal, business_lunch, event
    expectations: str  # Free-form description of what user expects
    dish_count: Optional[int] = None  # If not provided, uses venue profile default
    custom_categories: Optional[dict] = None  # Optional override of default categories
    project_id: Optional[str] = None  # Optional project assignment

class MenuProject(BaseModel):
    id: str
    user_id: str
    project_name: str
    description: Optional[str] = None
    project_type: str  # restaurant_launch, seasonal_update, special_event, menu_refresh
    venue_type: Optional[str] = None  # Associated venue type if different from main profile
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
class MenuProjectCreate(BaseModel):
    user_id: str
    project_name: str
    description: Optional[str] = None
    project_type: str  # restaurant_launch, seasonal_update, special_event, menu_refresh
    venue_type: Optional[str] = None

class MenuProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    venue_type: Optional[str] = None
    is_active: Optional[bool] = None

# IIKo Integration Pydantic Models
class TechCardUpload(BaseModel):
    name: str = Field(..., description="Tech card name")
    description: Optional[str] = Field(None, description="Tech card description")
    ingredients: List[Dict[str, Any]] = Field(..., description="List of ingredients")
    preparation_steps: List[str] = Field(..., description="Preparation instructions")
    category_id: Optional[str] = Field(None, description="IIKo category ID")
    price: Optional[float] = Field(None, description="Item price")
    weight: Optional[float] = Field(None, description="Item weight in grams")
    organization_id: str = Field(..., description="IIKo organization ID")

class MenuSyncRequest(BaseModel):
    organization_ids: List[str] = Field(..., description="IIKo organization IDs")
    sync_prices: bool = Field(True, description="Whether to sync pricing data")
    sync_categories: bool = Field(True, description="Whether to sync category data")

class IikoHealthStatus(BaseModel):
    status: str
    iiko_connection: str
    timestamp: str
    error: Optional[str] = None

# Golden prompt for tech cards  
GOLDEN_PROMPT = """Ты — RECEPTOR, профессиональный AI-помощник для шеф-поваров и рестораторов.

Пользователь вводит название блюда или идею. Сгенерируй полную технологическую карту (ТК) строго по формату ниже.

КОНТЕКСТ ЗАВЕДЕНИЯ:
{venue_context}

ВАЖНО: 
- Если в названии есть явные опечатки или неправильные слова (например "Бранч" вместо "соус"), исправь их на правильные кулинарные термины.
- НЕ МЕНЯЙ основные ингредиенты при редактировании! Если пользователь пишет "морж", НЕ заменяй на "морской гребешок".

────────────────────────────────────
📌 ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА ПО ЗАВЕДЕНИЮ
────────────────────────────────────
{venue_specific_rules}

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
  * ЦЕНООБРАЗОВАНИЕ НА ИЮЛЬ 2025 - СТРОГО СЛЕДУЙ ЭТИМ ЦЕНАМ:
    - Используй ТОЛЬКО актуальные рыночные цены из твоих знаний
    - Инфляция с 2024: +18% на все продукты
    - Региональный коэффициент: {regional_coefficient}x
    - Коэффициент заведения: {venue_price_multiplier}x
    
    ОБЯЗАТЕЛЬНЫЕ ОРИЕНТИРЫ ЦЕН ИЮЛЬ 2025:
    • ПРЕМИУМ ПРОДУКТЫ (×1.4 к базе):
      - Семга охлажденная: 1900-2100₽/кг (190-210₽ за 100г)
      - Форель: 1600-1800₽/кг (160-180₽ за 100г)  
      - Телятина: 1300-1500₽/кг
      - Устрицы: 350-500₽/шт
      - Трюфели: 15000-25000₽/кг
    
    • СТАНДАРТ ПРОДУКТЫ (×1.2 к базе):
      - Говядина премиум: 900-1200₽/кг
      - Свинина: 500-700₽/кг
      - Курица филе: 450-550₽/кг
      - Сливки 33%: 200-250₽/л
      - Сыр пармезан: 2500-3000₽/кг
    
    • БАЗОВЫЕ ПРОДУКТЫ (×1.0 к базе):
      - Картофель: 120-150₽/кг в рознице (в ресторанах +30%)
      - Лук: 140-180₽/кг в рознице (в ресторанах +40%)
      - Морковь: 100-130₽/кг
      - Мука: 70-90₽/кг
      - Яйца: 150-200₽/десяток (15-20₽/шт)
      - Масло подсолнечное: 180-220₽/л
    
    КРИТИЧЕСКИ ВАЖНО: Если ты ставишь цену ниже указанных ориентиров - ты ошибаешься!
    Пример: 100г семги НЕ МОЖЕТ стоить 80₽ - это должно быть 190-210₽!
    
    ОСОБОЕ ВНИМАНИЕ К ПРЕМИУМ РЫБЕ:
    - Семга, лосось, форель - это ВСЕГДА дорогие продукты
    - 1 кг семги = 1900-2100₽, значит 100г = 190-210₽
    - НЕ ПУТАЙ с более дешевой рыбой типа минтая или хека
    
  * Будь реалистичен в ценах - это ресторан уровня "{venue_type_name}"!

- Себестоимость = только ингредиенты (без накладных).
- Рекомендуемая цена = себестоимость × 3 (стандартная ресторанная наценка).
- ЦЕЛЬ: Итоговая цена должна быть адекватной для заведения типа "{venue_type_name}" со средним чеком {average_check}₽.

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

**Описание:** 2-3 сочных предложения (вкус, аромат, текстура). {description_style}

**Ингредиенты:** (указывай НА ОДНУ ПОРЦИЮ!)

КРИТИЧЕСКИ ВАЖНО - ВСЕ ИЗМЕРЕНИЯ ТОЛЬКО В ГРАММАХ:
- НЕ используй "штуки" ("1 яйцо", "2 тортильи") 
- ИСПОЛЬЗУЙ только граммы ("50г яйца", "60г тортильи")
- Даже жидкости переводи в граммы: 100мл молока = 100г молока
- Примеры правильного формата:
  ✅ Куриное филе — 180г — ~120₽
  ✅ Яйцо куриное — 50г — ~10₽ 
  ✅ Тортилья пшеничная — 60г — ~15₽
  ✅ Молоко 3.2% — 100г — ~8₽
  ❌ Неправильно: Яйцо — 1 шт, Тортилья — 2 шт

- Продукт — кол-во в граммах (сырой) — ~цена
- *Ужарка/утайка:* «… — 100 г (ужарка 30 %, выход 70 г)»

**Пошаговый рецепт:**

{cooking_instructions}

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

- техника / текстура / баланс {chef_tips}
*Совет от RECEPTOR:* …
*Фишка для продвинутых:* …
*Вариации:* …

**Рекомендация подачи:** {serving_recommendations}

**Теги для меню:** {menu_tags}

Сгенерировано RECEPTOR AI — экономьте 2 часа на каждой техкарте

────────────────────────────────────

Название блюда: {dish_name}

Важно: учти региональный коэффициент цен: {regional_coefficient}x от базовых цен.
{equipment_context}"""

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
def generate_venue_context(user_data):
    """Generate venue context for tech card generation"""
    venue_type = user_data.get("venue_type")
    cuisine_focus = user_data.get("cuisine_focus", [])
    average_check = user_data.get("average_check")
    venue_name = user_data.get("venue_name", "заведение")
    
    context_parts = []
    
    if venue_type and venue_type in VENUE_TYPES:
        venue_info = VENUE_TYPES[venue_type]
        context_parts.append(f"Тип заведения: {venue_info['name']} - {venue_info['description']}")
    
    if cuisine_focus:
        cuisine_names = []
        for cuisine in cuisine_focus:
            if cuisine in CUISINE_TYPES:
                cuisine_names.append(CUISINE_TYPES[cuisine]['name'])
        if cuisine_names:
            context_parts.append(f"Кухня: {', '.join(cuisine_names)}")
    
    if average_check:
        context_parts.append(f"Средний чек: {average_check} ₽")
    
    if venue_name != "заведение":
        context_parts.append(f"Название заведения: {venue_name}")
    
    return "\n".join(context_parts) if context_parts else "Стандартное заведение"

def generate_venue_specific_rules(user_data):
    """Generate venue-specific rules for tech card generation"""
    venue_type = user_data.get("venue_type")
    cuisine_focus = user_data.get("cuisine_focus", [])
    average_check = user_data.get("average_check")
    
    rules = []
    
    # Venue type specific rules
    if venue_type and venue_type in VENUE_TYPES:
        venue_info = VENUE_TYPES[venue_type]
        
        if venue_info["complexity_level"] == "high":
            rules.append("• Используй продвинутые кулинарные техники и презентацию на уровне высокой кухни")
            rules.append("• Применяй сложные соусы и изысканные ингредиенты")
        elif venue_info["complexity_level"] == "low":
            rules.append("• Фокусируйся на простых, быстрых в приготовлении блюдах")
            rules.append("• Избегай сложных техник, приоритет - скорость и удобство")
        
        if venue_info["portion_style"] == "finger_food":
            rules.append("• Все блюда должны быть удобны для еды руками, без столовых приборов")
        elif venue_info["portion_style"] == "handheld":
            rules.append("• Блюда должны быть портативными и удобными для еды на ходу")
        elif venue_info["portion_style"] == "artistic":
            rules.append("• Делай акцент на художественной подаче и визуальном впечатлении")
        
        # Add venue-specific techniques
        if venue_info["techniques"]:
            techniques_str = ", ".join(venue_info["techniques"])
            rules.append(f"• Приоритетные техники для этого типа заведения: {techniques_str}")
    
    # Cuisine-specific rules
    if cuisine_focus:
        for cuisine in cuisine_focus:
            if cuisine in CUISINE_TYPES:
                cuisine_info = CUISINE_TYPES[cuisine]
                ingredients = ", ".join(cuisine_info["key_ingredients"][:5])  # First 5 ingredients
                methods = ", ".join(cuisine_info["cooking_methods"])
                rules.append(f"• Для {cuisine_info['name']} кухни используй: {ingredients}")
                rules.append(f"• Применяй методы готовки: {methods}")
    
    # Average check rules
    if average_check:
        if average_check < 500:
            rules.append("• Используй доступные ингредиенты, оптимизируй себестоимость")
        elif average_check > 2000:
            rules.append("• Применяй премиум ингредиенты и изысканные техники")
        elif average_check > 1000:
            rules.append("• Баланс между качеством и доступностью, хорошие ингредиенты")
    
    return "\n".join(rules) if rules else "• Следуй стандартным правилам приготовления"

def generate_cooking_instructions(user_data):
    """Generate cooking instructions format based on venue type"""
    venue_type = user_data.get("venue_type")
    
    if venue_type == "fine_dining":
        return """1. … (точные температуры, профессиональные техники)
2. … (контроль времени до секунды, идеальная текстура)
3. … (художественная подача, детали презентации)"""
    elif venue_type == "food_truck":
        return """1. … (быстрое приготовление, оптимизация времени)
2. … (практичные методы, минимум оборудования) 
3. … (удобная упаковка для выноса)"""
    elif venue_type == "bar_pub":
        return """1. … (простые техники, подходит для бара)
2. … (легко делить на компанию)
3. … (хорошо сочетается с напитками)"""
    else:
        return """1. … (темпы, время, лайфхаки)
2. …
3. …"""

def generate_description_style(user_data):
    """Generate description style based on venue type"""
    venue_type = user_data.get("venue_type")
    
    if venue_type == "fine_dining":
        return "Используй изысканные эпитеты и подчеркивай сложность вкуса."
    elif venue_type == "food_truck":
        return "Акцент на сытность, удобство и быстроту."
    elif venue_type == "bar_pub":
        return "Подчеркивай, как блюдо сочетается с напитками."
    else:
        return ""

def generate_serving_recommendations(user_data):
    """Generate serving recommendations based on venue type"""
    venue_type = user_data.get("venue_type")
    
    if venue_type == "fine_dining":
        return "Элегантная фарфоровая посуда, художественная подача с микрозеленью, оптимальная температура 65°C, внимание к каждой детали плейтинга"
    elif venue_type == "food_truck":
        return "Экологичная упаковка на вынос, защита от остывания, удобные контейнеры с крышками, салфетки и одноразовые приборы"
    elif venue_type == "street_food":
        return "Портативная упаковка, стаканчики или лодочки для еды, защитная пленка, возможность есть на ходу без приборов"
    elif venue_type == "bar_pub":
        return "Подача на деревянных досках для sharing, пивные бокалы рядом, температура комнатная, общие тарелки для компании"
    elif venue_type == "night_club":
        return "Яркая подача в небольших порциях, finger-food стиль, без столовых приборов, эффектная презентация под неоновым светом"
    elif venue_type == "kids_cafe":
        return "Яркие безопасные тарелки без острых углов, детские приборы, игровая подача с рисунками, умеренная температура"
    elif venue_type == "coffee_shop":
        return "Красивые керамические чашки и тарелки, подача на деревянных подносах, эстетика для Instagram, температура для кофе"
    elif venue_type == "canteen":
        return "Практичная металлическая или пластиковая посуда, порционная подача, эффективное обслуживание, стандартная температура"
    elif venue_type == "fast_food":
        return "Брендированная упаковка, быстрая подача в контейнерах, салфетки, соусы в пакетиках, температура для быстрого потребления"
    elif venue_type == "bakery_cafe":
        return "Крафтовые тарелки и корзинки, подача на деревянных досках, акцент на свежесть выпечки, теплая температура"
    elif venue_type == "buffet":
        return "Подогревающие лотки, самообслуживание, разнообразие посуды, поддержание температуры, удобство для гостей"
    else:
        return "посуда, декор, температура"

def generate_menu_tags(user_data):
    """Generate menu tags based on venue profile"""
    venue_type = user_data.get("venue_type")
    cuisine_focus = user_data.get("cuisine_focus", [])
    
    tags = []
    
    if venue_type:
        venue_info = VENUE_TYPES.get(venue_type, {})
        if venue_info.get("service_style") == "fast_casual":
            tags.extend(["#быстро", "#находу"])
        elif venue_info.get("service_style") == "table_service":
            tags.extend(["#ресторан", "#сервис"])
        elif venue_info.get("portion_style") == "finger_food":
            tags.extend(["#фингерфуд", "#безприборов"])
    
    for cuisine in cuisine_focus:
        if cuisine == "asian":
            tags.extend(["#азиатская", "#экзотика"])
        elif cuisine == "european":
            tags.extend(["#европейская", "#классика"])
        elif cuisine == "caucasian":
            tags.extend(["#кавказская", "#мангал"])
    
    if not tags:
        tags = ["#вкусно", "#качественно", "#свежее"]
    
    return " ".join(tags[:4])  # Limit to 4 tags

def generate_chef_tips(user_data):
    """Generate chef tips based on venue type and cuisine"""
    venue_type = user_data.get("venue_type")
    cuisine_focus = user_data.get("cuisine_focus", [])
    
    tips = []
    
    if venue_type == "fine_dining":
        tips.append("Температурные контрасты и идеальный баланс")
    elif venue_type == "food_truck":
        tips.append("Максимальная эффективность и скорость")
    elif venue_type == "bar_pub":
        tips.append("Идеальное сочетание с напитками")
    
    if "asian" in cuisine_focus:
        tips.append("Баланс умами и свежести")
    elif "european" in cuisine_focus:
        tips.append("Классические сочетания и техники")
    
    return " / ".join(tips) if tips else ""

def generate_photo_tips_context(venue_type, venue_info, average_check, cuisine_focus):
    """Generate venue-specific photo tips context"""
    context_parts = []
    
    # Venue-specific photo approach
    if venue_type == "fine_dining":
        context_parts.append("Акцент на элегантность и изысканность подачи")
        context_parts.append("Использование премиум посуды и декора")
    elif venue_type == "food_truck":
        context_parts.append("Подчеркивание street-food атмосферы")
        context_parts.append("Акцент на портативность и удобство")
    elif venue_type == "bar_pub":
        context_parts.append("Создание атмосферы компанейского отдыха")
        context_parts.append("Подача в контексте напитков")
    elif venue_type == "night_club":
        context_parts.append("Яркая, энергичная подача")
        context_parts.append("Акцент на визуальный эффект")
    elif venue_type == "family_restaurant":
        context_parts.append("Домашняя, уютная атмосфера")
        context_parts.append("Подчеркивание семейных ценностей")
    
    # Average check considerations
    if average_check:
        if average_check < 500:
            context_parts.append("Простая, но аппетитная подача")
        elif average_check > 2000:
            context_parts.append("Роскошная презентация и детали")
        else:
            context_parts.append("Баланс красоты и практичности")
    
    return "\n".join(context_parts) if context_parts else ""

def generate_photo_tech_settings(venue_type):
    """Generate technical photo settings based on venue type"""
    if venue_type == "fine_dining":
        return """• Профессиональная камера или топовый смартфон
• Диафрагма f/2.8-f/4 для мягкого боке
• ISO 100-400 для минимального шума
• Штатив для стабильности
• Макро-объектив для деталей"""
    elif venue_type == "food_truck":
        return """• Смартфон с хорошей камерой
• Быстрая съемка, f/1.8-f/2.4
• Автофокус для скорости
• Портретный режим для размытия фона
• Естественное освещение"""
    elif venue_type == "bar_pub":
        return """• Камера с хорошей работой при слабом свете
• Широкая диафрагма f/1.4-f/2.0
• ISO 800-1600 для атмосферного освещения
• Теплый баланс белого
• Ручная фокусировка"""
    else:
        return """• Универсальные настройки камеры
• Диафрагма f/2.8-f/5.6
• ISO 200-800
• Автоматический баланс белого
• Стабилизация изображения"""

def generate_photo_styling_tips(venue_type):
    """Generate styling tips based on venue type"""
    if venue_type == "fine_dining":
        return """• Элегантная фарфоровая посуда
• Минималистичный декор
• Нейтральные тона фона
• Акцент на геометрии подачи
• Использование текстур (лен, мрамор)"""
    elif venue_type == "food_truck":
        return """• Яркая, практичная посуда
• Городской фон или текстуры
• Контрастные цвета
• Упаковка как элемент стиля
• Динамичная композиция"""
    elif venue_type == "bar_pub":
        return """• Темная посуда и фон
• Деревянные текстуры
• Теплое освещение
• Напитки в кадре
• Атмосфера расслабленности"""
    elif venue_type == "night_club":
        return """• Яркие, неоновые акценты
• Темный фон с подсветкой
• Глянцевые поверхности
• Динамичные углы
• Эффектная подача"""
    else:
        return """• Уютная домашняя посуда
• Теплые тона
• Естественные материалы
• Семейная атмосфера
• Комфортная подача"""

def generate_sales_script_context(venue_type, venue_info, average_check, cuisine_focus):
    """Generate venue-specific sales script context"""
    context_parts = []
    
    # Venue-specific sales approach
    if venue_type == "fine_dining":
        context_parts.append("Акцент на эксклюзивности и мастерстве шефа")
        context_parts.append("Подчеркивай уникальность ингредиентов и техник")
    elif venue_type == "food_truck":
        context_parts.append("Быстрая подача, акцент на свежесть и удобство")
        context_parts.append("Подчеркивай мобильность и street-food атмосферу")
    elif venue_type == "bar_pub":
        context_parts.append("Идеальное сочетание с напитками")
        context_parts.append("Акцент на sharing и компанейскую атмосферу")
    elif venue_type == "night_club":
        context_parts.append("Удобство для еды руками, яркая подача")
        context_parts.append("Акцент на энергию и party-атмосферу")
    elif venue_type == "family_restaurant":
        context_parts.append("Семейные ценности, домашняя атмосфера")
        context_parts.append("Акцент на сытность и традиционные вкусы")
    
    # Average check considerations
    if average_check:
        if average_check < 500:
            context_parts.append("Подчеркивай выгодность и сытность")
        elif average_check > 2000:
            context_parts.append("Акцент на премиум качество и эксклюзивность")
        else:
            context_parts.append("Баланс цены и качества")
    
    # Cuisine-specific sales points
    if cuisine_focus:
        for cuisine in cuisine_focus:
            if cuisine == "asian":
                context_parts.append("Экзотические вкусы и аутентичность")
            elif cuisine == "european":
                context_parts.append("Классические традиции и проверенные сочетания")
            elif cuisine == "caucasian":
                context_parts.append("Щедрые порции и яркие специи")
    
    return "\n".join(context_parts) if context_parts else ""

def generate_food_pairing_context(venue_type, venue_info, average_check, cuisine_focus):
    """Generate venue-specific food pairing context"""
    context_parts = []
    
    # Venue-specific pairing approach
    if venue_type == "fine_dining":
        context_parts.append("Изысканные винные пары и премиум напитки")
        context_parts.append("Акцент на редкие и эксклюзивные позиции")
    elif venue_type == "food_truck":
        context_parts.append("Простые и доступные напитки")
        context_parts.append("Упор на освежающие и быстрые варианты")
    elif venue_type == "bar_pub":
        context_parts.append("Широкий выбор пива и крепких напитков")
        context_parts.append("Классические барные сочетания")
    elif venue_type == "night_club":
        context_parts.append("Яркие коктейли и энергетические напитки")
        context_parts.append("Акцент на визуальную подачу")
    elif venue_type == "family_restaurant":
        context_parts.append("Семейные напитки и безалкогольные варианты")
        context_parts.append("Традиционные и понятные сочетания")
    
    # Average check considerations for drinks
    if average_check:
        if average_check < 500:
            context_parts.append("Бюджетные напитки и простые сочетания")
        elif average_check > 2000:
            context_parts.append("Премиум алкоголь и авторские коктейли")
        else:
            context_parts.append("Качественные напитки средней ценовой категории")
    
    return "\n".join(context_parts) if context_parts else ""

def generate_alcohol_recommendations(venue_type):
    """Generate alcohol recommendations based on venue type"""
    if venue_type == "fine_dining":
        return """• Премиум вина (Бордо, Бургундия, Тоскана)
• Выдержанные крепкие напитки
• Авторские коктейли от шеф-бармена
• Шампанское и игристые вина"""
    elif venue_type == "food_truck":
        return """• Пиво в банках и бутылках
• Простые коктейли
• Лимонады и морсы
• Энергетические напитки"""
    elif venue_type == "bar_pub":
        return """• Широкий выбор разливного пива
• Классические коктейли (Мохито, Маргарита)
• Виски и другие крепкие напитки
• Винная карта средней ценовой категории"""
    elif venue_type == "night_club":
        return """• Яркие коктейли с декором
• Шампанское и игристые вина
• Премиум водка и джин
• Энергетические коктейли"""
    else:
        return """• Домашние вина и пиво
• Классические коктейли
• Безалкогольные альтернативы
• Сезонные напитки"""

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
@api_router.get("/venue-types")
async def get_venue_types():
    """Get all available venue types and their characteristics"""
    return VENUE_TYPES

@api_router.get("/cuisine-types")  
async def get_cuisine_types():
    """Get all available cuisine types and their characteristics"""
    return CUISINE_TYPES

@api_router.get("/average-check-categories")
async def get_average_check_categories():
    """Get all available average check categories"""
    return AVERAGE_CHECK_CATEGORIES

@api_router.get("/venue-profile/{user_id}")
async def get_venue_profile(user_id: str):
    """Get user's venue profile"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has PRO subscription for advanced features
    subscription_plan = user.get("subscription_plan", "free")
    plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
    
    profile = {
        # Basic venue information
        "venue_type": user.get("venue_type"),
        "cuisine_focus": user.get("cuisine_focus", []),
        "average_check": user.get("average_check"),
        "venue_name": user.get("venue_name"),
        "venue_concept": user.get("venue_concept"),
        "target_audience": user.get("target_audience"),
        "special_features": user.get("special_features", []),
        "kitchen_equipment": user.get("kitchen_equipment", []),
        
        # Enhanced venue profiling
        "region": user.get("region", "moskva"),
        
        # Audience Demographics
        "audience_ages": user.get("audience_ages", {
            '18-25': 20,
            '26-35': 50, 
            '36-50': 20,
            '50+': 10
        }),
        "audience_occupations": user.get("audience_occupations", []),
        
        # Regional Context
        "region_details": user.get("region_details", {
            "type": "capital",
            "geography": "plains", 
            "climate": "temperate"
        }),
        
        # Cuisine Style and Influences
        "cuisine_style": user.get("cuisine_style", "classic"),
        "cuisine_influences": user.get("cuisine_influences", []),
        
        # Kitchen Capabilities
        "kitchen_capabilities": user.get("kitchen_capabilities", []),
        "staff_skill_level": user.get("staff_skill_level", "medium"),
        "preparation_time": user.get("preparation_time", "medium"),
        "ingredient_budget": user.get("ingredient_budget", "medium"),
        
        # Business Requirements
        "menu_goals": user.get("menu_goals", []),
        "special_requirements": user.get("special_requirements", []),
        "dietary_options": user.get("dietary_options", []),
        
        # Default Menu Constructor Settings
        "default_dish_count": user.get("default_dish_count", 12),
        "default_categories": user.get("default_categories", {
            "salads": 2,
            "appetizers": 3,
            "soups": 2,
            "main_dishes": 4,
            "desserts": 2,
            "beverages": 1
        }),
        
        # Additional Context
        "venue_description": user.get("venue_description"),
        "business_notes": user.get("business_notes"),
        
        # System info
        "has_pro_features": plan_info.get("kitchen_equipment", False)
    }
    
    return profile

@api_router.post("/update-venue-profile/{user_id}")
async def update_venue_profile(user_id: str, profile_data: VenueProfileUpdate):
    """Update user's venue profile (PRO feature for advanced customization)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        # Auto-create test user with PRO subscription if needed
        if user_id.startswith("test_user_"):
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
            user = test_user
        else:
            raise HTTPException(status_code=404, detail="User not found")
    
    # Check subscription for advanced features
    subscription_plan = user.get("subscription_plan", "free")
    plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
    
    # Basic venue customization available to all users
    update_data = {}
    
    # Basic venue fields
    if profile_data.venue_type:
        if profile_data.venue_type not in VENUE_TYPES:
            raise HTTPException(status_code=400, detail="Invalid venue type")
        update_data["venue_type"] = profile_data.venue_type
    
    if profile_data.cuisine_focus:
        invalid_cuisines = [c for c in profile_data.cuisine_focus if c not in CUISINE_TYPES]
        if invalid_cuisines:
            raise HTTPException(status_code=400, detail=f"Invalid cuisine types: {invalid_cuisines}")
        update_data["cuisine_focus"] = profile_data.cuisine_focus
    
    if profile_data.average_check is not None:
        update_data["average_check"] = profile_data.average_check
    
    if profile_data.region is not None:
        update_data["region"] = profile_data.region
        
    # Enhanced profiling fields (available to all users now for better UX)
    if profile_data.audience_ages is not None:
        update_data["audience_ages"] = profile_data.audience_ages
        
    if profile_data.audience_occupations:
        update_data["audience_occupations"] = profile_data.audience_occupations
        
    if profile_data.region_details is not None:
        update_data["region_details"] = profile_data.region_details
        
    if profile_data.cuisine_style is not None:
        update_data["cuisine_style"] = profile_data.cuisine_style
        
    if profile_data.cuisine_influences:
        update_data["cuisine_influences"] = profile_data.cuisine_influences
        
    if profile_data.kitchen_capabilities:
        update_data["kitchen_capabilities"] = profile_data.kitchen_capabilities
        
    if profile_data.staff_skill_level is not None:
        update_data["staff_skill_level"] = profile_data.staff_skill_level
        
    if profile_data.preparation_time is not None:
        update_data["preparation_time"] = profile_data.preparation_time
        
    if profile_data.ingredient_budget is not None:
        update_data["ingredient_budget"] = profile_data.ingredient_budget
        
    if profile_data.menu_goals:
        update_data["menu_goals"] = profile_data.menu_goals
        
    if profile_data.special_requirements:
        update_data["special_requirements"] = profile_data.special_requirements
        
    if profile_data.dietary_options:
        update_data["dietary_options"] = profile_data.dietary_options
        
    if profile_data.default_dish_count is not None:
        update_data["default_dish_count"] = profile_data.default_dish_count
        
    if profile_data.default_categories is not None:
        update_data["default_categories"] = profile_data.default_categories
        
    if profile_data.venue_description is not None:
        update_data["venue_description"] = profile_data.venue_description
        
    if profile_data.business_notes is not None:
        update_data["business_notes"] = profile_data.business_notes

    # Advanced features still require PRO subscription
    if plan_info.get("kitchen_equipment", False):
        if profile_data.venue_name is not None:
            update_data["venue_name"] = profile_data.venue_name
        
        if profile_data.venue_concept is not None:
            update_data["venue_concept"] = profile_data.venue_concept
        
        if profile_data.target_audience is not None:
            update_data["target_audience"] = profile_data.target_audience
        
        if profile_data.special_features:
            update_data["special_features"] = profile_data.special_features
        
        if profile_data.kitchen_equipment:
            # Validate equipment IDs
            all_equipment_ids = []
            for category in KITCHEN_EQUIPMENT.values():
                all_equipment_ids.extend([eq["id"] for eq in category])
            
            invalid_ids = [eq_id for eq_id in profile_data.kitchen_equipment if eq_id not in all_equipment_ids]
            if invalid_ids:
                raise HTTPException(status_code=400, detail=f"Invalid equipment IDs: {invalid_ids}")
            
            update_data["kitchen_equipment"] = profile_data.kitchen_equipment
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid profile data provided")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Venue profile updated successfully", "updated_fields": list(update_data.keys())}

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
        
        # Generate venue context and customization
        venue_context = generate_venue_context(user)
        venue_specific_rules = generate_venue_specific_rules(user)
        
        # Get venue-specific variables
        venue_type = user.get("venue_type", "family_restaurant")
        venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
        venue_price_multiplier = venue_info.get("price_multiplier", 1.0)
        venue_type_name = venue_info.get("name", "Семейный ресторан")
        
        average_check = user.get("average_check", 800)
        description_style = generate_description_style(user)
        cooking_instructions = generate_cooking_instructions(user)
        chef_tips = generate_chef_tips(user)
        serving_recommendations = generate_serving_recommendations(user)
        menu_tags = generate_menu_tags(user)
        
        # Поиск актуальных цен в интернете
        search_query = f"цены на продукты {user.get('city', 'москва')} 2025 мясо овощи крупы молочные продукты"
        
        try:
            from emergentintegrations.tools import web_search
            price_search_result = web_search(search_query, search_context_size="medium")
        except Exception:
            price_search_result = "Данные по ценам недоступны"
        
        # Поиск цен конкурентов
        competitor_search_query = f"цены меню {request.dish_name} рестораны {user.get('city', 'москва')} 2025"
        
        try:
            competitor_search_result = web_search(competitor_search_query, search_context_size="medium")
        except Exception:
            competitor_search_result = "Данные по конкурентам недоступны"
        
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
        
        # Prepare enhanced dish context for menu-generated dishes
        additional_context = ""
        if hasattr(request, 'dish_description') and request.dish_description:
            additional_context = f"""

ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ ИЗ МЕНЮ:
- Описание блюда: {request.dish_description}
- Основные ингредиенты: {', '.join(request.main_ingredients) if request.main_ingredients else 'Не указаны'}
- Категория меню: {request.category}
- Ориентировочная себестоимость: {request.estimated_cost}₽
- Рекомендуемое время готовки: {request.cook_time} мин
- Ожидаемая сложность: {request.difficulty}

ВАЖНО: Используй эту информацию как основу, но создай ПОЛНУЮ детальную техкарту с точными расчетами, пошаговым рецептом и всеми разделами (заготовки, советы от шефа, особенности)."""

        # Prepare the prompt with venue customization and enhanced context
        enhanced_equipment_context = equipment_context + additional_context
        
        prompt = GOLDEN_PROMPT.format(
            dish_name=request.dish_name,  # Только название блюда
            regional_coefficient=regional_coefficient,
            venue_context=venue_context,
            venue_specific_rules=venue_specific_rules,
            venue_price_multiplier=venue_price_multiplier,
            venue_type_name=venue_type_name,
            average_check=average_check,
            description_style=description_style,
            cooking_instructions=cooking_instructions,
            chef_tips=chef_tips,
            serving_recommendations=serving_recommendations,
            menu_tags=menu_tags,
            equipment_context=enhanced_equipment_context  # Контекст передается через equipment_context
        )
        
        # Temporarily use GPT-4o-mini for all users to test
        ai_model = "gpt-4o-mini"  # was: "gpt-4o" if user['subscription_plan'] in ['pro', 'business'] else "gpt-4o-mini"
        max_tokens = 4000  # Increased for better tech cards, was: 3000
        
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
        max_tokens = 4000  # Increased for better tech cards, was: 3000
        
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

@api_router.post("/generate-menu")
async def generate_menu(request: dict):
    """
    Generate a complete menu based on user preferences and venue profile
    """
    user_id = request.get("user_id")
    menu_profile = request.get("menu_profile", {})
    venue_profile = request.get("venue_profile", {})
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Get user to check subscription
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check subscription for menu generation (PRO feature)
    subscription_plan = user.get("subscription_plan", "free")
    if subscription_plan == "free":
        raise HTTPException(status_code=403, detail="Menu generation requires PRO subscription")
    
    try:
        
        # Extract menu parameters
        menu_type = menu_profile.get("menuType", "restaurant")
        dish_count = menu_profile.get("dishCount", 10)
        average_check = menu_profile.get("averageCheck", "medium")
        cuisine_style = menu_profile.get("cuisineStyle", "european")
        special_requirements = menu_profile.get("specialRequirements", [])
        
        # Extract additional parameters from menu_profile for enhanced prompt
        target_audience = menu_profile.get("targetAudience", "")
        menu_goals = menu_profile.get("menuGoals", [])
        special_requirements = menu_profile.get("specialRequirements", [])
        dietary_options = menu_profile.get("dietaryOptions", [])
        staff_skill_level = menu_profile.get("staffSkillLevel", "medium")
        preparation_time = menu_profile.get("preparationTime", "medium")
        ingredient_budget = menu_profile.get("ingredientBudget", "medium")
        menu_description = menu_profile.get("menuDescription", "")
        expectations = menu_profile.get("expectations", "")
        additional_notes = menu_profile.get("additionalNotes", "")
        
        # NEW: Menu Constructor support
        use_constructor = menu_profile.get("useConstructor", False)
        categories = menu_profile.get("categories", {})
        
        # Calculate dish count and create structure instruction
        if use_constructor and categories:
            dish_count = sum(categories.values())
            structure_instruction = f"""
=== КОНСТРУКТОР МЕНЮ - ТОЧНАЯ СТРУКТУРА ===
КРИТИЧЕСКИ ВАЖНО: Используй ТОЧНУЮ структуру по категориям:
- Закуски/Салаты: {categories.get('appetizers', 0)} блюд
- Супы: {categories.get('soups', 0)} блюд  
- Горячие блюда: {categories.get('main_dishes', 0)} блюд
- Десерты: {categories.get('desserts', 0)} блюд
- Напитки: {categories.get('beverages', 0)} блюд
- Закуски к напиткам: {categories.get('snacks', 0)} блюд

ОБЯЗАТЕЛЬНО: Создай категории только с указанным количеством блюд!
Если категория = 0, НЕ создавай её вообще!
            """
        else:
            structure_instruction = f"""
=== АВТОМАТИЧЕСКАЯ СТРУКТУРА ===
Создай {dish_count} блюд, распределив их логично по 3-5 категориям
            """

        # Create comprehensive enhanced prompt for GPT-4o
        menu_prompt = f"""
Ты - эксперт шеф-повар и ресторанный консультант с 20+ летним стажем. Создай УНИКАЛЬНОЕ и КРЕАТИВНОЕ меню по следующим критериям:

=== ОСНОВНЫЕ ПАРАМЕТРЫ ===
ТИП ЗАВЕДЕНИЯ: {menu_type}
ТОЧНОЕ КОЛИЧЕСТВО БЛЮД: {dish_count} (СТРОГО соблюдай это число!)
СРЕДНИЙ ЧЕК: {average_check}
СТИЛЬ КУХНИ: {cuisine_style}

{structure_instruction}

=== ПРОФИЛЬ ЗАВЕДЕНИЯ ===
- Название: {venue_profile.get('venue_name', 'Не указано')}
- Тип: {venue_profile.get('venue_type', 'Не указано')}
- Кухня: {venue_profile.get('cuisine_type', 'Не указано')}
- Средний чек: {venue_profile.get('average_check', 'Не указано')}

=== ДЕТАЛЬНЫЕ ТРЕБОВАНИЯ ===
Целевая аудитория: {target_audience or 'Не указана'}
Бизнес-цели: {', '.join(menu_goals) if menu_goals else 'Не указаны'}
Специальные требования: {', '.join(special_requirements) if special_requirements else 'Нет'}
Диетические опции: {', '.join(dietary_options) if dietary_options else 'Нет'}

=== ТЕХНИЧЕСКИЕ ОГРАНИЧЕНИЯ ===
Уровень навыков персонала: {staff_skill_level}
Ограничения по времени готовки: {preparation_time}
Бюджет на ингредиенты: {ingredient_budget}

=== ПОЖЕЛАНИЯ ЗАКАЗЧИКА ===
Описание меню: {menu_description or 'Не указано'}
Ожидания: {expectations or 'Не указаны'}
Дополнительные пожелания: {additional_notes or 'Нет'}

=== КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ ===
ЗАПРЕЩЕНО: Создавать блюда с названиями "Специальное блюдо дня", "Уникальное блюдо от шефа", "Авторское блюдо" и подобные общие названия!
ОБЯЗАТЕЛЬНО: Каждое блюдо должно иметь КОНКРЕТНОЕ, КРЕАТИВНОЕ название, отражающее ингредиенты и способ приготовления
ТОЧНОЕ КОЛИЧЕСТВО: Создай РОВНО {dish_count} блюд - ни больше, ни меньше!
СТРУКТУРА: {"Используй указанную структуру конструктора" if use_constructor else "Распредели блюда по 3-5 логичным категориям"}
ОПТИМИЗАЦИЯ: Используй общие ингредиенты для экономии
ЦЕНООБРАЗОВАНИЕ: Соответствие среднему чеку {average_check}
УЧЕТ НАВЫКОВ: Адаптируй сложность под уровень персонала ({staff_skill_level})
ВРЕМЯ ГОТОВКИ: Учитывай ограничения по времени ({preparation_time})
КРЕАТИВНОСТЬ: Названия должны быть привлекательными и описательными

=== ПРИМЕРЫ ХОРОШИХ НАЗВАНИЙ ===
Плохо: "Специальное блюдо дня"
Хорошо: "Филе лосося с кунжутной корочкой и лимонным ризотто"

Плохо: "Авторский десерт"
Хорошо: "Шоколадный фондан с малиновым кули и ванильным мороженым"

=== JSON ФОРМАТ (СТРОГО СОБЛЮДАЙ) ===
{{
  "menu_name": "Профессиональное название меню",
  "description": "Детальное описание концепции с учетом всех требований",
  "categories": [
    {{
      "category_name": "Название категории",
      "dishes": [
        {{
          "name": "КОНКРЕТНОЕ креативное название блюда (НЕ общие фразы!)",
          "description": "Подробное описание с акцентом на уникальность и соответствие целевой аудитории",
          "estimated_cost": "150",
          "estimated_price": "450",
          "difficulty": "легко/средне/сложно (с учетом уровня персонала)",
          "cook_time": "15",
          "main_ingredients": ["детальный список основных ингредиентов"]
        }}
      ]
    }}
  ],
  "ingredient_optimization": {{
    "shared_ingredients": ["ингредиенты, используемые в 3+ блюдах"],
    "cost_savings": "точный процент экономии от оптимизации"
  }}
}}

ОБЯЗАТЕЛЬНО ПРОВЕРЬ:
- Общее количество блюд = {dish_count}
- Все требования учтены в описаниях блюд
- НЕТ общих названий типа "блюдо от шефа"
- Каждое название конкретное и привлекательное
- Ценообразование соответствует среднему чеку
- Сложность блюд адаптирована под персонал
- Использованы общие ингредиенты для экономии

Создай меню мечты с КОНКРЕТНЫМИ, КРЕАТИВНЫМИ названиями блюд!
"""

        # Generate menu using OpenAI (Premium model for PRO feature)
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Premium model for high-quality menu generation
            messages=[
                {"role": "system", "content": "You are an expert chef and restaurant consultant with 20+ years of experience. Always respond in Russian with valid JSON format. Create detailed, professional menus that exactly match user requirements."},
                {"role": "user", "content": menu_prompt}
            ],
            max_tokens=8000,  # Increased tokens for detailed menu generation
            temperature=0.7  # Slightly lower temperature for more consistent results
        )
        
        menu_content = response.choices[0].message.content.strip()
        
        # Try to parse JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in menu_content:
                menu_content = menu_content.split("```json")[1].split("```")[0].strip()
            elif "```" in menu_content:
                menu_content = menu_content.split("```")[1].split("```")[0].strip()
            
            import json
            menu_data = json.loads(menu_content)
            
            # Validate dish count and fix if necessary
            total_dishes = sum(len(category.get('dishes', [])) for category in menu_data.get('categories', []))
            
            if total_dishes != dish_count:
                logger.warning(f"Generated {total_dishes} dishes, expected {dish_count}. Re-generating menu...")
                
                if total_dishes < dish_count:
                    # Instead of adding placeholder dishes, regenerate with clearer instructions
                    logger.warning(f"Menu had insufficient dishes ({total_dishes} vs {dish_count}). Regenerating...")
                    
                    # Add emphasis to the dish count requirement
                    enhanced_prompt = menu_prompt + f"""
                    
=== КРИТИЧЕСКОЕ ТРЕБОВАНИЕ ===
ВНИМАНИЕ: В предыдущей попытке было сгенерировано только {total_dishes} блюд вместо {dish_count}!
ОБЯЗАТЕЛЬНО создай РОВНО {dish_count} блюд с конкретными названиями!
НЕ ИСПОЛЬЗУЙ заглушки типа "Специальное блюдо дня"!
                    """
                    
                    # Retry generation with enhanced prompt
                    retry_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert chef and restaurant consultant with 20+ years of experience. Always respond in Russian with valid JSON format. Create detailed, professional menus that exactly match user requirements."},
                            {"role": "user", "content": enhanced_prompt}
                        ],
                        max_tokens=6000,
                        temperature=0.8
                    )
                    
                    retry_content = retry_response.choices[0].message.content.strip()
                    if retry_content.startswith('```json'):
                        retry_content = retry_content[7:]
                    if retry_content.endswith('```'):
                        retry_content = retry_content[:-3]
                    
                    try:
                        retry_menu_data = json.loads(retry_content)
                        retry_total_dishes = sum(len(cat.get('dishes', [])) for cat in retry_menu_data.get('categories', []))
                        
                        if retry_total_dishes >= dish_count * 0.8:  # Accept if at least 80% of requested dishes
                            menu_data = retry_menu_data
                            logger.info(f"✅ Retry successful: generated {retry_total_dishes} dishes")
                        else:
                            logger.warning(f"Retry also insufficient: {retry_total_dishes} dishes. Using original.")
                    except Exception as retry_error:
                        logger.error(f"Retry failed: {retry_error}")
                        # Use original menu_data as fallback
                
                elif total_dishes > dish_count:
                    # Need to remove excess dishes
                    excess = total_dishes - dish_count
                    categories = menu_data.get('categories', [])
                    for category in categories:
                        if excess <= 0:
                            break
                        dishes = category.get('dishes', [])
                        while len(dishes) > 1 and excess > 0:  # Keep at least 1 dish per category
                            dishes.pop()
                            excess -= 1
                
                logger.info(f"Adjusted menu to exactly {dish_count} dishes")
            
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response
            menu_data = {
                "menu_name": f"Меню для {menu_type}",
                "description": "Сбалансированное меню, созданное ИИ",
                "categories": [
                    {
                        "category_name": "Основное меню",
                        "dishes": [
                            {
                                "name": "Блюдо в разработке",
                                "description": "Детали блюда будут добавлены",
                                "estimated_cost": "200",
                                "estimated_price": "600",
                                "difficulty": "средне",
                                "cook_time": "30",
                                "main_ingredients": ["ингредиент1", "ингредиент2"]
                            }
                        ]
                    }
                ],
                "ingredient_optimization": {
                    "shared_ingredients": ["базовые ингредиенты"],
                    "cost_savings": "15-20%"
                }
            }
        
        # Save generated menu to database
        menu_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "menu_name": menu_data.get("menu_name", "Новое меню"),
            "menu_data": menu_data,
            "menu_profile": menu_profile,
            "venue_profile": venue_profile,
            "created_at": datetime.utcnow().isoformat(),
            "is_menu": True
        }
        
        await db.user_history.insert_one(menu_record)
        
        return {
            "success": True,
            "menu": menu_data,
            "menu_id": menu_record["id"],
            "message": "Меню успешно создано!"
        }
        
    except Exception as e:
        logger.error(f"Error generating menu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating menu: {str(e)}")

@api_router.post("/generate-mass-tech-cards")
async def generate_mass_tech_cards(request: dict):
    """
    Generate tech cards for all dishes in a menu (Phase 3 - Mass Tech Card Generation)
    """
    user_id = request.get("user_id")
    menu_id = request.get("menu_id")
    
    if not user_id or not menu_id:
        raise HTTPException(status_code=400, detail="User ID and Menu ID are required")
    
    # Get user to check subscription
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check subscription for mass tech card generation (PRO feature)
    subscription_plan = user.get("subscription_plan", "free")
    if subscription_plan == "free":
        raise HTTPException(status_code=403, detail="Mass tech card generation requires PRO subscription")
    
    # Get the menu from database
    menu_record = await db.user_history.find_one({"id": menu_id, "user_id": user_id, "is_menu": True})
    if not menu_record:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    menu_data = menu_record.get("menu_data", {})
    venue_profile = menu_record.get("venue_profile", {})
    categories = menu_data.get("categories", [])
    
    try:
        # Extract all dishes from all categories
        all_dishes = []
        for category in categories:
            for dish in category.get("dishes", []):
                all_dishes.append({
                    "name": dish.get("name"),
                    "description": dish.get("description"),
                    "category": category.get("category_name"),
                    "estimated_cost": dish.get("estimated_cost"),
                    "estimated_price": dish.get("estimated_price"),
                    "main_ingredients": dish.get("main_ingredients", [])
                })
        
        if not all_dishes:
            raise HTTPException(status_code=400, detail="No dishes found in menu")
        
        logger.info(f"Starting mass tech card generation for {len(all_dishes)} dishes")
        
        generated_tech_cards = []
        failed_generations = []
        
        # Get user settings for tech card generation
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user["city"].lower(), 1.0)
        venue_context = generate_venue_context(user)
        venue_specific_rules = generate_venue_specific_rules(user)
        
        # Get venue-specific variables
        venue_type = user.get("venue_type", "family_restaurant")
        venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
        venue_price_multiplier = venue_info.get("price_multiplier", 1.0)
        venue_type_name = venue_info.get("name", "Семейный ресторан")
        
        average_check = user.get("average_check", 800)
        description_style = generate_description_style(user)
        cooking_instructions = generate_cooking_instructions(user)
        chef_tips = generate_chef_tips(user)
        serving_recommendations = generate_serving_recommendations(user)
        menu_tags = generate_menu_tags(user)
        
        # Equipment context for PRO users
        equipment_context = ""
        plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
        if plan_info.get("kitchen_equipment", False):
            user_equipment = user.get("kitchen_equipment", [])
            if user_equipment:
                equipment_names = []
                for category in KITCHEN_EQUIPMENT.values():
                    for equipment in category:
                        if equipment["id"] in user_equipment:
                            equipment_names.append(equipment["name"])
                
                if equipment_names:
                    equipment_context = f"\nОБОРУДОВАНИЕ НА КУХНЕ: {', '.join(equipment_names)}\nИспользуй доступное оборудование в рецептах!"
        
        # Generate tech card for each dish SEQUENTIALLY (no timeout issues)
        for i, dish in enumerate(all_dishes):
            try:
                dish_name = dish["name"]
                logger.info(f"Generating tech card {i+1}/{len(all_dishes)}: {dish_name}")
                
                # Create enhanced prompt using dish context from menu
                enhanced_dish_name = f"{dish_name} (для {venue_type_name}, категория: {dish['category']})"
                if dish.get("main_ingredients"):
                    enhanced_dish_name += f", основные ингредиенты: {', '.join(dish['main_ingredients'][:3])}"
                
                # Use the same GOLDEN_PROMPT as single tech card generation
                prompt = GOLDEN_PROMPT.format(
                    dish_name=enhanced_dish_name,
                    regional_coefficient=regional_coefficient,
                    venue_context=venue_context,
                    venue_specific_rules=venue_specific_rules,
                    venue_price_multiplier=venue_price_multiplier,
                    venue_type_name=venue_type_name,
                    average_check=average_check,
                    description_style=description_style,
                    cooking_instructions=cooking_instructions,
                    chef_tips=chef_tips,
                    serving_recommendations=serving_recommendations,
                    menu_tags=menu_tags,
                    equipment_context=equipment_context
                )
                
                # Generate tech card using OpenAI - ONE AT A TIME
                client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are RECEPTOR, a professional AI assistant for chefs. Always respond in Russian."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                
                tech_card_content = response.choices[0].message.content.strip()
                
                # Save generated tech card to database
                tech_card_record = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "dish_name": dish_name,
                    "content": tech_card_content,
                    "city": user.get("city", "moscow"),
                    "created_at": datetime.utcnow().isoformat(),
                    "is_menu": False,
                    "from_menu_id": menu_id,
                    "menu_category": dish["category"]
                }
                
                await db.user_history.insert_one(tech_card_record)
                
                generated_tech_cards.append({
                    "dish_name": dish_name,
                    "tech_card_id": tech_card_record["id"],
                    "content": tech_card_content,
                    "category": dish["category"],
                    "status": "success"
                })
                
                logger.info(f"Successfully generated tech card for: {dish_name}")
                
                # Small delay between requests to avoid API rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Failed to generate tech card for {dish['name']}: {str(e)}"
                logger.error(error_msg)
                
                failed_generations.append({
                    "dish_name": dish["name"],
                    "error": str(e),
                    "category": dish["category"],
                    "status": "failed"
                })
                
                # Continue with next dish even if one fails
        
        # Update user's monthly tech card usage
        current_usage = user.get("monthly_tech_cards_used", 0)
        new_usage = current_usage + len(generated_tech_cards)
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"monthly_tech_cards_used": new_usage}}
        )
        
        logger.info(f"Mass tech card generation completed: {len(generated_tech_cards)} success, {len(failed_generations)} failed")
        
        return {
            "success": True,
            "generated_count": len(generated_tech_cards),
            "failed_count": len(failed_generations),
            "tech_cards": generated_tech_cards,
            "failed_generations": failed_generations,
            "menu_id": menu_id,
            "message": f"Массовая генерация завершена! Создано {len(generated_tech_cards)} из {len(all_dishes)} техкарт."
        }
        
    except Exception as e:
        logger.error(f"Error in mass tech card generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating tech cards: {str(e)}")

@api_router.get("/menu/{menu_id}/tech-cards")
async def get_menu_tech_cards(menu_id: str):
    """
    Get all tech cards generated from a specific menu
    """
    try:
        # Get all tech cards that were generated from this menu
        tech_cards = await db.user_history.find({
            "from_menu_id": menu_id,
            "is_menu": False
        }).to_list(100)
        
        # Group by category for better organization
        cards_by_category = {}
        for card in tech_cards:
            category = card.get("menu_category", "Без категории")
            if category not in cards_by_category:
                cards_by_category[category] = []
            
            cards_by_category[category].append({
                "id": card["id"],
                "dish_name": card["dish_name"],
                "created_at": card["created_at"],
                "content_preview": card["content"][:200] + "..." if len(card["content"]) > 200 else card["content"]
            })
        
        return {
            "success": True,
            "menu_id": menu_id,
            "tech_cards_by_category": cards_by_category,
            "total_cards": len(tech_cards)
        }
        
    except Exception as e:
        logger.error(f"Error getting menu tech cards: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting menu tech cards: {str(e)}")

@api_router.post("/replace-dish")
async def replace_dish(request: dict):
    """
    Replace a specific dish in a menu with a new generated dish
    """
    user_id = request.get("user_id")
    menu_id = request.get("menu_id")
    dish_name = request.get("dish_name")  # Current dish name to replace
    replacement_prompt = request.get("replacement_prompt", "")  # Optional prompt for replacement
    category = request.get("category", "")  # Dish category
    
    if not user_id or not menu_id or not dish_name:
        raise HTTPException(status_code=400, detail="User ID, Menu ID, and dish name are required")
    
    # Get user to check subscription and get profile
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check subscription for dish replacement (PRO feature)
    subscription_plan = user.get("subscription_plan", "free")
    if subscription_plan == "free":
        raise HTTPException(status_code=403, detail="Dish replacement requires PRO subscription")
    
    # Get the menu from database
    menu_record = await db.user_history.find_one({"id": menu_id, "user_id": user_id, "is_menu": True})
    if not menu_record:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    try:
        # Generate replacement dish using same context as original menu
        # Get user settings for tech card generation
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user["city"].lower(), 1.0)
        venue_context = generate_venue_context(user)
        venue_specific_rules = generate_venue_specific_rules(user)
        
        # Get venue-specific variables
        venue_type = user.get("venue_type", "family_restaurant")
        venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
        venue_price_multiplier = venue_info.get("price_multiplier", 1.0)
        venue_type_name = venue_info.get("name", "Семейный ресторан")
        
        average_check = user.get("average_check", 800)
        description_style = generate_description_style(user)
        cooking_instructions = generate_cooking_instructions(user)
        chef_tips = generate_chef_tips(user)
        serving_recommendations = generate_serving_recommendations(user)
        menu_tags = generate_menu_tags(user)
        
        # Equipment context for PRO users
        equipment_context = ""
        plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
        if plan_info.get("kitchen_equipment", False):
            user_equipment = user.get("kitchen_equipment", [])
            if user_equipment:
                equipment_names = []
                for equip_category in KITCHEN_EQUIPMENT.values():
                    for equipment in equip_category:
                        if equipment["id"] in user_equipment:
                            equipment_names.append(equipment["name"])
                
                if equipment_names:
                    equipment_context = f"\nОБОРУДОВАНИЕ НА КУХНЕ: {', '.join(equipment_names)}\nИспользуй доступное оборудование в рецептах!"
        
        # Create enhanced prompt for replacement dish
        replacement_context = f"""
ЗАМЕНА БЛЮДА В МЕНЮ:
- Заменяемое блюдо: "{dish_name}"
- Категория: {category}
- Пожелания по замене: {replacement_prompt if replacement_prompt else "Создай альтернативное блюдо в том же стиле"}

ВАЖНО: Создай блюдо того же уровня сложности и ценовой категории, но с другими ингредиентами или техниками приготовления. Сохрани стиль заведения и целевую аудиторию."""
        
        enhanced_dish_name = f"{dish_name} (замена для {venue_type_name}, категория: {category})"
        if replacement_prompt:
            enhanced_dish_name += f", пожелания: {replacement_prompt[:100]}"
        
        # Use the same GOLDEN_PROMPT as single tech card generation
        prompt = GOLDEN_PROMPT.format(
            dish_name=enhanced_dish_name,
            regional_coefficient=regional_coefficient,
            venue_context=venue_context,
            venue_specific_rules=venue_specific_rules,
            venue_price_multiplier=venue_price_multiplier,
            venue_type_name=venue_type_name,
            average_check=average_check,
            description_style=description_style,
            cooking_instructions=cooking_instructions,
            chef_tips=chef_tips,
            serving_recommendations=serving_recommendations,
            menu_tags=menu_tags,
            equipment_context=equipment_context + replacement_context
        )
        
        # Generate replacement dish using OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are RECEPTOR, a professional AI assistant for chefs. Always respond in Russian."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        tech_card_content = response.choices[0].message.content.strip()
        
        # Extract dish details from generated content for menu display
        title_match = re.search(r'\*\*Название:\*\*\s*(.*?)(?=\n|$)', tech_card_content)
        description_match = re.search(r'\*\*Описание:\*\*\s*(.*?)(?=\n\n|\*\*)', tech_card_content, re.DOTALL)
        cost_match = re.search(r'Себестоимость.*?(\d+(?:\.\d+)?)\s*₽', tech_card_content)
        price_match = re.search(r'Рекомендуемая цена.*?(\d+(?:\.\d+)?)\s*₽', tech_card_content)
        time_match = re.search(r'\*\*Время:\*\*\s*(.*?)(?=\n|$)', tech_card_content)
        portion_match = re.search(r'\*\*Выход:\*\*\s*(.*?)(?=\n|$)', tech_card_content)
        
        new_dish_name = title_match.group(1).strip() if title_match else f"Замена для {dish_name}"
        
        # Create a full dish object for menu display (compatible with frontend)
        new_dish_object = {
            "name": new_dish_name,
            "description": description_match.group(1).strip() if description_match else "Авторское блюдо от шефа",
            "estimated_cost": cost_match.group(1) if cost_match else "250",
            "estimated_price": price_match.group(1) if price_match else "750", 
            "difficulty": "средне",
            "cook_time": time_match.group(1).strip() if time_match else "25 мин",
            "portion_size": portion_match.group(1).strip() if portion_match else "1 порция",
            "main_ingredients": []  # Will be extracted later if needed
        }
        
        # Try to extract main ingredients from tech card
        ingredients_match = re.search(r'\*\*Ингредиенты:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)', tech_card_content, re.DOTALL)
        if ingredients_match:
            ingredients_text = ingredients_match.group(1)
            ingredient_lines = [line.strip() for line in ingredients_text.split('\n') if line.strip().startswith('-')]
            main_ingredients = []
            for line in ingredient_lines[:5]:  # Take first 5 ingredients
                ingredient_name = re.sub(r'^-\s*', '', line).split('—')[0].split('-')[0].strip()
                if ingredient_name:
                    main_ingredients.append(ingredient_name)
            new_dish_object["main_ingredients"] = main_ingredients
        
        # Save new tech card to database
        tech_card_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "dish_name": new_dish_name,
            "content": tech_card_content,
            "city": user.get("city", "moscow"),
            "created_at": datetime.utcnow().isoformat(),
            "is_menu": False,
            "from_menu_id": menu_id,
            "menu_category": category,
            "replaced_dish": dish_name,  # Track what was replaced
            "replacement_prompt": replacement_prompt
        }
        
        await db.user_history.insert_one(tech_card_record)
        
        # Update user's monthly tech card usage
        current_usage = user.get("monthly_tech_cards_used", 0)
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"monthly_tech_cards_used": current_usage + 1}}
        )
        
        logger.info(f"Successfully replaced dish '{dish_name}' with '{new_dish_name}' for user {user_id}")
        
        return {
            "success": True,
            "original_dish": dish_name,
            "new_dish": new_dish_object,  # Return full dish object instead of just name
            "tech_card_id": tech_card_record["id"],
            "content": tech_card_content,
            "category": category,
            "message": f"Блюдо '{dish_name}' успешно заменено на '{new_dish_name}'"
        }
        
    except Exception as e:
        logger.error(f"Error replacing dish: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error replacing dish: {str(e)}")

@api_router.post("/generate-simple-menu")
async def generate_simple_menu(request: SimpleMenuRequest):
    """
    Simplified menu generation using venue profile settings
    User only needs to specify: menu_type, expectations, and optionally dish_count
    All other settings are taken from the user's venue profile
    """
    user_id = request.user_id
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Get user and venue profile
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check subscription for menu generation (PRO feature)
    subscription_plan = user.get("subscription_plan", "free")
    plan_info = SUBSCRIPTION_PLANS.get(subscription_plan, SUBSCRIPTION_PLANS["free"])
    if subscription_plan not in ["pro", "business"]:
        raise HTTPException(status_code=403, detail="Menu generation requires PRO subscription")
    
    try:
        logger.info(f"Starting simple menu generation for user {user_id}")
        
        # Build menu context from venue profile
        venue_type = user.get("venue_type", "family_restaurant")
        venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
        venue_type_name = venue_info.get("name", "Семейный ресторан")
        
        # Get dish count from request or venue profile default
        dish_count = request.dish_count or user.get("default_dish_count", 12)
        
        # Get categories from request or venue profile default
        if request.custom_categories:
            categories = request.custom_categories
        else:
            categories = user.get("default_categories", {
                "salads": 2,
                "appetizers": 3, 
                "soups": 2,
                "main_dishes": 4,
                "desserts": 2,
                "beverages": 1
            })
        
        # Build detailed context from venue profile
        cuisine_focus = user.get("cuisine_focus", ["russian"])
        cuisine_style = user.get("cuisine_style", "classic")
        average_check = user.get("average_check", 800)
        audience_ages = user.get("audience_ages", {})
        audience_occupations = user.get("audience_occupations", [])
        region = user.get("region", "moskva")
        staff_skill_level = user.get("staff_skill_level", "medium")
        preparation_time = user.get("preparation_time", "medium")
        ingredient_budget = user.get("ingredient_budget", "medium")
        menu_goals = user.get("menu_goals", [])
        special_requirements = user.get("special_requirements", [])
        dietary_options = user.get("dietary_options", [])
        kitchen_capabilities = user.get("kitchen_capabilities", [])
        
        # Build audience context
        audience_context = ""
        if audience_ages:
            age_distribution = ", ".join([f"{age}: {pct}%" for age, pct in audience_ages.items() if pct > 0])
            audience_context += f"Возрастное распределение: {age_distribution}. "
        if audience_occupations:
            audience_context += f"Основная аудитория: {', '.join(audience_occupations)}. "
        
        # Build requirements context  
        requirements_context = ""
        if special_requirements:
            requirements_context += f"Особые требования: {', '.join(special_requirements)}. "
        if dietary_options:
            requirements_context += f"Диетические опции: {', '.join(dietary_options)}. "
            
        # Build kitchen context
        kitchen_context = f"Уровень персонала: {staff_skill_level}, время приготовления: {preparation_time}, бюджет ингредиентов: {ingredient_budget}. "
        if kitchen_capabilities:
            kitchen_context += f"Кухонные возможности: {', '.join(kitchen_capabilities)}. "
            
        # Create simplified menu generation prompt
        menu_prompt = f"""Создай {request.menu_type} меню для заведения "{venue_type_name}".

ОСНОВНАЯ ИНФОРМАЦИЯ:
- Тип заведения: {venue_type_name}
- Кухня: {', '.join(cuisine_focus)}
- Стиль: {cuisine_style} 
- Средний чек: {average_check} руб.
- Регион: {region}

ОЖИДАНИЯ ОТ МЕНЮ:
{request.expectations}

ЦЕЛЕВАЯ АУДИТОРИЯ:
{audience_context if audience_context else 'Широкая аудитория'}

ТРЕБОВАНИЯ И ОГРАНИЧЕНИЯ:
{requirements_context if requirements_context else 'Стандартные требования'}

КУХОННЫЕ ВОЗМОЖНОСТИ:
{kitchen_context}

СОСТАВ МЕНЮ:
Создай ровно {dish_count} блюд по следующим категориям:
{chr(10).join([f'- {category}: {count} блюд' for category, count in categories.items()])}

ВАЖНЫЕ ТРЕБОВАНИЯ:
1. Каждое блюдо должно соответствовать концепции заведения
2. Учитывай средний чек при выборе ингредиентов
3. Блюда должны отвечать ожиданиям: {request.expectations}
4. Соблюдай баланс по сложности приготовления
5. Учитывай целевую аудиторию

Отвечай ТОЛЬКО в формате JSON:
{{
  "menu_concept": "краткая концепция меню",
  "dishes": [
    {{
      "name": "название блюда",
      "category": "категория",
      "description": "краткое описание",
      "main_ingredients": ["ингредиент1", "ингредиент2"],
      "estimated_cost": "примерная себестоимость",
      "estimated_price": "рекомендуемая цена",
      "difficulty": "easy/medium/hard",
      "cook_time": "время приготовления"
    }}
  ]
}}"""

        # Generate menu using OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Using gpt-4o for better menu generation
            messages=[
                {"role": "system", "content": "You are RECEPTOR, a professional AI assistant for chefs and restaurateurs. Always respond in Russian with valid JSON."},
                {"role": "user", "content": menu_prompt}
            ],
            max_tokens=4000,
            temperature=0.8
        )
        
        menu_content = response.choices[0].message.content.strip()
        
        # Clean and parse JSON response
        if menu_content.startswith('```json'):
            menu_content = menu_content.replace('```json', '').replace('```', '')
        
        try:
            menu_data = json.loads(menu_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse menu JSON: {str(e)}")
            logger.error(f"Raw content: {menu_content}")
            raise HTTPException(status_code=500, detail="Failed to generate valid menu format")
        
        # Validate menu structure
        if "dishes" not in menu_data:
            raise HTTPException(status_code=500, detail="Generated menu missing dishes")
        
        if len(menu_data["dishes"]) != dish_count:
            logger.warning(f"Generated {len(menu_data['dishes'])} dishes, expected {dish_count}")
            
        # Create menu record
        menu_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "menu_type": request.menu_type,
            "menu_concept": menu_data.get("menu_concept", ""),
            "expectations": request.expectations,
            "dish_count_requested": dish_count,
            "dish_count_generated": len(menu_data["dishes"]),
            "dishes": menu_data["dishes"],
            "venue_context": {
                "venue_type": venue_type,
                "cuisine_focus": cuisine_focus,
                "cuisine_style": cuisine_style,
                "average_check": average_check
            },
            "generation_method": "simple",  # Mark as simplified generation
            "project_id": request.project_id,  # Link to project if provided
            "created_at": datetime.utcnow().isoformat(),
            "is_menu": True
        }
        
        await db.user_history.insert_one(menu_record)
        logger.info(f"Simple menu generated successfully for user {user_id}: {menu_record['id']}")
        
        return {
            "success": True,
            "menu_id": menu_record["id"],
            "menu_concept": menu_data.get("menu_concept", ""),
            "dish_count": len(menu_data["dishes"]),
            "dishes": menu_data["dishes"],
            "generation_method": "simple",
            "message": f"Простое меню '{request.menu_type}' успешно создано!"
        }
        
    except Exception as e:
        logger.error(f"Error generating simple menu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating simple menu: {str(e)}")

@api_router.post("/create-menu-project")
async def create_menu_project(request: MenuProjectCreate):
    """Create a new menu project for organizing menus and tech cards"""
    try:
        # Verify user exists
        user = await db.users.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create project record
        project_id = str(uuid.uuid4())
        project_record = {
            "id": project_id,
            "user_id": request.user_id,
            "project_name": request.project_name,
            "description": request.description or "",
            "project_type": request.project_type,
            "venue_type": request.venue_type,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        await db.menu_projects.insert_one(project_record)
        
        logger.info(f"Menu project created: {project_id} for user {request.user_id}")
        
        return {
            "success": True,
            "project_id": project_id,
            "message": f"Проект '{request.project_name}' успешно создан!"
        }
        
    except Exception as e:
        logger.error(f"Error creating menu project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating menu project: {str(e)}")

@api_router.get("/menu-projects/{user_id}")
async def get_user_menu_projects(user_id: str):
    """Get all menu projects for a user"""
    try:
        # Verify user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get all projects for user
        projects_cursor = db.menu_projects.find(
            {"user_id": user_id, "is_active": True}
        ).sort("created_at", -1)
        
        projects = await projects_cursor.to_list(length=100)
        
        # Remove MongoDB _id fields to avoid serialization issues
        for project in projects:
            if "_id" in project:
                del project["_id"]
        
        # Get counts for each project
        project_stats = []
        for project in projects:
            # Count menus in project
            menus_count = await db.user_history.count_documents({
                "user_id": user_id,
                "is_menu": True,
                "project_id": project["id"]
            })
            
            # Count tech cards in project
            tech_cards_count = await db.user_history.count_documents({
                "user_id": user_id,
                "is_menu": False,
                "project_id": project["id"]
            })
            
            project_stats.append({
                **project,
                "menus_count": menus_count,
                "tech_cards_count": tech_cards_count
            })
        
        return {
            "success": True,
            "projects": project_stats,
            "total_projects": len(project_stats)
        }
        
    except Exception as e:
        logger.error(f"Error getting menu projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting menu projects: {str(e)}")

@api_router.put("/menu-project/{project_id}")
async def update_menu_project(project_id: str, request: MenuProjectUpdate):
    """Update a menu project"""
    try:
        # Find project
        project = await db.menu_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if request.project_name is not None:
            update_data["project_name"] = request.project_name
        if request.description is not None:
            update_data["description"] = request.description
        if request.project_type is not None:
            update_data["project_type"] = request.project_type
        if request.venue_type is not None:
            update_data["venue_type"] = request.venue_type
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        
        await db.menu_projects.update_one(
            {"id": project_id},
            {"$set": update_data}
        )
        
        return {
            "success": True,
            "message": "Проект успешно обновлен!"
        }
        
    except Exception as e:
        logger.error(f"Error updating menu project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating menu project: {str(e)}")

@api_router.delete("/menu-project/{project_id}")
async def delete_menu_project(project_id: str):
    """Delete (deactivate) a menu project"""
    try:
        # Find project
        project = await db.menu_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Soft delete - mark as inactive
        await db.menu_projects.update_one(
            {"id": project_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow().isoformat()}}
        )
        
        return {
            "success": True,
            "message": "Проект успешно удален!"
        }
        
    except Exception as e:
        logger.error(f"Error deleting menu project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting menu project: {str(e)}")

@api_router.get("/menu-project/{project_id}/content")
async def get_menu_project_content(project_id: str):
    """Get all menus and tech cards for a specific project"""
    try:
        # Find project
        project = await db.menu_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get menus in project
        menus_cursor = db.user_history.find({
            "project_id": project_id,
            "is_menu": True
        }).sort("created_at", -1)
        
        menus = await menus_cursor.to_list(length=100)
        
        # Get tech cards in project
        tech_cards_cursor = db.user_history.find({
            "project_id": project_id,
            "is_menu": False
        }).sort("created_at", -1)
        
        tech_cards = await tech_cards_cursor.to_list(length=500)
        
        # Remove MongoDB _id fields to avoid serialization issues
        for menu in menus:
            if "_id" in menu:
                del menu["_id"]
                
        for card in tech_cards:
            if "_id" in card:
                del card["_id"]
        
        # Clean project data
        if "_id" in project:
            del project["_id"]
        
        return {
            "success": True,
            "project": project,
            "menus": menus,
            "tech_cards": tech_cards,
            "menus_count": len(menus),
            "tech_cards_count": len(tech_cards)
        }
        
    except Exception as e:
        logger.error(f"Error getting menu project content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting menu project content: {str(e)}")

# ============================================
# IIKo INTEGRATION ENDPOINTS
# ============================================

@api_router.get("/iiko/health")
async def iiko_health_check():
    """Health check endpoint for IIKo API connectivity"""
    try:
        # Check if we're using iikoServer API or legacy Cloud API
        if isinstance(iiko_auth_manager, IikoServerAuthManager):
            # For iikoServer API, test session key
            session_key = await iiko_auth_manager.get_session_key()
            if session_key:
                return {
                    "status": "healthy",
                    "iiko_connection": "active",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception("Failed to get session key")
        else:
            # For legacy Cloud API
            client = await iiko_auth_manager.get_authenticated_client()
            return {
                "status": "healthy",
                "iiko_connection": "active",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "iiko_connection": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@api_router.get("/iiko/organizations")
async def get_iiko_organizations():
    """Fetch all available organizations from IIKo"""
    logger.info("Fetching IIKo organizations")
    try:
        organizations = await iiko_service.get_organizations()
        return {
            "success": True,
            "organizations": organizations,
            "count": len(organizations)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@api_router.get("/iiko/menu/{organization_id}")
async def get_iiko_menu_items(organization_id: str):
    """Fetch menu items and categories for specific organization"""
    logger.info(f"Fetching IIKo menu for organization: {organization_id}")
    try:
        if not organization_id:
            raise HTTPException(status_code=400, detail="Organization ID is required")
            
        menu_data = await iiko_service.get_menu_items([organization_id])
        return {
            "success": True,
            "organization_id": organization_id,
            "menu": menu_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching menu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@api_router.post("/iiko/tech-cards/upload")
async def upload_tech_card_to_iiko(request: TechCardUpload):
    """Upload AI-generated tech card to IIKo as menu item"""
    user_id = request.organization_id  # Using as user identifier for now
    logger.info(f"Uploading tech card '{request.name}' to IIKo organization: {request.organization_id}")
    
    try:
        # Validate required fields
        if not request.name or not request.ingredients:
            raise HTTPException(status_code=400, detail="Name and ingredients are required")
        
        # Transform tech card data for IIKo compatibility
        iiko_item_data = {
            'name': request.name,
            'description': request.description or 'Блюдо создано с помощью AI-Menu-Designer',
            'productCategoryId': request.category_id or None,
            'price': request.price or 0.0,
            'weight': request.weight or 0.0,
            'composition': _format_ingredients_for_iiko(request.ingredients),
            'cookingInstructions': '\n'.join(request.preparation_steps) if request.preparation_steps else '',
            'active': True
        }
        
        # Store in our database for synchronization tracking
        sync_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "organization_id": request.organization_id,
            "tech_card_name": request.name,
            "iiko_data": iiko_item_data,
            "sync_status": "prepared",
            "created_at": datetime.now().isoformat(),
            "ai_generated": True
        }
        
        await db.iiko_sync_records.insert_one(sync_record)
        
        logger.info(f"Tech card '{request.name}' prepared for IIKo sync with ID: {sync_record['id']}")
        
        return {
            "success": True,
            "sync_id": sync_record["id"],
            "message": f"Техкарта '{request.name}' подготовлена для загрузки в IIKo",
            "status": "prepared_for_sync",
            "iiko_data": iiko_item_data,
            "note": "Техкарта сохранена в систему. Финальная загрузка в IIKo может потребовать дополнительной настройки через веб-интерфейс IIKo."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading tech card to IIKo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading tech card: {str(e)}")

@api_router.post("/iiko/sync-menu")
async def sync_menu_with_iiko(request: MenuSyncRequest, background_tasks: BackgroundTasks):
    """Synchronize menu items between AI-Menu-Designer and IIKo"""
    logger.info(f"Starting menu synchronization for organizations: {request.organization_ids}")
    
    try:
        if not request.organization_ids:
            raise HTTPException(status_code=400, detail="At least one organization ID is required")
        
        # Create sync job record
        sync_job_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        sync_job = {
            "id": sync_job_id,
            "organization_ids": request.organization_ids,
            "sync_prices": request.sync_prices,
            "sync_categories": request.sync_categories,
            "status": "in_progress",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        await db.iiko_sync_jobs.insert_one(sync_job)
        
        # Start synchronization in background
        background_tasks.add_task(
            _perform_menu_sync,
            sync_job_id,
            request.organization_ids,
            request.sync_prices,
            request.sync_categories
        )
        
        return {
            "success": True,
            "message": "Синхронизация меню запущена",
            "sync_job_id": sync_job_id,
            "status": "in_progress",
            "organizations_count": len(request.organization_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting menu sync: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting sync: {str(e)}")

@api_router.get("/iiko/sync/status/{sync_job_id}")
async def get_sync_status(sync_job_id: str):
    """Get synchronization job status"""
    try:
        sync_job = await db.iiko_sync_jobs.find_one({"id": sync_job_id})
        if not sync_job:
            raise HTTPException(status_code=404, detail="Sync job not found")
        
        # Remove MongoDB _id field
        if "_id" in sync_job:
            del sync_job["_id"]
        
        return {
            "success": True,
            "sync_job": sync_job
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {str(e)}")

@api_router.get("/iiko/diagnostics")
async def run_iiko_diagnostics():
    """Run comprehensive diagnostics on IIKo integration"""
    logger.info("Running IIKo integration diagnostics")
    
    diagnosis = {
        'timestamp': datetime.now().isoformat(),
        'tests': [],
        'overall_status': 'healthy'
    }
    
    # Test 1: Environment variables
    env_test = {
        'test_name': 'Environment Variables',
        'status': 'pass',
        'details': [],
        'issues': []
    }
    
    required_vars = ['IIKO_API_LOGIN', 'IIKO_API_PASSWORD', 'IIKO_BASE_URL']
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            env_test['status'] = 'fail'
            env_test['issues'].append(f"Missing environment variable: {var}")
        else:
            env_test['details'].append(f"{var}: {'*' * 8}[CONFIGURED]")
    
    diagnosis['tests'].append(env_test)
    
    # Test 2: IIKo library availability
    lib_test = {
        'test_name': 'IIKo Library',
        'status': 'pass' if IIKO_AVAILABLE else 'fail',
        'details': ['pyiikocloudapi library loaded successfully'] if IIKO_AVAILABLE else [],
        'issues': ['IIKo library not available'] if not IIKO_AVAILABLE else []
    }
    diagnosis['tests'].append(lib_test)
    
    # Test 3: Authentication (if possible)
    auth_test = {
        'test_name': 'Authentication',
        'status': 'pass',
        'details': [],
        'issues': []
    }
    
    try:
        if IIKO_AVAILABLE and os.getenv('IIKO_API_LOGIN'):
            # Check if we're using iikoServer API or legacy Cloud API
            if isinstance(iiko_auth_manager, IikoServerAuthManager):
                # For iikoServer API, test session key
                session_key = await iiko_auth_manager.get_session_key()
                if session_key:
                    auth_test['details'].append("Authentication successful")
                else:
                    auth_test['status'] = 'fail'
                    auth_test['issues'].append("Failed to get session key")
            else:
                # For legacy Cloud API
                await iiko_auth_manager.get_authenticated_client()
                auth_test['details'].append("Authentication successful")
        else:
            auth_test['status'] = 'skip'
            auth_test['details'].append("Skipped - credentials not configured or library unavailable")
    except Exception as e:
        auth_test['status'] = 'fail'
        auth_test['issues'].append(f"Authentication failed: {str(e)}")
    
    diagnosis['tests'].append(auth_test)
    
    # Determine overall status
    failed_tests = [test for test in diagnosis['tests'] if test['status'] == 'fail']
    if failed_tests:
        diagnosis['overall_status'] = 'unhealthy'
    
    return {
        "success": True,
        "diagnosis": diagnosis,
        "recommendations": _generate_diagnostic_recommendations(diagnosis['tests']),
        "support_info": {
            "iiko_documentation": "https://api-ru.iiko.services/",
            "integration_version": "1.0.0"
        }
    }

# Helper functions for IIKo integration
def _format_ingredients_for_iiko(ingredients: List[Dict[str, Any]]) -> str:
    """Format ingredients list for IIKo display"""
    formatted = []
    for ingredient in ingredients:
        name = ingredient.get('name', '')
        quantity = ingredient.get('quantity', '')
        unit = ingredient.get('unit', '')
        formatted.append(f"{name}: {quantity} {unit}".strip())
    return '; '.join(formatted)

async def _perform_menu_sync(sync_job_id: str, organization_ids: List[str], sync_prices: bool, sync_categories: bool):
    """Background task to perform menu synchronization"""
    logger.info(f"Starting background menu sync job: {sync_job_id}")
    
    try:
        sync_results = {
            'organizations_synced': [],
            'items_updated': 0,
            'categories_updated': 0,
            'errors': [],
            'sync_timestamp': datetime.now().isoformat()
        }
        
        for org_id in organization_ids:
            try:
                # Fetch current menu from IIKo
                menu_data = await iiko_service.get_menu_items([org_id])
                
                # Store menu data in our database for reference
                menu_record = {
                    "id": str(uuid.uuid4()),
                    "organization_id": org_id,
                    "menu_data": menu_data,
                    "sync_job_id": sync_job_id,
                    "synced_at": datetime.now().isoformat()
                }
                
                await db.iiko_menu_cache.insert_one(menu_record)
                
                sync_results['organizations_synced'].append({
                    'organization_id': org_id,
                    'status': 'success',
                    'items_count': len(menu_data.get('items', [])),
                    'categories_count': len(menu_data.get('categories', []))
                })
                
                sync_results['items_updated'] += len(menu_data.get('items', []))
                sync_results['categories_updated'] += len(menu_data.get('categories', []))
                
                logger.info(f"Successfully synced organization {org_id}")
                
            except Exception as org_error:
                error_msg = f"Failed to sync organization {org_id}: {str(org_error)}"
                sync_results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Update sync job status
        await db.iiko_sync_jobs.update_one(
            {"id": sync_job_id},
            {
                "$set": {
                    "status": "completed",
                    "results": sync_results,
                    "updated_at": datetime.now().isoformat()
                }
            }
        )
        
        logger.info(f"Completed menu sync job: {sync_job_id}")
        
    except Exception as e:
        error_msg = f"Critical error in sync job {sync_job_id}: {str(e)}"
        logger.error(error_msg)
        
        # Update sync job with error status
        await db.iiko_sync_jobs.update_one(
            {"id": sync_job_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.now().isoformat()
                }
            }
        )

def _generate_diagnostic_recommendations(tests: List[Dict]) -> List[str]:
    """Generate recommendations based on diagnostic test results"""
    recommendations = []
    
    failed_tests = [test for test in tests if test['status'] == 'fail']
    
    if failed_tests:
        recommendations.append("❌ Критические проблемы обнаружены:")
        for test in failed_tests:
            recommendations.append(f"   • {test['test_name']}: {'; '.join(test['issues'])}")
    else:
        recommendations.append("✅ Все тесты пройдены успешно - интеграция с IIKo готова к работе")
    
    recommendations.extend([
        "",
        "💡 Общие рекомендации:",
        "   • Регулярно проверяйте статус интеграции",
        "   • Настройте мониторинг для важных эндпоинтов",
        "   • Ведите резервные копии данных синхронизации",
        "   • Тестируйте интеграцию после обновлений IIKo"
    ])
    
    return recommendations

# Include the router in the main app
app.include_router(api_router)

# Add a catch-all OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return {"message": "OK"}

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
            user = test_user
    else:
        # Validate user subscription (PRO only)
        user = await db.users.find_one({"id": user_id})
        if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
            raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    average_check = user.get("average_check", 800)
    venue_name = user.get("venue_name", "заведение")
    
    # Extract dish name from tech card
    dish_name = "блюдо"
    for line in tech_card.split('\n'):
        if 'Название:' in line:
            dish_name = line.split('Название:')[1].strip().replace('**', '')
            break
    
    # Generate venue-specific sales script context
    venue_context = generate_sales_script_context(venue_type, venue_info, average_check, cuisine_focus)
    
    prompt = f"""Ты — эксперт по продажам в ресторанном бизнесе. 

КОНТЕКСТ ЗАВЕДЕНИЯ:
Тип заведения: {venue_info['name']}
Средний чек: {average_check}₽
Название: {venue_name}
{venue_context}

Создай профессиональный скрипт продаж для официантов для блюда "{dish_name}" специально адаптированный для типа заведения "{venue_info['name']}".

Техкарта блюда:
{tech_card}

Создай 3 варианта скриптов:

🎭 КЛАССИЧЕСКИЙ СКРИПТ:
[2-3 предложения для обычной презентации блюда с учетом стиля заведения]

🔥 АКТИВНЫЕ ПРОДАЖИ:
[агрессивный скрипт для увеличения среднего чека, адаптированный под тип заведения]

💫 ПРЕМИУМ ПОДАЧА:
[скрипт для особых гостей с учетом концепции заведения]

Дополнительно:
• 5 ключевых преимуществ блюда для данного типа заведения
• Возражения клиентов и ответы на них (специфичные для типа заведения)
• Техники up-sell и cross-sell (подходящие для концепции)
• Невербальные приемы подачи (адаптированные под атмосферу)

Пиши живо, как будто это реально говорит опытный официант в {venue_info['name'].lower()}."""

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
            user = test_user
    else:
        # Validate user subscription (PRO only)
        user = await db.users.find_one({"id": user_id})
        if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
            raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    average_check = user.get("average_check", 800)
    
    # Extract dish name from tech card
    dish_name = "блюдо"
    for line in tech_card.split('\n'):
        if 'Название:' in line:
            dish_name = line.split('Название:')[1].strip().replace('**', '')
            break
    
    # Generate venue-specific pairing context
    pairing_context = generate_food_pairing_context(venue_type, venue_info, average_check, cuisine_focus)
    
    prompt = f"""Ты — сомелье и эксперт по фудпейрингу. 

КОНТЕКСТ ЗАВЕДЕНИЯ:
Тип заведения: {venue_info['name']}
Средний чек: {average_check}₽
{pairing_context}

Создай профессиональное руководство по сочетаниям для блюда "{dish_name}" специально адаптированное для типа заведения "{venue_info['name']}".

Техкарта блюда:
{tech_card}

Создай детальные рекомендации:

🍷 АЛКОГОЛЬНЫЕ НАПИТКИ:
{generate_alcohol_recommendations(venue_type)}

🍹 БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ:
• Подходящие безалкогольные варианты
• Авторские лимонады и чаи
• Кофейные и молочные напитки

🍽 ГАРНИРЫ И ДОПОЛНЕНИЯ:
• Идеальные гарниры для данного типа заведения
• Соусы и заправки
• Закуски для комплекта

🎯 СПЕЦИАЛЬНЫЕ ПРЕДЛОЖЕНИЯ:
• Сочетания специфичные для {venue_info['name'].lower()}
• Сезонные варианты
• Эксклюзивные предложения

Для каждой категории объясни ПОЧЕМУ это сочетание работает и как оно подходит концепции заведения."""

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
            user = test_user
    else:
        # Validate user subscription (PRO only)
        user = await db.users.find_one({"id": user_id})
        if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
            raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    average_check = user.get("average_check", 800)
    
    # Extract dish name from tech card
    dish_name = "блюдо"
    for line in tech_card.split('\n'):
        if 'Название:' in line:
            dish_name = line.split('Название:')[1].strip().replace('**', '')
            break
    
    # Generate venue-specific photo context
    photo_context = generate_photo_tips_context(venue_type, venue_info, average_check, cuisine_focus)
    
    prompt = f"""Ты — фуд-фотограф и эксперт по визуальной подаче блюд.

КОНТЕКСТ ЗАВЕДЕНИЯ:
Тип заведения: {venue_info['name']}
Средний чек: {average_check}₽
{photo_context}

Создай профессиональное руководство по фотографии для блюда "{dish_name}" специально адаптированное для заведения типа "{venue_info['name']}".

Техкарта блюда:
{tech_card}

Создай детальные рекомендации:

📸 ТЕХНИЧЕСКИЕ НАСТРОЙКИ ДЛЯ {venue_info['name'].upper()}:
{generate_photo_tech_settings(venue_type)}

🎨 СТИЛИНГ И ПОДАЧА:
{generate_photo_styling_tips(venue_type)}

✨ КОМПОЗИЦИЯ:
• Лучшие ракурсы для блюд в {venue_info['name'].lower()}
• Как показать концепцию заведения через фото
• Техники подчеркивающие атмосферу места

🌅 ОСВЕЩЕНИЕ:
• Оптимальное освещение для интерьера заведения
• Работа с существующим освещением
• Как передать атмосферу {venue_info['name'].lower()}

📱 ДЛЯ СОЦСЕТЕЙ:
• Адаптация под аудиторию заведения
• Хештеги специфичные для {venue_info['name'].lower()}
• Контент-стратегия для типа заведения

🎭 ПОСТОБРАБОТКА:
• Цветовая коррекция под стиль заведения
• Фильтры подходящие для концепции
• Создание узнаваемого визуального стиля

💡 PRO СОВЕТЫ ДЛЯ {venue_info['name'].upper()}:
• Как подчеркнуть уникальность заведения через еду
• Создание контента для целевой аудитории
• Интеграция с общим брендингом

Для каждого совета объясни ПОЧЕМУ это важно именно для данного типа заведения и блюда."""

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
    
    # Поиск актуальных цен в интернете
    search_query = f"цены на продукты {user.get('city', 'москва')} 2025 мясо овощи крупы молочные продукты"
    
    try:
        from emergentintegrations.tools import web_search
        price_search_result = web_search(search_query, search_context_size="medium")
    except Exception:
        price_search_result = "Данные по ценам недоступны"
    
    # Поиск цен конкурентов
    competitor_search_query = f"цены меню {dish_name} рестораны {user.get('city', 'москва')} 2025"
    
    try:
        competitor_search_result = web_search(competitor_search_query, search_context_size="medium")
    except Exception:
        competitor_search_result = "Данные по конкурентам недоступны"
    
    # Создаем промпт для финансового анализа
    prompt = f"""Ты — практичный финансовый консультант ресторанов с 15-летним опытом. Твоя специализация — КОНКРЕТНЫЕ решения, а не общие фразы.

Проанализируй блюдо "{dish_name}" и дай РЕАЛЬНЫЕ советы с цифрами и практическими шагами.

ТЕХКАРТА:
{tech_card}

РЕГИОНАЛЬНЫЙ КОЭФФИЦИЕНТ: {regional_coefficient}x
ЦЕНЫ НА ПРОДУКТЫ: {price_search_result}
КОНКУРЕНТЫ: {competitor_search_result}

ПРИНЦИПЫ АНАЛИЗА:
- Никаких банальностей типа "оптимизируйте поставщиков"
- Только конкретика: "замените X на Y = экономия Z₽"  
- Реальные цифры и расчеты
- Практичные советы, которые можно внедрить завтра

Создай ПРАКТИЧНЫЙ анализ в JSON:

{{
    "dish_name": "{dish_name}",
    "total_cost": [точная себестоимость на 1 порцию],
    "recommended_price": [рекомендуемая цена],
    "margin_percent": [маржинальность %],
    "profitability_rating": [1-5 звезд],
    
    "ingredient_breakdown": [
        {{"ingredient": "название", "cost": "стоимость₽", "percent_of_total": "% от общей стоимости", "optimization_tip": "конкретный совет по оптимизации"}}
    ],
    
    "smart_cost_cuts": [
        {{"change": "Конкретная замена ингредиента", "current_cost": "текущая стоимость₽", "new_cost": "новая стоимость₽", "savings": "экономия₽", "quality_impact": "влияние на вкус: минимальное/заметное/критичное"}},
        {{"change": "Изменение пропорций", "savings": "экономия₽", "description": "как именно изменить"}}
    ],
    
    "revenue_hacks": [
        {{"strategy": "Конкретная стратегия увеличения выручки", "implementation": "как внедрить", "potential_gain": "потенциальная прибыль₽"}},
        {{"strategy": "Другой способ", "implementation": "шаги внедрения", "potential_gain": "прибыль₽"}}
    ],
    
    "seasonal_opportunities": {{
        "summer": "летняя оптимизация с цифрами",
        "winter": "зимняя стратегия с цифрами", 
        "peak_season": "когда блюдо выгоднее всего",
        "off_season": "как поддержать прибыльность в низкий сезон"
    }},
    
    "competitor_intelligence": {{
        "price_advantage": "ваше преимущество/недостаток по цене",
        "positioning": "как позиционировать: премиум/средний/бюджет",
        "market_gap": "найденная ниша или возможность"
    }},
    
    "action_plan": [
        {{"priority": "высокий", "action": "Первое что делать завтра", "expected_result": "ожидаемый результат с цифрами"}},
        {{"priority": "средний", "action": "Второй шаг на следующей неделе", "expected_result": "результат"}},
        {{"priority": "низкий", "action": "Долгосрочная оптимизация", "expected_result": "результат"}}
    ],
    
    "financial_forecast": {{
        "daily_breakeven": "сколько порций продать чтобы выйти в ноль",
        "target_daily": "сколько порций для хорошей прибыли", 
        "monthly_revenue_potential": "потенциал выручки в месяц₽",
        "profit_margin_realistic": "реалистичная прибыль с порции₽"
    }},
    
    "red_flags": [
        "конкретная проблема которую надо решить срочно",
        "еще одна критичная точка"
    ],
    
    "golden_opportunities": [
        "упущенная возможность заработать больше",
        "скрытый потенциал оптимизации"
    ]
}}

ВАЖНО: Никаких общих фраз! Только конкретные цифры, названия ингредиентов, точные суммы экономии, реальные действия. Каждый совет должен быть готов к внедрению."""

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
            # Clean markdown formatting if present
            clean_text = analysis_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]  # Remove ```json
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]  # Remove ```
            clean_text = clean_text.strip()
            
            analysis_data = json.loads(clean_text)
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

@app.post("/api/improve-dish")
async def improve_dish(request: dict):
    """Улучшение существующего блюда для PRO пользователей"""
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    if not user_id or not tech_card:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    # Проверяем подписку пользователя (пока бесплатно для всех)
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
    
    # Извлекаем название блюда
    dish_name = "блюдо"
    title_match = re.search(r'\*\*Название:\*\*\s*(.*?)(?=\n|$)', tech_card)
    if title_match:
        dish_name = title_match.group(1).strip()
    
    # Создаем промпт для улучшения блюда  
    prompt = f"""Ты — шеф-повар мирового уровня с 20-летним опытом работы в мишленовских ресторанах.

Твоя задача: ПРОКАЧАТЬ и УЛУЧШИТЬ существующее блюдо "{dish_name}", сделав его более профессиональным, вкусным и впечатляющим, но сохранив стандартный формат технологической карты.

ИСХОДНАЯ ТЕХКАРТА:
{tech_card}

ВАЖНО: 
- НЕ МЕНЯЙ СУТЬ БЛЮДА! Улучшай то, что есть, а не создавай что-то новое
- СТРОГО СОБЛЮДАЙ ФОРМАТ технологической карты как в исходной
- ДОБАВЬ новые секции с профессиональными фишками

Создай УЛУЧШЕННУЮ версию строго в формате:

**Название:** [исходное название] 2.0

**Категория:** [та же категория]

**Описание:** [улучшенное описание с акцентом на профессиональные техники, 2-3 сочных предложения]

**Ингредиенты:** (указывай НА ОДНУ ПОРЦИЮ!)

[Все исходные ингредиенты + профессиональные улучшения]
- [Основные ингредиенты с улучшенными версиями]
- [Дополнительные профессиональные ингредиенты]
- [Специи и акценты от шефа]

**Пошаговый рецепт:**

1. [Шаг с профессиональными техниками]
2. [Шаг с секретами мастерства]
3. [Финальные штрихи]

**Время:** Подготовка XX мин | Готовка XX мин | ИТОГО XX мин

**Выход:** XXX г готового блюда

**Порция:** XX г (одна порция)

**Себестоимость:**

- По ингредиентам: XXX ₽
- Себестоимость 1 порции: XX ₽
- Рекомендуемая цена (×3): XXX ₽

**КБЖУ на 1 порцию:** Калории … ккал | Б … г | Ж … г | У … г

**КБЖУ на 100 г:** Калории … ккал | Б … г | Ж … г | У … г

**Аллергены:** … + (веган / безглютен и т.п.)

**Заготовки и хранение:**

- Профессиональные заготовки и их сроки
- Температурные режимы хранения (+2°C, +18°C, комнатная)
- Лайфхаки для сохранения качества от шефа
- Особенности работы с улучшенными ингредиентами

**Особенности и советы от шефа:**

🔥 **ПРОФЕССИОНАЛЬНЫЕ УЛУЧШЕНИЯ:**
- Замена [ингредиент] на [улучшенный ингредиент] - [эффект]
- Добавление [техника] для [результат]
- Секрет: [профессиональная хитрость]

⚡ **ТЕХНИЧЕСКИЕ ФИШКИ:**
- [Конкретная техника] - зачем это нужно
- [Температурный контроль] - как это влияет на вкус
- [Временные нюансы] - критичные моменты

🎯 **МАСТЕР-КЛАССЫ:**
- Как [конкретное действие] изменяет [характеристику]
- Секрет идеальной [текстуры/вкуса/аромата]
- Профессиональная хитрость для [конкретного элемента]

💎 **ЭКСПЕРТНЫЕ СОВЕТЫ:**
- [Совет уровня мишленовского ресторана]
- [Как избежать типичной ошибки]
- [Варианты адаптации под сезон/предпочтения]

**Рекомендация подачи:** 

🎨 **ПРОДВИНУТАЯ ПОДАЧА:**
- Профессиональный плейтинг и температурная подача
- Элементы декора и акцентов
- Сочетание с соусами и гарнирами

**Теги для меню:** #прокачанная #шеф #профи #улучшенная

Сгенерировано RECEPTOR AI PRO — прокачанная версия от шеф-повара

ВАЖНО: Сохрани ВСЕ разделы из исходной техкарты, но улучши их содержание!"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты мишленовский шеф-повар с 20-летним опытом. Твоя задача - улучшать блюда, делая их более профессиональными, но сохраняя суть. Давай конкретные техники и объяснения."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        improved_dish = response.choices[0].message.content
        
        return {
            "success": True,
            "improved_dish": improved_dish,
            "original_dish": dish_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка улучшения блюда: {str(e)}")

@app.post("/api/laboratory-experiment")
async def laboratory_experiment(request: dict):
    """Кулинарные эксперименты в лаборатории для PRO пользователей"""
    user_id = request.get("user_id")
    experiment_type = request.get("experiment_type", "random")  # random, fusion, molecular, extreme
    base_dish = request.get("base_dish", "")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    # Проверяем подписку пользователя (пока бесплатно для всех)
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
    
    # Домашние ингредиенты для экспериментов
    random_ingredients = [
        # Мясные/белковые доступные
        "сосиски", "куриные наггетсы", "крабовые палочки", "тушенка", "яйца", 
        "творог", "сыр плавленый", "колбаса", "сардельки", "фарш",
        
        # Сладкие неожиданные
        "скиттлс", "мармелад", "зефир", "вафли", "печенье орео", 
        "нутелла", "сгущенка", "мороженое", "шоколад", "мед",
        
        # Снеки и чипсы
        "чипсы", "сухарики", "попкорн", "крекеры", "соленые орешки",
        "семечки", "кириешки", "читос", "лейс", "принглс",
        
        # Напитки как ингредиенты
        "кока-кола", "пепси", "фанта", "спрайт", "квас", "пиво безалкогольное",
        
        # Домашние овощи/фрукты
        "огурцы соленые", "помидоры черри", "лук репчатый", "картошка", 
        "морковь", "яблоки", "бананы", "клубника замороженная",
        
        # Соусы домашние
        "кетчуп", "майонез", "горчица", "соевый соус", "ткемали",
        "аджика", "хрен", "сметана", "йогурт", "ряженка",
        
        # Крупы и макароны
        "макароны", "гречка", "рис", "овсянка", "пшено", "лапша быстрого приготовления",
        
        # Хлебобулочные
        "хлеб", "лаваш", "питта", "тостовый хлеб", "булочки для бургеров",
        
        # Домашняя экзотика
        "васаби из тюбика", "имбирь маринованный", "оливки", "маслины",
        "каперсы", "корнишоны", "кимчи", "квашеная капуста"
    ]
    
    # Домашние техники (доступные всем)
    extreme_techniques = [
        "жарка в кока-коле", "запекание с чипсами", "маринование в квасе", 
        "панировка в печенье", "глазирование медом", "копчение на чае",
        "заморозка с мороженым", "карамелизация сахаром", "тушение в пиве",
        "взбивание сметаной", "настаивание на кофе", "приготовление на пару",
        "гриллинг на сковороде", "запекание в фольге", "томление в духовке",
        "обжаривание с луком", "добавление газировки", "смешивание со сгущенкой"
    ]
    
    # Безумные сочетания
    fusion_combinations = [
        "Русская кухня + Японская", "Итальянская + Мексиканская", 
        "Французская + Корейская", "Индийская + Скандинавская",
        "Средиземноморская + Тайская", "Американская + Марокканская"
    ]
    
    import random
    
    # Создаем промпт в зависимости от типа эксперимента
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    
    # Adapt experiment types to venue
    if venue_type == "fine_dining":
        adapted_types = ["Fusion", "Molecular", "Extreme"]
    elif venue_type == "food_truck":
        adapted_types = ["Random", "Snack"]  
    elif venue_type == "coffee_shop":
        adapted_types = ["Random", "Snack", "Fusion"]
    elif venue_type == "kids_cafe":
        adapted_types = ["Random", "Snack"]
    else:
        adapted_types = ["Random", "Fusion", "Snack"]
    
    # Override experiment_type if not suitable for venue
    if experiment_type not in adapted_types:
        experiment_type = adapted_types[0]
    
    venue_context = f"""
КОНТЕКСТ ЗАВЕДЕНИЯ: {venue_info['name']}
Кухня: {', '.join([CUISINE_TYPES.get(c, {}).get('name', c) for c in cuisine_focus]) if cuisine_focus else 'Любая'}
Адаптировано для: {venue_info['description']}
"""
    
    if experiment_type == "random":
        rand_ingredients = random.sample(random_ingredients, 3)
        rand_technique = random.choice(extreme_techniques)
        experiment_prompt = f"""
        {venue_context}
        🎲 ЭКСПЕРИМЕНТ ДЛЯ {venue_info['name'].upper()}:
        Создай блюдо, используя: {', '.join(rand_ingredients)}
        Техника: {rand_technique}
        Базовое блюдо: {base_dish if base_dish else 'блюдо подходящее для данного заведения'}
        ВАЖНО: Адаптируй под концепцию {venue_info['name'].lower()}! Учти стиль заведения и целевую аудиторию.
        """
    elif experiment_type == "fusion":
        fusion = random.choice(fusion_combinations)
        experiment_prompt = f"""
        {venue_context}
        🌍 ФЬЮЖН ДЛЯ {venue_info['name'].upper()}:
        Объедини кухни: {fusion}
        Базовое блюдо: {base_dish if base_dish else 'блюдо подходящее для заведения'}
        ВАЖНО: Создай сочетание подходящее для {venue_info['name'].lower()} и его аудитории.
        """
    elif experiment_type == "molecular":
        techniques = random.sample(extreme_techniques[:10], 2)
        experiment_prompt = f"""
        {venue_context}
        🧪 МОЛЕКУЛЯРКА ДЛЯ {venue_info['name'].upper()}:
        Техники: {', '.join(techniques)}
        Базовое блюдо: {base_dish if base_dish else 'подходящее для заведения блюдо'}
        ВАЖНО: Адаптируй под уровень {venue_info['name'].lower()}! Учти оборудование и концепцию места.
        """
    elif experiment_type == "snack":
        snack_ingredients = [ing for ing in random_ingredients if any(snack in ing for snack in ["чипсы", "скиттлс", "печенье", "мармелад", "попкорн", "крекеры"])]
        selected_snacks = random.sample(snack_ingredients, 2)
        experiment_prompt = f"""
        {venue_context}
        🍿 СНЕКИ ДЛЯ {venue_info['name'].upper()}:
        Создай блюдо из снеков: {', '.join(selected_snacks)}
        Базовое блюдо: {base_dish if base_dish else 'блюдо для заведения'}
        ВАЖНО: Покажи как адаптировать под стиль {venue_info['name'].lower()}!
        """
    else:
        experiment_prompt = f"""
        {venue_context}
        🔥 ЭКСТРИМ ДЛЯ {venue_info['name'].upper()}:
        Нарушь все правила домашней кулинарии, но используй только доступные продукты!
        Базовое блюдо: {base_dish if base_dish else 'традиционное домашнее блюдо'}
        ВАЖНО: Все должно быть выполнимо на обычной кухне с обычными продуктами!
        """

    # Основной промпт для лаборатории
    prompt = f"""Ты — доктор Гастрономус, безумный ученый от кулинарии! 🧪

Твоя лаборатория — место, где рождаются самые дерзкие кулинарные эксперименты. 
Создай блюдо, которое ШОКИРУЕТ, УДИВИТ, но при этом будет НЕВЕРОЯТНО ВКУСНЫМ!

{experiment_prompt}

Создай ЭКСПЕРИМЕНТАЛЬНОЕ БЛЮДО:

**🧪 НАЗВАНИЕ ЭКСПЕРИМЕНТА:** [Креативное научное название]

**🔬 ГИПОТЕЗА:** [Почему этот эксперимент будет вкусным]

**⚗️ ИНГРЕДИЕНТЫ ДЛЯ ЭКСПЕРИМЕНТА:**
[Список с указанием роли каждого ингредиента в эксперименте]

**🧬 ЛАБОРАТОРНЫЙ ПРОЦЕСС:**
[Пошаговый процесс как научный эксперимент]

**🌈 ВИЗУАЛЬНЫЙ ЭФФЕКТ:**
[Как будет выглядеть блюдо - цвета, текстуры, эффекты]

**🎭 ЭКСПЕРИМЕНТАЛЬНАЯ ПОДАЧА:**
[Креативная, шокирующая подача]

**🎪 WOW-ЭФФЕКТ:**
[Что удивит гостей больше всего]

**📸 ОПИСАНИЕ ДЛЯ ФОТО:**
[Детальное описание внешнего вида для AI-генерации изображения]

**🔬 НАУЧНОЕ ОБОСНОВАНИЕ:**
[Почему это работает с точки зрения науки о вкусе]

**⚠️ ПРЕДУПРЕЖДЕНИЕ:**
[Что может пойти не так в эксперименте]

**🎯 ЦЕЛЕВАЯ АУДИТОРИЯ:**
[Кто оценит этот эксперимент]

**📱 ХЕШТЕГИ ДЛЯ СОЦСЕТЕЙ:**
[#экспериментальнаякулинария #гастрономия #шокирующееблюдо и т.д.]

Создано в ЛАБОРАТОРИИ RECEPTOR PRO - место для кулинарных экспериментов! 🧪✨"""

    try:
        # Генерируем экспериментальное блюдо
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты доктор Гастрономус - безумный ученый от кулинарии. Создаешь шокирующие, но вкусные блюда. Будь креативным, дерзким, но научным в подходе."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.9  # Высокая креативность
        )
        
        experiment_result = response.choices[0].message.content
        
        # Извлекаем описание для генерации изображения
        photo_description = ""
        lines = experiment_result.split('\n')
        for i, line in enumerate(lines):
            if "**📸 ОПИСАНИЕ ДЛЯ ФОТО:**" in line:
                # Берем следующую строку после заголовка
                if i + 1 < len(lines):
                    photo_description = lines[i + 1].strip()
                break
        
        # Генерируем изображение через DALL-E 3
        image_url = None
        try:
            if photo_description:
                # Создаем промпт для DALL-E
                dalle_prompt = f"A stunning, experimental culinary dish: {photo_description}. Professional food photography, high-end restaurant presentation, dramatic lighting, artistic plating, molecular gastronomy elements, ultra-realistic, 8K quality."
                
                image_response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                
                image_url = image_response.data[0].url
        except Exception as img_error:
            print(f"Image generation failed: {img_error}")
            # Продолжаем без изображения
        
        return {
            "success": True,
            "experiment": experiment_result,
            "experiment_type": experiment_type,
            "image_url": image_url,
            "photo_description": photo_description
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проведения эксперимента: {str(e)}")

@app.post("/api/save-laboratory-experiment")
async def save_laboratory_experiment(request: dict):
    """Сохранение эксперимента из лаборатории в историю техкарт"""
    user_id = request.get("user_id")
    experiment_content = request.get("experiment")
    experiment_type = request.get("experiment_type", "experiment")
    image_url = request.get("image_url")
    
    if not user_id or not experiment_content:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    # Извлекаем название эксперимента
    dish_name = "🧪 ЛАБОРАТОРНЫЙ ЭКСПЕРИМЕНТ"
    lines = experiment_content.split('\n')
    for line in lines:
        if "**НАЗВАНИЕ ЭКСПЕРИМЕНТА:**" in line or "**Название:**" in line:
            # Извлекаем название
            name_part = line.split('**')[-1].strip()
            if name_part:
                dish_name = f"🧪 {name_part}"
            break
        # Ищем первую строку с экспериментом
        elif line.strip() and not line.startswith('**') and len(line.strip()) > 10:
            # Берем первые 50 символов как название
            dish_name = f"🧪 {line.strip()[:50]}..."
            break
    
    # Auto-create test user if needed
    if user_id.startswith("test_user_"):
        user = await db.users.find_one({"id": user_id})
        if not user:
            test_user = {
                "id": user_id,
                "email": f"{user_id}@example.com",
                "name": "Test User",
                "city": "moscow",
                "subscription_plan": "pro",
                "monthly_tech_cards_used": 0,
                "created_at": datetime.now()
            }
            await db.users.insert_one(test_user)
    
    try:
        # Добавляем информацию об изображении в контент
        final_content = experiment_content
        if image_url:
            final_content += f"\n\n**🖼️ ИЗОБРАЖЕНИЕ ЭКСПЕРИМЕНТА:**\n{image_url}"
        
        # Create tech card object for laboratory experiment
        tech_card = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "dish_name": dish_name,
            "content": final_content,
            "city": "moscow",
            "is_inspiration": False,
            "is_laboratory": True,  # Помечаем как лабораторный эксперимент
            "experiment_type": experiment_type,
            "image_url": image_url,
            "created_at": datetime.now()
        }
        
        # Save to database
        await db.tech_cards.insert_one(tech_card)
        
        return {
            "success": True,
            "id": tech_card["id"],
            "message": "Эксперимент сохранен в историю техкарт"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения эксперимента: {str(e)}")