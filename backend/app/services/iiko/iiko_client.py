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
        """
        try:
            if not self._client:
                self._initialize_client()
            
            if not organization_id:
                raise IikoAPIError("Organization ID cannot be empty")
            
            logger.info(f"Fetching nomenclature for organization: {organization_id}")
            response = self._client.nomenclature([organization_id])
            
            if not response:
                raise IikoAPIError("Empty response from nomenclature endpoint")
            
            # Parse products
            products = []
            if hasattr(response, 'products') and response.products:
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
            if hasattr(response, 'groups') and response.groups:
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