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
    def fetch_nomenclature(self, organization_id: str) -> Dict[str, Any]:
        """
        Retrieve nomenclature with comprehensive error handling for restaurant data.
        Implements retry logic for handling temporary service interruptions.
        Tries menu() first, then nomenclature().
        """
        try:
            if not self._client:
                self._initialize_client()
            
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"Fetching nomenclature for organization: {organization_id}")
            
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
                "organization_id": organization_id
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
    def get_sales_report(self, organization_id: str, date_from: str, date_to: str) -> Dict[str, Any]:
        """
        Get sales/revenue report from iikoCloud API.
        Note: This is a placeholder - iikoCloud API may not have direct sales reports endpoint.
        For sales data, you typically need to use orders endpoint or RMS Server API.
        """
        try:
            if not self._client:
                self._initialize_client()
            
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"Fetching sales report for organization: {organization_id}, from {date_from} to {date_to}")
            
            # iikoCloud API typically doesn't have direct sales reports
            # We would need to use orders endpoint or RMS Server API
            # This is a placeholder for future implementation
            raise IikoAPIError("Sales reports are not available via iikoCloud API. Use RMS Server API or orders endpoint instead.")
            
        except Exception as e:
            logger.error(f"Error in get_sales_report: {str(e)}")
            if isinstance(e, IikoAPIError):
                raise
            else:
                raise IikoAPIError(f"Failed to fetch sales report: {str(e)}")
    
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