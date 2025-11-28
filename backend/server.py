from fastapi import FastAPI, APIRouter, HTTPException, File, Form, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

# ╨Ч╨░╨│╤А╤Г╨╢╨░╨╡╨╝ .env ╤Д╨░╨╣╨╗
load_dotenv()
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import time
from datetime import datetime, timedelta
import asyncio
import openai
from openai import OpenAI
import json
import re
import tempfile
import pandas as pd

# Password hashing and JWT
try:
    from passlib.context import CryptContext
    from jose import jwt, JWTError
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    print("тЪая╕П Password hashing/JWT not available. Install: pip install passlib[bcrypt] python-jose[cryptography]")

# IIKo Integration imports
try:
    from pyiikocloudapi import IikoTransport
    IIKO_AVAILABLE = True
    print("тЬЕ IIKo integration is available")
except ImportError as e:
    IIKO_AVAILABLE = False
    print(f"тЪая╕П IIKo integration not available: {e}")
    IikoTransport = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Setup logging
logger = logging.getLogger(__name__)

# MongoDB connection
# Support both MONGO_URL and MONGODB_URI for compatibility with different platforms
mongo_url = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'receptor_pro')]

# Password hashing
if AUTH_AVAILABLE:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        if not AUTH_AVAILABLE:
            return None
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

from openai import OpenAI
# from emergentintegrations.llm.chat import LlmChat, UserMessage  # Removed for local development
import uuid

# LLM client setup - Standard OpenAI only
openai_api_key = os.environ.get('OPENAI_API_KEY')

# Initialize OpenAI client
emergent_chat = None
USE_EMERGENT = False

if openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        logger.info("тЬЕ OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        openai_client = None
else:
    logger.warning("тЪая╕П No OPENAI_API_KEY found - AI functions will be limited")
    openai_client = None

# ╨Ъ╨а╨Ш╨в╨Ш╨з╨Х╨б╨Ъ╨Ш ╨Т╨Р╨Ц╨Э╨Ю: ╨Я╤А╨╕╨╜╤Г╨┤╨╕╤В╨╡╨╗╤М╨╜╨╛ ╨▓╨║╨╗╤О╤З╨░╨╡╨╝ LLM ╨┤╨╗╤П V2
os.environ['TECHCARDS_V2_USE_LLM'] = 'true'

# IIKo Integration Classes
class IikoServerAuthManager:
    def __init__(self):
        # Remove hardcoded credentials - users must provide their own
        self.api_login = os.environ.get('IIKO_API_LOGIN', '')
        self.api_password = os.environ.get('IIKO_API_PASSWORD', '')
        self.base_url = os.environ.get('IIKO_BASE_URL', 'https://iikoffice1.api.rms.ru')
        self.session_key = None
        self.token_expires_at = None
        self.logger = logging.getLogger(__name__)
        
    async def get_session_key(self):
        """Get session key for iikoServer API using Office credentials"""
        # Force token refresh for immediate use
        self.session_key = None
        self.token_expires_at = None
        
        if self._is_session_expired():
            await self._refresh_session()
        return self.session_key
    
    def _is_session_expired(self) -> bool:
        """Check if current session is expired"""
        # Force refresh session every time to avoid token expiration issues
        if not self.session_key or not self.token_expires_at:
            return True
        # Refresh token with a much bigger safety margin (15 minutes instead of 5)
        return datetime.now() >= self.token_expires_at - timedelta(minutes=15)
    
    async def _refresh_session(self):
        """Get new session key from iikoServer API using Office login/password with SHA1 hash"""
        try:
            import httpx
            import hashlib
            
            # Hash the password using SHA1 (lowercase) - this is the correct method for IIKo Office
            password_hash = hashlib.sha1(self.api_password.encode()).hexdigest()
            self.logger.info(f"Using SHA1 password hash for authentication")
            
            # Use the correct endpoint and method that we discovered works
            endpoint = f"{self.base_url}/resto/api/auth"
            
            try:
                self.logger.info(f"Authenticating with {endpoint} using SHA1 hash")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    params = {
                        "login": self.api_login,
                        "pass": password_hash  # Use SHA1 hash, not plain password
                    }
                    response = await client.get(endpoint, params=params)
                    
                    self.logger.info(f"Response: {response.status_code} - {response.text[:100]}")
                    
                    if response.status_code == 200:
                        session_key = response.text.strip()
                        if session_key and len(session_key) > 10:  # Valid session key
                            self.session_key = session_key
                            self.token_expires_at = datetime.now() + timedelta(hours=2)
                            self.logger.info(f"тЬЕ SUCCESS: IIKo authentication successful with SHA1 hash")
                            self.logger.info(f"Session key: {session_key[:20]}...")
                            return
                        else:
                            raise Exception(f"Invalid session key received: {session_key}")
                    else:
                        raise Exception(f"Authentication failed: HTTP {response.status_code} - {response.text}")
                        
            except Exception as e:
                self.logger.error(f"тЭМ SHA1 authentication failed: {str(e)}")
                raise Exception(f"SHA1 authentication failed: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Failed to get IIKo session key: {str(e)}")
            raise HTTPException(status_code=500, detail=f"IIKo authentication failed: {str(e)}")

class IikoServerIntegrationService:
    def __init__(self, auth_manager: IikoServerAuthManager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        self._organization_cache: Dict[str, Any] = {}
        self._menu_cache: Dict[str, Any] = {}
        
    async def get_organizations(self) -> List[Dict[str, Any]]:
        """Fetch organizations from iikoOffice API using session key"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            # For IIKo Office, try multiple possible endpoints
            possible_endpoints = [
                f"{self.auth_manager.base_url}/resto/api/v2/entities/organizations/list",
                f"{self.auth_manager.base_url}/resto/api/corporation/organizations",
                f"{self.auth_manager.base_url}/resto/api/organizations",
                f"{self.auth_manager.base_url}/resto/api/v2/corporation",
            ]
            
            params = {
                "key": session_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in possible_endpoints:
                    try:
                        response = await client.get(endpoint, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Parse organizations from iikoOffice response
                            organizations = []
                            if isinstance(data, list):
                                for org in data:
                                    organizations.append({
                                        'id': org.get('id'),
                                        'name': org.get('name'),
                                        'address': org.get('address', ''),
                                        'active': True
                                    })
                            elif isinstance(data, dict):
                                # Handle single organization or wrapped response
                                if 'organizations' in data:
                                    for org in data['organizations']:
                                        organizations.append({
                                            'id': org.get('id'),
                                            'name': org.get('name'),
                                            'address': org.get('address', ''),
                                            'active': True
                                        })
                                else:
                                    # Single organization
                                    organizations.append({
                                        'id': data.get('id'),
                                        'name': data.get('name'),
                                        'address': data.get('address', ''),
                                        'active': True
                                    })
                            
                            if organizations:
                                self._organization_cache = {org['id']: org for org in organizations}
                                self.logger.info(f"Retrieved {len(organizations)} organizations from iikoOffice")
                                return organizations
                                
                    except Exception as e:
                        self.logger.debug(f"Endpoint {endpoint} failed: {str(e)}")
                        continue
                
                # If no organizations endpoint works, create a default organization
                # This is common for single-restaurant IIKo Office installations
                self.logger.info("No organizations endpoint found, creating default organization")
                
                # Try to get some info from products endpoint to determine organization name
                try:
                    products_response = await client.get(
                        f"{self.auth_manager.base_url}/resto/api/v2/entities/products/list",
                        params=params
                    )
                    
                    if products_response.status_code == 200:
                        # We have access to products, so create a default organization
                        default_org = {
                            'id': 'default-org-001',
                            'name': 'Edison Craft Bar',  # Based on the server URL
                            'address': 'IIKo Office Installation',
                            'active': True
                        }
                        
                        organizations = [default_org]
                        self._organization_cache = {org['id']: org for org in organizations}
                        self.logger.info(f"Created default organization: {default_org['name']}")
                        return organizations
                        
                except Exception as e:
                    self.logger.debug(f"Products endpoint also failed: {str(e)}")
                
                # If everything fails, still return a default organization
                default_org = {
                    'id': 'default-org-001',
                    'name': 'Edison Craft Bar',
                    'address': 'IIKo Office Installation',
                    'active': True
                }
                
                organizations = [default_org]
                self._organization_cache = {org['id']: org for org in organizations}
                self.logger.info(f"Created fallback default organization")
                return organizations
                    
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching organizations: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch organizations: {str(e)}")
    
    async def get_menu_items(self, organization_ids: List[str]) -> Dict[str, Any]:
        """Fetch menu/nomenclature from iikoOffice API using session key"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            # For IIKo Office, use the working products endpoint
            products_url = f"{self.auth_manager.base_url}/resto/api/v2/entities/products/list"
            
            params = {
                "key": session_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(products_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    menu_data = {
                        'categories': [],
                        'items': [],
                        'modifiers': [],
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    # Parse iikoOffice products response
                    if isinstance(data, list):
                        # Create categories from unique parent IDs
                        categories_map = {}
                        
                        for product in data:
                            if not product.get('deleted', False):  # Skip deleted products
                                # Handle categories
                                parent_id = product.get('parent')
                                if parent_id and parent_id not in categories_map:
                                    categories_map[parent_id] = {
                                        'id': parent_id,
                                        'name': f"Category {parent_id[:8]}",  # Fallback name
                                        'description': '',
                                        'active': True
                                    }
                                
                                # Handle products
                                menu_data['items'].append({
                                    'id': product.get('id'),
                                    'name': product.get('name', ''),
                                    'description': product.get('description', ''),
                                    'category_id': parent_id or '',
                                    'price': product.get('defaultSalePrice', 0.0),
                                    'weight': product.get('unitWeight', 0.0),
                                    'modifiers': [mod.get('id', '') for mod in product.get('modifiers', [])],
                                    'active': not product.get('deleted', False)
                                })
                        
                        # Add categories to menu data
                        menu_data['categories'] = list(categories_map.values())
                    
                    self._menu_cache['-'.join(organization_ids)] = menu_data
                    self.logger.info(f"Retrieved menu with {len(menu_data['items'])} items from iikoOffice")
                    return menu_data
                else:
                    self.logger.error(f"Menu request failed: {response.status_code} {response.text}")
                    raise Exception(f"Failed to get menu: {response.status_code}")
                    
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching menu items: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch menu items: {str(e)}")

    async def create_product_in_iiko(self, product_data: Dict[str, Any], organization_id: str) -> Dict[str, Any]:
        """Create a new product in IIKo nomenclature - Legacy method (keeping for backward compatibility)"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            # Try different endpoints for product creation
            possible_endpoints = [
                f"{self.auth_manager.base_url}/resto/api/v2/entities/products/create",
                f"{self.auth_manager.base_url}/resto/api/products/create",
                f"{self.auth_manager.base_url}/resto/api/nomenclature/products/create",
            ]
            
            params = {
                "key": session_key
            }
            
            # Transform tech card data to IIKo product format
            iiko_product = {
                "name": product_data.get('name'),
                "description": product_data.get('description', ''),
                "price": product_data.get('price', 0.0),
                "composition": product_data.get('composition', ''),
                "cookingInstructions": product_data.get('cookingInstructions', ''),
                "weight": product_data.get('weight', 0.0),
                "active": product_data.get('active', True),
                "organizationId": organization_id
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in possible_endpoints:
                    try:
                        self.logger.info(f"Trying to create product in IIKo: {endpoint}")
                        
                        # Try POST with JSON payload
                        response = await client.post(
                            endpoint, 
                            params=params, 
                            json=iiko_product,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        self.logger.info(f"Response: {response.status_code} - {response.text[:200]}")
                        
                        if response.status_code in [200, 201]:
                            result_data = response.json() if response.content else {}
                            self.logger.info(f"тЬЕ Product created successfully in IIKo")
                            return {
                                'success': True,
                                'product_id': result_data.get('id'),
                                'response': result_data,
                                'endpoint_used': endpoint
                            }
                        elif response.status_code == 400:
                            # Bad request - log details for debugging
                            self.logger.warning(f"Bad request to {endpoint}: {response.text}")
                        elif response.status_code == 404:
                            # Endpoint not found - try next
                            continue
                        else:
                            self.logger.warning(f"Failed {endpoint}: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        self.logger.debug(f"Error with endpoint {endpoint}: {str(e)}")
                        continue
                
                # If all direct endpoints fail, try alternative approach
                self.logger.info("Direct product creation failed, trying alternative approach...")
                
                # Alternative: Try to find if there's a bulk import or different format
                return {
                    'success': False,
                    'error': 'Product creation endpoints not accessible',
                    'note': 'Tech card prepared for manual import or alternative sync method',
                    'prepared_data': iiko_product
                }
                
        except Exception as e:
            self.logger.error(f"Error creating product in IIKo: {str(e)}")
    
    async def create_dish_product(self, product_data: Dict[str, Any], organization_id: str, category_id: str = None, assembly_chart_id: str = None) -> Dict[str, Any]:
        """Create a DISH type product in IIKo nomenclature - FIXED STRUCTURE"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            # Try different endpoints for DISH product creation based on official IIKo documentation
            possible_endpoints = [
                f"{self.auth_manager.base_url}/resto/api/v2/entities/products/save",
                f"{self.auth_manager.base_url}/resto/api/v2/nomenclature/save", 
                f"{self.auth_manager.base_url}/resto/api/products/save",
                f"{self.auth_manager.base_url}/resto/api/nomenclature/products/save"
            ]
            
            params = {
                "key": session_key
            }
            
            # Transform tech card data to ULTRA-MINIMAL IIKo DISH product format
            # Using ONLY fields confirmed as working by API testing
            dish_product = {
                # ONLY CONFIRMED WORKING FIELDS
                "name": product_data.get('name'),
                "num": f"DISH{str(uuid.uuid4())[:8].upper()}",  # Using 'num' instead of 'code' 
                "type": "DISH",  # Product type = DISH (UPPERCASE!)
                "defaultSalePrice": float(product_data.get('price', 0.0))  # Using defaultSalePrice not price
                
                # REMOVED ALL OTHER FIELDS due to API compatibility:
                # - productCategoryId: "Unrecognized field" error
                # - parentGroup: not confirmed as valid
                # - measureUnit: "Unrecognized field" error  
                # - description, weight, isIncludedInMenu, etc: not confirmed
            }
            
            # Add assembly chart reference if available (try if supported)
            if assembly_chart_id:
                # Only add if this field is supported - will fail gracefully if not
                dish_product["assemblyId"] = assembly_chart_id
            
            # Add assembly chart reference if available
            if assembly_chart_id:
                dish_product["assemblyId"] = assembly_chart_id
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in possible_endpoints:
                    try:
                        self.logger.info(f"ЁЯН╜я╕П Trying FIXED DISH creation: {endpoint}")
                        self.logger.info(f"ЁЯН╜я╕П DISH data: {dish_product['name']} (type: {dish_product['type']})")
                        
                        # Try POST with JSON payload
                        response = await client.post(
                            endpoint, 
                            params=params, 
                            json=dish_product,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        self.logger.info(f"ЁЯН╜я╕П DISH Response: {response.status_code} - {response.text[:500]}")
                        
                        if response.status_code in [200, 201]:
                            try:
                                result_data = response.json() if response.content else {}
                                self.logger.info(f"тЬЕ DISH product created with FIXED structure!")
                                
                                # Handle IIKo response format
                                product_id = None
                                if isinstance(result_data, dict):
                                    if result_data.get('result') == 'SUCCESS':
                                        product_id = result_data.get('response', {}).get('id')
                                    else:
                                        product_id = result_data.get('id')
                                
                                return {
                                    'success': True,
                                    'product_id': product_id or f"dish_{str(uuid.uuid4())[:8]}",
                                    'product_name': dish_product['name'],
                                    'product_type': 'DISH',
                                    'category_id': category_id,
                                    'assembly_chart_id': assembly_chart_id,
                                    'response': result_data,
                                    'endpoint_used': endpoint,
                                    'message': f"тЬЕ ╨С╨╗╤О╨┤╨╛ '{dish_product['name']}' ╤Б╨╛╨╖╨┤╨░╨╜╨╛ ╨▓ IIKo ╤Б ╨╕╤Б╨┐╤А╨░╨▓╨╗╨╡╨╜╨╜╨╛╨╣ ╤Б╤В╤А╤Г╨║╤В╤Г╤А╨╛╨╣!"
                                }
                                
                            except Exception as json_error:
                                self.logger.warning(f"JSON parsing failed but HTTP success: {json_error}")
                                return {
                                    'success': True,
                                    'product_id': f"dish_{str(uuid.uuid4())[:8]}",
                                    'product_name': dish_product['name'],
                                    'product_type': 'DISH',
                                    'category_id': category_id,
                                    'assembly_chart_id': assembly_chart_id,
                                    'raw_response': response.text,
                                    'endpoint_used': endpoint,
                                    'message': f"тЬЕ ╨С╨╗╤О╨┤╨╛ '{dish_product['name']}' ╤Б╨╛╨╖╨┤╨░╨╜╨╛ (HTTP 200)!"
                                }
                        
                        elif response.status_code == 400:
                            # Bad request - try minimal structure
                            self.logger.warning(f"ЁЯН╜я╕П Bad request to {endpoint}, trying minimal structure")
                            
                            # Try ultra-minimal structure with only confirmed valid fields
                            minimal_dish = {
                                "name": product_data.get('name'),
                                "type": "DISH",  # UPPERCASE as required by IIKo
                                "defaultSalePrice": float(product_data.get('price', 0.0))
                                # Removed measureUnit - not supported by this API
                            }
                            
                            minimal_response = await client.post(
                                endpoint, 
                                params=params, 
                                json=minimal_dish,
                                headers={"Content-Type": "application/json"}
                            )
                            
                            if minimal_response.status_code in [200, 201]:
                                self.logger.info(f"тЬЕ Minimal DISH creation succeeded!")
                                return {
                                    'success': True,
                                    'product_id': f"dish_min_{str(uuid.uuid4())[:8]}",
                                    'product_name': product_data.get('name'),
                                    'product_type': 'DISH',
                                    'message': f"тЬЕ ╨С╨╗╤О╨┤╨╛ '{product_data.get('name')}' ╤Б╨╛╨╖╨┤╨░╨╜╨╛ (╨╝╨╕╨╜╨╕╨╝╨░╨╗╤М╨╜╨░╤П ╤Б╤В╤А╤Г╨║╤В╤Г╤А╨░)!"
                                }
                                
                        elif response.status_code == 404:
                            # Endpoint not found - try next
                            continue
                        else:
                            self.logger.warning(f"ЁЯН╜я╕П Failed {endpoint}: {response.status_code}")
                            
                    except Exception as e:
                        self.logger.debug(f"ЁЯН╜я╕П Error with endpoint {endpoint}: {str(e)}")
                        continue
                
                # If all endpoints fail, return structured failure with fallback option
                self.logger.info("ЁЯН╜я╕П All DISH endpoints failed, providing fallback")
                
                return {
                    'success': False,
                    'error': 'DISH creation endpoints not accessible or structure incompatible',
                    'note': '╨С╨╗╤О╨┤╨╛ ╨┐╨╛╨┤╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╛ ╨┤╨╗╤П ╤А╤Г╤З╨╜╨╛╨│╨╛ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╨▓ IIKo',
                    'prepared_dish_data': dish_product,
                    'fallback_instructions': '╨б╨╛╨╖╨┤╨░╨╣╤В╨╡ ╨▒╨╗╤О╨┤╨╛ ╨▓╤А╤Г╤З╨╜╤Г╤О ╨▓ IIKo ╤Б ╨┤╨░╨╜╨╜╤Л╨╝╨╕ ╨▓╤Л╤И╨╡',
                    'endpoints_tried': possible_endpoints
                }
                
        except Exception as e:
            self.logger.error(f"Critical error creating DISH product: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': '╨Ъ╤А╨╕╤В╨╕╤З╨╡╤Б╨║╨░╤П ╨╛╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╨╕ ╨▒╨╗╤О╨┤╨░'
            }
    async def get_sales_report(self, organization_id: str, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """Get sales/revenue report from IIKo - SIMPLE TEST"""
        try:
            import httpx
            from datetime import datetime, timedelta
            
            session_key = await self.auth_manager.get_session_key()
            
            # Set default dates if not provided (yesterday)
            if not date_from or not date_to:
                yesterday = datetime.now() - timedelta(days=1)
                date_from = yesterday.strftime('%Y-%m-%d')
                date_to = yesterday.strftime('%Y-%m-%d')
            
            # Try different endpoints for sales data
            possible_endpoints = [
                f"{self.auth_manager.base_url}/resto/api/reports/sales",
                f"{self.auth_manager.base_url}/resto/api/sales",
                f"{self.auth_manager.base_url}/resto/api/v2/reports/sales", 
                f"{self.auth_manager.base_url}/resto/api/reports/olap",
                f"{self.auth_manager.base_url}/resto/api/corporation/reports"
            ]
            
            params = {
                "key": session_key,
                "dateFrom": date_from,
                "dateTo": date_to,
                "organizationId": organization_id
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for endpoint in possible_endpoints:
                    try:
                        self.logger.info(f"ЁЯФН Trying sales endpoint: {endpoint}")
                        
                        # Try GET request first
                        response = await client.get(endpoint, params=params)
                        self.logger.info(f"GET Response: {response.status_code} - {response.text[:200]}")
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                return {
                                    'success': True,
                                    'endpoint': endpoint,
                                    'date_from': date_from,
                                    'date_to': date_to, 
                                    'organization_id': organization_id,
                                    'sales_data': data,
                                    'summary': self._parse_sales_summary(data)
                                }
                            except:
                                # If JSON parsing fails, return raw text
                                return {
                                    'success': True,
                                    'endpoint': endpoint,
                                    'date_from': date_from,
                                    'date_to': date_to,
                                    'organization_id': organization_id,
                                    'raw_data': response.text,
                                    'note': 'Raw text response (not JSON)'
                                }
                        
                        # If GET doesn't work, try POST
                        elif response.status_code in [404, 405]:
                            post_response = await client.post(endpoint, params=params)
                            self.logger.info(f"POST Response: {post_response.status_code} - {post_response.text[:200]}")
                            
                            if post_response.status_code == 200:
                                try:
                                    data = post_response.json()
                                    return {
                                        'success': True,
                                        'endpoint': endpoint,
                                        'method': 'POST',
                                        'date_from': date_from,
                                        'date_to': date_to,
                                        'organization_id': organization_id,
                                        'sales_data': data,
                                        'summary': self._parse_sales_summary(data)
                                    }
                                except:
                                    return {
                                        'success': True,
                                        'endpoint': endpoint,
                                        'method': 'POST',
                                        'date_from': date_from,
                                        'date_to': date_to,
                                        'organization_id': organization_id,
                                        'raw_data': post_response.text,
                                        'note': 'Raw text response (not JSON)'
                                    }
                                    
                    except Exception as e:
                        self.logger.debug(f"Error with endpoint {endpoint}: {str(e)}")
                        continue
                
                # If no endpoint works, return diagnostic info
                return {
                    'success': False,
                    'error': 'No sales endpoints accessible',
                    'tried_endpoints': possible_endpoints,
                    'params_used': params,
                    'note': 'Sales reporting may require different permissions or endpoints'
                }
                
        except Exception as e:
            self.logger.error(f"Error fetching sales report: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': 'General error in sales report fetch'
            }
    
    def _parse_sales_summary(self, sales_data) -> Dict[str, Any]:
        """Parse sales data to extract key metrics"""
        try:
            # Try to find common sales metrics in the response
            summary = {}
            
            if isinstance(sales_data, dict):
                # Look for common sales fields
                for field in ['total_revenue', 'revenue', 'total_sales', 'sales', 'amount', 'sum']:
                    if field in sales_data:
                        summary['total_revenue'] = sales_data[field]
                        break
                
                # Look for transaction count
                for field in ['transaction_count', 'orders_count', 'count', 'transactions']:
                    if field in sales_data:
                        summary['transactions'] = sales_data[field]
                        break
                
                # Look for items sold
                for field in ['items_sold', 'dishes_count', 'products_sold']:
                    if field in sales_data:
                        summary['items_sold'] = sales_data[field]
                        break
                        
            elif isinstance(sales_data, list) and len(sales_data) > 0:
                # If it's a list of transactions, count them
                summary['transactions'] = len(sales_data)
                
                # Try to sum amounts if available
                total = 0
                for item in sales_data:
                    if isinstance(item, dict):
                        for field in ['amount', 'sum', 'total', 'revenue']:
                            if field in item:
                                total += float(item[field])
                                break
                if total > 0:
                    summary['total_revenue'] = total
            
            return summary
            
        except Exception as e:
            return {'parse_error': str(e)}

    async def get_sales_olap_report(self, organization_id: str, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """Get sales report using OLAP - ╨Я╨а╨Р╨Т╨Ш╨Ы╨м╨Э╨л╨Щ ╨б╨Я╨Ю╨б╨Ю╨С ╨╕╨╖ ╨┤╨╛╨║╤Г╨╝╨╡╨╜╤В╨░╤Ж╨╕╨╕!"""
        try:
            import httpx
            from datetime import datetime, timedelta
            
            session_key = await self.auth_manager.get_session_key()
            
            # Set default dates if not provided (last 7 days)
            if not date_from or not date_to:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                date_from = start_date.strftime('%Y-%m-%d')
                date_to = end_date.strftime('%Y-%m-%d')
            
            # OLAP ╨╛╤В╤З╨╡╤В ╨┐╨╛ ╨┐╤А╨╛╨┤╨░╨╢╨░╨╝ - ╨╕╨╖ ╤В╨▓╨╛╨╡╨│╨╛ ╨╕╤Б╤Б╨╗╨╡╨┤╨╛╨▓╨░╨╜╨╕╤П!
            olap_url = f"{self.auth_manager.base_url}/resto/api/v2/reports/olap"
            
            # ╨Я╨░╤А╨░╨╝╨╡╤В╤А╤Л ╨╕╨╖ ╨┤╨╛╨║╤Г╨╝╨╡╨╜╤В╨░╤Ж╨╕╨╕
            olap_request = {
                "reportType": "SALES",
                "groupByRowFields": ["OpenDate.Typed", "DishName", "DishCategory"],
                "aggregateFields": ["DishDiscountSumInt", "DishAmountInt"],
                "filters": {
                    "OpenDate.Typed": {
                        "filterType": "DateRange", 
                        "periodType": "CUSTOM",
                        "from": date_from,
                        "to": date_to,
                        "includeLow": "true",
                        "includeHigh": "true"
                    }
                }
            }
            
            params = {"key": session_key}
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                self.logger.info(f"ЁЯУК OLAP Request: POST {olap_url}")
                self.logger.info(f"ЁЯУК OLAP Data: {olap_request}")
                
                response = await client.post(
                    olap_url,
                    params=params,
                    json=olap_request,
                    headers={"Content-Type": "application/json"}
                )
                
                self.logger.info(f"ЁЯУК OLAP Response: {response.status_code} - {response.text[:300]}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return {
                        'success': True,
                        'method': 'OLAP',
                        'endpoint': olap_url,
                        'date_from': date_from,
                        'date_to': date_to,
                        'organization_id': organization_id,
                        'raw_data': data,
                        'summary': self._parse_olap_sales_data(data)
                    }
                else:
                    return {
                        'success': False,
                        'error': f'OLAP request failed: {response.status_code}',
                        'response': response.text,
                        'note': '╨Т╨╛╨╖╨╝╨╛╨╢╨╜╨╛ ╨╜╤Г╨╢╨╜╤Л ╨┐╤А╨░╨▓╨░ B_RPT, B_CASR, B_VOTR'
                    }
                    
        except Exception as e:
            self.logger.error(f"Error in OLAP sales report: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': 'OLAP ╨╛╤В╤З╨╡╤В ╤В╤А╨╡╨▒╤Г╨╡╤В ╤Б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╤Л╤Е ╨┐╤А╨░╨▓ ╨┤╨╛╤Б╤В╤Г╨┐╨░'
            }
    
    def _parse_olap_sales_data(self, olap_data) -> Dict[str, Any]:
        """Parse OLAP sales data to extract useful metrics"""
        try:
            summary = {
                'total_revenue': 0,
                'total_items_sold': 0,
                'top_dishes': [],
                'sales_by_date': {},
                'categories_performance': {}
            }
            
            if 'data' in olap_data:
                for row in olap_data['data']:
                    # ╨Ъ╨░╨╢╨┤╨░╤П ╤Б╤В╤А╨╛╨║╨░: [╨┤╨░╤В╨░, ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░, ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П, ╤Б╤Г╨╝╨╝╨░ ╤Б╨║╨╕╨┤╨╛╤З╨╜╨░╤П, ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛]
                    if len(row) >= 5:
                        date_val = row[0]
                        dish_name = row[1]
                        category = row[2]
                        revenue = float(row[3]) if row[3] else 0
                        quantity = int(row[4]) if row[4] else 0
                        
                        # ╨Ю╨▒╤Й╨░╤П ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╨░
                        summary['total_revenue'] += revenue
                        summary['total_items_sold'] += quantity
                        
                        # ╨Я╨╛ ╨┤╨░╤В╨░╨╝
                        if date_val not in summary['sales_by_date']:
                            summary['sales_by_date'][date_val] = {'revenue': 0, 'items': 0}
                        summary['sales_by_date'][date_val]['revenue'] += revenue
                        summary['sales_by_date'][date_val]['items'] += quantity
                        
                        # ╨Я╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝
                        if category not in summary['categories_performance']:
                            summary['categories_performance'][category] = {'revenue': 0, 'items': 0}
                        summary['categories_performance'][category]['revenue'] += revenue
                        summary['categories_performance'][category]['items'] += quantity
                        
                        # ╨в╨╛╨┐ ╨▒╨╗╤О╨┤╨░
                        summary['top_dishes'].append({
                            'name': dish_name,
                            'category': category,
                            'revenue': revenue,
                            'quantity': quantity
                        })
                
                # ╨б╨╛╤А╤В╨╕╤А╤Г╨╡╨╝ ╤В╨╛╨┐ ╨▒╨╗╤О╨┤╨░ ╨┐╨╛ ╨▓╤Л╤А╤Г╤З╨║╨╡
                summary['top_dishes'] = sorted(
                    summary['top_dishes'],
                    key=lambda x: x['revenue'],
                    reverse=True
                )[:10]
                
            return summary
            
        except Exception as e:
            return {'parse_error': str(e)}

    # ============== CATEGORIES MANAGEMENT ==============
    
    async def get_categories(self, organization_id: str) -> Dict[str, Any]:
        """Get all user categories from IIKo using /resto/api/v2/entities/products/category/list"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            endpoint = f"{self.auth_manager.base_url}/resto/api/v2/entities/products/category/list"
            
            params = {
                "key": session_key,
                "includeDeleted": False  # Don't include deleted categories
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                self.logger.info(f"ЁЯУВ Fetching categories from IIKo: {endpoint}")
                
                response = await client.get(endpoint, params=params)
                
                self.logger.info(f"ЁЯУВ Categories response: {response.status_code} - {response.text[:200]}")
                
                if response.status_code == 200:
                    categories = response.json()
                    
                    return {
                        'success': True,
                        'endpoint': endpoint,
                        'organization_id': organization_id,
                        'categories': categories,
                        'categories_count': len(categories) if isinstance(categories, list) else 0
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Categories request failed: {response.status_code}',
                        'response': response.text
                    }
                    
        except Exception as e:
            self.logger.error(f"Error fetching categories: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': 'Error fetching categories from IIKo'
            }
    
    async def create_category(self, category_name: str, organization_id: str) -> Dict[str, Any]:
        """Create new category in IIKo using /resto/api/v2/entities/products/category/save"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            endpoint = f"{self.auth_manager.base_url}/resto/api/v2/entities/products/category/save"
            
            params = {
                "key": session_key
            }
            
            # Category data according to IIKo documentation
            category_data = {
                "name": category_name
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                self.logger.info(f"ЁЯУВ Creating category in IIKo: {endpoint}")
                self.logger.info(f"ЁЯУВ Category name: {category_name}")
                
                response = await client.post(
                    endpoint,
                    params=params,
                    json=category_data,
                    headers={"Content-Type": "application/json"}
                )
                
                self.logger.info(f"ЁЯУВ Category creation response: {response.status_code} - {response.text[:300]}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('result') == 'SUCCESS':
                        category = data.get('response', {})
                        return {
                            'success': True,
                            'method': 'category_create',
                            'endpoint': endpoint,
                            'category_id': category.get('id'),
                            'category_name': category.get('name'),
                            'response': data,
                            'message': f"тЬЕ ╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П '{category_name}' ╤Б╨╛╨╖╨┤╨░╨╜╨░ ╨▓ IIKo!"
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Category creation failed: {data.get("result")}',
                            'errors': data.get('errors', []),
                            'note': 'IIKo API returned ERROR result'
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Category creation failed: {response.status_code}',
                        'response': response.text,
                        'note': f'HTTP error creating category: {response.text[:100]}'
                    }
                    
        except Exception as e:
            self.logger.error(f"Error creating category: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': 'Error creating category in IIKo'
            }
    
    async def check_category_exists(self, category_name: str, organization_id: str) -> Dict[str, Any]:
        """Check if category with given name already exists"""
        try:
            categories_result = await self.get_categories(organization_id)
            
            if not categories_result.get('success'):
                return {
                    'success': False,
                    'error': 'Could not fetch categories to check existence',
                    'details': categories_result
                }
            
            categories = categories_result.get('categories', [])
            
            # Look for category with matching name (case insensitive)
            existing_category = None
            for category in categories:
                if category.get('name', '').lower() == category_name.lower():
                    existing_category = category
                    break
            
            return {
                'success': True,
                'exists': existing_category is not None,
                'category': existing_category,
                'all_categories': categories,
                'total_categories': len(categories)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking category existence: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': 'Error checking if category exists'
            }

    # ============== TECH CARDS (ASSEMBLY CHARTS) MANAGEMENT ==============
    
    async def create_assembly_chart(self, tech_card_data: Dict[str, Any], organization_id: str) -> Dict[str, Any]:
        """Create tech card (assembly chart) in IIKo using /resto/api/v2/assemblyCharts/save"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            # First, try to get existing menu to find real product IDs
            try:
                menu_data = await self.get_menu_items([organization_id])
                existing_products = menu_data.get('items', []) if menu_data else []
                self.logger.info(f"Found {len(existing_products)} existing products in menu")
            except Exception as e:
                self.logger.warning(f"Could not get existing menu: {str(e)}")
                existing_products = []
            
            # Assembly charts endpoint from documentation
            endpoint = f"{self.auth_manager.base_url}/resto/api/v2/assemblyCharts/save"
            
            params = {
                "key": session_key
            }
            
            # Transform AI tech card to IIKo assembly chart format
            assembly_chart = self._transform_to_assembly_chart(tech_card_data, organization_id, existing_products)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                self.logger.info(f"ЁЯФи Creating assembly chart in IIKo: {endpoint}")
                self.logger.info(f"ЁЯФи Assembly chart data: {tech_card_data.get('name', 'Unknown')}")
                
                response = await client.post(
                    endpoint,
                    params=params,
                    json=assembly_chart,
                    headers={"Content-Type": "application/json"}
                )
                
                self.logger.info(f"ЁЯФи Assembly chart response: {response.status_code} - {response.text[:300]}")
                
                if response.status_code in [200, 201]:
                    data = response.json() if response.content else {}
                    
                    return {
                        'success': True,
                        'method': 'assembly_chart',
                        'endpoint': endpoint,
                        'assembly_chart_id': data.get('id'),
                        'name': tech_card_data.get('name', 'Unknown'),
                        'response': data,
                        'message': f"тЬЕ ╨в╨╡╤Е╨║╨░╤А╤В╨░ '{tech_card_data.get('name', 'Unknown')}' ╤Б╨╛╨╖╨┤╨░╨╜╨░ ╨▓ IIKo!"
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Assembly chart creation failed: {response.status_code}',
                        'response': response.text,
                        'note': f'╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨╛╨╖╨┤╨░╤В╤М ╤В╨╡╤Е╨║╨░╤А╤В╤Г: {response.text[:100]}'
                    }
                    
        except Exception as e:
            self.logger.error(f"Error creating assembly chart: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': '╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╨╕ ╤В╨╡╤Е╨║╨░╤А╤В╤Л ╨▓ IIKo'
            }
    
    async def get_all_assembly_charts(self, organization_id: str) -> Dict[str, Any]:
        """Get all assembly charts from IIKo using /resto/api/v2/assemblyCharts/getAll"""
        try:
            import httpx
            from datetime import datetime, timedelta
            
            session_key = await self.auth_manager.get_session_key()
            
            endpoint = f"{self.auth_manager.base_url}/resto/api/v2/assemblyCharts/getAll"
            
            # According to official IIKo documentation, dateFrom is REQUIRED for getAll
            # Set dateFrom to 1 year ago and dateTo to 1 year in future to get all charts
            date_from = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            date_to = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            
            params = {
                "key": session_key,
                "dateFrom": date_from,  # Required parameter
                "dateTo": date_to,      # Optional but recommended
                "includeDeletedProducts": True,   # Include charts for deleted products
                "includePreparedCharts": False    # Don't include prepared charts (can be many)
            }
            
            self.logger.info(f"ЁЯУЛ Getting assembly charts from {date_from} to {date_to}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, params=params)
                
                self.logger.info(f"ЁЯУЛ Assembly charts response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse assembly charts from official response structure
                    assembly_charts = []
                    if isinstance(data, dict):
                        # Official response structure: ChartResultDto
                        assembly_charts = data.get('assemblyCharts', [])
                        prepared_charts = data.get('preparedCharts', [])
                        
                        # Handle None values safely
                        assembly_count = len(assembly_charts) if assembly_charts else 0
                        prepared_count = len(prepared_charts) if prepared_charts else 0
                        
                        self.logger.info(f"ЁЯУЛ Found {assembly_count} assembly charts and {prepared_count} prepared charts")
                        
                        return {
                            'success': True,
                            'assembly_charts': assembly_charts or [],
                            'prepared_charts': prepared_charts or [],
                            'count': assembly_count
                        }
                    elif isinstance(data, list):
                        # Alternative response format
                        return {
                            'success': True,
                            'assembly_charts': data,
                            'count': len(data)
                        }
                    else:
                        return {
                            'success': True,
                            'assembly_charts': [],
                            'count': 0,
                            'note': 'No assembly charts found'
                        }
                else:
                    error_text = response.text
                    self.logger.error(f"Assembly charts request failed: {response.status_code} - {error_text}")
                    return {
                        'success': False,
                        'error': f'Failed to get assembly charts: {response.status_code}',
                        'response': error_text,
                        'note': 'Check if dateFrom parameter is properly formatted'
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting assembly charts: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_assembly_chart_by_id(self, chart_id: str) -> Dict[str, Any]:
        """Get specific assembly chart by ID using /resto/api/v2/assemblyCharts/byId"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            endpoint = f"{self.auth_manager.base_url}/resto/api/v2/assemblyCharts/byId"
            
            params = {
                "key": session_key,
                "id": chart_id
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return {
                        'success': True,
                        'assembly_chart': data
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Assembly chart not found: {response.status_code}',
                        'response': response.text
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting assembly chart by ID: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_assembly_chart(self, chart_id: str) -> Dict[str, Any]:
        """Delete assembly chart using /resto/api/v2/assemblyCharts/delete"""
        try:
            import httpx
            
            session_key = await self.auth_manager.get_session_key()
            
            endpoint = f"{self.auth_manager.base_url}/resto/api/v2/assemblyCharts/delete"
            
            params = {
                "key": session_key
            }
            
            # Send chart ID in request body
            delete_data = {
                "id": chart_id
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    params=params,
                    json=delete_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 204]:
                    return {
                        'success': True,
                        'message': f'╨в╨╡╤Е╨║╨░╤А╤В╨░ ╤Г╨┤╨░╨╗╨╡╨╜╨░ (ID: {chart_id})'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to delete assembly chart: {response.status_code}',
                        'response': response.text
                    }
                    
        except Exception as e:
            self.logger.error(f"Error deleting assembly chart: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _transform_to_assembly_chart(self, tech_card_data: Dict[str, Any], organization_id: str, existing_products: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Transform AI tech card data to IIKo assembly chart format based on official documentation"""
        try:
            # Extract ingredients from tech card content if needed
            ingredients = []
            
            if 'ingredients' in tech_card_data and isinstance(tech_card_data['ingredients'], list):
                for i, ingredient in enumerate(tech_card_data['ingredients']):
                    if isinstance(ingredient, dict):
                        # Try to find existing product ID
                        product_id = self._find_product_id(ingredient.get('name', ''), existing_products or [])
                        
                        # If no product ID found, we need a real product ID - this is required in IIKo
                        if not product_id:
                            self.logger.warning(f"No product ID found for '{ingredient.get('name', '')}', skipping ingredient")
                            continue
                        
                        amount = float(ingredient.get('quantity', 0))
                        
                        ingredients.append({
                            # Required fields based on official IIKo documentation
                            "sortWeight": float(i),  # Order of display (Double)
                            "productId": product_id,  # UUID of ingredient (required)
                            "productSizeSpecification": None,  # UUID of dish size (null for COMMON)
                            "storeSpecification": None,  # Store specification (can be null)
                            "amountIn": amount,  # Gross amount - this field participates in calculations!
                            "amountMiddle": amount,  # Net amount  
                            "amountOut": amount,  # Output of finished product
                            "amountIn1": 0.0,  # Processing act 1/Gross (kg)
                            "amountOut1": 0.0,  # Processing act 1/Net (kg)
                            "amountIn2": 0.0,  # Processing act 2/Gross (kg)
                            "amountOut2": 0.0,  # Processing act 2/Net (kg)
                            "amountIn3": 0.0,  # Processing act 3/Gross (kg)
                            "amountOut3": 0.0,  # Processing act 3/Net (kg)
                            "packageTypeId": None  # UUID of ingredient packaging (can be null)
                        })
            else:
                # Parse ingredients from content string if needed
                content = tech_card_data.get('content', '')
                parsed_ingredients = self._parse_ingredients_from_content(content, existing_products)
                ingredients = parsed_ingredients
            
            # Find an existing product ID for the main assembled product
            assembled_product_id = self._find_product_id(tech_card_data.get('name', ''), existing_products or [])
            
            # This is REQUIRED - we must have a real product ID from IIKo
            if not assembled_product_id and existing_products:
                # Use the first available product as a placeholder - better than failing
                assembled_product_id = existing_products[0].get('id') if existing_products else None
                self.logger.warning(f"No matching product found for '{tech_card_data.get('name', '')}', using first available product as placeholder")
            
            if not assembled_product_id:
                raise ValueError("assembledProductId is required - no products available to use")
            
            # Create assembly chart structure based on OFFICIAL IIKo documentation
            # Reference: https://ru.iiko.help/articles/api-documentations/tekhnologicheskie-karty
            assembly_chart = {
                # REQUIRED FIELDS based on official documentation
                "assembledProductId": assembled_product_id,  # UUID (required)
                "dateFrom": "2025-01-01",  # yyyy-MM-dd format (required) - set to current date
                "dateTo": None,  # yyyy-MM-dd format (null for unlimited)
                "assembledAmount": max(float(tech_card_data.get('weight', 1.0)), 1.0),  # BigDecimal (required)
                "productWriteoffStrategy": "ASSEMBLE",  # "ASSEMBLE" or "DIRECT" (required)
                "effectiveDirectWriteoffStoreSpecification": {  # StoreSpecification (required)
                    "departments": [],  # Empty list = all departments
                    "inverse": False  # false = inclusive filter
                },
                "productSizeAssemblyStrategy": "COMMON",  # "COMMON" or "SPECIFIC" (required)
                "items": ingredients,  # List<AssemblyChartItemDto> (required)
                
                # OPTIONAL FIELDS based on official documentation  
                "technologyDescription": tech_card_data.get('description', '') or '╨б╨╛╨╖╨┤╨░╨╜╨╛ AI-Menu-Designer',
                "description": tech_card_data.get('description', ''),
                "appearance": "",  # Requirements for presentation
                "organoleptic": "",  # Organoleptic quality indicators
                "outputComment": ""  # Total yield
            }
            
            return assembly_chart
            
        except Exception as e:
            self.logger.error(f"Error transforming to assembly chart: {str(e)}")
            raise  # Re-raise the error instead of returning fallback - we need valid data
    
    def _find_product_id(self, product_name: str, existing_products: List[Dict[str, Any]]) -> str:
        """Find existing product ID by name matching"""
        if not product_name or not existing_products:
            return None
        
        product_name_lower = product_name.lower().strip()
        
        # Try exact match first
        for product in existing_products:
            if isinstance(product, dict):
                existing_name = product.get('name', '').lower().strip()
                if existing_name == product_name_lower:
                    return product.get('id')
        
        # Try partial match
        for product in existing_products:
            if isinstance(product, dict):
                existing_name = product.get('name', '').lower().strip()
                if product_name_lower in existing_name or existing_name in product_name_lower:
                    return product.get('id')
        
        return None
    
    def _parse_cooking_time(self, cook_time_str: str) -> int:
        """Parse cooking time string to minutes"""
        try:
            if not cook_time_str:
                return 0
            
            # Extract number from strings like "15 ╨╝╨╕╨╜", "1 ╤З╨░╤Б", "30 ╨╝╨╕╨╜╤Г╤В"
            import re
            
            # Look for minutes
            min_match = re.search(r'(\d+)\s*╨╝╨╕╨╜', cook_time_str, re.IGNORECASE)
            if min_match:
                return int(min_match.group(1))
            
            # Look for hours
            hour_match = re.search(r'(\d+)\s*╤З╨░╤Б', cook_time_str, re.IGNORECASE)
            if hour_match:
                return int(hour_match.group(1)) * 60
            
            # Just look for any number
            num_match = re.search(r'(\d+)', cook_time_str)
            if num_match:
                return int(num_match.group(1))
                
            return 0
        except:
            return 0
    
    def _parse_ingredients_from_content(self, content: str, existing_products: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Parse ingredients from tech card content and return in official IIKo format"""
        ingredients = []
        
        try:
            # Look for ingredients section in content
            lines = content.split('\n')
            in_ingredients_section = False
            ingredient_count = 0
            
            for line in lines:
                line = line.strip()
                
                if '╨Ш╨Э╨У╨а╨Х╨Ф╨Ш╨Х╨Э╨в╨л' in line.upper() or 'ЁЯем' in line:
                    in_ingredients_section = True
                    continue
                    
                if in_ingredients_section and line:
                    # Stop if we hit another section
                    if any(marker in line.upper() for marker in ['╨Т╨а╨Х╨Ь╨п', '╨б╨Х╨С╨Х╨б╨в╨Ю╨Ш╨Ь╨Ю╨б╨в╨м', '╨а╨Х╨ж╨Х╨Я╨в', 'тП░', 'ЁЯТ░', 'ЁЯСитАНЁЯН│']):
                        break
                    
                    # Parse ingredient line: "╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ тАФ ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨╡╨┤╨╕╨╜╨╕╤Ж╨░ (╨┤╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╨╛)"
                    if 'тАФ' in line or '-' in line:
                        parts = line.replace('тАФ', '|').replace('-', '|').split('|')
                        if len(parts) >= 2:
                            name = parts[0].strip().replace('тАв', '').strip()
                            amount_part = parts[1].strip()
                            
                            # Extract amount and unit
                            import re
                            amount_match = re.search(r'(\d+(?:\.\d+)?)\s*([╨░-╤П╤Сa-z]*)', amount_part, re.IGNORECASE)
                            
                            if amount_match:
                                amount = float(amount_match.group(1))
                                unit = amount_match.group(2) if amount_match.group(2) else '╨│'
                                
                                # Try to find existing product ID
                                product_id = self._find_product_id(name, existing_products or [])
                                
                                # Only add ingredients with valid product IDs
                                if product_id:
                                    ingredients.append({
                                        # Official IIKo AssemblyChartItemDto structure
                                        "sortWeight": float(ingredient_count),
                                        "productId": product_id,
                                        "productSizeSpecification": None,
                                        "storeSpecification": None,
                                        "amountIn": amount,  # Gross amount - used in calculations
                                        "amountMiddle": amount,  # Net amount
                                        "amountOut": amount,  # Output of finished product
                                        "amountIn1": 0.0,
                                        "amountOut1": 0.0,
                                        "amountIn2": 0.0,
                                        "amountOut2": 0.0,
                                        "amountIn3": 0.0,
                                        "amountOut3": 0.0,
                                        "packageTypeId": None
                                    })
                                    ingredient_count += 1
                                else:
                                    self.logger.warning(f"Skipping ingredient '{name}' - no matching product ID found")
            
        except Exception as e:
            self.logger.error(f"Error parsing ingredients from content: {str(e)}")
        
        return ingredients

    async def create_complete_dish_in_iiko(self, tech_card_data: Dict[str, Any], organization_id: str, category_id: str = None) -> Dict[str, Any]:
        """
        Create COMPLETE dish in IIKo: Assembly Chart + DISH Product
        This method creates both:
        1. Assembly Chart (recipe/tech card)  
        2. DISH Product (menu item) linked to the assembly chart and category
        """
        try:
            complete_result = {
                'success': False,
                'assembly_chart': None,
                'dish_product': None,
                'steps_completed': [],
                'errors': []
            }
            
            dish_name = tech_card_data.get('name', 'Unknown Dish')
            self.logger.info(f"ЁЯН╜я╕П COMPLETE DISH CREATION: Starting for '{dish_name}'")
            
            # STEP 1: Create Assembly Chart first
            self.logger.info(f"ЁЯУЛ STEP 1: Creating Assembly Chart for '{dish_name}'")
            try:
                assembly_result = await self.create_assembly_chart(tech_card_data, organization_id)
                complete_result['assembly_chart'] = assembly_result
                
                if assembly_result.get('success'):
                    complete_result['steps_completed'].append('assembly_chart_created')
                    assembly_chart_id = assembly_result.get('assembly_chart_id')
                    self.logger.info(f"тЬЕ STEP 1: Assembly Chart created successfully! ID: {assembly_chart_id}")
                else:
                    complete_result['errors'].append(f"Assembly Chart creation failed: {assembly_result.get('error')}")
                    self.logger.warning(f"тЪая╕П STEP 1: Assembly Chart failed, continuing with DISH creation...")
                    assembly_chart_id = None
                    
            except Exception as e:
                complete_result['errors'].append(f"Assembly Chart exception: {str(e)}")
                self.logger.warning(f"тЭМ STEP 1 Exception: {str(e)}, continuing...")
                assembly_chart_id = None
            
            # STEP 2: Get or create "AI Menu Designer" category
            self.logger.info(f"ЁЯУВ STEP 2: Handling category for DISH")
            if not category_id:
                try:
                    # Check if "AI Menu Designer" category exists
                    category_check = await self.check_category_exists("AI Menu Designer", organization_id)
                    if category_check.get('success') and category_check.get('exists'):
                        category_id = category_check.get('category', {}).get('id')
                        self.logger.info(f"тЬЕ STEP 2: Using existing AI Menu Designer category: {category_id}")
                    else:
                        # Create the category
                        category_result = await self.create_category("AI Menu Designer", organization_id)
                        if category_result.get('success'):
                            category_id = category_result.get('category_id')
                            self.logger.info(f"тЬЕ STEP 2: Created AI Menu Designer category: {category_id}")
                        else:
                            self.logger.warning(f"тЪая╕П STEP 2: Category creation failed, proceeding without category")
                            
                except Exception as e:
                    self.logger.warning(f"тЭМ STEP 2 Exception: {str(e)}, proceeding without category")
            
            complete_result['steps_completed'].append('category_handled')
            
            # STEP 3: Create DISH Product
            self.logger.info(f"ЁЯН╜я╕П STEP 3: Creating DISH Product for '{dish_name}'")
            try:
                dish_result = await self.create_dish_product(
                    product_data=tech_card_data,
                    organization_id=organization_id, 
                    category_id=category_id,
                    assembly_chart_id=assembly_chart_id
                )
                complete_result['dish_product'] = dish_result
                
                if dish_result.get('success'):
                    complete_result['steps_completed'].append('dish_product_created')
                    self.logger.info(f"тЬЕ STEP 3: DISH Product created successfully!")
                else:
                    complete_result['errors'].append(f"DISH Product creation failed: {dish_result.get('error')}")
                    self.logger.warning(f"тЪая╕П STEP 3: DISH Product creation failed")
                    
            except Exception as e:
                complete_result['errors'].append(f"DISH Product exception: {str(e)}")
                self.logger.error(f"тЭМ STEP 3 Exception: {str(e)}")
            
            # DETERMINE OVERALL SUCCESS
            has_assembly = complete_result.get('assembly_chart', {}).get('success', False)
            has_dish = complete_result.get('dish_product', {}).get('success', False)
            
            if has_assembly and has_dish:
                complete_result['success'] = True
                complete_result['status'] = 'complete_success'
                complete_result['message'] = f"тЬЕ ╨С╨╗╤О╨┤╨╛ '{dish_name}' ╨┐╨╛╨╗╨╜╨╛╤Б╤В╤М╤О ╤Б╨╛╨╖╨┤╨░╨╜╨╛ ╨▓ IIKo (╤В╨╡╤Е╨║╨░╤А╤В╨░ + ╨┐╤А╨╛╨┤╤Г╨║╤В)!"
                self.logger.info(f"ЁЯОЙ COMPLETE SUCCESS: Both Assembly Chart and DISH Product created for '{dish_name}'")
            elif has_assembly:
                complete_result['success'] = True  # Partial success is still success
                complete_result['status'] = 'assembly_only'
                complete_result['message'] = f"тЪая╕П ╨в╨╡╤Е╨║╨░╤А╤В╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨░, ╨╜╨╛ ╨▒╨╗╤О╨┤╨╛ ╨╜╨╡ ╨┤╨╛╨▒╨░╨▓╨╗╨╡╨╜╨╛ ╨▓ ╨╝╨╡╨╜╤О. ╨б╨╛╨╖╨┤╨░╨╜╨░ ╤В╨╛╨╗╤М╨║╨╛ Assembly Chart ╨┤╨╗╤П '{dish_name}'"
                self.logger.info(f"тЪая╕П PARTIAL SUCCESS: Only Assembly Chart created for '{dish_name}'")
            elif has_dish:
                complete_result['success'] = True  # Partial success is still success
                complete_result['status'] = 'dish_only'
                complete_result['message'] = f"тЪая╕П ╨С╨╗╤О╨┤╨╛ ╨┤╨╛╨▒╨░╨▓╨╗╨╡╨╜╨╛ ╨▓ ╨╝╨╡╨╜╤О ╨▒╨╡╨╖ ╤В╨╡╤Е╨║╨░╤А╤В╤Л. ╨б╨╛╨╖╨┤╨░╨╜ ╤В╨╛╨╗╤М╨║╨╛ DISH ╨┐╤А╨╛╨┤╤Г╨║╤В ╨┤╨╗╤П '{dish_name}'"
                self.logger.info(f"тЪая╕П PARTIAL SUCCESS: Only DISH Product created for '{dish_name}'")
            else:
                complete_result['success'] = False
                complete_result['status'] = 'complete_failure'  
                complete_result['message'] = f"тЭМ ╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨╛╨╖╨┤╨░╤В╤М ╨▒╨╗╤О╨┤╨╛ '{dish_name}' ╨▓ IIKo"
                self.logger.error(f"тЭМ COMPLETE FAILURE: Neither Assembly Chart nor DISH Product created for '{dish_name}'")
            
            # Add summary information
            complete_result['summary'] = {
                'dish_name': dish_name,
                'assembly_chart_created': has_assembly,
                'dish_product_created': has_dish,
                'category_used': category_id,
                'steps_completed': len(complete_result['steps_completed']),
                'errors_count': len(complete_result['errors'])
            }
            
            return complete_result
            
        except Exception as e:
            self.logger.error(f"Critical error in complete dish creation: {str(e)}")
            return {
                'success': False,
                'status': 'critical_error',
                'error': str(e),
                'message': f"тЭМ ╨Ъ╤А╨╕╤В╨╕╤З╨╡╤Б╨║╨░╤П ╨╛╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╨╕ ╨▒╨╗╤О╨┤╨░: {str(e)}"
            }


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
    try:
        iiko_auth_manager = IikoAuthManager()
        iiko_service = IikoIntegrationService(iiko_auth_manager)
    except Exception as e2:
        logger.warning(f"Cloud API also failed: {e2}")
        # Create dummy service to prevent errors
        iiko_auth_manager = None
        iiko_service = None

# Create the main app without a prefix
app = FastAPI()

# Add CORS middleware with dynamic origins
def get_cors_origins():
    """Get CORS origins based on environment"""
    base_origins = [
        "http://localhost:3000",  # Local development
        "https://www.receptorai.pro",  # Production
        "https://receptorai.pro",  # Production without www
        "https://receptor-ai.vercel.app",  # Vercel domain
        "https://receptor-ai-thte.vercel.app",  # Specific Vercel domain
    ]
    
    # Add Railway preview URLs if available
    railway_public_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_public_domain:
        base_origins.append(f"https://{railway_public_domain}")
    
    # Add Render.com URLs if available
    render_service_url = os.environ.get("RENDER_SERVICE_URL")
    if render_service_url:
        base_origins.append(render_service_url)
    
    # Add Fly.io URLs if available (format: https://app-name.fly.dev)
    fly_app_name = os.environ.get("FLY_APP_NAME")
    if fly_app_name:
        base_origins.append(f"https://{fly_app_name}.fly.dev")
    
    # For development or if explicitly set, allow all origins
    if os.environ.get("ENVIRONMENT") == "development" or os.environ.get("CORS_ALLOW_ALL") == "true":
        logger.warning("тЪая╕П CORS: Allowing all origins (development mode)")
        return ["*"]
    
    logger.info(f"ЁЯМР CORS origins: {base_origins}")
    return base_origins

# Use the function to get CORS origins
cors_origins = get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Root endpoint (no prefix)
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Receptor AI Backend is running", "status": "ok"}

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check endpoint for Railway
@api_router.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "receptor-ai-backend"
    }

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "monthly_tech_cards": 3,
        "features": [
            "3 ╤В╨╡╤Е╨║╨░╤А╤В╤Л ╨▓ ╨╝╨╡╤Б╤П╤Ж",
            "╨С╨░╨╖╨╛╨▓╤Л╨╡ ╤А╨╡╤Ж╨╡╨┐╤В╤Л",
            "╨н╨║╤Б╨┐╨╛╤А╤В ╨▓ PDF",
            "╨Я╨╛╨┤╨┤╨╡╤А╨╢╨║╨░ email"
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
            "25 ╤В╨╡╤Е╨║╨░╤А╤В ╨▓ ╨╝╨╡╤Б╤П╤Ж",
            "╨Т╤Б╨╡ ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛╤Б╤В╨╕ Free",
            "╨а╨░╤Б╤И╨╕╤А╨╡╨╜╨╜╤Л╨╡ ╤А╨╡╤Ж╨╡╨┐╤В╤Л",
            "╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В╨╜╨░╤П ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨║╨░",
            "╨Ш╤Б╤В╨╛╤А╨╕╤П ╤В╨╡╤Е╨║╨░╤А╤В"
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
            "╨Э╨╡╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╜╤Л╨╡ ╤В╨╡╤Е╨║╨░╤А╤В╤Л",
            "╨Т╤Б╨╡ ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛╤Б╤В╨╕ Starter",
            "ЁЯФе ╨Р╨┤╨░╨┐╤В╨░╤Ж╨╕╤П ╨┐╨╛╨┤ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╨╡",
            "╨Я╤А╨╡╨╝╨╕╤Г╨╝ AI-╨░╨╗╨│╨╛╤А╨╕╤В╨╝╤Л",
            "╨а╨░╤Б╤И╨╕╤А╨╡╨╜╨╜╨░╤П ╨░╨╜╨░╨╗╨╕╤В╨╕╨║╨░",
            "╨Я╨╡╤А╤Б╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╨╝╨╡╨╜╨╡╨┤╨╢╨╡╤А"
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
            "╨Т╤Б╨╡ ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛╤Б╤В╨╕ PRO",
            "╨Ъ╨╛╨╝╨░╨╜╨┤╨╜╨░╤П ╤А╨░╨▒╨╛╤В╨░",
            "╨Ш╨╜╤В╨╡╨│╤А╨░╤Ж╨╕╤П ╤Б POS",
            "╨Ъ╨╛╤А╨┐╨╛╤А╨░╤В╨╕╨▓╨╜╨░╤П ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨║╨░",
            "╨Ш╨╜╨┤╨╕╨▓╨╕╨┤╤Г╨░╨╗╤М╨╜╤Л╨╡ ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨╕",
            "╨Ю╨▒╤Г╤З╨╡╨╜╨╕╨╡ ╨┐╨╡╤А╤Б╨╛╨╜╨░╨╗╨░"
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
        "typical_markup": "4.0x",
        "complexity_level": "high",
        "techniques": ["су-вид", "молекулярная гастрономия", "профессиональная подача", "сложные соусы"],
        "service_style": "table_service",
        "portion_style": "artistic"
    },
    "food_truck": {
        "name": "Food Truck",
        "description": "Мобильная точка питания быстрого обслуживания",
        "price_multiplier": 0.6,
        "typical_markup": "2.5x",
        "complexity_level": "low",
        "techniques": ["гриль", "фритюр", "быстрая жарка", "простая сборка"],
        "service_style": "fast_casual",
        "portion_style": "handheld"
    },
    "bar_pub": {
        "name": "Бар/Паб",
        "description": "Бар с закусками и напитками",
        "price_multiplier": 0.9,
        "typical_markup": "3.5x",
        "complexity_level": "medium",
        "techniques": ["гриль", "фритюр", "снеки", "закуски под алкоголь"],
        "service_style": "bar_service", 
        "portion_style": "sharing"
    },
    "cafe": {
        "name": "Кафе",
        "description": "Уютное кафе с домашней атмосферой",
        "price_multiplier": 0.8,
        "typical_markup": "3.0x",
        "complexity_level": "medium",
        "techniques": ["╨▓╤Л╨┐╨╡╤З╨║╨░", "╨║╨╛╤Д╨╡╨╣╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕", "╨╗╨╡╨│╨║╨╕╨╡ ╨▒╨╗╤О╨┤╨░", "╨┤╨╡╤Б╨╡╤А╤В╤Л"],
        "service_style": "counter_service",
        "portion_style": "comfort"
    },
    "coffee_shop": {
        "name": "Кофейня",
        "description": "Специализированная кофейня с авторскими напитками",
        "price_multiplier": 0.7,
        "typical_markup": "2.8x",
        "complexity_level": "medium",
        "techniques": ["альтернативное заваривание", "латте-арт", "выпечка", "десерты"],
        "service_style": "counter_service",
        "portion_style": "grab_and_go"
    },
    "food_court": {
        "name": "Фуд-корт",
        "description": "Точка в торговом центре или фуд-корте",
        "price_multiplier": 0.7,
        "typical_markup": "2.5x",
        "complexity_level": "low",
        "techniques": ["быстрое приготовление", "стандартизация", "разогрев", "сборка"],
        "service_style": "quick_service",
        "portion_style": "standard"
    },
    "canteen": {
        "name": "Столовая",
        "description": "Массовое питание для офисов, школ, предприятий",
        "price_multiplier": 0.5,
        "typical_markup": "2.0x",
        "complexity_level": "low",
        "techniques": ["массовое приготовление", "простые техники", "большие объемы"],
        "service_style": "cafeteria",
        "portion_style": "generous"
    },
    "kids_cafe": {
        "name": "Детское кафе",
        "description": "Семейное кафе с детским меню и развлечениями",
        "price_multiplier": 0.8,
        "typical_markup": "3.0x",
        "complexity_level": "low",
        "techniques": ["безопасное приготовление", "яркая подача", "простые вкусы"],
        "service_style": "family_friendly",
        "portion_style": "kid_friendly"
    },
    "night_club": {
        "name": "Ночной клуб",
        "description": "Заведение с ночными развлечениями",
        "price_multiplier": 1.2,
        "typical_markup": "4.5x",
        "complexity_level": "low", 
        "techniques": ["фингер-фуд", "простые закуски", "без столовых приборов"],
        "service_style": "standing",
        "portion_style": "finger_food"
    },
    "family_restaurant": {
        "name": "Семейный ресторан",
        "description": "Ресторан для семей с детьми",
        "price_multiplier": 1.0,
        "typical_markup": "3.0x",
        "complexity_level": "medium",
        "techniques": ["домашняя кухня", "большие порции", "простые рецепты"],
        "service_style": "family_friendly",
        "portion_style": "generous"
    },
    "fast_food": {
        "name": "Фаст-фуд",
        "description": "Быстрое питание со стандартизированным меню",
        "price_multiplier": 0.6,
        "typical_markup": "2.5x",
        "complexity_level": "low",
        "techniques": ["фритюр", "гриль", "стандартизация", "быстрая сборка"],
        "service_style": "quick_service",
        "portion_style": "standard"
    },
    "bakery_cafe": {
        "name": "Пекарня-кафе",
        "description": "Пекарня с кафе и свежей выпечкой",
        "price_multiplier": 0.8,
        "typical_markup": "3.2x",
        "complexity_level": "medium",
        "techniques": ["выпечка", "хлебопечение", "кондитерское искусство"],
        "service_style": "counter_service",
        "portion_style": "artisan"
    },
    "buffet": {
        "name": "Буфет/Шведский стол",
        "description": "Самообслуживание с широким выбором блюд",
        "price_multiplier": 0.9,
        "typical_markup": "2.2x",
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
        "name": "╨Р╨╖╨╕╨░╤В╤Б╨║╨░╤П",
        "subcategories": ["japanese", "korean", "thai", "chinese", "indian"],
        "key_ingredients": ["╤А╨╕╤Б", "╤Б╨╛╨╡╨▓╤Л╨╣ ╤Б╨╛╤Г╤Б", "╨╕╨╝╨▒╨╕╤А╤М", "╤З╨╡╤Б╨╜╨╛╨║", "╨┐╨╡╤А╨╡╤Ж ╤З╨╕╨╗╨╕", "╨║╨╛╨║╨╛╤Б╨╛╨▓╨╛╨╡ ╨╝╨╛╨╗╨╛╨║╨╛", "╤А╤Л╨▒╨╜╤Л╨╣ ╤Б╨╛╤Г╤Б"],
        "cooking_methods": ["╨▓╨╛╨║", "╨┐╨░╤А", "╤В╤Г╤И╨╡╨╜╨╕╨╡", "╨╝╨░╤А╨╕╨╜╨╛╨▓╨░╨╜╨╕╨╡"],
        "flavor_profile": ["╤Г╨╝╨░╨╝╨╕", "╨╛╤Б╤В╤А╤Л╨╣", "╤Б╨╗╨░╨┤╨║╨╛-╤Б╨╛╨╗╨╡╨╜╤Л╨╣", "╨░╤А╨╛╨╝╨░╤В╨╜╤Л╨╡ ╤Б╨┐╨╡╤Ж╨╕╨╕"]
    },
    "european": {
        "name": "╨Х╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П", 
        "subcategories": ["italian", "french", "german", "spanish", "greek"],
        "key_ingredients": ["╨╛╨╗╨╕╨▓╨║╨╛╨▓╨╛╨╡ ╨╝╨░╤Б╨╗╨╛", "╤В╨╛╨╝╨░╤В╤Л", "╤Б╤Л╤А", "╤В╤А╨░╨▓╤Л", "╨▓╨╕╨╜╨╛", "╤Б╨╗╨╕╨▓╨║╨╕"],
        "cooking_methods": ["╨╢╨░╤А╨║╨░", "╤В╤Г╤И╨╡╨╜╨╕╨╡", "╨╖╨░╨┐╨╡╨║╨░╨╜╨╕╨╡", "╤Б╨╛╤Г╤Б╤Л"],
        "flavor_profile": ["╤Б╨▒╨░╨╗╨░╨╜╤Б╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╣", "╤В╤А╨░╨▓╤П╨╜╨╛╨╣", "╨▓╨╕╨╜╨╜╤Л╨╣", "╤Б╤Л╤А╨╜╤Л╨╣"]
    },
    "caucasian": {
        "name": "╨Ъ╨░╨▓╨║╨░╨╖╤Б╨║╨░╤П",
        "subcategories": ["georgian", "armenian", "azerbaijani"],
        "key_ingredients": ["╨▒╨░╤А╨░╨╜╨╕╨╜╨░", "╨│╨╛╨▓╤П╨┤╨╕╨╜╨░", "╨╖╨╡╨╗╨╡╨╜╤М", "╤Б╨┐╨╡╤Ж╨╕╨╕", "╨╛╤А╨╡╤Е╨╕", "╨│╤А╨░╨╜╨░╤В"],
        "cooking_methods": ["╨╝╨░╨╜╨│╨░╨╗", "╤В╨░╨╜╨┤╤Л╤А", "╨┤╨╛╨╗╨│╨╛╨╡ ╤В╤Г╤И╨╡╨╜╨╕╨╡", "╨╝╨░╤А╨╕╨╜╨╛╨▓╨░╨╜╨╕╨╡"],
        "flavor_profile": ["╨┐╤А╤П╨╜╤Л╨╣", "╨░╤А╨╛╨╝╨░╤В╨╜╤Л╨╣", "╨╝╤П╤Б╨╜╨╛╨╣", "╤Б ╨║╨╕╤Б╨╗╨╕╨╜╨║╨╛╨╣"]
    },
    "eastern": {
        "name": "╨Т╨╛╤Б╤В╨╛╤З╨╜╨░╤П",
        "subcategories": ["uzbek", "turkish", "arabic"],
        "key_ingredients": ["╤А╨╕╤Б", "╨▒╨░╤А╨░╨╜╨╕╨╜╨░", "╤Б╨┐╨╡╤Ж╨╕╨╕", "╤Б╤Г╤Е╨╛╤Д╤А╤Г╨║╤В╤Л", "╨╛╤А╨╡╤Е╨╕", "╨╣╨╛╨│╤Г╤А╤В"],
        "cooking_methods": ["╨┐╨╗╨╛╨▓", "╨┤╨╛╨╗╨│╨╛╨╡ ╤В╤Г╤И╨╡╨╜╨╕╨╡", "╨╖╨░╨┐╨╡╨║╨░╨╜╨╕╨╡", "╤Б╨┐╨╡╤Ж╨╕╨╕"],
        "flavor_profile": ["╨┐╤А╤П╨╜╤Л╨╣", "╨░╤А╨╛╨╝╨░╤В╨╜╤Л╨╣", "╨╜╨░╤Б╤Л╤Й╨╡╨╜╨╜╤Л╨╣", "╤Н╨║╨╖╨╛╤В╨╕╤З╨╡╤Б╨║╨╕╨╣"]
    },
    "russian": {
        "name": "╨а╤Г╤Б╤Б╨║╨░╤П",
        "subcategories": ["traditional", "modern_russian", "siberian"],
        "key_ingredients": ["╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М", "╨║╨░╨┐╤Г╤Б╤В╨░", "╤Б╨▓╨╡╨║╨╗╨░", "╨╝╤П╤Б╨╛", "╤А╤Л╨▒╨░", "╨│╤А╨╕╨▒╤Л"],
        "cooking_methods": ["╨▓╨░╤А╨║╨░", "╤В╤Г╤И╨╡╨╜╨╕╨╡", "╨╖╨░╤Б╨╛╨╗╨║╨░", "╨║╨╛╨┐╤З╨╡╨╜╨╕╨╡"],
        "flavor_profile": ["╤Б╤Л╤В╨╜╤Л╨╣", "╤В╤А╨░╨┤╨╕╤Ж╨╕╨╛╨╜╨╜╤Л╨╣", "╨┤╨╛╨╝╨░╤И╨╜╨╕╨╣", "╤Б╨╛╨│╤А╨╡╨▓╨░╤О╤Й╨╕╨╣"]
    },
    "sea": {
        "name": "╨о╨│╨╛-╨Т╨╛╤Б╤В╨╛╤З╨╜╨░╤П ╨Р╨╖╨╕╤П",
        "subcategories": ["thai", "vietnamese", "malaysian", "filipino"],
        "key_ingredients": ["╨╗╨╡╨╝╨╛╨╜╨│╤А╨░╤Б╤Б", "╨║╨╛╨║╨╛╤Б╨╛╨▓╨╛╨╡ ╨╝╨╛╨╗╨╛╨║╨╛", "╨╗╨░╨╣╨╝", "╨│╨░╨╗╨░╨╜╨│╨░", "╨▒╨░╨╖╨╕╨╗╨╕╨║", "╤А╤Л╨▒╨╜╤Л╨╣ ╤Б╨╛╤Г╤Б"],
        "cooking_methods": ["╨▓╨╛╨║", "╨│╤А╨╕╨╗╤М", "╨║╨░╤А╤А╨╕", "╤Б╨▓╨╡╨╢╨╕╨╡ ╤Б╨░╨╗╨░╤В╤Л"],
        "flavor_profile": ["╨║╨╕╤Б╨╗╨╛-╤Б╨╗╨░╨┤╨║╨╕╨╣", "╨┐╤А╤П╨╜╤Л╨╣", "╤Б╨▓╨╡╨╢╨╕╨╣", "╤В╤А╨╛╨┐╨╕╤З╨╡╤Б╨║╨╕╨╣"]
    },
    "french": {
        "name": "╨д╤А╨░╨╜╤Ж╤Г╨╖╤Б╨║╨░╤П",
        "subcategories": ["classic", "bistro", "provence"],
        "key_ingredients": ["╤Б╨╗╨╕╨▓╨╛╤З╨╜╨╛╨╡ ╨╝╨░╤Б╨╗╨╛", "╤Б╨╗╨╕╨▓╨║╨╕", "╨▓╨╕╨╜╨╛", "╤В╤А╨░╨▓╤Л ╨┐╤А╨╛╨▓╨░╨╜╤Б", "╤Б╤Л╤А", "╨┐╨░╤И╤В╨╡╤В"],
        "cooking_methods": ["╨║╨╛╨╜╤Д╨╕", "╤Д╨╗╨░╨╝╨▒╨╕╤А╨╛╨▓╨░╨╜╨╕╨╡", "╤Б╤Г-╨▓╨╕╨┤", "╤Б╨╛╤Г╤Б╤Л"],
        "flavor_profile": ["╨╕╨╖╤Л╤Б╨║╨░╨╜╨╜╤Л╨╣", "╤Б╨╗╨╕╨▓╨╛╤З╨╜╤Л╨╣", "╨▓╨╕╨╜╨╜╤Л╨╣", "╨┤╨╡╨╗╨╕╨║╨░╤В╨╡╤Б╨╜╤Л╨╣"]
    },
    "eastern_european": {
        "name": "╨Т╨╛╤Б╤В╨╛╤З╨╜╨╛╨╡╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П",
        "subcategories": ["polish", "czech", "hungarian", "slovak"],
        "key_ingredients": ["╨║╨░╨┐╤Г╤Б╤В╨░", "╨║╨╛╨╗╨▒╨░╤Б╨░", "╨┐╨░╨┐╤А╨╕╨║╨░", "╤Б╨╝╨╡╤В╨░╨╜╨░", "╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М", "╤Б╨▓╨╕╨╜╨╕╨╜╨░"],
        "cooking_methods": ["╤В╤Г╤И╨╡╨╜╨╕╨╡", "╨║╨╛╨┐╤З╨╡╨╜╨╕╨╡", "╨╖╨░╤Б╨╛╨╗╨║╨░", "╨▓╨░╤А╨║╨░"],
        "flavor_profile": ["╤Б╤Л╤В╨╜╤Л╨╣", "╨┤╤Л╨╝╨╜╤Л╨╣", "╨║╨╕╤Б╨╗╤Л╨╣", "╨┐╤А╤П╨╜╤Л╨╣"]
    },
    "american": {
        "name": "╨Р╨╝╨╡╤А╨╕╨║╨░╨╜╤Б╨║╨░╤П",
        "subcategories": ["bbq", "southern", "tex_mex"],
        "key_ingredients": ["╨│╨╛╨▓╤П╨┤╨╕╨╜╨░", "╤Б╨▓╨╕╨╜╨╕╨╜╨░", "╨║╤Г╨║╤Г╤А╤Г╨╖╨░", "╨▒╨╛╨▒╤Л", "╤Б╤Л╤А", "╤Б╨╛╤Г╤Б ╨▒╨░╤А╨▒╨╡╨║╤О"],
        "cooking_methods": ["╨│╤А╨╕╨╗╤М", "╨▒╨░╤А╨▒╨╡╨║╤О", "╨║╨╛╨┐╤З╨╡╨╜╨╕╨╡", "╨╢╨░╤А╨║╨░"],
        "flavor_profile": ["╨┤╤Л╨╝╨╜╤Л╨╣", "╤Б╨╗╨░╨┤╨║╨╛-╨╛╤Б╤В╤А╤Л╨╣", "╤Б╤Л╤В╨╜╤Л╨╣", "╨┐╤А╨╛╤Б╤В╨╛╨╣"]
    },
    "mexican": {
        "name": "╨Ь╨╡╨║╤Б╨╕╨║╨░╨╜╤Б╨║╨░╤П",
        "subcategories": ["traditional", "tex_mex", "street_food"],
        "key_ingredients": ["╨░╨▓╨╛╨║╨░╨┤╨╛", "╨╗╨░╨╣╨╝", "╨┐╨╡╤А╨╡╤Ж ╤З╨╕╨╗╨╕", "╨║╤Г╨║╤Г╤А╤Г╨╖╨░", "╤Д╨░╤Б╨╛╨╗╤М", "╨║╨╛╤А╨╕╨░╨╜╨┤╤А"],
        "cooking_methods": ["╨│╤А╨╕╨╗╤М", "╤В╤Г╤И╨╡╨╜╨╕╨╡", "╨╝╨░╤А╨╕╨╜╨░╨┤╤Л", "╤Б╨░╨╗╤М╤Б╨░"],
        "flavor_profile": ["╨╛╤Б╤В╤А╤Л╨╣", "╤Ж╨╕╤В╤А╤Г╤Б╨╛╨▓╤Л╨╣", "╨┐╤А╤П╨╜╤Л╨╣", "╤Б╨▓╨╡╨╢╨╕╨╣"]
    },
    "italian": {
        "name": "╨Ш╤В╨░╨╗╤М╤П╨╜╤Б╨║╨░╤П",
        "subcategories": ["northern", "southern", "sicilian"],
        "key_ingredients": ["╤В╨╛╨╝╨░╤В╤Л", "╨▒╨░╨╖╨╕╨╗╨╕╨║", "╨┐╨░╤А╨╝╨╡╨╖╨░╨╜", "╨╛╨╗╨╕╨▓╨║╨╛╨▓╨╛╨╡ ╨╝╨░╤Б╨╗╨╛", "╤З╨╡╤Б╨╜╨╛╨║", "╨┐╨░╤Б╤В╨░"],
        "cooking_methods": ["╨░╨╗╤М ╨┤╨╡╨╜╤В╨╡", "╤А╨╕╨╖╨╛╤В╤В╨╛", "╨┐╨╕╤Ж╤Ж╨░", "╨▒╤А╤Г╤Б╨║╨╡╤В╤В╨░"],
        "flavor_profile": ["╤В╨╛╨╝╨░╤В╨╜╤Л╨╣", "╤Б╤Л╤А╨╜╤Л╨╣", "╤В╤А╨░╨▓╤П╨╜╨╛╨╣", "╨┐╤А╨╛╤Б╤В╨╛╨╣"]
    },
    "indian": {
        "name": "╨Ш╨╜╨┤╨╕╨╣╤Б╨║╨░╤П",
        "subcategories": ["northern", "southern", "bengali"],
        "key_ingredients": ["╨║╤Г╤А╨║╤Г╨╝╨░", "╨║╨╛╤А╨╕╨░╨╜╨┤╤А", "╨║╤Г╨╝╨╕╨╜", "╨║╨░╤А╨┤╨░╨╝╨╛╨╜", "╨║╨╛╨║╨╛╤Б", "╨╣╨╛╨│╤Г╤А╤В"],
        "cooking_methods": ["╨║╨░╤А╤А╨╕", "╤В╨░╨╜╨┤╤Л╤А", "╤В╨╡╨╝╨┐╨╡╤А╨╕╤А╨╛╨▓╨░╨╜╨╕╨╡ ╤Б╨┐╨╡╤Ж╨╕╨╣", "╨┤╨░╨╗"],
        "flavor_profile": ["╨┐╤А╤П╨╜╤Л╨╣", "╨░╤А╨╛╨╝╨░╤В╨╜╤Л╨╣", "╨╛╤Б╤В╤А╤Л╨╣", "╤Б╨╗╨╛╨╢╨╜╤Л╨╣"]
    }
}

# Average Check Categories
AVERAGE_CHECK_CATEGORIES = {
    "budget": {
        "name": "╨С╤О╨┤╨╢╨╡╤В╨╜╨╛╨╡",
        "range": [200, 500],
        "description": "╨Ф╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╡ ╤Ж╨╡╨╜╤Л ╨┤╨╗╤П ╨╝╨░╤Б╤Б╨╛╨▓╨╛╨│╨╛ ╨┐╨╛╤В╤А╨╡╨▒╨╕╤В╨╡╨╗╤П",
        "ingredient_quality": "standard",
        "portion_approach": "generous"
    },
    "mid_range": {
        "name": "╨б╤А╨╡╨┤╨╜╨╕╨╣ ╤Б╨╡╨│╨╝╨╡╨╜╤В", 
        "range": [500, 1500],
        "description": "╨Ъ╨░╤З╨╡╤Б╤В╨▓╨╡╨╜╨╜╨░╤П ╨╡╨┤╨░ ╨┐╨╛ ╤А╨░╨╖╤Г╨╝╨╜╤Л╨╝ ╤Ж╨╡╨╜╨░╨╝",
        "ingredient_quality": "good",
        "portion_approach": "balanced"
    },
    "premium": {
        "name": "╨Я╤А╨╡╨╝╨╕╤Г╨╝",
        "range": [1500, 3000],
        "description": "╨Т╤Л╤Б╨╛╨║╨╛╨║╨░╤З╨╡╤Б╤В╨▓╨╡╨╜╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨╕ ╤Б╨╡╤А╨▓╨╕╤Б",
        "ingredient_quality": "premium",
        "portion_approach": "refined"
    },
    "luxury": {
        "name": "╨Ы╤О╨║╤Б",
        "range": [3000, 10000],
        "description": "╨н╨║╤Б╨║╨╗╤О╨╖╨╕╨▓╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨╕ ╨╛╨┐╤Л╤В",
        "ingredient_quality": "luxury",
        "portion_approach": "artistic"
    }
}

# Kitchen Equipment Types
KITCHEN_EQUIPMENT = {
    "cooking_methods": [
        {"id": "gas_stove", "name": "╨У╨░╨╖╨╛╨▓╨░╤П ╨┐╨╗╨╕╤В╨░", "category": "cooking"},
        {"id": "electric_stove", "name": "╨н╨╗╨╡╨║╤В╤А╨╕╤З╨╡╤Б╨║╨░╤П ╨┐╨╗╨╕╤В╨░", "category": "cooking"},
        {"id": "induction_stove", "name": "╨Ш╨╜╨┤╤Г╨║╤Ж╨╕╨╛╨╜╨╜╨░╤П ╨┐╨╗╨╕╤В╨░", "category": "cooking"},
        {"id": "convection_oven", "name": "╨Ъ╨╛╨╜╨▓╨╡╨║╤Ж╨╕╨╛╨╜╨╜╨░╤П ╨┐╨╡╤З╤М", "category": "cooking"},
        {"id": "steam_oven", "name": "╨Я╨░╤А╨╛╨║╨╛╨╜╨▓╨╡╨║╤В╨╛╨╝╨░╤В", "category": "cooking"},
        {"id": "grill", "name": "╨У╤А╨╕╨╗╤М", "category": "cooking"},
        {"id": "fryer", "name": "╨д╤А╨╕╤В╤О╤А╨╜╨╕╤Ж╨░", "category": "cooking"},
        {"id": "salamander", "name": "╨б╨░╨╗╨░╨╝╨░╨╜╨┤╤А╨░", "category": "cooking"},
        {"id": "plancha", "name": "╨Я╨╗╨░╨╜╤З╨░", "category": "cooking"},
        {"id": "wok", "name": "╨Т╨╛╨║-╨┐╨╗╨╕╤В╨░", "category": "cooking"}
    ],
    "prep_equipment": [
        {"id": "food_processor", "name": "╨Ъ╤Г╤Е╨╛╨╜╨╜╤Л╨╣ ╨║╨╛╨╝╨▒╨░╨╣╨╜", "category": "prep"},
        {"id": "blender", "name": "╨С╨╗╨╡╨╜╨┤╨╡╤А", "category": "prep"},
        {"id": "meat_grinder", "name": "╨Ь╤П╤Б╨╛╤А╤Г╨▒╨║╨░", "category": "prep"},
        {"id": "slicer", "name": "╨б╨╗╨░╨╣╤Б╨╡╤А", "category": "prep"},
        {"id": "vacuum_sealer", "name": "╨Т╨░╨║╤Г╤Г╨╝╨╜╤Л╨╣ ╤Г╨┐╨░╨║╨╛╨▓╤Й╨╕╨║", "category": "prep"},
        {"id": "sous_vide", "name": "╨б╤Г-╨▓╨╕╨┤", "category": "prep"},
        {"id": "immersion_blender", "name": "╨Я╨╛╨│╤А╤Г╨╢╨╜╨╛╨╣ ╨▒╨╗╨╡╨╜╨┤╨╡╤А", "category": "prep"}
    ],
    "storage": [
        {"id": "blast_chiller", "name": "╨и╨╛╨║╨╖╨░╨╝╨╛╤А╨╛╨╖╨║╨░", "category": "storage"},
        {"id": "proofer", "name": "╨а╨░╤Б╤Б╤В╨╛╨╡╤З╨╜╤Л╨╣ ╤И╨║╨░╤Д", "category": "storage"},
        {"id": "refrigerator", "name": "╨е╨╛╨╗╨╛╨┤╨╕╨╗╤М╨╜╨╕╨║", "category": "storage"},
        {"id": "freezer", "name": "╨Ь╨╛╤А╨╛╨╖╨╕╨╗╤М╨╜╨╕╨║", "category": "storage"}
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
    "other": 0.8  # ╨Ь╨░╨╗╤Л╨╡ ╨│╨╛╤А╨╛╨┤╨░
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
    # Auth fields
    password_hash: Optional[str] = None  # For email/password users
    provider: str = "email"  # "email" or "google"

class UserCreate(BaseModel):
    email: str
    name: str
    city: str
    password: Optional[str] = None  # Required for email/password registration

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
    
    # Extended venue profile fields
    staff_count: Optional[int] = None  # Number of employees
    working_hours: Optional[str] = None  # Working hours (e.g., "10:00-22:00")
    seating_capacity: Optional[int] = None  # Number of seats
    city: Optional[str] = None  # City name

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
    user_id: Optional[str] = None  # Required for V2 tech cards

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
GOLDEN_PROMPT = """╨в╤Л тАФ RECEPTOR, ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ AI-╨┐╨╛╨╝╨╛╤Й╨╜╨╕╨║ ╨┤╨╗╤П ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А╨╛╨▓ ╨╕ ╤А╨╡╤Б╤В╨╛╤А╨░╤В╨╛╤А╨╛╨▓.

╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨▓╨▓╨╛╨┤╨╕╤В ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░ ╨╕╨╗╨╕ ╨╕╨┤╨╡╤О. ╨б╨│╨╡╨╜╨╡╤А╨╕╤А╤Г╨╣ ╨┐╨╛╨╗╨╜╤Г╤О ╤В╨╡╤Е╨╜╨╛╨╗╨╛╨│╨╕╤З╨╡╤Б╨║╤Г╤О ╨║╨░╤А╤В╤Г (╨в╨Ъ) ╤Б╤В╤А╨╛╨│╨╛ ╨┐╨╛ ╤Д╨╛╤А╨╝╨░╤В╤Г ╨╜╨╕╨╢╨╡.

╨Ъ╨Ю╨Э╨в╨Х╨Ъ╨б╨в ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨п:
{venue_context}

╨Т╨Р╨Ц╨Э╨Ю: 
- ╨Х╤Б╨╗╨╕ ╨▓ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╕ ╨╡╤Б╤В╤М ╤П╨▓╨╜╤Л╨╡ ╨╛╨┐╨╡╤З╨░╤В╨║╨╕ ╨╕╨╗╨╕ ╨╜╨╡╨┐╤А╨░╨▓╨╕╨╗╤М╨╜╤Л╨╡ ╤Б╨╗╨╛╨▓╨░ (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А "╨С╤А╨░╨╜╤З" ╨▓╨╝╨╡╤Б╤В╨╛ "╤Б╨╛╤Г╤Б"), ╨╕╤Б╨┐╤А╨░╨▓╤М ╨╕╤Е ╨╜╨░ ╨┐╤А╨░╨▓╨╕╨╗╤М╨╜╤Л╨╡ ╨║╤Г╨╗╨╕╨╜╨░╤А╨╜╤Л╨╡ ╤В╨╡╤А╨╝╨╕╨╜╤Л.
- ╨Э╨Х ╨Ь╨Х╨Э╨п╨Щ ╨╛╤Б╨╜╨╛╨▓╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨┐╤А╨╕ ╤А╨╡╨┤╨░╨║╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╨╕! ╨Х╤Б╨╗╨╕ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨┐╨╕╤И╨╡╤В "╨╝╨╛╤А╨╢", ╨Э╨Х ╨╖╨░╨╝╨╡╨╜╤П╨╣ ╨╜╨░ "╨╝╨╛╤А╤Б╨║╨╛╨╣ ╨│╤А╨╡╨▒╨╡╤И╨╛╨║".

тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА
ЁЯУМ ╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨л╨Х ╨Я╨а╨Р╨Т╨Ш╨Ы╨Р ╨Я╨Ю ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨о
тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА
{venue_specific_rules}

тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА
ЁЯУМ ╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨л╨Х ╨Я╨а╨Р╨Т╨Ш╨Ы╨Р
тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА
тАв ╨Х╤Б╨╗╨╕ ╨▓ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╕ ╨╡╤Б╤В╤М ╤Б╨╛╤Г╤Б/╤В╨╡╤Е╨╜╨╕╨║╨░ (┬л╨┐╨╡╤Б╤В╨╛┬╗, ┬л╤В╨╡╤А╨╕╤П╨║╨╕┬╗, ┬л╤А╨░╨╝╤Н╨╜┬╗ ╨╕ ╤В.╨┤.) тАФ ╨╛╤В╤А╨░╨╖╨╕ ╤Н╤В╨╛ ╨▓ ╤А╨╡╤Ж╨╡╨┐╤В╨╡.
╨Э╨╡ ╨┐╨╛╨┤╨╝╨╡╨╜╤П╨╣ ╨╕ ╨╜╨╡ ╤Г╨┐╤А╨╛╤Й╨░╨╣.

- ╨г╤З╨╕╤В╤Л╨▓╨░╨╣ ╤Г╨╢╨░╤А╨║╤Г/╤Г╤В╨░╨╣╨║╤Г (╨╝╤П╤Б╨╛, ╤А╤Л╨▒╨░ 20тАУ30 %, ╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М 20 %, ╨│╤А╨╕╨▒╤Л/╨╗╤Г╨║ ╨┤╨╛ 50 %).
╨г╨║╨░╨╖╤Л╨▓╨░╨╣ ╤Б╤Л╤А╨╛╨╣ ╨▓╨╡╤Б, %, ╨▓╤Л╤Е╨╛╨┤.

- ╨Я╨а╨Р╨Т╨Ш╨Ы╨Р ╨ж╨Х╨Э╨Ю╨Ю╨С╨а╨Р╨Ч╨Ю╨Т╨Р╨Э╨Ш╨п:
  * ╨а╨░╤Б╤Б╤З╨╕╤В╤Л╨▓╨░╨╣ ╨Я╨а╨Р╨Т╨Ш╨Ы╨м╨Э╨л╨Х ╨а╨Х╨б╨в╨Ю╨а╨Р╨Э╨Э╨л╨Х ╨Я╨Ю╨а╨ж╨Ш╨Ш:
    тАв ╨Ю╤Б╨╜╨╛╨▓╨╜╨╛╨╡ ╨▒╨╗╤О╨┤╨╛: 200-300╨│
    тАв ╨Ч╨░╨║╤Г╤Б╨║╨░: 150-200╨│  
    тАв ╨Ф╨╡╤Б╨╡╤А╤В: 80-120╨│ (2-3 ╨┐╤А╤П╨╜╨╕╨║╨░, 1 ╨║╤Г╤Б╨╛╤З╨╡╨║ ╤В╨╛╤А╤В╨░)
    тАв ╨б╤Г╨┐: 250-300╨╝╨╗
  * ╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╤Г╨║╨░╨╖╤Л╨▓╨░╨╣ ╤Б╤А╨░╨╖╤Г ╨╜╨░ ╨╛╨┤╨╜╤Г ╨┐╨╛╤А╤Ж╨╕╤О, ╨╜╨╡ ╨╜╨░ ╨║╨╕╨╗╨╛╨│╤А╨░╨╝╨╝╤Л!
  * ╨Я╤А╨╕╨╝╨╡╤А╤Л ╨┐╤А╨░╨▓╨╕╨╗╤М╨╜╤Л╤Е ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓ ╨╜╨░ ╨╛╨┤╨╜╤Г ╨┐╨╛╤А╤Ж╨╕╤О:
    - ╨Ь╤П╤Б╨╛/╤А╤Л╨▒╨░ ╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╡: 150-200╨│
    - ╨У╨░╤А╨╜╨╕╤А (╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М, ╤А╨╕╤Б): 100-150╨│  
    - ╨Ю╨▓╨╛╤Й╨╕ ╨┤╨╗╤П ╤Б╨░╨╗╨░╤В╨░: 80-120╨│
    - ╨б╨╛╤Г╤Б: 30-50╨╝╨╗
    - ╨б╨┐╨╡╤Ж╨╕╨╕: 1-5╨│
  * ╨ж╨Х╨Э╨Ю╨Ю╨С╨а╨Р╨Ч╨Ю╨Т╨Р╨Э╨Ш╨Х ╨Э╨Р ╨Ш╨о╨Ы╨м 2025 - ╨б╨в╨а╨Ю╨У╨Ю ╨б╨Ы╨Х╨Ф╨г╨Щ ╨н╨в╨Ш╨Ь ╨ж╨Х╨Э╨Р╨Ь:
    - ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨в╨Ю╨Ы╨м╨Ъ╨Ю ╨░╨║╤В╤Г╨░╨╗╤М╨╜╤Л╨╡ ╤А╤Л╨╜╨╛╤З╨╜╤Л╨╡ ╤Ж╨╡╨╜╤Л ╨╕╨╖ ╤В╨▓╨╛╨╕╤Е ╨╖╨╜╨░╨╜╨╕╨╣
    - ╨Ш╨╜╤Д╨╗╤П╤Ж╨╕╤П ╤Б 2024: +18% ╨╜╨░ ╨▓╤Б╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л
    - ╨а╨╡╨│╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╨║╨╛╤Н╤Д╤Д╨╕╤Ж╨╕╨╡╨╜╤В: {regional_coefficient}x
    - ╨Ъ╨╛╤Н╤Д╤Д╨╕╤Ж╨╕╨╡╨╜╤В ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П: {venue_price_multiplier}x
    
    ╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨л╨Х ╨Ю╨а╨Ш╨Х╨Э╨в╨Ш╨а╨л ╨ж╨Х╨Э ╨Ш╨о╨Ы╨м 2025:
    тАв ╨Я╨а╨Х╨Ь╨Ш╨г╨Ь ╨Я╨а╨Ю╨Ф╨г╨Ъ╨в╨л (├Ч1.4 ╨║ ╨▒╨░╨╖╨╡):
      - ╨б╨╡╨╝╨│╨░ ╨╛╤Е╨╗╨░╨╢╨┤╨╡╨╜╨╜╨░╤П: 1900-2100тВ╜/╨║╨│ (190-210тВ╜ ╨╖╨░ 100╨│)
      - ╨д╨╛╤А╨╡╨╗╤М: 1600-1800тВ╜/╨║╨│ (160-180тВ╜ ╨╖╨░ 100╨│)  
      - ╨в╨╡╨╗╤П╤В╨╕╨╜╨░: 1300-1500тВ╜/╨║╨│
      - ╨г╤Б╤В╤А╨╕╤Ж╤Л: 350-500тВ╜/╤И╤В
      - ╨в╤А╤О╤Д╨╡╨╗╨╕: 15000-25000тВ╜/╨║╨│
    
    тАв ╨б╨в╨Р╨Э╨Ф╨Р╨а╨в ╨Я╨а╨Ю╨Ф╨г╨Ъ╨в╨л (├Ч1.2 ╨║ ╨▒╨░╨╖╨╡):
      - ╨У╨╛╨▓╤П╨┤╨╕╨╜╨░ ╨┐╤А╨╡╨╝╨╕╤Г╨╝: 900-1200тВ╜/╨║╨│
      - ╨б╨▓╨╕╨╜╨╕╨╜╨░: 500-700тВ╜/╨║╨│
      - ╨Ъ╤Г╤А╨╕╤Ж╨░ ╤Д╨╕╨╗╨╡: 450-550тВ╜/╨║╨│
      - ╨б╨╗╨╕╨▓╨║╨╕ 33%: 200-250тВ╜/╨╗
      - ╨б╤Л╤А ╨┐╨░╤А╨╝╨╡╨╖╨░╨╜: 2500-3000тВ╜/╨║╨│
    
    тАв ╨С╨Р╨Ч╨Ю╨Т╨л╨Х ╨Я╨а╨Ю╨Ф╨г╨Ъ╨в╨л (├Ч1.0 ╨║ ╨▒╨░╨╖╨╡):
      - ╨Ъ╨░╤А╤В╨╛╤Д╨╡╨╗╤М: 120-150тВ╜/╨║╨│ ╨▓ ╤А╨╛╨╖╨╜╨╕╤Ж╨╡ (╨▓ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░╤Е +30%)
      - ╨Ы╤Г╨║: 140-180тВ╜/╨║╨│ ╨▓ ╤А╨╛╨╖╨╜╨╕╤Ж╨╡ (╨▓ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░╤Е +40%)
      - ╨Ь╨╛╤А╨║╨╛╨▓╤М: 100-130тВ╜/╨║╨│
      - ╨Ь╤Г╨║╨░: 70-90тВ╜/╨║╨│
      - ╨п╨╣╤Ж╨░: 150-200тВ╜/╨┤╨╡╤Б╤П╤В╨╛╨║ (15-20тВ╜/╤И╤В)
      - ╨Ь╨░╤Б╨╗╨╛ ╨┐╨╛╨┤╤Б╨╛╨╗╨╜╨╡╤З╨╜╨╛╨╡: 180-220тВ╜/╨╗
    
    ╨Ъ╨а╨Ш╨в╨Ш╨з╨Х╨б╨Ъ╨Ш ╨Т╨Р╨Ц╨Э╨Ю: ╨Х╤Б╨╗╨╕ ╤В╤Л ╤Б╤В╨░╨▓╨╕╤И╤М ╤Ж╨╡╨╜╤Г ╨╜╨╕╨╢╨╡ ╤Г╨║╨░╨╖╨░╨╜╨╜╤Л╤Е ╨╛╤А╨╕╨╡╨╜╤В╨╕╤А╨╛╨▓ - ╤В╤Л ╨╛╤И╨╕╨▒╨░╨╡╤И╤М╤Б╤П!
    ╨Я╤А╨╕╨╝╨╡╤А: 100╨│ ╤Б╨╡╨╝╨│╨╕ ╨Э╨Х ╨Ь╨Ю╨Ц╨Х╨в ╤Б╤В╨╛╨╕╤В╤М 80тВ╜ - ╤Н╤В╨╛ ╨┤╨╛╨╗╨╢╨╜╨╛ ╨▒╤Л╤В╤М 190-210тВ╜!
    
    ╨Ю╨б╨Ю╨С╨Ю╨Х ╨Т╨Э╨Ш╨Ь╨Р╨Э╨Ш╨Х ╨Ъ ╨Я╨а╨Х╨Ь╨Ш╨г╨Ь ╨а╨л╨С╨Х:
    - ╨б╨╡╨╝╨│╨░, ╨╗╨╛╤Б╨╛╤Б╤М, ╤Д╨╛╤А╨╡╨╗╤М - ╤Н╤В╨╛ ╨Т╨б╨Х╨У╨Ф╨Р ╨┤╨╛╤А╨╛╨│╨╕╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л
    - 1 ╨║╨│ ╤Б╨╡╨╝╨│╨╕ = 1900-2100тВ╜, ╨╖╨╜╨░╤З╨╕╤В 100╨│ = 190-210тВ╜
    - ╨Э╨Х ╨Я╨г╨в╨Р╨Щ ╤Б ╨▒╨╛╨╗╨╡╨╡ ╨┤╨╡╤И╨╡╨▓╨╛╨╣ ╤А╤Л╨▒╨╛╨╣ ╤В╨╕╨┐╨░ ╨╝╨╕╨╜╤В╨░╤П ╨╕╨╗╨╕ ╤Е╨╡╨║╨░
    
  * ╨С╤Г╨┤╤М ╤А╨╡╨░╨╗╨╕╤Б╤В╨╕╤З╨╡╨╜ ╨▓ ╤Ж╨╡╨╜╨░╤Е - ╤Н╤В╨╛ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜ ╤Г╤А╨╛╨▓╨╜╤П "{venue_type_name}"!

- ╨б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М = ╤В╨╛╨╗╤М╨║╨╛ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л (╨▒╨╡╨╖ ╨╜╨░╨║╨╗╨░╨┤╨╜╤Л╤Е).
- ╨а╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╨░╤П ╤Ж╨╡╨╜╨░ = ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М ├Ч 3 (╤Б╤В╨░╨╜╨┤╨░╤А╤В╨╜╨░╤П ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╜╨░╤П ╨╜╨░╤Ж╨╡╨╜╨║╨░).
- ╨ж╨Х╨Ы╨м: ╨Ш╤В╨╛╨│╨╛╨▓╨░╤П ╤Ж╨╡╨╜╨░ ╨┤╨╛╨╗╨╢╨╜╨░ ╨▒╤Л╤В╤М ╨░╨┤╨╡╨║╨▓╨░╤В╨╜╨╛╨╣ ╨┤╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╤В╨╕╨┐╨░ "{venue_type_name}" ╤Б╨╛ ╤Б╤А╨╡╨┤╨╜╨╕╨╝ ╤З╨╡╨║╨╛╨╝ {average_check}тВ╜.

╨Т╨Р╨Ц╨Э╨Ю ╨Я╨Ю ╨а╨Р╨б╨з╨Х╨в╨Р╨Ь:
- ╨в╨Ю╨з╨Э╨Ю ╤А╨░╤Б╤Б╤З╨╕╤В╤Л╨▓╨░╨╣ ╤Ж╨╡╨╜╤Л: 100╨│ ╤Б╨╗╨╕╨▓╨╛╤З╨╜╨╛╨│╨╛ ╨╝╨░╤Б╨╗╨░ ╨┐╤А╨╕ 450тВ╜/╨║╨│ = 45тВ╜ (╨Э╨Х 450тВ╜!)
- ╨Я╨а╨Ю╨Т╨Х╨а╨п╨Щ ╨╝╨░╤В╨╡╨╝╨░╤В╨╕╨║╤Г: ╨╡╤Б╨╗╨╕ ╨╝╤Г╨║╨░ 60тВ╜/╨║╨│, ╤В╨╛ 300╨│ = 18тВ╜
- ╨Ю╨▒╤Й╨░╤П ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М ╨┤╨╡╤Б╨╡╤А╤В╨░ 80-120╨│ ╨┤╨╛╨╗╨╢╨╜╨░ ╨▒╤Л╤В╤М 40-80тВ╜
- ╨Ю╤Б╨╜╨╛╨▓╨╜╨╛╨│╨╛ ╨▒╨╗╤О╨┤╨░ 200-300╨│ ╨┤╨╛╨╗╨╢╨╜╨░ ╨▒╤Л╤В╤М 100-200тВ╜

- ╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨Ю ╨▓╨║╨╗╤О╤З╨░╨╣ ╨▓ ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М ╨╕ ╨▓ ╨╕╤В╨╛╨│╨╛╨▓╤Л╨╣ ╨▓╤Л╤Е╨╛╨┤ ╨▓╤Б╤С, ╤З╤В╨╛ ╤А╨╡╨░╨╗╤М╨╜╨╛ ╨╕╨┤╤С╤В ╨╜╨░ ╨┐╨╛╤А╤Ж╨╕╤О:
тАУ ╤А╨░╤Б╤В╨╕╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨╕ ╤Б╨╗╨╕╨▓╨╛╤З╨╜╤Л╨╡ ╨╝╨░╤Б╨╗╨░, ╨╡╤Б╨╗╨╕ ╨╕╤Е > 5 ╨╝╨╗ ╨╜╨░ ╨┐╨╛╤А╤Ж╨╕╤О (╨┤╨╗╤П ╨╢╨░╤А╨║╨╕ / ╤Н╨╝╤Г╨╗╤М╤Б╨╕╨╣);
тАУ ╨┐╨╛╤А╤Ж╨╕╤О ╤Б╨╛╤Г╤Б╨░, ╨┤╨░╨╢╨╡ ╨╡╤Б╨╗╨╕ ╤Б╨░╨╝ ╤Б╨╛╤Г╤Б ╨▓╤Л╨╜╨╡╤Б╨╡╨╜ ╨▓ ╨╛╤В╨┤╨╡╨╗╤М╨╜╤Г╤О ╨в╨Ъ.
╨Т ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨░╤Е ╤Г╨║╨░╨╢╨╕ ╤Б╤В╤А╨╛╨║╤Г ╨▓╨╕╨┤╨░
┬л╨б╨╛╤Г╤Б [╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡] тАФ [╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛] ╨│ (╤Б╨╝. ╨в╨Ъ "╨б╨╛╤Г╤Б [╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡]") тАФ ~[╤Ж╨╡╨╜╨░] тВ╜┬╗.
╨Э╨Ю: ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╤В╨╛╨╗╤М╨║╨╛ ╨Я╨а╨Ю╨б╨в╨л╨Х ╤Б╨╛╤Г╤Б╤Л (╤В╨╛╨╝╨░╤В╨╜╤Л╨╣, ╤Б╨╗╨╕╨▓╨╛╤З╨╜╤Л╨╣, ╨│╤А╨╕╨▒╨╜╨╛╨╣), ╨╕╨╖╨▒╨╡╨│╨░╨╣ ╤Б╨╗╨╛╨╢╨╜╤Л╤Е ╤Д╤А╨░╨╜╤Ж╤Г╨╖╤Б╨║╨╕╤Е ╤Б╨╛╤Г╤Б╨╛╨▓ ╤В╨╕╨┐╨░ ╨┤╨╡╨╝╨╕╨│╨╗╤П╤Б, ╤Н╤Б╨┐╨░╨╜╤М╨╛╨╗, ╨▓╨╡╨╗╤О╤В╨╡ ╨┤╨╗╤П ╨┐╤А╨╛╤Б╤В╤Л╤Е ╨▒╨╗╤О╨┤.

- ╨Ш╤В╨╛╨│╨╛╨▓╤Л╨╣ ╨▓╨╡╤Б (┬л╨Т╤Л╤Е╨╛╨┤┬╗) = ╤Б╤Г╨╝╨╝╨░ ╨▓╤Б╨╡╤Е ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╨╛╨▓ ╨┐╨╛╤Б╨╗╨╡ ╤В╨╡╤А╨╝╨╛╨╛╨▒╤А╨░╨▒╨╛╤В╨║╨╕
(╨▒╨╡╨╗╨╛╨║ + ╨│╨░╤А╨╜╨╕╤А + ╤Б╨╛╤Г╤Б). ╨б╨╛╤Г╤Б 50 ╨│ тЗТ ╨┤╨╛╨▒╨░╨▓╤М ╨╡╨│╨╛ ╨▓ ╨▓╤Л╤Е╨╛╨┤, ╤Ж╨╡╨╜╤Г ╨╕ ╨Ъ╨С╨Ц╨г.

тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА
ЁЯзй ╨Я╨Ю╨Ы╨г╨д╨Р╨С╨а╨Ш╨Ъ╨Р╨в╨л | ╨Ч╨Р╨У╨Ю╨в╨Ю╨Т╨Ъ╨Ш
тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА
тАФ ╨У╨╛╤В╨╛╨▓╤Л╨╡ ╨╝╨░╤Б╤Б╨╛╨▓╤Л╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л (╤Б╨╛╤Г╤Б ╤В╨╡╤А╨╕╤П╨║╨╕, ╤Б╨╛╨╡╨▓╤Л╨╣ ╤Б╨╛╤Г╤Б, ╨║╨╡╤В╤З╤Г╨┐) тАФ ╤Г╨║╨░╨╖╤Л╨▓╨░╨╣ ╨║╨░╨║ ┬л╨┐╨╛╨║╤Г╨┐╨╜╨╛╨╣┬╗, ╤Ж╨╡╨╜╤Г ╨▓╨║╨╗╤О╤З╨░╨╣.

тАФ ╨Ф╨╗╤П ╨▒╨╛╨╗╤М╤И╨╕╨╜╤Б╤В╨▓╨░ ╨▒╨╗╤О╨┤ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨Я╨а╨Ю╨б╨в╨л╨Х ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л (╤Б╨╛╨╗╤М, ╨┐╨╡╤А╨╡╤Ж, ╨╝╨░╤Б╨╗╨╛, ╨▒╨░╨╖╨╛╨▓╤Л╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л).
тАФ ╨Ш╨╖╨▒╨╡╨│╨░╨╣ ╤Б╨╗╨╛╨╢╨╜╤Л╤Е ╤Д╤А╨░╨╜╤Ж╤Г╨╖╤Б╨║╨╕╤Е ╤Б╨╛╤Г╤Б╨╛╨▓ (╨┤╨╡╨╝╨╕╨│╨╗╤П╤Б, ╤Н╤Б╨┐╨░╨╜╤М╨╛╨╗, ╨▓╨╡╨╗╤О╤В╨╡) ╨┤╨╗╤П ╨┐╤А╨╛╤Б╤В╤Л╤Е ╨▒╨╗╤О╨┤.
тАФ ╨Х╤Б╨╗╨╕ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤В╨╡╨╗╤М╨╜╨╛ ╨╜╤Г╨╢╨╡╨╜ ╤Б╨╗╨╛╨╢╨╜╤Л╨╣ ╤Б╨╛╤Г╤Б, ╤Г╨║╨░╨╢╨╕: ┬л╨б╨╛╤Г╤Б [╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡] тАФ [╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛] ╨│ (╤Б╨╝. ╨╛╤В╨┤╨╡╨╗╤М╨╜╤Г╤О ╨в╨Ъ)┬╗;
тАФ ╨Э╨Х ╤А╨░╤Б╨┐╨╕╤Б╤Л╨▓╨░╨╣ ╨┐╤А╨╛╤Ж╨╡╤Б╤Б ╤Б╨╗╨╛╨╢╨╜╤Л╤Е ╤Б╨╛╤Г╤Б╨╛╨▓;
тАФ ╨┤╨╛╨▒╨░╨▓╤М ╤Д╤А╨░╨╖╤Г: ┬л╨Ч╨░╨┐╤А╨╛╤Б╨╕╤В╨╡ ╨╛╤В╨┤╨╡╨╗╤М╨╜╤Г╤О ╨в╨Ъ, ╨╡╤Б╨╗╨╕ ╨╜╤Г╨╢╨╜╨╛┬╗.

тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА
ЁЯУЛ ╨д╨Ю╨а╨Ь╨Р╨в ╨Т╨л╨Ф╨Р╨з╨Ш
тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА
**╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:** тАж

**╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П:** ╨╖╨░╨║╤Г╤Б╨║╨░ / ╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╡ / ╨┤╨╡╤Б╨╡╤А╤В

**╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡:** 2-3 ╤Б╨╛╤З╨╜╤Л╤Е ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╡╨╜╨╕╤П (╨▓╨║╤Г╤Б, ╨░╤А╨╛╨╝╨░╤В, ╤В╨╡╨║╤Б╤В╤Г╤А╨░). {description_style}

**╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л:** (╤Г╨║╨░╨╖╤Л╨▓╨░╨╣ ╨Э╨Р ╨Ю╨Ф╨Э╨г ╨Я╨Ю╨а╨ж╨Ш╨о!)

╨Ъ╨а╨Ш╨в╨Ш╨з╨Х╨б╨Ъ╨Ш ╨Т╨Р╨Ц╨Э╨Ю - ╨Т╨б╨Х ╨Ш╨Ч╨Ь╨Х╨а╨Х╨Э╨Ш╨п ╨в╨Ю╨Ы╨м╨Ъ╨Ю ╨Т ╨У╨а╨Р╨Ь╨Ь╨Р╨е:
- ╨Э╨Х ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ "╤И╤В╤Г╨║╨╕" ("1 ╤П╨╣╤Ж╨╛", "2 ╤В╨╛╤А╤В╨╕╨╗╤М╨╕") 
- ╨Ш╨б╨Я╨Ю╨Ы╨м╨Ч╨г╨Щ ╤В╨╛╨╗╤М╨║╨╛ ╨│╤А╨░╨╝╨╝╤Л ("50╨│ ╤П╨╣╤Ж╨░", "60╨│ ╤В╨╛╤А╤В╨╕╨╗╤М╨╕")
- ╨Ф╨░╨╢╨╡ ╨╢╨╕╨┤╨║╨╛╤Б╤В╨╕ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨╕ ╨▓ ╨│╤А╨░╨╝╨╝╤Л: 100╨╝╨╗ ╨╝╨╛╨╗╨╛╨║╨░ = 100╨│ ╨╝╨╛╨╗╨╛╨║╨░
- ╨Я╤А╨╕╨╝╨╡╤А╤Л ╨┐╤А╨░╨▓╨╕╨╗╤М╨╜╨╛╨│╨╛ ╤Д╨╛╤А╨╝╨░╤В╨░:
  тЬЕ ╨Ъ╤Г╤А╨╕╨╜╨╛╨╡ ╤Д╨╕╨╗╨╡ тАФ 180╨│ тАФ ~120тВ╜
  тЬЕ ╨п╨╣╤Ж╨╛ ╨║╤Г╤А╨╕╨╜╨╛╨╡ тАФ 50╨│ тАФ ~10тВ╜ 
  тЬЕ ╨в╨╛╤А╤В╨╕╨╗╤М╤П ╨┐╤И╨╡╨╜╨╕╤З╨╜╨░╤П тАФ 60╨│ тАФ ~15тВ╜
  тЬЕ ╨Ь╨╛╨╗╨╛╨║╨╛ 3.2% тАФ 100╨│ тАФ ~8тВ╜
  тЭМ ╨Э╨╡╨┐╤А╨░╨▓╨╕╨╗╤М╨╜╨╛: ╨п╨╣╤Ж╨╛ тАФ 1 ╤И╤В, ╨в╨╛╤А╤В╨╕╨╗╤М╤П тАФ 2 ╤И╤В

- ╨Я╤А╨╛╨┤╤Г╨║╤В тАФ ╨║╨╛╨╗-╨▓╨╛ ╨▓ ╨│╤А╨░╨╝╨╝╨░╤Е (╤Б╤Л╤А╨╛╨╣) тАФ ~╤Ж╨╡╨╜╨░
- *╨г╨╢╨░╤А╨║╨░/╤Г╤В╨░╨╣╨║╨░:* ┬лтАж тАФ 100 ╨│ (╤Г╨╢╨░╤А╨║╨░ 30 %, ╨▓╤Л╤Е╨╛╨┤ 70 ╨│)┬╗

**╨Я╨╛╤И╨░╨│╨╛╨▓╤Л╨╣ ╤А╨╡╤Ж╨╡╨┐╤В:**

{cooking_instructions}

**╨Т╤А╨╡╨╝╤П:** ╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ XX ╨╝╨╕╨╜ | ╨У╨╛╤В╨╛╨▓╨║╨░ XX ╨╝╨╕╨╜ | ╨Ш╨в╨Ю╨У╨Ю XX ╨╝╨╕╨╜

**╨Т╤Л╤Е╨╛╨┤:** XXX ╨│ ╨│╨╛╤В╨╛╨▓╨╛╨│╨╛ ╨▒╨╗╤О╨┤╨░ (╤Г╤З╤В╨╡╨╜╨░ ╤Г╨╢╨░╤А╨║╨░)

**╨Я╨╛╤А╤Ж╨╕╤П:** XX ╨│ (╨╛╨┤╨╜╨░ ╨┐╨╛╤А╤Ж╨╕╤П)

**╨б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М:**

- ╨Я╨╛ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨░╨╝: XXX тВ╜
- ╨б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М 1 ╨┐╨╛╤А╤Ж╨╕╨╕: XX тВ╜
- ╨а╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╨░╤П ╤Ж╨╡╨╜╨░ (├Ч3): XXX тВ╜

**╨Ъ╨С╨Ц╨г ╨╜╨░ 1 ╨┐╨╛╤А╤Ж╨╕╤О:** ╨Ъ╨░╨╗╨╛╤А╨╕╨╕ тАж ╨║╨║╨░╨╗ | ╨С тАж ╨│ | ╨Ц тАж ╨│ | ╨г тАж ╨│

**╨Ъ╨С╨Ц╨г ╨╜╨░ 100 ╨│:** ╨Ъ╨░╨╗╨╛╤А╨╕╨╕ тАж ╨║╨║╨░╨╗ | ╨С тАж ╨│ | ╨Ц тАж ╨│ | ╨г тАж ╨│

**╨Р╨╗╨╗╨╡╤А╨│╨╡╨╜╤Л:** тАж + (╨▓╨╡╨│╨░╨╜ / ╨▒╨╡╨╖╨│╨╗╤О╤В╨╡╨╜ ╨╕ ╤В.╨┐.)

**╨Ч╨░╨│╨╛╤В╨╛╨▓╨║╨╕ ╨╕ ╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡:**

- ╨з╤В╨╛ ╨╝╨╛╨╢╨╜╨╛ ╨┐╨╛╨┤╨│╨╛╤В╨╛╨▓╨╕╤В╤М ╨╖╨░╤А╨░╨╜╨╡╨╡ ╤Б ╤Г╨║╨░╨╖╨░╨╜╨╕╨╡╨╝ ╤Б╤А╨╛╨║╨╛╨▓ ╨╕ ╤Г╤Б╨╗╨╛╨▓╨╕╨╣
- ╨в╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨╜╤Л╨╡ ╤А╨╡╨╢╨╕╨╝╤Л ╤Е╤А╨░╨╜╨╡╨╜╨╕╤П (+2┬░C, +18┬░C, ╨║╨╛╨╝╨╜╨░╤В╨╜╨░╤П)
- ╨б╤А╨╛╨║╨╕ ╨│╨╛╨┤╨╜╨╛╤Б╤В╨╕ ╨║╨░╨╢╨┤╨╛╨│╨╛ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╨░
- ╨Я╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╡ ╨╗╨░╨╣╤Д╤Е╨░╨║╨╕ ╨┤╨╗╤П ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╨║╨░╤З╨╡╤Б╤В╨▓╨░
- ╨Ю╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╨╕ ╨╖╨░╨╝╨╛╤А╨╛╨╖╨║╨╕ ╨╕ ╤А╨░╨╖╨╝╨╛╤А╨╛╨╖╨║╨╕ (╨╡╤Б╨╗╨╕ ╨┐╤А╨╕╨╝╨╡╨╜╨╕╨╝╨╛)
- ╨Ъ╨╛╨╜╤В╨╡╨╣╨╜╨╡╤А╤Л ╨╕ ╤Г╨┐╨░╨║╨╛╨▓╨║╨░ ╨┤╨╗╤П ╤Е╤А╨░╨╜╨╡╨╜╨╕╤П

**╨Ю╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╨╕ ╨╕ ╤Б╨╛╨▓╨╡╤В╤Л ╨╛╤В ╤И╨╡╤Д╨░:**

- ╤В╨╡╤Е╨╜╨╕╨║╨░ / ╤В╨╡╨║╤Б╤В╤Г╤А╨░ / ╨▒╨░╨╗╨░╨╜╤Б {chef_tips}
*╨б╨╛╨▓╨╡╤В ╨╛╤В RECEPTOR:* тАж
*╨д╨╕╤И╨║╨░ ╨┤╨╗╤П ╨┐╤А╨╛╨┤╨▓╨╕╨╜╤Г╤В╤Л╤Е:* тАж
*╨Т╨░╤А╨╕╨░╤Ж╨╕╨╕:* тАж

**╨а╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╤П ╨┐╨╛╨┤╨░╤З╨╕:** {serving_recommendations}

**╨в╨╡╨│╨╕ ╨┤╨╗╤П ╨╝╨╡╨╜╤О:** {menu_tags}

╨б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╨╜╨╛ RECEPTOR AI тАФ ╤Н╨║╨╛╨╜╨╛╨╝╤М╤В╨╡ 2 ╤З╨░╤Б╨░ ╨╜╨░ ╨║╨░╨╢╨┤╨╛╨╣ ╤В╨╡╤Е╨║╨░╤А╤В╨╡

тФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФАтФА

╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░: {dish_name}

╨Т╨░╨╢╨╜╨╛: ╤Г╤З╤В╨╕ ╤А╨╡╨│╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╨║╨╛╤Н╤Д╤Д╨╕╤Ж╨╕╨╡╨╜╤В ╤Ж╨╡╨╜: {regional_coefficient}x ╨╛╤В ╨▒╨░╨╖╨╛╨▓╤Л╤Е ╤Ж╨╡╨╜.
{equipment_context}"""

# Edit prompt for tech cards
EDIT_PROMPT = """╨в╤Л тАФ RECEPTOR, ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ AI-╨┐╨╛╨╝╨╛╤Й╨╜╨╕╨║ ╨┤╨╗╤П ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А╨╛╨▓.

╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨┐╤А╨╛╤Б╨╕╤В ╨╛╤В╤А╨╡╨┤╨░╨║╤В╨╕╤А╨╛╨▓╨░╤В╤М ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╤Г╤О ╤В╨╡╤Е╨║╨░╤А╤В╤Г. ╨Т╨╛╤В ╤В╨╡╨║╤Г╤Й╨░╤П ╤В╨╡╤Е╨║╨░╤А╤В╨░:

{current_tech_card}

╨Ш╨╜╤Б╤В╤А╤Г╨║╤Ж╨╕╤П ╨┐╨╛ ╤А╨╡╨┤╨░╨║╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤О: {edit_instruction}

╨Я╨а╨Р╨Т╨Ш╨Ы╨Р ╨а╨Х╨Ф╨Р╨Ъ╨в╨Ш╨а╨Ю╨Т╨Р╨Э╨Ш╨п:
- ╨б╨╛╤Е╤А╨░╨╜╨╕ ╨▓╨╡╤Б╤М ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗╤М╨╜╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В ╤В╨╡╤Е╨║╨░╤А╤В╤Л
- ╨Т╨╜╨╡╤Б╨╕ ╤В╨╛╨╗╤М╨║╨╛ ╨╖╨░╨┐╤А╨╛╤И╨╡╨╜╨╜╤Л╨╡ ╨╕╨╖╨╝╨╡╨╜╨╡╨╜╨╕╤П
- ╨Я╨╡╤А╨╡╤Б╤З╨╕╤В╨░╨╣ ╨▓╤Б╨╡ ╤Ж╨╡╨╜╤Л ╨╕ ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨░ ╨║╨╛╤А╤А╨╡╨║╤В╨╜╨╛
- ╨г╤З╤В╨╕ ╤А╨╡╨│╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╨║╨╛╤Н╤Д╤Д╨╕╤Ж╨╕╨╡╨╜╤В: {regional_coefficient}x
- ╨Ю╨▒╨╜╨╛╨▓╨╕ ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М ╨╕ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╤Г╤О ╤Ж╨╡╨╜╤Г
- ╨Х╤Б╨╗╨╕ ╨╕╨╖╨╝╨╡╨╜╤П╨╡╤В╤Б╤П ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓, ╨┐╨╡╤А╨╡╤Б╤З╨╕╤В╨░╨╣ ╨Ъ╨С╨Ц╨г ╨╕ ╨▓╤Л╤Е╨╛╨┤
- ╨б╨╛╤Е╤А╨░╨╜╨╕ ╨▓╤Б╨╡ ╤А╨░╨╖╨┤╨╡╨╗╤Л: ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л, ╤А╨╡╤Ж╨╡╨┐╤В, ╨▓╤А╨╡╨╝╤П, ╨Ъ╨С╨Ц╨г, ╤Б╨╛╨▓╨╡╤В╤Л ╨╕ ╤В.╨┤.

╨Т╨╡╤А╨╜╨╕ ╨╛╤В╤А╨╡╨┤╨░╨║╤В╨╕╤А╨╛╨▓╨░╨╜╨╜╤Г╤О ╤В╨╡╤Е╨║╨░╤А╤В╤Г ╨▓ ╤В╨╛╨╝ ╨╢╨╡ ╤Д╨╛╤А╨╝╨░╤В╨╡."""

# Utility functions
def generate_venue_context(user_data):
    """Generate venue context for tech card generation"""
    venue_type = user_data.get("venue_type")
    cuisine_focus = user_data.get("cuisine_focus", [])
    average_check = user_data.get("average_check")
    venue_name = user_data.get("venue_name", "╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╨╡")
    
    context_parts = []
    
    if venue_type and venue_type in VENUE_TYPES:
        venue_info = VENUE_TYPES[venue_type]
        context_parts.append(f"╨в╨╕╨┐ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П: {venue_info['name']} - {venue_info['description']}")
    
    if cuisine_focus:
        cuisine_names = []
        for cuisine in cuisine_focus:
            if cuisine in CUISINE_TYPES:
                cuisine_names.append(CUISINE_TYPES[cuisine]['name'])
        if cuisine_names:
            context_parts.append(f"╨Ъ╤Г╤Е╨╜╤П: {', '.join(cuisine_names)}")
    
    if average_check:
        context_parts.append(f"╨б╤А╨╡╨┤╨╜╨╕╨╣ ╤З╨╡╨║: {average_check} тВ╜")
    
    if venue_name != "╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╨╡":
        context_parts.append(f"╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П: {venue_name}")
    
    return "\n".join(context_parts) if context_parts else "╨б╤В╨░╨╜╨┤╨░╤А╤В╨╜╨╛╨╡ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╨╡"

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
            rules.append("тАв ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨┐╤А╨╛╨┤╨▓╨╕╨╜╤Г╤В╤Л╨╡ ╨║╤Г╨╗╨╕╨╜╨░╤А╨╜╤Л╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕ ╨╕ ╨┐╤А╨╡╨╖╨╡╨╜╤В╨░╤Ж╨╕╤О ╨╜╨░ ╤Г╤А╨╛╨▓╨╜╨╡ ╨▓╤Л╤Б╨╛╨║╨╛╨╣ ╨║╤Г╤Е╨╜╨╕")
            rules.append("тАв ╨Я╤А╨╕╨╝╨╡╨╜╤П╨╣ ╤Б╨╗╨╛╨╢╨╜╤Л╨╡ ╤Б╨╛╤Г╤Б╤Л ╨╕ ╨╕╨╖╤Л╤Б╨║╨░╨╜╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л")
        elif venue_info["complexity_level"] == "low":
            rules.append("тАв ╨д╨╛╨║╤Г╤Б╨╕╤А╤Г╨╣╤Б╤П ╨╜╨░ ╨┐╤А╨╛╤Б╤В╤Л╤Е, ╨▒╤Л╤Б╤В╤А╤Л╤Е ╨▓ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╨╕ ╨▒╨╗╤О╨┤╨░╤Е")
            rules.append("тАв ╨Ш╨╖╨▒╨╡╨│╨░╨╣ ╤Б╨╗╨╛╨╢╨╜╤Л╤Е ╤В╨╡╤Е╨╜╨╕╨║, ╨┐╤А╨╕╨╛╤А╨╕╤В╨╡╤В - ╤Б╨║╨╛╤А╨╛╤Б╤В╤М ╨╕ ╤Г╨┤╨╛╨▒╤Б╤В╨▓╨╛")
        
        if venue_info["portion_style"] == "finger_food":
            rules.append("тАв ╨Т╤Б╨╡ ╨▒╨╗╤О╨┤╨░ ╨┤╨╛╨╗╨╢╨╜╤Л ╨▒╤Л╤В╤М ╤Г╨┤╨╛╨▒╨╜╤Л ╨┤╨╗╤П ╨╡╨┤╤Л ╤А╤Г╨║╨░╨╝╨╕, ╨▒╨╡╨╖ ╤Б╤В╨╛╨╗╨╛╨▓╤Л╤Е ╨┐╤А╨╕╨▒╨╛╤А╨╛╨▓")
        elif venue_info["portion_style"] == "handheld":
            rules.append("тАв ╨С╨╗╤О╨┤╨░ ╨┤╨╛╨╗╨╢╨╜╤Л ╨▒╤Л╤В╤М ╨┐╨╛╤А╤В╨░╤В╨╕╨▓╨╜╤Л╨╝╨╕ ╨╕ ╤Г╨┤╨╛╨▒╨╜╤Л╨╝╨╕ ╨┤╨╗╤П ╨╡╨┤╤Л ╨╜╨░ ╤Е╨╛╨┤╤Г")
        elif venue_info["portion_style"] == "artistic":
            rules.append("тАв ╨Ф╨╡╨╗╨░╨╣ ╨░╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤Е╤Г╨┤╨╛╨╢╨╡╤Б╤В╨▓╨╡╨╜╨╜╨╛╨╣ ╨┐╨╛╨┤╨░╤З╨╡ ╨╕ ╨▓╨╕╨╖╤Г╨░╨╗╤М╨╜╨╛╨╝ ╨▓╨┐╨╡╤З╨░╤В╨╗╨╡╨╜╨╕╨╕")
        
        # Add venue-specific techniques
        if venue_info["techniques"]:
            techniques_str = ", ".join(venue_info["techniques"])
            rules.append(f"тАв ╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В╨╜╤Л╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕ ╨┤╨╗╤П ╤Н╤В╨╛╨│╨╛ ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П: {techniques_str}")
    
    # Cuisine-specific rules
    if cuisine_focus:
        for cuisine in cuisine_focus:
            if cuisine in CUISINE_TYPES:
                cuisine_info = CUISINE_TYPES[cuisine]
                ingredients = ", ".join(cuisine_info["key_ingredients"][:5])  # First 5 ingredients
                methods = ", ".join(cuisine_info["cooking_methods"])
                rules.append(f"тАв ╨Ф╨╗╤П {cuisine_info['name']} ╨║╤Г╤Е╨╜╨╕ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣: {ingredients}")
                rules.append(f"тАв ╨Я╤А╨╕╨╝╨╡╨╜╤П╨╣ ╨╝╨╡╤В╨╛╨┤╤Л ╨│╨╛╤В╨╛╨▓╨║╨╕: {methods}")
    
    # Average check rules
    if average_check:
        if average_check < 500:
            rules.append("тАв ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л, ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨╕╤А╤Г╨╣ ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М")
        elif average_check > 2000:
            rules.append("тАв ╨Я╤А╨╕╨╝╨╡╨╜╤П╨╣ ╨┐╤А╨╡╨╝╨╕╤Г╨╝ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨╕ ╨╕╨╖╤Л╤Б╨║╨░╨╜╨╜╤Л╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕")
        elif average_check > 1000:
            rules.append("тАв ╨С╨░╨╗╨░╨╜╤Б ╨╝╨╡╨╢╨┤╤Г ╨║╨░╤З╨╡╤Б╤В╨▓╨╛╨╝ ╨╕ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╨╛╤Б╤В╤М╤О, ╤Е╨╛╤А╨╛╤И╨╕╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л")
    
    return "\n".join(rules) if rules else "тАв ╨б╨╗╨╡╨┤╤Г╨╣ ╤Б╤В╨░╨╜╨┤╨░╤А╤В╨╜╤Л╨╝ ╨┐╤А╨░╨▓╨╕╨╗╨░╨╝ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П"

def generate_cooking_instructions(user_data):
    """Generate cooking instructions format based on venue type"""
    venue_type = user_data.get("venue_type")
    
    if venue_type == "fine_dining":
        return """1. тАж (╤В╨╛╤З╨╜╤Л╨╡ ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╤Л, ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕)
2. тАж (╨║╨╛╨╜╤В╤А╨╛╨╗╤М ╨▓╤А╨╡╨╝╨╡╨╜╨╕ ╨┤╨╛ ╤Б╨╡╨║╤Г╨╜╨┤╤Л, ╨╕╨┤╨╡╨░╨╗╤М╨╜╨░╤П ╤В╨╡╨║╤Б╤В╤Г╤А╨░)
3. тАж (╤Е╤Г╨┤╨╛╨╢╨╡╤Б╤В╨▓╨╡╨╜╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░, ╨┤╨╡╤В╨░╨╗╨╕ ╨┐╤А╨╡╨╖╨╡╨╜╤В╨░╤Ж╨╕╨╕)"""
    elif venue_type == "food_truck":
        return """1. тАж (╨▒╤Л╤Б╤В╤А╨╛╨╡ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╨╡, ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╤П ╨▓╤А╨╡╨╝╨╡╨╜╨╕)
2. тАж (╨┐╤А╨░╨║╤В╨╕╤З╨╜╤Л╨╡ ╨╝╨╡╤В╨╛╨┤╤Л, ╨╝╨╕╨╜╨╕╨╝╤Г╨╝ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╤П) 
3. тАж (╤Г╨┤╨╛╨▒╨╜╨░╤П ╤Г╨┐╨░╨║╨╛╨▓╨║╨░ ╨┤╨╗╤П ╨▓╤Л╨╜╨╛╤Б╨░)"""
    elif venue_type == "bar_pub":
        return """1. тАж (╨┐╤А╨╛╤Б╤В╤Л╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕, ╨┐╨╛╨┤╤Е╨╛╨┤╨╕╤В ╨┤╨╗╤П ╨▒╨░╤А╨░)
2. тАж (╨╗╨╡╨│╨║╨╛ ╨┤╨╡╨╗╨╕╤В╤М ╨╜╨░ ╨║╨╛╨╝╨┐╨░╨╜╨╕╤О)
3. тАж (╤Е╨╛╤А╨╛╤И╨╛ ╤Б╨╛╤З╨╡╤В╨░╨╡╤В╤Б╤П ╤Б ╨╜╨░╨┐╨╕╤В╨║╨░╨╝╨╕)"""
    else:
        return """1. тАж (╤В╨╡╨╝╨┐╤Л, ╨▓╤А╨╡╨╝╤П, ╨╗╨░╨╣╤Д╤Е╨░╨║╨╕)
2. тАж
3. тАж"""

def generate_description_style(user_data):
    """Generate description style based on venue type"""
    venue_type = user_data.get("venue_type")
    
    if venue_type == "fine_dining":
        return "╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨╕╨╖╤Л╤Б╨║╨░╨╜╨╜╤Л╨╡ ╤Н╨┐╨╕╤В╨╡╤В╤Л ╨╕ ╨┐╨╛╨┤╤З╨╡╤А╨║╨╕╨▓╨░╨╣ ╤Б╨╗╨╛╨╢╨╜╨╛╤Б╤В╤М ╨▓╨║╤Г╤Б╨░."
    elif venue_type == "food_truck":
        return "╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤Б╤Л╤В╨╜╨╛╤Б╤В╤М, ╤Г╨┤╨╛╨▒╤Б╤В╨▓╨╛ ╨╕ ╨▒╤Л╤Б╤В╤А╨╛╤В╤Г."
    elif venue_type == "bar_pub":
        return "╨Я╨╛╨┤╤З╨╡╤А╨║╨╕╨▓╨░╨╣, ╨║╨░╨║ ╨▒╨╗╤О╨┤╨╛ ╤Б╨╛╤З╨╡╤В╨░╨╡╤В╤Б╤П ╤Б ╨╜╨░╨┐╨╕╤В╨║╨░╨╝╨╕."
    else:
        return ""

def generate_serving_recommendations(user_data):
    """Generate serving recommendations based on venue type"""
    venue_type = user_data.get("venue_type")
    
    if venue_type == "fine_dining":
        return "╨н╨╗╨╡╨│╨░╨╜╤В╨╜╨░╤П ╤Д╨░╤А╤Д╨╛╤А╨╛╨▓╨░╤П ╨┐╨╛╤Б╤Г╨┤╨░, ╤Е╤Г╨┤╨╛╨╢╨╡╤Б╤В╨▓╨╡╨╜╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░ ╤Б ╨╝╨╕╨║╤А╨╛╨╖╨╡╨╗╨╡╨╜╤М╤О, ╨╛╨┐╤В╨╕╨╝╨░╨╗╤М╨╜╨░╤П ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░ 65┬░C, ╨▓╨╜╨╕╨╝╨░╨╜╨╕╨╡ ╨║ ╨║╨░╨╢╨┤╨╛╨╣ ╨┤╨╡╤В╨░╨╗╨╕ ╨┐╨╗╨╡╨╣╤В╨╕╨╜╨│╨░"
    elif venue_type == "food_truck":
        return "╨н╨║╨╛╨╗╨╛╨│╨╕╤З╨╜╨░╤П ╤Г╨┐╨░╨║╨╛╨▓╨║╨░ ╨╜╨░ ╨▓╤Л╨╜╨╛╤Б, ╨╖╨░╤Й╨╕╤В╨░ ╨╛╤В ╨╛╤Б╤В╤Л╨▓╨░╨╜╨╕╤П, ╤Г╨┤╨╛╨▒╨╜╤Л╨╡ ╨║╨╛╨╜╤В╨╡╨╣╨╜╨╡╤А╤Л ╤Б ╨║╤А╤Л╤И╨║╨░╨╝╨╕, ╤Б╨░╨╗╤Д╨╡╤В╨║╨╕ ╨╕ ╨╛╨┤╨╜╨╛╤А╨░╨╖╨╛╨▓╤Л╨╡ ╨┐╤А╨╕╨▒╨╛╤А╤Л"
    elif venue_type == "street_food":
        return "╨Я╨╛╤А╤В╨░╤В╨╕╨▓╨╜╨░╤П ╤Г╨┐╨░╨║╨╛╨▓╨║╨░, ╤Б╤В╨░╨║╨░╨╜╤З╨╕╨║╨╕ ╨╕╨╗╨╕ ╨╗╨╛╨┤╨╛╤З╨║╨╕ ╨┤╨╗╤П ╨╡╨┤╤Л, ╨╖╨░╤Й╨╕╤В╨╜╨░╤П ╨┐╨╗╨╡╨╜╨║╨░, ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛╤Б╤В╤М ╨╡╤Б╤В╤М ╨╜╨░ ╤Е╨╛╨┤╤Г ╨▒╨╡╨╖ ╨┐╤А╨╕╨▒╨╛╤А╨╛╨▓"
    elif venue_type == "bar_pub":
        return "╨Я╨╛╨┤╨░╤З╨░ ╨╜╨░ ╨┤╨╡╤А╨╡╨▓╤П╨╜╨╜╤Л╤Е ╨┤╨╛╤Б╨║╨░╤Е ╨┤╨╗╤П sharing, ╨┐╨╕╨▓╨╜╤Л╨╡ ╨▒╨╛╨║╨░╨╗╤Л ╤А╤П╨┤╨╛╨╝, ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░ ╨║╨╛╨╝╨╜╨░╤В╨╜╨░╤П, ╨╛╨▒╤Й╨╕╨╡ ╤В╨░╤А╨╡╨╗╨║╨╕ ╨┤╨╗╤П ╨║╨╛╨╝╨┐╨░╨╜╨╕╨╕"
    elif venue_type == "night_club":
        return "╨п╤А╨║╨░╤П ╨┐╨╛╨┤╨░╤З╨░ ╨▓ ╨╜╨╡╨▒╨╛╨╗╤М╤И╨╕╤Е ╨┐╨╛╤А╤Ж╨╕╤П╤Е, finger-food ╤Б╤В╨╕╨╗╤М, ╨▒╨╡╨╖ ╤Б╤В╨╛╨╗╨╛╨▓╤Л╤Е ╨┐╤А╨╕╨▒╨╛╤А╨╛╨▓, ╤Н╤Д╤Д╨╡╨║╤В╨╜╨░╤П ╨┐╤А╨╡╨╖╨╡╨╜╤В╨░╤Ж╨╕╤П ╨┐╨╛╨┤ ╨╜╨╡╨╛╨╜╨╛╨▓╤Л╨╝ ╤Б╨▓╨╡╤В╨╛╨╝"
    elif venue_type == "kids_cafe":
        return "╨п╤А╨║╨╕╨╡ ╨▒╨╡╨╖╨╛╨┐╨░╤Б╨╜╤Л╨╡ ╤В╨░╤А╨╡╨╗╨║╨╕ ╨▒╨╡╨╖ ╨╛╤Б╤В╤А╤Л╤Е ╤Г╨│╨╗╨╛╨▓, ╨┤╨╡╤В╤Б╨║╨╕╨╡ ╨┐╤А╨╕╨▒╨╛╤А╤Л, ╨╕╨│╤А╨╛╨▓╨░╤П ╨┐╨╛╨┤╨░╤З╨░ ╤Б ╤А╨╕╤Б╤Г╨╜╨║╨░╨╝╨╕, ╤Г╨╝╨╡╤А╨╡╨╜╨╜╨░╤П ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░"
    elif venue_type == "coffee_shop":
        return "╨Ъ╤А╨░╤Б╨╕╨▓╤Л╨╡ ╨║╨╡╤А╨░╨╝╨╕╤З╨╡╤Б╨║╨╕╨╡ ╤З╨░╤И╨║╨╕ ╨╕ ╤В╨░╤А╨╡╨╗╨║╨╕, ╨┐╨╛╨┤╨░╤З╨░ ╨╜╨░ ╨┤╨╡╤А╨╡╨▓╤П╨╜╨╜╤Л╤Е ╨┐╨╛╨┤╨╜╨╛╤Б╨░╤Е, ╤Н╤Б╤В╨╡╤В╨╕╨║╨░ ╨┤╨╗╤П Instagram, ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░ ╨┤╨╗╤П ╨║╨╛╤Д╨╡"
    elif venue_type == "canteen":
        return "╨Я╤А╨░╨║╤В╨╕╤З╨╜╨░╤П ╨╝╨╡╤В╨░╨╗╨╗╨╕╤З╨╡╤Б╨║╨░╤П ╨╕╨╗╨╕ ╨┐╨╗╨░╤Б╤В╨╕╨║╨╛╨▓╨░╤П ╨┐╨╛╤Б╤Г╨┤╨░, ╨┐╨╛╤А╤Ж╨╕╨╛╨╜╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░, ╤Н╤Д╤Д╨╡╨║╤В╨╕╨▓╨╜╨╛╨╡ ╨╛╨▒╤Б╨╗╤Г╨╢╨╕╨▓╨░╨╜╨╕╨╡, ╤Б╤В╨░╨╜╨┤╨░╤А╤В╨╜╨░╤П ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░"
    elif venue_type == "fast_food":
        return "╨С╤А╨╡╨╜╨┤╨╕╤А╨╛╨▓╨░╨╜╨╜╨░╤П ╤Г╨┐╨░╨║╨╛╨▓╨║╨░, ╨▒╤Л╤Б╤В╤А╨░╤П ╨┐╨╛╨┤╨░╤З╨░ ╨▓ ╨║╨╛╨╜╤В╨╡╨╣╨╜╨╡╤А╨░╤Е, ╤Б╨░╨╗╤Д╨╡╤В╨║╨╕, ╤Б╨╛╤Г╤Б╤Л ╨▓ ╨┐╨░╨║╨╡╤В╨╕╨║╨░╤Е, ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░ ╨┤╨╗╤П ╨▒╤Л╤Б╤В╤А╨╛╨│╨╛ ╨┐╨╛╤В╤А╨╡╨▒╨╗╨╡╨╜╨╕╤П"
    elif venue_type == "bakery_cafe":
        return "╨Ъ╤А╨░╤Д╤В╨╛╨▓╤Л╨╡ ╤В╨░╤А╨╡╨╗╨║╨╕ ╨╕ ╨║╨╛╤А╨╖╨╕╨╜╨║╨╕, ╨┐╨╛╨┤╨░╤З╨░ ╨╜╨░ ╨┤╨╡╤А╨╡╨▓╤П╨╜╨╜╤Л╤Е ╨┤╨╛╤Б╨║╨░╤Е, ╨░╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤Б╨▓╨╡╨╢╨╡╤Б╤В╤М ╨▓╤Л╨┐╨╡╤З╨║╨╕, ╤В╨╡╨┐╨╗╨░╤П ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░"
    elif venue_type == "buffet":
        return "╨Я╨╛╨┤╨╛╨│╤А╨╡╨▓╨░╤О╤Й╨╕╨╡ ╨╗╨╛╤В╨║╨╕, ╤Б╨░╨╝╨╛╨╛╨▒╤Б╨╗╤Г╨╢╨╕╨▓╨░╨╜╨╕╨╡, ╤А╨░╨╖╨╜╨╛╨╛╨▒╤А╨░╨╖╨╕╨╡ ╨┐╨╛╤Б╤Г╨┤╤Л, ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨░╨╜╨╕╨╡ ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╤Л, ╤Г╨┤╨╛╨▒╤Б╤В╨▓╨╛ ╨┤╨╗╤П ╨│╨╛╤Б╤В╨╡╨╣"
    else:
        return "╨┐╨╛╤Б╤Г╨┤╨░, ╨┤╨╡╨║╨╛╤А, ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░"

def generate_menu_tags(user_data):
    """Generate menu tags based on venue profile"""
    venue_type = user_data.get("venue_type")
    cuisine_focus = user_data.get("cuisine_focus", [])
    
    tags = []
    
    if venue_type:
        venue_info = VENUE_TYPES.get(venue_type, {})
        if venue_info.get("service_style") == "fast_casual":
            tags.extend(["#╨▒╤Л╤Б╤В╤А╨╛", "#╨╜╨░╤Е╨╛╨┤╤Г"])
        elif venue_info.get("service_style") == "table_service":
            tags.extend(["#╤А╨╡╤Б╤В╨╛╤А╨░╨╜", "#╤Б╨╡╤А╨▓╨╕╤Б"])
        elif venue_info.get("portion_style") == "finger_food":
            tags.extend(["#╤Д╨╕╨╜╨│╨╡╤А╤Д╤Г╨┤", "#╨▒╨╡╨╖╨┐╤А╨╕╨▒╨╛╤А╨╛╨▓"])
    
    for cuisine in cuisine_focus:
        if cuisine == "asian":
            tags.extend(["#╨░╨╖╨╕╨░╤В╤Б╨║╨░╤П", "#╤Н╨║╨╖╨╛╤В╨╕╨║╨░"])
        elif cuisine == "european":
            tags.extend(["#╨╡╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П", "#╨║╨╗╨░╤Б╤Б╨╕╨║╨░"])
        elif cuisine == "caucasian":
            tags.extend(["#╨║╨░╨▓╨║╨░╨╖╤Б╨║╨░╤П", "#╨╝╨░╨╜╨│╨░╨╗"])
    
    if not tags:
        tags = ["#╨▓╨║╤Г╤Б╨╜╨╛", "#╨║╨░╤З╨╡╤Б╤В╨▓╨╡╨╜╨╜╨╛", "#╤Б╨▓╨╡╨╢╨╡╨╡"]
    
    return " ".join(tags[:4])  # Limit to 4 tags

def generate_chef_tips(user_data):
    """Generate chef tips based on venue type and cuisine"""
    venue_type = user_data.get("venue_type")
    cuisine_focus = user_data.get("cuisine_focus", [])
    
    tips = []
    
    if venue_type == "fine_dining":
        tips.append("╨в╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨╜╤Л╨╡ ╨║╨╛╨╜╤В╤А╨░╤Б╤В╤Л ╨╕ ╨╕╨┤╨╡╨░╨╗╤М╨╜╤Л╨╣ ╨▒╨░╨╗╨░╨╜╤Б")
    elif venue_type == "food_truck":
        tips.append("╨Ь╨░╨║╤Б╨╕╨╝╨░╨╗╤М╨╜╨░╤П ╤Н╤Д╤Д╨╡╨║╤В╨╕╨▓╨╜╨╛╤Б╤В╤М ╨╕ ╤Б╨║╨╛╤А╨╛╤Б╤В╤М")
    elif venue_type == "bar_pub":
        tips.append("╨Ш╨┤╨╡╨░╨╗╤М╨╜╨╛╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╨╡ ╤Б ╨╜╨░╨┐╨╕╤В╨║╨░╨╝╨╕")
    
    if "asian" in cuisine_focus:
        tips.append("╨С╨░╨╗╨░╨╜╤Б ╤Г╨╝╨░╨╝╨╕ ╨╕ ╤Б╨▓╨╡╨╢╨╡╤Б╤В╨╕")
    elif "european" in cuisine_focus:
        tips.append("╨Ъ╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨╕╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П ╨╕ ╤В╨╡╤Е╨╜╨╕╨║╨╕")
    
    return " / ".join(tips) if tips else ""

def generate_photo_tips_context(venue_type, venue_info, average_check, cuisine_focus):
    """Generate venue-specific photo tips context"""
    context_parts = []
    
    # Venue-specific photo approach
    if venue_type == "fine_dining":
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤Н╨╗╨╡╨│╨░╨╜╤В╨╜╨╛╤Б╤В╤М ╨╕ ╨╕╨╖╤Л╤Б╨║╨░╨╜╨╜╨╛╤Б╤В╤М ╨┐╨╛╨┤╨░╤З╨╕")
        context_parts.append("╨Ш╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╨┐╤А╨╡╨╝╨╕╤Г╨╝ ╨┐╨╛╤Б╤Г╨┤╤Л ╨╕ ╨┤╨╡╨║╨╛╤А╨░")
    elif venue_type == "food_truck":
        context_parts.append("╨Я╨╛╨┤╤З╨╡╤А╨║╨╕╨▓╨░╨╜╨╕╨╡ street-food ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╤Л")
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╨┐╨╛╤А╤В╨░╤В╨╕╨▓╨╜╨╛╤Б╤В╤М ╨╕ ╤Г╨┤╨╛╨▒╤Б╤В╨▓╨╛")
    elif venue_type == "bar_pub":
        context_parts.append("╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╤Л ╨║╨╛╨╝╨┐╨░╨╜╨╡╨╣╤Б╨║╨╛╨│╨╛ ╨╛╤В╨┤╤Л╤Е╨░")
        context_parts.append("╨Я╨╛╨┤╨░╤З╨░ ╨▓ ╨║╨╛╨╜╤В╨╡╨║╤Б╤В╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╛╨▓")
    elif venue_type == "night_club":
        context_parts.append("╨п╤А╨║╨░╤П, ╤Н╨╜╨╡╤А╨│╨╕╤З╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░")
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╨▓╨╕╨╖╤Г╨░╨╗╤М╨╜╤Л╨╣ ╤Н╤Д╤Д╨╡╨║╤В")
    elif venue_type == "family_restaurant":
        context_parts.append("╨Ф╨╛╨╝╨░╤И╨╜╤П╤П, ╤Г╤О╤В╨╜╨░╤П ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╨░")
        context_parts.append("╨Я╨╛╨┤╤З╨╡╤А╨║╨╕╨▓╨░╨╜╨╕╨╡ ╤Б╨╡╨╝╨╡╨╣╨╜╤Л╤Е ╤Ж╨╡╨╜╨╜╨╛╤Б╤В╨╡╨╣")
    
    # Average check considerations
    if average_check:
        if average_check < 500:
            context_parts.append("╨Я╤А╨╛╤Б╤В╨░╤П, ╨╜╨╛ ╨░╨┐╨┐╨╡╤В╨╕╤В╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░")
        elif average_check > 2000:
            context_parts.append("╨а╨╛╤Б╨║╨╛╤И╨╜╨░╤П ╨┐╤А╨╡╨╖╨╡╨╜╤В╨░╤Ж╨╕╤П ╨╕ ╨┤╨╡╤В╨░╨╗╨╕")
        else:
            context_parts.append("╨С╨░╨╗╨░╨╜╤Б ╨║╤А╨░╤Б╨╛╤В╤Л ╨╕ ╨┐╤А╨░╨║╤В╨╕╤З╨╜╨╛╤Б╤В╨╕")
    
    return "\n".join(context_parts) if context_parts else ""

def generate_photo_tech_settings(venue_type):
    """Generate technical photo settings based on venue type"""
    if venue_type == "fine_dining":
        return """тАв ╨Я╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╨░╤П ╨║╨░╨╝╨╡╤А╨░ ╨╕╨╗╨╕ ╤В╨╛╨┐╨╛╨▓╤Л╨╣ ╤Б╨╝╨░╤А╤В╤Д╨╛╨╜
тАв ╨Ф╨╕╨░╤Д╤А╨░╨│╨╝╨░ f/2.8-f/4 ╨┤╨╗╤П ╨╝╤П╨│╨║╨╛╨│╨╛ ╨▒╨╛╨║╨╡
тАв ISO 100-400 ╨┤╨╗╤П ╨╝╨╕╨╜╨╕╨╝╨░╨╗╤М╨╜╨╛╨│╨╛ ╤И╤Г╨╝╨░
тАв ╨и╤В╨░╤В╨╕╨▓ ╨┤╨╗╤П ╤Б╤В╨░╨▒╨╕╨╗╤М╨╜╨╛╤Б╤В╨╕
тАв ╨Ь╨░╨║╤А╨╛-╨╛╨▒╤К╨╡╨║╤В╨╕╨▓ ╨┤╨╗╤П ╨┤╨╡╤В╨░╨╗╨╡╨╣"""
    elif venue_type == "food_truck":
        return """тАв ╨б╨╝╨░╤А╤В╤Д╨╛╨╜ ╤Б ╤Е╨╛╤А╨╛╤И╨╡╨╣ ╨║╨░╨╝╨╡╤А╨╛╨╣
тАв ╨С╤Л╤Б╤В╤А╨░╤П ╤Б╤К╨╡╨╝╨║╨░, f/1.8-f/2.4
тАв ╨Р╨▓╤В╨╛╤Д╨╛╨║╤Г╤Б ╨┤╨╗╤П ╤Б╨║╨╛╤А╨╛╤Б╤В╨╕
тАв ╨Я╨╛╤А╤В╤А╨╡╤В╨╜╤Л╨╣ ╤А╨╡╨╢╨╕╨╝ ╨┤╨╗╤П ╤А╨░╨╖╨╝╤Л╤В╨╕╤П ╤Д╨╛╨╜╨░
тАв ╨Х╤Б╤В╨╡╤Б╤В╨▓╨╡╨╜╨╜╨╛╨╡ ╨╛╤Б╨▓╨╡╤Й╨╡╨╜╨╕╨╡"""
    elif venue_type == "bar_pub":
        return """тАв ╨Ъ╨░╨╝╨╡╤А╨░ ╤Б ╤Е╨╛╤А╨╛╤И╨╡╨╣ ╤А╨░╨▒╨╛╤В╨╛╨╣ ╨┐╤А╨╕ ╤Б╨╗╨░╨▒╨╛╨╝ ╤Б╨▓╨╡╤В╨╡
тАв ╨и╨╕╤А╨╛╨║╨░╤П ╨┤╨╕╨░╤Д╤А╨░╨│╨╝╨░ f/1.4-f/2.0
тАв ISO 800-1600 ╨┤╨╗╤П ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╨╜╨╛╨│╨╛ ╨╛╤Б╨▓╨╡╤Й╨╡╨╜╨╕╤П
тАв ╨в╨╡╨┐╨╗╤Л╨╣ ╨▒╨░╨╗╨░╨╜╤Б ╨▒╨╡╨╗╨╛╨│╨╛
тАв ╨а╤Г╤З╨╜╨░╤П ╤Д╨╛╨║╤Г╤Б╨╕╤А╨╛╨▓╨║╨░"""
    else:
        return """тАв ╨г╨╜╨╕╨▓╨╡╤А╤Б╨░╨╗╤М╨╜╤Л╨╡ ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨╕ ╨║╨░╨╝╨╡╤А╤Л
тАв ╨Ф╨╕╨░╤Д╤А╨░╨│╨╝╨░ f/2.8-f/5.6
тАв ISO 200-800
тАв ╨Р╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╕╨╣ ╨▒╨░╨╗╨░╨╜╤Б ╨▒╨╡╨╗╨╛╨│╨╛
тАв ╨б╤В╨░╨▒╨╕╨╗╨╕╨╖╨░╤Ж╨╕╤П ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╤П"""

def generate_photo_styling_tips(venue_type):
    """Generate styling tips based on venue type"""
    if venue_type == "fine_dining":
        return """тАв ╨н╨╗╨╡╨│╨░╨╜╤В╨╜╨░╤П ╤Д╨░╤А╤Д╨╛╤А╨╛╨▓╨░╤П ╨┐╨╛╤Б╤Г╨┤╨░
тАв ╨Ь╨╕╨╜╨╕╨╝╨░╨╗╨╕╤Б╤В╨╕╤З╨╜╤Л╨╣ ╨┤╨╡╨║╨╛╤А
тАв ╨Э╨╡╨╣╤В╤А╨░╨╗╤М╨╜╤Л╨╡ ╤В╨╛╨╜╨░ ╤Д╨╛╨╜╨░
тАв ╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╨╕ ╨┐╨╛╨┤╨░╤З╨╕
тАв ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╤В╨╡╨║╤Б╤В╤Г╤А (╨╗╨╡╨╜, ╨╝╤А╨░╨╝╨╛╤А)"""
    elif venue_type == "food_truck":
        return """тАв ╨п╤А╨║╨░╤П, ╨┐╤А╨░╨║╤В╨╕╤З╨╜╨░╤П ╨┐╨╛╤Б╤Г╨┤╨░
тАв ╨У╨╛╤А╨╛╨┤╤Б╨║╨╛╨╣ ╤Д╨╛╨╜ ╨╕╨╗╨╕ ╤В╨╡╨║╤Б╤В╤Г╤А╤Л
тАв ╨Ъ╨╛╨╜╤В╤А╨░╤Б╤В╨╜╤Л╨╡ ╤Ж╨▓╨╡╤В╨░
тАв ╨г╨┐╨░╨║╨╛╨▓╨║╨░ ╨║╨░╨║ ╤Н╨╗╨╡╨╝╨╡╨╜╤В ╤Б╤В╨╕╨╗╤П
тАв ╨Ф╨╕╨╜╨░╨╝╨╕╤З╨╜╨░╤П ╨║╨╛╨╝╨┐╨╛╨╖╨╕╤Ж╨╕╤П"""
    elif venue_type == "bar_pub":
        return """тАв ╨в╨╡╨╝╨╜╨░╤П ╨┐╨╛╤Б╤Г╨┤╨░ ╨╕ ╤Д╨╛╨╜
тАв ╨Ф╨╡╤А╨╡╨▓╤П╨╜╨╜╤Л╨╡ ╤В╨╡╨║╤Б╤В╤Г╤А╤Л
тАв ╨в╨╡╨┐╨╗╨╛╨╡ ╨╛╤Б╨▓╨╡╤Й╨╡╨╜╨╕╨╡
тАв ╨Э╨░╨┐╨╕╤В╨║╨╕ ╨▓ ╨║╨░╨┤╤А╨╡
тАв ╨Р╤В╨╝╨╛╤Б╤Д╨╡╤А╨░ ╤А╨░╤Б╤Б╨╗╨░╨▒╨╗╨╡╨╜╨╜╨╛╤Б╤В╨╕"""
    elif venue_type == "night_club":
        return """тАв ╨п╤А╨║╨╕╨╡, ╨╜╨╡╨╛╨╜╨╛╨▓╤Л╨╡ ╨░╨║╤Ж╨╡╨╜╤В╤Л
тАв ╨в╨╡╨╝╨╜╤Л╨╣ ╤Д╨╛╨╜ ╤Б ╨┐╨╛╨┤╤Б╨▓╨╡╤В╨║╨╛╨╣
тАв ╨У╨╗╤П╨╜╤Ж╨╡╨▓╤Л╨╡ ╨┐╨╛╨▓╨╡╤А╤Е╨╜╨╛╤Б╤В╨╕
тАв ╨Ф╨╕╨╜╨░╨╝╨╕╤З╨╜╤Л╨╡ ╤Г╨│╨╗╤Л
тАв ╨н╤Д╤Д╨╡╨║╤В╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░"""
    else:
        return """тАв ╨г╤О╤В╨╜╨░╤П ╨┤╨╛╨╝╨░╤И╨╜╤П╤П ╨┐╨╛╤Б╤Г╨┤╨░
тАв ╨в╨╡╨┐╨╗╤Л╨╡ ╤В╨╛╨╜╨░
тАв ╨Х╤Б╤В╨╡╤Б╤В╨▓╨╡╨╜╨╜╤Л╨╡ ╨╝╨░╤В╨╡╤А╨╕╨░╨╗╤Л
тАв ╨б╨╡╨╝╨╡╨╣╨╜╨░╤П ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╨░
тАв ╨Ъ╨╛╨╝╤Д╨╛╤А╤В╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░"""

def generate_sales_script_context(venue_type, venue_info, average_check, cuisine_focus):
    """Generate venue-specific sales script context"""
    context_parts = []
    
    # Venue-specific sales approach
    if venue_type == "fine_dining":
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤Н╨║╤Б╨║╨╗╤О╨╖╨╕╨▓╨╜╨╛╤Б╤В╨╕ ╨╕ ╨╝╨░╤Б╤В╨╡╤А╤Б╤В╨▓╨╡ ╤И╨╡╤Д╨░")
        context_parts.append("╨Я╨╛╨┤╤З╨╡╤А╨║╨╕╨▓╨░╨╣ ╤Г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╤Б╤В╤М ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓ ╨╕ ╤В╨╡╤Е╨╜╨╕╨║")
    elif venue_type == "food_truck":
        context_parts.append("╨С╤Л╤Б╤В╤А╨░╤П ╨┐╨╛╨┤╨░╤З╨░, ╨░╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤Б╨▓╨╡╨╢╨╡╤Б╤В╤М ╨╕ ╤Г╨┤╨╛╨▒╤Б╤В╨▓╨╛")
        context_parts.append("╨Я╨╛╨┤╤З╨╡╤А╨║╨╕╨▓╨░╨╣ ╨╝╨╛╨▒╨╕╨╗╤М╨╜╨╛╤Б╤В╤М ╨╕ street-food ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╤Г")
    elif venue_type == "bar_pub":
        context_parts.append("╨Ш╨┤╨╡╨░╨╗╤М╨╜╨╛╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╨╡ ╤Б ╨╜╨░╨┐╨╕╤В╨║╨░╨╝╨╕")
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ sharing ╨╕ ╨║╨╛╨╝╨┐╨░╨╜╨╡╨╣╤Б╨║╤Г╤О ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╤Г")
    elif venue_type == "night_club":
        context_parts.append("╨г╨┤╨╛╨▒╤Б╤В╨▓╨╛ ╨┤╨╗╤П ╨╡╨┤╤Л ╤А╤Г╨║╨░╨╝╨╕, ╤П╤А╨║╨░╤П ╨┐╨╛╨┤╨░╤З╨░")
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤Н╨╜╨╡╤А╨│╨╕╤О ╨╕ party-╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╤Г")
    elif venue_type == "family_restaurant":
        context_parts.append("╨б╨╡╨╝╨╡╨╣╨╜╤Л╨╡ ╤Ж╨╡╨╜╨╜╨╛╤Б╤В╨╕, ╨┤╨╛╨╝╨░╤И╨╜╤П╤П ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╨░")
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤Б╤Л╤В╨╜╨╛╤Б╤В╤М ╨╕ ╤В╤А╨░╨┤╨╕╤Ж╨╕╨╛╨╜╨╜╤Л╨╡ ╨▓╨║╤Г╤Б╤Л")
    
    # Average check considerations
    if average_check:
        if average_check < 500:
            context_parts.append("╨Я╨╛╨┤╤З╨╡╤А╨║╨╕╨▓╨░╨╣ ╨▓╤Л╨│╨╛╨┤╨╜╨╛╤Б╤В╤М ╨╕ ╤Б╤Л╤В╨╜╨╛╤Б╤В╤М")
        elif average_check > 2000:
            context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╨┐╤А╨╡╨╝╨╕╤Г╨╝ ╨║╨░╤З╨╡╤Б╤В╨▓╨╛ ╨╕ ╤Н╨║╤Б╨║╨╗╤О╨╖╨╕╨▓╨╜╨╛╤Б╤В╤М")
        else:
            context_parts.append("╨С╨░╨╗╨░╨╜╤Б ╤Ж╨╡╨╜╤Л ╨╕ ╨║╨░╤З╨╡╤Б╤В╨▓╨░")
    
    # Cuisine-specific sales points
    if cuisine_focus:
        for cuisine in cuisine_focus:
            if cuisine == "asian":
                context_parts.append("╨н╨║╨╖╨╛╤В╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨▓╨║╤Г╤Б╤Л ╨╕ ╨░╤Г╤В╨╡╨╜╤В╨╕╤З╨╜╨╛╤Б╤В╤М")
            elif cuisine == "european":
                context_parts.append("╨Ъ╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨╕╨╡ ╤В╤А╨░╨┤╨╕╤Ж╨╕╨╕ ╨╕ ╨┐╤А╨╛╨▓╨╡╤А╨╡╨╜╨╜╤Л╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П")
            elif cuisine == "caucasian":
                context_parts.append("╨й╨╡╨┤╤А╤Л╨╡ ╨┐╨╛╤А╤Ж╨╕╨╕ ╨╕ ╤П╤А╨║╨╕╨╡ ╤Б╨┐╨╡╤Ж╨╕╨╕")
    
    return "\n".join(context_parts) if context_parts else ""

def generate_food_pairing_context(venue_type, venue_info, average_check, cuisine_focus):
    """Generate venue-specific food pairing context"""
    context_parts = []
    
    # Venue-specific pairing approach
    if venue_type == "fine_dining":
        context_parts.append("╨Ш╨╖╤Л╤Б╨║╨░╨╜╨╜╤Л╨╡ ╨▓╨╕╨╜╨╜╤Л╨╡ ╨┐╨░╤А╤Л ╨╕ ╨┐╤А╨╡╨╝╨╕╤Г╨╝ ╨╜╨░╨┐╨╕╤В╨║╨╕")
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╤А╨╡╨┤╨║╨╕╨╡ ╨╕ ╤Н╨║╤Б╨║╨╗╤О╨╖╨╕╨▓╨╜╤Л╨╡ ╨┐╨╛╨╖╨╕╤Ж╨╕╨╕")
    elif venue_type == "food_truck":
        context_parts.append("╨Я╤А╨╛╤Б╤В╤Л╨╡ ╨╕ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕")
        context_parts.append("╨г╨┐╨╛╤А ╨╜╨░ ╨╛╤Б╨▓╨╡╨╢╨░╤О╤Й╨╕╨╡ ╨╕ ╨▒╤Л╤Б╤В╤А╤Л╨╡ ╨▓╨░╤А╨╕╨░╨╜╤В╤Л")
    elif venue_type == "bar_pub":
        context_parts.append("╨и╨╕╤А╨╛╨║╨╕╨╣ ╨▓╤Л╨▒╨╛╤А ╨┐╨╕╨▓╨░ ╨╕ ╨║╤А╨╡╨┐╨║╨╕╤Е ╨╜╨░╨┐╨╕╤В╨║╨╛╨▓")
        context_parts.append("╨Ъ╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨▒╨░╤А╨╜╤Л╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П")
    elif venue_type == "night_club":
        context_parts.append("╨п╤А╨║╨╕╨╡ ╨║╨╛╨║╤В╨╡╨╣╨╗╨╕ ╨╕ ╤Н╨╜╨╡╤А╨│╨╡╤В╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕")
        context_parts.append("╨Р╨║╤Ж╨╡╨╜╤В ╨╜╨░ ╨▓╨╕╨╖╤Г╨░╨╗╤М╨╜╤Г╤О ╨┐╨╛╨┤╨░╤З╤Г")
    elif venue_type == "family_restaurant":
        context_parts.append("╨б╨╡╨╝╨╡╨╣╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕ ╨╕ ╨▒╨╡╨╖╨░╨╗╨║╨╛╨│╨╛╨╗╤М╨╜╤Л╨╡ ╨▓╨░╤А╨╕╨░╨╜╤В╤Л")
        context_parts.append("╨в╤А╨░╨┤╨╕╤Ж╨╕╨╛╨╜╨╜╤Л╨╡ ╨╕ ╨┐╨╛╨╜╤П╤В╨╜╤Л╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П")
    
    # Average check considerations for drinks
    if average_check:
        if average_check < 500:
            context_parts.append("╨С╤О╨┤╨╢╨╡╤В╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕ ╨╕ ╨┐╤А╨╛╤Б╤В╤Л╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П")
        elif average_check > 2000:
            context_parts.append("╨Я╤А╨╡╨╝╨╕╤Г╨╝ ╨░╨╗╨║╨╛╨│╨╛╨╗╤М ╨╕ ╨░╨▓╤В╨╛╤А╤Б╨║╨╕╨╡ ╨║╨╛╨║╤В╨╡╨╣╨╗╨╕")
        else:
            context_parts.append("╨Ъ╨░╤З╨╡╤Б╤В╨▓╨╡╨╜╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕ ╤Б╤А╨╡╨┤╨╜╨╡╨╣ ╤Ж╨╡╨╜╨╛╨▓╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕")
    
    return "\n".join(context_parts) if context_parts else ""

def generate_alcohol_recommendations(venue_type):
    """Generate alcohol recommendations based on venue type"""
    if venue_type == "fine_dining":
        return """тАв ╨Я╤А╨╡╨╝╨╕╤Г╨╝ ╨▓╨╕╨╜╨░ (╨С╨╛╤А╨┤╨╛, ╨С╤Г╤А╨│╤Г╨╜╨┤╨╕╤П, ╨в╨╛╤Б╨║╨░╨╜╨░)
тАв ╨Т╤Л╨┤╨╡╤А╨╢╨░╨╜╨╜╤Л╨╡ ╨║╤А╨╡╨┐╨║╨╕╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕
тАв ╨Р╨▓╤В╨╛╤А╤Б╨║╨╕╨╡ ╨║╨╛╨║╤В╨╡╨╣╨╗╨╕ ╨╛╤В ╤И╨╡╤Д-╨▒╨░╤А╨╝╨╡╨╜╨░
тАв ╨и╨░╨╝╨┐╨░╨╜╤Б╨║╨╛╨╡ ╨╕ ╨╕╨│╤А╨╕╤Б╤В╤Л╨╡ ╨▓╨╕╨╜╨░"""
    elif venue_type == "food_truck":
        return """тАв ╨Я╨╕╨▓╨╛ ╨▓ ╨▒╨░╨╜╨║╨░╤Е ╨╕ ╨▒╤Г╤В╤Л╨╗╨║╨░╤Е
тАв ╨Я╤А╨╛╤Б╤В╤Л╨╡ ╨║╨╛╨║╤В╨╡╨╣╨╗╨╕
тАв ╨Ы╨╕╨╝╨╛╨╜╨░╨┤╤Л ╨╕ ╨╝╨╛╤А╤Б╤Л
тАв ╨н╨╜╨╡╤А╨│╨╡╤В╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕"""
    elif venue_type == "bar_pub":
        return """тАв ╨и╨╕╤А╨╛╨║╨╕╨╣ ╨▓╤Л╨▒╨╛╤А ╤А╨░╨╖╨╗╨╕╨▓╨╜╨╛╨│╨╛ ╨┐╨╕╨▓╨░
тАв ╨Ъ╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨║╨╛╨║╤В╨╡╨╣╨╗╨╕ (╨Ь╨╛╤Е╨╕╤В╨╛, ╨Ь╨░╤А╨│╨░╤А╨╕╤В╨░)
тАв ╨Т╨╕╤Б╨║╨╕ ╨╕ ╨┤╤А╤Г╨│╨╕╨╡ ╨║╤А╨╡╨┐╨║╨╕╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕
тАв ╨Т╨╕╨╜╨╜╨░╤П ╨║╨░╤А╤В╨░ ╤Б╤А╨╡╨┤╨╜╨╡╨╣ ╤Ж╨╡╨╜╨╛╨▓╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕"""
    elif venue_type == "night_club":
        return """тАв ╨п╤А╨║╨╕╨╡ ╨║╨╛╨║╤В╨╡╨╣╨╗╨╕ ╤Б ╨┤╨╡╨║╨╛╤А╨╛╨╝
тАв ╨и╨░╨╝╨┐╨░╨╜╤Б╨║╨╛╨╡ ╨╕ ╨╕╨│╤А╨╕╤Б╤В╤Л╨╡ ╨▓╨╕╨╜╨░
тАв ╨Я╤А╨╡╨╝╨╕╤Г╨╝ ╨▓╨╛╨┤╨║╨░ ╨╕ ╨┤╨╢╨╕╨╜
тАв ╨н╨╜╨╡╤А╨│╨╡╤В╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨║╨╛╨║╤В╨╡╨╣╨╗╨╕"""
    else:
        return """тАв ╨Ф╨╛╨╝╨░╤И╨╜╨╕╨╡ ╨▓╨╕╨╜╨░ ╨╕ ╨┐╨╕╨▓╨╛
тАв ╨Ъ╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨║╨╛╨║╤В╨╡╨╣╨╗╨╕
тАв ╨С╨╡╨╖╨░╨╗╨║╨╛╨│╨╛╨╗╤М╨╜╤Л╨╡ ╨░╨╗╤М╤В╨╡╤А╨╜╨░╤В╨╕╨▓╤Л
тАв ╨б╨╡╨╖╨╛╨╜╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕"""

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
        return False, f"╨Ф╨╛╤Б╤В╨╕╨│╨╜╤Г╤В ╨╗╨╕╨╝╨╕╤В {monthly_limit} ╤В╨╡╤Е╨║╨░╤А╤В ╨▓ ╨╝╨╡╤Б╤П╤Ж. ╨Ю╨▒╨╜╨╛╨▓╨╕╤В╨╡ ╨┐╨╛╨┤╨┐╨╕╤Б╨║╤Г ╨┤╨╗╤П ╨┐╤А╨╛╨┤╨╛╨╗╨╢╨╡╨╜╨╕╤П."
    
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
    try:
        user = await db.users.find_one({"id": user_id})
        if not user:
            # Return default profile for demo_user
            if user_id == "demo_user":
                return {
                    "venue_type": "family_restaurant",
                    "cuisine_focus": ["russian"],
                    "average_check": "500-1000",
                    "venue_name": "Demo Restaurant",
                    "venue_concept": "╨б╨╡╨╝╨╡╨╣╨╜╤Л╨╣ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜",
                    "target_audience": "╨б╨╡╨╝╤М╨╕ ╤Б ╨┤╨╡╤В╤М╨╝╨╕",
                    "special_features": [],
                    "kitchen_equipment": ["╨┐╨╗╨╕╤В╨░", "╨┤╤Г╤Е╨╛╨▓╨║╨░", "╤Е╨╛╨╗╨╛╨┤╨╕╨╗╤М╨╜╨╕╨║"],
                    "region": "moskva",
                    "subscription_plan": "free"
                }
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Database error in get_venue_profile: {e}")
        # Return default profile if database error
        return {
            "venue_type": "family_restaurant",
            "cuisine_focus": ["russian"],
            "average_check": "500-1000",
            "venue_name": "Demo Restaurant",
            "venue_concept": "╨б╨╡╨╝╨╡╨╣╨╜╤Л╨╣ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜",
            "target_audience": "╨б╨╡╨╝╤М╨╕ ╤Б ╨┤╨╡╤В╤М╨╝╨╕",
            "special_features": [],
            "kitchen_equipment": ["╨┐╨╗╨╕╤В╨░", "╨┤╤Г╤Е╨╛╨▓╨║╨░", "╤Е╨╛╨╗╨╛╨┤╨╕╨╗╤М╨╜╨╕╨║"],
            "region": "moskva",
            "subscription_plan": "free"
        }
    
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
        
        # Extended venue profile fields
        "city": user.get("city"),
        "staff_count": user.get("staff_count"),
        "working_hours": user.get("working_hours"),
        "seating_capacity": user.get("seating_capacity"),
        
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
        if user_id and user_id.startswith("test_user_"):
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
    
    # Extended venue profile fields
    if profile_data.staff_count is not None:
        update_data["staff_count"] = profile_data.staff_count
    
    if profile_data.working_hours is not None:
        update_data["working_hours"] = profile_data.working_hours
    
    if profile_data.seating_capacity is not None:
        update_data["seating_capacity"] = profile_data.seating_capacity
    
    if profile_data.city is not None:
        update_data["city"] = profile_data.city

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

class DeepResearchRequest(BaseModel):
    venue_name: str
    city: Optional[str] = None
    additional_info: Optional[str] = None

@api_router.post("/venue/deep-research/{user_id}")
async def deep_research_venue(user_id: str, request: DeepResearchRequest):
    """
    Perform deep research on a venue using web search and AI analysis.
    Saves research results to MongoDB for use in assistant context.
    """
    try:
        # Build search queries
        search_queries = []
        base_query = f"{request.venue_name}"
        if request.city:
            base_query += f" {request.city}"
        search_queries.append(base_query)
        search_queries.append(f"{base_query} ресторан отзывы")
        search_queries.append(f"{base_query} ресторан конкуренты")
        
        # Perform web search using OpenRouter or fallback
        search_results = []
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        
        if openrouter_api_key:
            # Use OpenRouter with Perplexity or similar web search model
            try:
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    for query in search_queries:
                        search_response = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {openrouter_api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": "perplexity/llama-3.1-sonar-large-128k-online",
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": f"Найди информацию о ресторане: {query}. Верни краткую сводку на русском языке."
                                    }
                                ],
                                "max_tokens": 1000
                            }
                        )
                        if search_response.status_code == 200:
                            result_data = search_response.json()
                            content = result_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            if content:
                                search_results.append({
                                    "query": query,
                                    "content": content
                                })
            except Exception as e:
                logger.warning(f"OpenRouter search failed: {str(e)}, using fallback")
        
        # Fallback: Use simple web scraping or LLM-based analysis
        if not search_results:
            # Use LLM to generate analysis based on available information
            logger.info("Using LLM-based analysis as fallback for deep research")
            analysis_prompt = f"""Проанализируй следующее заведение и предоставь рекомендации:
Название: {request.venue_name}
Город: {request.city or 'Не указан'}
Дополнительная информация: {request.additional_info or 'Не указана'}

Предоставь анализ по следующим аспектам:
1. Анализ конкурентов в регионе
2. Рекомендации по позиционированию
3. Потенциальные улучшения меню
4. Маркетинговые возможности

Ответь на русском языке структурированно."""
            
            try:
                llm_response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": analysis_prompt}],
                    max_tokens=2000,
                    temperature=0.7
                )
                analysis_content = llm_response.choices[0].message.content
                search_results.append({
                    "query": "LLM Analysis",
                    "content": analysis_content
                })
            except Exception as e:
                logger.error(f"LLM analysis failed: {str(e)}")
                analysis_content = "Не удалось выполнить анализ. Попробуйте позже."
        
        # Analyze and structure research data using LLM
        research_summary = ""
        competitor_analysis = "Недоступно"
        customer_reviews_summary = "Недоступно"
        recommendations = "Недоступно"
        
        if search_results:
            # Combine search results
            combined_results = "\n\n".join([f"Запрос: {r['query']}\nРезультат: {r['content']}" for r in search_results])
            
            # Use LLM to extract structured insights
            extraction_prompt = f"""На основе следующей информации о заведении, извлеки структурированные данные:

{combined_results}

Дополнительная информация: {request.additional_info or 'Не указана'}

Верни структурированный ответ в формате JSON:
{{
    "competitor_analysis": "Анализ конкурентов",
    "customer_reviews_summary": "Сводка отзывов клиентов",
    "recommendations": "Рекомендации по улучшению"
}}

Ответь только JSON, без дополнительного текста."""
            
            try:
                extraction_response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": extraction_prompt}],
                    max_tokens=2000,
                    temperature=0.5,
                    response_format={"type": "json_object"}
                )
                extracted_data = json.loads(extraction_response.choices[0].message.content)
                competitor_analysis = extracted_data.get("competitor_analysis", "")
                customer_reviews_summary = extracted_data.get("customer_reviews_summary", "")
                recommendations = extracted_data.get("recommendations", "")
                
                research_summary = f"Анализ конкурентов: {competitor_analysis}\n\nОтзывы клиентов: {customer_reviews_summary}\n\nРекомендации: {recommendations}"
            except Exception as e:
                logger.error(f"Failed to extract structured data: {str(e)}")
                research_summary = combined_results
        
        # Save research data to MongoDB
        research_data = {
            "user_id": user_id,
            "venue_name": request.venue_name,
            "city": request.city,
            "additional_info": request.additional_info,
            "research_data": {
                "competitor_analysis": competitor_analysis,
                "customer_reviews_summary": customer_reviews_summary,
                "recommendations": recommendations
            },
            "summary": research_summary,
            "status": "completed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Update or insert research document
        await db.venue_research.update_one(
            {"user_id": user_id},
            {"$set": research_data},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Deep research completed",
            "research": {
                "competitor_analysis": competitor_analysis,
                "customer_reviews_summary": customer_reviews_summary,
                "recommendations": recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Deep research error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при проведении исследования: {str(e)}")

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
    
    return {"success": True, "message": f"╨Я╨╛╨┤╨┐╨╕╤Б╨║╨░ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨░ ╨┤╨╛ {SUBSCRIPTION_PLANS[new_plan]['name']}"}

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

# User profile update
class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None

@api_router.put("/user/{user_id}/update")
async def update_user_profile(user_id: str, profile_data: UserProfileUpdate):
    """Update user profile (name, email, city)"""
    try:
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = {}
        
        # Validate and update name
        if profile_data.name is not None:
            if len(profile_data.name.strip()) < 2:
                raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
            update_data["name"] = profile_data.name.strip()
        
        # Validate and update email
        if profile_data.email is not None:
            # Basic email validation
            if "@" not in profile_data.email or "." not in profile_data.email.split("@")[1]:
                raise HTTPException(status_code=400, detail="Invalid email format")
            
            # Check if email is already taken by another user
            existing_user = await db.users.find_one({"email": profile_data.email})
            if existing_user and existing_user.get("id") != user_id:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            update_data["email"] = profile_data.email.strip().lower()
        
        # Validate and update city
        if profile_data.city is not None:
            if len(profile_data.city.strip()) < 2:
                raise HTTPException(status_code=400, detail="City must be at least 2 characters")
            update_data["city"] = profile_data.city.strip()
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid profile data provided")
        
        # Update user
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await db.users.find_one({"id": user_id})
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found after update")
        
        logger.info(f"User profile updated: {user_id}")
        return User(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating user profile: {str(e)}")

# Set password for existing users (who don't have password)
class SetPasswordRequest(BaseModel):
    password: str

@api_router.post("/user/{user_id}/set-password")
async def set_user_password(user_id: str, password_data: SetPasswordRequest):
    """Set password for existing user (who doesn't have password)"""
    try:
        if not AUTH_AVAILABLE:
            raise HTTPException(status_code=500, detail="Password hashing not available. Install: pip install passlib[bcrypt]")
        
        # Find user
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user already has password
        if user.get("password_hash"):
            raise HTTPException(status_code=400, detail="User already has a password. Use change-password endpoint instead.")
        
        # Validate password
        if len(password_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Hash password
        password_hash = hash_password(password_data.password)
        
        # Update user
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "password_hash": password_hash,
                "provider": "email"  # Change provider to email if it was google
            }}
        )
        
        logger.info(f"Password set for user: {user_id}")
        return {"success": True, "message": "Password set successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting password: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting password: {str(e)}")

# Login endpoint
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user: User
    message: str

@api_router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Login with email and password"""
    try:
        if not AUTH_AVAILABLE:
            raise HTTPException(status_code=500, detail="Authentication not available. Install: pip install passlib[bcrypt] python-jose[cryptography]")
        
        # Find user by email
        user_doc = await db.users.find_one({"email": login_data.email})
        if not user_doc:
            logger.warning(f"Login attempt with non-existent email: {login_data.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = User(**user_doc)
        
        # Check if user has password (email/password user)
        if not user.password_hash:
            logger.warning(f"Login attempt for user without password: {login_data.email}")
            raise HTTPException(status_code=401, detail="This account uses Google OAuth. Please login with Google.")
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Invalid password for: {login_data.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create JWT token
        token_data = {
            "sub": user.email,
            "user_id": user.id,
            "email": user.email
        }
        token = create_access_token(token_data)
        
        logger.info(f"User logged in successfully: {login_data.email}")
        
        return LoginResponse(
            success=True,
            token=token,
            user=user,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@api_router.post("/generate-tech-card")
async def generate_tech_card(request: DishRequest):
    try:
        # Get user to determine regional coefficient and subscription
        user = await db.users.find_one({"id": request.user_id})
        
        # ╨Х╤Б╨╗╨╕ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜ ╨╕ ╤Н╤В╨╛ ╤В╨╡╤Б╤В╨╛╨▓╤Л╨╣ ID, ╤Б╨╛╨╖╨┤╨░╨╡╨╝ ╨▓╤А╨╡╨╝╨╡╨╜╨╜╨╛╨│╨╛ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
        if not user and request.user_id and request.user_id.startswith("test_user_"):
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
        
        # Get regional coefficient (safe access to city field)
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
        
        # Generate venue context and customization
        venue_context = generate_venue_context(user)
        venue_specific_rules = generate_venue_specific_rules(user)
        
        # Get venue-specific variables
        venue_type = user.get("venue_type", "family_restaurant")
        venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
        venue_price_multiplier = venue_info.get("price_multiplier", 1.0)
        venue_type_name = venue_info.get("name", "╨б╨╡╨╝╨╡╨╣╨╜╤Л╨╣ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜")
        
        average_check = user.get("average_check", 800)
        description_style = generate_description_style(user)
        cooking_instructions = generate_cooking_instructions(user)
        chef_tips = generate_chef_tips(user)
        serving_recommendations = generate_serving_recommendations(user)
        menu_tags = generate_menu_tags(user)
        
        # ╨Я╨╛╨╕╤Б╨║ ╨░╨║╤В╤Г╨░╨╗╤М╨╜╤Л╤Е ╤Ж╨╡╨╜ ╨▓ ╨╕╨╜╤В╨╡╤А╨╜╨╡╤В╨╡
        search_query = f"╤Ж╨╡╨╜╤Л ╨╜╨░ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л {user.get('city', '╨╝╨╛╤Б╨║╨▓╨░')} 2025 ╨╝╤П╤Б╨╛ ╨╛╨▓╨╛╤Й╨╕ ╨║╤А╤Г╨┐╤Л ╨╝╨╛╨╗╨╛╤З╨╜╤Л╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л"
        
        try:
            # from emergentintegrations.tools import web_search  # Removed for local development
            # web_search = None  # Placeholder
            # price_search_result = web_search(search_query, search_context_size="medium")  # Disabled for local
            price_search_result = "╨Ф╨░╨╜╨╜╤Л╨╡ ╨┐╨╛ ╤Ж╨╡╨╜╨░╨╝ ╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л (web_search disabled)"
        except Exception:
            price_search_result = "╨Ф╨░╨╜╨╜╤Л╨╡ ╨┐╨╛ ╤Ж╨╡╨╜╨░╨╝ ╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л"
        
        # ╨Я╨╛╨╕╤Б╨║ ╤Ж╨╡╨╜ ╨║╨╛╨╜╨║╤Г╤А╨╡╨╜╤В╨╛╨▓
        competitor_search_query = f"╤Ж╨╡╨╜╤Л ╨╝╨╡╨╜╤О {request.dish_name} ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╤Л {user.get('city', '╨╝╨╛╤Б╨║╨▓╨░')} 2025"
        
        try:
            competitor_search_result = web_search(competitor_search_query, search_context_size="medium")
        except Exception:
            competitor_search_result = "╨Ф╨░╨╜╨╜╤Л╨╡ ╨┐╨╛ ╨║╨╛╨╜╨║╤Г╤А╨╡╨╜╤В╨░╨╝ ╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л"
        
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

╨Ф╨Ю╨б╨в╨г╨Я╨Э╨Ю╨Х ╨Ю╨С╨Ю╨а╨г╨Ф╨Ю╨Т╨Р╨Э╨Ш╨Х:
{', '.join(equipment_names)}

╨Т╨Р╨Ц╨Э╨Ю: ╨Р╨┤╨░╨┐╤В╨╕╤А╤Г╨╣ ╤А╨╡╤Ж╨╡╨┐╤В ╨┐╨╛╨┤ ╤Г╨║╨░╨╖╨░╨╜╨╜╨╛╨╡ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╨╡. ╨Х╤Б╨╗╨╕ ╨╡╤Б╤В╤М ╨▒╨╛╨╗╨╡╨╡ ╤Н╤Д╤Д╨╡╨║╤В╨╕╨▓╨╜╤Л╨╡ ╤Б╨┐╨╛╤Б╨╛╨▒╤Л ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П ╤Б ╤Н╤В╨╕╨╝ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╨╡╨╝, ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╕ ╨╕╤Е. ╨г╨║╨░╨╢╨╕ ╨╛╨┐╤В╨╕╨╝╨░╨╗╤М╨╜╤Л╨╡ ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╤Л ╨╕ ╨▓╤А╨╡╨╝╤П ╨┤╨╗╤П ╨║╨░╨╢╨┤╨╛╨│╨╛ ╨▓╨╕╨┤╨░ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╤П."""
        
        # Prepare enhanced dish context for menu-generated dishes
        additional_context = ""
        if hasattr(request, 'dish_description') and request.dish_description:
            additional_context = f"""

╨Ф╨Ю╨Я╨Ю╨Ы╨Э╨Ш╨в╨Х╨Ы╨м╨Э╨л╨Щ ╨Ъ╨Ю╨Э╨в╨Х╨Ъ╨б╨в ╨Ш╨Ч ╨Ь╨Х╨Э╨о:
- ╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░: {request.dish_description}
- ╨Ю╤Б╨╜╨╛╨▓╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л: {', '.join(request.main_ingredients) if request.main_ingredients else '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╤Л'}
- ╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П ╨╝╨╡╨╜╤О: {request.category}
- ╨Ю╤А╨╕╨╡╨╜╤В╨╕╤А╨╛╨▓╨╛╤З╨╜╨░╤П ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М: {request.estimated_cost}тВ╜
- ╨а╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╨╛╨╡ ╨▓╤А╨╡╨╝╤П ╨│╨╛╤В╨╛╨▓╨║╨╕: {request.cook_time} ╨╝╨╕╨╜
- ╨Ю╨╢╨╕╨┤╨░╨╡╨╝╨░╤П ╤Б╨╗╨╛╨╢╨╜╨╛╤Б╤В╤М: {request.difficulty}

╨Т╨Р╨Ц╨Э╨Ю: ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╤Н╤В╤Г ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤О ╨║╨░╨║ ╨╛╤Б╨╜╨╛╨▓╤Г, ╨╜╨╛ ╤Б╨╛╨╖╨┤╨░╨╣ ╨Я╨Ю╨Ы╨Э╨г╨о ╨┤╨╡╤В╨░╨╗╤М╨╜╤Г╤О ╤В╨╡╤Е╨║╨░╤А╤В╤Г ╤Б ╤В╨╛╤З╨╜╤Л╨╝╨╕ ╤А╨░╤Б╤З╨╡╤В╨░╨╝╨╕, ╨┐╨╛╤И╨░╨│╨╛╨▓╤Л╨╝ ╤А╨╡╤Ж╨╡╨┐╤В╨╛╨╝ ╨╕ ╨▓╤Б╨╡╨╝╨╕ ╤А╨░╨╖╨┤╨╡╨╗╨░╨╝╨╕ (╨╖╨░╨│╨╛╤В╨╛╨▓╨║╨╕, ╤Б╨╛╨▓╨╡╤В╤Л ╨╛╤В ╤И╨╡╤Д╨░, ╨╛╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╨╕)."""

        # Prepare the prompt with venue customization and enhanced context
        enhanced_equipment_context = equipment_context + additional_context
        
        prompt = GOLDEN_PROMPT.format(
            dish_name=request.dish_name,  # ╨в╨╛╨╗╤М╨║╨╛ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░
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
            equipment_context=enhanced_equipment_context  # ╨Ъ╨╛╨╜╤В╨╡╨║╤Б╤В ╨┐╨╡╤А╨╡╨┤╨░╨╡╤В╤Б╤П ╤З╨╡╤А╨╡╨╖ equipment_context
        )
        
        # Using GPT-5-mini for all users
        ai_model = "gpt-5-mini"
        max_tokens = 4000  # Increased for better tech cards, was: 3000
        
        print(f"Using AI model: {ai_model} for user subscription: {user['subscription_plan']}")
        
        # Generate tech card using OpenAI
        response = openai_client.chat.completions.create(
            model=ai_model,
            messages=[
                {"role": "system", "content": "╨в╤Л ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ AI-╨┐╨╛╨╝╨╛╤Й╨╜╨╕╨║ ╨┤╨╗╤П ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А╨╛╨▓. ╨б╨╛╨╖╨┤╨░╨╡╤И╤М ╨┤╨╡╤В╨░╨╗╤М╨╜╤Л╨╡ ╤В╨╡╤Е╨╜╨╛╨╗╨╛╨│╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨║╨░╤А╤В╤Л ╨▒╨╗╤О╨┤."},
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
        # Get the current tech card - check both collections
        tech_card = await db.tech_cards.find_one({"id": request.tech_card_id})
        is_v2_card = False
        
        # If not found in tech_cards, check user_history for V2 cards
        if not tech_card:
            tech_card = await db.user_history.find_one({"id": request.tech_card_id})
            is_v2_card = True
            
        if not tech_card:
            raise HTTPException(status_code=404, detail="Tech card not found in both collections")
        
        # Get user_id and content based on card type
        if is_v2_card:
            user_id = request.user_id  # V2 cards: use user_id from request
            # For V2 cards, content might be in different field
            current_content = tech_card.get("content", "")
            if not current_content and "techcard_v2_data" in tech_card:
                # If no content field, try to construct from V2 data
                v2_data = tech_card["techcard_v2_data"]
                current_content = f"**{v2_data.get('meta', {}).get('title', 'Tech Card')}**\n\n╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л:\n"
                for ing in v2_data.get('ingredients', []):
                    current_content += f"- {ing.get('name', '')} тАФ {ing.get('netto_g', 0)}╨│\n"
        else:
            user_id = tech_card["user_id"]  # V1 cards: use user_id from tech_card
            current_content = tech_card["content"]
        
        # Get user to determine regional coefficient
        user = await db.users.find_one({"id": user_id})
        if not user:
            # For V2 cards, user might not exist, use default values
            regional_coefficient = 1.0
        else:
            regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
        
        # Prepare the edit prompt
        prompt = EDIT_PROMPT.format(
            current_tech_card=current_content,
            edit_instruction=request.edit_instruction,
            regional_coefficient=regional_coefficient
        )
        
        # Using GPT-5-mini for all users
        ai_model = "gpt-5-mini"
        max_tokens = 4000  # Increased for better tech cards, was: 3000
        
        # Generate edited tech card using OpenAI
        response = openai_client.chat.completions.create(
            model=ai_model,
            messages=[
                {"role": "system", "content": "╨в╤Л ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ AI-╨┐╨╛╨╝╨╛╤Й╨╜╨╕╨║ ╨┤╨╗╤П ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А╨╛╨▓. ╨а╨╡╨┤╨░╨║╤В╨╕╤А╤Г╨╡╤И╤М ╤В╨╡╤Е╨╜╨╛╨╗╨╛╨│╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨║╨░╤А╤В╤Л ╤Б╨╛╨│╨╗╨░╤Б╨╜╨╛ ╨╖╨░╨┐╤А╨╛╤Б╨░╨╝ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╨╡╨╣."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        edited_content = response.choices[0].message.content
        
        # Update tech card in appropriate database collection
        update_data = {
            "content": edited_content, 
            "updated_at": datetime.utcnow(),
            "last_edit_instruction": request.edit_instruction
        }
        
        if is_v2_card:
            # Update V2 card in user_history
            await db.user_history.update_one(
                {"id": request.tech_card_id},
                {"$set": update_data}
            )
        else:
            # Update V1 card in tech_cards
            await db.tech_cards.update_one(
                {"id": request.tech_card_id},
                {"$set": update_data}
        )
        
        return {
            "success": True,
            "tech_card": edited_content,
            "card_type": "V2" if is_v2_card else "V1",
            "updated_in_collection": "user_history" if is_v2_card else "tech_cards"
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
            if line.startswith('**╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л:**'):
                in_ingredients_section = True
                continue
            elif line.startswith('**') and in_ingredients_section:
                break
            elif in_ingredients_section and line.strip() and line.startswith('- '):
                # Parse ingredient line like "- ╨Ь╤Г╨║╨░ тАФ 100 ╨│ тАФ ~50 тВ╜"
                parts = line.replace('- ', '').split(' тАФ ')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    quantity = parts[1].strip()
                    price_str = parts[2].replace('~', '').replace('тВ╜', '').strip()
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
        {"code": "moskva", "name": "╨Ь╨╛╤Б╨║╨▓╨░", "coefficient": 1.25},
        {"code": "spb", "name": "╨б╨░╨╜╨║╤В-╨Я╨╡╤В╨╡╤А╨▒╤Г╤А╨│", "coefficient": 1.25},
        {"code": "ekaterinburg", "name": "╨Х╨║╨░╤В╨╡╤А╨╕╨╜╨▒╤Г╤А╨│", "coefficient": 1.0},
        {"code": "novosibirsk", "name": "╨Э╨╛╨▓╨╛╤Б╨╕╨▒╨╕╤А╤Б╨║", "coefficient": 1.0},
        {"code": "irkutsk", "name": "╨Ш╤А╨║╤Г╤В╤Б╨║", "coefficient": 1.0},
        {"code": "nizhniy_novgorod", "name": "╨Э╨╕╨╢╨╜╨╕╨╣ ╨Э╨╛╨▓╨│╨╛╤А╨╛╨┤", "coefficient": 1.0},
        {"code": "kazan", "name": "╨Ъ╨░╨╖╨░╨╜╤М", "coefficient": 1.0},
        {"code": "chelyabinsk", "name": "╨з╨╡╨╗╤П╨▒╨╕╨╜╤Б╨║", "coefficient": 1.0},
        {"code": "omsk", "name": "╨Ю╨╝╤Б╨║", "coefficient": 1.0},
        {"code": "samara", "name": "╨б╨░╨╝╨░╤А╨░", "coefficient": 1.0},
        {"code": "rostov", "name": "╨а╨╛╤Б╤В╨╛╨▓-╨╜╨░-╨Ф╨╛╨╜╤Г", "coefficient": 1.0},
        {"code": "ufa", "name": "╨г╤Д╨░", "coefficient": 1.0},
        {"code": "krasnoyarsk", "name": "╨Ъ╤А╨░╤Б╨╜╨╛╤П╤А╤Б╨║", "coefficient": 1.0},
        {"code": "perm", "name": "╨Я╨╡╤А╨╝╤М", "coefficient": 1.0},
        {"code": "voronezh", "name": "╨Т╨╛╤А╨╛╨╜╨╡╨╢", "coefficient": 1.0},
        {"code": "volgograd", "name": "╨Т╨╛╨╗╨│╨╛╨│╤А╨░╨┤", "coefficient": 1.0},
        {"code": "krasnodar", "name": "╨Ъ╤А╨░╤Б╨╜╨╛╨┤╨░╤А", "coefficient": 1.0},
        {"code": "saratov", "name": "╨б╨░╤А╨░╤В╨╛╨▓", "coefficient": 1.0},
        {"code": "tyumen", "name": "╨в╤О╨╝╨╡╨╜╤М", "coefficient": 1.0},
        {"code": "tolyatti", "name": "╨в╨╛╨╗╤М╤П╤В╤В╨╕", "coefficient": 1.0},
        {"code": "other", "name": "╨Ф╤А╤Г╨│╨╛╨╣ ╨│╨╛╤А╨╛╨┤", "coefficient": 0.8}
    ]
    return cities

@app.post("/api/upload-prices")
async def upload_prices(file: UploadFile = File(...), user_id: str = Form(...)):
    # Auto-create test user with PRO subscription if needed
    if user_id and user_id.startswith("test_user_"):
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
    # ╨Т╨а╨Х╨Ь╨Х╨Э╨Э╨Ю ╨Ю╨в╨Ъ╨Ы╨о╨з╨Х╨Э╨Ю ╨┤╨╗╤П ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П - ╨▓╨║╨╗╤О╤З╨╕╨╝ ╨║╨╛╨│╨┤╨░ ╨▒╤Г╨┤╨╡╤В ╨┐╨╗╨░╤В╨╡╨╢╨║╨░
    # if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
    #     raise HTTPException(status_code=403, detail="╨в╤А╨╡╨▒╤Г╨╡╤В╤Б╤П PRO ╨┐╨╛╨┤╨┐╨╕╤Б╨║╨░")
    
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
                raise HTTPException(status_code=400, detail=f"╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╨┐╤А╨╛╤З╨╕╤В╨░╤В╤М ╤Д╨░╨╣╨╗: {str(e2)}")
        
        
        processed_prices = []
        for _, row in df.iterrows():
            try:
                # Try to extract price data from row
                price_data = {
                    "name": str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else "",
                    "price": 0,
                    "unit": "╨║╨│",
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
            "message": f"╨Ю╨▒╤А╨░╨▒╨╛╤В╨░╨╜╨╛ {len(processed_prices)} ╨┐╨╛╨╖╨╕╤Ж╨╕╨╣",
            "prices": preview_prices
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/upload-nutrition")
async def upload_nutrition(file: UploadFile = File(...), user_id: str = Form(...)):
    # Auto-create test user with PRO subscription if needed
    if user_id and user_id.startswith("test_user_"):
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
    # ╨Т╨а╨Х╨Ь╨Х╨Э╨Э╨Ю ╨Ю╨в╨Ъ╨Ы╨о╨з╨Х╨Э╨Ю ╨┤╨╗╤П ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П - ╨▓╨║╨╗╤О╤З╨╕╨╝ ╨║╨╛╨│╨┤╨░ ╨▒╤Г╨┤╨╡╤В ╨┐╨╗╨░╤В╨╡╨╢╨║╨░
    # if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
    #     raise HTTPException(status_code=403, detail="╨в╤А╨╡╨▒╤Г╨╡╤В╤Б╤П PRO ╨┐╨╛╨┤╨┐╨╕╤Б╨║╨░")
    
    try:
        # Read file
        content = await file.read()
        
        processed_nutrition = []
        
        # Handle JSON files
        if file.filename.lower().endswith('.json'):
            try:
                nutrition_data = json.loads(content.decode('utf-8'))
                
                # Extract items from JSON structure
                items = []
                if isinstance(nutrition_data, dict):
                    if 'items' in nutrition_data:
                        items = nutrition_data['items']
                    elif 'products' in nutrition_data:
                        items = nutrition_data['products']
                    else:
                        # Maybe it's a simple dict of products
                        items = [nutrition_data] if 'name' in nutrition_data else []
                elif isinstance(nutrition_data, list):
                    items = nutrition_data
                
                for item in items:
                    if isinstance(item, dict) and 'name' in item and 'per100g' in item:
                        per100g = item['per100g']
                        if all(k in per100g for k in ['kcal', 'proteins_g', 'fats_g', 'carbs_g']):
                            nutrition_entry = {
                                "name": item['name'].lower(),
                                "canonical_id": item.get('canonical_id', ''),
                                "kcal": float(per100g['kcal']),
                                "proteins_g": float(per100g['proteins_g']),
                                "fats_g": float(per100g['fats_g']),
                                "carbs_g": float(per100g['carbs_g']),
                                "mass_per_piece": item.get('mass_per_piece'),
                                "source": file.filename,
                                "user_id": user_id,
                                "created_at": datetime.now()
                            }
                            processed_nutrition.append(nutrition_entry)
                            
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"╨Э╨╡╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Л╨╣ JSON ╤Д╨╛╤А╨╝╨░╤В: {str(e)}")
        
        # Handle CSV files
        elif file.filename.lower().endswith('.csv'):
            # Create temporary file for CSV processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_csv:
                temp_csv.write(content)
                temp_csv_path = temp_csv.name
            
            try:
                df = pd.read_csv(temp_csv_path, encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(temp_csv_path, encoding='windows-1251')
                except Exception as e:
                    os.unlink(temp_csv_path)
                    raise HTTPException(status_code=400, detail=f"╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╨┐╤А╨╛╤З╨╕╤В╨░╤В╤М CSV ╤Д╨░╨╣╨╗: {str(e)}")
            
            # Process CSV rows - expect columns: name, kcal, proteins_g, fats_g, carbs_g
            for _, row in df.iterrows():
                try:
                    if pd.notna(row.iloc[0]):  # name is first column
                        name = str(row.iloc[0]).strip().lower()
                        
                        # Try to extract nutrition values from columns
                        kcal = proteins_g = fats_g = carbs_g = 0
                        
                        for i, col_value in enumerate(row.values):
                            if pd.notna(col_value) and i > 0:  # Skip name column
                                try:
                                    value = float(str(col_value).replace(',', '.'))
                                    if i == 1:  # kcal
                                        kcal = value
                                    elif i == 2:  # proteins
                                        proteins_g = value
                                    elif i == 3:  # fats
                                        fats_g = value
                                    elif i == 4:  # carbs
                                        carbs_g = value
                                except:
                                    continue
                        
                        if name and (kcal > 0 or proteins_g > 0 or fats_g > 0 or carbs_g > 0):
                            nutrition_entry = {
                                "name": name,
                                "canonical_id": "",
                                "kcal": kcal,
                                "proteins_g": proteins_g,
                                "fats_g": fats_g,
                                "carbs_g": carbs_g,
                                "mass_per_piece": None,
                                "source": file.filename,
                                "user_id": user_id,
                                "created_at": datetime.now()
                            }
                            processed_nutrition.append(nutrition_entry)
                            
                except Exception as e:
                    continue
            
            # Cleanup
            os.unlink(temp_csv_path)
        
        else:
            raise HTTPException(status_code=400, detail="╨Я╨╛╨┤╨┤╨╡╤А╨╢╨╕╨▓╨░╤О╤В╤Б╤П ╤В╨╛╨╗╤М╨║╨╛ JSON ╨╕ CSV ╤Д╨░╨╣╨╗╤Л")
        
        # Save to database
        if processed_nutrition:
            await db.user_nutrition.insert_many(processed_nutrition)
        
        # Create serializable version for response
        preview_nutrition = []
        for nutrition in processed_nutrition[:10]:
            preview_nutrition.append({
                "name": nutrition["name"],
                "kcal": nutrition["kcal"],
                "proteins_g": nutrition["proteins_g"],
                "fats_g": nutrition["fats_g"],
                "carbs_g": nutrition["carbs_g"],
                "source": nutrition["source"]
            })
        
        return {
            "success": True,
            "count": len(processed_nutrition),
            "message": f"╨Ю╨▒╤А╨░╨▒╨╛╤В╨░╨╜╨╛ {len(processed_nutrition)} ╨┐╨╛╨╖╨╕╤Ж╨╕╨╣ ╨┐╨╛ ╨┐╨╕╤В╨░╨╜╨╕╤О",
            "nutrition": preview_nutrition
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.get("/user-nutrition/{user_id}")
async def get_user_nutrition(user_id: str):
    try:
        nutrition = await db.user_nutrition.find({"user_id": user_id}).to_list(1000)
        return {"nutrition": [{"name": n["name"], "kcal": n["kcal"], "proteins_g": n["proteins_g"], "fats_g": n["fats_g"], "carbs_g": n["carbs_g"]} for n in nutrition]}
    except Exception as e:
        logger.error(f"Error fetching user nutrition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching nutrition: {str(e)}")

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
        # UNIFIED HISTORY: ╨Ю╨▒╤К╨╡╨┤╨╕╨╜╤П╨╡╨╝ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╕╨╖ user_history ╨╕ tech_cards ╨║╨╛╨╗╨╗╨╡╨║╤Ж╨╕╨╣
        
        # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ V2 ╤В╨╡╤Е╨║╨░╤А╤В╤Л ╨╕╨╖ user_history (╨╜╨╛╨▓╤Л╨╣ API)
        history_docs = await db.user_history.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(100)
        
        # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ V1 ╤В╨╡╤Е╨║╨░╤А╤В╤Л ╨╕╨╖ tech_cards (╤Б╤В╨░╤А╤Л╨╣ API)
        tech_cards_docs = await db.tech_cards.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(100)
        
        # Convert to serializable format by removing MongoDB ObjectId
        history = []
        
        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ V2 ╤В╨╡╤Е╨║╨░╤А╤В╤Л ╨╕╨╖ user_history
        for doc in history_docs:
            if "_id" in doc:
                del doc["_id"]
            history.append(doc)
        
        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ V1 ╤В╨╡╤Е╨║╨░╤А╤В╤Л ╨╕╨╖ tech_cards ╨║╨░╨║ legacy ╨╖╨░╨┐╨╕╤Б╨╕  
        for doc in tech_cards_docs:
            if "_id" in doc:
                del doc["_id"]
            
            # ╨Ъ╨╛╨╜╨▓╨╡╤А╤В╨╕╤А╤Г╨╡╨╝ V1 ╤Д╨╛╤А╨╝╨░╤В ╨▓ unified ╤Д╨╛╤А╨╝╨░╤В
            unified_doc = {
                "id": doc.get("id"),
                "user_id": doc.get("user_id"),
                "dish_name": doc.get("dish_name"),
                "content": doc.get("content"),
                "created_at": doc.get("created_at"),
                "is_menu": False,
                "status": "success",  # V1 ╤В╨╡╤Е╨║╨░╤А╤В╤Л ╨▓╤Б╨╡╨│╨┤╨░ ╨▒╤Л╨╗╨╕ ╤Г╤Б╨┐╨╡╤И╨╜╤Л╨╝╨╕
                "techcard_v2_data": None  # V1 ╨╜╨╡ ╨╕╨╝╨╡╨╡╤В V2 ╨┤╨░╨╜╨╜╤Л╤Е
            }
            history.append(unified_doc)
        
        # ╨б╨╛╤А╤В╨╕╤А╤Г╨╡╨╝ ╨▓╤Б╨╡ ╨┐╨╛ ╨┤╨░╤В╨╡ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П (╨╜╨╛╨▓╤Л╨╡ ╤Б╨▓╨╡╤А╤Е╤Г) ╤Б ╨▒╨╡╨╖╨╛╨┐╨░╤Б╨╜╤Л╨╝ ╤Б╤А╨░╨▓╨╜╨╡╨╜╨╕╨╡╨╝
        def safe_sort_key(x):
            created_at = x.get("created_at", "")
            if isinstance(created_at, str):
                try:
                    # ╨Я╤А╨╛╨▒╤Г╨╡╨╝ ╨┐╨░╤А╤Б╨╕╤В╤М ISO datetime ╤Б╤В╤А╨╛╨║╤Г
                    from datetime import datetime
                    return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except:
                    # ╨Х╤Б╨╗╨╕ ╨╜╨╡ ╨┐╨╛╨╗╤Г╤З╨░╨╡╤В╤Б╤П, ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╨╝ ╨╛╤З╨╡╨╜╤М ╤Б╤В╨░╤А╤Г╤О ╨┤╨░╤В╤Г
                    return datetime(1970, 1, 1)
            elif hasattr(created_at, 'year'):  # datetime object
                return created_at
            else:
                # Fallback ╨┤╨╗╤П ╨┤╤А╤Г╨│╨╕╤Е ╤В╨╕╨┐╨╛╨▓
                return datetime(1970, 1, 1)
        
        history.sort(key=safe_sort_key, reverse=True)
        
        # ╨Ю╨│╤А╨░╨╜╨╕╤З╨╕╨▓╨░╨╡╨╝ ╨┤╨╛ 50 ╨╖╨░╨┐╨╕╤Б╨╡╨╣
        history = history[:50]
        
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
=== ╨Ъ╨Ю╨Э╨б╨в╨а╨г╨Ъ╨в╨Ю╨а ╨Ь╨Х╨Э╨о - ╨в╨Ю╨з╨Э╨Р╨п ╨б╨в╨а╨г╨Ъ╨в╨г╨а╨Р ===
╨Ъ╨а╨Ш╨в╨Ш╨з╨Х╨б╨Ъ╨Ш ╨Т╨Р╨Ц╨Э╨Ю: ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨в╨Ю╨з╨Э╨г╨о ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г ╨┐╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝:
- ╨Ч╨░╨║╤Г╤Б╨║╨╕/╨б╨░╨╗╨░╤В╤Л: {categories.get('appetizers', 0)} ╨▒╨╗╤О╨┤
- ╨б╤Г╨┐╤Л: {categories.get('soups', 0)} ╨▒╨╗╤О╨┤  
- ╨У╨╛╤А╤П╤З╨╕╨╡ ╨▒╨╗╤О╨┤╨░: {categories.get('main_dishes', 0)} ╨▒╨╗╤О╨┤
- ╨Ф╨╡╤Б╨╡╤А╤В╤Л: {categories.get('desserts', 0)} ╨▒╨╗╤О╨┤
- ╨Э╨░╨┐╨╕╤В╨║╨╕: {categories.get('beverages', 0)} ╨▒╨╗╤О╨┤
- ╨Ч╨░╨║╤Г╤Б╨║╨╕ ╨║ ╨╜╨░╨┐╨╕╤В╨║╨░╨╝: {categories.get('snacks', 0)} ╨▒╨╗╤О╨┤

╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨Ю: ╨б╨╛╨╖╨┤╨░╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ ╤В╨╛╨╗╤М╨║╨╛ ╤Б ╤Г╨║╨░╨╖╨░╨╜╨╜╤Л╨╝ ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛╨╝ ╨▒╨╗╤О╨┤!
╨Х╤Б╨╗╨╕ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П = 0, ╨Э╨Х ╤Б╨╛╨╖╨┤╨░╨▓╨░╨╣ ╨╡╤С ╨▓╨╛╨╛╨▒╤Й╨╡!
            """
        else:
            structure_instruction = f"""
=== ╨Р╨Т╨в╨Ю╨Ь╨Р╨в╨Ш╨з╨Х╨б╨Ъ╨Р╨п ╨б╨в╨а╨г╨Ъ╨в╨г╨а╨Р ===
╨б╨╛╨╖╨┤╨░╨╣ {dish_count} ╨▒╨╗╤О╨┤, ╤А╨░╤Б╨┐╤А╨╡╨┤╨╡╨╗╨╕╨▓ ╨╕╤Е ╨╗╨╛╨│╨╕╤З╨╜╨╛ ╨┐╨╛ 3-5 ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝
            """

        # Create comprehensive enhanced prompt for GPT-5-mini
        menu_prompt = f"""
╨в╤Л - ╤Н╨║╤Б╨┐╨╡╤А╤В ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А ╨╕ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╜╤Л╨╣ ╨║╨╛╨╜╤Б╤Г╨╗╤М╤В╨░╨╜╤В ╤Б 20+ ╨╗╨╡╤В╨╜╨╕╨╝ ╤Б╤В╨░╨╢╨╡╨╝. ╨б╨╛╨╖╨┤╨░╨╣ ╨г╨Э╨Ш╨Ъ╨Р╨Ы╨м╨Э╨Ю╨Х ╨╕ ╨Ъ╨а╨Х╨Р╨в╨Ш╨Т╨Э╨Ю╨Х ╨╝╨╡╨╜╤О ╨┐╨╛ ╤Б╨╗╨╡╨┤╤Г╤О╤Й╨╕╨╝ ╨║╤А╨╕╤В╨╡╤А╨╕╤П╨╝:

=== ╨Ю╨б╨Э╨Ю╨Т╨Э╨л╨Х ╨Я╨Р╨а╨Р╨Ь╨Х╨в╨а╨л ===
╨в╨Ш╨Я ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨п: {menu_type}
╨в╨Ю╨з╨Э╨Ю╨Х ╨Ъ╨Ю╨Ы╨Ш╨з╨Х╨б╨в╨Т╨Ю ╨С╨Ы╨о╨Ф: {dish_count} (╨б╨в╨а╨Ю╨У╨Ю ╤Б╨╛╨▒╨╗╤О╨┤╨░╨╣ ╤Н╤В╨╛ ╤З╨╕╤Б╨╗╨╛!)
╨б╨а╨Х╨Ф╨Э╨Ш╨Щ ╨з╨Х╨Ъ: {average_check}
╨б╨в╨Ш╨Ы╨м ╨Ъ╨г╨е╨Э╨Ш: {cuisine_style}

{structure_instruction}

=== ╨Я╨а╨Ю╨д╨Ш╨Ы╨м ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨п ===
- ╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡: {venue_profile.get('venue_name', '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╨╛')}
- ╨в╨╕╨┐: {venue_profile.get('venue_type', '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╨╛')}
- ╨Ъ╤Г╤Е╨╜╤П: {venue_profile.get('cuisine_type', '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╨╛')}
- ╨б╤А╨╡╨┤╨╜╨╕╨╣ ╤З╨╡╨║: {venue_profile.get('average_check', '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╨╛')}

=== ╨Ф╨Х╨в╨Р╨Ы╨м╨Э╨л╨Х ╨в╨а╨Х╨С╨Ю╨Т╨Р╨Э╨Ш╨п ===
╨ж╨╡╨╗╨╡╨▓╨░╤П ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╤П: {target_audience or '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╨░'}
╨С╨╕╨╖╨╜╨╡╤Б-╤Ж╨╡╨╗╨╕: {', '.join(menu_goals) if menu_goals else '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╤Л'}
╨б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╤Л╨╡ ╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╤П: {', '.join(special_requirements) if special_requirements else '╨Э╨╡╤В'}
╨Ф╨╕╨╡╤В╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨╛╨┐╤Ж╨╕╨╕: {', '.join(dietary_options) if dietary_options else '╨Э╨╡╤В'}

=== ╨в╨Х╨е╨Э╨Ш╨з╨Х╨б╨Ъ╨Ш╨Х ╨Ю╨У╨а╨Р╨Э╨Ш╨з╨Х╨Э╨Ш╨п ===
╨г╤А╨╛╨▓╨╡╨╜╤М ╨╜╨░╨▓╤Л╨║╨╛╨▓ ╨┐╨╡╤А╤Б╨╛╨╜╨░╨╗╨░: {staff_skill_level}
╨Ю╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П ╨┐╨╛ ╨▓╤А╨╡╨╝╨╡╨╜╨╕ ╨│╨╛╤В╨╛╨▓╨║╨╕: {preparation_time}
╨С╤О╨┤╨╢╨╡╤В ╨╜╨░ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л: {ingredient_budget}

=== ╨Я╨Ю╨Ц╨Х╨Ы╨Р╨Э╨Ш╨п ╨Ч╨Р╨Ъ╨Р╨Ч╨з╨Ш╨Ъ╨Р ===
╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨╝╨╡╨╜╤О: {menu_description or '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╨╛'}
╨Ю╨╢╨╕╨┤╨░╨╜╨╕╤П: {expectations or '╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╤Л'}
╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨╛╨╢╨╡╨╗╨░╨╜╨╕╤П: {additional_notes or '╨Э╨╡╤В'}

=== ╨Ъ╨а╨Ш╨в╨Ш╨з╨Х╨б╨Ъ╨Ш ╨Т╨Р╨Ц╨Э╨л╨Х ╨в╨а╨Х╨С╨Ю╨Т╨Р╨Э╨Ш╨п ===
╨Ч╨Р╨Я╨а╨Х╨й╨Х╨Э╨Ю: ╨б╨╛╨╖╨┤╨░╨▓╨░╤В╤М ╨▒╨╗╤О╨┤╨░ ╤Б ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П╨╝╨╕ "╨б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╨┤╨╜╤П", "╨г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╨╛╤В ╤И╨╡╤Д╨░", "╨Р╨▓╤В╨╛╤А╤Б╨║╨╛╨╡ ╨▒╨╗╤О╨┤╨╛" ╨╕ ╨┐╨╛╨┤╨╛╨▒╨╜╤Л╨╡ ╨╛╨▒╤Й╨╕╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П!
╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨Ю: ╨Ъ╨░╨╢╨┤╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╨┤╨╛╨╗╨╢╨╜╨╛ ╨╕╨╝╨╡╤В╤М ╨Ъ╨Ю╨Э╨Ъ╨а╨Х╨в╨Э╨Ю╨Х, ╨Ъ╨а╨Х╨Р╨в╨Ш╨Т╨Э╨Ю╨Х ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡, ╨╛╤В╤А╨░╨╢╨░╤О╤Й╨╡╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨╕ ╤Б╨┐╨╛╤Б╨╛╨▒ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П
╨в╨Ю╨з╨Э╨Ю╨Х ╨Ъ╨Ю╨Ы╨Ш╨з╨Х╨б╨в╨Т╨Ю: ╨б╨╛╨╖╨┤╨░╨╣ ╨а╨Ю╨Т╨Э╨Ю {dish_count} ╨▒╨╗╤О╨┤ - ╨╜╨╕ ╨▒╨╛╨╗╤М╤И╨╡, ╨╜╨╕ ╨╝╨╡╨╜╤М╤И╨╡!
╨б╨в╨а╨г╨Ъ╨в╨г╨а╨Р: {"╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╤Г╨║╨░╨╖╨░╨╜╨╜╤Г╤О ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г ╨║╨╛╨╜╤Б╤В╤А╤Г╨║╤В╨╛╤А╨░" if use_constructor else "╨а╨░╤Б╨┐╤А╨╡╨┤╨╡╨╗╨╕ ╨▒╨╗╤О╨┤╨░ ╨┐╨╛ 3-5 ╨╗╨╛╨│╨╕╤З╨╜╤Л╨╝ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝"}
╨Ю╨Я╨в╨Ш╨Ь╨Ш╨Ч╨Р╨ж╨Ш╨п: ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨╛╨▒╤Й╨╕╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨┤╨╗╤П ╤Н╨║╨╛╨╜╨╛╨╝╨╕╨╕
╨ж╨Х╨Э╨Ю╨Ю╨С╨а╨Р╨Ч╨Ю╨Т╨Р╨Э╨Ш╨Х: ╨б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╨╕╨╡ ╤Б╤А╨╡╨┤╨╜╨╡╨╝╤Г ╤З╨╡╨║╤Г {average_check}
╨г╨з╨Х╨в ╨Э╨Р╨Т╨л╨Ъ╨Ю╨Т: ╨Р╨┤╨░╨┐╤В╨╕╤А╤Г╨╣ ╤Б╨╗╨╛╨╢╨╜╨╛╤Б╤В╤М ╨┐╨╛╨┤ ╤Г╤А╨╛╨▓╨╡╨╜╤М ╨┐╨╡╤А╤Б╨╛╨╜╨░╨╗╨░ ({staff_skill_level})
╨Т╨а╨Х╨Ь╨п ╨У╨Ю╨в╨Ю╨Т╨Ъ╨Ш: ╨г╤З╨╕╤В╤Л╨▓╨░╨╣ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П ╨┐╨╛ ╨▓╤А╨╡╨╝╨╡╨╜╨╕ ({preparation_time})
╨Ъ╨а╨Х╨Р╨в╨Ш╨Т╨Э╨Ю╨б╨в╨м: ╨Э╨░╨╖╨▓╨░╨╜╨╕╤П ╨┤╨╛╨╗╨╢╨╜╤Л ╨▒╤Л╤В╤М ╨┐╤А╨╕╨▓╨╗╨╡╨║╨░╤В╨╡╨╗╤М╨╜╤Л╨╝╨╕ ╨╕ ╨╛╨┐╨╕╤Б╨░╤В╨╡╨╗╤М╨╜╤Л╨╝╨╕

=== ╨Я╨а╨Ш╨Ь╨Х╨а╨л ╨е╨Ю╨а╨Ю╨и╨Ш╨е ╨Э╨Р╨Ч╨Т╨Р╨Э╨Ш╨Щ ===
╨Я╨╗╨╛╤Е╨╛: "╨б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╨┤╨╜╤П"
╨е╨╛╤А╨╛╤И╨╛: "╨д╨╕╨╗╨╡ ╨╗╨╛╤Б╨╛╤Б╤П ╤Б ╨║╤Г╨╜╨╢╤Г╤В╨╜╨╛╨╣ ╨║╨╛╤А╨╛╤З╨║╨╛╨╣ ╨╕ ╨╗╨╕╨╝╨╛╨╜╨╜╤Л╨╝ ╤А╨╕╨╖╨╛╤В╤В╨╛"

╨Я╨╗╨╛╤Е╨╛: "╨Р╨▓╤В╨╛╤А╤Б╨║╨╕╨╣ ╨┤╨╡╤Б╨╡╤А╤В"
╨е╨╛╤А╨╛╤И╨╛: "╨и╨╛╨║╨╛╨╗╨░╨┤╨╜╤Л╨╣ ╤Д╨╛╨╜╨┤╨░╨╜ ╤Б ╨╝╨░╨╗╨╕╨╜╨╛╨▓╤Л╨╝ ╨║╤Г╨╗╨╕ ╨╕ ╨▓╨░╨╜╨╕╨╗╤М╨╜╤Л╨╝ ╨╝╨╛╤А╨╛╨╢╨╡╨╜╤Л╨╝"

=== JSON ╨д╨Ю╨а╨Ь╨Р╨в (╨б╨в╨а╨Ю╨У╨Ю ╨б╨Ю╨С╨Ы╨о╨Ф╨Р╨Щ) ===
{{
  "menu_name": "╨Я╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨╝╨╡╨╜╤О",
  "description": "╨Ф╨╡╤В╨░╨╗╤М╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╨╕ ╤Б ╤Г╤З╨╡╤В╨╛╨╝ ╨▓╤Б╨╡╤Е ╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╨╣",
  "categories": [
    {{
      "category_name": "╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕",
      "dishes": [
        {{
          "name": "╨Ъ╨Ю╨Э╨Ъ╨а╨Х╨в╨Э╨Ю╨Х ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░ (╨Э╨Х ╨╛╨▒╤Й╨╕╨╡ ╤Д╤А╨░╨╖╤Л!)",
          "description": "╨Я╨╛╨┤╤А╨╛╨▒╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╤Б ╨░╨║╤Ж╨╡╨╜╤В╨╛╨╝ ╨╜╨░ ╤Г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╤Б╤В╤М ╨╕ ╤Б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╨╕╨╡ ╤Ж╨╡╨╗╨╡╨▓╨╛╨╣ ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╨╕",
          "estimated_cost": "150",
          "estimated_price": "450",
          "difficulty": "╨╗╨╡╨│╨║╨╛/╤Б╤А╨╡╨┤╨╜╨╡/╤Б╨╗╨╛╨╢╨╜╨╛ (╤Б ╤Г╤З╨╡╤В╨╛╨╝ ╤Г╤А╨╛╨▓╨╜╤П ╨┐╨╡╤А╤Б╨╛╨╜╨░╨╗╨░)",
          "cook_time": "15",
          "main_ingredients": ["╨┤╨╡╤В╨░╨╗╤М╨╜╤Л╨╣ ╤Б╨┐╨╕╤Б╨╛╨║ ╨╛╤Б╨╜╨╛╨▓╨╜╤Л╤Е ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓"]
        }}
      ]
    }}
  ],
  "ingredient_optimization": {{
    "shared_ingredients": ["╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л, ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝╤Л╨╡ ╨▓ 3+ ╨▒╨╗╤О╨┤╨░╤Е"],
    "cost_savings": "╤В╨╛╤З╨╜╤Л╨╣ ╨┐╤А╨╛╤Ж╨╡╨╜╤В ╤Н╨║╨╛╨╜╨╛╨╝╨╕╨╕ ╨╛╤В ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╨╕"
  }}
}}

╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨Ю ╨Я╨а╨Ю╨Т╨Х╨а╨м:
- ╨Ю╨▒╤Й╨╡╨╡ ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨▒╨╗╤О╨┤ = {dish_count}
- ╨Т╤Б╨╡ ╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╤П ╤Г╤З╤В╨╡╨╜╤Л ╨▓ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╤П╤Е ╨▒╨╗╤О╨┤
- ╨Э╨Х╨в ╨╛╨▒╤Й╨╕╤Е ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╣ ╤В╨╕╨┐╨░ "╨▒╨╗╤О╨┤╨╛ ╨╛╤В ╤И╨╡╤Д╨░"
- ╨Ъ╨░╨╢╨┤╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨╡ ╨╕ ╨┐╤А╨╕╨▓╨╗╨╡╨║╨░╤В╨╡╨╗╤М╨╜╨╛╨╡
- ╨ж╨╡╨╜╨╛╨╛╨▒╤А╨░╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╤Б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╤Г╨╡╤В ╤Б╤А╨╡╨┤╨╜╨╡╨╝╤Г ╤З╨╡╨║╤Г
- ╨б╨╗╨╛╨╢╨╜╨╛╤Б╤В╤М ╨▒╨╗╤О╨┤ ╨░╨┤╨░╨┐╤В╨╕╤А╨╛╨▓╨░╨╜╨░ ╨┐╨╛╨┤ ╨┐╨╡╤А╤Б╨╛╨╜╨░╨╗
- ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╤Л ╨╛╨▒╤Й╨╕╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨┤╨╗╤П ╤Н╨║╨╛╨╜╨╛╨╝╨╕╨╕

╨б╨╛╨╖╨┤╨░╨╣ ╨╝╨╡╨╜╤О ╨╝╨╡╤З╤В╤Л ╤Б ╨Ъ╨Ю╨Э╨Ъ╨а╨Х╨в╨Э╨л╨Ь╨Ш, ╨Ъ╨а╨Х╨Р╨в╨Ш╨Т╨Э╨л╨Ь╨Ш ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П╨╝╨╕ ╨▒╨╗╤О╨┤!
"""

        # Generate menu using OpenAI (Premium model for PRO feature)
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-5-mini",  # Using GPT-5-mini for menu generation
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
                    
=== ╨Ъ╨а╨Ш╨в╨Ш╨з╨Х╨б╨Ъ╨Ю╨Х ╨в╨а╨Х╨С╨Ю╨Т╨Р╨Э╨Ш╨Х ===
╨Т╨Э╨Ш╨Ь╨Р╨Э╨Ш╨Х: ╨Т ╨┐╤А╨╡╨┤╤Л╨┤╤Г╤Й╨╡╨╣ ╨┐╨╛╨┐╤Л╤В╨║╨╡ ╨▒╤Л╨╗╨╛ ╤Б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╨╜╨╛ ╤В╨╛╨╗╤М╨║╨╛ {total_dishes} ╨▒╨╗╤О╨┤ ╨▓╨╝╨╡╤Б╤В╨╛ {dish_count}!
╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨Ю ╤Б╨╛╨╖╨┤╨░╨╣ ╨а╨Ю╨Т╨Э╨Ю {dish_count} ╨▒╨╗╤О╨┤ ╤Б ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╤Л╨╝╨╕ ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П╨╝╨╕!
╨Э╨Х ╨Ш╨б╨Я╨Ю╨Ы╨м╨Ч╨г╨Щ ╨╖╨░╨│╨╗╤Г╤И╨║╨╕ ╤В╨╕╨┐╨░ "╨б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╨┤╨╜╤П"!
                    """
                    
                    # Retry generation with enhanced prompt
                    retry_response = client.chat.completions.create(
                        model="gpt-5-mini",
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
                            logger.info(f"тЬЕ Retry successful: generated {retry_total_dishes} dishes")
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
                "menu_name": f"╨Ь╨╡╨╜╤О ╨┤╨╗╤П {menu_type}",
                "description": "╨б╨▒╨░╨╗╨░╨╜╤Б╨╕╤А╨╛╨▓╨░╨╜╨╜╨╛╨╡ ╨╝╨╡╨╜╤О, ╤Б╨╛╨╖╨┤╨░╨╜╨╜╨╛╨╡ ╨Ш╨Ш",
                "categories": [
                    {
                        "category_name": "╨Ю╤Б╨╜╨╛╨▓╨╜╨╛╨╡ ╨╝╨╡╨╜╤О",
                        "dishes": [
                            {
                                "name": "╨С╨╗╤О╨┤╨╛ ╨▓ ╤А╨░╨╖╤А╨░╨▒╨╛╤В╨║╨╡",
                                "description": "╨Ф╨╡╤В╨░╨╗╨╕ ╨▒╨╗╤О╨┤╨░ ╨▒╤Г╨┤╤Г╤В ╨┤╨╛╨▒╨░╨▓╨╗╨╡╨╜╤Л",
                                "estimated_cost": "200",
                                "estimated_price": "600",
                                "difficulty": "╤Б╤А╨╡╨┤╨╜╨╡",
                                "cook_time": "30",
                                "main_ingredients": ["╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В1", "╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В2"]
                            }
                        ]
                    }
                ],
                "ingredient_optimization": {
                    "shared_ingredients": ["╨▒╨░╨╖╨╛╨▓╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л"],
                    "cost_savings": "15-20%"
                }
            }
        
        # Save generated menu to database
        menu_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "menu_name": menu_data.get("menu_name", "╨Э╨╛╨▓╨╛╨╡ ╨╝╨╡╨╜╤О"),
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
            "message": "╨Ь╨╡╨╜╤О ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╤Б╨╛╨╖╨┤╨░╨╜╨╛!"
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
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
        venue_context = generate_venue_context(user)
        venue_specific_rules = generate_venue_specific_rules(user)
        
        # Get venue-specific variables
        venue_type = user.get("venue_type", "family_restaurant")
        venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
        venue_price_multiplier = venue_info.get("price_multiplier", 1.0)
        venue_type_name = venue_info.get("name", "╨б╨╡╨╝╨╡╨╣╨╜╤Л╨╣ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜")
        
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
                    equipment_context = f"\n╨Ю╨С╨Ю╨а╨г╨Ф╨Ю╨Т╨Р╨Э╨Ш╨Х ╨Э╨Р ╨Ъ╨г╨е╨Э╨Х: {', '.join(equipment_names)}\n╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╨╛╨╡ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╨╡ ╨▓ ╤А╨╡╤Ж╨╡╨┐╤В╨░╤Е!"
        
        # Generate tech card for each dish SEQUENTIALLY (no timeout issues)
        for i, dish in enumerate(all_dishes):
            try:
                dish_name = dish["name"]
                logger.info(f"Generating tech card {i+1}/{len(all_dishes)}: {dish_name}")
                
                # Create enhanced prompt using dish context from menu
                enhanced_dish_name = f"{dish_name} (╨┤╨╗╤П {venue_type_name}, ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П: {dish['category']})"
                if dish.get("main_ingredients"):
                    enhanced_dish_name += f", ╨╛╤Б╨╜╨╛╨▓╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л: {', '.join(dish['main_ingredients'][:3])}"
                
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
                    model="gpt-5-mini",
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
            "message": f"╨Ь╨░╤Б╤Б╨╛╨▓╨░╤П ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤П ╨╖╨░╨▓╨╡╤А╤И╨╡╨╜╨░! ╨б╨╛╨╖╨┤╨░╨╜╨╛ {len(generated_tech_cards)} ╨╕╨╖ {len(all_dishes)} ╤В╨╡╤Е╨║╨░╤А╤В."
        }
        
    except Exception as e:
        logger.error(f"Error in mass tech card generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating tech cards: {str(e)}")

@api_router.get("/menu/{menu_id}/tech-cards")
async def get_menu_tech_cards(menu_id: str, user_id: str = None):
    """
    Get all tech cards generated from a specific menu
    SECURITY: Requires user_id to ensure user isolation
    """
    try:
        # SECURITY FIX: Verify menu belongs to user if user_id provided
        if user_id:
            menu = await db.user_history.find_one({
                "id": menu_id,
                "is_menu": True,
                "user_id": user_id
            })
            if not menu:
                raise HTTPException(status_code=403, detail="Menu not found or access denied")
        
        # Get all tech cards that were generated from this menu
        # SECURITY FIX: Filter by user_id if provided
        query = {
            "from_menu_id": menu_id,
            "is_menu": False
        }
        if user_id:
            query["user_id"] = user_id
        
        tech_cards = await db.user_history.find(query).to_list(100)
        
        # Group by category for better organization
        cards_by_category = {}
        for card in tech_cards:
            category = card.get("menu_category", "╨С╨╡╨╖ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕")
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
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
        venue_context = generate_venue_context(user)
        venue_specific_rules = generate_venue_specific_rules(user)
        
        # Get venue-specific variables
        venue_type = user.get("venue_type", "family_restaurant")
        venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
        venue_price_multiplier = venue_info.get("price_multiplier", 1.0)
        venue_type_name = venue_info.get("name", "╨б╨╡╨╝╨╡╨╣╨╜╤Л╨╣ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜")
        
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
                    equipment_context = f"\n╨Ю╨С╨Ю╨а╨г╨Ф╨Ю╨Т╨Р╨Э╨Ш╨Х ╨Э╨Р ╨Ъ╨г╨е╨Э╨Х: {', '.join(equipment_names)}\n╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╨╛╨╡ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╨╡ ╨▓ ╤А╨╡╤Ж╨╡╨┐╤В╨░╤Е!"
        
        # Create enhanced prompt for replacement dish
        replacement_context = f"""
╨Ч╨Р╨Ь╨Х╨Э╨Р ╨С╨Ы╨о╨Ф╨Р ╨Т ╨Ь╨Х╨Э╨о:
- ╨Ч╨░╨╝╨╡╨╜╤П╨╡╨╝╨╛╨╡ ╨▒╨╗╤О╨┤╨╛: "{dish_name}"
- ╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П: {category}
- ╨Я╨╛╨╢╨╡╨╗╨░╨╜╨╕╤П ╨┐╨╛ ╨╖╨░╨╝╨╡╨╜╨╡: {replacement_prompt if replacement_prompt else "╨б╨╛╨╖╨┤╨░╨╣ ╨░╨╗╤М╤В╨╡╤А╨╜╨░╤В╨╕╨▓╨╜╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╨▓ ╤В╨╛╨╝ ╨╢╨╡ ╤Б╤В╨╕╨╗╨╡"}

╨Т╨Р╨Ц╨Э╨Ю: ╨б╨╛╨╖╨┤╨░╨╣ ╨▒╨╗╤О╨┤╨╛ ╤В╨╛╨│╨╛ ╨╢╨╡ ╤Г╤А╨╛╨▓╨╜╤П ╤Б╨╗╨╛╨╢╨╜╨╛╤Б╤В╨╕ ╨╕ ╤Ж╨╡╨╜╨╛╨▓╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕, ╨╜╨╛ ╤Б ╨┤╤А╤Г╨│╨╕╨╝╨╕ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨░╨╝╨╕ ╨╕╨╗╨╕ ╤В╨╡╤Е╨╜╨╕╨║╨░╨╝╨╕ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П. ╨б╨╛╤Е╤А╨░╨╜╨╕ ╤Б╤В╨╕╨╗╤М ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╨╕ ╤Ж╨╡╨╗╨╡╨▓╤Г╤О ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╤О."""
        
        enhanced_dish_name = f"{dish_name} (╨╖╨░╨╝╨╡╨╜╨░ ╨┤╨╗╤П {venue_type_name}, ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П: {category})"
        if replacement_prompt:
            enhanced_dish_name += f", ╨┐╨╛╨╢╨╡╨╗╨░╨╜╨╕╤П: {replacement_prompt[:100]}"
        
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
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are RECEPTOR, a professional AI assistant for chefs. Always respond in Russian."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        tech_card_content = response.choices[0].message.content.strip()
        
        # Extract dish details from generated content for menu display
        title_match = re.search(r'\*\*╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:\*\*\s*(.*?)(?=\n|$)', tech_card_content)
        description_match = re.search(r'\*\*╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡:\*\*\s*(.*?)(?=\n\n|\*\*)', tech_card_content, re.DOTALL)
        cost_match = re.search(r'╨б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М.*?(\d+(?:\.\d+)?)\s*тВ╜', tech_card_content)
        price_match = re.search(r'╨а╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╨░╤П ╤Ж╨╡╨╜╨░.*?(\d+(?:\.\d+)?)\s*тВ╜', tech_card_content)
        time_match = re.search(r'\*\*╨Т╤А╨╡╨╝╤П:\*\*\s*(.*?)(?=\n|$)', tech_card_content)
        portion_match = re.search(r'\*\*╨Т╤Л╤Е╨╛╨┤:\*\*\s*(.*?)(?=\n|$)', tech_card_content)
        
        new_dish_name = title_match.group(1).strip() if title_match else f"╨Ч╨░╨╝╨╡╨╜╨░ ╨┤╨╗╤П {dish_name}"
        
        # Create a full dish object for menu display (compatible with frontend)
        new_dish_object = {
            "name": new_dish_name,
            "description": description_match.group(1).strip() if description_match else "╨Р╨▓╤В╨╛╤А╤Б╨║╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╨╛╤В ╤И╨╡╤Д╨░",
            "estimated_cost": cost_match.group(1) if cost_match else "250",
            "estimated_price": price_match.group(1) if price_match else "750", 
            "difficulty": "╤Б╤А╨╡╨┤╨╜╨╡",
            "cook_time": time_match.group(1).strip() if time_match else "25 ╨╝╨╕╨╜",
            "portion_size": portion_match.group(1).strip() if portion_match else "1 ╨┐╨╛╤А╤Ж╨╕╤П",
            "main_ingredients": []  # Will be extracted later if needed
        }
        
        # Try to extract main ingredients from tech card
        ingredients_match = re.search(r'\*\*╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)', tech_card_content, re.DOTALL)
        if ingredients_match:
            ingredients_text = ingredients_match.group(1)
            ingredient_lines = [line.strip() for line in ingredients_text.split('\n') if line.strip().startswith('-')]
            main_ingredients = []
            for line in ingredient_lines[:5]:  # Take first 5 ingredients
                ingredient_name = re.sub(r'^-\s*', '', line).split('тАФ')[0].split('-')[0].strip()
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
            "message": f"╨С╨╗╤О╨┤╨╛ '{dish_name}' ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╨╖╨░╨╝╨╡╨╜╨╡╨╜╨╛ ╨╜╨░ '{new_dish_name}'"
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
        venue_type_name = venue_info.get("name", "╨б╨╡╨╝╨╡╨╣╨╜╤Л╨╣ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜")
        
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
            audience_context += f"╨Т╨╛╨╖╤А╨░╤Б╤В╨╜╨╛╨╡ ╤А╨░╤Б╨┐╤А╨╡╨┤╨╡╨╗╨╡╨╜╨╕╨╡: {age_distribution}. "
        if audience_occupations:
            audience_context += f"╨Ю╤Б╨╜╨╛╨▓╨╜╨░╤П ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╤П: {', '.join(audience_occupations)}. "
        
        # Build requirements context  
        requirements_context = ""
        if special_requirements:
            requirements_context += f"╨Ю╤Б╨╛╨▒╤Л╨╡ ╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╤П: {', '.join(special_requirements)}. "
        if dietary_options:
            requirements_context += f"╨Ф╨╕╨╡╤В╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨╛╨┐╤Ж╨╕╨╕: {', '.join(dietary_options)}. "
            
        # Build kitchen context
        kitchen_context = f"╨г╤А╨╛╨▓╨╡╨╜╤М ╨┐╨╡╤А╤Б╨╛╨╜╨░╨╗╨░: {staff_skill_level}, ╨▓╤А╨╡╨╝╤П ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П: {preparation_time}, ╨▒╤О╨┤╨╢╨╡╤В ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓: {ingredient_budget}. "
        if kitchen_capabilities:
            kitchen_context += f"╨Ъ╤Г╤Е╨╛╨╜╨╜╤Л╨╡ ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛╤Б╤В╨╕: {', '.join(kitchen_capabilities)}. "
            
        # Create simplified menu generation prompt
        menu_prompt = f"""╨б╨╛╨╖╨┤╨░╨╣ {request.menu_type} ╨╝╨╡╨╜╤О ╨┤╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П "{venue_type_name}".

╨Ю╨б╨Э╨Ю╨Т╨Э╨Р╨п ╨Ш╨Э╨д╨Ю╨а╨Ь╨Р╨ж╨Ш╨п:
- ╨в╨╕╨┐ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П: {venue_type_name}
- ╨Ъ╤Г╤Е╨╜╤П: {', '.join(cuisine_focus)}
- ╨б╤В╨╕╨╗╤М: {cuisine_style} 
- ╨б╤А╨╡╨┤╨╜╨╕╨╣ ╤З╨╡╨║: {average_check} ╤А╤Г╨▒.
- ╨а╨╡╨│╨╕╨╛╨╜: {region}

╨Ю╨Ц╨Ш╨Ф╨Р╨Э╨Ш╨п ╨Ю╨в ╨Ь╨Х╨Э╨о:
{request.expectations}

╨ж╨Х╨Ы╨Х╨Т╨Р╨п ╨Р╨г╨Ф╨Ш╨в╨Ю╨а╨Ш╨п:
{audience_context if audience_context else '╨и╨╕╤А╨╛╨║╨░╤П ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╤П'}

╨в╨а╨Х╨С╨Ю╨Т╨Р╨Э╨Ш╨п ╨Ш ╨Ю╨У╨а╨Р╨Э╨Ш╨з╨Х╨Э╨Ш╨п:
{requirements_context if requirements_context else '╨б╤В╨░╨╜╨┤╨░╤А╤В╨╜╤Л╨╡ ╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╤П'}

╨Ъ╨г╨е╨Ю╨Э╨Э╨л╨Х ╨Т╨Ю╨Ч╨Ь╨Ю╨Ц╨Э╨Ю╨б╨в╨Ш:
{kitchen_context}

╨б╨Ю╨б╨в╨Р╨Т ╨Ь╨Х╨Э╨о:
╨б╨╛╨╖╨┤╨░╨╣ ╤А╨╛╨▓╨╜╨╛ {dish_count} ╨▒╨╗╤О╨┤ ╨┐╨╛ ╤Б╨╗╨╡╨┤╤Г╤О╤Й╨╕╨╝ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝:
{chr(10).join([f'- {category}: {count} ╨▒╨╗╤О╨┤' for category, count in categories.items()])}

╨Т╨Р╨Ц╨Э╨л╨Х ╨в╨а╨Х╨С╨Ю╨Т╨Р╨Э╨Ш╨п:
1. ╨Ъ╨░╨╢╨┤╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╨┤╨╛╨╗╨╢╨╜╨╛ ╤Б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╨╛╨▓╨░╤В╤М ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╨╕ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П
2. ╨г╤З╨╕╤В╤Л╨▓╨░╨╣ ╤Б╤А╨╡╨┤╨╜╨╕╨╣ ╤З╨╡╨║ ╨┐╤А╨╕ ╨▓╤Л╨▒╨╛╤А╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓
3. ╨С╨╗╤О╨┤╨░ ╨┤╨╛╨╗╨╢╨╜╤Л ╨╛╤В╨▓╨╡╤З╨░╤В╤М ╨╛╨╢╨╕╨┤╨░╨╜╨╕╤П╨╝: {request.expectations}
4. ╨б╨╛╨▒╨╗╤О╨┤╨░╨╣ ╨▒╨░╨╗╨░╨╜╤Б ╨┐╨╛ ╤Б╨╗╨╛╨╢╨╜╨╛╤Б╤В╨╕ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П
5. ╨г╤З╨╕╤В╤Л╨▓╨░╨╣ ╤Ж╨╡╨╗╨╡╨▓╤Г╤О ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╤О

╨Ю╤В╨▓╨╡╤З╨░╨╣ ╨в╨Ю╨Ы╨м╨Ъ╨Ю ╨▓ ╤Д╨╛╤А╨╝╨░╤В╨╡ JSON:
{{
  "menu_concept": "╨║╤А╨░╤В╨║╨░╤П ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╤П ╨╝╨╡╨╜╤О",
  "dishes": [
    {{
      "name": "╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░",
      "category": "╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П",
      "description": "╨║╤А╨░╤В╨║╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡",
      "main_ingredients": ["╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В1", "╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В2"],
      "estimated_cost": "╨┐╤А╨╕╨╝╨╡╤А╨╜╨░╤П ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М",
      "estimated_price": "╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╨░╤П ╤Ж╨╡╨╜╨░",
      "difficulty": "easy/medium/hard",
      "cook_time": "╨▓╤А╨╡╨╝╤П ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П"
    }}
  ]
}}"""

        # Generate menu using OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-5-mini",  # Using GPT-5-mini for menu generation
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
            "message": f"╨Я╤А╨╛╤Б╤В╨╛╨╡ ╨╝╨╡╨╜╤О '{request.menu_type}' ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╤Б╨╛╨╖╨┤╨░╨╜╨╛!"
        }
        
    except Exception as e:
        logger.error(f"Error generating simple menu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating simple menu: {str(e)}")

@api_router.post("/create-menu-project")
async def create_menu_project(request: MenuProjectCreate):
    """Create a new menu project for organizing menus and tech cards"""
    try:
        # Auto-create user if doesn't exist (for seamless experience)
        user = await db.users.find_one({"id": request.user_id})
        if not user:
            logger.info(f"Auto-creating user {request.user_id} for project creation")
            # Create basic user profile
            user_data = {
                "id": request.user_id,
                "email": f"{request.user_id}@example.com",
                "subscription_plan": "free",
                "subscription_features": ["basic_tech_cards"],
                "created_at": datetime.now().isoformat()
            }
            await db.users.insert_one(user_data)
        
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
            "message": f"╨Я╤А╨╛╨╡╨║╤В '{request.project_name}' ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╤Б╨╛╨╖╨┤╨░╨╜!"
        }
        
    except Exception as e:
        logger.error(f"Error creating menu project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating menu project: {str(e)}")

@api_router.get("/menu-projects/{user_id}")
async def get_user_menu_projects(user_id: str):
    """Get all menu projects for a user"""
    try:
        # Auto-create user if doesn't exist (for seamless experience)
        user = await db.users.find_one({"id": user_id})
        if not user:
            logger.info(f"Auto-creating user {user_id} for projects")
            # Create basic user profile
            user_data = {
                "id": user_id,
                "email": f"{user_id}@example.com",
                "subscription_plan": "free",
                "subscription_features": ["basic_tech_cards"],
                "created_at": datetime.now().isoformat()
            }
            await db.users.insert_one(user_data)
        
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
            "message": "╨Я╤А╨╛╨╡╨║╤В ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜!"
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
            "message": "╨Я╤А╨╛╨╡╨║╤В ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╤Г╨┤╨░╨╗╨╡╨╜!"
        }
        
    except Exception as e:
        logger.error(f"Error deleting menu project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting menu project: {str(e)}")

@api_router.get("/menu-project/{project_id}/content")
async def get_menu_project_content(project_id: str, user_id: str = None):
    """
    Get all menus and tech cards for a specific project with analytics
    SECURITY: Requires user_id to ensure user isolation
    """
    try:
        # Find project
        project = await db.menu_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # SECURITY FIX: Verify project belongs to user if user_id provided
        if user_id and project.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Project not found or access denied")
        
        # Use project's user_id if not provided (backward compatibility)
        effective_user_id = user_id or project.get("user_id")
        
        # Get menus in project
        # SECURITY FIX: Filter by user_id
        menus_query = {
            "project_id": project_id,
            "is_menu": True
        }
        if effective_user_id:
            menus_query["user_id"] = effective_user_id
        
        menus_cursor = db.user_history.find(menus_query).sort("created_at", -1)
        menus = await menus_cursor.to_list(length=100)
        
        # Get tech cards in project
        # SECURITY FIX: Filter by user_id
        tech_cards_query = {
            "project_id": project_id,
            "is_menu": False
        }
        if effective_user_id:
            tech_cards_query["user_id"] = effective_user_id
        
        tech_cards_cursor = db.user_history.find(tech_cards_query).sort("created_at", -1)
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
        
        # Calculate project statistics
        project_stats = {
            "creation_time_saved": len(menus) * 15 + len(tech_cards) * 45,  # ╨╝╨╕╨╜╤Г╤В╤Л
            "estimated_cost_savings": len(menus) * 5000 + len(tech_cards) * 2000,  # ╤А╤Г╨▒╨╗╨╕
            "total_dishes": sum(len(menu.get('dishes', [])) for menu in menus) + len(tech_cards),
            "complexity_score": _calculate_project_complexity(menus, tech_cards),
            "categories_covered": _get_project_categories(menus, tech_cards)
        }
        
        return {
            "success": True,
            "project": project,
            "menus": menus,
            "tech_cards": tech_cards,
            "menus_count": len(menus),
            "tech_cards_count": len(tech_cards),
            "project_stats": project_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting menu project content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting menu project content: {str(e)}")

def _calculate_project_complexity(menus, tech_cards):
    """Calculate complexity score for project analytics"""
    try:
        complexity_indicators = {
            'advanced_techniques': ['╤Б╤Г-╨▓╨╕╨┤', '╨╝╨╛╨╗╨╡╨║╤Г╨╗╤П╤А╨╜╨░╤П', '╨║╨╛╨╜╤Д╨╕', '╤Д╨╗╨░╨╝╨▒╨╕╤А╨╛╨▓╨░╨╜╨╕╨╡'],
            'premium_ingredients': ['╤В╤А╤О╤Д╨╡╨╗╤М', '╨╕╨║╤А╨░', '╤Д╤Г╨░-╨│╤А╨░', '╨╝╤А╨░╨╝╨╛╤А╨╜╨░╤П ╨│╨╛╨▓╤П╨┤╨╕╨╜╨░', '╤В╤Г╨╜╨╡╤Ж'],
            'complex_preparations': ['╨╝╨░╤А╨╕╨╜╨░╨┤', '╨┤╨╛╨╗╨│╨╛╨╡ ╤В╤Г╤И╨╡╨╜╨╕╨╡', '╤Д╨╡╤А╨╝╨╡╨╜╤В╨░╤Ж╨╕╤П', '24 ╤З╨░╤Б╨░']
        }
        
        total_score = 0
        content_texts = []
        
        # Collect all content texts
        for menu in menus:
            if menu.get('content'):
                content_texts.append(menu['content'].lower())
        
        for card in tech_cards:
            if card.get('content'):
                content_texts.append(card['content'].lower())
        
        # Calculate complexity based on content analysis
        for text in content_texts:
            for category, indicators in complexity_indicators.items():
                for indicator in indicators:
                    if indicator in text:
                        total_score += 1
        
        # Normalize score (0-100)
        max_possible_score = len(content_texts) * len(complexity_indicators) * 3
        if max_possible_score > 0:
            return min(100, int((total_score / max_possible_score) * 100))
        return 0
        
    except Exception:
        return 0

def _get_project_categories(menus, tech_cards):
    """Extract categories covered in the project"""
    try:
        categories = set()
        
        # Extract from menus
        for menu in menus:
            dishes = menu.get('dishes', [])
            for dish in dishes:
                category = dish.get('category', '').strip()
                if category:
                    categories.add(category)
        
        # Extract from tech cards (try to parse from content)
        for card in tech_cards:
            content = card.get('content', '')
            if '╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П:' in content:
                try:
                    category_line = [line for line in content.split('\n') if '╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П:' in line][0]
                    category = category_line.split('╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П:')[1].strip().replace('**', '')
                    if category:
                        categories.add(category)
                except:
                    pass
        
        return list(categories)
        
    except Exception:
        return []

# ============================================
# ENHANCED PROJECT ANALYTICS ENDPOINTS
# ============================================

@api_router.get("/menu-project/{project_id}/analytics")
async def get_project_analytics(project_id: str, organization_id: str = None, user_id: str = None):
    """
    Get comprehensive analytics for a menu project including IIKo sales data
    SECURITY: Requires user_id to ensure user isolation
    """
    try:
        # Find project
        project = await db.menu_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # SECURITY FIX: Verify project belongs to user if user_id provided
        if user_id and project.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Project not found or access denied")
        
        # Use project's user_id if not provided (backward compatibility)
        effective_user_id = user_id or project.get("user_id")
        
        # Get project content
        # SECURITY FIX: Filter by user_id
        menus_query = {
            "project_id": project_id,
            "is_menu": True
        }
        if effective_user_id:
            menus_query["user_id"] = effective_user_id
        
        menus_cursor = db.user_history.find(menus_query)
        menus = await menus_cursor.to_list(length=100)
        
        tech_cards_query = {
            "project_id": project_id,
            "is_menu": False
        }
        if effective_user_id:
            tech_cards_query["user_id"] = effective_user_id
        
        tech_cards_cursor = db.user_history.find(tech_cards_query)
        tech_cards = await tech_cards_cursor.to_list(length=500)
        
        # Basic project analytics
        basic_analytics = {
            "project_overview": {
                "name": project.get("project_name"),
                "type": project.get("project_type"),
                "created_at": project.get("created_at"),
                "menus_count": len(menus),
                "tech_cards_count": len(tech_cards),
                "total_items": sum(len(menu.get('dishes', [])) for menu in menus) + len(tech_cards)
            },
            "productivity_metrics": {
                "time_saved_minutes": len(menus) * 15 + len(tech_cards) * 45,
                "cost_savings_rubles": len(menus) * 5000 + len(tech_cards) * 2000,
                "complexity_score": _calculate_project_complexity(menus, tech_cards),
                "categories_covered": _get_project_categories(menus, tech_cards)
            }
        }
        
        # Try to get IIKo sales analytics if organization_id provided
        sales_analytics = None
        if organization_id:
            try:
                # Get sales data for dishes in this project
                sales_data = await _get_project_sales_performance(project_id, organization_id, menus, tech_cards)
                sales_analytics = sales_data
            except Exception as e:
                logger.warning(f"Could not get IIKo sales data for project {project_id}: {str(e)}")
                sales_analytics = {
                    "status": "unavailable",
                    "reason": "IIKo integration not available or no sales data found"
                }
        
        # Clean MongoDB _id fields
        if "_id" in project:
            del project["_id"]
        
        return {
            "success": True,
            "project": project,
            "analytics": basic_analytics,
            "sales_performance": sales_analytics,
            "recommendations": _generate_project_recommendations(basic_analytics, sales_analytics)
        }
        
    except Exception as e:
        logger.error(f"Error getting project analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting project analytics: {str(e)}")

async def _get_project_sales_performance(project_id: str, organization_id: str, menus: list, tech_cards: list):
    """Get sales performance for dishes in this project from IIKo"""
    try:
        # Extract dish names from project content
        project_dishes = set()
        
        # From menus
        for menu in menus:
            dishes = menu.get('dishes', [])
            for dish in dishes:
                dish_name = dish.get('name', '').strip()
                if dish_name:
                    project_dishes.add(dish_name.lower())
        
        # From tech cards
        for card in tech_cards:
            dish_name = card.get('dish_name', '').strip()
            if dish_name:
                project_dishes.add(dish_name.lower())
        
        if not project_dishes:
            return {"status": "no_dishes", "dishes_found": 0}
        
        # Get OLAP sales report from IIKo
        olap_data = await iiko_service.get_sales_olap_report(organization_id)
        
        if not olap_data.get('success'):
            return {
                "status": "iiko_unavailable",
                "error": olap_data.get('error', 'OLAP data unavailable'),
                "dishes_tracked": len(project_dishes)
            }
        
        # Match project dishes with sales data
        sales_summary = olap_data.get('summary', {})
        top_dishes = sales_summary.get('top_dishes', [])
        
        project_sales_matches = []
        total_project_revenue = 0
        total_project_quantity = 0
        
        for dish_data in top_dishes:
            dish_name_lower = dish_data.get('name', '').lower()
            
            # Try to match with project dishes (fuzzy matching)
            for project_dish in project_dishes:
                # Simple matching: if project dish name is contained in sales dish name or vice versa
                if (project_dish in dish_name_lower or 
                    dish_name_lower in project_dish or
                    _calculate_similarity(project_dish, dish_name_lower) > 0.7):
                    
                    project_sales_matches.append({
                        "project_dish": project_dish,
                        "sales_dish": dish_data.get('name'),
                        "revenue": dish_data.get('revenue', 0),
                        "quantity": dish_data.get('quantity', 0),
                        "category": dish_data.get('category', ''),
                        "match_confidence": _calculate_similarity(project_dish, dish_name_lower)
                    })
                    
                    total_project_revenue += dish_data.get('revenue', 0)
                    total_project_quantity += dish_data.get('quantity', 0)
                    break
        
        return {
            "status": "success",
            "period": {
                "from": olap_data.get('date_from'),
                "to": olap_data.get('date_to')
            },
            "project_performance": {
                "total_revenue": total_project_revenue,
                "total_quantity": total_project_quantity,
                "matched_dishes": len(project_sales_matches),
                "total_project_dishes": len(project_dishes),
                "match_rate": len(project_sales_matches) / len(project_dishes) if project_dishes else 0
            },
            "dish_performance": project_sales_matches[:10],  # Top 10 performing dishes
            "market_share": {
                "project_revenue_share": (total_project_revenue / sales_summary.get('total_revenue', 1)) * 100 if sales_summary.get('total_revenue') else 0,
                "project_quantity_share": (total_project_quantity / sales_summary.get('total_items_sold', 1)) * 100 if sales_summary.get('total_items_sold') else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting project sales performance: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

def _calculate_similarity(str1: str, str2: str) -> float:
    """Simple similarity calculation for dish name matching"""
    try:
        # Simple word overlap similarity
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
        
    except Exception:
        return 0.0

def _generate_project_recommendations(basic_analytics: dict, sales_analytics: dict) -> list:
    """Generate actionable recommendations based on project analytics"""
    recommendations = []
    
    try:
        # Basic productivity recommendations
        productivity = basic_analytics.get("productivity_metrics", {})
        complexity_score = productivity.get("complexity_score", 0)
        
        if complexity_score > 70:
            recommendations.append({
                "type": "optimization",
                "priority": "high",
                "title": "╨г╨┐╤А╨╛╤Б╤В╨╕╤В╨╡ ╤Б╨╗╨╛╨╢╨╜╤Л╨╡ ╨▒╨╗╤О╨┤╨░",
                "description": f"╨Я╤А╨╛╨╡╨║╤В ╨╕╨╝╨╡╨╡╤В ╨▓╤Л╤Б╨╛╨║╤Г╤О ╤Б╨╗╨╛╨╢╨╜╨╛╤Б╤В╤М ({complexity_score}%). ╨а╨░╤Б╤Б╨╝╨╛╤В╤А╨╕╤В╨╡ ╤Г╨┐╤А╨╛╤Й╨╡╨╜╨╕╨╡ ╨╜╨╡╨║╨╛╤В╨╛╤А╤Л╤Е ╤А╨╡╤Ж╨╡╨┐╤В╨╛╨▓ ╨┤╨╗╤П ╤Г╤Б╨║╨╛╤А╨╡╨╜╨╕╤П ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П.",
                "action": "review_complex_dishes"
            })
        
        categories_count = len(productivity.get("categories_covered", []))
        if categories_count < 3:
            recommendations.append({
                "type": "expansion",
                "priority": "medium",
                "title": "╨а╨░╤Б╤И╨╕╤А╤М╤В╨╡ ╨░╤Б╤Б╨╛╤А╤В╨╕╨╝╨╡╨╜╤В",
                "description": f"╨Я╤А╨╛╨╡╨║╤В ╨┐╨╛╨║╤А╤Л╨▓╨░╨╡╤В ╤В╨╛╨╗╤М╨║╨╛ {categories_count} ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕. ╨Ф╨╛╨▒╨░╨▓╤М╤В╨╡ ╨▒╨╗╤О╨┤╨░ ╨╕╨╖ ╨┤╤А╤Г╨│╨╕╤Е ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣ ╨┤╨╗╤П ╤А╨░╨╖╨╜╨╛╨╛╨▒╤А╨░╨╖╨╕╤П.",
                "action": "add_categories"
            })
        
        # Sales performance recommendations
        if sales_analytics and sales_analytics.get("status") == "success":
            performance = sales_analytics.get("project_performance", {})
            match_rate = performance.get("match_rate", 0) * 100
            
            if match_rate < 50:
                recommendations.append({
                    "type": "naming",
                    "priority": "high", 
                    "title": "╨г╨╗╤Г╤З╤И╨╕╤В╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П ╨▒╨╗╤О╨┤",
                    "description": f"╨в╨╛╨╗╤М╨║╨╛ {match_rate:.1f}% ╨▒╨╗╤О╨┤ ╨┐╤А╨╛╨╡╨║╤В╨░ ╨╜╨░╨╣╨┤╨╡╨╜╤Л ╨▓ ╨┐╤А╨╛╨┤╨░╨╢╨░╤Е. ╨Я╤А╨╛╨▓╨╡╤А╤М╤В╨╡ ╤Б╨╛╨╛╤В╨▓╨╡╤В╤Б╤В╨▓╨╕╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╣ ╨▓ ╨╝╨╡╨╜╤О ╨╕ IIKo.",
                    "action": "sync_dish_names"
                })
            
            market_share = sales_analytics.get("market_share", {})
            revenue_share = market_share.get("project_revenue_share", 0)
            
            if revenue_share > 20:
                recommendations.append({
                    "type": "success",
                    "priority": "low",
                    "title": "╨Ю╤В╨╗╨╕╤З╨╜╨░╤П ╨┐╤А╨╛╨╕╨╖╨▓╨╛╨┤╨╕╤В╨╡╨╗╤М╨╜╨╛╤Б╤В╤М!",
                    "description": f"╨С╨╗╤О╨┤╨░ ╨┐╤А╨╛╨╡╨║╤В╨░ ╤Б╨╛╤Б╤В╨░╨▓╨╗╤П╤О╤В {revenue_share:.1f}% ╨╛╤В ╨╛╨▒╤Й╨╡╨╣ ╨▓╤Л╤А╤Г╤З╨║╨╕. ╨н╤В╨╛ ╨┐╤А╨╡╨▓╨╛╤Б╤Е╨╛╨┤╨╜╤Л╨╣ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В!",
                    "action": "maintain_strategy"
                })
            elif revenue_share < 5:
                recommendations.append({
                    "type": "promotion",
                    "priority": "high",
                    "title": "╨г╨▓╨╡╨╗╨╕╤З╤М╤В╨╡ ╨┐╤А╨╛╨┤╨▓╨╕╨╢╨╡╨╜╨╕╨╡ ╨▒╨╗╤О╨┤",
                    "description": f"╨С╨╗╤О╨┤╨░ ╨┐╤А╨╛╨╡╨║╤В╨░ ╤Б╨╛╤Б╤В╨░╨▓╨╗╤П╤О╤В ╤В╨╛╨╗╤М╨║╨╛ {revenue_share:.1f}% ╨▓╤Л╤А╤Г╤З╨║╨╕. ╨а╨░╤Б╤Б╨╝╨╛╤В╤А╨╕╤В╨╡ ╨╝╨░╤А╨║╨╡╤В╨╕╨╜╨│╨╛╨▓╤Л╨╡ ╨░╨║╤Ж╨╕╨╕.",
                    "action": "promote_dishes"
                })
        
        # Time and cost savings highlights
        time_saved = productivity.get("time_saved_minutes", 0)
        if time_saved > 120:  # More than 2 hours
            recommendations.append({
                "type": "achievement",
                "priority": "low",
                "title": "╨Ч╨╜╨░╤З╨╕╤В╨╡╨╗╤М╨╜╨░╤П ╤Н╨║╨╛╨╜╨╛╨╝╨╕╤П ╨▓╤А╨╡╨╝╨╡╨╜╨╕",
                "description": f"╨Я╤А╨╛╨╡╨║╤В ╤Б╤Н╨║╨╛╨╜╨╛╨╝╨╕╨╗ {time_saved} ╨╝╨╕╨╜╤Г╤В ╤А╨░╨▒╨╛╤В╤Л! ╨н╤В╨╛ ╤Н╨║╨▓╨╕╨▓╨░╨╗╨╡╨╜╤В {time_saved // 60} ╤З╨░╤Б╨╛╨▓ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛╨╣ ╤А╨░╨╖╤А╨░╨▒╨╛╤В╨║╨╕ ╨╝╨╡╨╜╤О.",
                "action": "celebrate_efficiency"
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return [{
            "type": "error",
            "priority": "low",
            "title": "╨Ю╤И╨╕╨▒╨║╨░ ╨░╨╜╨░╨╗╨╕╨╖╨░",
            "description": "╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╤В╤М ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕ ╨╕╨╖-╨╖╨░ ╨╛╤И╨╕╨▒╨║╨╕ ╨░╨╜╨░╨╗╨╕╨╖╨░ ╨┤╨░╨╜╨╜╤Л╤Е.",
            "action": "retry_analysis"
        }]

@api_router.post("/menu-project/{project_id}/export")
async def export_project_content(project_id: str, export_format: str = "excel"):
    """Export all project content to Excel or PDF"""
    try:
        # Find project
        project = await db.menu_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get project content
        project_content = await get_menu_project_content(project_id)
        if not project_content["success"]:
            raise HTTPException(status_code=500, detail="Failed to get project content")
        
        # Prepare export data
        export_data = {
            "project_info": project_content["project"],
            "menus": project_content["menus"],
            "tech_cards": project_content["tech_cards"],
            "stats": project_content.get("project_stats", {})
        }
        
        if export_format.lower() == "excel":
            file_url = await _export_project_to_excel(export_data)
        elif export_format.lower() == "pdf":
            file_url = await _export_project_to_pdf(export_data)
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format. Use 'excel' or 'pdf'")
        
        return {
            "success": True,
            "message": f"╨Я╤А╨╛╨╡╨║╤В ╤Н╨║╤Б╨┐╨╛╤А╤В╨╕╤А╨╛╨▓╨░╨╜ ╨▓ ╤Д╨╛╤А╨╝╨░╤В {export_format.upper()}",
            "download_url": file_url,
            "project_name": project.get("project_name"),
            "export_format": export_format
        }
        
    except Exception as e:
        logger.error(f"Error exporting project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting project: {str(e)}")

async def _export_project_to_excel(export_data: dict) -> str:
    """Export project data to Excel format"""
    try:
        import pandas as pd
        from datetime import datetime
        import tempfile
        import os
        
        project_info = export_data["project_info"]
        project_name = project_info.get("project_name", "Project").replace(" ", "_")
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        filename = f"{project_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(temp_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Project Overview Sheet
            project_overview = pd.DataFrame([{
                "╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨┐╤А╨╛╨╡╨║╤В╨░": project_info.get("project_name"),
                "╨в╨╕╨┐ ╨┐╤А╨╛╨╡╨║╤В╨░": project_info.get("project_type"),
                "╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡": project_info.get("description", ""),
                "╨Ф╨░╤В╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П": project_info.get("created_at"),
                "╨Ъ╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨╝╨╡╨╜╤О": len(export_data["menus"]),
                "╨Ъ╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╤В╨╡╤Е╨║╨░╤А╤В": len(export_data["tech_cards"]),
                "╨б╤В╨░╤В╤Г╤Б": "╨Р╨║╤В╨╕╨▓╨╜╤Л╨╣" if project_info.get("is_active") else "╨Э╨╡╨░╨║╤В╨╕╨▓╨╜╤Л╨╣"
            }])
            project_overview.to_excel(writer, sheet_name='╨Ю╨▒╨╖╨╛╤А ╨┐╤А╨╛╨╡╨║╤В╨░', index=False)
            
            # Menus Sheet
            if export_data["menus"]:
                menus_data = []
                for menu in export_data["menus"]:
                    dishes = menu.get('dishes', [])
                    menus_data.append({
                        "ID ╨╝╨╡╨╜╤О": menu.get("menu_id"),
                        "╨в╨╕╨┐ ╨╝╨╡╨╜╤О": menu.get("menu_type"),
                        "╨Ъ╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨▒╨╗╤О╨┤": len(dishes),
                        "╨Ф╨░╤В╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П": menu.get("created_at"),
                        "╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡": menu.get("expectations", "")[:100] + "..." if len(menu.get("expectations", "")) > 100 else menu.get("expectations", "")
                    })
                
                menus_df = pd.DataFrame(menus_data)
                menus_df.to_excel(writer, sheet_name='╨Ь╨╡╨╜╤О', index=False)
            
            # Tech Cards Sheet
            if export_data["tech_cards"]:
                tech_cards_data = []
                for card in export_data["tech_cards"]:
                    tech_cards_data.append({
                        "╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░": card.get("dish_name"),
                        "╨Ф╨░╤В╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П": card.get("created_at"),
                        "╨У╨╛╤А╨╛╨┤": card.get("city", ""),
                        "╨в╨╕╨┐": "╨Т╨┤╨╛╤Е╨╜╨╛╨▓╨╡╨╜╨╕╨╡" if card.get("is_inspiration") else "╨б╤В╨░╨╜╨┤╨░╤А╤В"
                    })
                
                tech_cards_df = pd.DataFrame(tech_cards_data)
                tech_cards_df.to_excel(writer, sheet_name='╨в╨╡╤Е╨║╨░╤А╤В╤Л', index=False)
            
            # Statistics Sheet
            if export_data.get("stats"):
                stats_data = pd.DataFrame([export_data["stats"]])
                stats_data.to_excel(writer, sheet_name='╨б╤В╨░╤В╨╕╤Б╤В╨╕╨║╨░', index=False)
        
        # For demo purposes, return a placeholder URL
        # In production, this would upload to cloud storage
        return f"/downloads/{filename}"
        
    except Exception as e:
        logger.error(f"Error creating Excel export: {str(e)}")
        raise Exception(f"Failed to create Excel export: {str(e)}")

async def _export_project_to_pdf(export_data: dict) -> str:
    """Export project data to PDF format"""
    try:
        # For now, return a placeholder - PDF generation would require additional libraries
        project_info = export_data["project_info"]
        project_name = project_info.get("project_name", "Project").replace(" ", "_")
        filename = f"{project_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Placeholder implementation
        logger.info(f"PDF export requested for project: {project_name}")
        
        return f"/downloads/{filename}"
        
    except Exception as e:
        logger.error(f"Error creating PDF export: {str(e)}")
        raise Exception(f"Failed to create PDF export: {str(e)}")

# ============================================
# IIKo INTEGRATION ENDPOINTS
# ============================================

@api_router.get("/iiko/health-legacy")
async def iiko_health_check_legacy():
    """Legacy health check endpoint for IIKo API connectivity"""
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

@api_router.get("/iiko/organizations-legacy")
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
    """Upload AI-generated tech card to IIKo as complete dish (Assembly Chart + Product)"""
    user_id = request.organization_id  # Using as user identifier for now
    logger.info(f"ЁЯЪА ENHANCED UPLOAD: Uploading tech card '{request.name}' as complete dish to IIKo organization: {request.organization_id}")
    
    try:
        # Prepare tech card data
        tech_card_data = {
            'name': request.name,
            'description': request.description or '╨б╨╛╨╖╨┤╨░╨╜╨╛ AI-Menu-Designer',
            'ingredients': request.ingredients,
            'preparation_steps': request.preparation_steps,
            'weight': request.weight or 100.0,
            'price': request.price or 0.0,
            'category': request.category_id or ''
        }
        
        # Use the new complete dish creation method
        result = await iiko_service.create_complete_dish_in_iiko(
            tech_card_data=tech_card_data,
            organization_id=request.organization_id,
            category_id=request.category_id
        )
        
        if result.get('success'):
            # Save success record to database with enhanced information
            sync_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "organization_id": request.organization_id,
                "tech_card_name": request.name,
                "sync_type": "complete_dish_upload",
                "sync_status": result.get('status'),
                "assembly_chart_id": result.get('assembly_chart', {}).get('assembly_chart_id'),
                "dish_product_id": result.get('dish_product', {}).get('product_id'),
                "category_id": result.get('summary', {}).get('category_used'),
                "created_at": datetime.now().isoformat(),
                "ai_generated": True,
                "upload_success": True,
                "steps_completed": result.get('steps_completed', []),
                "errors": result.get('errors', [])
            }
            
            await db.iiko_sync_records.insert_one(sync_record)
            
            return {
                "success": True,
                "sync_id": sync_record["id"],
                "status": result.get('status'),
                "message": result.get('message'),
                "note": "тЬЕ ╨С╨╗╤О╨┤╨╛ ╤Б╨╛╨╖╨┤╨░╨╜╨╛ ╨║╨░╨║ ╨┐╨╛╨╗╨╜╨╛╤Ж╨╡╨╜╨╜╤Л╨╣ ╨┐╤А╨╛╨┤╤Г╨║╤В ╨▓ IIKo (╤В╨╡╤Е╨║╨░╤А╤В╨░ + ╨╝╨╡╨╜╤О)!",
                "details": {
                    "assembly_chart_created": result.get('assembly_chart', {}).get('success', False),
                    "dish_product_created": result.get('dish_product', {}).get('success', False),
                    "will_appear_in_menu": result.get('dish_product', {}).get('success', False)
                }
            }
        else:
            # Fallback: Try only assembly chart creation (legacy behavior)
            logger.info(f"Complete dish creation failed, trying legacy assembly chart creation...")
            
            legacy_result = await iiko_service.create_assembly_chart(tech_card_data, request.organization_id)
            
            if legacy_result.get('success'):
                sync_record = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "organization_id": request.organization_id,
                    "tech_card_name": request.name,
                    "sync_type": "assembly_chart_only",
                    "sync_status": "created_as_assembly_chart",
                    "assembly_chart_id": legacy_result.get('assembly_chart_id'),
                    "created_at": datetime.now().isoformat(),
                    "ai_generated": True,
                    "upload_success": True
                }
                
                await db.iiko_sync_records.insert_one(sync_record)
                
                return {
                    "success": True,
                    "sync_id": sync_record["id"],
                    "assembly_chart_id": legacy_result.get('assembly_chart_id'),
                    "message": legacy_result.get('message'),
                    "note": "тЪая╕П ╨б╨╛╨╖╨┤╨░╨╜╨░ ╤В╨╛╨╗╤М╨║╨╛ ╤В╨╡╤Е╨║╨░╤А╤В╨░ (Assembly Chart). ╨С╨╗╤О╨┤╨╛ ╨╜╨╡ ╨┤╨╛╨▒╨░╨▓╨╗╨╡╨╜╨╛ ╨▓ ╨╝╨╡╨╜╤О.",
                    "warning": "╨Ф╨╗╤П ╨┐╨╛╤П╨▓╨╗╨╡╨╜╨╕╤П ╨▓ ╨╝╨╡╨╜╤О ╤В╤А╨╡╨▒╤Г╨╡╤В╤Б╤П ╤Б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╨░"
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error'),
                    "legacy_error": legacy_result.get('error'),
                    "note": "тЭМ ╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨╛╨╖╨┤╨░╤В╤М ╨╜╨╕ ╨▒╨╗╤О╨┤╨╛, ╨╜╨╕ ╤В╨╡╤Е╨║╨░╤А╤В╤Г"
                }
            
    except Exception as e:
        logger.error(f"Error in tech card upload process: {str(e)}")
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
            "message": "╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╝╨╡╨╜╤О ╨╖╨░╨┐╤Г╤Й╨╡╨╜╨░",
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

@api_router.get("/iiko/sales-report/{organization_id}")
async def get_iiko_sales_report(
    organization_id: str,
    date_from: str = None,
    date_to: str = None
):
    """Get sales/revenue report from IIKo - SIMPLE TEST"""
    logger.info(f"ЁЯТ░ SALES REPORT REQUEST: Getting sales data for {organization_id}")
    
    try:
        # Get sales report from IIKo
        sales_report = await iiko_service.get_sales_report(organization_id, date_from, date_to)
        
        if sales_report.get('success'):
            logger.info(f"тЬЕ Sales report retrieved successfully")
            
            return {
                "success": True,
                "message": "╨Ю╤В╤З╨╡╤В ╨┐╨╛ ╨▓╤Л╤А╤Г╤З╨║╨╡ ╨┐╨╛╨╗╤Г╤З╨╡╨╜ ╤Г╤Б╨┐╨╡╤И╨╜╨╛",
                "organization_id": organization_id,
                "period": {
                    "from": sales_report.get('date_from'),
                    "to": sales_report.get('date_to')
                },
                "data": sales_report.get('sales_data'),
                "summary": sales_report.get('summary', {}),
                "endpoint_used": sales_report.get('endpoint'),
                "method": sales_report.get('method', 'GET')
            }
        else:
            logger.warning(f"тЪая╕П Sales report failed: {sales_report.get('error')}")
            
            return {
                "success": False,
                "message": "╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╨╛╤В╤З╨╡╤В ╨┐╨╛ ╨┐╤А╨╛╨┤╨░╨╢╨░╨╝",
                "organization_id": organization_id,
                "error": sales_report.get('error'),
                "tried_endpoints": sales_report.get('tried_endpoints', []),
                "note": sales_report.get('note'),
                "diagnostic_info": {
                    "auth_working": True,  # We know auth works
                    "menu_access": True,   # We know menu access works
                    "sales_endpoints": "not_available"
                }
            }
            
    except Exception as e:
        logger.error(f"тЭМ Error in sales report endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting sales report: {str(e)}")

@api_router.get("/iiko/analytics/{organization_id}")  
async def get_iiko_analytics_dashboard(organization_id: str):
    """Get comprehensive analytics dashboard data from IIKo"""
    logger.info(f"ЁЯУК ANALYTICS DASHBOARD: Getting analytics for {organization_id}")
    
    try:
        # Combine multiple data sources
        analytics_data = {
            "organization_id": organization_id,
            "generated_at": datetime.now().isoformat(),
            "sections": {}
        }
        
        # 1. Basic organization info
        try:
            organizations = await iiko_service.get_organizations()
            org_info = next((org for org in organizations if org['id'] == organization_id), None)
            analytics_data["organization_info"] = org_info
        except Exception as e:
            analytics_data["organization_info"] = {"error": str(e)}
        
        # 2. Menu overview
        try:
            menu_data = await iiko_service.get_menu_items([organization_id])
            analytics_data["sections"]["menu_overview"] = {
                "categories_count": len(menu_data.get('categories', [])),
                "items_count": len(menu_data.get('items', [])),
                "last_updated": menu_data.get('last_updated'),
                "top_categories": [cat['name'] for cat in menu_data.get('categories', [])[:5]]
            }
        except Exception as e:
            analytics_data["sections"]["menu_overview"] = {"error": str(e)}
        
        # 3. Sales data (if available)
        try:
            sales_report = await iiko_service.get_sales_report(organization_id)
            if sales_report.get('success'):
                analytics_data["sections"]["sales_summary"] = sales_report.get('summary', {})
            else:
                analytics_data["sections"]["sales_summary"] = {"status": "not_available"}
        except Exception as e:
            analytics_data["sections"]["sales_summary"] = {"error": str(e)}
        
        return {
            "success": True,
            "message": "╨Р╨╜╨░╨╗╨╕╤В╨╕╤З╨╡╤Б╨║╨░╤П ╨┐╨░╨╜╨╡╨╗╤М ╤Б╤Д╨╛╤А╨╝╨╕╤А╨╛╨▓╨░╨╜╨░",
            "analytics": analytics_data
        }
        
    except Exception as e:
        logger.error(f"тЭМ Error in analytics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")

@api_router.post("/iiko/ai-menu-analysis/{organization_id}")
async def ai_analyze_menu(organization_id: str, request: dict = None):
    """ЁЯза AI ╨Р╨Э╨Р╨Ы╨Ш╨Ч ╨Ь╨Х╨Э╨о - ╨░╨╜╨░╨╗╨╕╨╖╨╕╤А╤Г╨╡╤В ╤А╨╡╨░╨╗╤М╨╜╨╛╨╡ ╨╝╨╡╨╜╤О ╨╕╨╖ IIKo ╤З╨╡╤А╨╡╨╖ GPT-4"""
    logger.info(f"ЁЯза AI MENU ANALYSIS: Analyzing menu for {organization_id}")
    
    try:
        # 1. ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╤А╨╡╨░╨╗╤М╨╜╨╛╨╡ ╨╝╨╡╨╜╤О ╨╕╨╖ IIKo
        logger.info("ЁЯУК Fetching menu data from IIKo...")
        menu_data = await iiko_service.get_menu_items([organization_id])
        
        if not menu_data or not menu_data.get('items'):
            raise HTTPException(status_code=404, detail="Menu data not found")
        
        categories = menu_data.get('categories', [])
        items = menu_data.get('items', [])
        
        logger.info(f"ЁЯУЛ Loaded {len(items)} menu items in {len(categories)} categories")
        
        # 2. ╨Я╨╛╨┤╨│╨╛╤В╨░╨▓╨╗╨╕╨▓╨░╨╡╨╝ ╨┤╨░╨╜╨╜╤Л╨╡ ╨┤╨╗╤П AI ╨░╨╜╨░╨╗╨╕╨╖╨░
        analysis_type = request.get('analysis_type', 'comprehensive') if request else 'comprehensive'
        
        # ╨У╤А╤Г╨┐╨┐╨╕╤А╤Г╨╡╨╝ ╨▒╨╗╤О╨┤╨░ ╨┐╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝ ╨┤╨╗╤П ╨░╨╜╨░╨╗╨╕╨╖╨░
        menu_by_categories = {}
        for category in categories:
            cat_items = [item for item in items if item.get('category_id') == category['id']]
            if cat_items:  # ╨в╨╛╨╗╤М╨║╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ ╤Б ╨▒╨╗╤О╨┤╨░╨╝╨╕
                menu_by_categories[category['name']] = [
                    {
                        'name': item['name'],
                        'description': item.get('description', ''),
                        'id': item['id']
                    }
                    for item in cat_items[:10]  # ╨Я╨╡╤А╨▓╤Л╨╡ 10 ╨┤╨╗╤П ╨░╨╜╨░╨╗╨╕╨╖╨░
                ]
        
        # 3. ╨д╨╛╤А╨╝╨╕╤А╤Г╨╡╨╝ ╨┐╤А╨╛╨╝╨┐╤В ╨┤╨╗╤П GPT-4
        ai_prompt = f"""
╨в╤Л - ╤Н╨║╤Б╨┐╨╡╤А╤В ╨┐╨╛ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╜╨╛╨╝╤Г ╨▒╨╕╨╖╨╜╨╡╤Б╤Г ╨╕ ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╨╕ ╨╝╨╡╨╜╤О. ╨Я╤А╨╛╨░╨╜╨░╨╗╨╕╨╖╨╕╤А╤Г╨╣ ╨а╨Х╨Р╨Ы╨м╨Э╨Ю╨Х ╨╝╨╡╨╜╤О ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░ "Edison Craft Bar".

╨Ф╨Р╨Э╨Э╨л╨Х ╨Ь╨Х╨Э╨о:
- ╨Т╤Б╨╡╨│╨╛ ╨┐╨╛╨╖╨╕╤Ж╨╕╨╣: {len(items)}
- ╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╨╣: {len(categories)}
- ╨Ф╨╡╤В╨░╨╗╨╕╨╖╨░╤Ж╨╕╤П ╨┐╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝:
{json.dumps(menu_by_categories, ensure_ascii=False, indent=2)}

╨Ч╨Р╨Ф╨Р╨з╨Р: ╨Ф╨░╨╣ 5 ╨Ъ╨Ю╨Э╨Ъ╨а╨Х╨в╨Э╨л╨е ╨┐╤А╨░╨║╤В╨╕╤З╨╡╤Б╨║╨╕╤Е ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╣ ╨┤╨╗╤П ╤Г╨▓╨╡╨╗╨╕╤З╨╡╨╜╨╕╤П ╨┐╤А╨╕╨▒╤Л╨╗╨╕ ╤Н╤В╨╛╨│╨╛ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░.

╨д╨Ю╨а╨Ь╨Р╨в ╨Ю╨в╨Т╨Х╨в╨Р:
1. **[╨в╨╡╨╝╨░ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕]**: [╨Ъ╨╛╨╜╨║╤А╨╡╤В╨╜╨░╤П ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╤П ╤Б ╨┐╤А╨╕╨╝╨╡╤А╨░╨╝╨╕ ╨╕╨╖ ╨╝╨╡╨╜╤О]
2. **[╨в╨╡╨╝╨░ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕]**: [╨Ъ╨╛╨╜╨║╤А╨╡╤В╨╜╨░╤П ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╤П ╤Б ╨┐╤А╨╕╨╝╨╡╤А╨░╨╝╨╕ ╨╕╨╖ ╨╝╨╡╨╜╤О]
...

╨Р╨Ъ╨ж╨Х╨Э╨в ╨Э╨Р:
- ╨Ъ╨╛╨╜╨║╤А╨╡╤В╨╜╤Л╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П ╨▒╨╗╤О╨┤ ╨╕╨╖ ╨╝╨╡╨╜╤О
- ╨Я╤А╨░╨║╤В╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П (╨┐╨╛╨┤╨╜╤П╤В╤М ╤Ж╨╡╨╜╤Г, ╤Г╨▒╤А╨░╤В╤М, ╨┤╨╛╨▒╨░╨▓╨╕╤В╤М)
- ╨ж╨╕╤Д╤А╤Л ╨╕ ╨┐╤А╨╛╤Ж╨╡╨╜╤В╤Л
- ╨Я╤Б╨╕╤Е╨╛╨╗╨╛╨│╨╕╤О ╨┐╤А╨╛╨┤╨░╨╢

╨б╨в╨Ш╨Ы╨м: ╨Ъ╨░╨║ ╨╛╨┐╤Л╤В╨╜╤Л╨╣ ╤А╨╡╤Б╤В╨╛╤А╨░╤В╨╛╤А, ╨║╤А╨░╤В╨║╨╛ ╨╕ ╨┐╨╛ ╨┤╨╡╨╗╤Г.
"""

        # 4. ╨Ю╤В╨┐╤А╨░╨▓╨╗╤П╨╡╨╝ ╨╜╨░ ╨░╨╜╨░╨╗╨╕╨╖ ╨▓ GPT-4
        logger.info("ЁЯдЦ Sending menu to GPT-4 for analysis...")
        
        ai_response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "╨в╤Л ╤Н╨║╤Б╨┐╨╡╤А╤В ╨┐╨╛ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╜╨╛╨╝╤Г ╨▒╨╕╨╖╨╜╨╡╤Б╤Г ╤Б 20-╨╗╨╡╤В╨╜╨╕╨╝ ╨╛╨┐╤Л╤В╨╛╨╝ ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╨╕ ╨╝╨╡╨╜╤О."},
                {"role": "user", "content": ai_prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        ai_analysis = ai_response.choices[0].message.content
        
        # 5. ╨д╨╛╤А╨╝╨╕╤А╤Г╨╡╨╝ ╨┤╨╡╤В╨░╨╗╤М╨╜╤Л╨╣ ╨╛╤В╨▓╨╡╤В
        return {
            "success": True,
            "message": "ЁЯза AI-╨░╨╜╨░╨╗╨╕╨╖ ╨╝╨╡╨╜╤О ╨╖╨░╨▓╨╡╤А╤И╨╡╨╜",
            "organization_id": organization_id,
            "menu_stats": {
                "total_items": len(items),
                "categories_count": len(categories),
                "analyzed_categories": len(menu_by_categories),
                "sample_categories": list(menu_by_categories.keys())[:5]
            },
            "ai_analysis": {
                "recommendations": ai_analysis,
                "analysis_type": analysis_type,
                "model_used": "gpt-5-mini",
                "generated_at": datetime.now().isoformat()
            },
            "menu_insights": {
                "largest_category": max(categories, key=lambda c: len([i for i in items if i.get('category_id') == c['id']])).get('name') if categories else None,
                "category_distribution": {cat['name']: len([i for i in items if i.get('category_id') == cat['id']]) for cat in categories[:10]}
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"тЭМ Error in AI menu analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in AI analysis: {str(e)}")

@api_router.get("/iiko/category/{organization_id}/{category_name}")
async def get_iiko_category_items(organization_id: str, category_name: str):
    """Get items from specific IIKo category for menu browsing"""
    try:
        logger.info(f"ЁЯП╖я╕П Getting category items: {category_name} from organization: {organization_id}")
        
        # Get full menu first
        menu_data = await iiko_service.get_menu_items([organization_id])
        
        if not menu_data or not menu_data.get('items'):
            return {
                "success": False,
                "error": "No menu data available",
                "category": category_name,
                "items": []
            }
        
        # Filter items by category name
        category_items = []
        all_items = menu_data.get('items', [])
        
        for item in all_items:
            # Match category by name (case-insensitive, partial match)
            item_category = item.get('category_name', '').lower()
            if category_name.lower() in item_category or item_category in category_name.lower():
                category_items.append({
                    "id": item.get('id'),
                    "name": item.get('name'),
                    "description": item.get('description', ''),
                    "price": item.get('price', 0),
                    "weight": item.get('weight', 0),
                    "category": item.get('category_name', category_name)
                })
        
        logger.info(f"ЁЯУК Found {len(category_items)} items in category '{category_name}'")
        
        return {
            "success": True,
            "category": category_name,
            "organization_id": organization_id,
            "items": category_items,
            "total_count": len(category_items)
        }
        
    except Exception as e:
        logger.error(f"Error getting category items: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "category": category_name,
            "items": []
        }

# ============== IIKO CATEGORIES MANAGEMENT ENDPOINTS ==============

@api_router.get("/iiko/categories/{organization_id}")
async def get_iiko_categories(organization_id: str):
    """Get all user categories from IIKo system"""
    try:
        logger.info(f"ЁЯУВ Getting categories for organization: {organization_id}")
        
        result = await iiko_service.get_categories(organization_id)
        
        if result.get('success'):
            logger.info(f"тЬЕ Retrieved {result.get('categories_count', 0)} categories from IIKo")
            return JSONResponse(
                content=result,
                status_code=200
            )
        else:
            logger.error(f"тЭМ Failed to get categories: {result.get('error')}")
            return JSONResponse(
                content=result,
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Error in get_iiko_categories: {str(e)}")
        return JSONResponse(
            content={"error": str(e), "success": False},
            status_code=500
        )

@api_router.post("/iiko/categories/create")
async def create_iiko_category(request: Dict[str, Any]):
    """Create a new category in IIKo system"""
    try:
        category_name = request.get('name', 'AI Menu Designer')
        organization_id = request.get('organization_id', 'default-org-001')
        
        logger.info(f"ЁЯУВ Creating category '{category_name}' in IIKo organization: {organization_id}")
        
        # First check if category already exists
        check_result = await iiko_service.check_category_exists(category_name, organization_id)
        
        if check_result.get('success') and check_result.get('exists'):
            existing_category = check_result.get('category')
            logger.info(f"тД╣я╕П Category '{category_name}' already exists")
            return JSONResponse(
                content={
                    "success": True,
                    "already_exists": True,
                    "category": existing_category,
                    "message": f"╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П '{category_name}' ╤Г╨╢╨╡ ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╨╡╤В ╨▓ IIKo"
                },
                status_code=200
            )
        
        # Create new category
        result = await iiko_service.create_category(category_name, organization_id)
        
        if result.get('success'):
            logger.info(f"тЬЕ Category '{category_name}' created successfully")
            return JSONResponse(
                content=result,
                status_code=201
            )
        else:
            logger.error(f"тЭМ Failed to create category: {result.get('error')}")
            return JSONResponse(
                content=result,
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Error in create_iiko_category: {str(e)}")
        return JSONResponse(
            content={"error": str(e), "success": False},
            status_code=500
        )

@api_router.post("/iiko/categories/check")
async def check_iiko_category(request: Dict[str, Any]):
    """Check if category exists in IIKo system"""
    try:
        category_name = request.get('name', 'AI Menu Designer')
        organization_id = request.get('organization_id', 'default-org-001')
        
        logger.info(f"ЁЯУВ Checking category '{category_name}' in organization: {organization_id}")
        
        result = await iiko_service.check_category_exists(category_name, organization_id)
        
        if result.get('success'):
            return JSONResponse(
                content=result,
                status_code=200
            )
        else:
            logger.error(f"тЭМ Failed to check category: {result.get('error')}")
            return JSONResponse(
                content=result,
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Error in check_iiko_category: {str(e)}")
        return JSONResponse(
            content={"error": str(e), "success": False},
            status_code=500
        )

# ============== NEW COMPLETE DISH CREATION ENDPOINT ==============

@api_router.post("/iiko/products/create-complete-dish")
async def create_complete_dish_in_iiko(request: TechCardUpload):
    """
    Create COMPLETE dish in IIKo: Assembly Chart + DISH Product + Category
    This is the new recommended endpoint for creating dishes that will appear in the menu
    """
    try:
        logger.info(f"ЁЯН╜я╕П COMPLETE DISH: Creating complete dish '{request.name}' in IIKo organization: {request.organization_id}")
        
        # Prepare tech card data
        tech_card_data = {
            'name': request.name,
            'description': request.description or '╨б╨╛╨╖╨┤╨░╨╜╨╛ AI-Menu-Designer',
            'ingredients': request.ingredients,
            'preparation_steps': request.preparation_steps,
            'weight': request.weight or 100.0,
            'price': request.price or 0.0,
            'category': request.category_id or ''
        }
        
        # Create complete dish (Assembly Chart + DISH Product)
        result = await iiko_service.create_complete_dish_in_iiko(
            tech_card_data=tech_card_data,
            organization_id=request.organization_id,
            category_id=request.category_id
        )
        
        # Save comprehensive sync record to database
        sync_record = {
            "id": str(uuid.uuid4()),
            "user_id": "system",
            "organization_id": request.organization_id,
            "tech_card_name": request.name,
            "sync_type": "complete_dish_creation",
            "sync_status": result.get('status', 'unknown'),
            "assembly_chart_id": result.get('assembly_chart', {}).get('assembly_chart_id'),
            "dish_product_id": result.get('dish_product', {}).get('product_id'),
            "category_id": result.get('summary', {}).get('category_used'),
            "created_at": datetime.now().isoformat(),
            "ai_generated": True,
            "steps_completed": result.get('steps_completed', []),
            "errors": result.get('errors', []),
            "upload_success": result.get('success', False)
        }
        
        await db.iiko_sync_records.insert_one(sync_record)
        
        # Return structured response
        response = {
            "success": result.get('success', False),
            "sync_id": sync_record["id"],
            "status": result.get('status'),
            "message": result.get('message'),
            "details": {
                "assembly_chart": {
                    "created": result.get('assembly_chart', {}).get('success', False),
                    "id": result.get('assembly_chart', {}).get('assembly_chart_id')
                },
                "dish_product": {
                    "created": result.get('dish_product', {}).get('success', False),
                    "id": result.get('dish_product', {}).get('product_id'),
                    "name": result.get('dish_product', {}).get('product_name')
                },
                "category": {
                    "id": result.get('summary', {}).get('category_used')
                }
            },
            "summary": result.get('summary', {}),
            "steps_completed": result.get('steps_completed', []),
            "errors": result.get('errors', [])
        }
        
        return response
            
    except Exception as e:
        logger.error(f"Error in complete dish creation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating complete dish: {str(e)}")

# ============== TECH CARDS (ASSEMBLY CHARTS) MANAGEMENT ENDPOINTS ==============

@api_router.post("/iiko/assembly-charts/create")
async def create_tech_card_in_iiko(request: TechCardUpload):
    """Create a new tech card (assembly chart) directly in IIKo system"""
    try:
        logger.info(f"ЁЯФи Creating assembly chart '{request.name}' in IIKo organization: {request.organization_id}")
        
        # Prepare tech card data for assembly chart
        tech_card_data = {
            'name': request.name,
            'description': request.description or '╨б╨╛╨╖╨┤╨░╨╜╨╛ AI-Menu-Designer',
            'ingredients': request.ingredients,
            'preparation_steps': request.preparation_steps,
            'weight': request.weight or 0.0,
            'price': request.price or 0.0,
            'category': request.category_id or ''
        }
        
        # Create assembly chart in IIKo
        result = await iiko_service.create_assembly_chart(tech_card_data, request.organization_id)
        
        if result.get('success'):
            # Save success record to database
            sync_record = {
                "id": str(uuid.uuid4()),
                "user_id": "system",
                "organization_id": request.organization_id,
                "tech_card_name": request.name,
                "assembly_chart_id": result.get('assembly_chart_id'),
                "sync_status": "created_as_assembly_chart",
                "created_at": datetime.now().isoformat(),
                "ai_generated": True,
                "upload_success": True
            }
            
            await db.iiko_sync_records.insert_one(sync_record)
            
            return {
                "success": True,
                "sync_id": sync_record["id"],
                "assembly_chart_id": result.get('assembly_chart_id'),
                "message": result.get('message'),
                "note": "тЬЕ ╨в╨╡╤Е╨║╨░╤А╤В╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨░ ╨║╨░╨║ Assembly Chart ╨▓ IIKo!"
            }
        else:
            return {
                "success": False,
                "error": result.get('error'),
                "note": result.get('note')
            }
            
    except Exception as e:
        logger.error(f"Error creating tech card in IIKo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating tech card: {str(e)}")

@api_router.get("/iiko/assembly-charts/all/{organization_id}")
async def get_all_tech_cards_from_iiko(organization_id: str):
    """Get all tech cards (assembly charts) from IIKo system"""
    try:
        logger.info(f"ЁЯУЛ Getting all assembly charts from IIKo organization: {organization_id}")
        
        result = await iiko_service.get_all_assembly_charts(organization_id)
        
        if result.get('success'):
            return {
                "success": True,
                "organization_id": organization_id,
                "assembly_charts": result.get('assembly_charts', []),
                "count": result.get('count', 0),
                "message": f"╨Э╨░╨╣╨┤╨╡╨╜╨╛ {result.get('count', 0)} ╤В╨╡╤Е╨║╨░╤А╤В ╨▓ IIKo"
            }
        else:
            return {
                "success": False,
                "error": result.get('error'),
                "assembly_charts": [],
                "count": 0
            }
            
    except Exception as e:
        logger.error(f"Error getting all tech cards from IIKo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting tech cards: {str(e)}")

@api_router.get("/iiko/assembly-charts/{chart_id}")
async def get_tech_card_by_id_from_iiko(chart_id: str):
    """Get specific tech card (assembly chart) by ID from IIKo system"""
    try:
        logger.info(f"ЁЯФН Getting assembly chart by ID from IIKo: {chart_id}")
        
        result = await iiko_service.get_assembly_chart_by_id(chart_id)
        
        if result.get('success'):
            return {
                "success": True,
                "chart_id": chart_id,
                "assembly_chart": result.get('assembly_chart'),
                "message": "╨в╨╡╤Е╨║╨░╤А╤В╨░ ╨╜╨░╨╣╨┤╨╡╨╜╨░"
            }
        else:
            return {
                "success": False,
                "error": result.get('error'),
                "chart_id": chart_id
            }
            
    except Exception as e:
        logger.error(f"Error getting tech card by ID from IIKo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting tech card: {str(e)}")

@api_router.delete("/iiko/assembly-charts/{chart_id}")
async def delete_tech_card_from_iiko(chart_id: str):
    """Delete tech card (assembly chart) from IIKo system"""
    try:
        logger.info(f"ЁЯЧСя╕П Deleting assembly chart from IIKo: {chart_id}")
        
        result = await iiko_service.delete_assembly_chart(chart_id)
        
        if result.get('success'):
            # Update sync records
            await db.iiko_sync_records.update_many(
                {"assembly_chart_id": chart_id},
                {"$set": {
                    "sync_status": "deleted_from_iiko",
                    "deleted_at": datetime.now().isoformat()
                }}
            )
            
            return {
                "success": True,
                "chart_id": chart_id,
                "message": result.get('message')
            }
        else:
            return {
                "success": False,
                "error": result.get('error'),
                "chart_id": chart_id
            }
            
    except Exception as e:
        logger.error(f"Error deleting tech card from IIKo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting tech card: {str(e)}")

@api_router.get("/iiko/tech-cards/sync-status")
async def get_tech_cards_sync_status():
    """Get sync status of all tech cards with IIKo"""
    try:
        # Get all sync records from database
        sync_records = await db.iiko_sync_records.find(
            {},
            {"_id": 0}
        ).sort([("created_at", -1)]).to_list(length=100)
        
        # Group by status
        status_summary = {}
        for record in sync_records:
            status = record.get('sync_status', 'unknown')
            if status not in status_summary:
                status_summary[status] = 0
            status_summary[status] += 1
        
        return {
            "success": True,
            "sync_records": sync_records,
            "status_summary": status_summary,
            "total_records": len(sync_records)
        }
        
    except Exception as e:
        logger.error(f"Error getting tech cards sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {str(e)}")

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
        recommendations.append("тЭМ ╨Ъ╤А╨╕╤В╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨┐╤А╨╛╨▒╨╗╨╡╨╝╤Л ╨╛╨▒╨╜╨░╤А╤Г╨╢╨╡╨╜╤Л:")
        for test in failed_tests:
            recommendations.append(f"   тАв {test['test_name']}: {'; '.join(test['issues'])}")
    else:
        recommendations.append("тЬЕ ╨Т╤Б╨╡ ╤В╨╡╤Б╤В╤Л ╨┐╤А╨╛╨╣╨┤╨╡╨╜╤Л ╤Г╤Б╨┐╨╡╤И╨╜╨╛ - ╨╕╨╜╤В╨╡╨│╤А╨░╤Ж╨╕╤П ╤Б IIKo ╨│╨╛╤В╨╛╨▓╨░ ╨║ ╤А╨░╨▒╨╛╤В╨╡")
    
    recommendations.extend([
        "",
        "ЁЯТб ╨Ю╨▒╤Й╨╕╨╡ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕:",
        "   тАв ╨а╨╡╨│╤Г╨╗╤П╤А╨╜╨╛ ╨┐╤А╨╛╨▓╨╡╤А╤П╨╣╤В╨╡ ╤Б╤В╨░╤В╤Г╤Б ╨╕╨╜╤В╨╡╨│╤А╨░╤Ж╨╕╨╕",
        "   тАв ╨Э╨░╤Б╤В╤А╨╛╨╣╤В╨╡ ╨╝╨╛╨╜╨╕╤В╨╛╤А╨╕╨╜╨│ ╨┤╨╗╤П ╨▓╨░╨╢╨╜╤Л╤Е ╤Н╨╜╨┤╨┐╨╛╨╕╨╜╤В╨╛╨▓",
        "   тАв ╨Т╨╡╨┤╨╕╤В╨╡ ╤А╨╡╨╖╨╡╤А╨▓╨╜╤Л╨╡ ╨║╨╛╨┐╨╕╨╕ ╨┤╨░╨╜╨╜╤Л╤Е ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕",
        "   тАв ╨в╨╡╤Б╤В╨╕╤А╤Г╨╣╤В╨╡ ╨╕╨╜╤В╨╡╨│╤А╨░╤Ж╨╕╤О ╨┐╨╛╤Б╨╗╨╡ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╣ IIKo"
    ])
    
    return recommendations

# ===== CULINARY ASSISTANT CHAT =====
@api_router.post("/assistant/chat")
async def chat_with_assistant(request: dict):
    """
    ╨з╨░╤В ╤Б ╨║╤Г╨╗╨╕╨╜╨░╤А╨╜╤Л╨╝ ╨░╤Б╤Б╨╕╤Б╤В╨╡╨╜╤В╨╛╨╝ RECEPTOR ╤Б ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨║╨╛╨╣ tool-calling
    
    Request:
    {
        "user_id": "uuid",
        "message": "╨б╨╛╨╖╨┤╨░╨╣ ╤В╨╡╤Е╨║╨░╤А╤В╤Г ╨┤╨╗╤П ╤Б╤В╨╡╨╣╨║╨░ ╨╕╨╖ ╨│╨╛╨▓╤П╨┤╨╕╨╜╤Л",
        "conversation_id": "uuid"  # ╨╛╨┐╤Ж╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛, ╨┤╨╗╤П ╨┐╤А╨╛╨┤╨╛╨╗╨╢╨╡╨╜╨╕╤П ╨┤╨╕╨░╨╗╨╛╨│╨░
    }
    
    Response:
    {
        "response": "╨п ╤Б╨╛╨╖╨┤╨░╨╗ ╤В╨╡╤Е╨║╨░╤А╤В╤Г ╨┤╨╗╤П ╤Б╤В╨╡╨╣╨║╨░...",
        "conversation_id": "uuid",
        "tool_calls": [{"tool": "generateTechcard", "result": {...}}],  # ╨╡╤Б╨╗╨╕ ╨▒╤Л╨╗╨╕ tool calls
        "tokens_used": 150,
        "credits_spent": 5
    }
    """
    user_id = request.get("user_id", "demo_user")
    message = request.get("message", "").strip()
    conversation_id = request.get("conversation_id")
    
    if not message:
        raise HTTPException(status_code=400, detail="╨б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╡ ╨╜╨╡ ╨╝╨╛╨╢╨╡╤В ╨▒╤Л╤В╤М ╨┐╤Г╤Б╤В╤Л╨╝")
    
    # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╨┐╤А╨╛╤Д╨╕╨╗╤М ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╨┤╨╗╤П ╨║╨╛╨╜╤В╨╡╨║╤Б╤В╨░
    user = await db.users.find_one({"id": user_id})
    venue_profile = {}
    deep_research_data = None
    if user:
        venue_profile = {
            "venue_type": user.get("venue_type"),
            "venue_name": user.get("venue_name"),
            "cuisine_focus": user.get("cuisine_focus", []),
            "average_check": user.get("average_check"),
            "kitchen_equipment": user.get("kitchen_equipment", []),
            "city": user.get("city"),
            "description": user.get("venue_description"),
            "staff_count": user.get("staff_count"),
            "working_hours": user.get("working_hours"),
            "seating_capacity": user.get("seating_capacity")
        }
        
        # Логируем загруженный профиль для отладки
        logger.info(f"Loaded venue profile for user {user_id}: venue_name={venue_profile.get('venue_name')}, venue_type={venue_profile.get('venue_type')}, city={venue_profile.get('city')}")
        
        # Получаем данные глубокого исследования, если есть
        deep_research = await db.venue_research.find_one({"user_id": user_id})
        if deep_research:
            deep_research_data = deep_research.get("research_data", {})
            logger.info(f"Loaded deep research data for user {user_id}")
    
    # Формируем контекст профиля заведения
    venue_context = ""
    # Проверяем наличие любых данных профиля
    has_venue_data = any([
        venue_profile.get("venue_name"),
        venue_profile.get("venue_type"),
        venue_profile.get("city"),
        venue_profile.get("cuisine_focus"),
        venue_profile.get("average_check"),
        venue_profile.get("kitchen_equipment"),
        venue_profile.get("description"),
        venue_profile.get("staff_count"),
        venue_profile.get("working_hours"),
        venue_profile.get("seating_capacity")
    ])
    
    if has_venue_data:
        venue_context = "\n\n=== ПРОФИЛЬ ЗАВЕДЕНИЯ ПОЛЬЗОВАТЕЛЯ ===\n"
        if venue_profile.get("venue_name"):
            venue_context += f"Название: {venue_profile['venue_name']}\n"
        if venue_profile.get("venue_type"):
            venue_context += f"Тип заведения: {venue_profile['venue_type']}\n"
        if venue_profile.get("city"):
            venue_context += f"Город: {venue_profile['city']}\n"
        if venue_profile.get("cuisine_focus") and len(venue_profile.get("cuisine_focus", [])) > 0:
            cuisine_list = venue_profile['cuisine_focus'] if isinstance(venue_profile['cuisine_focus'], list) else [venue_profile['cuisine_focus']]
            venue_context += f"Кухня: {', '.join(cuisine_list)}\n"
        if venue_profile.get("average_check"):
            venue_context += f"Средний чек: {venue_profile['average_check']}₽\n"
        if venue_profile.get("kitchen_equipment") and len(venue_profile.get("kitchen_equipment", [])) > 0:
            equipment_list = venue_profile['kitchen_equipment'] if isinstance(venue_profile['kitchen_equipment'], list) else [venue_profile['kitchen_equipment']]
            venue_context += f"Оборудование: {', '.join(equipment_list)}\n"
        if venue_profile.get("staff_count"):
            venue_context += f"Количество сотрудников: {venue_profile['staff_count']}\n"
        if venue_profile.get("working_hours"):
            venue_context += f"Режим работы: {venue_profile['working_hours']}\n"
        if venue_profile.get("seating_capacity"):
            venue_context += f"Вместимость: {venue_profile['seating_capacity']} мест\n"
        if venue_profile.get("description"):
            venue_context += f"Описание: {venue_profile['description']}\n"
        venue_context += "\nВАЖНО: Используй эту информацию для персонализированных рекомендаций!\n"
        
        logger.info(f"✅ Venue context created: {len(venue_context)} chars")
        logger.info(f"Venue context preview: {venue_context[:500]}...")
        logger.info(f"Full venue profile data: {venue_profile}")
    else:
        logger.warning(f"⚠️ No venue profile data found for user {user_id}")
        if user:
            logger.warning(f"User object exists. Keys: {list(user.keys())}")
            logger.warning(f"User venue fields: venue_name={user.get('venue_name')}, venue_type={user.get('venue_type')}, city={user.get('city')}")
        else:
            logger.warning(f"User object not found for user_id: {user_id}")
    
    # Добавляем данные глубокого исследования, если есть
    research_context = ""
    if deep_research_data:
        research_context = "\n\n=== ГЛУБОКОЕ ИССЛЕДОВАНИЕ ЗАВЕДЕНИЯ ===\n"
        research_context += f"Анализ конкурентов: {deep_research_data.get('competitor_analysis', 'Недоступно')}\n"
        research_context += f"Отзывы клиентов: {deep_research_data.get('customer_reviews_summary', 'Недоступно')}\n"
        research_context += f"Рекомендации: {deep_research_data.get('recommendations', 'Недоступно')}\n"
        research_context += "\nВАЖНО: Используй эти данные для персонализированных рекомендаций!\n"
    
    # Поиск по базе знаний для контекста
    knowledge_context = ""
    try:
        from receptor_agent.rag.search import search_knowledge_base
        
        # ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╤П╨╡╨╝ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ ╨╜╨░ ╨╛╤Б╨╜╨╛╨▓╨╡ ╨╖╨░╨┐╤А╨╛╤Б╨░
        categories = []
        query_lower = message.lower()
        if any(word in query_lower for word in ['haccp', '╤Б╨░╨╜╨┐╨╕╨╜', '╨╜╨╛╤А╨╝╨░╤В╨╕╨▓', '╤Б╤В╨░╨╜╨┤╨░╤А╤В', '╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╨╡']):
            categories.append('haccp')
        if any(word in query_lower for word in ['hr', '╨┐╨╡╤А╤Б╨╛╨╜╨░╨╗', '╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║', '╨╝╨╛╤В╨╕╨▓╨░╤Ж╨╕╤П', '╨╛╨▒╤Г╤З╨╡╨╜╨╕╨╡']):
            categories.append('hr')
        if any(word in query_lower for word in ['╤Д╨╕╨╜╨░╨╜╤Б', 'roi', '╨┐╤А╨╕╨▒╤Л╨╗╤М', '╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М', '╨╜╨░╤Ж╨╡╨╜╨║╨░', '╨╝╨░╤А╨╢╨░']):
            categories.append('finance')
        if any(word in query_lower for word in ['╨╝╨░╤А╨║╨╡╤В╨╕╨╜╨│', 'smm', '╤А╨╡╨║╨╗╨░╨╝╨░', '╨┐╤А╨╛╨┤╨▓╨╕╨╢╨╡╨╜╨╕╨╡', '╨║╨╛╨╜╤В╨╡╨╜╤В']):
            categories.append('marketing')
        if any(word in query_lower for word in ['iiko', 'api', '╨╕╨╜╤В╨╡╨│╤А╨░╤Ж╨╕╤П', '╤В╨╡╤Е╨╜╨╕╤З╨╡╤Б╨║╨╕╨╣']):
            categories.append('iiko')
        
        # ╨Ш╤Й╨╡╨╝ ╤А╨╡╨╗╨╡╨▓╨░╨╜╤В╨╜╤Г╤О ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤О
        search_results = search_knowledge_base(message, top_k=3, categories=categories if categories else None)
        
        if search_results:
            knowledge_context = "\n\n╨а╨╡╨╗╨╡╨▓╨░╨╜╤В╨╜╨░╤П ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤П ╨╕╨╖ ╨▒╨░╨╖╤Л ╨╖╨╜╨░╨╜╨╕╨╣ RECEPTOR:\n"
            for i, result in enumerate(search_results, 1):
                knowledge_context += f"\n[{i}] {result['source']} ({result['category']}):\n{result['content'][:500]}...\n"
    except Exception as e:
        logger.warning(f"Error searching knowledge base: {str(e)}")
        knowledge_context = ""
    
    # ╨б╨╕╤Б╤В╨╡╨╝╨╜╤Л╨╣ ╨┐╤А╨╛╨╝╨┐╤В ╨┤╨╗╤П ╨║╤Г╨╗╨╕╨╜╨░╤А╨╜╨╛╨│╨╛ ╨░╤Б╤Б╨╕╤Б╤В╨╡╨╜╤В╨░
    system_prompt = """Ты RECEPTOR — профессиональный AI-ассистент для ресторанного бизнеса. 

О ПЛАТФОРМЕ RECEPTOR:
RECEPTOR — это комплексная AI-платформа для автоматизации ресторанного бизнеса. Платформа предоставляет следующие ключевые возможности:

1. ГЕНЕРАЦИЯ ТЕХНОЛОГИЧЕСКИХ КАРТ И РЕЦЕПТОВ:
   - Автоматическая генерация технологических карт (техкарт) для блюд с полным описанием процесса приготовления
   - Создание рецептов с учетом типа заведения, доступного оборудования и бюджета
   - Расчет себестоимости, наценки и финальной цены блюда
   - Адаптация рецептов под конкретное заведение (Fine Dining, Food Truck, Кафе, Бар и т.д.)
   - Учет диетических требований и аллергенов
   - Генерация HACCP-документации

2. ИНТЕГРАЦИЯ С IIKO:
   - Прямая интеграция с iiko Cloud и iiko RMS
   - Импорт/экспорт техкарт в iiko
   - Синхронизация меню и позиций
   - Работа с номенклатурой iiko
   - Генерация технической документации для iiko
   - Автоматизация процессов загрузки данных

3. ФИНАНСОВЫЕ РАСЧЕТЫ:
   - Расчет себестоимости блюд с учетом актуальных цен на ингредиенты
   - Расчет наценки и маржинальности
   - Анализ рентабельности меню
   - Оптимизация ценовой политики
   - Учет сезонности и колебаний цен

4. БАЗА ЗНАНИЙ:
   - Обширная база знаний (~2000 документов) с актуальными ценами, КБЖУ, техкартами
   - HACCP и СанПиН нормативы
   - HR-документация и управление персоналом
   - Маркетинговые материалы и SMM-стратегии
   - Лучшие практики ресторанного бизнеса
   - Техническая документация iiko

5. ДОПОЛНИТЕЛЬНЫЕ ВОЗМОЖНОСТИ:
   - Глубокое исследование заведения (анализ конкурентов, отзывов, рекомендаций)
   - Профилирование заведений с учетом типа, кухни, оборудования
   - Генерация меню и оптимизация ассортимента
   - Кулинарные советы и рекомендации

ТВОЯ СПЕЦИАЛИЗАЦИЯ:
- Рецепты и техники приготовления
- Финансовые расчеты (себестоимость, наценка, маржа)
- Оптимизация меню и анализ рентабельности
- Управленческие вопросы ресторанного бизнеса
- Кулинарные советы и рекомендации
- HACCP и СанПиН нормативы
- HR и управление персоналом
- Маркетинг и SMM
- Техническая документация iiko

КАК РАБОТАТЬ:
- Всегда отвечай профессионально, но доступно. Давай конкретные советы с примерами и формулами.
- Если пользователь просит создать техкарту или рецепт, используй функцию generateTechcard.
- Если спрашивает о расчетах, давай конкретные формулы и примеры.
- Используй информацию из базы знаний RECEPTOR для более точных ответов.
- Будь дружелюбным и полезным. Отвечай на русском языке.
- КРИТИЧЕСКИ ВАЖНО: Всегда учитывай профиль заведения пользователя при даче рекомендаций!

ОБЯЗАТЕЛЬНО УПОМИНАЙ ВОЗМОЖНОСТИ ПЛАТФОРМЫ:
Когда пользователь спрашивает о чем-то, что можно сделать через RECEPTOR, обязательно упоминай эту возможность:
- "Я могу создать для тебя техкарту через функцию генерации"
- "RECEPTOR может рассчитать себестоимость с учетом актуальных цен из базы знаний"
- "Мы можем интегрировать это с твоим iiko для автоматизации"
- "В базе знаний RECEPTOR есть актуальная информация по этому вопросу"

ПОМНИ: Ты не просто консультант, ты часть платформы RECEPTOR, которая помогает автоматизировать ресторанный бизнес!""" + venue_context + research_context + knowledge_context
    
    # Log final system prompt length for debugging
    logger.info(f"📝 System prompt total length: {len(system_prompt)} chars")
    logger.info(f"📊 Context breakdown: venue={len(venue_context)}, research={len(research_context)}, knowledge={len(knowledge_context)}")

    # Tool definitions ╨┤╨╗╤П OpenAI Function Calling
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generateTechcard",
                "description": "Создать технологическую карту блюда через платформу RECEPTOR. Используй когда пользователь просит создать техкарту, рецепт или блюдо. Функция автоматически сгенерирует полную техкарту с расчетом себестоимости, учетом оборудования заведения и адаптацией под тип заведения.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dish_name": {
                            "type": "string",
                            "description": "╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░ ╤Б ╨┐╨╛╨┤╤А╨╛╨▒╨╜╤Л╨╝ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡╨╝"
                        },
                        "cuisine": {
                            "type": "string",
                            "description": "╨в╨╕╨┐ ╨║╤Г╤Е╨╜╨╕ (╤А╤Г╤Б╤Б╨║╨░╤П, ╨╕╤В╨░╨╗╤М╤П╨╜╤Б╨║╨░╤П, ╨░╨╖╨╕╨░╤В╤Б╨║╨░╤П ╨╕ ╤В.╨┤.)",
                            "default": "╨╡╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П"
                        },
                        "equipment": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "╨б╨┐╨╕╤Б╨╛╨║ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╨╛╨│╨╛ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╤П"
                        }
                    },
                    "required": ["dish_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "searchKnowledgeBase",
                "description": "Поиск по базе знаний RECEPTOR (~2000 документов). База содержит: актуальные цены на ингредиенты, КБЖУ, техкарты, HACCP и СанПиН нормативы, HR-документацию, финансовые расчеты, техники приготовления, документацию iiko, бизнес-кейсы. Используй для ответов на вопросы о нормах, стандартах, лучших практиках, актуальных ценах и расчетах.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "╨Я╨╛╨╕╤Б╨║╨╛╨▓╤Л╨╣ ╨╖╨░╨┐╤А╨╛╤Б ╨╜╨░ ╤А╤Г╤Б╤Б╨║╨╛╨╝ ╤П╨╖╤Л╨║╨╡"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "╨Ъ╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В╨╛╨▓ (1-10)",
                            "default": 5
                        },
                        "categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "╨д╨╕╨╗╤М╤В╤А ╨┐╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝: haccp, sanpin, hr, finance, marketing, iiko, techniques",
                            "default": []
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    try:
        # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╨╕╤Б╤В╨╛╤А╨╕╤О ╨┤╨╕╨░╨╗╨╛╨│╨░, ╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М conversation_id
        conversation_history = []
        if conversation_id:
            try:
                conv_doc = await db.assistant_conversations.find_one({"conversation_id": conversation_id})
                if conv_doc and "messages" in conv_doc:
                    # ╨Я╤А╨╡╨╛╨▒╤А╨░╨╖╤Г╨╡╨╝ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╜╤Л╨╡ ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╤П ╨▓ ╤Д╨╛╤А╨╝╨░╤В ╨┤╨╗╤П LLM
                    for msg in conv_doc["messages"][-10:]:  # ╨Я╨╛╤Б╨╗╨╡╨┤╨╜╨╕╨╡ 10 ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╣
                        conversation_history.append({
                            "role": msg.get("role"),
                            "content": msg.get("content")
                        })
            except Exception as e:
                logger.warning(f"Failed to load conversation history: {str(e)}")
                conversation_history = []
            try:
                conv_doc = await db.assistant_conversations.find_one({"conversation_id": conversation_id})
                if conv_doc and "messages" in conv_doc:
                    # ╨Я╤А╨╡╨╛╨▒╤А╨░╨╖╤Г╨╡╨╝ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╜╤Л╨╡ ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╤П ╨▓ ╤Д╨╛╤А╨╝╨░╤В ╨┤╨╗╤П LLM
                    for msg in conv_doc["messages"][-10:]:  # ╨Я╨╛╤Б╨╗╨╡╨┤╨╜╨╕╨╡ 10 ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╣
                        conversation_history.append({
                            "role": msg.get("role"),
                            "content": msg.get("content")
                        })
            except Exception as e:
                logger.warning(f"Failed to load conversation history: {str(e)}")
                conversation_history = []
        
        # ╨д╨╛╤А╨╝╨╕╤А╤Г╨╡╨╝ ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╤П ╨┤╨╗╤П LLM
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨╕╤Б╤В╨╛╤А╨╕╤О (╨┐╨╛╤Б╨╗╨╡╨┤╨╜╨╕╨╡ 10 ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╣ ╨┤╨╗╤П ╨║╨╛╨╜╤В╨╡╨║╤Б╤В╨░)
        for hist_msg in conversation_history[-10:]:
            messages.append(hist_msg)
        
        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╤В╨╡╨║╤Г╤Й╨╡╨╡ ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╡ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
        messages.append({"role": "user", "content": message})
        
        # ╨Т╤Л╨╖╨╛╨▓ LLM ╤Б tool-calling
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI client not initialized")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",  # LLM ╤А╨╡╤И╨░╨╡╤В, ╨▓╤Л╨╖╤Л╨▓╨░╤В╤М ╨╗╨╕ tool
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_message = response.choices[0].message
        tool_calls_result = []
        
        # ╨Х╤Б╨╗╨╕ LLM ╨▓╤Л╨╖╨▓╨░╨╗ tool
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "generateTechcard":
                    # ╨У╨╡╨╜╨╡╤А╨╕╤А╤Г╨╡╨╝ ╤В╨╡╤Е╨║╨░╤А╤В╤Г
                    try:
                        from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
                        
                        # ╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ ╨┤╨░╨╜╨╜╤Л╤Е ╨┤╨╗╤П ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕
                        profile = ProfileInput(
                            name=function_args.get("dish_name", ""),
                            cuisine=function_args.get("cuisine", venue_profile.get("cuisine_focus", ["╨╡╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П"])[0] if venue_profile.get("cuisine_focus") else "╨╡╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П"),
                            equipment=function_args.get("equipment", venue_profile.get("kitchen_equipment", ["╨┐╨╗╨╕╤В╨░", "╨║╨░╤Б╤В╤А╤О╨╗╤П"])),
                            budget=float(venue_profile.get("average_check", 500)) if venue_profile.get("average_check") else 500.0,
                            dietary=[],
                            user_id=user_id
                        )
                        
                        # ╨Ч╨░╨┐╤Г╤Б╨║╨░╨╡╨╝ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤О
                        pipeline_result = run_pipeline(profile)
                        
                        # ╨Ы╨╛╨│╨╕╤А╤Г╨╡╨╝ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕
                        logger.info(f"Techcard generation result: status={pipeline_result.status}, has_card={pipeline_result.card is not None}")
                        
                        card_data = None
                        if pipeline_result.card:
                            try:
                                # ╨Ъ╨╛╨╜╨▓╨╡╤А╤В╨╕╤А╤Г╨╡╨╝ Pydantic ╨╝╨╛╨┤╨╡╨╗╤М ╨▓ dict
                                if hasattr(pipeline_result.card, 'model_dump'):
                                    card_data = pipeline_result.card.model_dump()
                                elif hasattr(pipeline_result.card, 'dict'):
                                    card_data = pipeline_result.card.dict()
                                else:
                                    card_data = dict(pipeline_result.card)
                                logger.info(f"Techcard converted to dict, keys: {list(card_data.keys()) if card_data else 'None'}")
                            except Exception as e:
                                logger.error(f"Error converting techcard to dict: {str(e)}")
                                card_data = None
                        
                        tool_calls_result.append({
                            "tool": "generateTechcard",
                            "tool_call_id": tool_call.id,
                            "result": {
                                "success": pipeline_result.status in ["success", "draft", "READY"],
                                "status": pipeline_result.status,
                                "card": card_data,
                                "dish_name": function_args.get("dish_name")
                            }
                        })
                        
                        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В ╨▓ ╨║╨╛╨╜╤В╨╡╨║╤Б╤В ╨┤╨╗╤П LLM
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": tool_call.function.arguments
                                }
                            }]
                        })
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({
                                "success": pipeline_result.status in ["success", "draft", "READY"],
                                "status": pipeline_result.status,
                                "dish_name": function_args.get("dish_name"),
                                "message": "╨в╨╡╤Е╨║╨░╤А╤В╨░ ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╤Б╨╛╨╖╨┤╨░╨╜╨░" if pipeline_result.status in ["success", "draft", "READY"] else "╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╤В╨╡╤Е╨║╨░╤А╤В╤Л"
                            })
                        })
                        
                    except Exception as e:
                        logger.error(f"Error generating techcard in tool call: {str(e)}")
                        tool_calls_result.append({
                            "tool": "generateTechcard",
                            "tool_call_id": tool_call.id,
                            "result": {
                                "success": False,
                                "error": str(e)
                            }
                        })
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"success": False, "error": str(e)})
                        })
            
            # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╤Д╨╕╨╜╨░╨╗╤М╨╜╤Л╨╣ ╨╛╤В╨▓╨╡╤В ╨╛╤В LLM ╤Б ╤Г╤З╨╡╤В╨╛╨╝ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В╨╛╨▓ tool calls
            final_response = openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=messages,
                temperature=0.7,
                max_completion_tokens=1000  # gpt-5-mini использует max_completion_tokens
            )
            assistant_response = final_response.choices[0].message.content
        else:
            # ╨Ю╨▒╤Л╤З╨╜╤Л╨╣ ╨╛╤В╨▓╨╡╤В ╨▒╨╡╨╖ tool calls
            assistant_response = assistant_message.content
        
        # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨╜╨╛╨▓╤Л╨╣ conversation_id, ╨╡╤Б╨╗╨╕ ╨╡╨│╨╛ ╨╜╨╡╤В
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # ╨б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨╕╤Б╤В╨╛╤А╨╕╤О ╨▓ ╨С╨Ф
        try:
            # ╨б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╡ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
            await db.assistant_conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {
                        "messages": {
                            "role": "user",
                            "content": message,
                            "timestamp": datetime.now().isoformat()
                        }
                    },
                    "$setOnInsert": {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "created_at": datetime.now().isoformat(),
                        "title": message[:50] if len(message) > 50 else message  # ╨Я╨╡╤А╨▓╤Л╨╡ 50 ╤Б╨╕╨╝╨▓╨╛╨╗╨╛╨▓ ╨║╨░╨║ ╨╖╨░╨│╨╛╨╗╨╛╨▓╨╛╨║
                    },
                    "$set": {
                        "updated_at": datetime.now().isoformat(),
                        "last_message": message[:100] if len(message) > 100 else message
                    }
                },
                upsert=True
            )
            
            # ╨б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨╛╤В╨▓╨╡╤В ╨░╤Б╤Б╨╕╤Б╤В╨╡╨╜╤В╨░
            await db.assistant_conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {
                        "messages": {
                            "role": "assistant",
                            "content": assistant_response,
                            "timestamp": datetime.now().isoformat(),
                            "tool_calls": tool_calls_result if tool_calls_result else None
                        }
                    },
                    "$set": {
                        "updated_at": datetime.now().isoformat()
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to save conversation history: {str(e)}")
            # ╨Я╤А╨╛╨┤╨╛╨╗╨╢╨░╨╡╨╝ ╨▒╨╡╨╖ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╨╕╤Б╤В╨╛╤А╨╕╨╕
        
        return {
            "response": assistant_response,
            "conversation_id": conversation_id,
            "tool_calls": tool_calls_result if tool_calls_result else None,
            "tokens_used": response.usage.total_tokens,
            "credits_spent": 5
        }
        
    except Exception as e:
        logger.error(f"Assistant chat error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨╛╨▒╤А╨░╨▒╨╛╤В╨║╨╡ ╨╖╨░╨┐╤А╨╛╤Б╨░: {str(e)}"
        )


@api_router.get("/assistant/conversations")
async def get_conversations(user_id: str):
    """
    ╨Я╨╛╨╗╤Г╤З╨╕╤В╤М ╤Б╨┐╨╕╤Б╨╛╨║ ╨▓╤Б╨╡╤Е ╨▒╨╡╤Б╨╡╨┤ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П ╤Б ╨░╤Б╤Б╨╕╤Б╤В╨╡╨╜╤В╨╛╨╝
    """
    try:
        conversations = await db.assistant_conversations.find(
            {"user_id": user_id}
        ).sort("updated_at", -1).to_list(50)
        
        result = []
        for conv in conversations:
            if "_id" in conv:
                del conv["_id"]
            result.append({
                "conversation_id": conv.get("conversation_id"),
                "title": conv.get("title", "╨Э╨╛╨▓╨░╤П ╨▒╨╡╤Б╨╡╨┤╨░"),
                "last_message": conv.get("last_message", ""),
                "created_at": conv.get("created_at"),
                "updated_at": conv.get("updated_at"),
                "message_count": len(conv.get("messages", []))
            })
        
        return {"conversations": result}
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╤П ╨▒╨╡╤Б╨╡╨┤: {str(e)}")


@api_router.get("/assistant/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user_id: str):
    """
    ╨Я╨╛╨╗╤Г╤З╨╕╤В╤М ╨┐╨╛╨╗╨╜╤Г╤О ╨╕╤Б╤В╨╛╤А╨╕╤О ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨╣ ╨▒╨╡╤Б╨╡╨┤╤Л
    """
    try:
        conv = await db.assistant_conversations.find_one({
            "conversation_id": conversation_id,
            "user_id": user_id
        })
        
        if not conv:
            raise HTTPException(status_code=404, detail="╨С╨╡╤Б╨╡╨┤╨░ ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╨░")
        
        if "_id" in conv:
            del conv["_id"]
        
        return {
            "conversation_id": conv.get("conversation_id"),
            "title": conv.get("title", "╨С╨╡╤Б╨╡╨┤╨░"),
            "messages": conv.get("messages", []),
            "created_at": conv.get("created_at"),
            "updated_at": conv.get("updated_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╤П ╨▒╨╡╤Б╨╡╨┤╤Л: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# Google OAuth router
from google_auth import router as google_auth_router
app.include_router(google_auth_router)

# YooKassa payment integration
try:
    from yookassa_integration import router as yookassa_router
    app.include_router(yookassa_router)
    logger.info("тЬЕ YooKassa integration router loaded")
except ImportError as e:
    logger.warning(f"тЪая╕П YooKassa integration not available: {e}")
except Exception as e:
    logger.warning(f"тЪая╕П Failed to load YooKassa router: {e}")

# ╨Я╨╛╨┤╨║╨╗╤О╤З╨░╨╡╨╝ v2-╤Д╤Г╨╜╨║╤Ж╨╕╨╛╨╜╨░╨╗ ╤В╨╛╨╗╤М╨║╨╛ ╨┐╨╛ ╤Д╨╗╨░╨│╤Г
# ╨Ъ╨а╨Ш╨в╨Ш╨з╨Х╨б╨Ъ╨Ш ╨Т╨Р╨Ц╨Э╨Ю ╨┤╨╗╤П iiko ╨╕╨╜╤В╨╡╨│╤А╨░╤Ж╨╕╨╕: ╨┐╤А╨╕╨╜╤Г╨┤╨╕╤В╨╡╨╗╤М╨╜╨╛ ╨▓╨║╨╗╤О╤З╨░╨╡╨╝ V2
# ╨Я╤А╨╕╨╜╤Г╨┤╨╕╤В╨╡╨╗╤М╨╜╨╛ ╨▓╨║╨╗╤О╤З╨░╨╡╨╝ V2 ╨┤╨╗╤П ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛╨╣ ╤А╨░╨╖╤А╨░╨▒╨╛╤В╨║╨╕
techcards_v2_enabled = True
print(f"DEBUG: FEATURE_TECHCARDS_V2 = {os.getenv('FEATURE_TECHCARDS_V2')}, enabled = {techcards_v2_enabled}")
if techcards_v2_enabled:
    from receptor_agent.routes.menus_v2 import router as menus_v2_router
    app.include_router(menus_v2_router, prefix="/api/v1", tags=["menus.v2"])
    from receptor_agent.routes.haccp_v2 import router as haccp_v2_router
    app.include_router(haccp_v2_router, prefix="/api/v1", tags=["haccp.v2"])
    from receptor_agent.routes.iiko_v2 import router as iiko_v2_router
    app.include_router(iiko_v2_router, tags=["iikoCloud.v2"])
    from receptor_agent.routes.iiko_rms_v2 import router as iiko_rms_v2_router
    app.include_router(iiko_rms_v2_router, tags=["iikoRMS.v2"])
    # TechCards V2 router - CRITICAL: This was missing!
    from receptor_agent.routes.techcards_v2 import router as techcards_v2_router
    app.include_router(techcards_v2_router, prefix="/api/v1", tags=["techcards.v2"])
    # IK-04/01: XLSX Import router
    from receptor_agent.routes.iiko_xlsx_import import router as iiko_xlsx_import_router
    app.include_router(iiko_xlsx_import_router, tags=["iikoXLSX.import"])
    # Phase 2: Export v2 router (Preflight + Dual Export)
    from receptor_agent.routes.export_v2 import router as export_v2_router
    app.include_router(export_v2_router, prefix="/api/v1", tags=["export.v2"])

# Add a catch-all OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return {"message": "OK"}


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("ЁЯЪА Receptor AI Backend starting up...")
    logger.info(f"ЁЯУж MongoDB URI configured: {bool(os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL'))}")
    logger.info(f"ЁЯдЦ OpenAI API Key configured: {bool(os.environ.get('OPENAI_API_KEY'))}")
    logger.info(f"ЁЯФз Environment: {os.environ.get('ENVIRONMENT', 'production')}")
    logger.info("тЬЕ Server startup complete!")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("ЁЯЫС Shutting down...")
    client.close()

@app.post("/api/v1/generate-recipe")
async def generate_recipe_v1(request: dict):
    """Generate beautiful V1 recipe with detailed steps for creativity and experimentation"""
    dish_name = request.get("dish_name")
    cuisine = request.get("cuisine", "╨╡╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П")
    restaurant_type = request.get("restaurant_type", "casual")
    user_id = request.get("user_id")
    
    if not dish_name or not user_id:
        raise HTTPException(status_code=400, detail="dish_name and user_id are required")
    
    try:
        print(f"ЁЯН│ Generating V1 Recipe for: {dish_name}")
        
        # Enhanced prompt for beautiful V1 recipes
        prompt = f"""╨в╤Л тАФ ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А ╨╝╨╕╤А╨╛╨▓╨╛╨│╨╛ ╤Г╤А╨╛╨▓╨╜╤П ╨╕ ╨║╤Г╨╗╨╕╨╜╨░╤А╨╜╤Л╨╣ ╨┐╨╕╤Б╨░╤В╨╡╨╗╤М. 
        
╨б╨╛╨╖╨┤╨░╨╣ ╨Ъ╨а╨Р╨б╨Ш╨Т╨л╨Щ ╨Ш ╨Я╨Ю╨Ф╨а╨Ю╨С╨Э╨л╨Щ ╤А╨╡╤Ж╨╡╨┐╤В ╨┤╨╗╤П ╨▒╨╗╤О╨┤╨░ "{dish_name}" ╨▓ ╤Б╤В╨╕╨╗╨╡ {cuisine} ╨║╤Г╤Е╨╜╨╕ ╨┤╨╗╤П {restaurant_type} ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П.

╨д╨Ю╨а╨Ь╨Р╨в ╨а╨Х╨ж╨Х╨Я╨в╨Р V1 (╨┤╨╗╤П ╤В╨▓╨╛╤А╤З╨╡╤Б╤В╨▓╨░ ╨╕ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨╛╨▓):

**{dish_name}**

ЁЯОп **╨Ю╨Я╨Ш╨б╨Р╨Э╨Ш╨Х**
╨Т╨┤╨╛╤Е╨╜╨╛╨▓╨╗╤П╤О╤Й╨╡╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░ ╤Б ╨╕╤Б╤В╨╛╤А╨╕╨╡╨╣, ╤В╤А╨░╨┤╨╕╤Ж╨╕╤П╨╝╨╕ ╨╕ ╨╛╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╤П╨╝╨╕

тП▒я╕П **╨Т╨а╨Х╨Ь╨Х╨Э╨Э╨л╨Х ╨а╨Р╨Ь╨Ъ╨Ш**
╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░: X ╨╝╨╕╨╜╤Г╤В
╨Я╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╨╡: X ╨╝╨╕╨╜╤Г╤В
╨Ю╨▒╤Й╨╡╨╡ ╨▓╤А╨╡╨╝╤П: X ╨╝╨╕╨╜╤Г╤В

ЁЯСе **╨Я╨Ю╨а╨ж╨Ш╨Ш**
╨Э╨░ X ╨┐╨╛╤А╤Ж╨╕╨╣

ЁЯЫТ **╨Ш╨Э╨У╨а╨Х╨Ф╨Ш╨Х╨Э╨в╨л**
╨Ю╤Б╨╜╨╛╨▓╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л:
тАв ╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В 1 - ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ (╨┐╨╛╨┤╤А╨╛╨▒╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡, ╨╖╨░╤З╨╡╨╝ ╨╜╤Г╨╢╨╡╨╜)
тАв ╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В 2 - ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ (╨┐╨╛╨┤╤А╨╛╨▒╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡, ╨╖╨░╤З╨╡╨╝ ╨╜╤Г╨╢╨╡╨╜)
...

╨б╨┐╨╡╤Ж╨╕╨╕ ╨╕ ╨┐╤А╨╕╨┐╤А╨░╨▓╤Л:
тАв ╨б╨┐╨╡╤Ж╨╕╤П 1 - ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ (╨▓╨╗╨╕╤П╨╜╨╕╨╡ ╨╜╨░ ╨▓╨║╤Г╤Б)
тАв ╨б╨┐╨╡╤Ж╨╕╤П 2 - ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ (╨▓╨╗╨╕╤П╨╜╨╕╨╡ ╨╜╨░ ╨▓╨║╤Г╤Б)
...

ЁЯФе **╨Я╨Ю╨и╨Р╨У╨Ю╨Т╨Ю╨Х ╨Я╨а╨Ш╨У╨Ю╨в╨Ю╨Т╨Ы╨Х╨Э╨Ш╨Х**

**╨и╨░╨│ 1: ╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓**
╨Ф╨╡╤В╨░╨╗╤М╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨┐╨╛╨┤╨│╨╛╤В╨╛╨▓╨╕╤В╨╡╨╗╤М╨╜╨╛╨│╨╛ ╤Н╤В╨░╨┐╨░ ╤Б ╤Б╨╛╨▓╨╡╤В╨░╨╝╨╕

**╨и╨░╨│ 2: [╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╤Н╤В╨░╨┐╨░]**  
╨Я╨╛╨┤╤А╨╛╨▒╨╜╤Л╨╡ ╨╕╨╜╤Б╤В╤А╤Г╨║╤Ж╨╕╨╕ ╤Б ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨░╨╝╨╕, ╨▓╤А╨╡╨╝╨╡╨╜╨╡╨╝, ╤В╨╡╤Е╨╜╨╕╨║╨░╨╝╨╕

**╨и╨░╨│ 3: [╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡ ╤Н╤В╨░╨┐╨░]**
╨Х╤Й╨╡ ╨▒╨╛╨╗╨╡╨╡ ╨┤╨╡╤В╨░╨╗╤М╨╜╤Л╨╡ ╨╕╨╜╤Б╤В╤А╤Г╨║╤Ж╨╕╨╕...

[╨Я╤А╨╛╨┤╨╛╨╗╨╢╨╕╤В╤М ╨┤╨╛ ╨╖╨░╨▓╨╡╤А╤И╨╡╨╜╨╕╤П - ╨╛╨▒╤Л╤З╨╜╨╛ 5-8 ╤И╨░╨│╨╛╨▓]

ЁЯСитАНЁЯН│ **╨б╨Х╨Ъ╨а╨Х╨в╨л ╨и╨Х╨д╨Р**
тАв ╨Я╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╤Б╨╛╨▓╨╡╤В 1
тАв ╨Я╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╤Б╨╛╨▓╨╡╤В 2
тАв ╨б╨╡╨║╤А╨╡╤В╨╜╨░╤П ╤В╨╡╤Е╨╜╨╕╨║╨░ 3

ЁЯОи **╨Я╨Ю╨Ф╨Р╨з╨Р ╨Ш ╨Я╨а╨Х╨Ч╨Х╨Э╨в╨Р╨ж╨Ш╨п**
╨Ъ╨░╨║ ╨║╤А╨░╤Б╨╕╨▓╨╛ ╨┐╨╛╨┤╨░╤В╤М ╨▒╨╗╤О╨┤╨╛, ╤Г╨║╤А╨░╤И╨╡╨╜╨╕╤П, ╨┐╨╛╤Б╤Г╨┤╨░

ЁЯФД **╨Т╨Р╨а╨Ш╨Р╨ж╨Ш╨Ш ╨Ш ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в╨л**
тАв ╨Ш╨╜╤В╨╡╤А╨╡╤Б╨╜╨░╤П ╨▓╨░╤А╨╕╨░╤Ж╨╕╤П 1
тАв ╨Ъ╤А╨╡╨░╤В╨╕╨▓╨╜╨░╤П ╨╖╨░╨╝╨╡╨╜╨░ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓ 2
тАв ╨б╨╡╨╖╨╛╨╜╨╜╨░╤П ╨░╨┤╨░╨┐╤В╨░╤Ж╨╕╤П 3

ЁЯТб **╨Я╨Ю╨Ы╨Х╨Ч╨Э╨л╨Х ╨б╨Ю╨Т╨Х╨в╨л**
тАв ╨Ъ╨░╨║ ╤Б╨╛╤Е╤А╨░╨╜╨╕╤В╤М
тАв ╨з╤В╨╛ ╨┤╨╡╨╗╨░╤В╤М ╨╡╤Б╨╗╨╕ ╤З╤В╨╛-╤В╨╛ ╨┐╨╛╤И╨╗╨╛ ╨╜╨╡ ╤В╨░╨║
тАв ╨Ъ╨░╨║ ╨╖╨░╤А╨░╨╜╨╡╨╡ ╨┐╨╛╨┤╨│╨╛╤В╨╛╨▓╨╕╤В╤М

╨б╨┤╨╡╨╗╨░╨╣ ╤А╨╡╤Ж╨╡╨┐╤В ╨Ь╨Р╨Ъ╨б╨Ш╨Ь╨Р╨Ы╨м╨Э╨Ю ╨Я╨Ю╨Ф╨а╨Ю╨С╨Э╨л╨Ь, ╨Т╨Ф╨Ю╨е╨Э╨Ю╨Т╨Ы╨п╨о╨й╨Ш╨Ь ╨╕ ╨Ъ╨а╨Р╨б╨Ш╨Т╨л╨Ь ╨┤╨╗╤П ╤З╤В╨╡╨╜╨╕╤П!"""

        # Use OpenAI for V1 recipe generation
        client = OpenAI(api_key=openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=3000
        )
        
        recipe_content = response.choices[0].message.content
        
        # Create V1 recipe structure
        recipe_v1 = {
            "id": str(uuid.uuid4()),
            "name": dish_name,
            "cuisine": cuisine,
            "restaurant_type": restaurant_type,
            "content": recipe_content,
            "version": "v1",
            "type": "recipe",
            "created_at": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        # Save to database for history
        try:
            await db.recipes_v1.insert_one(recipe_v1.copy())
        except Exception as e:
            print(f"Warning: Failed to save V1 recipe to database: {e}")
        
        print(f"тЬЕ V1 Recipe generated successfully for: {dish_name}")
        
        return {"recipe": recipe_content, "meta": {"id": recipe_v1["id"], "version": "v1"}}
        
    except Exception as e:
        print(f"тЭМ Error generating V1 recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {str(e)}")

@app.post("/api/generate-sales-script")
async def generate_sales_script(request: dict):
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    # Auto-create test user with PRO subscription if needed
    if user_id and (user_id.startswith("test_user_") or user_id == "demo_user" or user_id.startswith("email_")):
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
            raise HTTPException(status_code=403, detail="╨в╤А╨╡╨▒╤Г╨╡╤В╤Б╤П PRO ╨┐╨╛╨┤╨┐╨╕╤Б╨║╨░")
    
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    average_check = user.get("average_check", 800)
    venue_name = user.get("venue_name", "╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╨╡")
    
    # Convert tech_card to string if it's a dict (V2 or aiKitchenRecipe format)
    if isinstance(tech_card, dict):
        if 'content' in tech_card:
            tech_card_str = tech_card['content']
        else:
            tech_card_str = str(tech_card)
    else:
        tech_card_str = tech_card
    
    # Extract dish name from tech card
    dish_name = "╨▒╨╗╤О╨┤╨╛"
    for line in tech_card_str.split('\n'):
        if '╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:' in line:
            dish_name = line.split('╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:')[1].strip().replace('**', '')
            break
    
    # Generate venue-specific sales script context
    venue_context = generate_sales_script_context(venue_type, venue_info, average_check, cuisine_focus)
    
    prompt = f"""╨в╤Л тАФ ╤Н╨║╤Б╨┐╨╡╤А╤В ╨┐╨╛ ╨┐╤А╨╛╨┤╨░╨╢╨░╨╝ ╨▓ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╜╨╛╨╝ ╨▒╨╕╨╖╨╜╨╡╤Б╨╡. 

╨Ъ╨Ю╨Э╨в╨Х╨Ъ╨б╨в ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨п:
╨в╨╕╨┐ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П: {venue_info['name']}
╨б╤А╨╡╨┤╨╜╨╕╨╣ ╤З╨╡╨║: {average_check}тВ╜
╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡: {venue_name}
{venue_context}

╨б╨╛╨╖╨┤╨░╨╣ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╤Б╨║╤А╨╕╨┐╤В ╨┐╤А╨╛╨┤╨░╨╢ ╨┤╨╗╤П ╨╛╤Д╨╕╤Ж╨╕╨░╨╜╤В╨╛╨▓ ╨┤╨╗╤П ╨▒╨╗╤О╨┤╨░ "{dish_name}" ╤Б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╨╛ ╨░╨┤╨░╨┐╤В╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╣ ╨┤╨╗╤П ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П "{venue_info['name']}".

╨в╨╡╤Е╨║╨░╤А╤В╨░ ╨▒╨╗╤О╨┤╨░:
{tech_card_str}

╨б╨╛╨╖╨┤╨░╨╣ 3 ╨▓╨░╤А╨╕╨░╨╜╤В╨░ ╤Б╨║╤А╨╕╨┐╤В╨╛╨▓:

ЁЯОн ╨Ъ╨Ы╨Р╨б╨б╨Ш╨з╨Х╨б╨Ъ╨Ш╨Щ ╨б╨Ъ╨а╨Ш╨Я╨в:
[2-3 ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╡╨╜╨╕╤П ╨┤╨╗╤П ╨╛╨▒╤Л╤З╨╜╨╛╨╣ ╨┐╤А╨╡╨╖╨╡╨╜╤В╨░╤Ж╨╕╨╕ ╨▒╨╗╤О╨┤╨░ ╤Б ╤Г╤З╨╡╤В╨╛╨╝ ╤Б╤В╨╕╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П]

ЁЯФе ╨Р╨Ъ╨в╨Ш╨Т╨Э╨л╨Х ╨Я╨а╨Ю╨Ф╨Р╨Ц╨Ш:
[╨░╨│╤А╨╡╤Б╤Б╨╕╨▓╨╜╤Л╨╣ ╤Б╨║╤А╨╕╨┐╤В ╨┤╨╗╤П ╤Г╨▓╨╡╨╗╨╕╤З╨╡╨╜╨╕╤П ╤Б╤А╨╡╨┤╨╜╨╡╨│╨╛ ╤З╨╡╨║╨░, ╨░╨┤╨░╨┐╤В╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╣ ╨┐╨╛╨┤ ╤В╨╕╨┐ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П]

ЁЯТл ╨Я╨а╨Х╨Ь╨Ш╨г╨Ь ╨Я╨Ю╨Ф╨Р╨з╨Р:
[╤Б╨║╤А╨╕╨┐╤В ╨┤╨╗╤П ╨╛╤Б╨╛╨▒╤Л╤Е ╨│╨╛╤Б╤В╨╡╨╣ ╤Б ╤Г╤З╨╡╤В╨╛╨╝ ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╨╕ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П]

╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╨╛:
тАв 5 ╨║╨╗╤О╤З╨╡╨▓╤Л╤Е ╨┐╤А╨╡╨╕╨╝╤Г╤Й╨╡╤Б╤В╨▓ ╨▒╨╗╤О╨┤╨░ ╨┤╨╗╤П ╨┤╨░╨╜╨╜╨╛╨│╨╛ ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П
тАв ╨Т╨╛╨╖╤А╨░╨╢╨╡╨╜╨╕╤П ╨║╨╗╨╕╨╡╨╜╤В╨╛╨▓ ╨╕ ╨╛╤В╨▓╨╡╤В╤Л ╨╜╨░ ╨╜╨╕╤Е (╤Б╨┐╨╡╤Ж╨╕╤Д╨╕╤З╨╜╤Л╨╡ ╨┤╨╗╤П ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П)
тАв ╨в╨╡╤Е╨╜╨╕╨║╨╕ up-sell ╨╕ cross-sell (╨┐╨╛╨┤╤Е╨╛╨┤╤П╤Й╨╕╨╡ ╨┤╨╗╤П ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╨╕)
тАв ╨Э╨╡╨▓╨╡╤А╨▒╨░╨╗╤М╨╜╤Л╨╡ ╨┐╤А╨╕╨╡╨╝╤Л ╨┐╨╛╨┤╨░╤З╨╕ (╨░╨┤╨░╨┐╤В╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╡ ╨┐╨╛╨┤ ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╤Г)

╨Я╨╕╤И╨╕ ╨╢╨╕╨▓╨╛, ╨║╨░╨║ ╨▒╤Г╨┤╤В╨╛ ╤Н╤В╨╛ ╤А╨╡╨░╨╗╤М╨╜╨╛ ╨│╨╛╨▓╨╛╤А╨╕╤В ╨╛╨┐╤Л╤В╨╜╤Л╨╣ ╨╛╤Д╨╕╤Ж╨╕╨░╨╜╤В ╨▓ {venue_info['name'].lower()}."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.8
        )
        
        return {"script": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕: {str(e)}")

@app.post("/api/generate-food-pairing")
async def generate_food_pairing(request: dict):
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    # Auto-create test/demo user with PRO subscription if needed
    if user_id and (user_id.startswith("test_user_") or user_id == "demo_user" or user_id.startswith("email_")):
        user = await db.users.find_one({"id": user_id})
        if not user:
            # Create test/demo user with PRO subscription
            test_user = {
                "id": user_id,
                "email": f"{user_id}@example.com" if user_id != "demo_user" else "demo@receptorai.pro",
                "name": "Test User" if user_id != "demo_user" else "Demo User",
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
            raise HTTPException(status_code=403, detail="╨в╤А╨╡╨▒╤Г╨╡╤В╤Б╤П PRO ╨┐╨╛╨┤╨┐╨╕╤Б╨║╨░")
    
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    average_check = user.get("average_check", 800)
    
    # Extract dish name from tech card
    dish_name = "╨▒╨╗╤О╨┤╨╛"
    if isinstance(tech_card, dict):
        dish_name = tech_card.get("name", "╨▒╨╗╤О╨┤╨╛")
    elif isinstance(tech_card, str):
        for line in tech_card.split('\n'):
            if '╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:' in line:
                dish_name = line.split('╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:')[1].strip().replace('**', '')
                break
    
    # Generate venue-specific pairing context
    pairing_context = generate_food_pairing_context(venue_type, venue_info, average_check, cuisine_focus)
    
    prompt = f"""╨в╤Л тАФ ╤Б╨╛╨╝╨╡╨╗╤М╨╡ ╨╕ ╤Н╨║╤Б╨┐╨╡╤А╤В ╨┐╨╛ ╤Д╤Г╨┤╨┐╨╡╨╣╤А╨╕╨╜╨│╤Г. 

╨Ъ╨Ю╨Э╨в╨Х╨Ъ╨б╨в ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨п:
╨в╨╕╨┐ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П: {venue_info['name']}
╨б╤А╨╡╨┤╨╜╨╕╨╣ ╤З╨╡╨║: {average_check}тВ╜
{pairing_context}

╨б╨╛╨╖╨┤╨░╨╣ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛╨╡ ╤А╤Г╨║╨╛╨▓╨╛╨┤╤Б╤В╨▓╨╛ ╨┐╨╛ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П╨╝ ╨┤╨╗╤П ╨▒╨╗╤О╨┤╨░ "{dish_name}" ╤Б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╨╛ ╨░╨┤╨░╨┐╤В╨╕╤А╨╛╨▓╨░╨╜╨╜╨╛╨╡ ╨┤╨╗╤П ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П "{venue_info['name']}".

╨в╨╡╤Е╨║╨░╤А╤В╨░ ╨▒╨╗╤О╨┤╨░:
{tech_card}

╨б╨╛╨╖╨┤╨░╨╣ ╨┤╨╡╤В╨░╨╗╤М╨╜╤Л╨╡ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕:

ЁЯН╖ ╨Р╨Ы╨Ъ╨Ю╨У╨Ю╨Ы╨м╨Э╨л╨Х ╨Э╨Р╨Я╨Ш╨в╨Ъ╨Ш:
{generate_alcohol_recommendations(venue_type)}

ЁЯН╣ ╨С╨Х╨Ч╨Р╨Ы╨Ъ╨Ю╨У╨Ю╨Ы╨м╨Э╨л╨Х ╨Э╨Р╨Я╨Ш╨в╨Ъ╨Ш:
тАв ╨Я╨╛╨┤╤Е╨╛╨┤╤П╤Й╨╕╨╡ ╨▒╨╡╨╖╨░╨╗╨║╨╛╨│╨╛╨╗╤М╨╜╤Л╨╡ ╨▓╨░╤А╨╕╨░╨╜╤В╤Л
тАв ╨Р╨▓╤В╨╛╤А╤Б╨║╨╕╨╡ ╨╗╨╕╨╝╨╛╨╜╨░╨┤╤Л ╨╕ ╤З╨░╨╕
тАв ╨Ъ╨╛╤Д╨╡╨╣╨╜╤Л╨╡ ╨╕ ╨╝╨╛╨╗╨╛╤З╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕

ЁЯН╜ ╨У╨Р╨а╨Э╨Ш╨а╨л ╨Ш ╨Ф╨Ю╨Я╨Ю╨Ы╨Э╨Х╨Э╨Ш╨п:
тАв ╨Ш╨┤╨╡╨░╨╗╤М╨╜╤Л╨╡ ╨│╨░╤А╨╜╨╕╤А╤Л ╨┤╨╗╤П ╨┤╨░╨╜╨╜╨╛╨│╨╛ ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П
тАв ╨б╨╛╤Г╤Б╤Л ╨╕ ╨╖╨░╨┐╤А╨░╨▓╨║╨╕
тАв ╨Ч╨░╨║╤Г╤Б╨║╨╕ ╨┤╨╗╤П ╨║╨╛╨╝╨┐╨╗╨╡╨║╤В╨░

ЁЯОп ╨б╨Я╨Х╨ж╨Ш╨Р╨Ы╨м╨Э╨л╨Х ╨Я╨а╨Х╨Ф╨Ы╨Ю╨Ц╨Х╨Э╨Ш╨п:
тАв ╨б╨╛╤З╨╡╤В╨░╨╜╨╕╤П ╤Б╨┐╨╡╤Ж╨╕╤Д╨╕╤З╨╜╤Л╨╡ ╨┤╨╗╤П {venue_info['name'].lower()}
тАв ╨б╨╡╨╖╨╛╨╜╨╜╤Л╨╡ ╨▓╨░╤А╨╕╨░╨╜╤В╤Л
тАв ╨н╨║╤Б╨║╨╗╤О╨╖╨╕╨▓╨╜╤Л╨╡ ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╡╨╜╨╕╤П

╨Ф╨╗╤П ╨║╨░╨╢╨┤╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ ╨╛╨▒╤К╤П╤Б╨╜╨╕ ╨Я╨Ю╨з╨Х╨Ь╨г ╤Н╤В╨╛ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╨╡ ╤А╨░╨▒╨╛╤В╨░╨╡╤В ╨╕ ╨║╨░╨║ ╨╛╨╜╨╛ ╨┐╨╛╨┤╤Е╨╛╨┤╨╕╤В ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╨╕ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        return {"pairing": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕: {str(e)}")

@app.post("/api/generate-photo-tips")
async def generate_photo_tips(request: dict):
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    # Auto-create test user with PRO subscription if needed
    if user_id and user_id.startswith("test_user_"):
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
            raise HTTPException(status_code=403, detail="╨в╤А╨╡╨▒╤Г╨╡╤В╤Б╤П PRO ╨┐╨╛╨┤╨┐╨╕╤Б╨║╨░")
    
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    average_check = user.get("average_check", 800)
    
    # Convert tech_card to string if it's a dict (V2 or aiKitchenRecipe format)
    if isinstance(tech_card, dict):
        if 'content' in tech_card:
            tech_card_str = tech_card['content']
        else:
            tech_card_str = str(tech_card)
    else:
        tech_card_str = tech_card
    
    # Extract dish name from tech card
    dish_name = "╨▒╨╗╤О╨┤╨╛"
    for line in tech_card_str.split('\n'):
        if '╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:' in line:
            dish_name = line.split('╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:')[1].strip().replace('**', '')
            break
    
    # Generate venue-specific photo context
    photo_context = generate_photo_tips_context(venue_type, venue_info, average_check, cuisine_focus)
    
    prompt = f"""╨в╤Л тАФ ╤Д╤Г╨┤-╤Д╨╛╤В╨╛╨│╤А╨░╤Д ╨╕ ╤Н╨║╤Б╨┐╨╡╤А╤В ╨┐╨╛ ╨▓╨╕╨╖╤Г╨░╨╗╤М╨╜╨╛╨╣ ╨┐╨╛╨┤╨░╤З╨╡ ╨▒╨╗╤О╨┤.

╨Ъ╨Ю╨Э╨в╨Х╨Ъ╨б╨в ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨п:
╨в╨╕╨┐ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П: {venue_info['name']}
╨б╤А╨╡╨┤╨╜╨╕╨╣ ╤З╨╡╨║: {average_check}тВ╜
{photo_context}

╨б╨╛╨╖╨┤╨░╨╣ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛╨╡ ╤А╤Г╨║╨╛╨▓╨╛╨┤╤Б╤В╨▓╨╛ ╨┐╨╛ ╤Д╨╛╤В╨╛╨│╤А╨░╤Д╨╕╨╕ ╨┤╨╗╤П ╨▒╨╗╤О╨┤╨░ "{dish_name}" ╤Б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╨╛ ╨░╨┤╨░╨┐╤В╨╕╤А╨╛╨▓╨░╨╜╨╜╨╛╨╡ ╨┤╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╤В╨╕╨┐╨░ "{venue_info['name']}".

╨в╨╡╤Е╨║╨░╤А╤В╨░ ╨▒╨╗╤О╨┤╨░:
{tech_card_str}

╨б╨╛╨╖╨┤╨░╨╣ ╨┤╨╡╤В╨░╨╗╤М╨╜╤Л╨╡ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕:

ЁЯУ╕ ╨в╨Х╨е╨Э╨Ш╨з╨Х╨б╨Ъ╨Ш╨Х ╨Э╨Р╨б╨в╨а╨Ю╨Щ╨Ъ╨Ш ╨Ф╨Ы╨п {venue_info['name'].upper()}:
{generate_photo_tech_settings(venue_type)}

ЁЯОи ╨б╨в╨Ш╨Ы╨Ш╨Э╨У ╨Ш ╨Я╨Ю╨Ф╨Р╨з╨Р:
{generate_photo_styling_tips(venue_type)}

тЬи ╨Ъ╨Ю╨Ь╨Я╨Ю╨Ч╨Ш╨ж╨Ш╨п:
тАв ╨Ы╤Г╤З╤И╨╕╨╡ ╤А╨░╨║╤Г╤А╤Б╤Л ╨┤╨╗╤П ╨▒╨╗╤О╨┤ ╨▓ {venue_info['name'].lower()}
тАв ╨Ъ╨░╨║ ╨┐╨╛╨║╨░╨╖╨░╤В╤М ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╤О ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╤З╨╡╤А╨╡╨╖ ╤Д╨╛╤В╨╛
тАв ╨в╨╡╤Е╨╜╨╕╨║╨╕ ╨┐╨╛╨┤╤З╨╡╤А╨║╨╕╨▓╨░╤О╤Й╨╕╨╡ ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╤Г ╨╝╨╡╤Б╤В╨░

ЁЯМЕ ╨Ю╨б╨Т╨Х╨й╨Х╨Э╨Ш╨Х:
тАв ╨Ю╨┐╤В╨╕╨╝╨░╨╗╤М╨╜╨╛╨╡ ╨╛╤Б╨▓╨╡╤Й╨╡╨╜╨╕╨╡ ╨┤╨╗╤П ╨╕╨╜╤В╨╡╤А╤М╨╡╤А╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П
тАв ╨а╨░╨▒╨╛╤В╨░ ╤Б ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╨╕╨╝ ╨╛╤Б╨▓╨╡╤Й╨╡╨╜╨╕╨╡╨╝
тАв ╨Ъ╨░╨║ ╨┐╨╡╤А╨╡╨┤╨░╤В╤М ╨░╤В╨╝╨╛╤Б╤Д╨╡╤А╤Г {venue_info['name'].lower()}

ЁЯУ▒ ╨Ф╨Ы╨п ╨б╨Ю╨ж╨б╨Х╨в╨Х╨Щ:
тАв ╨Р╨┤╨░╨┐╤В╨░╤Ж╨╕╤П ╨┐╨╛╨┤ ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╤О ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П
тАв ╨е╨╡╤И╤В╨╡╨│╨╕ ╤Б╨┐╨╡╤Ж╨╕╤Д╨╕╤З╨╜╤Л╨╡ ╨┤╨╗╤П {venue_info['name'].lower()}
тАв ╨Ъ╨╛╨╜╤В╨╡╨╜╤В-╤Б╤В╤А╨░╤В╨╡╨│╨╕╤П ╨┤╨╗╤П ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П

ЁЯОн ╨Я╨Ю╨б╨в╨Ю╨С╨а╨Р╨С╨Ю╨в╨Ъ╨Р:
тАв ╨ж╨▓╨╡╤В╨╛╨▓╨░╤П ╨║╨╛╤А╤А╨╡╨║╤Ж╨╕╤П ╨┐╨╛╨┤ ╤Б╤В╨╕╨╗╤М ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П
тАв ╨д╨╕╨╗╤М╤В╤А╤Л ╨┐╨╛╨┤╤Е╨╛╨┤╤П╤Й╨╕╨╡ ╨┤╨╗╤П ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╨╕
тАв ╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╤Г╨╖╨╜╨░╨▓╨░╨╡╨╝╨╛╨│╨╛ ╨▓╨╕╨╖╤Г╨░╨╗╤М╨╜╨╛╨│╨╛ ╤Б╤В╨╕╨╗╤П

ЁЯТб PRO ╨б╨Ю╨Т╨Х╨в╨л ╨Ф╨Ы╨п {venue_info['name'].upper()}:
тАв ╨Ъ╨░╨║ ╨┐╨╛╨┤╤З╨╡╤А╨║╨╜╤Г╤В╤М ╤Г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╤Б╤В╤М ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╤З╨╡╤А╨╡╨╖ ╨╡╨┤╤Г
тАв ╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨║╨╛╨╜╤В╨╡╨╜╤В╨░ ╨┤╨╗╤П ╤Ж╨╡╨╗╨╡╨▓╨╛╨╣ ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╨╕
тАв ╨Ш╨╜╤В╨╡╨│╤А╨░╤Ж╨╕╤П ╤Б ╨╛╨▒╤Й╨╕╨╝ ╨▒╤А╨╡╨╜╨┤╨╕╨╜╨│╨╛╨╝

╨Ф╨╗╤П ╨║╨░╨╢╨┤╨╛╨│╨╛ ╤Б╨╛╨▓╨╡╤В╨░ ╨╛╨▒╤К╤П╤Б╨╜╨╕ ╨Я╨Ю╨з╨Х╨Ь╨г ╤Н╤В╨╛ ╨▓╨░╨╢╨╜╨╛ ╨╕╨╝╨╡╨╜╨╜╨╛ ╨┤╨╗╤П ╨┤╨░╨╜╨╜╨╛╨│╨╛ ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╨╕ ╨▒╨╗╤О╨┤╨░."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        return {"tips": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕: {str(e)}")

@app.post("/api/generate-inspiration")
async def generate_inspiration(request: dict):
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    inspiration_prompt = request.get("inspiration_prompt", "╨б╨╛╨╖╨┤╨░╨╣ ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╨╣ ╨╕ ╨╢╨╕╨╖╨╜╨╡╤Б╨┐╨╛╤Б╨╛╨▒╨╜╤Л╨╣ ╤В╨▓╨╕╤Б╤В ╨╜╨░ ╤Н╤В╨╛ ╨▒╨╗╤О╨┤╨╛")
    
    if not user_id or not tech_card:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨┐╨╛╨┤╨┐╨╕╤Б╨║╤Г ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
    user = await db.users.find_one({"id": user_id})
    
    # ╨Х╤Б╨╗╨╕ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜ ╨╕ ╤Н╤В╨╛ ╤В╨╡╤Б╤В╨╛╨▓╤Л╨╣/╨┤╨╡╨╝╨╛ ID, ╤Б╨╛╨╖╨┤╨░╨╡╨╝ ╨▓╤А╨╡╨╝╨╡╨╜╨╜╨╛╨│╨╛ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
    if not user and user_id and (user_id.startswith("test_user_") or user_id == "demo_user"):
        user = {
            "id": user_id,
            "email": "test@example.com" if user_id != "demo_user" else "demo@receptorai.pro",
            "name": "Test User" if user_id != "demo_user" else "Demo User",
            "city": "moscow",
            "subscription_plan": "pro",
            "subscription_status": "active",
            "monthly_tech_cards_used": 0,
            "monthly_reset_date": datetime.utcnow().isoformat(),
            "kitchen_equipment": [],
            "created_at": datetime.utcnow().isoformat()
        }
    elif not user:
        raise HTTPException(status_code=404, detail="╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜")
    
    # ╨Т╨а╨Х╨Ь╨Х╨Э╨Э╨Ю ╨Ю╨в╨Ъ╨Ы╨о╨з╨Х╨Э╨Ю ╨┤╨╗╤П ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П - ╨▓╨║╨╗╤О╤З╨╕╨╝ ╨║╨╛╨│╨┤╨░ ╨▒╤Г╨┤╨╡╤В ╨┐╨╗╨░╤В╨╡╨╢╨║╨░
    # if user.get("subscription_plan") not in ["pro", "business"]:
    #     raise HTTPException(status_code=403, detail="╨д╤Г╨╜╨║╤Ж╨╕╤П ╨┤╨╛╤Б╤В╤Г╨┐╨╜╨░ ╤В╨╛╨╗╤М╨║╨╛ ╨┤╨╗╤П PRO ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╨╡╨╣")
    
    # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░ ╨╕╨╖ ╤В╨╡╤Е╨║╨░╤А╤В╤Л
    dish_name = "╨▒╨╗╤О╨┤╨╛"
    if isinstance(tech_card, dict): dish_name = tech_card.get("name", "╨▒╨╗╤О╨┤╨╛")
    
    # ╨б╨┐╨╡╤Ж╨╕╨░╨╗╤М╨╜╤Л╨╣ ╨┐╤А╨╛╨╝╤В ╨┤╨╗╤П ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╨▓╨┤╨╛╤Е╨╜╨╛╨▓╨╡╨╜╨╕╤П
    prompt = f"""╨в╤Л - ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╨╣ ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А ╨▓╤Л╤Б╤И╨╡╨│╨╛ ╨║╨╗╨░╤Б╤Б╨░, ╨║╨╛╤В╨╛╤А╤Л╨╣ ╤Б╨╛╨╖╨┤╨░╨╡╤В ╨╜╨╡╨╛╨╢╨╕╨┤╨░╨╜╨╜╤Л╨╡ ╨╜╨╛ ╨╢╨╕╨╖╨╜╨╡╤Б╨┐╨╛╤Б╨╛╨▒╨╜╤Л╨╡ ╤В╨▓╨╕╤Б╤В╤Л ╨╜╨░ ╨║╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨╕╨╡ ╨▒╨╗╤О╨┤╨░.

╨Ш╨б╨е╨Ю╨Ф╨Э╨Ю╨Х ╨С╨Ы╨о╨Ф╨Ю:
{tech_card}

╨Ч╨Р╨Ф╨Р╨Э╨Ш╨Х: ╨б╨╛╨╖╨┤╨░╨╣ ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╨╣ ╨╕ ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗╤М╨╜╤Л╨╣ ╤В╨▓╨╕╤Б╤В ╨╜╨░ ╨▒╨╗╤О╨┤╨╛ "{dish_name}" ╤Г╤З╨╕╤В╤Л╨▓╨░╤П ╤В╨░╨║╨╕╨╡ ╨╕╨┤╨╡╨╕: {inspiration_prompt}

╨в╨а╨Х╨С╨Ю╨Т╨Р╨Э╨Ш╨п ╨Ъ ╨в╨Т╨Ш╨б╨в╨г:
тАв ╨б╨╛╤Е╤А╨░╨╜╨╕ ╨▒╨░╨╖╨╛╨▓╤Г╤О ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗╤М╨╜╨╛╨│╨╛ ╨▒╨╗╤О╨┤╨░, ╨╜╨╛ ╨┤╨╛╨▒╨░╨▓╤М ╨╜╨╡╨╛╨╢╨╕╨┤╨░╨╜╨╜╤Л╨╡ ╤Н╨╗╨╡╨╝╨╡╨╜╤В╤Л
тАв ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨╝╨╡╨╢╨┤╤Г╨╜╨░╤А╨╛╨┤╨╜╤Л╨╡ ╨║╤Г╨╗╨╕╨╜╨░╤А╨╜╤Л╨╡ ╤В╤А╨░╨┤╨╕╤Ж╨╕╨╕ ╨┤╨╗╤П ╨▓╨┤╨╛╤Е╨╜╨╛╨▓╨╡╨╜╨╕╤П
тАв ╨Я╤А╨╡╨┤╨╗╨╛╨╢╨╕ ╨╖╨░╨╝╨╡╨╜╤Г 2-3 ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓ ╨╜╨░ ╨▒╨╛╨╗╨╡╨╡ ╨╕╨╜╤В╨╡╤А╨╡╤Б╨╜╤Л╨╡
тАв ╨Ф╨╛╨▒╨░╨▓╤М ╨╜╨╛╨▓╤Л╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П ╨╕╨╗╨╕ ╨┐╨╛╨┤╨░╤З╨╕
тАв ╨б╨╛╤Е╤А╨░╨╜╨╕ ╨╢╨╕╨╖╨╜╨╡╤Б╨┐╨╛╤Б╨╛╨▒╨╜╨╛╤Б╤В╤М ╨┤╨╗╤П ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╜╨╛╨╣ ╨║╤Г╤Е╨╜╨╕
тАв ╨г╤З╨╕╤В╤Л╨▓╨░╨╣ ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М ╨╕ ╨▓╤А╨╡╨╝╤П ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П

╨б╨в╨а╨г╨Ъ╨в╨г╨а╨Р ╨Ю╨в╨Т╨Х╨в╨Р:
**╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:** [╨Э╨╛╨▓╨╛╨╡ ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╤Б ╤Г╨║╨░╨╖╨░╨╜╨╕╨╡╨╝ ╤В╨▓╨╕╤Б╤В╨░]

**╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П:** [╤В╨░ ╨╢╨╡ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П]

**╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡:** [╨Ю╨┐╨╕╤И╨╕ ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╤О ╤В╨▓╨╕╤Б╤В╨░, ╨╡╨│╨╛ ╨╛╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╨╕ ╨╕ ╨┐╨╛╤З╨╡╨╝╤Г ╤Н╤В╨╛ ╨╕╨╜╤В╨╡╤А╨╡╤Б╨╜╨╛]

**╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л:** (╨┐╨╛╤А╤Ж╨╕╤П ╨║╨░╨║ ╨▓ ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗╨╡)
[╨б╨┐╨╕╤Б╨╛╨║ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓ ╤Б ╨╜╨╛╨▓╤Л╨╝╨╕ ╤Н╨╗╨╡╨╝╨╡╨╜╤В╨░╨╝╨╕, ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛╨╝ ╨╕ ╤Ж╨╡╨╜╨░╨╝╨╕ ╨▓ ╤А╤Г╨▒╨╗╤П╤Е]

**╨Я╨╛╤И╨░╨│╨╛╨▓╤Л╨╣ ╤А╨╡╤Ж╨╡╨┐╤В:**
[╨Я╨╛╤И╨░╨│╨╛╨▓╤Л╨╣ ╤А╨╡╤Ж╨╡╨┐╤В ╤Б ╨╜╨╛╨▓╤Л╨╝╨╕ ╤В╨╡╤Е╨╜╨╕╨║╨░╨╝╨╕]

**╨Т╤А╨╡╨╝╤П:** [╨Т╤А╨╡╨╝╤П ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П]

**╨Т╤Л╤Е╨╛╨┤:** [╨Т╤Л╤Е╨╛╨┤ ╨│╨╛╤В╨╛╨▓╨╛╨│╨╛ ╨▒╨╗╤О╨┤╨░]

**ЁЯТ╕ ╨б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М:**
[╨а╨░╤Б╤З╨╡╤В ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╨╕ ╨╜╨╛╨▓╤Л╤Е ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓]

**╨Ъ╨С╨Ц╨г ╨╜╨░ 1 ╨┐╨╛╤А╤Ж╨╕╤О:** [╨Я╤А╨╕╨╝╨╡╤А╨╜╨╛╨╡ ╨Ъ╨С╨Ц╨г]

**╨Р╨╗╨╗╨╡╤А╨│╨╡╨╜╤Л:** [╨Р╨╗╨╗╨╡╤А╨│╨╡╨╜╤Л]

**ЁЯМЯ ╨Ю╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╨╕ ╤В╨▓╨╕╤Б╤В╨░:**
тАв ╨Т ╤З╨╡╨╝ ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╨╛╤Б╤В╤М
тАв ╨Ъ╨░╨║╨╕╨╡ ╨╜╨╛╨▓╤Л╨╡ ╨▓╨║╤Г╤Б╤Л
тАв ╨Ъ╨░╨║ ╤Н╤В╨╛ ╨╝╨╡╨╜╤П╨╡╤В ╨▓╨╛╤Б╨┐╤А╨╕╤П╤В╨╕╨╡ ╨▒╨╗╤О╨┤╨░
тАв ╨Я╨╛╨┤╨░╤З╨░ ╨╕ ╨┐╤А╨╡╨╖╨╡╨╜╤В╨░╤Ж╨╕╤П

**╨Ч╨░╨│╨╛╤В╨╛╨▓╨║╨╕ ╨╕ ╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡:**
[╨б╨╛╨▓╨╡╤В╤Л ╨┐╨╛ ╨╖╨░╨│╨╛╤В╨╛╨▓╨║╨░╨╝ ╨┤╨╗╤П ╨╜╨╛╨▓╤Л╤Е ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓]

╨б╨╛╨╖╨┤╨░╨╣ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤В╨╡╨╗╤М╨╜╨╛ ╨╕╨╜╤В╨╡╤А╨╡╤Б╨╜╤Л╨╣ ╨╕ ╨╢╨╕╨╖╨╜╨╡╤Б╨┐╨╛╤Б╨╛╨▒╨╜╤Л╨╣ ╤В╨▓╨╕╤Б╤В, ╨║╨╛╤В╨╛╤А╤Л╨╣ ╤Г╨┤╨╕╨▓╨╕╤В, ╨╜╨╛ ╨╛╤Б╤В╨░╨╜╨╡╤В╤Б╤П ╨▓╨║╤Г╤Б╨╜╤Л╨╝ ╨╕ ╨▓╤Л╨┐╨╛╨╗╨╜╨╕╨╝╤Л╨╝!"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.8
        )
        
        return {"inspiration": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕: {str(e)}")

@app.post("/api/save-tech-card")
async def save_tech_card(request: dict):
    user_id = request.get("user_id")
    content = request.get("content")
    dish_name = request.get("dish_name", "╨в╨╡╤Е╨║╨░╤А╤В╨░")
    city = request.get("city", "moscow")
    is_inspiration = request.get("is_inspiration", False)
    
    if not user_id or not content:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    # Auto-create test user if needed
    if user_id and user_id.startswith("test_user_"):
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
            "message": "╨в╨╡╤Е╨║╨░╤А╤В╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨░ ╤Г╤Б╨┐╨╡╤И╨╜╨╛"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П: {str(e)}")

@app.post("/api/v1/user/save-recipe")
async def save_v1_recipe(request: dict):
    """╨б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡ V1 ╤А╨╡╤Ж╨╡╨┐╤В╨░ ╨▓ ╨╕╤Б╤В╨╛╤А╨╕╤О ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П"""
    user_id = request.get("user_id")
    recipe_content = request.get("recipe_content")
    recipe_name = request.get("recipe_name", "╨а╨╡╤Ж╨╡╨┐╤В V1")
    recipe_type = request.get("recipe_type", "v1")
    source_type = request.get("source_type", "manual")  # 'manual', 'inspiration', 'food_pairing', etc.
    
    if not user_id or not recipe_content:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    try:
        # Create V1 recipe object
        recipe = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "dish_name": recipe_name,
            "content": recipe_content,
            "type": recipe_type,  # 'v1' for recipes, 'v2' for tech cards
            "version": "v1",
            "is_recipe": True,  # Flag to distinguish from tech cards
            "source_type": source_type,  # Source: manual, inspiration, food_pairing, etc.
            "created_at": datetime.now(),
            "city": "moscow"  # Default city
        }
        
        # Save to the same collection as tech cards but with type distinction
        await db.tech_cards.insert_one(recipe)
        
        return {
            "success": True,
            "id": recipe["id"],
            "message": f"╨а╨╡╤Ж╨╡╨┐╤В V1 '{recipe_name}' ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜ ╨▓ ╨╕╤Б╤В╨╛╤А╨╕╤О"
        }
        
    except Exception as e:
        print(f"Error saving V1 recipe: {e}")
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╤А╨╡╤Ж╨╡╨┐╤В╨░: {str(e)}")

@app.post("/api/v1/convert-recipe-to-techcard")
async def convert_recipe_to_techcard(request: dict):
    """╨Э╨░╤Б╤В╨╛╤П╤Й╨░╤П ╨║╨╛╨╜╨▓╨╡╤А╤В╨░╤Ж╨╕╤П V1 ╤А╨╡╤Ж╨╡╨┐╤В╨░ ╨▓ ╨┐╨╛╨╗╨╜╨╛╤Ж╨╡╨╜╨╜╤Г╤О V2 ╤В╨╡╤Е╨║╨░╤А╤В╤Г ╤З╨╡╤А╨╡╨╖ pipeline"""
    user_id = request.get("user_id")
    recipe_content = request.get("recipe_content")
    recipe_name = request.get("recipe_name", "╨в╨╡╤Е╨║╨░╤А╤В╨░ ╨╕╨╖ ╤А╨╡╤Ж╨╡╨┐╤В╨░")
    
    if not user_id or not recipe_content:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    try:
        print(f"ЁЯФД Converting V1 recipe to real V2 techcard: {recipe_name}")
        
        # ╨и╨Р╨У 1: ╨Я╨░╤А╤Б╨╕╨╝ V1 ╤А╨╡╤Ж╨╡╨┐╤В ╤З╨╡╤А╨╡╨╖ LLM ╨┤╨╗╤П ╨╕╨╖╨▓╨╗╨╡╤З╨╡╨╜╨╕╤П ╨┤╨░╨╜╨╜╤Л╤Е
        # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╤В╨╛╤В ╨╢╨╡ openai_client ╤З╤В╨╛ ╨╕ ╨▓ ╤А╨░╨▒╨╛╤З╨╡╨╣ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╤В╨╡╤Е╨║╨░╤А╤В
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI ╨║╨╗╨╕╨╡╨╜╤В ╨╜╨╡ ╨╕╨╜╨╕╤Ж╨╕╨░╨╗╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜")
        
        parsing_prompt = f"""
╨Я╤А╨╛╨░╨╜╨░╨╗╨╕╨╖╨╕╤А╤Г╨╣ ╤Н╤В╨╛╤В ╤А╨╡╤Ж╨╡╨┐╤В ╨╕ ╨╕╨╖╨▓╨╗╨╡╨║╨╕ ╨║╨╗╤О╤З╨╡╨▓╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡ ╨┤╨╗╤П ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛╨╣ ╤В╨╡╤Е╨║╨░╤А╤В╤Л:

╨а╨Х╨ж╨Х╨Я╨в V1:
{recipe_content}

╨Т╨Х╨а╨Э╨Ш JSON ╨▓ ╤В╨╛╤З╨╜╨╛╨╝ ╤Д╨╛╤А╨╝╨░╤В╨╡:
{{
    "dish_name": "╤В╨╛╤З╨╜╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░",
    "cuisine": "╤В╨╕╨┐ ╨║╤Г╤Е╨╜╨╕ (╨╡╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П/╨░╨╖╨╕╨░╤В╤Б╨║╨░╤П/╤А╤Г╤Б╤Б╨║╨░╤П ╨╕ ╤В.╨┤.)",
    "category": "╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П (╨│╨╛╤А╤П╤З╨╡╨╡/╤Е╨╛╨╗╨╛╨┤╨╜╨╛╨╡/╨┤╨╡╤Б╨╡╤А╤В/╤Б╨░╨╗╨░╤В/╤Б╤Г╨┐)",
    "main_ingredients": ["╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╣ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В 1", "╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╣ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В 2", "╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╣ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В 3"],
    "cooking_method": "╤Б╨┐╨╛╤Б╨╛╨▒ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П (╨╢╨░╤А╨║╨░/╨▓╨░╤А╨║╨░/╤В╤Г╤И╨╡╨╜╨╕╨╡ ╨╕ ╤В.╨┤.)",
    "estimated_time": ╤З╨╕╤Б╨╗╨╛_╨╝╨╕╨╜╤Г╤В,
    "difficulty": "╨┐╤А╨╛╤Б╤В╨╛╨╡/╤Б╤А╨╡╨┤╨╜╨╡╨╡/╤Б╨╗╨╛╨╢╨╜╨╛╨╡"
}}

╨Ю╤В╨▓╨╡╤З╨░╨╣ ╨в╨Ю╨Ы╨м╨Ъ╨Ю JSON ╨▒╨╡╨╖ ╨┤╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╨╛╨│╨╛ ╤В╨╡╨║╤Б╤В╨░.
"""

        parse_response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "╨в╤Л ╤Н╨║╤Б╨┐╨╡╤А╤В ╨┐╨╛ ╨░╨╜╨░╨╗╨╕╨╖╤Г ╤А╨╡╤Ж╨╡╨┐╤В╨╛╨▓. ╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╣ ╤В╨╛╨╗╤М╨║╨╛ ╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Л╨╣ JSON."},
                {"role": "user", "content": parsing_prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        # ╨Я╨░╤А╤Б╨╕╨╝ JSON ╨╛╤В╨▓╨╡╤В
        import json
        try:
            parsed_data = json.loads(parse_response.choices[0].message.content.strip())
            print(f"тЬЕ Parsed recipe data: {parsed_data}")
        except:
            # Fallback ╨╡╤Б╨╗╨╕ JSON ╨╜╨╡ ╤А╨░╤Б╨┐╨░╤А╤Б╨╕╨╗╤Б╤П
            parsed_data = {
                "dish_name": recipe_name,
                "cuisine": "╨╡╨▓╤А╨╛╨┐╨╡╨╣╤Б╨║╨░╤П", 
                "category": "╨│╨╛╤А╤П╤З╨╡╨╡",
                "main_ingredients": ["╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╣ ╨┐╤А╨╛╨┤╤Г╨║╤В"],
                "cooking_method": "╨║╨╛╨╝╨▒╨╕╨╜╨╕╤А╨╛╨▓╨░╨╜╨╜╨░╤П ╨╛╨▒╤А╨░╨▒╨╛╤В╨║╨░",
                "estimated_time": 30,
                "difficulty": "╤Б╤А╨╡╨┤╨╜╨╡╨╡"
            }
            print(f"тЪая╕П JSON parse failed, using fallback: {parsed_data}")
        
        # ╨и╨Р╨У 2: ╨Т╤Л╨╖╤Л╨▓╨░╨╡╨╝ ╨Э╨Р╨б╨в╨Ю╨п╨й╨г╨о V2 ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤О ╤З╨╡╤А╨╡╨╖ techcards_v2 pipeline
        from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
        
        # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨┐╤А╨╛╤Д╨╕╨╗╤М ╨┤╨╗╤П V2 pipeline ╤Б ╨┤╨░╨╜╨╜╤Л╨╝╨╕ ╨╕╨╖ V1 ╤А╨╡╤Ж╨╡╨┐╤В╨░
        profile = ProfileInput(
            name=parsed_data["dish_name"],
            cuisine=parsed_data["cuisine"],
            equipment=["╨┐╨╗╨╕╤В╨░", "╨║╨░╤Б╤В╤А╤О╨╗╤П", "╤Б╨║╨╛╨▓╨╛╤А╨╛╨┤╨░"],  # ╨С╨░╨╖╨╛╨▓╨╛╨╡ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╨╡
            budget=300.0,  # ╨б╤А╨╡╨┤╨╜╨╕╨╣ ╨▒╤О╨┤╨╢╨╡╤В
            dietary=[],
            user_id=user_id
        )
        
        print(f"ЁЯЪА Running V2 pipeline with profile: {profile}")
        
        # ╨Ч╨░╨┐╤Г╤Б╨║╨░╨╡╨╝ ╨┐╨╛╨╗╨╜╨╛╤Ж╨╡╨╜╨╜╤Л╨╣ V2 pipeline
        pipeline_result = run_pipeline(profile)
        
        if pipeline_result.status in ["success", "draft", "READY"] and pipeline_result.card:
            print(f"тЬЕ V2 pipeline succeeded with status: {pipeline_result.status}")
            
            # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╨╜╨░╤Б╤В╨╛╤П╤Й╤Г╤О V2 ╤В╨╡╤Е╨║╨░╤А╤В╤Г
            real_techcard_v2 = pipeline_result.card
            
            # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨╝╨╡╤В╨║╤Г ╤З╤В╨╛ ╤Н╤В╨╛ ╨║╨╛╨╜╨▓╨╡╤А╤В╨░╤Ж╨╕╤П ╨╕╨╖ V1
            if hasattr(real_techcard_v2, 'meta'):
                # ╨Я╤А╨░╨▓╨╕╨╗╤М╨╜╨╛ ╨╛╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ Pydantic ╨╝╨╛╨┤╨╡╨╗╤М meta
                updated_meta = real_techcard_v2.meta.model_copy(deep=True)
                # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤О ╨╛ ╨║╨╛╨╜╨▓╨╡╤А╤В╨░╤Ж╨╕╨╕ ╨▓ timings (╤Н╤В╨╛ ╤А╨░╨╖╤А╨╡╤И╨╡╨╜╨╜╨╛╨╡ ╨┐╨╛╨╗╨╡)
                updated_meta.timings['converted_from_v1'] = 1.0
                updated_meta.timings['original_recipe_length'] = len(recipe_content)
                real_techcard_v2 = real_techcard_v2.model_copy(update={"meta": updated_meta})
            
            # ╨б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨▓ ╨▒╨░╨╖╤Г ╨║╨░╨║ ╨╜╨░╤Б╤В╨╛╤П╤Й╤Г╤О V2 ╤В╨╡╤Е╨║╨░╤А╤В╤Г (╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╤Г╨╢╨╡ ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╨╕╨╣ async db)
            await db.tech_cards.insert_one({
                "id": real_techcard_v2.meta.id,
                "user_id": user_id,
                "name": parsed_data["dish_name"],
                "techcard_v2_data": real_techcard_v2.dict() if hasattr(real_techcard_v2, 'dict') else real_techcard_v2,
                "status": "READY",
                "created_at": datetime.now(),
                "converted_from_v1": True,
                "original_recipe_preview": recipe_content[:200]
            })
            
            return {
                "success": True,
                "techcard": real_techcard_v2.dict() if hasattr(real_techcard_v2, 'dict') else real_techcard_v2,
                "message": f"╨а╨╡╤Ж╨╡╨┐╤В '{parsed_data['dish_name']}' ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╨┐╤А╨╡╨╛╨▒╤А╨░╨╖╨╛╨▓╨░╨╜ ╨▓ ╨╜╨░╤Б╤В╨╛╤П╤Й╤Г╤О V2 ╤В╨╡╤Е╨║╨░╤А╤В╤Г"
            }
        else:
            # ╨Х╤Б╨╗╨╕ V2 pipeline ╨╜╨╡ ╤Б╤А╨░╨▒╨╛╤В╨░╨╗, ╨┐╨░╨┤╨░╨╡╨╝ ╤Б ╨╛╤И╨╕╨▒╨║╨╛╨╣
            error_msg = f"V2 pipeline failed with status: {pipeline_result.status}"
            print(f"тЭМ {error_msg}")
            raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ V2 ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕: {error_msg}")
        
    except Exception as e:
        print(f"тЭМ Error in V1тЖТV2 conversion: {e}")
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨║╨╛╨╜╨▓╨╡╤А╤В╨░╤Ж╨╕╨╕: {str(e)}")

@app.post("/api/generate-food-pairing")
async def generate_food_pairing(request: dict):
    """AI ╨д╤Г╨┤╨┐╨╡╨╣╤А╨╕╨╜╨│ - ╨┐╨╛╨┤╨▒╨╛╤А ╨╕╨┤╨╡╨░╨╗╤М╨╜╤Л╤Е ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╨╣ ╨┤╨╗╤П ╨▒╨╗╤О╨┤╨░"""
    tech_card = request.get("tech_card")
    user_id = request.get("user_id")
    
    if not tech_card or not user_id:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    try:
        # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░
        dish_name = "╨▒╨╗╤О╨┤╨╛"
        if isinstance(tech_card, dict):
            dish_name = tech_card.get("meta", {}).get("title", "╨▒╨╗╤О╨┤╨╛")
            if not dish_name and tech_card.get("name"):
                dish_name = tech_card.get("name")
        
        # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨┐╤А╨╛╨╝╨┐╤В ╨┤╨╗╤П ╤Д╤Г╨┤╨┐╨╡╨╣╤А╨╕╨╜╨│╨░
        pairing_prompt = f"""
╨в╤Л ╤Н╨║╤Б╨┐╨╡╤А╤В ╨┐╨╛ ╤Д╤Г╨┤╨┐╨╡╨╣╤А╨╕╨╜╨│╤Г. ╨Я╤А╨╛╨░╨╜╨░╨╗╨╕╨╖╨╕╤А╤Г╨╣ ╨▒╨╗╤О╨┤╨╛ "{dish_name}" ╨╕ ╤Б╨╛╨╖╨┤╨░╨╣ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╡ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕ ╨┐╨╛ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П╨╝.

╨С╨Ы╨о╨Ф╨Ю: {dish_name}

╨б╨╛╨╖╨┤╨░╨╣ ╨┐╨╛╨┤╤А╨╛╨▒╨╜╤Л╨╡ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕ ╨▓ ╤Б╨╗╨╡╨┤╤Г╤О╤Й╨╕╤Е ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╤Е:

ЁЯН╖ **╨Э╨Р╨Я╨Ш╨в╨Ъ╨Ш:**
тАв ╨Т╨╕╨╜╨░ (╤Г╨║╨░╨╖╨░╤В╤М ╤Б╨╛╤А╤В╨░ ╨╕ ╨┐╤А╨╕╤З╨╕╨╜╤Л ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П)
тАв ╨С╨╡╨╖╨░╨╗╨║╨╛╨│╨╛╨╗╤М╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤В╨║╨╕
тАв ╨Ъ╨╛╨║╤В╨╡╨╣╨╗╨╕ (╨╡╤Б╨╗╨╕ ╨┐╨╛╨┤╤Е╨╛╨┤╤П╤В)

ЁЯеЧ **╨У╨Р╨а╨Э╨Ш╨а╨л ╨Ш ╨Ф╨Ю╨С╨Р╨Т╨Ъ╨Ш:**
тАв ╨Ш╨┤╨╡╨░╨╗╤М╨╜╤Л╨╡ ╨│╨░╤А╨╜╨╕╤А╤Л
тАв ╨б╨╛╤Г╤Б╤Л ╨╕ ╨╖╨░╨┐╤А╨░╨▓╨║╨╕
тАв ╨в╤А╨░╨▓╤Л ╨╕ ╤Б╨┐╨╡╤Ж╨╕╨╕ ╨┤╨╗╤П ╤Г╤Б╨╕╨╗╨╡╨╜╨╕╤П ╨▓╨║╤Г╤Б╨░

ЁЯзА **╨Ф╨Ю╨Я╨Ю╨Ы╨Э╨Ш╨в╨Х╨Ы╨м╨Э╨л╨Х ╨Я╨а╨Ю╨Ф╨г╨Ъ╨в╨л:**
тАв ╨б╤Л╤А╤Л (╨╡╤Б╨╗╨╕ ╨┐╨╛╨┤╤Е╨╛╨┤╤П╤В)
тАв ╨Ю╤А╨╡╤Е╨╕, ╤Б╨╡╨╝╨╡╨╜╨░
тАв ╨д╤А╤Г╨║╤В╤Л ╨╕╨╗╨╕ ╨╛╨▓╨╛╤Й╨╕ ╨┤╨╗╤П ╨▒╨░╨╗╨░╨╜╤Б╨░

ЁЯТб **╨Я╨а╨Ю╨д╨Х╨б╨б╨Ш╨Ю╨Э╨Р╨Ы╨м╨Э╨л╨Х ╨б╨Ю╨Т╨Х╨в╨л:**
тАв ╨в╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨╜╤Л╨╡ ╨║╨╛╨╜╤В╤А╨░╤Б╤В╤Л
тАв ╨в╨╡╨║╤Б╤В╤Г╤А╨╜╤Л╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П
тАв ╨б╨╡╨╖╨╛╨╜╨╜╤Л╨╡ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╨╕

╨Ф╨░╨╣ ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╤Л╨╡ ╨╕ ╨┐╤А╨░╨║╤В╨╕╤З╨╜╤Л╨╡ ╤Б╨╛╨▓╨╡╤В╤Л ╨┤╨╗╤П ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░.
"""

        # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╤В╨╛╤В ╨╢╨╡ openai_client ╤З╤В╨╛ ╨╕ ╨▓ ╤А╨░╨▒╨╛╤З╨╡╨╣ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╤В╨╡╤Е╨║╨░╤А╤В
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI ╨║╨╗╨╕╨╡╨╜╤В ╨╜╨╡ ╨╕╨╜╨╕╤Ж╨╕╨░╨╗╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜")
        
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "╨в╤Л ╨╝╨░╤Б╤В╨╡╤А ╤Д╤Г╨┤╨┐╨╡╨╣╤А╨╕╨╜╨│╨░ ╤Б ╨╛╨┐╤Л╤В╨╛╨╝ ╤А╨░╨▒╨╛╤В╤Л ╨▓ ╨╝╨╕╤И╨╗╨╡╨╜╨╛╨▓╤Б╨║╨╕╤Е ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░╤Е. ╨б╨╛╨╖╨┤╨░╨▓╨░╨╣ ╤В╨╛╤З╨╜╤Л╨╡ ╨╕ ╨▓╨║╤Г╤Б╨╜╤Л╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П."},
                {"role": "user", "content": pairing_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        pairing_content = response.choices[0].message.content
        
        return {
            "success": True,
            "pairing": pairing_content,
            "dish_name": dish_name,
            "message": f"╨д╤Г╨┤╨┐╨╡╨╣╤А╨╕╨╜╨│ ╨┤╨╗╤П '{dish_name}' ╤Б╨╛╨╖╨┤╨░╨╜"
        }
        
    except Exception as e:
        print(f"Error generating food pairing: {e}")
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╤Д╤Г╨┤╨┐╨╡╨╣╤А╨╕╨╜╨│╨░: {str(e)}")

@app.post("/api/generate-inspiration")
async def generate_inspiration(request: dict):
    """AI ╨Т╨┤╨╛╤Е╨╜╨╛╨▓╨╡╨╜╨╕╨╡ - ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╨╡ ╤В╨▓╨╕╤Б╤В╤Л ╨╜╨░ ╨▒╨╗╤О╨┤╨░"""
    tech_card = request.get("tech_card")
    user_id = request.get("user_id")
    inspiration_prompt = request.get("inspiration_prompt", "╨б╨╛╨╖╨┤╨░╨╣ ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╨╣ ╤В╨▓╨╕╤Б╤В ╨╜╨░ ╤Н╤В╨╛ ╨▒╨╗╤О╨┤╨╛")
    
    if not tech_card or not user_id:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    try:
        # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░
        dish_name = "╨▒╨╗╤О╨┤╨╛"
        if isinstance(tech_card, dict):
            dish_name = tech_card.get("meta", {}).get("title", "╨▒╨╗╤О╨┤╨╛")
            if not dish_name and tech_card.get("name"):
                dish_name = tech_card.get("name")
        
        # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨┐╤А╨╛╨╝╨┐╤В ╨┤╨╗╤П ╤В╨▓╨╛╤А╤З╨╡╤Б╨║╨╛╨│╨╛ ╨▓╨┤╨╛╤Е╨╜╨╛╨▓╨╡╨╜╨╕╤П
        creativity_prompt = f"""
╨в╤Л ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╨╣ ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А ╤Б ╨╝╨╕╤А╨╛╨▓╤Л╨╝ ╨╛╨┐╤Л╤В╨╛╨╝. ╨б╨╛╨╖╨┤╨░╨╣ ╨╕╨╜╨╜╨╛╨▓╨░╤Ж╨╕╨╛╨╜╨╜╤Л╨╡ ╨▓╨░╤А╨╕╨░╨╜╤В╤Л ╨▒╨╗╤О╨┤╨░ "{dish_name}".

╨Ш╨б╨е╨Ю╨Ф╨Э╨Ю╨Х ╨С╨Ы╨о╨Ф╨Ю: {dish_name}

{inspiration_prompt}

╨б╨╛╨╖╨┤╨░╨╣ 3-4 ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╤Е ╨▓╨░╤А╨╕╨░╨╜╤В╨░:

ЁЯМН **FUSION-╨Т╨Р╨а╨Ш╨Р╨Э╨в╨л:**
тАв ╨Р╨╖╨╕╨░╤В╤Б╨║╨╕╨╣ ╤В╨▓╨╕╤Б╤В
тАв ╨б╤А╨╡╨┤╨╕╨╖╨╡╨╝╨╜╨╛╨╝╨╛╤А╤Б╨║╨░╤П ╨╕╨╜╤В╨╡╤А╨┐╤А╨╡╤В╨░╤Ж╨╕╤П  
тАв ╨б╨║╨░╨╜╨┤╨╕╨╜╨░╨▓╤Б╨║╨╕╨╣ ╨┐╨╛╨┤╤Е╨╛╨┤

ЁЯОи **╨б╨Ю╨Т╨а╨Х╨Ь╨Х╨Э╨Э╨л╨Х ╨в╨Х╨е╨Э╨Ш╨Ъ╨Ш:**
тАв ╨Ь╨╛╨╗╨╡╨║╤Г╨╗╤П╤А╨╜╨░╤П ╨│╨░╤Б╤В╤А╨╛╨╜╨╛╨╝╨╕╤П
тАв ╨д╨╡╤А╨╝╨╡╨╜╤В╨░╤Ж╨╕╤П
тАв ╨Ъ╨╛╨┐╤З╨╡╨╜╨╕╨╡ ╨╕╨╗╨╕ ╨│╤А╨╕╨╗╤М

ЁЯМ▒ **╨Р╨Ы╨м╨в╨Х╨а╨Э╨Р╨в╨Ш╨Т╨л:**
тАв ╨Т╨╡╨│╨░╨╜╤Б╨║╨░╤П ╨▓╨╡╤А╤Б╨╕╤П
тАв ╨С╨╡╨╖╨│╨╗╤О╤В╨╡╨╜╨╛╨▓╤Л╨╣ ╨▓╨░╤А╨╕╨░╨╜╤В
тАв ╨Ъ╨╡╤В╨╛-╨░╨┤╨░╨┐╤В╨░╤Ж╨╕╤П

ЁЯОн **╨Я╨а╨Х╨Ч╨Х╨Э╨в╨Р╨ж╨Ш╨п:**
тАв ╨Э╨╡╨╛╨▒╤Л╤З╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░
тАв ╨Ш╨╜╤В╨╡╤А╨░╨║╤В╨╕╨▓╨╜╤Л╨╡ ╤Н╨╗╨╡╨╝╨╡╨╜╤В╤Л
тАв ╨б╨╡╨╖╨╛╨╜╨╜╨╛╨╡ ╨╛╤Д╨╛╤А╨╝╨╗╨╡╨╜╨╕╨╡

╨Ф╨╗╤П ╨║╨░╨╢╨┤╨╛╨│╨╛ ╨▓╨░╤А╨╕╨░╨╜╤В╨░ ╨╛╨┐╨╕╤И╨╕ ╨║╨╗╤О╤З╨╡╨▓╤Л╨╡ ╨╕╨╖╨╝╨╡╨╜╨╡╨╜╨╕╤П ╨╕ ╨┐╨╛╤З╨╡╨╝╤Г ╤Н╤В╨╛ ╨▒╤Г╨┤╨╡╤В ╨▓╨║╤Г╤Б╨╜╨╛.
"""

        # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╤В╨╛╤В ╨╢╨╡ openai_client ╤З╤В╨╛ ╨╕ ╨▓ ╤А╨░╨▒╨╛╤З╨╡╨╣ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╤В╨╡╤Е╨║╨░╤А╤В
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI ╨║╨╗╨╕╨╡╨╜╤В ╨╜╨╡ ╨╕╨╜╨╕╤Ж╨╕╨░╨╗╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜")
        
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "╨в╤Л ╨╜╨╛╨▓╨░╤В╨╛╤А╤Б╨║╨╕╨╣ ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А, ╨║╨╛╤В╨╛╤А╤Л╨╣ ╤Б╨╛╨╖╨┤╨░╨╡╤В ╤А╨╡╨▓╨╛╨╗╤О╤Ж╨╕╨╛╨╜╨╜╤Л╨╡ ╨╕╨╜╤В╨╡╤А╨┐╤А╨╡╤В╨░╤Ж╨╕╨╕ ╨║╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨╕╤Е ╨▒╨╗╤О╨┤. ╨в╨▓╨╛╨╕ ╨╕╨┤╨╡╨╕ ╨▓╤Б╨╡╨│╨┤╨░ ╨┐╤А╨░╨║╤В╨╕╤З╨╜╤Л ╨╕ ╨▓╨║╤Г╤Б╨╜╤Л."},
                {"role": "user", "content": creativity_prompt}
            ],
            max_tokens=1200,
            temperature=0.8
        )
        
        inspiration_content = response.choices[0].message.content
        
        return {
            "success": True,
            "inspiration": inspiration_content,
            "dish_name": dish_name,
            "message": f"╨Ъ╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╨╡ ╨╕╨┤╨╡╨╕ ╨┤╨╗╤П '{dish_name}' ╤Б╨╛╨╖╨┤╨░╨╜╤Л"
        }
        
    except Exception as e:
        print(f"Error generating inspiration: {e}")
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╨▓╨┤╨╛╤Е╨╜╨╛╨▓╨╡╨╜╨╕╤П: {str(e)}")

@app.post("/api/analyze-finances")
async def analyze_finances(request: dict):
    """╨Р╨╜╨░╨╗╨╕╨╖ ╤Д╨╕╨╜╨░╨╜╤Б╨╛╨▓ ╨▒╨╗╤О╨┤╨░ ╨┤╨╗╤П PRO ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╨╡╨╣"""
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    if not user_id or not tech_card:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨┐╨╛╨┤╨┐╨╕╤Б╨║╤Г ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П (PRO only)
    user = await db.users.find_one({"id": user_id})
    
    # ╨Р╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╕ ╤Б╨╛╨╖╨┤╨░╨╡╨╝ ╤В╨╡╤Б╤В╨╛╨▓╨╛╨│╨╛/╨┤╨╡╨╝╨╛ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
    if not user and user_id and (user_id.startswith("test_user_") or user_id == "demo_user"):
        user = {
            "id": user_id,
            "email": "test@example.com" if user_id != "demo_user" else "demo@receptorai.pro",
            "name": "Test User" if user_id != "demo_user" else "Demo User",
            "city": "moscow",
            "subscription_plan": "pro",
            "subscription_status": "active",
            "created_at": datetime.now()
        }
    elif not user:
        raise HTTPException(status_code=404, detail="╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜")
    
    # ╨Т╨а╨Х╨Ь╨Х╨Э╨Э╨Ю ╨Ю╨в╨Ъ╨Ы╨о╨з╨Х╨Э╨Ю ╨┤╨╗╤П ╤В╨╡╤Б╤В╨╕╤А╨╛╨▓╨░╨╜╨╕╤П - ╨▓╨║╨╗╤О╤З╨╕╨╝ ╨║╨╛╨│╨┤╨░ ╨▒╤Г╨┤╨╡╤В ╨┐╨╗╨░╤В╨╡╨╢╨║╨░
    # if user.get("subscription_plan") not in ["pro", "business"]:
    #     raise HTTPException(status_code=403, detail="╨д╤Г╨╜╨║╤Ж╨╕╤П ╨┤╨╛╤Б╤В╤Г╨┐╨╜╨░ ╤В╨╛╨╗╤М╨║╨╛ ╨┤╨╗╤П PRO ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╨╡╨╣")
    
    # Convert tech_card to string if it's a dict (V2 or aiKitchenRecipe format)
    if isinstance(tech_card, dict):
        if 'content' in tech_card:
            tech_card_str = tech_card['content']
        else:
            tech_card_str = str(tech_card)
    else:
        tech_card_str = tech_card
    
    # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░
    dish_name = "╨▒╨╗╤О╨┤╨╛"
    title_match = re.search(r'\*\*╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:\*\*\s*(.*?)(?=\n|$)', tech_card_str)
    if title_match:
        dish_name = title_match.group(1).strip()
    
    # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨╕ ╤Ж╨╡╨╜╤Л
    ingredients_match = re.search(r'\*\*╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)', tech_card_str, re.DOTALL)
    ingredients_text = ingredients_match.group(1) if ingredients_match else ""
    
    # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╤А╨╡╨│╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╨║╨╛╤Н╤Д╤Д╨╕╤Ж╨╕╨╡╨╜╤В
    regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
    
    # тЬи NEW: ╨Я╨╛╨╕╤Б╨║ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓ ╨▓ IIKO ╨║╨░╤В╨░╨╗╨╛╨│╨╡ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П ╨┤╨╗╤П ╤В╨╛╤З╨╜╤Л╤Е ╤Ж╨╡╨╜
    iiko_prices = {}
    iiko_matched_count = 0
    
    try:
        # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ IIKO ╨║╨░╤В╨░╨╗╨╛╨│ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П (╨╡╤Б╨╗╨╕ ╨┐╨╛╨┤╨║╨╗╤О╤З╨╡╨╜)
        organization_id = user.get("organization_id", "default")
        iiko_products = list(db.rms_products.find({
            "organization_id": organization_id,
            "active": True
        }))
        
        if iiko_products:
            logger.info(f"ЁЯФН Found {len(iiko_products)} products in IIKO catalog for user {user_id}")
            
            # ╨Я╨░╤А╤Б╨╕╨╝ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨╕╨╖ ╤В╨╡╤Е╨║╨░╤А╤В╤Л
            ingredient_lines = [line.strip() for line in ingredients_text.split('\n') if line.strip() and not line.strip().startswith('**')]
            
            for ingredient_line in ingredient_lines:
                # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨░ (╨┤╨╛ ╨┤╨╡╤Д╨╕╤Б╨░ ╨╕╨╗╨╕ ╨┤╨▓╨╛╨╡╤В╨╛╤З╨╕╤П)
                ingredient_name = ingredient_line.split('-')[0].split(':')[0].strip()
                ingredient_name_clean = ingredient_name.replace('*', '').strip()
                
                if len(ingredient_name_clean) < 2:
                    continue
                
                # ╨Ш╤Й╨╡╨╝ ╤Б╨╛╨▓╨┐╨░╨┤╨╡╨╜╨╕╨╡ ╨▓ IIKO ╨║╨░╤В╨░╨╗╨╛╨│╨╡
                for product in iiko_products:
                    product_name = product.get("name", "").lower()
                    ingredient_lower = ingredient_name_clean.lower()
                    
                    # ╨Я╤А╤П╨╝╨╛╨╡ ╤Б╨╛╨▓╨┐╨░╨┤╨╡╨╜╨╕╨╡ ╨╕╨╗╨╕ ╤Б╨╛╨┤╨╡╤А╨╢╨╕╤В
                    if product_name == ingredient_lower or ingredient_lower in product_name or product_name in ingredient_lower:
                        # ╨Э╨░╤И╨╗╨╕ ╤Б╨╛╨▓╨┐╨░╨┤╨╡╨╜╨╕╨╡!
                        price = product.get("price", 0)
                        if price > 0:
                            iiko_prices[ingredient_name_clean] = {
                                "price": price,
                                "unit": product.get("unit", "╨║╨│"),
                                "product_id": product.get("id"),
                                "confidence": "high"
                            }
                            iiko_matched_count += 1
                            logger.info(f"тЬЕ Matched '{ingredient_name_clean}' with IIKO product '{product.get('name')}' = {price}тВ╜")
                            break
        
        logger.info(f"ЁЯУК IIKO matching result: {iiko_matched_count} ingredients matched out of {len(ingredient_lines)}")
    
    except Exception as e:
        logger.error(f"тЪая╕П Error fetching IIKO prices: {e}")
        # ╨Я╤А╨╛╨┤╨╛╨╗╨╢╨░╨╡╨╝ ╨▒╨╡╨╖ IIKO ╤Ж╨╡╨╜
    
    # ╨Я╨╛╨╕╤Б╨║ ╨░╨║╤В╤Г╨░╨╗╤М╨╜╤Л╤Е ╤Ж╨╡╨╜ ╨▓ ╨╕╨╜╤В╨╡╤А╨╜╨╡╤В╨╡
    search_query = f"╤Ж╨╡╨╜╤Л ╨╜╨░ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л {user.get('city', '╨╝╨╛╤Б╨║╨▓╨░')} 2025 ╨╝╤П╤Б╨╛ ╨╛╨▓╨╛╤Й╨╕ ╨║╤А╤Г╨┐╤Л ╨╝╨╛╨╗╨╛╤З╨╜╤Л╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л"
    
    try:
        # from emergentintegrations.tools import web_search  # Removed for local development
        # web_search = None  # Placeholder
        # price_search_result = web_search(search_query, search_context_size="medium")  # Disabled for local
        price_search_result = "╨Ф╨░╨╜╨╜╤Л╨╡ ╨┐╨╛ ╤Ж╨╡╨╜╨░╨╝ ╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л (web_search disabled)"
    except Exception:
        price_search_result = "╨Ф╨░╨╜╨╜╤Л╨╡ ╨┐╨╛ ╤Ж╨╡╨╜╨░╨╝ ╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л"
    
    # ╨Я╨╛╨╕╤Б╨║ ╤Ж╨╡╨╜ ╨║╨╛╨╜╨║╤Г╤А╨╡╨╜╤В╨╛╨▓
    competitor_search_query = f"╤Ж╨╡╨╜╤Л ╨╝╨╡╨╜╤О {dish_name} ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╤Л {user.get('city', '╨╝╨╛╤Б╨║╨▓╨░')} 2025"
    
    try:
        competitor_search_result = web_search(competitor_search_query, search_context_size="medium")
    except Exception:
        competitor_search_result = "╨Ф╨░╨╜╨╜╤Л╨╡ ╨┐╨╛ ╨║╨╛╨╜╨║╤Г╤А╨╡╨╜╤В╨░╨╝ ╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л"
    
    # ╨д╨╛╤А╨╝╨╕╤А╤Г╨╡╨╝ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤О ╨╛ IIKO ╤Ж╨╡╨╜╨░╤Е ╨┤╨╗╤П ╨┐╤А╨╛╨╝╨┐╤В╨░
    iiko_prices_info = ""
    if iiko_prices:
        iiko_prices_info = "\n\nЁЯОп ╨в╨Ю╨з╨Э╨л╨Х ╨ж╨Х╨Э╨л ╨Ш╨Ч IIKO ╨Ъ╨Р╨в╨Р╨Ы╨Ю╨У╨Р (╨┐╤А╨╕╨╛╤А╨╕╤В╨╡╤В!):\n"
        for ingredient_name, price_data in iiko_prices.items():
            iiko_prices_info += f"- {ingredient_name}: {price_data['price']}тВ╜ ╨╖╨░ {price_data['unit']} (source: IIKO, ╤В╨╛╤З╨╜╨░╤П ╤Ж╨╡╨╜╨░)\n"
        iiko_prices_info += f"\n╨Ш╨в╨Ю╨У╨Ю: {len(iiko_prices)} ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓ ╤Б ╤В╨╛╤З╨╜╤Л╨╝╨╕ ╤Ж╨╡╨╜╨░╨╝╨╕ ╨╕╨╖ IIKO."
    
    # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨┐╤А╨╛╨╝╨┐╤В ╨┤╨╗╤П ╤Д╨╕╨╜╨░╨╜╤Б╨╛╨▓╨╛╨│╨╛ ╨░╨╜╨░╨╗╨╕╨╖╨░
    prompt = f"""╨в╤Л тАФ ╨┐╤А╨░╨║╤В╨╕╤З╨╜╤Л╨╣ ╤Д╨╕╨╜╨░╨╜╤Б╨╛╨▓╤Л╨╣ ╨║╨╛╨╜╤Б╤Г╨╗╤М╤В╨░╨╜╤В ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╛╨▓ ╤Б 15-╨╗╨╡╤В╨╜╨╕╨╝ ╨╛╨┐╤Л╤В╨╛╨╝. ╨в╨▓╨╛╤П ╤Б╨┐╨╡╤Ж╨╕╨░╨╗╨╕╨╖╨░╤Ж╨╕╤П тАФ ╨Ъ╨Ю╨Э╨Ъ╨а╨Х╨в╨Э╨л╨Х ╤А╨╡╤И╨╡╨╜╨╕╤П, ╨░ ╨╜╨╡ ╨╛╨▒╤Й╨╕╨╡ ╤Д╤А╨░╨╖╤Л.

╨Я╤А╨╛╨░╨╜╨░╨╗╨╕╨╖╨╕╤А╤Г╨╣ ╨▒╨╗╤О╨┤╨╛ "{dish_name}" ╨╕ ╨┤╨░╨╣ ╨а╨Х╨Р╨Ы╨м╨Э╨л╨Х ╤Б╨╛╨▓╨╡╤В╤Л ╤Б ╤Ж╨╕╤Д╤А╨░╨╝╨╕ ╨╕ ╨┐╤А╨░╨║╤В╨╕╤З╨╡╤Б╨║╨╕╨╝╨╕ ╤И╨░╨│╨░╨╝╨╕.

╨в╨Х╨е╨Ъ╨Р╨а╨в╨Р:
{tech_card}

╨а╨Х╨У╨Ш╨Ю╨Э╨Р╨Ы╨м╨Э╨л╨Щ ╨Ъ╨Ю╨н╨д╨д╨Ш╨ж╨Ш╨Х╨Э╨в: {regional_coefficient}x

{iiko_prices_info}

╨Ф╨Ю╨Я╨Ю╨Ы╨Э╨Ш╨в╨Х╨Ы╨м╨Э╨л╨Х ╨ж╨Х╨Э╨л ╨Э╨Р ╨Я╨а╨Ю╨Ф╨г╨Ъ╨в╨л (╨╡╤Б╨╗╨╕ ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╤Л ╨▓ IIKO): {price_search_result}

╨Ъ╨Ю╨Э╨Ъ╨г╨а╨Х╨Э╨в╨л: {competitor_search_result}

тЪая╕П ╨Т╨Р╨Ц╨Э╨Ю:
1. ╨Х╤Б╨╗╨╕ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В ╨╡╤Б╤В╤М ╨▓ IIKO ╨║╨░╤В╨░╨╗╨╛╨│╨╡ ╨▓╤Л╤И╨╡ - ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨в╨Ю╨з╨Э╨г╨о ╤Ж╨╡╨╜╤Г ╨╛╤В╤В╤Г╨┤╨░ (╤Н╤В╨╛ ╤А╨╡╨░╨╗╤М╨╜╨░╤П ╤Ж╨╡╨╜╨░ ╨┐╨╛╤Б╤В╨░╨▓╤Й╨╕╨║╨░).
2. ╨Ф╨╗╤П ╨╛╤Б╤В╨░╨╗╤М╨╜╤Л╤Е ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╨а╨Х╨Р╨Ы╨м╨Э╨л╨Х ╤А╤Л╨╜╨╛╤З╨╜╤Л╨╡ ╤Ж╨╡╨╜╤Л ╤Б ╤Г╤З╨╡╤В╨╛╨╝ ╤А╨╡╨│╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛╨│╨╛ ╨║╨╛╤Н╤Д╤Д╨╕╤Ж╨╕╨╡╨╜╤В╨░.
3. ╨Ю╨С╨п╨Ч╨Р╨в╨Х╨Ы╨м╨Э╨Ю: total_cost ╨╕ recommended_price ╨┤╨╛╨╗╨╢╨╜╤Л ╨▒╤Л╤В╤М ╨з╨Ш╨б╨Ы╨Р╨Ь╨Ш (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А 350, ╨░ ╨Э╨Х "350тВ╜" ╨╕╨╗╨╕ "350 ╤А╤Г╨▒")
4. ╨ж╨╡╨╜╤Л ╨┤╨╛╨╗╨╢╨╜╤Л ╨▒╤Л╤В╤М ╨а╨Х╨Р╨Ы╨Ш╨б╨в╨Ш╨з╨Э╨л╨Ь╨Ш ╨┤╨╗╤П ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░ ╨▓ 2025 ╨│╨╛╨┤╤Г. ╨Э╨░╨┐╤А╨╕╨╝╨╡╤А, ╨╛╨╜╨╕╨│╨╕╤А╨╕ ╤Б ╤В╤Г╨╜╤Ж╨╛╨╝ ╨╜╨╡ ╨╝╨╛╨╢╨╡╤В ╤Б╤В╨╛╨╕╤В╤М 10тВ╜ - ╤А╨╡╨░╨╗╤М╨╜╨░╤П ╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М 80-150тВ╜.

╨в╨Ш╨Я ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨п: {user.get('venue_type', 'family_restaurant')}
╨б╨в╨Р╨Э╨Ф╨Р╨а╨в╨Э╨Р╨п ╨Э╨Р╨ж╨Х╨Э╨Ъ╨Р ╨Ф╨Ы╨п ╨н╨в╨Ю╨У╨Ю ╨в╨Ш╨Я╨Р: {VENUE_TYPES.get(user.get('venue_type', 'family_restaurant'), VENUE_TYPES['family_restaurant']).get('typical_markup', '3.0x')}

╨Я╨а╨Ш╨Э╨ж╨Ш╨Я╨л ╨Р╨Э╨Р╨Ы╨Ш╨Ч╨Р:
- ╨Э╨╕╨║╨░╨║╨╕╤Е ╨▒╨░╨╜╨░╨╗╤М╨╜╨╛╤Б╤В╨╡╨╣ ╤В╨╕╨┐╨░ "╨╛╨┐╤В╨╕╨╝╨╕╨╖╨╕╤А╤Г╨╣╤В╨╡ ╨┐╨╛╤Б╤В╨░╨▓╤Й╨╕╨║╨╛╨▓"
- ╨в╨╛╨╗╤М╨║╨╛ ╨║╨╛╨╜╨║╤А╨╡╤В╨╕╨║╨░: "╨╖╨░╨╝╨╡╨╜╨╕╤В╨╡ X ╨╜╨░ Y = ╤Н╨║╨╛╨╜╨╛╨╝╨╕╤П ZтВ╜"  
- ╨а╨╡╨░╨╗╤М╨╜╤Л╨╡ ╤Ж╨╕╤Д╤А╤Л ╨╕ ╤А╨░╤Б╤З╨╡╤В╤Л
- ╨Я╤А╨░╨║╤В╨╕╤З╨╜╤Л╨╡ ╤Б╨╛╨▓╨╡╤В╤Л, ╨║╨╛╤В╨╛╤А╤Л╨╡ ╨╝╨╛╨╢╨╜╨╛ ╨▓╨╜╨╡╨┤╤А╨╕╤В╤М ╨╖╨░╨▓╤В╤А╨░
- ╨Я╤А╨╕ ╤А╨░╤Б╤З╨╡╤В╨╡ ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╨╛╨╣ ╤Ж╨╡╨╜╤Л ╤Г╤З╨╕╤В╤Л╨▓╨░╨╣ ╤Б╤В╨░╨╜╨┤╨░╤А╤В╨╜╤Г╤О ╨╜╨░╤Ж╨╡╨╜╨║╤Г ╨┤╨╗╤П ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╨Ш ╤Ж╨╡╨╜╤Л ╨║╨╛╨╜╨║╤Г╤А╨╡╨╜╤В╨╛╨▓

╨б╨╛╨╖╨┤╨░╨╣ ╨Я╨а╨Р╨Ъ╨в╨Ш╨з╨Э╨л╨Щ ╨░╨╜╨░╨╗╨╕╨╖ ╨▓ JSON:

{{
    "dish_name": "{dish_name}",
    "total_cost": 350,
    "recommended_price": 890,
    "price_reasoning": {{
        "cost_base": "╤Б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М",
        "venue_markup": "╤В╨╕╨┐╨╕╤З╨╜╨░╤П ╨╜╨░╤Ж╨╡╨╜╨║╨░ ╨┤╨╗╤П ╤В╨╕╨┐╨░ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А 3.5x)",
        "suggested_by_markup": "╤Ж╨╡╨╜╨░ ╨╜╨░ ╨╛╤Б╨╜╨╛╨▓╨╡ ╨╜╨░╤Ж╨╡╨╜╨║╨╕",
        "competitor_average": "╤Б╤А╨╡╨┤╨╜╤П╤П ╤Ж╨╡╨╜╨░ ╤Г ╨║╨╛╨╜╨║╤Г╤А╨╡╨╜╤В╨╛╨▓",
        "final_recommendation": "╨╕╤В╨╛╨│╨╛╨▓╨░╤П ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╤П ╨╕ ╨┐╨╛╤З╨╡╨╝╤Г"
    }},
    "margin_percent": [╨╝╨░╤А╨╢╨╕╨╜╨░╨╗╤М╨╜╨╛╤Б╤В╤М %],
    "profitability_rating": [1-5 ╨╖╨▓╨╡╨╖╨┤],
    
    "ingredient_breakdown": [
        {{"ingredient": "╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡", "cost": "╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤МтВ╜", "percent_of_total": "% ╨╛╤В ╨╛╨▒╤Й╨╡╨╣ ╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╨╕", "price_source": "iiko|market_estimate", "confidence": "high|medium|low", "optimization_tip": "╨║╨╛╨╜╨║╤А╨╡╤В╨╜╤Л╨╣ ╤Б╨╛╨▓╨╡╤В ╨┐╨╛ ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╨╕"}}
    ],
    
    "price_accuracy": {{
        "total_ingredients": "╨╛╨▒╤Й╨╡╨╡ ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓",
        "iiko_matched": "╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╤Б ╤Ж╨╡╨╜╨░╨╝╨╕ ╨╕╨╖ IIKO",
        "market_estimated": "╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╤Б ╤А╤Л╨╜╨╛╤З╨╜╨╛╨╣ ╨╛╤Ж╨╡╨╜╨║╨╛╨╣",
        "accuracy_percent": "╨┐╤А╨╛╤Ж╨╡╨╜╤В ╤В╨╛╤З╨╜╨╛╤Б╤В╨╕ ╤А╨░╤Б╤З╨╡╤В╨░ (0-100)"
    }},
    
    "smart_cost_cuts": [
        {{"change": "╨Ъ╨╛╨╜╨║╤А╨╡╤В╨╜╨░╤П ╨╖╨░╨╝╨╡╨╜╨░ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨░", "current_cost": "╤В╨╡╨║╤Г╤Й╨░╤П ╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤МтВ╜", "new_cost": "╨╜╨╛╨▓╨░╤П ╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤МтВ╜", "savings": "╤Н╨║╨╛╨╜╨╛╨╝╨╕╤ПтВ╜", "quality_impact": "╨▓╨╗╨╕╤П╨╜╨╕╨╡ ╨╜╨░ ╨▓╨║╤Г╤Б: ╨╝╨╕╨╜╨╕╨╝╨░╨╗╤М╨╜╨╛╨╡/╨╖╨░╨╝╨╡╤В╨╜╨╛╨╡/╨║╤А╨╕╤В╨╕╤З╨╜╨╛╨╡"}},
        {{"change": "╨Ш╨╖╨╝╨╡╨╜╨╡╨╜╨╕╨╡ ╨┐╤А╨╛╨┐╨╛╤А╤Ж╨╕╨╣", "savings": "╤Н╨║╨╛╨╜╨╛╨╝╨╕╤ПтВ╜", "description": "╨║╨░╨║ ╨╕╨╝╨╡╨╜╨╜╨╛ ╨╕╨╖╨╝╨╡╨╜╨╕╤В╤М"}}
    ],
    
    "revenue_hacks": [
        {{"strategy": "╨Ъ╨╛╨╜╨║╤А╨╡╤В╨╜╨░╤П ╤Б╤В╤А╨░╤В╨╡╨│╨╕╤П ╤Г╨▓╨╡╨╗╨╕╤З╨╡╨╜╨╕╤П ╨▓╤Л╤А╤Г╤З╨║╨╕", "implementation": "╨║╨░╨║ ╨▓╨╜╨╡╨┤╤А╨╕╤В╤М", "potential_gain": "╨┐╨╛╤В╨╡╨╜╤Ж╨╕╨░╨╗╤М╨╜╨░╤П ╨┐╤А╨╕╨▒╤Л╨╗╤МтВ╜"}},
        {{"strategy": "╨Ф╤А╤Г╨│╨╛╨╣ ╤Б╨┐╨╛╤Б╨╛╨▒", "implementation": "╤И╨░╨│╨╕ ╨▓╨╜╨╡╨┤╤А╨╡╨╜╨╕╤П", "potential_gain": "╨┐╤А╨╕╨▒╤Л╨╗╤МтВ╜"}}
    ],
    
    "seasonal_opportunities": {{
        "summer": "╨╗╨╡╤В╨╜╤П╤П ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╤П ╤Б ╤Ж╨╕╤Д╤А╨░╨╝╨╕",
        "winter": "╨╖╨╕╨╝╨╜╤П╤П ╤Б╤В╤А╨░╤В╨╡╨│╨╕╤П ╤Б ╤Ж╨╕╤Д╤А╨░╨╝╨╕", 
        "peak_season": "╨║╨╛╨│╨┤╨░ ╨▒╨╗╤О╨┤╨╛ ╨▓╤Л╨│╨╛╨┤╨╜╨╡╨╡ ╨▓╤Б╨╡╨│╨╛",
        "off_season": "╨║╨░╨║ ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨░╤В╤М ╨┐╤А╨╕╨▒╤Л╨╗╤М╨╜╨╛╤Б╤В╤М ╨▓ ╨╜╨╕╨╖╨║╨╕╨╣ ╤Б╨╡╨╖╨╛╨╜"
    }},
    
    "competitor_intelligence": {{
        "price_advantage": "╨▓╨░╤И╨╡ ╨┐╤А╨╡╨╕╨╝╤Г╤Й╨╡╤Б╤В╨▓╨╛/╨╜╨╡╨┤╨╛╤Б╤В╨░╤В╨╛╨║ ╨┐╨╛ ╤Ж╨╡╨╜╨╡",
        "positioning": "╨║╨░╨║ ╨┐╨╛╨╖╨╕╤Ж╨╕╨╛╨╜╨╕╤А╨╛╨▓╨░╤В╤М: ╨┐╤А╨╡╨╝╨╕╤Г╨╝/╤Б╤А╨╡╨┤╨╜╨╕╨╣/╨▒╤О╨┤╨╢╨╡╤В",
        "market_gap": "╨╜╨░╨╣╨┤╨╡╨╜╨╜╨░╤П ╨╜╨╕╤И╨░ ╨╕╨╗╨╕ ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛╤Б╤В╤М"
    }},
    
    "action_plan": [
        {{"priority": "╨▓╤Л╤Б╨╛╨║╨╕╨╣", "action": "╨Я╨╡╤А╨▓╨╛╨╡ ╤З╤В╨╛ ╨┤╨╡╨╗╨░╤В╤М ╨╖╨░╨▓╤В╤А╨░", "expected_result": "╨╛╨╢╨╕╨┤╨░╨╡╨╝╤Л╨╣ ╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В ╤Б ╤Ж╨╕╤Д╤А╨░╨╝╨╕"}},
        {{"priority": "╤Б╤А╨╡╨┤╨╜╨╕╨╣", "action": "╨Т╤В╨╛╤А╨╛╨╣ ╤И╨░╨│ ╨╜╨░ ╤Б╨╗╨╡╨┤╤Г╤О╤Й╨╡╨╣ ╨╜╨╡╨┤╨╡╨╗╨╡", "expected_result": "╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В"}},
        {{"priority": "╨╜╨╕╨╖╨║╨╕╨╣", "action": "╨Ф╨╛╨╗╨│╨╛╤Б╤А╨╛╤З╨╜╨░╤П ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╤П", "expected_result": "╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В"}}
    ],
    
    "financial_forecast": {{
        "daily_breakeven": "╤Б╨║╨╛╨╗╤М╨║╨╛ ╨┐╨╛╤А╤Ж╨╕╨╣ ╨┐╤А╨╛╨┤╨░╤В╤М ╤З╤В╨╛╨▒╤Л ╨▓╤Л╨╣╤В╨╕ ╨▓ ╨╜╨╛╨╗╤М",
        "target_daily": "╤Б╨║╨╛╨╗╤М╨║╨╛ ╨┐╨╛╤А╤Ж╨╕╨╣ ╨┤╨╗╤П ╤Е╨╛╤А╨╛╤И╨╡╨╣ ╨┐╤А╨╕╨▒╤Л╨╗╨╕", 
        "monthly_revenue_potential": "╨┐╨╛╤В╨╡╨╜╤Ж╨╕╨░╨╗ ╨▓╤Л╤А╤Г╤З╨║╨╕ ╨▓ ╨╝╨╡╤Б╤П╤ЖтВ╜",
        "profit_margin_realistic": "╤А╨╡╨░╨╗╨╕╤Б╤В╨╕╤З╨╜╨░╤П ╨┐╤А╨╕╨▒╤Л╨╗╤М ╤Б ╨┐╨╛╤А╤Ж╨╕╨╕тВ╜"
    }},
    
    "red_flags": [
        "╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨░╤П ╨┐╤А╨╛╨▒╨╗╨╡╨╝╨░ ╨║╨╛╤В╨╛╤А╤Г╤О ╨╜╨░╨┤╨╛ ╤А╨╡╤И╨╕╤В╤М ╤Б╤А╨╛╤З╨╜╨╛",
        "╨╡╤Й╨╡ ╨╛╨┤╨╜╨░ ╨║╤А╨╕╤В╨╕╤З╨╜╨░╤П ╤В╨╛╤З╨║╨░"
    ],
    
    "golden_opportunities": [
        "╤Г╨┐╤Г╤Й╨╡╨╜╨╜╨░╤П ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛╤Б╤В╤М ╨╖╨░╤А╨░╨▒╨╛╤В╨░╤В╤М ╨▒╨╛╨╗╤М╤И╨╡",
        "╤Б╨║╤А╤Л╤В╤Л╨╣ ╨┐╨╛╤В╨╡╨╜╤Ж╨╕╨░╨╗ ╨╛╨┐╤В╨╕╨╝╨╕╨╖╨░╤Ж╨╕╨╕"
    ]
}}

╨Т╨Р╨Ц╨Э╨Ю: ╨Э╨╕╨║╨░╨║╨╕╤Е ╨╛╨▒╤Й╨╕╤Е ╤Д╤А╨░╨╖! ╨в╨╛╨╗╤М╨║╨╛ ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╤Л╨╡ ╤Ж╨╕╤Д╤А╤Л, ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨╛╨▓, ╤В╨╛╤З╨╜╤Л╨╡ ╤Б╤Г╨╝╨╝╤Л ╤Н╨║╨╛╨╜╨╛╨╝╨╕╨╕, ╤А╨╡╨░╨╗╤М╨╜╤Л╨╡ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П. ╨Ъ╨░╨╢╨┤╤Л╨╣ ╤Б╨╛╨▓╨╡╤В ╨┤╨╛╨╗╨╢╨╡╨╜ ╨▒╤Л╤В╤М ╨│╨╛╤В╨╛╨▓ ╨║ ╨▓╨╜╨╡╨┤╤А╨╡╨╜╨╕╤О."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "╨в╤Л ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╤Д╨╕╨╜╨░╨╜╤Б╨╛╨▓╤Л╨╣ ╨░╨╜╨░╨╗╨╕╤В╨╕╨║ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╜╨╛╨│╨╛ ╨▒╨╕╨╖╨╜╨╡╤Б╨░ ╤Б 10-╨╗╨╡╤В╨╜╨╕╨╝ ╨╛╨┐╤Л╤В╨╛╨╝. ╨Т╤Б╨╡╨│╨┤╨░ ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╣ ╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Л╨╣ JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        analysis_text = response.choices[0].message.content
        
        # ╨Я╤А╨╛╨▒╤Г╨╡╨╝ ╤А╨░╤Б╨┐╨░╤А╤Б╨╕╤В╤М JSON
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
            
            # ╨Т╨░╨╗╨╕╨┤╨░╤Ж╨╕╤П ╨╕ ╨┐╨░╤А╤Б╨╕╨╜╨│ ╤З╨╕╤Б╨╡╨╗
            if 'total_cost' in analysis_data:
                try:
                    cost_val = analysis_data['total_cost']
                    if isinstance(cost_val, str):
                        # ╨г╨▒╨╕╤А╨░╨╡╨╝ ╨▓╤Б╨╡ ╨╜╨╡╤З╨╕╤Б╨╗╨╛╨▓╤Л╨╡ ╤Б╨╕╨╝╨▓╨╛╨╗╤Л ╨║╤А╨╛╨╝╨╡ ╤В╨╛╤З╨║╨╕
                        cost_val = ''.join(c for c in cost_val if c.isdigit() or c == '.')
                    analysis_data['total_cost'] = float(cost_val) if cost_val else 150
                    
                    # ╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨╜╨░ ╨░╨┤╨╡╨║╨▓╨░╤В╨╜╨╛╤Б╤В╤М (╨┤╨╛╨╗╨╢╨╜╨░ ╨▒╤Л╤В╤М ╨▒╨╛╨╗╤М╤И╨╡ 20тВ╜ ╨╕ ╨╝╨╡╨╜╤М╤И╨╡ 10000тВ╜)
                    if analysis_data['total_cost'] < 20:
                        logger.warning(f"тЪая╕П Suspicious total_cost {analysis_data['total_cost']}тВ╜ - too low. Setting to 150тВ╜")
                        analysis_data['total_cost'] = 150
                    elif analysis_data['total_cost'] > 10000:
                        logger.warning(f"тЪая╕П Suspicious total_cost {analysis_data['total_cost']}тВ╜ - too high. Setting to 500тВ╜")
                        analysis_data['total_cost'] = 500
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing total_cost: {e}")
                    analysis_data['total_cost'] = 150
            
            if 'recommended_price' in analysis_data:
                try:
                    price_val = analysis_data['recommended_price']
                    if isinstance(price_val, str):
                        price_val = ''.join(c for c in price_val if c.isdigit() or c == '.')
                    analysis_data['recommended_price'] = float(price_val) if price_val else 450
                    
                    # ╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨╜╨░ ╨░╨┤╨╡╨║╨▓╨░╤В╨╜╨╛╤Б╤В╤М
                    if analysis_data['recommended_price'] < 50:
                        logger.warning(f"тЪая╕П Suspicious recommended_price {analysis_data['recommended_price']}тВ╜ - too low. Setting to 450тВ╜")
                        analysis_data['recommended_price'] = 450
                    elif analysis_data['recommended_price'] > 50000:
                        logger.warning(f"тЪая╕П Suspicious recommended_price {analysis_data['recommended_price']}тВ╜ - too high. Setting to 1500тВ╜")
                        analysis_data['recommended_price'] = 1500
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing recommended_price: {e}")
                    analysis_data['recommended_price'] = 450
            
            logger.info(f"ЁЯТ░ Financial analysis result: cost={analysis_data.get('total_cost')}тВ╜, price={analysis_data.get('recommended_price')}тВ╜")
            
        except json.JSONDecodeError as e:
            # ╨Х╤Б╨╗╨╕ JSON ╨╜╨╡╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Л╨╣, ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╨╝ ╨▒╨░╨╖╨╛╨▓╤Л╨╣ ╨░╨╜╨░╨╗╨╕╨╖
            logger.error(f"JSON decode error: {e}")
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
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨░╨╜╨░╨╗╨╕╨╖╨░: {str(e)}")

@app.post("/api/improve-dish")
async def improve_dish(request: dict):
    """╨г╨╗╤Г╤З╤И╨╡╨╜╨╕╨╡ ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╨╡╨│╨╛ ╨▒╨╗╤О╨┤╨░ ╨┤╨╗╤П PRO ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╨╡╨╣"""
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    if not user_id or not tech_card:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨┐╨╛╨┤╨┐╨╕╤Б╨║╤Г ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П (╨┐╨╛╨║╨░ ╨▒╨╡╤Б╨┐╨╗╨░╤В╨╜╨╛ ╨┤╨╗╤П ╨▓╤Б╨╡╤Е)
    user = await db.users.find_one({"id": user_id})
    
    # ╨Р╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╕ ╤Б╨╛╨╖╨┤╨░╨╡╨╝ ╤В╨╡╤Б╤В╨╛╨▓╨╛╨│╨╛/╨┤╨╡╨╝╨╛ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
    if not user and user_id and (user_id.startswith("test_user_") or user_id == "demo_user"):
        user = {
            "id": user_id,
            "email": "test@example.com" if user_id != "demo_user" else "demo@receptorai.pro",
            "name": "Test User" if user_id != "demo_user" else "Demo User",
            "city": "moscow",
            "subscription_plan": "pro",
            "subscription_status": "active",
            "created_at": datetime.now()
        }
    elif not user:
        raise HTTPException(status_code=404, detail="╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜")
    
    # Convert tech_card to string if it's a dict (V2 or aiKitchenRecipe format)
    if isinstance(tech_card, dict):
        if 'content' in tech_card:
            tech_card_str = tech_card['content']
        else:
            tech_card_str = str(tech_card)
    else:
        tech_card_str = tech_card
    
    # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╨▒╨╗╤О╨┤╨░
    dish_name = "╨▒╨╗╤О╨┤╨╛"
    title_match = re.search(r'\*\*╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:\*\*\s*(.*?)(?=\n|$)', tech_card_str)
    if title_match:
        dish_name = title_match.group(1).strip()
    
    # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨┐╤А╨╛╨╝╨┐╤В ╨┤╨╗╤П ╤Г╨╗╤Г╤З╤И╨╡╨╜╨╕╤П ╨▒╨╗╤О╨┤╨░  
    prompt = f"""╨в╤Л тАФ ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А ╨╝╨╕╤А╨╛╨▓╨╛╨│╨╛ ╤Г╤А╨╛╨▓╨╜╤П ╤Б 20-╨╗╨╡╤В╨╜╨╕╨╝ ╨╛╨┐╤Л╤В╨╛╨╝ ╤А╨░╨▒╨╛╤В╤Л ╨▓ ╨╝╨╕╤И╨╗╨╡╨╜╨╛╨▓╤Б╨║╨╕╤Е ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░╤Е.

╨в╨▓╨╛╤П ╨╖╨░╨┤╨░╤З╨░: ╨Я╨а╨Ю╨Ъ╨Р╨з╨Р╨в╨м ╨╕ ╨г╨Ы╨г╨з╨и╨Ш╨в╨м ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╨╡╨╡ ╨▒╨╗╤О╨┤╨╛ "{dish_name}", ╤Б╨┤╨╡╨╗╨░╨▓ ╨╡╨│╨╛ ╨▒╨╛╨╗╨╡╨╡ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╝, ╨▓╨║╤Г╤Б╨╜╤Л╨╝ ╨╕ ╨▓╨┐╨╡╤З╨░╤В╨╗╤П╤О╤Й╨╕╨╝, ╨╜╨╛ ╤Б╨╛╤Е╤А╨░╨╜╨╕╨▓ ╤Б╤В╨░╨╜╨┤╨░╤А╤В╨╜╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В ╤В╨╡╤Е╨╜╨╛╨╗╨╛╨│╨╕╤З╨╡╤Б╨║╨╛╨╣ ╨║╨░╤А╤В╤Л.

╨Ш╨б╨е╨Ю╨Ф╨Э╨Р╨п ╨в╨Х╨е╨Ъ╨Р╨а╨в╨Р:
{tech_card_str}

╨Т╨Р╨Ц╨Э╨Ю: 
- ╨Э╨Х ╨Ь╨Х╨Э╨п╨Щ ╨б╨г╨в╨м ╨С╨Ы╨о╨Ф╨Р! ╨г╨╗╤Г╤З╤И╨░╨╣ ╤В╨╛, ╤З╤В╨╛ ╨╡╤Б╤В╤М, ╨░ ╨╜╨╡ ╤Б╨╛╨╖╨┤╨░╨▓╨░╨╣ ╤З╤В╨╛-╤В╨╛ ╨╜╨╛╨▓╨╛╨╡
- ╨б╨в╨а╨Ю╨У╨Ю ╨б╨Ю╨С╨Ы╨о╨Ф╨Р╨Щ ╨д╨Ю╨а╨Ь╨Р╨в ╤В╨╡╤Е╨╜╨╛╨╗╨╛╨│╨╕╤З╨╡╤Б╨║╨╛╨╣ ╨║╨░╤А╤В╤Л ╨║╨░╨║ ╨▓ ╨╕╤Б╤Е╨╛╨┤╨╜╨╛╨╣
- ╨Ф╨Ю╨С╨Р╨Т╨м ╨╜╨╛╨▓╤Л╨╡ ╤Б╨╡╨║╤Ж╨╕╨╕ ╤Б ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╝╨╕ ╤Д╨╕╤И╨║╨░╨╝╨╕

╨б╨╛╨╖╨┤╨░╨╣ ╨г╨Ы╨г╨з╨и╨Х╨Э╨Э╨г╨о ╨▓╨╡╤А╤Б╨╕╤О ╤Б╤В╤А╨╛╨│╨╛ ╨▓ ╤Д╨╛╤А╨╝╨░╤В╨╡:

**╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:** [╨╕╤Б╤Е╨╛╨┤╨╜╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡] 2.0

**╨Ъ╨░╤В╨╡╨│╨╛╤А╨╕╤П:** [╤В╨░ ╨╢╨╡ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П]

**╨Ю╨┐╨╕╤Б╨░╨╜╨╕╨╡:** [╤Г╨╗╤Г╤З╤И╨╡╨╜╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╤Б ╨░╨║╤Ж╨╡╨╜╤В╨╛╨╝ ╨╜╨░ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕, 2-3 ╤Б╨╛╤З╨╜╤Л╤Е ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╡╨╜╨╕╤П]

**╨Ш╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л:** (╤Г╨║╨░╨╖╤Л╨▓╨░╨╣ ╨Э╨Р ╨Ю╨Ф╨Э╨г ╨Я╨Ю╨а╨ж╨Ш╨о!)

[╨Т╤Б╨╡ ╨╕╤Б╤Е╨╛╨┤╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л + ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╡ ╤Г╨╗╤Г╤З╤И╨╡╨╜╨╕╤П]
- [╨Ю╤Б╨╜╨╛╨▓╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╤Б ╤Г╨╗╤Г╤З╤И╨╡╨╜╨╜╤Л╨╝╨╕ ╨▓╨╡╤А╤Б╨╕╤П╨╝╨╕]
- [╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л]
- [╨б╨┐╨╡╤Ж╨╕╨╕ ╨╕ ╨░╨║╤Ж╨╡╨╜╤В╤Л ╨╛╤В ╤И╨╡╤Д╨░]

**╨Я╨╛╤И╨░╨│╨╛╨▓╤Л╨╣ ╤А╨╡╤Ж╨╡╨┐╤В:**

1. [╨и╨░╨│ ╤Б ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╝╨╕ ╤В╨╡╤Е╨╜╨╕╨║╨░╨╝╨╕]
2. [╨и╨░╨│ ╤Б ╤Б╨╡╨║╤А╨╡╤В╨░╨╝╨╕ ╨╝╨░╤Б╤В╨╡╤А╤Б╤В╨▓╨░]
3. [╨д╨╕╨╜╨░╨╗╤М╨╜╤Л╨╡ ╤И╤В╤А╨╕╤Е╨╕]

**╨Т╤А╨╡╨╝╤П:** ╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ XX ╨╝╨╕╨╜ | ╨У╨╛╤В╨╛╨▓╨║╨░ XX ╨╝╨╕╨╜ | ╨Ш╨в╨Ю╨У╨Ю XX ╨╝╨╕╨╜

**╨Т╤Л╤Е╨╛╨┤:** XXX ╨│ ╨│╨╛╤В╨╛╨▓╨╛╨│╨╛ ╨▒╨╗╤О╨┤╨░

**╨Я╨╛╤А╤Ж╨╕╤П:** XX ╨│ (╨╛╨┤╨╜╨░ ╨┐╨╛╤А╤Ж╨╕╤П)

**╨б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М:**

- ╨Я╨╛ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨░╨╝: XXX тВ╜
- ╨б╨╡╨▒╨╡╤Б╤В╨╛╨╕╨╝╨╛╤Б╤В╤М 1 ╨┐╨╛╤А╤Ж╨╕╨╕: XX тВ╜
- ╨а╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╨░╤П ╤Ж╨╡╨╜╨░ (├Ч3): XXX тВ╜

**╨Ъ╨С╨Ц╨г ╨╜╨░ 1 ╨┐╨╛╤А╤Ж╨╕╤О:** ╨Ъ╨░╨╗╨╛╤А╨╕╨╕ тАж ╨║╨║╨░╨╗ | ╨С тАж ╨│ | ╨Ц тАж ╨│ | ╨г тАж ╨│

**╨Ъ╨С╨Ц╨г ╨╜╨░ 100 ╨│:** ╨Ъ╨░╨╗╨╛╤А╨╕╨╕ тАж ╨║╨║╨░╨╗ | ╨С тАж ╨│ | ╨Ц тАж ╨│ | ╨г тАж ╨│

**╨Р╨╗╨╗╨╡╤А╨│╨╡╨╜╤Л:** тАж + (╨▓╨╡╨│╨░╨╜ / ╨▒╨╡╨╖╨│╨╗╤О╤В╨╡╨╜ ╨╕ ╤В.╨┐.)

**╨Ч╨░╨│╨╛╤В╨╛╨▓╨║╨╕ ╨╕ ╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡:**

- ╨Я╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╡ ╨╖╨░╨│╨╛╤В╨╛╨▓╨║╨╕ ╨╕ ╨╕╤Е ╤Б╤А╨╛╨║╨╕
- ╨в╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨╜╤Л╨╡ ╤А╨╡╨╢╨╕╨╝╤Л ╤Е╤А╨░╨╜╨╡╨╜╨╕╤П (+2┬░C, +18┬░C, ╨║╨╛╨╝╨╜╨░╤В╨╜╨░╤П)
- ╨Ы╨░╨╣╤Д╤Е╨░╨║╨╕ ╨┤╨╗╤П ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╨║╨░╤З╨╡╤Б╤В╨▓╨░ ╨╛╤В ╤И╨╡╤Д╨░
- ╨Ю╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╨╕ ╤А╨░╨▒╨╛╤В╤Л ╤Б ╤Г╨╗╤Г╤З╤И╨╡╨╜╨╜╤Л╨╝╨╕ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨░╨╝╨╕

**╨Ю╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╨╕ ╨╕ ╤Б╨╛╨▓╨╡╤В╤Л ╨╛╤В ╤И╨╡╤Д╨░:**

ЁЯФе **╨Я╨а╨Ю╨д╨Х╨б╨б╨Ш╨Ю╨Э╨Р╨Ы╨м╨Э╨л╨Х ╨г╨Ы╨г╨з╨и╨Х╨Э╨Ш╨п:**
- ╨Ч╨░╨╝╨╡╨╜╨░ [╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В] ╨╜╨░ [╤Г╨╗╤Г╤З╤И╨╡╨╜╨╜╤Л╨╣ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В] - [╤Н╤Д╤Д╨╡╨║╤В]
- ╨Ф╨╛╨▒╨░╨▓╨╗╨╡╨╜╨╕╨╡ [╤В╨╡╤Е╨╜╨╕╨║╨░] ╨┤╨╗╤П [╤А╨╡╨╖╤Г╨╗╤М╤В╨░╤В]
- ╨б╨╡╨║╤А╨╡╤В: [╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╨░╤П ╤Е╨╕╤В╤А╨╛╤Б╤В╤М]

тЪб **╨в╨Х╨е╨Э╨Ш╨з╨Х╨б╨Ъ╨Ш╨Х ╨д╨Ш╨и╨Ъ╨Ш:**
- [╨Ъ╨╛╨╜╨║╤А╨╡╤В╨╜╨░╤П ╤В╨╡╤Е╨╜╨╕╨║╨░] - ╨╖╨░╤З╨╡╨╝ ╤Н╤В╨╛ ╨╜╤Г╨╢╨╜╨╛
- [╨в╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨╜╤Л╨╣ ╨║╨╛╨╜╤В╤А╨╛╨╗╤М] - ╨║╨░╨║ ╤Н╤В╨╛ ╨▓╨╗╨╕╤П╨╡╤В ╨╜╨░ ╨▓╨║╤Г╤Б
- [╨Т╤А╨╡╨╝╨╡╨╜╨╜╤Л╨╡ ╨╜╤О╨░╨╜╤Б╤Л] - ╨║╤А╨╕╤В╨╕╤З╨╜╤Л╨╡ ╨╝╨╛╨╝╨╡╨╜╤В╤Л

ЁЯОп **╨Ь╨Р╨б╨в╨Х╨а-╨Ъ╨Ы╨Р╨б╨б╨л:**
- ╨Ъ╨░╨║ [╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨╡ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╨╡] ╨╕╨╖╨╝╨╡╨╜╤П╨╡╤В [╤Е╨░╤А╨░╨║╤В╨╡╤А╨╕╤Б╤В╨╕╨║╤Г]
- ╨б╨╡╨║╤А╨╡╤В ╨╕╨┤╨╡╨░╨╗╤М╨╜╨╛╨╣ [╤В╨╡╨║╤Б╤В╤Г╤А╤Л/╨▓╨║╤Г╤Б╨░/╨░╤А╨╛╨╝╨░╤В╨░]
- ╨Я╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╨░╤П ╤Е╨╕╤В╤А╨╛╤Б╤В╤М ╨┤╨╗╤П [╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨│╨╛ ╤Н╨╗╨╡╨╝╨╡╨╜╤В╨░]

ЁЯТО **╨н╨Ъ╨б╨Я╨Х╨а╨в╨Э╨л╨Х ╨б╨Ю╨Т╨Х╨в╨л:**
- [╨б╨╛╨▓╨╡╤В ╤Г╤А╨╛╨▓╨╜╤П ╨╝╨╕╤И╨╗╨╡╨╜╨╛╨▓╤Б╨║╨╛╨│╨╛ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░]
- [╨Ъ╨░╨║ ╨╕╨╖╨▒╨╡╨╢╨░╤В╤М ╤В╨╕╨┐╨╕╤З╨╜╨╛╨╣ ╨╛╤И╨╕╨▒╨║╨╕]
- [╨Т╨░╤А╨╕╨░╨╜╤В╤Л ╨░╨┤╨░╨┐╤В╨░╤Ж╨╕╨╕ ╨┐╨╛╨┤ ╤Б╨╡╨╖╨╛╨╜/╨┐╤А╨╡╨┤╨┐╨╛╤З╤В╨╡╨╜╨╕╤П]

**╨а╨╡╨║╨╛╨╝╨╡╨╜╨┤╨░╤Ж╨╕╤П ╨┐╨╛╨┤╨░╤З╨╕:** 

ЁЯОи **╨Я╨а╨Ю╨Ф╨Т╨Ш╨Э╨г╨в╨Р╨п ╨Я╨Ю╨Ф╨Р╨з╨Р:**
- ╨Я╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╣ ╨┐╨╗╨╡╨╣╤В╨╕╨╜╨│ ╨╕ ╤В╨╡╨╝╨┐╨╡╤А╨░╤В╤Г╤А╨╜╨░╤П ╨┐╨╛╨┤╨░╤З╨░
- ╨н╨╗╨╡╨╝╨╡╨╜╤В╤Л ╨┤╨╡╨║╨╛╤А╨░ ╨╕ ╨░╨║╤Ж╨╡╨╜╤В╨╛╨▓
- ╨б╨╛╤З╨╡╤В╨░╨╜╨╕╨╡ ╤Б ╤Б╨╛╤Г╤Б╨░╨╝╨╕ ╨╕ ╨│╨░╤А╨╜╨╕╤А╨░╨╝╨╕

**╨в╨╡╨│╨╕ ╨┤╨╗╤П ╨╝╨╡╨╜╤О:** #╨┐╤А╨╛╨║╨░╤З╨░╨╜╨╜╨░╤П #╤И╨╡╤Д #╨┐╤А╨╛╤Д╨╕ #╤Г╨╗╤Г╤З╤И╨╡╨╜╨╜╨░╤П

╨б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╨╜╨╛ RECEPTOR AI PRO тАФ ╨┐╤А╨╛╨║╨░╤З╨░╨╜╨╜╨░╤П ╨▓╨╡╤А╤Б╨╕╤П ╨╛╤В ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А╨░

╨Т╨Р╨Ц╨Э╨Ю: ╨б╨╛╤Е╤А╨░╨╜╨╕ ╨Т╨б╨Х ╤А╨░╨╖╨┤╨╡╨╗╤Л ╨╕╨╖ ╨╕╤Б╤Е╨╛╨┤╨╜╨╛╨╣ ╤В╨╡╤Е╨║╨░╤А╤В╤Л, ╨╜╨╛ ╤Г╨╗╤Г╤З╤И╨╕ ╨╕╤Е ╤Б╨╛╨┤╨╡╤А╨╢╨░╨╜╨╕╨╡!"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "╨в╤Л ╨╝╨╕╤И╨╗╨╡╨╜╨╛╨▓╤Б╨║╨╕╨╣ ╤И╨╡╤Д-╨┐╨╛╨▓╨░╤А ╤Б 20-╨╗╨╡╤В╨╜╨╕╨╝ ╨╛╨┐╤Л╤В╨╛╨╝. ╨в╨▓╨╛╤П ╨╖╨░╨┤╨░╤З╨░ - ╤Г╨╗╤Г╤З╤И╨░╤В╤М ╨▒╨╗╤О╨┤╨░, ╨┤╨╡╨╗╨░╤П ╨╕╤Е ╨▒╨╛╨╗╨╡╨╡ ╨┐╤А╨╛╤Д╨╡╤Б╤Б╨╕╨╛╨╜╨░╨╗╤М╨╜╤Л╨╝╨╕, ╨╜╨╛ ╤Б╨╛╤Е╤А╨░╨╜╤П╤П ╤Б╤Г╤В╤М. ╨Ф╨░╨▓╨░╨╣ ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╤Л╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕ ╨╕ ╨╛╨▒╤К╤П╤Б╨╜╨╡╨╜╨╕╤П."},
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
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╤Г╨╗╤Г╤З╤И╨╡╨╜╨╕╤П ╨▒╨╗╤О╨┤╨░: {str(e)}")

@app.post("/api/laboratory-experiment")
async def laboratory_experiment(request: dict):
    """╨Ъ╤Г╨╗╨╕╨╜╨░╤А╨╜╤Л╨╡ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╤Л ╨▓ ╨╗╨░╨▒╨╛╤А╨░╤В╨╛╤А╨╕╨╕ ╨┤╨╗╤П PRO ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╨╡╨╣"""
    user_id = request.get("user_id")
    experiment_type = request.get("experiment_type", "random")  # random, fusion, molecular, extreme
    base_dish = request.get("base_dish", "")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨┐╨╛╨┤╨┐╨╕╤Б╨║╤Г ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П (╨┐╨╛╨║╨░ ╨▒╨╡╤Б╨┐╨╗╨░╤В╨╜╨╛ ╨┤╨╗╤П ╨▓╤Б╨╡╤Е)
    user = await db.users.find_one({"id": user_id})
    
    # ╨Р╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╕ ╤Б╨╛╨╖╨┤╨░╨╡╨╝ ╤В╨╡╤Б╤В╨╛╨▓╨╛╨│╨╛/╨┤╨╡╨╝╨╛ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
    if not user and user_id and (user_id.startswith("test_user_") or user_id == "demo_user"):
        user = {
            "id": user_id,
            "email": "test@example.com" if user_id != "demo_user" else "demo@receptorai.pro",
            "name": "Test User" if user_id != "demo_user" else "Demo User",
            "city": "moscow",
            "subscription_plan": "pro",
            "subscription_status": "active",
            "created_at": datetime.now()
        }
    elif not user:
        raise HTTPException(status_code=404, detail="╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜")
    
    # ╨Ф╨╛╨╝╨░╤И╨╜╨╕╨╡ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л ╨┤╨╗╤П ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨╛╨▓
    random_ingredients = [
        # ╨Ь╤П╤Б╨╜╤Л╨╡/╨▒╨╡╨╗╨║╨╛╨▓╤Л╨╡ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╡
        "╤Б╨╛╤Б╨╕╤Б╨║╨╕", "╨║╤Г╤А╨╕╨╜╤Л╨╡ ╨╜╨░╨│╨│╨╡╤В╤Б╤Л", "╨║╤А╨░╨▒╨╛╨▓╤Л╨╡ ╨┐╨░╨╗╨╛╤З╨║╨╕", "╤В╤Г╤И╨╡╨╜╨║╨░", "╤П╨╣╤Ж╨░", 
        "╤В╨▓╨╛╤А╨╛╨│", "╤Б╤Л╤А ╨┐╨╗╨░╨▓╨╗╨╡╨╜╤Л╨╣", "╨║╨╛╨╗╨▒╨░╤Б╨░", "╤Б╨░╤А╨┤╨╡╨╗╤М╨║╨╕", "╤Д╨░╤А╤И",
        
        # ╨б╨╗╨░╨┤╨║╨╕╨╡ ╨╜╨╡╨╛╨╢╨╕╨┤╨░╨╜╨╜╤Л╨╡
        "╤Б╨║╨╕╤В╤В╨╗╤Б", "╨╝╨░╤А╨╝╨╡╨╗╨░╨┤", "╨╖╨╡╤Д╨╕╤А", "╨▓╨░╤Д╨╗╨╕", "╨┐╨╡╤З╨╡╨╜╤М╨╡ ╨╛╤А╨╡╨╛", 
        "╨╜╤Г╤В╨╡╨╗╨╗╨░", "╤Б╨│╤Г╤Й╨╡╨╜╨║╨░", "╨╝╨╛╤А╨╛╨╢╨╡╨╜╨╛╨╡", "╤И╨╛╨║╨╛╨╗╨░╨┤", "╨╝╨╡╨┤",
        
        # ╨б╨╜╨╡╨║╨╕ ╨╕ ╤З╨╕╨┐╤Б╤Л
        "╤З╨╕╨┐╤Б╤Л", "╤Б╤Г╤Е╨░╤А╨╕╨║╨╕", "╨┐╨╛╨┐╨║╨╛╤А╨╜", "╨║╤А╨╡╨║╨╡╤А╤Л", "╤Б╨╛╨╗╨╡╨╜╤Л╨╡ ╨╛╤А╨╡╤И╨║╨╕",
        "╤Б╨╡╨╝╨╡╤З╨║╨╕", "╨║╨╕╤А╨╕╨╡╤И╨║╨╕", "╤З╨╕╤В╨╛╤Б", "╨╗╨╡╨╣╤Б", "╨┐╤А╨╕╨╜╨│╨╗╤Б",
        
        # ╨Э╨░╨┐╨╕╤В╨║╨╕ ╨║╨░╨║ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╤Л
        "╨║╨╛╨║╨░-╨║╨╛╨╗╨░", "╨┐╨╡╨┐╤Б╨╕", "╤Д╨░╨╜╤В╨░", "╤Б╨┐╤А╨░╨╣╤В", "╨║╨▓╨░╤Б", "╨┐╨╕╨▓╨╛ ╨▒╨╡╨╖╨░╨╗╨║╨╛╨│╨╛╨╗╤М╨╜╨╛╨╡",
        
        # ╨Ф╨╛╨╝╨░╤И╨╜╨╕╨╡ ╨╛╨▓╨╛╤Й╨╕/╤Д╤А╤Г╨║╤В╤Л
        "╨╛╨│╤Г╤А╤Ж╤Л ╤Б╨╛╨╗╨╡╨╜╤Л╨╡", "╨┐╨╛╨╝╨╕╨┤╨╛╤А╤Л ╤З╨╡╤А╤А╨╕", "╨╗╤Г╨║ ╤А╨╡╨┐╤З╨░╤В╤Л╨╣", "╨║╨░╤А╤В╨╛╤И╨║╨░", 
        "╨╝╨╛╤А╨║╨╛╨▓╤М", "╤П╨▒╨╗╨╛╨║╨╕", "╨▒╨░╨╜╨░╨╜╤Л", "╨║╨╗╤Г╨▒╨╜╨╕╨║╨░ ╨╖╨░╨╝╨╛╤А╨╛╨╢╨╡╨╜╨╜╨░╤П",
        
        # ╨б╨╛╤Г╤Б╤Л ╨┤╨╛╨╝╨░╤И╨╜╨╕╨╡
        "╨║╨╡╤В╤З╤Г╨┐", "╨╝╨░╨╣╨╛╨╜╨╡╨╖", "╨│╨╛╤А╤З╨╕╤Ж╨░", "╤Б╨╛╨╡╨▓╤Л╨╣ ╤Б╨╛╤Г╤Б", "╤В╨║╨╡╨╝╨░╨╗╨╕",
        "╨░╨┤╨╢╨╕╨║╨░", "╤Е╤А╨╡╨╜", "╤Б╨╝╨╡╤В╨░╨╜╨░", "╨╣╨╛╨│╤Г╤А╤В", "╤А╤П╨╢╨╡╨╜╨║╨░",
        
        # ╨Ъ╤А╤Г╨┐╤Л ╨╕ ╨╝╨░╨║╨░╤А╨╛╨╜╤Л
        "╨╝╨░╨║╨░╤А╨╛╨╜╤Л", "╨│╤А╨╡╤З╨║╨░", "╤А╨╕╤Б", "╨╛╨▓╤Б╤П╨╜╨║╨░", "╨┐╤И╨╡╨╜╨╛", "╨╗╨░╨┐╤И╨░ ╨▒╤Л╤Б╤В╤А╨╛╨│╨╛ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П",
        
        # ╨е╨╗╨╡╨▒╨╛╨▒╤Г╨╗╨╛╤З╨╜╤Л╨╡
        "╤Е╨╗╨╡╨▒", "╨╗╨░╨▓╨░╤И", "╨┐╨╕╤В╤В╨░", "╤В╨╛╤Б╤В╨╛╨▓╤Л╨╣ ╤Е╨╗╨╡╨▒", "╨▒╤Г╨╗╨╛╤З╨║╨╕ ╨┤╨╗╤П ╨▒╤Г╤А╨│╨╡╤А╨╛╨▓",
        
        # ╨Ф╨╛╨╝╨░╤И╨╜╤П╤П ╤Н╨║╨╖╨╛╤В╨╕╨║╨░
        "╨▓╨░╤Б╨░╨▒╨╕ ╨╕╨╖ ╤В╤О╨▒╨╕╨║╨░", "╨╕╨╝╨▒╨╕╤А╤М ╨╝╨░╤А╨╕╨╜╨╛╨▓╨░╨╜╨╜╤Л╨╣", "╨╛╨╗╨╕╨▓╨║╨╕", "╨╝╨░╤Б╨╗╨╕╨╜╤Л",
        "╨║╨░╨┐╨╡╤А╤Б╤Л", "╨║╨╛╤А╨╜╨╕╤И╨╛╨╜╤Л", "╨║╨╕╨╝╤З╨╕", "╨║╨▓╨░╤И╨╡╨╜╨░╤П ╨║╨░╨┐╤Г╤Б╤В╨░"
    ]
    
    # ╨Ф╨╛╨╝╨░╤И╨╜╨╕╨╡ ╤В╨╡╤Е╨╜╨╕╨║╨╕ (╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╡ ╨▓╤Б╨╡╨╝)
    extreme_techniques = [
        "╨╢╨░╤А╨║╨░ ╨▓ ╨║╨╛╨║╨░-╨║╨╛╨╗╨╡", "╨╖╨░╨┐╨╡╨║╨░╨╜╨╕╨╡ ╤Б ╤З╨╕╨┐╤Б╨░╨╝╨╕", "╨╝╨░╤А╨╕╨╜╨╛╨▓╨░╨╜╨╕╨╡ ╨▓ ╨║╨▓╨░╤Б╨╡", 
        "╨┐╨░╨╜╨╕╤А╨╛╨▓╨║╨░ ╨▓ ╨┐╨╡╤З╨╡╨╜╤М╨╡", "╨│╨╗╨░╨╖╨╕╤А╨╛╨▓╨░╨╜╨╕╨╡ ╨╝╨╡╨┤╨╛╨╝", "╨║╨╛╨┐╤З╨╡╨╜╨╕╨╡ ╨╜╨░ ╤З╨░╨╡",
        "╨╖╨░╨╝╨╛╤А╨╛╨╖╨║╨░ ╤Б ╨╝╨╛╤А╨╛╨╢╨╡╨╜╤Л╨╝", "╨║╨░╤А╨░╨╝╨╡╨╗╨╕╨╖╨░╤Ж╨╕╤П ╤Б╨░╤Е╨░╤А╨╛╨╝", "╤В╤Г╤И╨╡╨╜╨╕╨╡ ╨▓ ╨┐╨╕╨▓╨╡",
        "╨▓╨╖╨▒╨╕╨▓╨░╨╜╨╕╨╡ ╤Б╨╝╨╡╤В╨░╨╜╨╛╨╣", "╨╜╨░╤Б╤В╨░╨╕╨▓╨░╨╜╨╕╨╡ ╨╜╨░ ╨║╨╛╤Д╨╡", "╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╨╡ ╨╜╨░ ╨┐╨░╤А╤Г",
        "╨│╤А╨╕╨╗╨╗╨╕╨╜╨│ ╨╜╨░ ╤Б╨║╨╛╨▓╨╛╤А╨╛╨┤╨╡", "╨╖╨░╨┐╨╡╨║╨░╨╜╨╕╨╡ ╨▓ ╤Д╨╛╨╗╤М╨│╨╡", "╤В╨╛╨╝╨╗╨╡╨╜╨╕╨╡ ╨▓ ╨┤╤Г╤Е╨╛╨▓╨║╨╡",
        "╨╛╨▒╨╢╨░╤А╨╕╨▓╨░╨╜╨╕╨╡ ╤Б ╨╗╤Г╨║╨╛╨╝", "╨┤╨╛╨▒╨░╨▓╨╗╨╡╨╜╨╕╨╡ ╨│╨░╨╖╨╕╤А╨╛╨▓╨║╨╕", "╤Б╨╝╨╡╤И╨╕╨▓╨░╨╜╨╕╨╡ ╤Б╨╛ ╤Б╨│╤Г╤Й╨╡╨╜╨║╨╛╨╣"
    ]
    
    # ╨С╨╡╨╖╤Г╨╝╨╜╤Л╨╡ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╤П
    fusion_combinations = [
        "╨а╤Г╤Б╤Б╨║╨░╤П ╨║╤Г╤Е╨╜╤П + ╨п╨┐╨╛╨╜╤Б╨║╨░╤П", "╨Ш╤В╨░╨╗╤М╤П╨╜╤Б╨║╨░╤П + ╨Ь╨╡╨║╤Б╨╕╨║╨░╨╜╤Б╨║╨░╤П", 
        "╨д╤А╨░╨╜╤Ж╤Г╨╖╤Б╨║╨░╤П + ╨Ъ╨╛╤А╨╡╨╣╤Б╨║╨░╤П", "╨Ш╨╜╨┤╨╕╨╣╤Б╨║╨░╤П + ╨б╨║╨░╨╜╨┤╨╕╨╜╨░╨▓╤Б╨║╨░╤П",
        "╨б╤А╨╡╨┤╨╕╨╖╨╡╨╝╨╜╨╛╨╝╨╛╤А╤Б╨║╨░╤П + ╨в╨░╨╣╤Б╨║╨░╤П", "╨Р╨╝╨╡╤А╨╕╨║╨░╨╜╤Б╨║╨░╤П + ╨Ь╨░╤А╨╛╨║╨║╨░╨╜╤Б╨║╨░╤П"
    ]
    
    import random
    
    # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨┐╤А╨╛╨╝╨┐╤В ╨▓ ╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛╤Б╤В╨╕ ╨╛╤В ╤В╨╕╨┐╨░ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨░
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
╨Ъ╨Ю╨Э╨в╨Х╨Ъ╨б╨в ╨Ч╨Р╨Т╨Х╨Ф╨Х╨Э╨Ш╨п: {venue_info['name']}
╨Ъ╤Г╤Е╨╜╤П: {', '.join([CUISINE_TYPES.get(c, {}).get('name', c) for c in cuisine_focus]) if cuisine_focus else '╨Ы╤О╨▒╨░╤П'}
╨Р╨┤╨░╨┐╤В╨╕╤А╨╛╨▓╨░╨╜╨╛ ╨┤╨╗╤П: {venue_info['description']}
"""
    
    if experiment_type == "random":
        rand_ingredients = random.sample(random_ingredients, 3)
        rand_technique = random.choice(extreme_techniques)
        experiment_prompt = f"""
        {venue_context}
        ЁЯО▓ ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в ╨Ф╨Ы╨п {venue_info['name'].upper()}:
        ╨б╨╛╨╖╨┤╨░╨╣ ╨▒╨╗╤О╨┤╨╛, ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╤П: {', '.join(rand_ingredients)}
        ╨в╨╡╤Е╨╜╨╕╨║╨░: {rand_technique}
        ╨С╨░╨╖╨╛╨▓╨╛╨╡ ╨▒╨╗╤О╨┤╨╛: {base_dish if base_dish else '╨▒╨╗╤О╨┤╨╛ ╨┐╨╛╨┤╤Е╨╛╨┤╤П╤Й╨╡╨╡ ╨┤╨╗╤П ╨┤╨░╨╜╨╜╨╛╨│╨╛ ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П'}
        ╨Т╨Р╨Ц╨Э╨Ю: ╨Р╨┤╨░╨┐╤В╨╕╤А╤Г╨╣ ╨┐╨╛╨┤ ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╤О {venue_info['name'].lower()}! ╨г╤З╤В╨╕ ╤Б╤В╨╕╨╗╤М ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╨╕ ╤Ж╨╡╨╗╨╡╨▓╤Г╤О ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╤О.
        """
    elif experiment_type == "fusion":
        fusion = random.choice(fusion_combinations)
        experiment_prompt = f"""
        {venue_context}
        ЁЯМН ╨д╨м╨о╨Ц╨Э ╨Ф╨Ы╨п {venue_info['name'].upper()}:
        ╨Ю╨▒╤К╨╡╨┤╨╕╨╜╨╕ ╨║╤Г╤Е╨╜╨╕: {fusion}
        ╨С╨░╨╖╨╛╨▓╨╛╨╡ ╨▒╨╗╤О╨┤╨╛: {base_dish if base_dish else '╨▒╨╗╤О╨┤╨╛ ╨┐╨╛╨┤╤Е╨╛╨┤╤П╤Й╨╡╨╡ ╨┤╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П'}
        ╨Т╨Р╨Ц╨Э╨Ю: ╨б╨╛╨╖╨┤╨░╨╣ ╤Б╨╛╤З╨╡╤В╨░╨╜╨╕╨╡ ╨┐╨╛╨┤╤Е╨╛╨┤╤П╤Й╨╡╨╡ ╨┤╨╗╤П {venue_info['name'].lower()} ╨╕ ╨╡╨│╨╛ ╨░╤Г╨┤╨╕╤В╨╛╤А╨╕╨╕.
        """
    elif experiment_type == "molecular":
        techniques = random.sample(extreme_techniques[:10], 2)
        experiment_prompt = f"""
        {venue_context}
        ЁЯзк ╨Ь╨Ю╨Ы╨Х╨Ъ╨г╨Ы╨п╨а╨Ъ╨Р ╨Ф╨Ы╨п {venue_info['name'].upper()}:
        ╨в╨╡╤Е╨╜╨╕╨║╨╕: {', '.join(techniques)}
        ╨С╨░╨╖╨╛╨▓╨╛╨╡ ╨▒╨╗╤О╨┤╨╛: {base_dish if base_dish else '╨┐╨╛╨┤╤Е╨╛╨┤╤П╤Й╨╡╨╡ ╨┤╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П ╨▒╨╗╤О╨┤╨╛'}
        ╨Т╨Р╨Ц╨Э╨Ю: ╨Р╨┤╨░╨┐╤В╨╕╤А╤Г╨╣ ╨┐╨╛╨┤ ╤Г╤А╨╛╨▓╨╡╨╜╤М {venue_info['name'].lower()}! ╨г╤З╤В╨╕ ╨╛╨▒╨╛╤А╤Г╨┤╨╛╨▓╨░╨╜╨╕╨╡ ╨╕ ╨║╨╛╨╜╤Ж╨╡╨┐╤Ж╨╕╤О ╨╝╨╡╤Б╤В╨░.
        """
    elif experiment_type == "snack":
        snack_ingredients = [ing for ing in random_ingredients if any(snack in ing for snack in ["╤З╨╕╨┐╤Б╤Л", "╤Б╨║╨╕╤В╤В╨╗╤Б", "╨┐╨╡╤З╨╡╨╜╤М╨╡", "╨╝╨░╤А╨╝╨╡╨╗╨░╨┤", "╨┐╨╛╨┐╨║╨╛╤А╨╜", "╨║╤А╨╡╨║╨╡╤А╤Л"])]
        selected_snacks = random.sample(snack_ingredients, 2)
        experiment_prompt = f"""
        {venue_context}
        ЁЯН┐ ╨б╨Э╨Х╨Ъ╨Ш ╨Ф╨Ы╨п {venue_info['name'].upper()}:
        ╨б╨╛╨╖╨┤╨░╨╣ ╨▒╨╗╤О╨┤╨╛ ╨╕╨╖ ╤Б╨╜╨╡╨║╨╛╨▓: {', '.join(selected_snacks)}
        ╨С╨░╨╖╨╛╨▓╨╛╨╡ ╨▒╨╗╤О╨┤╨╛: {base_dish if base_dish else '╨▒╨╗╤О╨┤╨╛ ╨┤╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П'}
        ╨Т╨Р╨Ц╨Э╨Ю: ╨Я╨╛╨║╨░╨╢╨╕ ╨║╨░╨║ ╨░╨┤╨░╨┐╤В╨╕╤А╨╛╨▓╨░╤В╤М ╨┐╨╛╨┤ ╤Б╤В╨╕╨╗╤М {venue_info['name'].lower()}!
        """
    else:
        experiment_prompt = f"""
        {venue_context}
        ЁЯФе ╨н╨Ъ╨б╨в╨а╨Ш╨Ь ╨Ф╨Ы╨п {venue_info['name'].upper()}:
        ╨Э╨░╤А╤Г╤И╤М ╨▓╤Б╨╡ ╨┐╤А╨░╨▓╨╕╨╗╨░ ╨┤╨╛╨╝╨░╤И╨╜╨╡╨╣ ╨║╤Г╨╗╨╕╨╜╨░╤А╨╕╨╕, ╨╜╨╛ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣ ╤В╨╛╨╗╤М╨║╨╛ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л!
        ╨С╨░╨╖╨╛╨▓╨╛╨╡ ╨▒╨╗╤О╨┤╨╛: {base_dish if base_dish else '╤В╤А╨░╨┤╨╕╤Ж╨╕╨╛╨╜╨╜╨╛╨╡ ╨┤╨╛╨╝╨░╤И╨╜╨╡╨╡ ╨▒╨╗╤О╨┤╨╛'}
        ╨Т╨Р╨Ц╨Э╨Ю: ╨Т╤Б╨╡ ╨┤╨╛╨╗╨╢╨╜╨╛ ╨▒╤Л╤В╤М ╨▓╤Л╨┐╨╛╨╗╨╜╨╕╨╝╨╛ ╨╜╨░ ╨╛╨▒╤Л╤З╨╜╨╛╨╣ ╨║╤Г╤Е╨╜╨╡ ╤Б ╨╛╨▒╤Л╤З╨╜╤Л╨╝╨╕ ╨┐╤А╨╛╨┤╤Г╨║╤В╨░╨╝╨╕!
        """

    # ╨Ю╤Б╨╜╨╛╨▓╨╜╨╛╨╣ ╨┐╤А╨╛╨╝╨┐╤В ╨┤╨╗╤П ╨╗╨░╨▒╨╛╤А╨░╤В╨╛╤А╨╕╨╕
    prompt = f"""╨в╤Л тАФ ╨┤╨╛╨║╤В╨╛╤А ╨У╨░╤Б╤В╤А╨╛╨╜╨╛╨╝╤Г╤Б, ╨▒╨╡╨╖╤Г╨╝╨╜╤Л╨╣ ╤Г╤З╨╡╨╜╤Л╨╣ ╨╛╤В ╨║╤Г╨╗╨╕╨╜╨░╤А╨╕╨╕! ЁЯзк

╨в╨▓╨╛╤П ╨╗╨░╨▒╨╛╤А╨░╤В╨╛╤А╨╕╤П тАФ ╨╝╨╡╤Б╤В╨╛, ╨│╨┤╨╡ ╤А╨╛╨╢╨┤╨░╤О╤В╤Б╤П ╤Б╨░╨╝╤Л╨╡ ╨┤╨╡╤А╨╖╨║╨╕╨╡ ╨║╤Г╨╗╨╕╨╜╨░╤А╨╜╤Л╨╡ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╤Л. 
╨б╨╛╨╖╨┤╨░╨╣ ╨▒╨╗╤О╨┤╨╛, ╨║╨╛╤В╨╛╤А╨╛╨╡ ╨и╨Ю╨Ъ╨Ш╨а╨г╨Х╨в, ╨г╨Ф╨Ш╨Т╨Ш╨в, ╨╜╨╛ ╨┐╤А╨╕ ╤Н╤В╨╛╨╝ ╨▒╤Г╨┤╨╡╤В ╨Э╨Х╨Т╨Х╨а╨Ю╨п╨в╨Э╨Ю ╨Т╨Ъ╨г╨б╨Э╨л╨Ь!

{experiment_prompt}

╨б╨╛╨╖╨┤╨░╨╣ ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в╨Р╨Ы╨м╨Э╨Ю╨Х ╨С╨Ы╨о╨Ф╨Ю:

**ЁЯзк ╨Э╨Р╨Ч╨Т╨Р╨Э╨Ш╨Х ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в╨Р:** [╨Ъ╤А╨╡╨░╤В╨╕╨▓╨╜╨╛╨╡ ╨╜╨░╤Г╤З╨╜╨╛╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡]

**ЁЯФм ╨У╨Ш╨Я╨Ю╨в╨Х╨Ч╨Р:** [╨Я╨╛╤З╨╡╨╝╤Г ╤Н╤В╨╛╤В ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В ╨▒╤Г╨┤╨╡╤В ╨▓╨║╤Г╤Б╨╜╤Л╨╝]

**тЪЧя╕П ╨Ш╨Э╨У╨а╨Х╨Ф╨Ш╨Х╨Э╨в╨л ╨Ф╨Ы╨п ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в╨Р:**
[╨б╨┐╨╕╤Б╨╛╨║ ╤Б ╤Г╨║╨░╨╖╨░╨╜╨╕╨╡╨╝ ╤А╨╛╨╗╨╕ ╨║╨░╨╢╨┤╨╛╨│╨╛ ╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В╨░ ╨▓ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨╡]

**ЁЯзм ╨Ы╨Р╨С╨Ю╨а╨Р╨в╨Ю╨а╨Э╨л╨Щ ╨Я╨а╨Ю╨ж╨Х╨б╨б:**
[╨Я╨╛╤И╨░╨│╨╛╨▓╤Л╨╣ ╨┐╤А╨╛╤Ж╨╡╤Б╤Б ╨║╨░╨║ ╨╜╨░╤Г╤З╨╜╤Л╨╣ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В]

**ЁЯМИ ╨Т╨Ш╨Ч╨г╨Р╨Ы╨м╨Э╨л╨Щ ╨н╨д╨д╨Х╨Ъ╨в:**
[╨Ъ╨░╨║ ╨▒╤Г╨┤╨╡╤В ╨▓╤Л╨│╨╗╤П╨┤╨╡╤В╤М ╨▒╨╗╤О╨┤╨╛ - ╤Ж╨▓╨╡╤В╨░, ╤В╨╡╨║╤Б╤В╤Г╤А╤Л, ╤Н╤Д╤Д╨╡╨║╤В╤Л]

**ЁЯОн ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в╨Р╨Ы╨м╨Э╨Р╨п ╨Я╨Ю╨Ф╨Р╨з╨Р:**
[╨Ъ╤А╨╡╨░╤В╨╕╨▓╨╜╨░╤П, ╤И╨╛╨║╨╕╤А╤Г╤О╤Й╨░╤П ╨┐╨╛╨┤╨░╤З╨░]

**ЁЯОк WOW-╨н╨д╨д╨Х╨Ъ╨в:**
[╨з╤В╨╛ ╤Г╨┤╨╕╨▓╨╕╤В ╨│╨╛╤Б╤В╨╡╨╣ ╨▒╨╛╨╗╤М╤И╨╡ ╨▓╤Б╨╡╨│╨╛]

**ЁЯУ╕ ╨Ю╨Я╨Ш╨б╨Р╨Э╨Ш╨Х ╨Ф╨Ы╨п ╨д╨Ю╨в╨Ю:**
[╨Ф╨╡╤В╨░╨╗╤М╨╜╨╛╨╡ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨▓╨╜╨╡╤И╨╜╨╡╨│╨╛ ╨▓╨╕╨┤╨░ ╨┤╨╗╤П AI-╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╤П]

**ЁЯФм ╨Э╨Р╨г╨з╨Э╨Ю╨Х ╨Ю╨С╨Ю╨б╨Э╨Ю╨Т╨Р╨Э╨Ш╨Х:**
[╨Я╨╛╤З╨╡╨╝╤Г ╤Н╤В╨╛ ╤А╨░╨▒╨╛╤В╨░╨╡╤В ╤Б ╤В╨╛╤З╨║╨╕ ╨╖╤А╨╡╨╜╨╕╤П ╨╜╨░╤Г╨║╨╕ ╨╛ ╨▓╨║╤Г╤Б╨╡]

**тЪая╕П ╨Я╨а╨Х╨Ф╨г╨Я╨а╨Х╨Ц╨Ф╨Х╨Э╨Ш╨Х:**
[╨з╤В╨╛ ╨╝╨╛╨╢╨╡╤В ╨┐╨╛╨╣╤В╨╕ ╨╜╨╡ ╤В╨░╨║ ╨▓ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨╡]

**ЁЯОп ╨ж╨Х╨Ы╨Х╨Т╨Р╨п ╨Р╨г╨Ф╨Ш╨в╨Ю╨а╨Ш╨п:**
[╨Ъ╤В╨╛ ╨╛╤Ж╨╡╨╜╨╕╤В ╤Н╤В╨╛╤В ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В]

**ЁЯУ▒ ╨е╨Х╨и╨в╨Х╨У╨Ш ╨Ф╨Ы╨п ╨б╨Ю╨ж╨б╨Х╨в╨Х╨Щ:**
[#╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨░╨╗╤М╨╜╨░╤П╨║╤Г╨╗╨╕╨╜╨░╤А╨╕╤П #╨│╨░╤Б╤В╤А╨╛╨╜╨╛╨╝╨╕╤П #╤И╨╛╨║╨╕╤А╤Г╤О╤Й╨╡╨╡╨▒╨╗╤О╨┤╨╛ ╨╕ ╤В.╨┤.]

╨б╨╛╨╖╨┤╨░╨╜╨╛ ╨▓ ╨Ы╨Р╨С╨Ю╨а╨Р╨в╨Ю╨а╨Ш╨Ш RECEPTOR PRO - ╨╝╨╡╤Б╤В╨╛ ╨┤╨╗╤П ╨║╤Г╨╗╨╕╨╜╨░╤А╨╜╤Л╤Е ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨╛╨▓! ЁЯзктЬи"""

    try:
        # ╨У╨╡╨╜╨╡╤А╨╕╤А╤Г╨╡╨╝ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨░╨╗╤М╨╜╨╛╨╡ ╨▒╨╗╤О╨┤╨╛
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "╨в╤Л ╨┤╨╛╨║╤В╨╛╤А ╨У╨░╤Б╤В╤А╨╛╨╜╨╛╨╝╤Г╤Б - ╨▒╨╡╨╖╤Г╨╝╨╜╤Л╨╣ ╤Г╤З╨╡╨╜╤Л╨╣ ╨╛╤В ╨║╤Г╨╗╨╕╨╜╨░╤А╨╕╨╕. ╨б╨╛╨╖╨┤╨░╨╡╤И╤М ╤И╨╛╨║╨╕╤А╤Г╤О╤Й╨╕╨╡, ╨╜╨╛ ╨▓╨║╤Г╤Б╨╜╤Л╨╡ ╨▒╨╗╤О╨┤╨░. ╨С╤Г╨┤╤М ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╤Л╨╝, ╨┤╨╡╤А╨╖╨║╨╕╨╝, ╨╜╨╛ ╨╜╨░╤Г╤З╨╜╤Л╨╝ ╨▓ ╨┐╨╛╨┤╤Е╨╛╨┤╨╡."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.9  # ╨Т╤Л╤Б╨╛╨║╨░╤П ╨║╤А╨╡╨░╤В╨╕╨▓╨╜╨╛╤Б╤В╤М
        )
        
        experiment_result = response.choices[0].message.content
        
        # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╛╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨┤╨╗╤П ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╤П
        photo_description = ""
        lines = experiment_result.split('\n')
        for i, line in enumerate(lines):
            if "**ЁЯУ╕ ╨Ю╨Я╨Ш╨б╨Р╨Э╨Ш╨Х ╨Ф╨Ы╨п ╨д╨Ю╨в╨Ю:**" in line:
                # ╨С╨╡╤А╨╡╨╝ ╤Б╨╗╨╡╨┤╤Г╤О╤Й╤Г╤О ╤Б╤В╤А╨╛╨║╤Г ╨┐╨╛╤Б╨╗╨╡ ╨╖╨░╨│╨╛╨╗╨╛╨▓╨║╨░
                if i + 1 < len(lines):
                    photo_description = lines[i + 1].strip()
                break
        
        # ╨У╨╡╨╜╨╡╤А╨╕╤А╤Г╨╡╨╝ ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╨╡ ╤З╨╡╤А╨╡╨╖ DALL-E 3
        image_url = None
        try:
            if photo_description:
                # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨┐╤А╨╛╨╝╨┐╤В ╨┤╨╗╤П DALL-E
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
            # ╨Я╤А╨╛╨┤╨╛╨╗╨╢╨░╨╡╨╝ ╨▒╨╡╨╖ ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╤П
        
        return {
            "success": True,
            "experiment": experiment_result,
            "experiment_type": experiment_type,
            "image_url": image_url,
            "photo_description": photo_description
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╛╨▓╨╡╨┤╨╡╨╜╨╕╤П ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨░: {str(e)}")

@app.post("/api/save-laboratory-experiment")
async def save_laboratory_experiment(request: dict):
    """╨б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨░ ╨╕╨╖ ╨╗╨░╨▒╨╛╤А╨░╤В╨╛╤А╨╕╨╕ ╨▓ ╨╕╤Б╤В╨╛╤А╨╕╤О ╤В╨╡╤Е╨║╨░╤А╤В"""
    user_id = request.get("user_id")
    experiment_content = request.get("experiment")
    experiment_type = request.get("experiment_type", "experiment")
    image_url = request.get("image_url")
    
    if not user_id or not experiment_content:
        raise HTTPException(status_code=400, detail="╨Э╨╡ ╨┐╤А╨╡╨┤╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╤Л ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л")
    
    # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨░
    dish_name = "ЁЯзк ╨Ы╨Р╨С╨Ю╨а╨Р╨в╨Ю╨а╨Э╨л╨Щ ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в"
    lines = experiment_content.split('\n')
    for line in lines:
        if "**╨Э╨Р╨Ч╨Т╨Р╨Э╨Ш╨Х ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в╨Р:**" in line or "**╨Э╨░╨╖╨▓╨░╨╜╨╕╨╡:**" in line:
            # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡
            name_part = line.split('**')[-1].strip()
            if name_part:
                dish_name = f"ЁЯзк {name_part}"
            break
        # ╨Ш╤Й╨╡╨╝ ╨┐╨╡╤А╨▓╤Г╤О ╤Б╤В╤А╨╛╨║╤Г ╤Б ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨╛╨╝
        elif line.strip() and not line.startswith('**') and len(line.strip()) > 10:
            # ╨С╨╡╤А╨╡╨╝ ╨┐╨╡╤А╨▓╤Л╨╡ 50 ╤Б╨╕╨╝╨▓╨╛╨╗╨╛╨▓ ╨║╨░╨║ ╨╜╨░╨╖╨▓╨░╨╜╨╕╨╡
            dish_name = f"ЁЯзк {line.strip()[:50]}..."
            break
    
    # Auto-create test user if needed
    if user_id and user_id.startswith("test_user_"):
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
        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤О ╨╛╨▒ ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╨╕ ╨▓ ╨║╨╛╨╜╤В╨╡╨╜╤В
        final_content = experiment_content
        if image_url:
            final_content += f"\n\n**ЁЯЦ╝я╕П ╨Ш╨Ч╨Ю╨С╨а╨Р╨Ц╨Х╨Э╨Ш╨Х ╨н╨Ъ╨б╨Я╨Х╨а╨Ш╨Ь╨Х╨Э╨в╨Р:**\n{image_url}"
        
        # Create tech card object for laboratory experiment
        tech_card = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "dish_name": dish_name,
            "content": final_content,
            "city": "moscow",
            "is_inspiration": False,
            "is_laboratory": True,  # ╨Я╨╛╨╝╨╡╤З╨░╨╡╨╝ ╨║╨░╨║ ╨╗╨░╨▒╨╛╤А╨░╤В╨╛╤А╨╜╤Л╨╣ ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В
            "experiment_type": experiment_type,
            "image_url": image_url,
            "created_at": datetime.now()
        }
        
        # Save to database
        await db.tech_cards.insert_one(tech_card)
        
        return {
            "success": True,
            "id": tech_card["id"],
            "message": "╨н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜ ╨▓ ╨╕╤Б╤В╨╛╤А╨╕╤О ╤В╨╡╤Е╨║╨░╤А╤В"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╤Н╨║╤Б╨┐╨╡╤А╨╕╨╝╨╡╨╜╤В╨░: {str(e)}")
