"""
iikoCloud API Client for restaurant management integration
Provides READ-ONLY access to organization nomenclature and price information
"""

import os
import logging
import asyncio
import time
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime, timedelta
from functools import wraps

from pyiikocloudapi import IikoTransport
from pyiikocloudapi.models import BaseOrganizationsModel, BaseNomenclatureModel
from requests.exceptions import RequestException, Timeout, ConnectionError
import traceback
import requests

# Configure logging
logger = logging.getLogger(__name__)

class IikoAPIError(Exception):
    """Custom exception for iikoCloud API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, correlation_id: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.correlation_id = correlation_id
        super().__init__(self.message)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff_multiplier: float = 2.0):
    """
    Decorator for implementing exponential backoff retry logic for API operations.
    Essential for handling transient failures in restaurant management systems.
    """
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except (RequestException, Timeout, ConnectionError) as e:
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
            
            raise IikoAPIError(f"Operation failed after {max_retries + 1} attempts: {str(last_exception)}")
        
        return sync_wrapper
    return decorator

class IikoClient:
    """
    Enhanced iikoCloud API client with comprehensive error handling and retry logic
    Provides READ-ONLY access to restaurant management data
    """
    
    def __init__(self, api_login: str, base_url: str = "https://api-ru.iiko.services", 
                 timeout: int = 30, max_retries: int = 3, retry_delay: float = 1.0):
        self.api_login = api_login
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[IikoTransport] = None
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the iikoCloud API client with proper error handling"""
        try:
            self._client = IikoTransport(self.api_login)
            logger.info("iikoCloud API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize iikoCloud API client: {str(e)}")
            raise IikoAPIError(f"Client initialization failed: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_access_token(self) -> Dict[str, Any]:
        """
        Get access token from iikoCloud API with retry logic
        Returns token and expiration information
        """
        try:
            if not self._client:
                self._initialize_client()
            
            logger.info("Fetching access token from iikoCloud API")
            
            # Get organizations call also validates token
            response = self._client.organizations()
            
            if not response:
                raise IikoAPIError("Failed to get access token - invalid response")
            
            # Token is managed internally by pyiikocloudapi
            # We simulate token response for compatibility
            self._token_expires_at = datetime.now() + timedelta(hours=1)
            
            token_info = {
                "access_token": "managed_by_client",
                "expires_at": self._token_expires_at.isoformat(),
                "token_type": "Bearer"
            }
            
            logger.info("Successfully obtained access token")
            return token_info
            
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to get access token: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def list_organizations(self) -> List[Dict[str, Any]]:
        """
        Retrieve organizations with retry logic and error handling.
        Essential for restaurant management system initialization.
        """
        try:
            if not self._client:
                self._initialize_client()
            
            logger.info("Fetching organizations from iikoCloud API")
            response = self._client.organizations()
            
            if not response or not hasattr(response, 'organizations'):
                raise IikoAPIError("Invalid response format from organizations endpoint")
            
            organizations = []
            for org in response.organizations:
                org_data = {
                    "id": str(org.id),
                    "name": org.name,
                    "country": getattr(org, 'country', None),
                    "restaurant_address": getattr(org, 'restaurant_address', None),
                    "timezone": getattr(org, 'timezone', None)
                }
                organizations.append(org_data)
            
            logger.info(f"Successfully retrieved {len(organizations)} organizations")
            return organizations
            
        except Exception as e:
            logger.error(f"Error in list_organizations: {str(e)}")
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch organizations: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def fetch_nomenclature(self, organization_id: str, use_direct_http: bool = True) -> Dict[str, Any]:
        """
        Retrieve nomenclature with comprehensive error handling for restaurant data.
        Implements retry logic for handling temporary service interruptions.
        
        Args:
            organization_id: Organization ID
            use_direct_http: If True, use direct HTTP request to /api/v1/menu (recommended)
        
        Returns:
            Dictionary with products and groups
        """
        try:
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"Fetching nomenclature for organization: {organization_id}, use_direct_http={use_direct_http}")
            
            # Try direct HTTP first (more reliable)
            if use_direct_http:
                try:
                    return self.fetch_nomenclature_direct_http(organization_id)
                except Exception as http_error:
                    logger.warning(f"Direct HTTP request failed: {http_error}, falling back to pyiikocloudapi...")
                    # Fall through to pyiikocloudapi method
            
            # Fallback to pyiikocloudapi library
            if not self._client:
                self._initialize_client()
            
            # Try menu() method first (as per documentation: GET /api/v1/menu)
            response = None
            try:
                if hasattr(self._client, 'menu'):
                    logger.info("Trying menu() method first...")
                    response = self._client.menu([organization_id])
                    logger.info(f"✅ menu() method succeeded")
                else:
                    logger.info("menu() method not available, using nomenclature()...")
                    response = self._client.nomenclature([organization_id])
            except Exception as menu_error:
                logger.warning(f"menu() method failed: {menu_error}, falling back to nomenclature()...")
                response = self._client.nomenclature([organization_id])
            
            if not response:
                raise IikoAPIError("Empty response from nomenclature endpoint")
            
            logger.info(f"Response received: type={type(response)}, hasattr products={hasattr(response, 'products')}, hasattr groups={hasattr(response, 'groups')}")
            
            # Parse products
            products = []
            if hasattr(response, 'products'):
                logger.info(f"Response.products exists: {response.products is not None}, type={type(response.products)}")
                if response.products:
                    logger.info(f"Response.products is iterable, length: {len(response.products) if hasattr(response.products, '__len__') else 'unknown'}")
                    for product in response.products:
                        # Parse size prices
                        size_prices = []
                        if hasattr(product, 'size_prices') and product.size_prices:
                            for size_price in product.size_prices:
                                price_info = {
                                    "size_id": str(getattr(size_price, 'size_id', None)) if getattr(size_price, 'size_id', None) else None,
                                    "price": float(size_price.price.current_price) if hasattr(size_price, 'price') and hasattr(size_price.price, 'current_price') else 0.0
                                }
                                size_prices.append(price_info)
                        
                        product_data = {
                            "id": str(product.id),
                            "name": product.name,
                            "description": getattr(product, 'description', None),
                            "group_id": str(getattr(product, 'group_id', None)) if getattr(product, 'group_id', None) else None,
                            "size_prices": size_prices,
                            "tags": getattr(product, 'tags', []),
                            "is_deleted": getattr(product, 'is_deleted', False)
                        }
                        products.append(product_data)
            
            # Parse groups
            groups = []
            if hasattr(response, 'groups'):
                logger.info(f"Response.groups exists: {response.groups is not None}, type={type(response.groups)}")
                if response.groups:
                    logger.info(f"Response.groups is iterable, length: {len(response.groups) if hasattr(response.groups, '__len__') else 'unknown'}")
                    for group in response.groups:
                        group_data = {
                            "id": str(group.id),
                            "name": group.name,
                            "parent_group": str(getattr(group, 'parent_group', None)) if getattr(group, 'parent_group', None) else None,
                            "is_deleted": getattr(group, 'is_deleted', False)
                        }
                        groups.append(group_data)
            
            nomenclature_data = {
                "products": products,
                "groups": groups,
                "correlation_id": str(getattr(response, 'correlation_id', None)) if getattr(response, 'correlation_id', None) else None,
                "organization_id": organization_id,
                "source": "pyiikocloudapi"
            }
            
            logger.info(f"Successfully retrieved nomenclature: {len(products)} products, {len(groups)} groups")
            return nomenclature_data
            
        except Exception as e:
            logger.error(f"Error in fetch_nomenclature: {str(e)}")
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch nomenclature: {str(e)}")
    
    def _get_access_token_direct(self) -> str:
        """
        Get access token via direct HTTP request to Cloud API.
        Returns token string for use in Authorization header.
        """
        try:
            # Cloud API v1 endpoint for access token
            token_url = f"{self.base_url}/api/1/access_token"
            
            response = requests.post(
                token_url,
                json={"apiLogin": self.api_login},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            token = token_data.get("token")
            if not token:
                raise IikoAPIError("Token not found in response")
            
            logger.info("✅ Access token obtained via direct HTTP request")
            return token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get access token via HTTP: {e}")
            raise IikoAPIError(f"Failed to get access token: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_sales_report(self, organization_id: str, date_from: str, date_to: str, group_by: str = "DAY") -> Dict[str, Any]:
        """
        Get sales report from iikoCloud API via direct HTTP request.
        
        Args:
            organization_id: Organization ID
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            group_by: Grouping period (HOUR, DAY, WEEK, MONTH)
        
        Returns:
            Dictionary with sales report data
        """
        try:
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"📊 Fetching sales report via direct HTTP: org={organization_id}, from={date_from}, to={date_to}, groupBy={group_by}")
            
            # Get access token
            token = self._get_access_token_direct()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Try different possible endpoints for sales reports
            possible_endpoints = [
                f"{self.base_url}/api/v1/reports/sales",
                f"{self.base_url}/api/1/reports/sales",
                f"{self.base_url}/cloud/api/v1/reports/sales"
            ]
            
            params = {
                "organizationId": organization_id,
                "dateFrom": date_from,
                "dateTo": date_to,
                "groupBy": group_by
            }
            
            last_error = None
            for endpoint in possible_endpoints:
                try:
                    logger.info(f"Trying endpoint: {endpoint}")
                    response = requests.get(
                        endpoint,
                        headers=headers,
                        params=params,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        report_data = response.json()
                        logger.info(f"✅ Sales report received from {endpoint}")
                        return report_data
                    elif response.status_code == 404:
                        logger.warning(f"Endpoint {endpoint} not found (404), trying next...")
                        continue
                    else:
                        logger.warning(f"Endpoint {endpoint} returned {response.status_code}: {response.text[:200]}")
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        continue
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request to {endpoint} failed: {e}")
                    last_error = str(e)
                    continue
            
            # If all endpoints failed, try using orders endpoint as alternative
            logger.info("All reports endpoints failed, trying orders endpoint as alternative...")
            try:
                orders_endpoint = f"{self.base_url}/api/1/orders"
                orders_params = {
                    "organizationId": organization_id,
                    "dateFrom": date_from,
                    "dateTo": date_to
                }
                
                response = requests.get(
                    orders_endpoint,
                    headers=headers,
                    params=orders_params,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    orders_data = response.json()
                    logger.info(f"✅ Orders data received, calculating sales from orders...")
                    
                    # Calculate sales from orders
                    total_revenue = 0.0
                    total_checks = 0
                    orders = orders_data.get("orders", []) if isinstance(orders_data, dict) else orders_data if isinstance(orders_data, list) else []
                    
                    for order in orders:
                        if isinstance(order, dict):
                            total_revenue += float(order.get("sum", 0) or 0)
                            total_checks += 1
                    
                    avg_check = total_revenue / total_checks if total_checks > 0 else 0.0
                    
                    return {
                        "totalRevenue": total_revenue,
                        "totalChecks": total_checks,
                        "averageCheck": avg_check,
                        "data": [],
                        "source": "orders_endpoint",
                        "message": "Данные рассчитаны на основе заказов"
                    }
            except Exception as e:
                logger.warning(f"Orders endpoint also failed: {e}")
            
            # Final fallback
            raise IikoAPIError(f"Failed to get sales report from all endpoints. Last error: {last_error}")
            
        except Exception as e:
            logger.error(f"Error in get_sales_report: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch sales report: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def fetch_nomenclature_direct_http(self, organization_id: str, include_archived: bool = False) -> Dict[str, Any]:
        """
        Fetch nomenclature via direct HTTP request to /api/v1/menu endpoint.
        This is more reliable than using pyiikocloudapi library.
        
        Args:
            organization_id: Organization ID
            include_archived: Include archived items
        
        Returns:
            Dictionary with products and groups
        """
        try:
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"📋 Fetching menu/nomenclature via direct HTTP: org={organization_id}, includeArchived={include_archived}")
            
            # Get access token
            token = self._get_access_token_direct()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Try different possible endpoints for menu
            possible_endpoints = [
                f"{self.base_url}/api/v1/menu",
                f"{self.base_url}/api/1/menu",
                f"{self.base_url}/cloud/api/v1/menu"
            ]
            
            params = {
                "organizationId": organization_id,
                "includeArchived": str(include_archived).lower()
            }
            
            last_error = None
            for endpoint in possible_endpoints:
                try:
                    logger.info(f"Trying menu endpoint: {endpoint}")
                    response = requests.get(
                        endpoint,
                        headers=headers,
                        params=params,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        menu_data = response.json()
                        logger.info(f"✅ Menu/nomenclature received from {endpoint}")
                        
                        # Parse response structure
                        products = menu_data.get("products", []) if isinstance(menu_data, dict) else []
                        groups = menu_data.get("groups", []) if isinstance(menu_data, dict) else []
                        
                        # If response is a list, it might be products directly
                        if isinstance(menu_data, list):
                            products = menu_data
                            groups = []
                        
                        logger.info(f"📊 Parsed: {len(products)} products, {len(groups)} groups")
                        
                        return {
                            "products": products,
                            "groups": groups,
                            "organization_id": organization_id,
                            "source": "direct_http"
                        }
                    elif response.status_code == 401 or response.status_code == 403:
                        # Проверяем, есть ли сообщение о правах доступа
                        try:
                            error_data = response.json()
                            error_desc = error_data.get("errorDescription", "")
                            if "not allowed" in error_desc.lower() or "right" in error_desc.lower():
                                logger.warning(f"⚠️ API key does not have permission for {endpoint}: {error_desc}")
                                # Это нормально - не все API ключи имеют права на меню
                                # Продолжаем пробовать другие endpoints, но не считаем это критической ошибкой
                                last_error = f"HTTP {response.status_code}: Permission denied - {error_desc}"
                                continue
                        except:
                            pass
                        logger.warning(f"Endpoint {endpoint} returned {response.status_code}: {response.text[:200]}")
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        continue
                    elif response.status_code == 404:
                        logger.warning(f"Endpoint {endpoint} not found (404), trying next...")
                        continue
                    else:
                        logger.warning(f"Endpoint {endpoint} returned {response.status_code}: {response.text[:200]}")
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        continue
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request to {endpoint} failed: {e}")
                    last_error = str(e)
                    continue
            
            # Если все endpoints вернули 401/403 с "not allowed" - это нормально, просто нет прав
            if "Permission denied" in last_error or "not allowed" in last_error.lower():
                logger.info(f"ℹ️ API key does not have permission for menu endpoint. This is normal - not all API keys have menu access.")
                # Возвращаем пустую номенклатуру вместо ошибки
                return {
                    "products": [],
                    "groups": [],
                    "organization_id": organization_id,
                    "source": "direct_http",
                    "message": "API key does not have permission for menu endpoint. Use RMS Server for nomenclature."
                }
            
            raise IikoAPIError(f"Failed to get menu from all endpoints. Last error: {last_error}")
            
        except Exception as e:
            logger.error(f"Error in fetch_nomenclature_direct_http: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch menu via direct HTTP: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_orders(self, organization_id: str, date_from: str, date_to: str, statuses: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get orders from iikoCloud API.
        
        Args:
            organization_id: Organization ID
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            statuses: Optional list of order statuses to filter
        
        Returns:
            Dictionary with orders data
        """
        try:
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"📦 Fetching orders: org={organization_id}, from={date_from}, to={date_to}")
            
            token = self._get_access_token_direct()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            endpoint = f"{self.base_url}/api/v1/orders"
            params = {
                "organizationId": organization_id,
                "dateFrom": date_from,
                "dateTo": date_to
            }
            
            if statuses:
                params["statuses"] = ",".join(statuses)
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            orders_data = response.json()
            orders = orders_data.get("orders", []) if isinstance(orders_data, dict) else orders_data if isinstance(orders_data, list) else []
            
            logger.info(f"✅ Received {len(orders)} orders")
            
            return {
                "orders": orders,
                "count": len(orders),
                "organization_id": organization_id,
                "date_from": date_from,
                "date_to": date_to
            }
            
        except Exception as e:
            logger.error(f"Error in get_orders: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch orders: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_stock_report(self, organization_id: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get stock report from iikoCloud API.
        
        Args:
            organization_id: Organization ID
            date: Report date (YYYY-MM-DD), defaults to today
        
        Returns:
            Dictionary with stock report data
        """
        try:
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"📦 Fetching stock report: org={organization_id}, date={date}")
            
            token = self._get_access_token_direct()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            endpoint = f"{self.base_url}/api/v1/stock/report"
            params = {
                "organizationId": organization_id,
                "date": date
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            stock_data = response.json()
            logger.info(f"✅ Stock report received")
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error in get_stock_report: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch stock report: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_purchases_report(self, organization_id: str, date_from: str, date_to: str, supplier_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get purchases report from iikoCloud API.
        
        Args:
            organization_id: Organization ID
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            supplier_id: Optional supplier ID to filter
        
        Returns:
            Dictionary with purchases report data
        """
        try:
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"🛒 Fetching purchases report: org={organization_id}, from={date_from}, to={date_to}")
            
            token = self._get_access_token_direct()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            endpoint = f"{self.base_url}/api/v1/reports/purchases"
            params = {
                "organizationId": organization_id,
                "dateFrom": date_from,
                "dateTo": date_to
            }
            
            if supplier_id:
                params["supplierId"] = supplier_id
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            purchases_data = response.json()
            logger.info(f"✅ Purchases report received")
            
            return purchases_data
            
        except Exception as e:
            logger.error(f"Error in get_purchases_report: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch purchases report: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_employees(self, organization_id: str) -> Dict[str, Any]:
        """
        Get employees list from iikoCloud API.
        
        Args:
            organization_id: Organization ID
        
        Returns:
            Dictionary with employees data
        """
        try:
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"👥 Fetching employees: org={organization_id}")
            
            # Пробуем сначала с токеном
            token = self._get_access_token_direct()
            logger.debug(f"🔑 Token obtained: {token[:20]}... (truncated)")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            endpoint = f"{self.base_url}/api/v1/employees"
            params = {
                "organizationId": organization_id
            }
            
            logger.info(f"📡 Requesting employees from: {endpoint} with org_id: {organization_id}")
            response = requests.get(endpoint, headers=headers, params=params, timeout=self.timeout)
            
            # Логируем статус ответа
            logger.info(f"📡 Employees API response status: {response.status_code}")
            
            # Обрабатываем ошибки авторизации
            if response.status_code == 401:
                error_detail = response.text
                logger.error(f"❌ 401 Unauthorized with token. Response: {error_detail}")
                
                # Пробуем использовать сам API ключ вместо токена (как в документации)
                logger.info(f"🔄 Trying with API key directly instead of token...")
                headers_api_key = {
                    "Authorization": f"Bearer {self.api_login}",
                    "Content-Type": "application/json"
                }
                response = requests.get(endpoint, headers=headers_api_key, params=params, timeout=self.timeout)
                logger.info(f"📡 Employees API response status with API key: {response.status_code}")
                
                if response.status_code == 401:
                    # Если и с API ключом не работает, значит нет прав
                    error_detail = response.text
                    logger.error(f"❌ 401 Unauthorized even with API key. Response: {error_detail}")
                    raise IikoAPIError(
                        "API ключ не имеет прав на получение данных о сотрудниках. "
                        "Проверьте настройки прав доступа в iikoWeb для endpoint 'api/v1/employees'. "
                        "Убедитесь, что в настройках API ключа включено право 'Employees' или 'Сотрудники'.",
                        status_code=401
                    )
            
            if response.status_code == 404:
                logger.warning(f"⚠️ Employees endpoint not found (404). Trying alternative endpoint...")
                # Пробуем альтернативный endpoint
                endpoint_alt = f"{self.base_url}/api/1/employees"
                response = requests.get(endpoint_alt, headers=headers, params=params, timeout=self.timeout)
                logger.info(f"📡 Alternative endpoint response status: {response.status_code}")
                
                if response.status_code == 401:
                    error_detail = response.text
                    logger.error(f"❌ 401 Unauthorized on alternative endpoint. Response: {error_detail}")
                    raise IikoAPIError(
                        "API ключ не имеет прав на получение данных о сотрудниках. "
                        "Проверьте настройки прав доступа в iikoWeb.",
                        status_code=401
                    )
            
            response.raise_for_status()
            
            employees_data = response.json()
            logger.debug(f"📦 Raw employees response: {type(employees_data)}, keys: {employees_data.keys() if isinstance(employees_data, dict) else 'N/A (list)'}")
            
            # Обрабатываем разные форматы ответа
            if isinstance(employees_data, dict):
                employees = employees_data.get("employees", employees_data.get("items", employees_data.get("data", [])))
            elif isinstance(employees_data, list):
                employees = employees_data
            else:
                employees = []
            
            logger.info(f"✅ Received {len(employees)} employees")
            
            return {
                "employees": employees,
                "count": len(employees),
                "organization_id": organization_id
            }
            
        except Exception as e:
            logger.error(f"Error in get_employees: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch employees: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_employee_attendances(self, employee_id: str, date_from: str, date_to: str) -> Dict[str, Any]:
        """
        Get employee attendances from iikoCloud API.
        
        Args:
            employee_id: Employee ID
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with attendances data
        """
        try:
            if not employee_id:
                raise IikoAPIError("Employee ID cannot be empty")
            
            logger.info(f"⏰ Fetching attendances: employee={employee_id}, from={date_from}, to={date_to}")
            
            token = self._get_access_token_direct()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            endpoint = f"{self.base_url}/api/v1/employees/{employee_id}/attendances"
            params = {
                "dateFrom": date_from,
                "dateTo": date_to
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            attendances_data = response.json()
            attendances = attendances_data.get("attendances", []) if isinstance(attendances_data, dict) else attendances_data if isinstance(attendances_data, list) else []
            
            logger.info(f"✅ Received {len(attendances)} attendances")
            
            return {
                "attendances": attendances,
                "count": len(attendances),
                "employee_id": employee_id,
                "date_from": date_from,
                "date_to": date_to
            }
            
        except Exception as e:
            logger.error(f"Error in get_employee_attendances: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch attendances: {str(e)}")
    
    # ============ BI & ANALYTICS METHODS ============
    
    def _calculate_date_range(self, period_type: str) -> tuple[str, str]:
        """
        Calculate date_from and date_to based on period_type
        
        Args:
            period_type: Period type (TODAY, YESTERDAY, CURRENT_WEEK, LAST_WEEK, CURRENT_MONTH, LAST_MONTH)
        
        Returns:
            Tuple of (date_from, date_to) in YYYY-MM-DD format
        """
        today = datetime.now()
        
        if period_type == "TODAY":
            date_from = today.strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        elif period_type == "YESTERDAY":
            yesterday = today - timedelta(days=1)
            date_from = yesterday.strftime("%Y-%m-%d")
            date_to = yesterday.strftime("%Y-%m-%d")
        elif period_type == "CURRENT_WEEK":
            # Начало недели (понедельник)
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            date_from = week_start.strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        elif period_type == "LAST_WEEK":
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            last_week_start = week_start - timedelta(days=7)
            last_week_end = week_start - timedelta(days=1)
            date_from = last_week_start.strftime("%Y-%m-%d")
            date_to = last_week_end.strftime("%Y-%m-%d")
        elif period_type == "CURRENT_MONTH":
            date_from = today.replace(day=1).strftime("%Y-%m-%d")
            date_to = today.strftime("%Y-%m-%d")
        elif period_type == "LAST_MONTH":
            first_day_current_month = today.replace(day=1)
            last_day_last_month = first_day_current_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            date_from = first_day_last_month.strftime("%Y-%m-%d")
            date_to = last_day_last_month.strftime("%Y-%m-%d")
        else:
            # Default to LAST_MONTH
            first_day_current_month = today.replace(day=1)
            last_day_last_month = first_day_current_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            date_from = first_day_last_month.strftime("%Y-%m-%d")
            date_to = last_day_last_month.strftime("%Y-%m-%d")
        
        return date_from, date_to
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_revenue_by_period(
        self,
        organization_id: str,
        period_type: str = "LAST_MONTH",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get revenue report by period using Cloud API
        
        Args:
            organization_id: Organization ID
            period_type: Period type (TODAY, YESTERDAY, CURRENT_WEEK, LAST_WEEK, CURRENT_MONTH, LAST_MONTH)
            date_from: Start date (YYYY-MM-DD), optional if period_type is set
            date_to: End date (YYYY-MM-DD), optional if period_type is set
        
        Returns:
            Dictionary with revenue data grouped by day
        """
        try:
            if not date_from or not date_to:
                date_from, date_to = self._calculate_date_range(period_type)
            
            # Используем sales report с группировкой по дням
            sales_report = self.get_sales_report(organization_id, date_from, date_to, group_by="DAY")
            
            # Обрабатываем структуру ответа
            # Cloud API может возвращать данные в разных форматах
            revenue_data = []
            total_revenue = 0.0
            
            if isinstance(sales_report, dict):
                # Если есть готовые данные по дням
                if "items" in sales_report:
                    for item in sales_report["items"]:
                        date = item.get("date") or item.get("period")
                        revenue = float(item.get("revenue", 0) or item.get("sum", 0) or item.get("total", 0))
                        revenue_data.append({
                            "date": date,
                            "revenue": revenue
                        })
                        total_revenue += revenue
                elif "report" in sales_report and isinstance(sales_report["report"], list):
                    for item in sales_report["report"]:
                        date = item.get("date") or item.get("period")
                        revenue = float(item.get("revenue", 0) or item.get("sum", 0) or item.get("total", 0))
                        revenue_data.append({
                            "date": date,
                            "revenue": revenue
                        })
                        total_revenue += revenue
                elif "totalRevenue" in sales_report:
                    # Если есть только общая сумма
                    total_revenue = float(sales_report.get("totalRevenue", 0))
            
            return {
                "period_type": period_type,
                "date_from": date_from,
                "date_to": date_to,
                "data": revenue_data,
                "total_revenue": total_revenue,
                "source": "cloud_api"
            }
            
        except Exception as e:
            logger.error(f"Error in get_revenue_by_period: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            raise IikoAPIError(f"Failed to get revenue by period: {str(e)}")
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff_multiplier=2.0)
    def get_dish_statistics(
        self,
        organization_id: str,
        period_type: str = "LAST_MONTH",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Get top dishes statistics from Cloud API using orders
        
        Args:
            organization_id: Organization ID
            period_type: Period type (TODAY, YESTERDAY, CURRENT_WEEK, LAST_WEEK, CURRENT_MONTH, LAST_MONTH)
            date_from: Start date (YYYY-MM-DD), optional if period_type is set
            date_to: End date (YYYY-MM-DD), optional if period_type is set
            top_n: Number of top dishes to return
        
        Returns:
            Dictionary with dish statistics
        """
        try:
            if not date_from or not date_to:
                date_from, date_to = self._calculate_date_range(period_type)
            
            # Получаем заказы за период
            orders_data = self.get_orders(organization_id, date_from, date_to)
            orders = orders_data.get("orders", [])
            
            # Агрегируем данные по блюдам
            dish_stats = {}  # dish_name -> {amount: float, revenue: float, count: int}
            
            for order in orders:
                if not isinstance(order, dict):
                    continue
                
                # Обрабатываем позиции заказа
                items = order.get("items", []) or order.get("orderItems", []) or []
                
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    
                    dish_name = item.get("name") or item.get("productName") or item.get("dishName") or "Без названия"
                    
                    # Получаем количество и сумму
                    amount = float(item.get("amount", 0) or item.get("quantity", 0) or item.get("count", 0) or 1)
                    price = float(item.get("price", 0) or item.get("sum", 0) or item.get("totalPrice", 0) or 0)
                    revenue = amount * price
                    
                    # Если есть отдельное поле с суммой
                    if "sum" in item or "totalPrice" in item or "total" in item:
                        revenue = float(item.get("sum") or item.get("totalPrice") or item.get("total") or 0)
                    
                    if dish_name not in dish_stats:
                        dish_stats[dish_name] = {
                            "DishName": dish_name,
                            "DishAmountInt": 0.0,
                            "DishSumInt": 0.0,
                            "count": 0
                        }
                    
                    dish_stats[dish_name]["DishAmountInt"] += amount
                    dish_stats[dish_name]["DishSumInt"] += revenue
                    dish_stats[dish_name]["count"] += 1
            
            # Сортируем по выручке и берем топ-N
            sorted_dishes = sorted(
                dish_stats.values(),
                key=lambda x: x["DishSumInt"],
                reverse=True
            )[:top_n]
            
            # Рассчитываем общую выручку
            total_revenue = sum(dish["DishSumInt"] for dish in dish_stats.values())
            
            return {
                "data": sorted_dishes,
                "total_revenue": total_revenue,
                "total_dishes": len(dish_stats),
                "top_n": top_n,
                "period_type": period_type,
                "date_from": date_from,
                "date_to": date_to,
                "source": "cloud_api_orders"
            }
            
        except Exception as e:
            logger.error(f"Error in get_dish_statistics: {str(e)}", exc_info=True)
            if isinstance(e, IikoAPIError):
                raise
            raise IikoAPIError(f"Failed to get dish statistics: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check to verify API connectivity and authentication.
        Essential for monitoring restaurant management system integration status.
        """
        try:
            start_time = time.time()
            organizations = self.list_organizations()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "organizations_count": len(organizations),
                "api_login": self.api_login[:8] + "..." if len(self.api_login) > 8 else "***",
                "base_url": self.base_url
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_login": self.api_login[:8] + "..." if len(self.api_login) > 8 else "***",
                "base_url": self.base_url
            }

# Global client instance - initialized on first use
_iiko_client: Optional[IikoClient] = None

def get_iiko_client() -> IikoClient:
    """Get or create global IikoClient instance"""
    global _iiko_client
    
    if _iiko_client is None:
        # Ensure environment variables are loaded
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Try to load .env file from backend directory
        backend_dir = Path(__file__).parent.parent.parent
        env_file = backend_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
        
        api_login = os.getenv('IIKO_API_LOGIN')
        if not api_login:
            raise IikoAPIError("IIKO_API_LOGIN environment variable not set")
        
        base_url = os.getenv('IIKO_BASE_URL', 'https://api-ru.iiko.services')
        timeout = int(os.getenv('IIKO_TIMEOUT', '30'))
        max_retries = int(os.getenv('IIKO_RETRY_ATTEMPTS', '3'))
        retry_delay = float(os.getenv('IIKO_RETRY_DELAY', '1.0'))
        
        _iiko_client = IikoClient(
            api_login=api_login,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
    
    return _iiko_client