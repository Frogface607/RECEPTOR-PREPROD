"""
API endpoints for iikoCloud integration
Provides READ-ONLY access to organization nomenclature and price information
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from ..integrations.iiko_service import get_iiko_service, IikoAPIError

logger = logging.getLogger(__name__)

# Router for iikoCloud API endpoints
router = APIRouter(prefix="/api/iiko", tags=["iikoCloud Integration"])

# Request/Response models
class ConnectRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="User ID for token association")

class ConnectResponse(BaseModel):
    status: str = Field(description="Connection status")
    organizations: List[Dict[str, Any]] = Field(description="Available organizations")
    token_expires_at: str = Field(description="Token expiration timestamp")

class SelectOrganizationRequest(BaseModel):
    organization_id: str = Field(description="Organization ID to select")
    user_id: Optional[str] = Field(None, description="User ID for token association")

class SelectOrganizationResponse(BaseModel):
    status: str = Field(description="Selection status")
    organization: Dict[str, Any] = Field(description="Selected organization details")

class SyncNomenclatureRequest(BaseModel):
    force: bool = Field(default=False, description="Force sync even if already running")

class SyncNomenclatureResponse(BaseModel):
    status: str = Field(description="Sync status")
    sync_id: str = Field(description="Sync operation ID")
    stats: Optional[Dict[str, int]] = Field(None, description="Sync statistics")

class OrganizationResponse(BaseModel):
    id: str = Field(description="Organization ID")
    name: str = Field(description="Organization name")
    country: Optional[str] = Field(None, description="Organization country")
    restaurant_address: Optional[str] = Field(None, description="Restaurant address")
    timezone: Optional[str] = Field(None, description="Organization timezone")

class ProductSearchResponse(BaseModel):
    sku_id: str = Field(description="Product SKU ID")
    name: str = Field(description="Product name")
    unit: str = Field(description="Product unit")
    price_per_unit: float = Field(description="Price per unit")
    currency: str = Field(description="Price currency")
    asOf: str = Field(description="Price date")
    match_score: float = Field(description="Match score (0-1)")
    article: Optional[str] = Field(None, description="Product article")
    group_name: Optional[str] = Field(None, description="Product group name")

@router.post("/connect", response_model=ConnectResponse)
async def connect_to_iiko(request: ConnectRequest):
    """
    Connect to iikoCloud API and retrieve available organizations
    This endpoint establishes connection and caches authentication token
    """
    try:
        logger.info(f"Connecting to iikoCloud for user: {request.user_id}")
        
        service = get_iiko_service()
        result = service.connect_organization(user_id=request.user_id)
        
        return ConnectResponse(
            status=result["status"],
            organizations=result["organizations"],
            token_expires_at=result["token_expires_at"]
        )
        
    except IikoAPIError as e:
        logger.error(f"iikoCloud API error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error connecting to iikoCloud: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/organizations", response_model=List[OrganizationResponse])
async def get_organizations(user_id: Optional[str] = Query(None, description="User ID")):
    """
    Get list of available organizations
    Returns cached organizations or fetches from API if needed
    """
    try:
        logger.info(f"Getting organizations for user: {user_id}")
        
        service = get_iiko_service()
        organizations = service.get_organizations(user_id=user_id)
        
        response = []
        for org in organizations:
            response.append(OrganizationResponse(
                id=org["id"],
                name=org["name"],
                country=org.get("country"),
                restaurant_address=org.get("restaurant_address"),
                timezone=org.get("timezone")
            ))
        
        return response
        
    except IikoAPIError as e:
        logger.error(f"iikoCloud API error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/select-org", response_model=SelectOrganizationResponse)
async def select_organization(request: SelectOrganizationRequest):
    """
    Select organization for further operations
    Updates token record with selected organization information
    """
    try:
        logger.info(f"Selecting organization {request.organization_id} for user: {request.user_id}")
        
        service = get_iiko_service()
        result = service.select_organization(
            organization_id=request.organization_id,
            user_id=request.user_id
        )
        
        return SelectOrganizationResponse(
            status=result["status"],
            organization=result["organization"]
        )
        
    except IikoAPIError as e:
        logger.error(f"iikoCloud API error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error selecting organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/sync/nomenclature", response_model=SyncNomenclatureResponse)
async def sync_nomenclature(
    organization_id: str = Query(description="Organization ID to sync"),
    request: SyncNomenclatureRequest = SyncNomenclatureRequest(),
    background_tasks: BackgroundTasks = None
):
    """
    Synchronize nomenclature from iikoCloud
    Updates products and groups in database
    """
    try:
        logger.info(f"Starting nomenclature sync for organization: {organization_id}")
        
        service = get_iiko_service()
        
        # For now, run sync synchronously
        # In production, you might want to run this in background
        result = service.sync_nomenclature(
            organization_id=organization_id,
            force=request.force
        )
        
        return SyncNomenclatureResponse(
            status=result["status"],
            sync_id=result.get("sync_id", ""),
            stats=result.get("stats")
        )
        
    except IikoAPIError as e:
        logger.error(f"iikoCloud API error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error syncing nomenclature: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/sync/status")
async def get_sync_status(organization_id: str = Query(description="Organization ID")):
    """
    Get synchronization status for organization
    Returns information about latest sync operation
    """
    try:
        logger.info(f"Getting sync status for organization: {organization_id}")
        
        service = get_iiko_service()
        status = service.get_sync_status(organization_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/products/search", response_model=List[ProductSearchResponse])
async def search_products(
    organization_id: str = Query(description="Organization ID"),
    q: str = Query(description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results")
):
    """
    Search products in organization
    Returns matching products with relevance scores
    """
    try:
        logger.info(f"Searching products in organization {organization_id}: '{q}'")
        
        service = get_iiko_service()
        products = service.search_products(
            organization_id=organization_id,
            query=q,
            limit=limit
        )
        
        response = []
        for product in products:
            response.append(ProductSearchResponse(
                sku_id=product["sku_id"],
                name=product["name"],
                unit=product["unit"],
                price_per_unit=product["price_per_unit"],
                currency=product["currency"],
                asOf=product["asOf"],
                match_score=product["match_score"],
                article=product.get("article"),
                group_name=product.get("group_name")
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for iikoCloud integration
    Verifies API connectivity and returns status information
    """
    try:
        service = get_iiko_service()
        health_status = service.iiko_client.health_check()
        
        return {
            "service": "iikoCloud Integration",
            "status": health_status["status"],
            "timestamp": datetime.now().isoformat(),
            "details": health_status
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "service": "iikoCloud Integration",
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }