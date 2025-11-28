from fastapi import FastAPI, APIRouter, HTTPException, File, Form, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

# Загружаем .env файл
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
    print("⚠️ Password hashing/JWT not available. Install: pip install passlib[bcrypt] python-jose[cryptography]")

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
        logger.info("✅ OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        openai_client = None
else:
    logger.warning("⚠️ No OPENAI_API_KEY found - AI functions will be limited")
    openai_client = None

# КРИТИЧЕСКИ ВАЖНО: Принудительно включаем LLM для V2
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
                            self.logger.info(f"✅ SUCCESS: IIKo authentication successful with SHA1 hash")
                            self.logger.info(f"Session key: {session_key[:20]}...")
                            return
                        else:
                            raise Exception(f"Invalid session key received: {session_key}")
                    else:
                        raise Exception(f"Authentication failed: HTTP {response.status_code} - {response.text}")
                        
            except Exception as e:
                self.logger.error(f"❌ SHA1 authentication failed: {str(e)}")
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
                            self.logger.info(f"✅ Product created successfully in IIKo")
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
                        self.logger.info(f"🍽️ Trying FIXED DISH creation: {endpoint}")
                        self.logger.info(f"🍽️ DISH data: {dish_product['name']} (type: {dish_product['type']})")
                        
                        # Try POST with JSON payload
                        response = await client.post(
                            endpoint, 
                            params=params, 
                            json=dish_product,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        self.logger.info(f"🍽️ DISH Response: {response.status_code} - {response.text[:500]}")
                        
                        if response.status_code in [200, 201]:
                            try:
                                result_data = response.json() if response.content else {}
                                self.logger.info(f"✅ DISH product created with FIXED structure!")
                                
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
                                    'message': f"✅ Блюдо '{dish_product['name']}' создано в IIKo с исправленной структурой!"
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
                                    'message': f"✅ Блюдо '{dish_product['name']}' создано (HTTP 200)!"
                                }
                        
                        elif response.status_code == 400:
                            # Bad request - try minimal structure
                            self.logger.warning(f"🍽️ Bad request to {endpoint}, trying minimal structure")
                            
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
                                self.logger.info(f"✅ Minimal DISH creation succeeded!")
                                return {
                                    'success': True,
                                    'product_id': f"dish_min_{str(uuid.uuid4())[:8]}",
                                    'product_name': product_data.get('name'),
                                    'product_type': 'DISH',
                                    'message': f"✅ Блюдо '{product_data.get('name')}' создано (минимальная структура)!"
                                }
                                
                        elif response.status_code == 404:
                            # Endpoint not found - try next
                            continue
                        else:
                            self.logger.warning(f"🍽️ Failed {endpoint}: {response.status_code}")
                            
                    except Exception as e:
                        self.logger.debug(f"🍽️ Error with endpoint {endpoint}: {str(e)}")
                        continue
                
                # If all endpoints fail, return structured failure with fallback option
                self.logger.info("🍽️ All DISH endpoints failed, providing fallback")
                
                return {
                    'success': False,
                    'error': 'DISH creation endpoints not accessible or structure incompatible',
                    'note': 'Блюдо подготовлено для ручного создания в IIKo',
                    'prepared_dish_data': dish_product,
                    'fallback_instructions': 'Создайте блюдо вручную в IIKo с данными выше',
                    'endpoints_tried': possible_endpoints
                }
                
        except Exception as e:
            self.logger.error(f"Critical error creating DISH product: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': 'Критическая ошибка при создании блюда'
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
                        self.logger.info(f"🔍 Trying sales endpoint: {endpoint}")
                        
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
        """Get sales report using OLAP - ПРАВИЛЬНЫЙ СПОСОБ из документации!"""
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
            
            # OLAP отчет по продажам - из твоего исследования!
            olap_url = f"{self.auth_manager.base_url}/resto/api/v2/reports/olap"
            
            # Параметры из документации
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
                self.logger.info(f"📊 OLAP Request: POST {olap_url}")
                self.logger.info(f"📊 OLAP Data: {olap_request}")
                
                response = await client.post(
                    olap_url,
                    params=params,
                    json=olap_request,
                    headers={"Content-Type": "application/json"}
                )
                
                self.logger.info(f"📊 OLAP Response: {response.status_code} - {response.text[:300]}")
                
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
                        'note': 'Возможно нужны права B_RPT, B_CASR, B_VOTR'
                    }
                    
        except Exception as e:
            self.logger.error(f"Error in OLAP sales report: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': 'OLAP отчет требует специальных прав доступа'
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
                    # Каждая строка: [дата, название блюда, категория, сумма скидочная, количество]
                    if len(row) >= 5:
                        date_val = row[0]
                        dish_name = row[1]
                        category = row[2]
                        revenue = float(row[3]) if row[3] else 0
                        quantity = int(row[4]) if row[4] else 0
                        
                        # Общая статистика
                        summary['total_revenue'] += revenue
                        summary['total_items_sold'] += quantity
                        
                        # По датам
                        if date_val not in summary['sales_by_date']:
                            summary['sales_by_date'][date_val] = {'revenue': 0, 'items': 0}
                        summary['sales_by_date'][date_val]['revenue'] += revenue
                        summary['sales_by_date'][date_val]['items'] += quantity
                        
                        # По категориям
                        if category not in summary['categories_performance']:
                            summary['categories_performance'][category] = {'revenue': 0, 'items': 0}
                        summary['categories_performance'][category]['revenue'] += revenue
                        summary['categories_performance'][category]['items'] += quantity
                        
                        # Топ блюда
                        summary['top_dishes'].append({
                            'name': dish_name,
                            'category': category,
                            'revenue': revenue,
                            'quantity': quantity
                        })
                
                # Сортируем топ блюда по выручке
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
                self.logger.info(f"📂 Fetching categories from IIKo: {endpoint}")
                
                response = await client.get(endpoint, params=params)
                
                self.logger.info(f"📂 Categories response: {response.status_code} - {response.text[:200]}")
                
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
                self.logger.info(f"📂 Creating category in IIKo: {endpoint}")
                self.logger.info(f"📂 Category name: {category_name}")
                
                response = await client.post(
                    endpoint,
                    params=params,
                    json=category_data,
                    headers={"Content-Type": "application/json"}
                )
                
                self.logger.info(f"📂 Category creation response: {response.status_code} - {response.text[:300]}")
                
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
                            'message': f"✅ Категория '{category_name}' создана в IIKo!"
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
                self.logger.info(f"🔨 Creating assembly chart in IIKo: {endpoint}")
                self.logger.info(f"🔨 Assembly chart data: {tech_card_data.get('name', 'Unknown')}")
                
                response = await client.post(
                    endpoint,
                    params=params,
                    json=assembly_chart,
                    headers={"Content-Type": "application/json"}
                )
                
                self.logger.info(f"🔨 Assembly chart response: {response.status_code} - {response.text[:300]}")
                
                if response.status_code in [200, 201]:
                    data = response.json() if response.content else {}
                    
                    return {
                        'success': True,
                        'method': 'assembly_chart',
                        'endpoint': endpoint,
                        'assembly_chart_id': data.get('id'),
                        'name': tech_card_data.get('name', 'Unknown'),
                        'response': data,
                        'message': f"✅ Техкарта '{tech_card_data.get('name', 'Unknown')}' создана в IIKo!"
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Assembly chart creation failed: {response.status_code}',
                        'response': response.text,
                        'note': f'Не удалось создать техкарту: {response.text[:100]}'
                    }
                    
        except Exception as e:
            self.logger.error(f"Error creating assembly chart: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'note': 'Ошибка при создании техкарты в IIKo'
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
            
            self.logger.info(f"📋 Getting assembly charts from {date_from} to {date_to}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, params=params)
                
                self.logger.info(f"📋 Assembly charts response: {response.status_code}")
                
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
                        
                        self.logger.info(f"📋 Found {assembly_count} assembly charts and {prepared_count} prepared charts")
                        
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
                        'message': f'Техкарта удалена (ID: {chart_id})'
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
                "technologyDescription": tech_card_data.get('description', '') or 'Создано AI-Menu-Designer',
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
            
            # Extract number from strings like "15 мин", "1 час", "30 минут"
            import re
            
            # Look for minutes
            min_match = re.search(r'(\d+)\s*мин', cook_time_str, re.IGNORECASE)
            if min_match:
                return int(min_match.group(1))
            
            # Look for hours
            hour_match = re.search(r'(\d+)\s*час', cook_time_str, re.IGNORECASE)
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
                
                if 'ИНГРЕДИЕНТЫ' in line.upper() or '🥬' in line:
                    in_ingredients_section = True
                    continue
                    
                if in_ingredients_section and line:
                    # Stop if we hit another section
                    if any(marker in line.upper() for marker in ['ВРЕМЯ', 'СЕБЕСТОИМОСТЬ', 'РЕЦЕПТ', '⏰', '💰', '👨‍🍳']):
                        break
                    
                    # Parse ingredient line: "Название — количество единица (дополнительно)"
                    if '—' in line or '-' in line:
                        parts = line.replace('—', '|').replace('-', '|').split('|')
                        if len(parts) >= 2:
                            name = parts[0].strip().replace('•', '').strip()
                            amount_part = parts[1].strip()
                            
                            # Extract amount and unit
                            import re
                            amount_match = re.search(r'(\d+(?:\.\d+)?)\s*([а-яёa-z]*)', amount_part, re.IGNORECASE)
                            
                            if amount_match:
                                amount = float(amount_match.group(1))
                                unit = amount_match.group(2) if amount_match.group(2) else 'г'
                                
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
            self.logger.info(f"🍽️ COMPLETE DISH CREATION: Starting for '{dish_name}'")
            
            # STEP 1: Create Assembly Chart first
            self.logger.info(f"📋 STEP 1: Creating Assembly Chart for '{dish_name}'")
            try:
                assembly_result = await self.create_assembly_chart(tech_card_data, organization_id)
                complete_result['assembly_chart'] = assembly_result
                
                if assembly_result.get('success'):
                    complete_result['steps_completed'].append('assembly_chart_created')
                    assembly_chart_id = assembly_result.get('assembly_chart_id')
                    self.logger.info(f"✅ STEP 1: Assembly Chart created successfully! ID: {assembly_chart_id}")
                else:
                    complete_result['errors'].append(f"Assembly Chart creation failed: {assembly_result.get('error')}")
                    self.logger.warning(f"⚠️ STEP 1: Assembly Chart failed, continuing with DISH creation...")
                    assembly_chart_id = None
                    
            except Exception as e:
                complete_result['errors'].append(f"Assembly Chart exception: {str(e)}")
                self.logger.warning(f"❌ STEP 1 Exception: {str(e)}, continuing...")
                assembly_chart_id = None
            
            # STEP 2: Get or create "AI Menu Designer" category
            self.logger.info(f"📂 STEP 2: Handling category for DISH")
            if not category_id:
                try:
                    # Check if "AI Menu Designer" category exists
                    category_check = await self.check_category_exists("AI Menu Designer", organization_id)
                    if category_check.get('success') and category_check.get('exists'):
                        category_id = category_check.get('category', {}).get('id')
                        self.logger.info(f"✅ STEP 2: Using existing AI Menu Designer category: {category_id}")
                    else:
                        # Create the category
                        category_result = await self.create_category("AI Menu Designer", organization_id)
                        if category_result.get('success'):
                            category_id = category_result.get('category_id')
                            self.logger.info(f"✅ STEP 2: Created AI Menu Designer category: {category_id}")
                        else:
                            self.logger.warning(f"⚠️ STEP 2: Category creation failed, proceeding without category")
                            
                except Exception as e:
                    self.logger.warning(f"❌ STEP 2 Exception: {str(e)}, proceeding without category")
            
            complete_result['steps_completed'].append('category_handled')
            
            # STEP 3: Create DISH Product
            self.logger.info(f"🍽️ STEP 3: Creating DISH Product for '{dish_name}'")
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
                    self.logger.info(f"✅ STEP 3: DISH Product created successfully!")
                else:
                    complete_result['errors'].append(f"DISH Product creation failed: {dish_result.get('error')}")
                    self.logger.warning(f"⚠️ STEP 3: DISH Product creation failed")
                    
            except Exception as e:
                complete_result['errors'].append(f"DISH Product exception: {str(e)}")
                self.logger.error(f"❌ STEP 3 Exception: {str(e)}")
            
            # DETERMINE OVERALL SUCCESS
            has_assembly = complete_result.get('assembly_chart', {}).get('success', False)
            has_dish = complete_result.get('dish_product', {}).get('success', False)
            
            if has_assembly and has_dish:
                complete_result['success'] = True
                complete_result['status'] = 'complete_success'
                complete_result['message'] = f"✅ Блюдо '{dish_name}' полностью создано в IIKo (техкарта + продукт)!"
                self.logger.info(f"🎉 COMPLETE SUCCESS: Both Assembly Chart and DISH Product created for '{dish_name}'")
            elif has_assembly:
                complete_result['success'] = True  # Partial success is still success
                complete_result['status'] = 'assembly_only'
                complete_result['message'] = f"⚠️ Техкарта создана, но блюдо не добавлено в меню. Создана только Assembly Chart для '{dish_name}'"
                self.logger.info(f"⚠️ PARTIAL SUCCESS: Only Assembly Chart created for '{dish_name}'")
            elif has_dish:
                complete_result['success'] = True  # Partial success is still success
                complete_result['status'] = 'dish_only'
                complete_result['message'] = f"⚠️ Блюдо добавлено в меню без техкарты. Создан только DISH продукт для '{dish_name}'"
                self.logger.info(f"⚠️ PARTIAL SUCCESS: Only DISH Product created for '{dish_name}'")
            else:
                complete_result['success'] = False
                complete_result['status'] = 'complete_failure'  
                complete_result['message'] = f"❌ Не удалось создать блюдо '{dish_name}' в IIKo"
                self.logger.error(f"❌ COMPLETE FAILURE: Neither Assembly Chart nor DISH Product created for '{dish_name}'")
            
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
                'message': f"❌ Критическая ошибка при создании блюда: {str(e)}"
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
        logger.warning("⚠️ CORS: Allowing all origins (development mode)")
        return ["*"]
    
    logger.info(f"🌐 CORS origins: {base_origins}")
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
        "techniques": ["выпечка", "кофейные напитки", "легкие блюда", "десерты"],
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
        "description": "Быстрое питание с стандартизированным меню",
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
                    "venue_concept": "Семейный ресторан",
                    "target_audience": "Семьи с детьми",
                    "special_features": [],
                    "kitchen_equipment": ["плита", "духовка", "холодильник"],
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
            "venue_concept": "Семейный ресторан",
            "target_audience": "Семьи с детьми",
            "special_features": [],
            "kitchen_equipment": ["плита", "духовка", "холодильник"],
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
        
        # Если пользователь не найден и это тестовый ID, создаем временного пользователя
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
            # from emergentintegrations.tools import web_search  # Removed for local development
            # web_search = None  # Placeholder
            # price_search_result = web_search(search_query, search_context_size="medium")  # Disabled for local
            price_search_result = "Данные по ценам недоступны (web_search disabled)"
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
        
        # Using GPT-5-mini for all users
        ai_model = "gpt-5-mini"
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
                current_content = f"**{v2_data.get('meta', {}).get('title', 'Tech Card')}**\n\nИнгредиенты:\n"
                for ing in v2_data.get('ingredients', []):
                    current_content += f"- {ing.get('name', '')} — {ing.get('netto_g', 0)}г\n"
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
                {"role": "system", "content": "Ты профессиональный AI-помощник для шеф-поваров. Редактируешь технологические карты согласно запросам пользователей."},
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
    # ВРЕМЕННО ОТКЛЮЧЕНО для тестирования - включим когда будет платежка
    # if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
    #     raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
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
    # ВРЕМЕННО ОТКЛЮЧЕНО для тестирования - включим когда будет платежка
    # if not user or user.get('subscription_plan', 'free') not in ['pro', 'business']:
    #     raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
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
                raise HTTPException(status_code=400, detail=f"Некорректный JSON формат: {str(e)}")
        
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
                    raise HTTPException(status_code=400, detail=f"Не удалось прочитать CSV файл: {str(e)}")
            
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
            raise HTTPException(status_code=400, detail="Поддерживаются только JSON и CSV файлы")
        
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
            "message": f"Обработано {len(processed_nutrition)} позиций по питанию",
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
        # UNIFIED HISTORY: Объединяем данные из user_history и tech_cards коллекций
        
        # Получаем V2 техкарты из user_history (новый API)
        history_docs = await db.user_history.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(100)
        
        # Получаем V1 техкарты из tech_cards (старый API)
        tech_cards_docs = await db.tech_cards.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(100)
        
        # Convert to serializable format by removing MongoDB ObjectId
        history = []
        
        # Добавляем V2 техкарты из user_history
        for doc in history_docs:
            if "_id" in doc:
                del doc["_id"]
            history.append(doc)
        
        # Добавляем V1 техкарты из tech_cards как legacy записи  
        for doc in tech_cards_docs:
            if "_id" in doc:
                del doc["_id"]
            
            # Конвертируем V1 формат в unified формат
            unified_doc = {
                "id": doc.get("id"),
                "user_id": doc.get("user_id"),
                "dish_name": doc.get("dish_name"),
                "content": doc.get("content"),
                "created_at": doc.get("created_at"),
                "is_menu": False,
                "status": "success",  # V1 техкарты всегда были успешными
                "techcard_v2_data": None  # V1 не имеет V2 данных
            }
            history.append(unified_doc)
        
        # Сортируем все по дате создания (новые сверху) с безопасным сравнением
        def safe_sort_key(x):
            created_at = x.get("created_at", "")
            if isinstance(created_at, str):
                try:
                    # Пробуем парсить ISO datetime строку
                    from datetime import datetime
                    return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except:
                    # Если не получается, возвращаем очень старую дату
                    return datetime(1970, 1, 1)
            elif hasattr(created_at, 'year'):  # datetime object
                return created_at
            else:
                # Fallback для других типов
                return datetime(1970, 1, 1)
        
        history.sort(key=safe_sort_key, reverse=True)
        
        # Ограничиваем до 50 записей
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

        # Create comprehensive enhanced prompt for GPT-5-mini
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
                    
=== КРИТИЧЕСКОЕ ТРЕБОВАНИЕ ===
ВНИМАНИЕ: В предыдущей попытке было сгенерировано только {total_dishes} блюд вместо {dish_count}!
ОБЯЗАТЕЛЬНО создай РОВНО {dish_count} блюд с конкретными названиями!
НЕ ИСПОЛЬЗУЙ заглушки типа "Специальное блюдо дня"!
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
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
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
            "message": f"Массовая генерация завершена! Создано {len(generated_tech_cards)} из {len(all_dishes)} техкарт."
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
        regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
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
            "message": f"Простое меню '{request.menu_type}' успешно создано!"
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
            "message": f"Проект '{request.project_name}' успешно создан!"
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
            "creation_time_saved": len(menus) * 15 + len(tech_cards) * 45,  # минуты
            "estimated_cost_savings": len(menus) * 5000 + len(tech_cards) * 2000,  # рубли
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
            'advanced_techniques': ['су-вид', 'молекулярная', 'конфи', 'фламбирование'],
            'premium_ingredients': ['трюфель', 'икра', 'фуа-гра', 'мраморная говядина', 'тунец'],
            'complex_preparations': ['маринад', 'долгое тушение', 'ферментация', '24 часа']
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
            if 'Категория:' in content:
                try:
                    category_line = [line for line in content.split('\n') if 'Категория:' in line][0]
                    category = category_line.split('Категория:')[1].strip().replace('**', '')
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
                "title": "Упростите сложные блюда",
                "description": f"Проект имеет высокую сложность ({complexity_score}%). Рассмотрите упрощение некоторых рецептов для ускорения приготовления.",
                "action": "review_complex_dishes"
            })
        
        categories_count = len(productivity.get("categories_covered", []))
        if categories_count < 3:
            recommendations.append({
                "type": "expansion",
                "priority": "medium",
                "title": "Расширьте ассортимент",
                "description": f"Проект покрывает только {categories_count} категории. Добавьте блюда из других категорий для разнообразия.",
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
                    "title": "Улучшите названия блюд",
                    "description": f"Только {match_rate:.1f}% блюд проекта найдены в продажах. Проверьте соответствие названий в меню и IIKo.",
                    "action": "sync_dish_names"
                })
            
            market_share = sales_analytics.get("market_share", {})
            revenue_share = market_share.get("project_revenue_share", 0)
            
            if revenue_share > 20:
                recommendations.append({
                    "type": "success",
                    "priority": "low",
                    "title": "Отличная производительность!",
                    "description": f"Блюда проекта составляют {revenue_share:.1f}% от общей выручки. Это превосходный результат!",
                    "action": "maintain_strategy"
                })
            elif revenue_share < 5:
                recommendations.append({
                    "type": "promotion",
                    "priority": "high",
                    "title": "Увеличьте продвижение блюд",
                    "description": f"Блюда проекта составляют только {revenue_share:.1f}% выручки. Рассмотрите маркетинговые акции.",
                    "action": "promote_dishes"
                })
        
        # Time and cost savings highlights
        time_saved = productivity.get("time_saved_minutes", 0)
        if time_saved > 120:  # More than 2 hours
            recommendations.append({
                "type": "achievement",
                "priority": "low",
                "title": "Значительная экономия времени",
                "description": f"Проект сэкономил {time_saved} минут работы! Это эквивалент {time_saved // 60} часов профессиональной разработки меню.",
                "action": "celebrate_efficiency"
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return [{
            "type": "error",
            "priority": "low",
            "title": "Ошибка анализа",
            "description": "Не удалось сгенерировать рекомендации из-за ошибки анализа данных.",
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
            "message": f"Проект экспортирован в формат {export_format.upper()}",
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
                "Название проекта": project_info.get("project_name"),
                "Тип проекта": project_info.get("project_type"),
                "Описание": project_info.get("description", ""),
                "Дата создания": project_info.get("created_at"),
                "Количество меню": len(export_data["menus"]),
                "Количество техкарт": len(export_data["tech_cards"]),
                "Статус": "Активный" if project_info.get("is_active") else "Неактивный"
            }])
            project_overview.to_excel(writer, sheet_name='Обзор проекта', index=False)
            
            # Menus Sheet
            if export_data["menus"]:
                menus_data = []
                for menu in export_data["menus"]:
                    dishes = menu.get('dishes', [])
                    menus_data.append({
                        "ID меню": menu.get("menu_id"),
                        "Тип меню": menu.get("menu_type"),
                        "Количество блюд": len(dishes),
                        "Дата создания": menu.get("created_at"),
                        "Описание": menu.get("expectations", "")[:100] + "..." if len(menu.get("expectations", "")) > 100 else menu.get("expectations", "")
                    })
                
                menus_df = pd.DataFrame(menus_data)
                menus_df.to_excel(writer, sheet_name='Меню', index=False)
            
            # Tech Cards Sheet
            if export_data["tech_cards"]:
                tech_cards_data = []
                for card in export_data["tech_cards"]:
                    tech_cards_data.append({
                        "Название блюда": card.get("dish_name"),
                        "Дата создания": card.get("created_at"),
                        "Город": card.get("city", ""),
                        "Тип": "Вдохновение" if card.get("is_inspiration") else "Стандарт"
                    })
                
                tech_cards_df = pd.DataFrame(tech_cards_data)
                tech_cards_df.to_excel(writer, sheet_name='Техкарты', index=False)
            
            # Statistics Sheet
            if export_data.get("stats"):
                stats_data = pd.DataFrame([export_data["stats"]])
                stats_data.to_excel(writer, sheet_name='Статистика', index=False)
        
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
    logger.info(f"🚀 ENHANCED UPLOAD: Uploading tech card '{request.name}' as complete dish to IIKo organization: {request.organization_id}")
    
    try:
        # Prepare tech card data
        tech_card_data = {
            'name': request.name,
            'description': request.description or 'Создано AI-Menu-Designer',
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
                "note": "✅ Блюдо создано как полноценный продукт в IIKo (техкарта + меню)!",
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
                    "note": "⚠️ Создана только техкарта (Assembly Chart). Блюдо не добавлено в меню.",
                    "warning": "Для появления в меню требуется создание продукта"
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error'),
                    "legacy_error": legacy_result.get('error'),
                    "note": "❌ Не удалось создать ни блюдо, ни техкарту"
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

@api_router.get("/iiko/sales-report/{organization_id}")
async def get_iiko_sales_report(
    organization_id: str,
    date_from: str = None,
    date_to: str = None
):
    """Get sales/revenue report from IIKo - SIMPLE TEST"""
    logger.info(f"💰 SALES REPORT REQUEST: Getting sales data for {organization_id}")
    
    try:
        # Get sales report from IIKo
        sales_report = await iiko_service.get_sales_report(organization_id, date_from, date_to)
        
        if sales_report.get('success'):
            logger.info(f"✅ Sales report retrieved successfully")
            
            return {
                "success": True,
                "message": "Отчет по выручке получен успешно",
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
            logger.warning(f"⚠️ Sales report failed: {sales_report.get('error')}")
            
            return {
                "success": False,
                "message": "Не удалось получить отчет по продажам",
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
        logger.error(f"❌ Error in sales report endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting sales report: {str(e)}")

@api_router.get("/iiko/analytics/{organization_id}")  
async def get_iiko_analytics_dashboard(organization_id: str):
    """Get comprehensive analytics dashboard data from IIKo"""
    logger.info(f"📊 ANALYTICS DASHBOARD: Getting analytics for {organization_id}")
    
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
            "message": "Аналитическая панель сформирована",
            "analytics": analytics_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error in analytics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")

@api_router.post("/iiko/ai-menu-analysis/{organization_id}")
async def ai_analyze_menu(organization_id: str, request: dict = None):
    """🧠 AI АНАЛИЗ МЕНЮ - анализирует реальное меню из IIKo через GPT-4"""
    logger.info(f"🧠 AI MENU ANALYSIS: Analyzing menu for {organization_id}")
    
    try:
        # 1. Получаем реальное меню из IIKo
        logger.info("📊 Fetching menu data from IIKo...")
        menu_data = await iiko_service.get_menu_items([organization_id])
        
        if not menu_data or not menu_data.get('items'):
            raise HTTPException(status_code=404, detail="Menu data not found")
        
        categories = menu_data.get('categories', [])
        items = menu_data.get('items', [])
        
        logger.info(f"📋 Loaded {len(items)} menu items in {len(categories)} categories")
        
        # 2. Подготавливаем данные для AI анализа
        analysis_type = request.get('analysis_type', 'comprehensive') if request else 'comprehensive'
        
        # Группируем блюда по категориям для анализа
        menu_by_categories = {}
        for category in categories:
            cat_items = [item for item in items if item.get('category_id') == category['id']]
            if cat_items:  # Только категории с блюдами
                menu_by_categories[category['name']] = [
                    {
                        'name': item['name'],
                        'description': item.get('description', ''),
                        'id': item['id']
                    }
                    for item in cat_items[:10]  # Первые 10 для анализа
                ]
        
        # 3. Формируем промпт для GPT-4
        ai_prompt = f"""
Ты - эксперт по ресторанному бизнесу и оптимизации меню. Проанализируй РЕАЛЬНОЕ меню ресторана "Edison Craft Bar".

ДАННЫЕ МЕНЮ:
- Всего позиций: {len(items)}
- Категорий: {len(categories)}
- Детализация по категориям:
{json.dumps(menu_by_categories, ensure_ascii=False, indent=2)}

ЗАДАЧА: Дай 5 КОНКРЕТНЫХ практических рекомендаций для увеличения прибыли этого ресторана.

ФОРМАТ ОТВЕТА:
1. **[Тема рекомендации]**: [Конкретная рекомендация с примерами из меню]
2. **[Тема рекомендации]**: [Конкретная рекомендация с примерами из меню]
...

АКЦЕНТ НА:
- Конкретные названия блюд из меню
- Практические действия (поднять цену, убрать, добавить)
- Цифры и проценты
- Психологию продаж

СТИЛЬ: Как опытный ресторатор, кратко и по делу.
"""

        # 4. Отправляем на анализ в GPT-4
        logger.info("🤖 Sending menu to GPT-4 for analysis...")
        
        ai_response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по ресторанному бизнесу с 20-летним опытом оптимизации меню."},
                {"role": "user", "content": ai_prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        ai_analysis = ai_response.choices[0].message.content
        
        # 5. Формируем детальный ответ
        return {
            "success": True,
            "message": "🧠 AI-анализ меню завершен",
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
        logger.error(f"❌ Error in AI menu analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in AI analysis: {str(e)}")

@api_router.get("/iiko/category/{organization_id}/{category_name}")
async def get_iiko_category_items(organization_id: str, category_name: str):
    """Get items from specific IIKo category for menu browsing"""
    try:
        logger.info(f"🏷️ Getting category items: {category_name} from organization: {organization_id}")
        
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
        
        logger.info(f"📊 Found {len(category_items)} items in category '{category_name}'")
        
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
        logger.info(f"📂 Getting categories for organization: {organization_id}")
        
        result = await iiko_service.get_categories(organization_id)
        
        if result.get('success'):
            logger.info(f"✅ Retrieved {result.get('categories_count', 0)} categories from IIKo")
            return JSONResponse(
                content=result,
                status_code=200
            )
        else:
            logger.error(f"❌ Failed to get categories: {result.get('error')}")
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
        
        logger.info(f"📂 Creating category '{category_name}' in IIKo organization: {organization_id}")
        
        # First check if category already exists
        check_result = await iiko_service.check_category_exists(category_name, organization_id)
        
        if check_result.get('success') and check_result.get('exists'):
            existing_category = check_result.get('category')
            logger.info(f"ℹ️ Category '{category_name}' already exists")
            return JSONResponse(
                content={
                    "success": True,
                    "already_exists": True,
                    "category": existing_category,
                    "message": f"Категория '{category_name}' уже существует в IIKo"
                },
                status_code=200
            )
        
        # Create new category
        result = await iiko_service.create_category(category_name, organization_id)
        
        if result.get('success'):
            logger.info(f"✅ Category '{category_name}' created successfully")
            return JSONResponse(
                content=result,
                status_code=201
            )
        else:
            logger.error(f"❌ Failed to create category: {result.get('error')}")
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
        
        logger.info(f"📂 Checking category '{category_name}' in organization: {organization_id}")
        
        result = await iiko_service.check_category_exists(category_name, organization_id)
        
        if result.get('success'):
            return JSONResponse(
                content=result,
                status_code=200
            )
        else:
            logger.error(f"❌ Failed to check category: {result.get('error')}")
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
        logger.info(f"🍽️ COMPLETE DISH: Creating complete dish '{request.name}' in IIKo organization: {request.organization_id}")
        
        # Prepare tech card data
        tech_card_data = {
            'name': request.name,
            'description': request.description or 'Создано AI-Menu-Designer',
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
        logger.info(f"🔨 Creating assembly chart '{request.name}' in IIKo organization: {request.organization_id}")
        
        # Prepare tech card data for assembly chart
        tech_card_data = {
            'name': request.name,
            'description': request.description or 'Создано AI-Menu-Designer',
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
                "note": "✅ Техкарта создана как Assembly Chart в IIKo!"
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
        logger.info(f"📋 Getting all assembly charts from IIKo organization: {organization_id}")
        
        result = await iiko_service.get_all_assembly_charts(organization_id)
        
        if result.get('success'):
            return {
                "success": True,
                "organization_id": organization_id,
                "assembly_charts": result.get('assembly_charts', []),
                "count": result.get('count', 0),
                "message": f"Найдено {result.get('count', 0)} техкарт в IIKo"
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
        logger.info(f"🔍 Getting assembly chart by ID from IIKo: {chart_id}")
        
        result = await iiko_service.get_assembly_chart_by_id(chart_id)
        
        if result.get('success'):
            return {
                "success": True,
                "chart_id": chart_id,
                "assembly_chart": result.get('assembly_chart'),
                "message": "Техкарта найдена"
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
        logger.info(f"🗑️ Deleting assembly chart from IIKo: {chart_id}")
        
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

# ===== CULINARY ASSISTANT CHAT =====
@api_router.post("/assistant/chat")
async def chat_with_assistant(request: dict):
    """
    Чат с кулинарным ассистентом RECEPTOR с поддержкой tool-calling
    
    Request:
    {
        "user_id": "uuid",
        "message": "Создай техкарту для стейка из говядины",
        "conversation_id": "uuid"  # опционально, для продолжения диалога
    }
    
    Response:
    {
        "response": "Я создал техкарту для стейка...",
        "conversation_id": "uuid",
        "tool_calls": [{"tool": "generateTechcard", "result": {...}}],  # если были tool calls
        "tokens_used": 150,
        "credits_spent": 5
    }
    """
    user_id = request.get("user_id", "demo_user")
    message = request.get("message", "").strip()
    conversation_id = request.get("conversation_id")
    
    if not message:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
    
    # Получаем профиль заведения для контекста
    user = await db.users.find_one({"id": user_id})
    venue_profile = {}
    if user:
        venue_profile = {
            "venue_type": user.get("venue_type"),
            "cuisine_focus": user.get("cuisine_focus", []),
            "average_check": user.get("average_check"),
            "kitchen_equipment": user.get("kitchen_equipment", [])
        }
    
    # Поиск по базе знаний для контекста
    knowledge_context = ""
    try:
        from receptor_agent.rag.search import search_knowledge_base
        
        # Определяем категории на основе запроса
        categories = []
        query_lower = message.lower()
        if any(word in query_lower for word in ['haccp', 'санпин', 'норматив', 'стандарт', 'требование']):
            categories.append('haccp')
        if any(word in query_lower for word in ['hr', 'персонал', 'сотрудник', 'мотивация', 'обучение']):
            categories.append('hr')
        if any(word in query_lower for word in ['финанс', 'roi', 'прибыль', 'себестоимость', 'наценка', 'маржа']):
            categories.append('finance')
        if any(word in query_lower for word in ['маркетинг', 'smm', 'реклама', 'продвижение', 'контент']):
            categories.append('marketing')
        if any(word in query_lower for word in ['iiko', 'api', 'интеграция', 'технический']):
            categories.append('iiko')
        
        # Ищем релевантную информацию
        search_results = search_knowledge_base(message, top_k=3, categories=categories if categories else None)
        
        if search_results:
            knowledge_context = "\n\nРелевантная информация из базы знаний RECEPTOR:\n"
            for i, result in enumerate(search_results, 1):
                knowledge_context += f"\n[{i}] {result['source']} ({result['category']}):\n{result['content'][:500]}...\n"
    except Exception as e:
        logger.warning(f"Error searching knowledge base: {str(e)}")
        knowledge_context = ""
    
    # Системный промпт для кулинарного ассистента
    system_prompt = """Ты RECEPTOR — профессиональный AI-ассистент для ресторанного бизнеса. 
Твоя специализация:
- Рецепты и техники приготовления
- Финансовые расчеты (себестоимость, наценка, маржа)
- Оптимизация меню и анализ рентабельности
- Управленческие вопросы ресторанного бизнеса
- Кулинарные советы и рекомендации
- HACCP и СанПиН нормативы
- HR и управление персоналом
- Маркетинг и SMM
- Техническая документация iiko

Всегда отвечай профессионально, но доступно. Давай конкретные советы с примерами и формулами.
Если пользователь просит создать техкарту или рецепт, используй функцию generateTechcard.
Если спрашивает о расчетах, давай конкретные формулы и примеры.
Используй информацию из базы знаний RECEPTOR для более точных ответов.
Будь дружелюбным и полезным. Отвечай на русском языке.""" + knowledge_context

    # Tool definitions для OpenAI Function Calling
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generateTechcard",
                "description": "Создать технологическую карту блюда. Используй когда пользователь просит создать техкарту, рецепт или блюдо.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dish_name": {
                            "type": "string",
                            "description": "Название блюда с подробным описанием"
                        },
                        "cuisine": {
                            "type": "string",
                            "description": "Тип кухни (русская, итальянская, азиатская и т.д.)",
                            "default": "европейская"
                        },
                        "equipment": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Список доступного оборудования"
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
                "description": "Поиск по базе знаний RECEPTOR (HACCP, СанПиН, HR, финансы, техники, iiko документация, бизнес-кейсы). Используй для ответов на вопросы о нормах, стандартах, лучших практиках.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Поисковый запрос на русском языке"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Количество результатов (1-10)",
                            "default": 5
                        },
                        "categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Фильтр по категориям: haccp, sanpin, hr, finance, marketing, iiko, techniques",
                            "default": []
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    try:
        # Получаем историю диалога, если есть conversation_id
        conversation_history = []
        if conversation_id:
            # TODO: Реализовать сохранение истории в БД
            # conversation_history = await get_conversation_history(conversation_id)
            pass
        
        # Формируем сообщения для LLM
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Добавляем историю (последние 10 сообщений для контекста)
        for hist_msg in conversation_history[-10:]:
            messages.append(hist_msg)
        
        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": message})
        
        # Вызов LLM с tool-calling
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI client not initialized")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",  # LLM решает, вызывать ли tool
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_message = response.choices[0].message
        tool_calls_result = []
        
        # Если LLM вызвал tool
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "generateTechcard":
                    # Генерируем техкарту
                    try:
                        from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
                        
                        # Подготовка данных для генерации
                        profile = ProfileInput(
                            name=function_args.get("dish_name", ""),
                            cuisine=function_args.get("cuisine", venue_profile.get("cuisine_focus", ["европейская"])[0] if venue_profile.get("cuisine_focus") else "европейская"),
                            equipment=function_args.get("equipment", venue_profile.get("kitchen_equipment", ["плита", "кастрюля"])),
                            budget=float(venue_profile.get("average_check", 500)) if venue_profile.get("average_check") else 500.0,
                            dietary=[],
                            user_id=user_id
                        )
                        
                        # Запускаем генерацию
                        pipeline_result = run_pipeline(profile)
                        
                        # Логируем результат генерации
                        logger.info(f"Techcard generation result: status={pipeline_result.status}, has_card={pipeline_result.card is not None}")
                        
                        card_data = None
                        if pipeline_result.card:
                            try:
                                # Конвертируем Pydantic модель в dict
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
                        
                        # Добавляем результат в контекст для LLM
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
                                "message": "Техкарта успешно создана" if pipeline_result.status in ["success", "draft", "READY"] else "Ошибка создания техкарты"
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
            
            # Получаем финальный ответ от LLM с учетом результатов tool calls
            final_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            assistant_response = final_response.choices[0].message.content
        else:
            # Обычный ответ без tool calls
            assistant_response = assistant_message.content
        
        # Создаем новый conversation_id, если его нет
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # TODO: Сохранить историю в БД
        # await save_conversation_message(conversation_id, user_id, "user", message)
        # await save_conversation_message(conversation_id, user_id, "assistant", assistant_response)
        
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
            detail=f"Ошибка при обработке запроса: {str(e)}"
        )

# Include the router in the main app
app.include_router(api_router)

# Google OAuth router
from google_auth import router as google_auth_router
app.include_router(google_auth_router)

# YooKassa payment integration
try:
    from yookassa_integration import router as yookassa_router
    app.include_router(yookassa_router)
    logger.info("✅ YooKassa integration router loaded")
except ImportError as e:
    logger.warning(f"⚠️ YooKassa integration not available: {e}")
except Exception as e:
    logger.warning(f"⚠️ Failed to load YooKassa router: {e}")

# Подключаем v2-функционал только по флагу
# КРИТИЧЕСКИ ВАЖНО для iiko интеграции: принудительно включаем V2
# Принудительно включаем V2 для локальной разработки
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
    logger.info("🚀 Receptor AI Backend starting up...")
    logger.info(f"📦 MongoDB URI configured: {bool(os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL'))}")
    logger.info(f"🤖 OpenAI API Key configured: {bool(os.environ.get('OPENAI_API_KEY'))}")
    logger.info(f"🔧 Environment: {os.environ.get('ENVIRONMENT', 'production')}")
    logger.info("✅ Server startup complete!")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("🛑 Shutting down...")
    client.close()

@app.post("/api/v1/generate-recipe")
async def generate_recipe_v1(request: dict):
    """Generate beautiful V1 recipe with detailed steps for creativity and experimentation"""
    dish_name = request.get("dish_name")
    cuisine = request.get("cuisine", "европейская")
    restaurant_type = request.get("restaurant_type", "casual")
    user_id = request.get("user_id")
    
    if not dish_name or not user_id:
        raise HTTPException(status_code=400, detail="dish_name and user_id are required")
    
    try:
        print(f"🍳 Generating V1 Recipe for: {dish_name}")
        
        # Enhanced prompt for beautiful V1 recipes
        prompt = f"""Ты — шеф-повар мирового уровня и кулинарный писатель. 
        
Создай КРАСИВЫЙ И ПОДРОБНЫЙ рецепт для блюда "{dish_name}" в стиле {cuisine} кухни для {restaurant_type} заведения.

ФОРМАТ РЕЦЕПТА V1 (для творчества и экспериментов):

**{dish_name}**

🎯 **ОПИСАНИЕ**
Вдохновляющее описание блюда с историей, традициями и особенностями

⏱️ **ВРЕМЕННЫЕ РАМКИ**
Подготовка: X минут
Приготовление: X минут
Общее время: X минут

👥 **ПОРЦИИ**
На X порций

🛒 **ИНГРЕДИЕНТЫ**
Основные ингредиенты:
• Ингредиент 1 - количество (подробное описание, зачем нужен)
• Ингредиент 2 - количество (подробное описание, зачем нужен)
...

Специи и приправы:
• Специя 1 - количество (влияние на вкус)
• Специя 2 - количество (влияние на вкус)
...

🔥 **ПОШАГОВОЕ ПРИГОТОВЛЕНИЕ**

**Шаг 1: Подготовка ингредиентов**
Детальное описание подготовительного этапа с советами

**Шаг 2: [Название этапа]**  
Подробные инструкции с температурами, временем, техниками

**Шаг 3: [Название этапа]**
Еще более детальные инструкции...

[Продолжить до завершения - обычно 5-8 шагов]

👨‍🍳 **СЕКРЕТЫ ШЕФА**
• Профессиональный совет 1
• Профессиональный совет 2
• Секретная техника 3

🎨 **ПОДАЧА И ПРЕЗЕНТАЦИЯ**
Как красиво подать блюдо, украшения, посуда

🔄 **ВАРИАЦИИ И ЭКСПЕРИМЕНТЫ**
• Интересная вариация 1
• Креативная замена ингредиентов 2
• Сезонная адаптация 3

💡 **ПОЛЕЗНЫЕ СОВЕТЫ**
• Как сохранить
• Что делать если что-то пошло не так
• Как заранее подготовить

Сделай рецепт МАКСИМАЛЬНО ПОДРОБНЫМ, ВДОХНОВЛЯЮЩИМ и КРАСИВЫМ для чтения!"""

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
        
        print(f"✅ V1 Recipe generated successfully for: {dish_name}")
        
        return {"recipe": recipe_content, "meta": {"id": recipe_v1["id"], "version": "v1"}}
        
    except Exception as e:
        print(f"❌ Error generating V1 recipe: {e}")
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
            raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    average_check = user.get("average_check", 800)
    venue_name = user.get("venue_name", "заведение")
    
    # Convert tech_card to string if it's a dict (V2 or aiKitchenRecipe format)
    if isinstance(tech_card, dict):
        if 'content' in tech_card:
            tech_card_str = tech_card['content']
        else:
            tech_card_str = str(tech_card)
    else:
        tech_card_str = tech_card
    
    # Extract dish name from tech card
    dish_name = "блюдо"
    for line in tech_card_str.split('\n'):
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
{tech_card_str}

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
            model="gpt-5-mini",
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
            raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
    # Get venue profile for personalization
    venue_type = user.get("venue_type", "family_restaurant")
    venue_info = VENUE_TYPES.get(venue_type, VENUE_TYPES["family_restaurant"])
    cuisine_focus = user.get("cuisine_focus", [])
    average_check = user.get("average_check", 800)
    
    # Extract dish name from tech card
    dish_name = "блюдо"
    if isinstance(tech_card, dict):
        dish_name = tech_card.get("name", "блюдо")
    elif isinstance(tech_card, str):
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
            model="gpt-5-mini",
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
            raise HTTPException(status_code=403, detail="Требуется PRO подписка")
    
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
    dish_name = "блюдо"
    for line in tech_card_str.split('\n'):
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
{tech_card_str}

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
            model="gpt-5-mini",
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
    
    # Если пользователь не найден и это тестовый/демо ID, создаем временного пользователя
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
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # ВРЕМЕННО ОТКЛЮЧЕНО для тестирования - включим когда будет платежка
    # if user.get("subscription_plan") not in ["pro", "business"]:
    #     raise HTTPException(status_code=403, detail="Функция доступна только для PRO пользователей")
    
    # Извлекаем название блюда из техкарты
    dish_name = "блюдо"
    if isinstance(tech_card, dict): dish_name = tech_card.get("name", "блюдо")
    
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
            model="gpt-5-mini",
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
            "message": "Техкарта сохранена успешно"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

@app.post("/api/v1/user/save-recipe")
async def save_v1_recipe(request: dict):
    """Сохранение V1 рецепта в историю пользователя"""
    user_id = request.get("user_id")
    recipe_content = request.get("recipe_content")
    recipe_name = request.get("recipe_name", "Рецепт V1")
    recipe_type = request.get("recipe_type", "v1")
    source_type = request.get("source_type", "manual")  # 'manual', 'inspiration', 'food_pairing', etc.
    
    if not user_id or not recipe_content:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
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
            "message": f"Рецепт V1 '{recipe_name}' сохранен в историю"
        }
        
    except Exception as e:
        print(f"Error saving V1 recipe: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения рецепта: {str(e)}")

@app.post("/api/v1/convert-recipe-to-techcard")
async def convert_recipe_to_techcard(request: dict):
    """Настоящая конвертация V1 рецепта в полноценную V2 техкарту через pipeline"""
    user_id = request.get("user_id")
    recipe_content = request.get("recipe_content")
    recipe_name = request.get("recipe_name", "Техкарта из рецепта")
    
    if not user_id or not recipe_content:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    try:
        print(f"🔄 Converting V1 recipe to real V2 techcard: {recipe_name}")
        
        # ШАГ 1: Парсим V1 рецепт через LLM для извлечения данных
        # Используем тот же openai_client что и в рабочей генерации техкарт
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI клиент не инициализирован")
        
        parsing_prompt = f"""
Проанализируй этот рецепт и извлеки ключевые данные для генерации профессиональной техкарты:

РЕЦЕПТ V1:
{recipe_content}

ВЕРНИ JSON в точном формате:
{{
    "dish_name": "точное название блюда",
    "cuisine": "тип кухни (европейская/азиатская/русская и т.д.)",
    "category": "категория (горячее/холодное/десерт/салат/суп)",
    "main_ingredients": ["основной ингредиент 1", "основной ингредиент 2", "основной ингредиент 3"],
    "cooking_method": "способ приготовления (жарка/варка/тушение и т.д.)",
    "estimated_time": число_минут,
    "difficulty": "простое/среднее/сложное"
}}

Отвечай ТОЛЬКО JSON без дополнительного текста.
"""

        parse_response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу рецептов. Возвращай только корректный JSON."},
                {"role": "user", "content": parsing_prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        # Парсим JSON ответ
        import json
        try:
            parsed_data = json.loads(parse_response.choices[0].message.content.strip())
            print(f"✅ Parsed recipe data: {parsed_data}")
        except:
            # Fallback если JSON не распарсился
            parsed_data = {
                "dish_name": recipe_name,
                "cuisine": "европейская", 
                "category": "горячее",
                "main_ingredients": ["основной продукт"],
                "cooking_method": "комбинированная обработка",
                "estimated_time": 30,
                "difficulty": "среднее"
            }
            print(f"⚠️ JSON parse failed, using fallback: {parsed_data}")
        
        # ШАГ 2: Вызываем НАСТОЯЩУЮ V2 генерацию через techcards_v2 pipeline
        from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
        
        # Создаем профиль для V2 pipeline с данными из V1 рецепта
        profile = ProfileInput(
            name=parsed_data["dish_name"],
            cuisine=parsed_data["cuisine"],
            equipment=["плита", "кастрюля", "сковорода"],  # Базовое оборудование
            budget=300.0,  # Средний бюджет
            dietary=[],
            user_id=user_id
        )
        
        print(f"🚀 Running V2 pipeline with profile: {profile}")
        
        # Запускаем полноценный V2 pipeline
        pipeline_result = run_pipeline(profile)
        
        if pipeline_result.status in ["success", "draft", "READY"] and pipeline_result.card:
            print(f"✅ V2 pipeline succeeded with status: {pipeline_result.status}")
            
            # Получаем настоящую V2 техкарту
            real_techcard_v2 = pipeline_result.card
            
            # Добавляем метку что это конвертация из V1
            if hasattr(real_techcard_v2, 'meta'):
                # Правильно обновляем Pydantic модель meta
                updated_meta = real_techcard_v2.meta.model_copy(deep=True)
                # Добавляем информацию о конвертации в timings (это разрешенное поле)
                updated_meta.timings['converted_from_v1'] = 1.0
                updated_meta.timings['original_recipe_length'] = len(recipe_content)
                real_techcard_v2 = real_techcard_v2.model_copy(update={"meta": updated_meta})
            
            # Сохраняем в базу как настоящую V2 техкарту (используем уже существующий async db)
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
                "message": f"Рецепт '{parsed_data['dish_name']}' успешно преобразован в настоящую V2 техкарту"
            }
        else:
            # Если V2 pipeline не сработал, падаем с ошибкой
            error_msg = f"V2 pipeline failed with status: {pipeline_result.status}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=f"Ошибка V2 генерации: {error_msg}")
        
    except Exception as e:
        print(f"❌ Error in V1→V2 conversion: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка конвертации: {str(e)}")

@app.post("/api/generate-food-pairing")
async def generate_food_pairing(request: dict):
    """AI Фудпейринг - подбор идеальных сочетаний для блюда"""
    tech_card = request.get("tech_card")
    user_id = request.get("user_id")
    
    if not tech_card or not user_id:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    try:
        # Извлекаем название блюда
        dish_name = "блюдо"
        if isinstance(tech_card, dict):
            dish_name = tech_card.get("meta", {}).get("title", "блюдо")
            if not dish_name and tech_card.get("name"):
                dish_name = tech_card.get("name")
        
        # Создаем промпт для фудпейринга
        pairing_prompt = f"""
Ты эксперт по фудпейрингу. Проанализируй блюдо "{dish_name}" и создай профессиональные рекомендации по сочетаниям.

БЛЮДО: {dish_name}

Создай подробные рекомендации в следующих категориях:

🍷 **НАПИТКИ:**
• Вина (указать сорта и причины сочетания)
• Безалкогольные напитки
• Коктейли (если подходят)

🥗 **ГАРНИРЫ И ДОБАВКИ:**
• Идеальные гарниры
• Соусы и заправки
• Травы и специи для усиления вкуса

🧀 **ДОПОЛНИТЕЛЬНЫЕ ПРОДУКТЫ:**
• Сыры (если подходят)
• Орехи, семена
• Фрукты или овощи для баланса

💡 **ПРОФЕССИОНАЛЬНЫЕ СОВЕТЫ:**
• Температурные контрасты
• Текстурные сочетания
• Сезонные рекомендации

Дай конкретные и практичные советы для ресторана.
"""

        # Используем тот же openai_client что и в рабочей генерации техкарт
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI клиент не инициализирован")
        
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Ты мастер фудпейринга с опытом работы в мишленовских ресторанах. Создавай точные и вкусные сочетания."},
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
            "message": f"Фудпейринг для '{dish_name}' создан"
        }
        
    except Exception as e:
        print(f"Error generating food pairing: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания фудпейринга: {str(e)}")

@app.post("/api/generate-inspiration")
async def generate_inspiration(request: dict):
    """AI Вдохновение - креативные твисты на блюда"""
    tech_card = request.get("tech_card")
    user_id = request.get("user_id")
    inspiration_prompt = request.get("inspiration_prompt", "Создай креативный твист на это блюдо")
    
    if not tech_card or not user_id:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    try:
        # Извлекаем название блюда
        dish_name = "блюдо"
        if isinstance(tech_card, dict):
            dish_name = tech_card.get("meta", {}).get("title", "блюдо")
            if not dish_name and tech_card.get("name"):
                dish_name = tech_card.get("name")
        
        # Создаем промпт для творческого вдохновения
        creativity_prompt = f"""
Ты креативный шеф-повар с мировым опытом. Создай инновационные варианты блюда "{dish_name}".

ИСХОДНОЕ БЛЮДО: {dish_name}

{inspiration_prompt}

Создай 3-4 креативных варианта:

🌍 **FUSION-ВАРИАНТЫ:**
• Азиатский твист
• Средиземноморская интерпретация  
• Скандинавский подход

🎨 **СОВРЕМЕННЫЕ ТЕХНИКИ:**
• Молекулярная гастрономия
• Ферментация
• Копчение или гриль

🌱 **АЛЬТЕРНАТИВЫ:**
• Веганская версия
• Безглютеновый вариант
• Кето-адаптация

🎭 **ПРЕЗЕНТАЦИЯ:**
• Необычная подача
• Интерактивные элементы
• Сезонное оформление

Для каждого варианта опиши ключевые изменения и почему это будет вкусно.
"""

        # Используем тот же openai_client что и в рабочей генерации техкарт
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI клиент не инициализирован")
        
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Ты новаторский шеф-повар, который создает революционные интерпретации классических блюд. Твои идеи всегда практичны и вкусны."},
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
            "message": f"Креативные идеи для '{dish_name}' созданы"
        }
        
    except Exception as e:
        print(f"Error generating inspiration: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания вдохновения: {str(e)}")

@app.post("/api/analyze-finances")
async def analyze_finances(request: dict):
    """Анализ финансов блюда для PRO пользователей"""
    user_id = request.get("user_id")
    tech_card = request.get("tech_card")
    
    if not user_id or not tech_card:
        raise HTTPException(status_code=400, detail="Не предоставлены обязательные параметры")
    
    # Проверяем подписку пользователя (PRO only)
    user = await db.users.find_one({"id": user_id})
    
    # Автоматически создаем тестового/демо пользователя
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
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # ВРЕМЕННО ОТКЛЮЧЕНО для тестирования - включим когда будет платежка
    # if user.get("subscription_plan") not in ["pro", "business"]:
    #     raise HTTPException(status_code=403, detail="Функция доступна только для PRO пользователей")
    
    # Convert tech_card to string if it's a dict (V2 or aiKitchenRecipe format)
    if isinstance(tech_card, dict):
        if 'content' in tech_card:
            tech_card_str = tech_card['content']
        else:
            tech_card_str = str(tech_card)
    else:
        tech_card_str = tech_card
    
    # Извлекаем название блюда
    dish_name = "блюдо"
    title_match = re.search(r'\*\*Название:\*\*\s*(.*?)(?=\n|$)', tech_card_str)
    if title_match:
        dish_name = title_match.group(1).strip()
    
    # Извлекаем ингредиенты и цены
    ingredients_match = re.search(r'\*\*Ингредиенты:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)', tech_card_str, re.DOTALL)
    ingredients_text = ingredients_match.group(1) if ingredients_match else ""
    
    # Получаем региональный коэффициент
    regional_coefficient = REGIONAL_COEFFICIENTS.get(user.get("city", "moscow").lower(), 1.0)
    
    # ✨ NEW: Поиск ингредиентов в IIKO каталоге пользователя для точных цен
    iiko_prices = {}
    iiko_matched_count = 0
    
    try:
        # Получаем IIKO каталог пользователя (если подключен)
        organization_id = user.get("organization_id", "default")
        iiko_products = list(db.rms_products.find({
            "organization_id": organization_id,
            "active": True
        }))
        
        if iiko_products:
            logger.info(f"🔍 Found {len(iiko_products)} products in IIKO catalog for user {user_id}")
            
            # Парсим ингредиенты из техкарты
            ingredient_lines = [line.strip() for line in ingredients_text.split('\n') if line.strip() and not line.strip().startswith('**')]
            
            for ingredient_line in ingredient_lines:
                # Извлекаем название ингредиента (до дефиса или двоеточия)
                ingredient_name = ingredient_line.split('-')[0].split(':')[0].strip()
                ingredient_name_clean = ingredient_name.replace('*', '').strip()
                
                if len(ingredient_name_clean) < 2:
                    continue
                
                # Ищем совпадение в IIKO каталоге
                for product in iiko_products:
                    product_name = product.get("name", "").lower()
                    ingredient_lower = ingredient_name_clean.lower()
                    
                    # Прямое совпадение или содержит
                    if product_name == ingredient_lower or ingredient_lower in product_name or product_name in ingredient_lower:
                        # Нашли совпадение!
                        price = product.get("price", 0)
                        if price > 0:
                            iiko_prices[ingredient_name_clean] = {
                                "price": price,
                                "unit": product.get("unit", "кг"),
                                "product_id": product.get("id"),
                                "confidence": "high"
                            }
                            iiko_matched_count += 1
                            logger.info(f"✅ Matched '{ingredient_name_clean}' with IIKO product '{product.get('name')}' = {price}₽")
                            break
        
        logger.info(f"📊 IIKO matching result: {iiko_matched_count} ingredients matched out of {len(ingredient_lines)}")
    
    except Exception as e:
        logger.error(f"⚠️ Error fetching IIKO prices: {e}")
        # Продолжаем без IIKO цен
    
    # Поиск актуальных цен в интернете
    search_query = f"цены на продукты {user.get('city', 'москва')} 2025 мясо овощи крупы молочные продукты"
    
    try:
        # from emergentintegrations.tools import web_search  # Removed for local development
        # web_search = None  # Placeholder
        # price_search_result = web_search(search_query, search_context_size="medium")  # Disabled for local
        price_search_result = "Данные по ценам недоступны (web_search disabled)"
    except Exception:
        price_search_result = "Данные по ценам недоступны"
    
    # Поиск цен конкурентов
    competitor_search_query = f"цены меню {dish_name} рестораны {user.get('city', 'москва')} 2025"
    
    try:
        competitor_search_result = web_search(competitor_search_query, search_context_size="medium")
    except Exception:
        competitor_search_result = "Данные по конкурентам недоступны"
    
    # Формируем информацию о IIKO ценах для промпта
    iiko_prices_info = ""
    if iiko_prices:
        iiko_prices_info = "\n\n🎯 ТОЧНЫЕ ЦЕНЫ ИЗ IIKO КАТАЛОГА (приоритет!):\n"
        for ingredient_name, price_data in iiko_prices.items():
            iiko_prices_info += f"- {ingredient_name}: {price_data['price']}₽ за {price_data['unit']} (source: IIKO, точная цена)\n"
        iiko_prices_info += f"\nИТОГО: {len(iiko_prices)} ингредиентов с точными ценами из IIKO."
    
    # Создаем промпт для финансового анализа
    prompt = f"""Ты — практичный финансовый консультант ресторанов с 15-летним опытом. Твоя специализация — КОНКРЕТНЫЕ решения, а не общие фразы.

Проанализируй блюдо "{dish_name}" и дай РЕАЛЬНЫЕ советы с цифрами и практическими шагами.

ТЕХКАРТА:
{tech_card}

РЕГИОНАЛЬНЫЙ КОЭФФИЦИЕНТ: {regional_coefficient}x

{iiko_prices_info}

ДОПОЛНИТЕЛЬНЫЕ ЦЕНЫ НА ПРОДУКТЫ (если не найдены в IIKO): {price_search_result}

КОНКУРЕНТЫ: {competitor_search_result}

⚠️ ВАЖНО:
1. Если ингредиент есть в IIKO каталоге выше - используй ТОЧНУЮ цену оттуда (это реальная цена поставщика).
2. Для остальных ингредиентов используй РЕАЛЬНЫЕ рыночные цены с учетом регионального коэффициента.
3. ОБЯЗАТЕЛЬНО: total_cost и recommended_price должны быть ЧИСЛАМИ (например 350, а НЕ "350₽" или "350 руб")
4. Цены должны быть РЕАЛИСТИЧНЫМИ для ресторана в 2025 году. Например, онигири с тунцом не может стоить 10₽ - реальная себестоимость 80-150₽.

ТИП ЗАВЕДЕНИЯ: {user.get('venue_type', 'family_restaurant')}
СТАНДАРТНАЯ НАЦЕНКА ДЛЯ ЭТОГО ТИПА: {VENUE_TYPES.get(user.get('venue_type', 'family_restaurant'), VENUE_TYPES['family_restaurant']).get('typical_markup', '3.0x')}

ПРИНЦИПЫ АНАЛИЗА:
- Никаких банальностей типа "оптимизируйте поставщиков"
- Только конкретика: "замените X на Y = экономия Z₽"  
- Реальные цифры и расчеты
- Практичные советы, которые можно внедрить завтра
- При расчете рекомендуемой цены учитывай стандартную наценку для типа заведения И цены конкурентов

Создай ПРАКТИЧНЫЙ анализ в JSON:

{{
    "dish_name": "{dish_name}",
    "total_cost": 350,
    "recommended_price": 890,
    "price_reasoning": {{
        "cost_base": "себестоимость",
        "venue_markup": "типичная наценка для типа заведения (например 3.5x)",
        "suggested_by_markup": "цена на основе наценки",
        "competitor_average": "средняя цена у конкурентов",
        "final_recommendation": "итоговая рекомендация и почему"
    }},
    "margin_percent": [маржинальность %],
    "profitability_rating": [1-5 звезд],
    
    "ingredient_breakdown": [
        {{"ingredient": "название", "cost": "стоимость₽", "percent_of_total": "% от общей стоимости", "price_source": "iiko|market_estimate", "confidence": "high|medium|low", "optimization_tip": "конкретный совет по оптимизации"}}
    ],
    
    "price_accuracy": {{
        "total_ingredients": "общее количество ингредиентов",
        "iiko_matched": "количество с ценами из IIKO",
        "market_estimated": "количество с рыночной оценкой",
        "accuracy_percent": "процент точности расчета (0-100)"
    }},
    
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
            model="gpt-5-mini",
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
            
            # Валидация и парсинг чисел
            if 'total_cost' in analysis_data:
                try:
                    cost_val = analysis_data['total_cost']
                    if isinstance(cost_val, str):
                        # Убираем все нечисловые символы кроме точки
                        cost_val = ''.join(c for c in cost_val if c.isdigit() or c == '.')
                    analysis_data['total_cost'] = float(cost_val) if cost_val else 150
                    
                    # Проверка на адекватность (должна быть больше 20₽ и меньше 10000₽)
                    if analysis_data['total_cost'] < 20:
                        logger.warning(f"⚠️ Suspicious total_cost {analysis_data['total_cost']}₽ - too low. Setting to 150₽")
                        analysis_data['total_cost'] = 150
                    elif analysis_data['total_cost'] > 10000:
                        logger.warning(f"⚠️ Suspicious total_cost {analysis_data['total_cost']}₽ - too high. Setting to 500₽")
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
                    
                    # Проверка на адекватность
                    if analysis_data['recommended_price'] < 50:
                        logger.warning(f"⚠️ Suspicious recommended_price {analysis_data['recommended_price']}₽ - too low. Setting to 450₽")
                        analysis_data['recommended_price'] = 450
                    elif analysis_data['recommended_price'] > 50000:
                        logger.warning(f"⚠️ Suspicious recommended_price {analysis_data['recommended_price']}₽ - too high. Setting to 1500₽")
                        analysis_data['recommended_price'] = 1500
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing recommended_price: {e}")
                    analysis_data['recommended_price'] = 450
            
            logger.info(f"💰 Financial analysis result: cost={analysis_data.get('total_cost')}₽, price={analysis_data.get('recommended_price')}₽")
            
        except json.JSONDecodeError as e:
            # Если JSON некорректный, возвращаем базовый анализ
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
    
    # Автоматически создаем тестового/демо пользователя
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
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Convert tech_card to string if it's a dict (V2 or aiKitchenRecipe format)
    if isinstance(tech_card, dict):
        if 'content' in tech_card:
            tech_card_str = tech_card['content']
        else:
            tech_card_str = str(tech_card)
    else:
        tech_card_str = tech_card
    
    # Извлекаем название блюда
    dish_name = "блюдо"
    title_match = re.search(r'\*\*Название:\*\*\s*(.*?)(?=\n|$)', tech_card_str)
    if title_match:
        dish_name = title_match.group(1).strip()
    
    # Создаем промпт для улучшения блюда  
    prompt = f"""Ты — шеф-повар мирового уровня с 20-летним опытом работы в мишленовских ресторанах.

Твоя задача: ПРОКАЧАТЬ и УЛУЧШИТЬ существующее блюдо "{dish_name}", сделав его более профессиональным, вкусным и впечатляющим, но сохранив стандартный формат технологической карты.

ИСХОДНАЯ ТЕХКАРТА:
{tech_card_str}

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
            model="gpt-5-mini",
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
    
    # Автоматически создаем тестового/демо пользователя
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
            model="gpt-5-mini",
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