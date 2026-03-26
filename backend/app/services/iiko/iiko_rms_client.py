"""
iiko RMS Client for direct server integration
Provides direct access to iiko RMS server nomenclature and data
"""

import os
import logging
import time
import hashlib
import threading
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
        self.olap_timeout = timeout * 4  # OLAP-запросы могут быть долгими (120сек по умолчанию)
        self.session_key = None
        self.session_expires_at = None
        self._auth_lock = threading.Lock()  # Защита от race condition при аутентификации
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
            # Mask credentials in logs
            masked_host = self.host
            masked_login = self.login[:3] + "***" if len(self.login) > 3 else "***"
            logger.info(f"Authenticating with iiko RMS server: {masked_host} (login: {masked_login})")
            
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
                    
                    # Mask session key in logs
                    masked_session = session_key[:6] + "***" + session_key[-4:] if len(session_key) > 10 else "***"
                    logger.info(f"✅ iiko RMS authentication successful")
                    logger.info(f"Session key: {masked_session}")
                    return session_key
                else:
                    raise IikoRmsAPIError(f"Invalid session key received")
            elif response.status_code == 401:
                error_msg = response.text.strip() if response.text else "Invalid credentials"
                logger.error(f"Authentication failed (401): {error_msg}")
                raise IikoRmsAPIError(
                    f"Authentication failed: Invalid credentials (401). "
                    f"Please check your login and password in settings."
                )
            elif response.status_code == 403:
                error_msg = response.text.strip() if response.text else "Access denied"
                logger.error(f"Authentication failed (403): {error_msg}")
                logger.error(f"Response body: {response.text[:200] if response.text else 'Empty'}")
                raise IikoRmsAPIError(
                    f"Authentication failed: Access denied (403). "
                    f"Possible reasons: user blocked, insufficient permissions, or account restrictions. "
                    f"Please check your account status in iiko RMS."
                )
            else:
                error_msg = response.text.strip() if response.text else f"HTTP {response.status_code}"
                logger.error(f"Authentication failed ({response.status_code}): {error_msg}")
                raise IikoRmsAPIError(
                    f"Authentication failed: HTTP {response.status_code} - {error_msg}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during authentication: {str(e)}")
            raise IikoRmsAPIError(f"Failed to authenticate: Network error")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise IikoRmsAPIError(f"Failed to authenticate: {str(e)}")
    
    def _get_session_key(self, force_refresh: bool = False) -> str:
        """
        Get valid session key, authenticate if needed.
        Thread-safe: uses lock to prevent concurrent re-authentication.

        Args:
            force_refresh: If True, force re-authentication even if session is valid
        """
        # Fast path: session is valid, no lock needed
        if (not force_refresh and
            self.session_key and
            self.session_expires_at and
            datetime.now() < self.session_expires_at - timedelta(minutes=5)):
            return self.session_key

        # Slow path: need to authenticate, use lock to prevent race condition
        with self._auth_lock:
            # Double-check after acquiring lock (another thread may have already authenticated)
            if (not force_refresh and
                self.session_key and
                self.session_expires_at and
                datetime.now() < self.session_expires_at - timedelta(minutes=5)):
                return self.session_key

            if force_refresh:
                self.session_key = None
                self.session_expires_at = None
                logger.info("Force refreshing RMS session...")

            return self.authenticate()
    
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
                        data = self._safe_json(response)
                        
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
                'name': 'Моё заведение',
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
                        data = self._safe_json(response)
                        
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
    
    def fetch_prices(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """
        IK-03: Fetch pricing data from iiko RMS server
        Returns pricing information with VAT and units
        """
        try:
            # Reuse existing nomenclature fetch logic but focus on pricing
            nomenclature_data = self.fetch_nomenclature(organization_id)
            
            prices = []
            products = nomenclature_data.get('products', [])
            
            logger.info(f"Processing pricing data for {len(products)} products from iiko RMS")
            
            for product in products:
                # Only include products with pricing information
                if product.get('purchase_price') or product.get('price'):
                    price_data = {
                        "skuId": product.get('id'),
                        "name": product.get('name'),
                        "article": product.get('article', ''),
                        "unit": product.get('unit', 'pcs'),
                        "original_unit": product.get('original_unit', product.get('unit', 'pcs')),
                        "price_per_unit": product.get('purchase_price_per_unit') or product.get('price_per_unit'),
                        "currency": product.get('currency', 'RUB'),
                        "vat_pct": product.get('vat_pct', 0.0),
                        "source": "iiko",
                        "active": product.get('active', True)
                    }
                    
                    # Only add if we have a valid price
                    if price_data["price_per_unit"] and price_data["price_per_unit"] > 0:
                        prices.append(price_data)
            
            result = {
                "prices": prices,
                "organization_id": organization_id or "default",
                "fetched_at": datetime.now().isoformat(),
                "total_count": len(prices)
            }
            
            logger.info(f"✅ Successfully processed {len(prices)} price entries from iiko RMS")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch prices from iiko RMS: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise IikoRmsAPIError(f"Price fetch failed: {str(e)}")
    
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
                    data = self._safe_json(response)
                    
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
        """Normalize product data from iiko RMS format with IK-03 pricing support"""
        try:
            # Extract basic product information
            product_id = raw_product.get('id', '')
            name = raw_product.get('name', '')
            
            if not product_id or not name:
                return None
            
            # Extract additional fields - берем НОМЕНКЛАТУРНЫЙ КОД (num), а не код быстрого набора
            article = None
            
            # ПРАВИЛЬНЫЙ приоритет полей для поиска АРТИКУЛА (номенклатурного кода)
            article_fields = [
                'num',                      # ✅ ОСНОВНОЕ поле артикула в iiko Server API
                'article',                  # ✅ Альтернативное название номенклатурного кода  
                'nomenclatureCode',         # ✅ Номенклатурный код
                'productCode',              # ✅ Код продукта
                'itemCode',                 # ✅ Код товара
            ]
            
            for field in article_fields:
                if field in raw_product and raw_product[field]:
                    article_value = str(raw_product[field]).strip()
                    if article_value and article_value != '0':
                        article = article_value
                        if 'свинин' in name.lower() or 'филе' in name.lower():
                            logger.info(f"  Selected ARTICLE from field '{field}': {article_value}")
                        break
            
            # НЕ ИСПОЛЬЗУЕМ ДЛЯ АРТИКУЛА (это коды быстрого набора):
            # - 'code' = код быстрого набора iikoFront  
            # - 'orderItemId' = служебный код
            
            # Сохраняем код быстрого набора отдельно (для справки)
            quick_dial_code = raw_product.get('code', raw_product.get('orderItemId', ''))
            
            if not article:
                # Если артикул не найден, логируем для отладки
                logger.warning(f"No article found for product '{name}', available fields: {list(raw_product.keys())}")
                article = ""
            
            group_id = raw_product.get('category', raw_product.get('group', raw_product.get('groupId', '')))
            unit = raw_product.get('unit', raw_product.get('measureUnit', 'pcs'))
            
            # IK-03: Enhanced price information extraction
            price = None
            purchase_price = None  # IK-03: закупочная цена
            
            # Try multiple fields for price information
            if 'purchasePrice' in raw_product:
                purchase_price = float(raw_product['purchasePrice'])
            elif 'purchase_price' in raw_product:
                purchase_price = float(raw_product['purchase_price'])
            elif 'cost' in raw_product:
                purchase_price = float(raw_product['cost'])
            elif 'price' in raw_product:
                # Fallback to regular price if no purchase price
                purchase_price = float(raw_product['price'])
            
            if 'price' in raw_product:
                price = float(raw_product['price'])
            elif purchase_price:
                price = purchase_price  # Fallback
            
            # IK-03: VAT information extraction
            vat_pct = 0.0  # Default VAT
            if 'vat' in raw_product:
                vat_pct = float(raw_product.get('vat', 0))
            elif 'vatRate' in raw_product:
                vat_pct = float(raw_product.get('vatRate', 0))
            elif 'tax' in raw_product:
                vat_pct = float(raw_product.get('tax', 0))
            elif 'taxRate' in raw_product:
                vat_pct = float(raw_product.get('taxRate', 0))
            
            # IK-03: Try to get VAT from category/group if not on product
            if vat_pct == 0.0 and group_id:
                # This could be enhanced later to fetch group VAT rates
                pass
            
            # Currency extraction (IK-03: expect RUB)
            currency = raw_product.get('currency', 'RUB')
            if currency not in ['RUB', 'руб', 'рублей']:
                currency = 'RUB'  # Force RUB for consistency
            
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
            
            # IK-03: Calculate normalized purchase price per unit
            purchase_price_per_unit = None
            price_per_unit = None
            
            if purchase_price:
                purchase_price_per_unit = purchase_price / unit_coefficient if unit_coefficient > 1 else purchase_price
            
            if price:
                price_per_unit = price / unit_coefficient if unit_coefficient > 1 else price
            
            product = {
                "id": str(product_id),
                "name": name,
                "article": article,  # Номенклатурный код (из 'num')
                "quick_dial_code": quick_dial_code,  # Код быстрого набора (из 'code')
                "group_id": str(group_id) if group_id else None,
                "unit": normalized_unit,
                "original_unit": unit,  # IK-03: keep original for reference
                "unit_coefficient": unit_coefficient,
                # IK-03: Enhanced pricing fields
                "price": price,
                "price_per_unit": price_per_unit,
                "purchase_price": purchase_price,
                "purchase_price_per_unit": purchase_price_per_unit,
                "currency": currency,
                "vat_pct": vat_pct,
                # Basic fields
                "active": raw_product.get('active', True),
                "description": raw_product.get('description', ''),
                "barcode": raw_product.get('barcode', ''),
                "type": raw_product.get('type', 'product')
            }
            
            return product
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse numeric values in product {raw_product.get('name', 'unknown')}: {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"Failed to normalize product {raw_product.get('name', 'unknown')}: {str(e)}")
            return None
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to normalize product {raw_product.get('name', 'unknown')}: {str(e)}")
            return None
    
    def _safe_json(self, response: requests.Response) -> dict:
        """Safely parse JSON response, handle HTML errors gracefully."""
        try:
            return self._safe_json(response)
        except (ValueError, requests.exceptions.JSONDecodeError) as e:
            # iiko sometimes returns HTML error pages instead of JSON
            content_preview = response.text[:200] if response.text else "(empty)"
            logger.error(f"Failed to parse JSON response (HTTP {response.status_code}): {content_preview}")
            raise IikoRmsAPIError(
                f"iiko returned non-JSON response (HTTP {response.status_code}). "
                f"Server may be overloaded or misconfigured.",
                status_code=response.status_code
            )

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
            
            # Mask credentials in response
            masked_login = self.login[:3] + "***" if len(self.login) > 3 else "***"
            
            return {
                "status": "healthy",
                "host": self.host,
                "login": masked_login,
                "session_valid": bool(session_key),
                "organizations_count": len(organizations),
                "auth_time": auth_time,
                "total_time": total_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            masked_login = self.login[:3] + "***" if len(self.login) > 3 else "***"
            return {
                "status": "unhealthy",
                "host": self.host,
                "login": masked_login,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_olap_columns(self, report_type: str = "SALES") -> Dict[str, Any]:
        """
        Получить список доступных полей для OLAP отчета
        
        Args:
            report_type: Тип отчета - "SALES", "TRANSACTIONS", "DELIVERIES"
        
        Returns:
            Словарь с описанием полей отчета
        """
        try:
            session_key = self._get_session_key()
            
            endpoint = "/resto/api/v2/reports/olap/columns"
            url = self._make_url(endpoint)
            params = {
                "key": session_key,
                "reportType": report_type
            }
            
            logger.info(f"Fetching OLAP columns for report type: {report_type}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            columns_data = self._safe_json(response)
            logger.info(f"✅ Successfully fetched OLAP columns for {report_type}")
            
            return {
                "report_type": report_type,
                "columns": columns_data,
                "fetched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching OLAP columns: {str(e)}")
            raise IikoRmsAPIError(f"Failed to get OLAP columns: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_olap_report(
        self,
        report_type: str = "SALES",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        period_type: str = "CUSTOM",
        group_by_row_fields: Optional[List[str]] = None,
        group_by_col_fields: Optional[List[str]] = None,
        aggregate_fields: Optional[List[str]] = None,
        build_summary: bool = True,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получить OLAP отчет из iiko RMS Server
        
        Args:
            report_type: "SALES", "TRANSACTIONS", "DELIVERIES"
            date_from: Дата начала (YYYY-MM-DD или ISO format)
            date_to: Дата окончания (YYYY-MM-DD или ISO format)
            period_type: "CUSTOM", "TODAY", "YESTERDAY", "CURRENT_WEEK", "CURRENT_MONTH", "LAST_MONTH", etc.
            group_by_row_fields: Поля для группировки по строкам (например, ["DishName", "DishGroup"])
            group_by_col_fields: Поля для группировки по столбцам
            aggregate_fields: Поля для агрегации (например, ["DishAmountInt", "DishSumInt"])
            build_summary: Строить ли итоговую строку
            organization_id: ID организации (опционально)
        
        Returns:
            Словарь с данными отчета
        """
        try:
            session_key = self._get_session_key()
            
            # Подготовка дат на основе period_type
            if period_type != "CUSTOM" and not date_from and not date_to:
                # Генерируем даты на основе period_type
                now = datetime.now()
                if period_type == "TODAY":
                    date_from = now.strftime("%Y-%m-%dT00:00:00.000")
                    date_to = now.strftime("%Y-%m-%dT23:59:59.999")
                elif period_type == "YESTERDAY":
                    yesterday = now - timedelta(days=1)
                    date_from = yesterday.strftime("%Y-%m-%dT00:00:00.000")
                    date_to = yesterday.strftime("%Y-%m-%dT23:59:59.999")
                elif period_type == "LAST_MONTH":
                    # Первый день прошлого месяца
                    first_day_last_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
                    # Последний день прошлого месяца
                    last_day_last_month = now.replace(day=1) - timedelta(days=1)
                    date_from = first_day_last_month.strftime("%Y-%m-%dT00:00:00.000")
                    date_to = last_day_last_month.strftime("%Y-%m-%dT23:59:59.999")
                elif period_type == "CURRENT_MONTH":
                    first_day = now.replace(day=1)
                    date_from = first_day.strftime("%Y-%m-%dT00:00:00.000")
                    date_to = now.strftime("%Y-%m-%dT23:59:59.999")
                elif period_type == "LAST_WEEK":
                    # Понедельник прошлой недели
                    days_since_monday = now.weekday()
                    last_monday = now - timedelta(days=days_since_monday + 7)
                    last_sunday = last_monday + timedelta(days=6)
                    date_from = last_monday.strftime("%Y-%m-%dT00:00:00.000")
                    date_to = last_sunday.strftime("%Y-%m-%dT23:59:59.999")
                elif period_type == "CURRENT_WEEK":
                    # Понедельник текущей недели
                    days_since_monday = now.weekday()
                    this_monday = now - timedelta(days=days_since_monday)
                    date_from = this_monday.strftime("%Y-%m-%dT00:00:00.000")
                    date_to = now.strftime("%Y-%m-%dT23:59:59.999")
                else:
                    # По умолчанию - вчерашний день
                    yesterday = now - timedelta(days=1)
                    date_from = yesterday.strftime("%Y-%m-%dT00:00:00.000")
                    date_to = yesterday.strftime("%Y-%m-%dT23:59:59.999")
            elif date_from and date_to:
                # Конвертируем в ISO формат если нужно
                if "T" not in date_from:
                    date_from = f"{date_from}T00:00:00.000"
                if "T" not in date_to:
                    date_to = f"{date_to}T23:59:59.999"
            elif not date_from and period_type == "CUSTOM":
                # По умолчанию для CUSTOM - вчерашний день
                yesterday = datetime.now() - timedelta(days=1)
                date_from = yesterday.strftime("%Y-%m-%dT00:00:00.000")
                date_to = yesterday.strftime("%Y-%m-%dT23:59:59.999")
            
            # Значения по умолчанию для полей
            if not group_by_row_fields:
                if report_type == "SALES":
                    group_by_row_fields = ["DishName"]
                else:
                    group_by_row_fields = []
            
            if not aggregate_fields:
                if report_type == "SALES":
                    aggregate_fields = ["DishAmountInt", "DishSumInt"]
                else:
                    aggregate_fields = []
            
            # Построение фильтров
            filters = {}
            # Обязательный фильтр по дате (требуется с версии iiko 5.5)
            if period_type == "CUSTOM":
                # Для CUSTOM - передаем даты с временем
                if date_from and date_to:
                    filters["OpenDate.Typed"] = {
                        "filterType": "DateRange",
                        "periodType": "CUSTOM",
                        "from": date_from,
                        "to": date_to,
                        "includeLow": True,
                        "includeHigh": True
                    }
            else:
                # Для предопределенных периодов передаем periodType и дату БЕЗ времени
                # Согласно документации (пример для CURRENT_MONTH), нужна дата в формате yyyy-MM-dd
                date_only = None
                if date_from:
                    # Берем только дату без времени (формат yyyy-MM-dd)
                    date_only = date_from.split('T')[0] if 'T' in date_from else date_from
                    # Убираем время если есть
                    if len(date_only) > 10:
                        date_only = date_only[:10]
                
                filter_obj = {
                    "filterType": "DateRange",
                    "periodType": period_type
                }
                # Добавляем from только если есть дата (дата без времени)
                if date_only:
                    filter_obj["from"] = date_only
                
                filters["OpenDate.Typed"] = filter_obj
            
            # Добавляем фильтр по организации если указана
            if organization_id and organization_id != "default":
                filters["Department.Id"] = {
                    "filterType": "IncludeValues",
                    "values": [organization_id]
                }
            
            # Тело запроса
            request_body = {
                "reportType": report_type,
                "buildSummary": build_summary,
                "groupByRowFields": group_by_row_fields,
                "groupByColFields": group_by_col_fields or [],
                "aggregateFields": aggregate_fields,
                "filters": filters
            }
            
            endpoint = "/resto/api/v2/reports/olap"
            url = self._make_url(endpoint)
            params = {"key": session_key}
            
            logger.info(f"Fetching OLAP report: type={report_type}, period={period_type}, from={date_from}, to={date_to}")
            response = self.session.post(
                url,
                params=params,
                json=request_body,
                timeout=self.olap_timeout  # OLAP запросы могут быть долгими (120сек по умолчанию)
            )

            if response.status_code == 400:
                error_data = self._safe_json(response)
                error_msg = error_data.get("message", response.text)
                logger.error(f"OLAP request validation error: {error_msg}")
                raise IikoRmsAPIError(f"Invalid OLAP request: {error_msg}")

            response.raise_for_status()
            report_data = self._safe_json(response)
            
            logger.info(f"✅ Successfully fetched OLAP report: {report_type}")
            
            return {
                "report_type": report_type,
                "data": report_data.get("data", []),
                "summary": report_data.get("summary", []),
                "date_from": date_from,
                "date_to": date_to,
                "period_type": period_type,
                "fetched_at": datetime.now().isoformat(),
                "row_count": len(report_data.get("data", []))
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching OLAP report: {str(e)}")
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.text[:200]
                except:
                    pass
            raise IikoRmsAPIError(f"Network error: {error_detail}")
        except Exception as e:
            logger.error(f"Error fetching OLAP report: {str(e)}", exc_info=True)
            if isinstance(e, IikoRmsAPIError):
                raise
            raise IikoRmsAPIError(f"Failed to get OLAP report: {str(e)}")
    
    def get_sales_report(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        period_type: str = "YESTERDAY",
        group_by: str = "dish",  # "dish", "date", "group"
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получить отчет по продажам через OLAP API (упрощенный интерфейс)
        
        Args:
            date_from: Дата начала (YYYY-MM-DD)
            date_to: Дата окончания (YYYY-MM-DD)
            period_type: Тип периода
            group_by: Группировка - "dish" (по блюдам), "date" (по датам), "group" (по группам)
            organization_id: ID организации
        
        Returns:
            Упрощенный отчет по продажам
        """
        # Настройка группировки
        if group_by == "dish":
            group_by_row_fields = ["DishName", "DishGroup"]
        elif group_by == "date":
            group_by_row_fields = ["OpenDate.Typed"]
        elif group_by == "group":
            group_by_row_fields = ["DishGroup"]
        else:
            group_by_row_fields = ["DishName"]
        
        aggregate_fields = ["DishAmountInt", "DishSumInt", "DiscountSum"]
        
        return self.get_olap_report(
            report_type="SALES",
            date_from=date_from,
            date_to=date_to,
            period_type=period_type,
            group_by_row_fields=group_by_row_fields,
            aggregate_fields=aggregate_fields,
            organization_id=organization_id
        )
    
    def get_revenue_by_period(
        self,
        period_type: str = "LAST_MONTH",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получить выручку по периодам
        
        Args:
            period_type: Тип периода
            organization_id: ID организации
        
        Returns:
            Отчет с выручкой по периодам
        """
        return self.get_olap_report(
            report_type="SALES",
            period_type=period_type,
            group_by_row_fields=["OpenDate.Typed"],
            aggregate_fields=["DishSumInt", "DiscountSum"],
            organization_id=organization_id
        )
    
    def get_dish_statistics(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        period_type: str = "LAST_MONTH",
        top_n: int = 10,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получить статистику по блюдам (топ продаж)
        
        Args:
            date_from: Дата начала
            date_to: Дата окончания
            period_type: Тип периода
            top_n: Количество топ блюд
            organization_id: ID организации
        
        Returns:
            Статистика по блюдам
        """
        report = self.get_olap_report(
            report_type="SALES",
            date_from=date_from,
            date_to=date_to,
            period_type=period_type,
            group_by_row_fields=["DishName", "DishGroup"],
            aggregate_fields=["DishAmountInt", "DishSumInt"],
            organization_id=organization_id
        )
        
        # Сортируем по сумме продаж и берем топ-N
        data = report.get("data", [])
        if data:
            # Сортируем по DishSumInt (сумма продаж)
            sorted_data = sorted(
                data,
                key=lambda x: float(x.get("DishSumInt", 0) or 0),
                reverse=True
            )
            report["data"] = sorted_data[:top_n]
            report["top_n"] = top_n
        
        return report
    
    def get_sales_by_shifts(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        period_type: str = "YESTERDAY",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получить отчет по продажам сгруппированный по кассовым сменам
        
        Args:
            date_from: Дата начала (YYYY-MM-DD)
            date_to: Дата окончания (YYYY-MM-DD)
            period_type: Тип периода
            organization_id: ID организации
        
        Returns:
            Отчет по сменам с выручкой и количеством чеков
        """
        # Пробуем разные варианты полей для группировки по сменам
        # В разных версиях iiko могут быть разные названия полей
        possible_shift_fields = [
            ["SessionOpenDate.Typed", "SessionCloseDate.Typed"],
            ["Session.Id", "SessionOpenDate.Typed"],
            ["CashSessionOpenDate.Typed"],
            ["SessionDate.Typed"]
        ]
        
        # Сначала пытаемся получить список доступных полей
        try:
            columns = self.get_olap_columns(report_type="SALES")
            available_columns = columns.get("columns", {})
            
            # Ищем подходящие поля для смен
            shift_fields = None
            for field_set in possible_shift_fields:
                if all(field in available_columns for field in field_set):
                    shift_fields = field_set
                    break
                # Или хотя бы одно поле из набора
                for field in field_set:
                    if field in available_columns:
                        shift_fields = [field]
                        break
                    if shift_fields:
                        break
            
            # Если не нашли специфичные поля, используем SessionOpenDate или SessionDate
            if not shift_fields:
                # Пробуем найти любое поле со словом Session
                for field_name in available_columns.keys():
                    if "ession" in field_name or "hift" in field_name or "ession" in field_name.lower():
                        shift_fields = [field_name]
                        break
            
            # Если ничего не нашли, используем OpenDate как fallback
            if not shift_fields:
                shift_fields = ["OpenDate.Typed"]
                logger.warning("Session fields not found, using OpenDate.Typed as fallback")
        except Exception as e:
            logger.warning(f"Could not fetch OLAP columns, using default: {str(e)}")
            shift_fields = ["OpenDate.Typed"]
        
        # Получаем отчет с группировкой по сменам
        report = self.get_olap_report(
            report_type="SALES",
            date_from=date_from,
            date_to=date_to,
            period_type=period_type,
            group_by_row_fields=shift_fields,
            aggregate_fields=["DishSumInt", "DishAmountInt", "DiscountSum"],
            organization_id=organization_id
        )
        
        # Добавляем метаданную о том, какие поля использовались
        report["group_by_fields"] = shift_fields
        report["report_subtype"] = "shifts"
        
        return report

# Global RMS client instance
_iiko_rms_client: Optional[IikoRmsClient] = None

def get_iiko_rms_client() -> IikoRmsClient:
    """Get or create global IikoRmsClient instance"""
    global _iiko_rms_client
    
    if _iiko_rms_client is None:
        # Get credentials from environment (no hardcoded defaults)
        host = os.getenv('IIKO_RMS_HOST', '')
        login = os.getenv('IIKO_RMS_LOGIN', '') 
        password = os.getenv('IIKO_RMS_PASSWORD', '')
        timeout = int(os.getenv('IIKO_RMS_TIMEOUT', '30'))
        
        _iiko_rms_client = IikoRmsClient(
            host=host,
            login=login,
            password=password,
            timeout=timeout
        )
    
    return _iiko_rms_client