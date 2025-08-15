"""
iiko RMS Client for direct server integration
Provides direct access to iiko RMS server nomenclature and data
"""

import os
import logging
import time
import hashlib
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
import traceback

# Configure logging
logger = logging.getLogger(__name__)

class IikoRmsAPIError(Exception):
    """Custom exception for iiko RMS API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff_multiplier: float = 2.0):
    """Decorator for implementing exponential backoff retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except (requests.exceptions.RequestException, requests.exceptions.Timeout, 
                       requests.exceptions.ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff_multiplier ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed. Last error: {str(e)}")
                        
                except Exception as e:
                    logger.error(f"Non-recoverable error in {func.__name__}: {str(e)}\n{traceback.format_exc()}")
                    raise
            
            raise IikoRmsAPIError(f"Operation failed after {max_retries + 1} attempts: {str(last_exception)}")
        
        return wrapper
    return decorator

class IikoRmsClient:
    """
    iiko RMS (Restaurant Management System) API client
    Provides direct access to iiko server for nomenclature and operational data
    """
    
    def __init__(self, host: str, login: str, password: str, timeout: int = 30):
        self.host = host.rstrip('/')
        self.login = login
        self.password = password
        self.timeout = timeout
        self.session_key = None
        self.session_expires_at = None
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # Common headers
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': 'Receptor-iiko-RMS-Client/1.0'
        })
    
    def _make_url(self, path: str) -> str:
        """Construct full URL for API endpoint"""
        return f"https://{self.host}{path}"
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def authenticate(self) -> str:
        """
        Authenticate with iiko RMS server and get session key
        Uses SHA1 hash authentication method
        """
        try:
            logger.info(f"Authenticating with iiko RMS server: {self.host}")
            
            # Step 1: Create SHA1 hash of password
            password_hash = hashlib.sha1(self.password.encode('utf-8')).hexdigest()
            
            # Step 2: Request session key
            auth_url = self._make_url("/resto/api/auth")
            auth_params = {
                "login": self.login,
                "pass": password_hash
            }
            
            # Use simple headers for authentication (RMS server doesn't accept JSON headers)
            auth_headers = {
                'User-Agent': 'Receptor-iiko-RMS-Client/1.0'
            }
            response = requests.get(auth_url, params=auth_params, headers=auth_headers, timeout=self.timeout)
            
            if response.status_code == 200:
                session_key = response.text.strip()
                if session_key and len(session_key) > 10:  # Valid session key
                    self.session_key = session_key
                    self.session_expires_at = datetime.now() + timedelta(hours=2)
                    
                    logger.info(f"✅ iiko RMS authentication successful")
                    logger.info(f"Session key: {session_key[:20]}...")
                    return session_key
                else:
                    raise IikoRmsAPIError(f"Invalid session key received: {session_key}")
            else:
                raise IikoRmsAPIError(
                    f"Authentication failed: HTTP {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise IikoRmsAPIError(f"Failed to authenticate: {str(e)}")
    
    def _get_session_key(self) -> str:
        """Get valid session key, authenticate if needed"""
        if (not self.session_key or 
            not self.session_expires_at or 
            datetime.now() >= self.session_expires_at - timedelta(minutes=5)):
            
            return self.authenticate()
        
        return self.session_key
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_organizations(self) -> List[Dict[str, Any]]:
        """Get list of organizations from iiko RMS"""
        try:
            session_key = self._get_session_key()
            
            # Try multiple possible endpoints for organizations
            possible_endpoints = [
                "/resto/api/v2/entities/organizations/list",
                "/resto/api/corporation/organizations", 
                "/resto/api/organizations",
                "/resto/api/v2/corporation"
            ]
            
            params = {"key": session_key}
            
            for endpoint in possible_endpoints:
                try:
                    url = self._make_url(endpoint)
                    response = self.session.get(url, params=params, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        data = response.json() if response.content else {}
                        
                        # Parse organizations from response
                        organizations = []
                        if isinstance(data, list):
                            for org in data:
                                organizations.append({
                                    'id': org.get('id'),
                                    'name': org.get('name'),
                                    'address': org.get('address', ''),
                                    'active': org.get('active', True)
                                })
                        elif isinstance(data, dict):
                            if 'organizations' in data:
                                for org in data['organizations']:
                                    organizations.append({
                                        'id': org.get('id'),
                                        'name': org.get('name'), 
                                        'address': org.get('address', ''),
                                        'active': org.get('active', True)
                                    })
                            else:
                                # Single organization
                                organizations.append({
                                    'id': data.get('id'),
                                    'name': data.get('name'),
                                    'address': data.get('address', ''),
                                    'active': data.get('active', True)
                                })
                        
                        if organizations:
                            logger.info(f"Retrieved {len(organizations)} organizations from {endpoint}")
                            return organizations
                            
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {str(e)}")
                    continue
            
            # If no organizations endpoint works, create default organization
            logger.info("No organizations found, creating default organization")
            return [{
                'id': 'default',
                'name': 'Edison Craft Bar',
                'address': 'Default Location',
                'active': True
            }]
            
        except Exception as e:
            logger.error(f"Error getting organizations: {str(e)}")
            raise IikoRmsAPIError(f"Failed to get organizations: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0) 
    def fetch_nomenclature(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch nomenclature (products) from iiko RMS server
        Returns structured data with products, groups, and units
        """
        try:
            session_key = self._get_session_key()
            
            logger.info(f"Fetching nomenclature from iiko RMS")
            
            # Try multiple possible endpoints for nomenclature
            possible_endpoints = [
                "/resto/api/v2/entities/products/list",
                "/resto/api/products/list",
                "/resto/api/menu/list",
                "/resto/api/nomenclature/list"
            ]
            
            params = {"key": session_key}
            if organization_id and organization_id != 'default':
                params["organization"] = organization_id
            
            products = []
            groups = []
            
            for endpoint in possible_endpoints:
                try:
                    url = self._make_url(endpoint)
                    response = self.session.get(url, params=params, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        data = response.json() if response.content else {}
                        
                        logger.info(f"✅ Successfully fetched data from {endpoint}")
                        
                        # Parse products from response
                        if isinstance(data, list):
                            raw_products = data
                        elif isinstance(data, dict):
                            raw_products = data.get('items', data.get('products', data.get('nomenclature', [])))
                        else:
                            raw_products = []
                        
                        # Process products
                        for item in raw_products:
                            product = self._normalize_product(item)
                            if product:
                                products.append(product)
                        
                        if products:
                            logger.info(f"Processed {len(products)} products from iiko RMS")
                            break
                            
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {str(e)}")
                    continue
            
            # Try to get product groups
            try:
                groups = self._fetch_product_groups(session_key, organization_id)
            except Exception as e:
                logger.warning(f"Failed to fetch product groups: {str(e)}")
                groups = []
            
            result = {
                "products": products,
                "groups": groups,
                "organization_id": organization_id or "default",
                "fetched_at": datetime.now().isoformat(),
                "total_products": len(products),
                "total_groups": len(groups)
            }
            
            logger.info(f"Nomenclature fetch completed: {len(products)} products, {len(groups)} groups")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching nomenclature: {str(e)}")
            raise IikoRmsAPIError(f"Failed to fetch nomenclature: {str(e)}")
    
    def _fetch_product_groups(self, session_key: str, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch product groups/categories"""
        possible_endpoints = [
            "/resto/api/v2/entities/product_categories/list",
            "/resto/api/product_categories/list", 
            "/resto/api/categories/list",
            "/resto/api/groups/list"
        ]
        
        params = {"key": session_key}
        if organization_id and organization_id != 'default':
            params["organization"] = organization_id
        
        for endpoint in possible_endpoints:
            try:
                url = self._make_url(endpoint)
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json() if response.content else {}
                    
                    if isinstance(data, list):
                        raw_groups = data
                    elif isinstance(data, dict):
                        raw_groups = data.get('items', data.get('categories', data.get('groups', [])))
                    else:
                        continue
                    
                    groups = []
                    for item in raw_groups:
                        group = {
                            "id": str(item.get('id', '')),
                            "name": item.get('name', ''),
                            "parent_id": str(item.get('parent', item.get('parentId', ''))),
                            "active": item.get('active', True)
                        }
                        if group["name"]:
                            groups.append(group)
                    
                    if groups:
                        logger.info(f"Retrieved {len(groups)} groups from {endpoint}")
                        return groups
                        
            except Exception as e:
                logger.debug(f"Groups endpoint {endpoint} failed: {str(e)}")
                continue
        
        return []
    
    def _normalize_product(self, raw_product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize product data from iiko RMS format"""
        try:
            # Extract basic product information
            product_id = raw_product.get('id', '')
            name = raw_product.get('name', '')
            
            if not product_id or not name:
                return None
            
            # Extract additional fields
            article = raw_product.get('article', raw_product.get('code', ''))
            group_id = raw_product.get('category', raw_product.get('group', raw_product.get('groupId', '')))
            unit = raw_product.get('unit', raw_product.get('measureUnit', 'pcs'))
            
            # Price information
            price = None
            if 'price' in raw_product:
                price = float(raw_product['price'])
            elif 'cost' in raw_product:
                price = float(raw_product['cost'])
            
            # Normalize unit to standard format
            unit_mapping = {
                'kg': 'g', 'кг': 'g', 'kilogram': 'g',
                'g': 'g', 'г': 'g', 'gram': 'g',
                'l': 'ml', 'л': 'ml', 'liter': 'ml', 'litre': 'ml',
                'ml': 'ml', 'мл': 'ml', 'milliliter': 'ml',
                'шт': 'pcs', 'pcs': 'pcs', 'piece': 'pcs', 'pieces': 'pcs'
            }
            
            normalized_unit = unit_mapping.get(unit.lower(), 'pcs')
            
            # Calculate unit coefficient for price normalization
            unit_coefficient = 1.0
            if unit.lower() in ['kg', 'кг', 'kilogram']:
                unit_coefficient = 1000.0  # kg to g
            elif unit.lower() in ['l', 'л', 'liter', 'litre']:
                unit_coefficient = 1000.0  # l to ml
            
            # Calculate price per normalized unit
            price_per_unit = None
            if price:
                price_per_unit = price / unit_coefficient if unit_coefficient > 1 else price
            
            product = {
                "id": str(product_id),
                "name": name,
                "article": article,
                "group_id": str(group_id) if group_id else None,
                "unit": normalized_unit,
                "unit_coefficient": unit_coefficient,
                "price": price,
                "price_per_unit": price_per_unit,
                "active": raw_product.get('active', True),
                "description": raw_product.get('description', ''),
                "barcode": raw_product.get('barcode', ''),
                "type": raw_product.get('type', 'product')
            }
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to normalize product {raw_product.get('name', 'unknown')}: {str(e)}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check for iiko RMS connectivity"""
        try:
            start_time = time.time()
            
            # Test authentication
            session_key = self._get_session_key()
            auth_time = time.time() - start_time
            
            # Test organizations access
            organizations = self.get_organizations()
            total_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "host": self.host,
                "login": self.login[:3] + "***",
                "session_valid": bool(session_key),
                "organizations_count": len(organizations),
                "auth_time": auth_time,
                "total_time": total_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "host": self.host,
                "login": self.login[:3] + "***",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global RMS client instance
_iiko_rms_client: Optional[IikoRmsClient] = None

def get_iiko_rms_client() -> IikoRmsClient:
    """Get or create global IikoRmsClient instance"""
    global _iiko_rms_client
    
    if _iiko_rms_client is None:
        # Get credentials from environment
        host = os.getenv('IIKO_RMS_HOST', 'edison-bar.iiko.it')
        login = os.getenv('IIKO_RMS_LOGIN', 'Sergey') 
        password = os.getenv('IIKO_RMS_PASSWORD', 'metkamfetamin')
        timeout = int(os.getenv('IIKO_RMS_TIMEOUT', '30'))
        
        _iiko_rms_client = IikoRmsClient(
            host=host,
            login=login,
            password=password,
            timeout=timeout
        )
    
    return _iiko_rms_client