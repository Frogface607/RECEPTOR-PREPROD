"""
API endpoints for iiko RMS integration
Provides direct access to iiko RMS server for nomenclature and operations
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from datetime import datetime

from ..integrations.iiko_rms_service import get_iiko_rms_service, IikoRmsAPIError
from ..integrations.iiko_rms_client import get_iiko_rms_client
from ..integrations.iiko_xlsx_parser import IikoXlsxParser, IikoXlsxParseError  # IK-04/01: XLSX Parser
from ..techcards_v2.schemas import TechCardV2

logger = logging.getLogger(__name__)

# Router for iiko RMS API endpoints
router = APIRouter(prefix="/api/v1/iiko/rms", tags=["iiko RMS Integration"])

# Request/Response models
class ConnectRmsRequest(BaseModel):
    host: str = Field(description="iiko RMS server host")
    login: str = Field(description="RMS login")
    password: str = Field(description="RMS password")
    user_id: Optional[str] = Field(None, description="User ID for connection association")

class ConnectRmsResponse(BaseModel):
    status: str = Field(description="Connection status")
    host: str = Field(description="Connected host")
    organizations: List[Dict[str, Any]] = Field(description="Available organizations")
    session_expires_at: str = Field(description="Session expiration timestamp")

class SelectRmsOrganizationRequest(BaseModel):
    organization_id: str = Field(description="Organization ID to select")
    user_id: Optional[str] = Field(None, description="User ID for connection association")

class SelectRmsOrganizationResponse(BaseModel):
    status: str = Field(description="Selection status")
    organization: Dict[str, Any] = Field(description="Selected organization details")

class SyncRmsNomenclatureRequest(BaseModel):
    force: bool = Field(default=False, description="Force sync even if already running")

class SyncRmsNomenclatureResponse(BaseModel):
    status: str = Field(description="Sync status")
    sync_id: str = Field(description="Sync operation ID")
    stats: Optional[Dict[str, int]] = Field(None, description="Sync statistics")

# IK-03: Price sync request/response models
class SyncRmsPricesRequest(BaseModel):
    organization_id: str = Field(default="default", description="Organization ID for price sync")
    force: bool = Field(default=False, description="Force sync even if recently synced")

class SyncRmsPricesResponse(BaseModel):
    status: str = Field(description="Sync status")
    organization_id: str = Field(description="Organization ID")
    items_processed: int = Field(description="Number of price items processed")
    items_created: int = Field(description="Number of new price records created")
    items_updated: int = Field(description="Number of price records updated")
    sync_timestamp: str = Field(description="Sync completion timestamp")
    message: str = Field(description="Sync result message")

class RmsProductSearchResponse(BaseModel):
    sku_id: str = Field(description="Product SKU ID")
    name: str = Field(description="Product name")
    article: Optional[str] = Field(None, description="Product article")
    unit: str = Field(description="Product unit")
    price_per_unit: Optional[float] = Field(None, description="Price per unit")
    currency: str = Field(description="Price currency")
    asOf: str = Field(description="Sync date")
    match_score: float = Field(description="Match score (0-1)")
    group_name: Optional[str] = Field(None, description="Product group name")
    source: str = Field(description="Data source")
    product_type: str = Field(description="Product type")
    active: bool = Field(description="Product active status")

class RmsConnectionStatusResponse(BaseModel):
    status: str = Field(description="Connection status")
    host: Optional[str] = Field(None, description="Connected host")
    login: Optional[str] = Field(None, description="Login (masked)")
    organization_id: Optional[str] = Field(None, description="Selected organization ID")
    organization_name: Optional[str] = Field(None, description="Selected organization name")
    last_connection: Optional[datetime] = Field(None, description="Last connection time")
    session_expires_at: Optional[datetime] = Field(None, description="Session expiration")

@router.post("/connect", response_model=ConnectRmsResponse)
async def connect_to_rms(request: ConnectRmsRequest):
    """
    Connect to iiko RMS server and retrieve available organizations
    This endpoint establishes direct connection to RMS server
    """
    try:
        logger.info(f"Connecting to iiko RMS: {request.host} with login: {request.login}")
        
        service = get_iiko_rms_service()
        result = service.connect_rms(
            host=request.host,
            login=request.login,
            password=request.password,
            user_id=request.user_id
        )
        
        return ConnectRmsResponse(
            status=result["status"],
            host=result["host"],
            organizations=result["organizations"],
            session_expires_at=result["session_expires_at"]
        )
        
    except IikoRmsAPIError as e:
        logger.error(f"iiko RMS API error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error connecting to iiko RMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/select-org", response_model=SelectRmsOrganizationResponse)
async def select_rms_organization(request: SelectRmsOrganizationRequest):
    """
    Select organization for RMS operations
    Updates connection record with selected organization
    """
    try:
        logger.info(f"Selecting RMS organization {request.organization_id} for user: {request.user_id}")
        
        service = get_iiko_rms_service()
        result = service.select_rms_organization(
            organization_id=request.organization_id,
            user_id=request.user_id
        )
        
        return SelectRmsOrganizationResponse(
            status=result["status"],
            organization=result["organization"]
        )
        
    except IikoRmsAPIError as e:
        logger.error(f"iiko RMS API error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error selecting RMS organization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/sync/nomenclature", response_model=SyncRmsNomenclatureResponse)
async def sync_rms_nomenclature(
    organization_id: str = Query(description="Organization ID to sync"),
    request: SyncRmsNomenclatureRequest = SyncRmsNomenclatureRequest(),
    background_tasks: BackgroundTasks = None
):
    """
    Synchronize nomenclature from iiko RMS server
    Updates products and groups in database, generates auto-mappings
    """
    try:
        logger.info(f"Starting RMS nomenclature sync for organization: {organization_id}")
        
        service = get_iiko_rms_service()
        
        # Run sync synchronously for now
        # In production, consider running in background for large datasets
        result = service.sync_rms_nomenclature(
            organization_id=organization_id,
            force=request.force
        )
        
        return SyncRmsNomenclatureResponse(
            status=result["status"],
            sync_id=result.get("sync_id", ""),
            stats=result.get("stats")
        )
        
    except IikoRmsAPIError as e:
        logger.error(f"iiko RMS API error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error syncing RMS nomenclature: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/products/search", response_model=List[RmsProductSearchResponse])
async def search_rms_products(
    organization_id: str = Query(description="Organization ID"),
    q: str = Query(description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    user_id: Optional[str] = Query(None, description="User ID for access control")
):
    """
    Search products in RMS organization
    Returns matching products with relevance scores and enhanced fuzzy matching
    CRITICAL: Now requires user_id for data isolation
    """
    try:
        logger.info(f"Searching RMS products in organization {organization_id}: '{q}' for user: {user_id}")
        
        # КРИТИЧЕСКИ ВАЖНО: проверка доступа пользователя к данным RMS
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required for RMS access")
            
        # Проверяем что у пользователя есть активное подключение
        service = get_iiko_rms_service()
        connection_status = service.get_rms_connection_status(user_id=user_id, auto_restore=False)
        
        if connection_status.get("status") != "connected":
            raise HTTPException(status_code=403, detail="Active RMS connection required for product search")
        
        products = service.search_rms_products(
            organization_id=organization_id,
            query=q,
            limit=limit
        )
        
        response = []
        for product in products:
            response.append(RmsProductSearchResponse(
                sku_id=product["sku_id"],
                name=product["name"],
                article=product["article"],
                unit=product["unit"],
                price_per_unit=product["price_per_unit"],
                currency=product["currency"],
                asOf=product["asOf"],
                match_score=product["match_score"],
                group_name=product.get("group_name"),
                source=product["source"],
                product_type=product["product_type"],
                active=product["active"]
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error searching RMS products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/disconnect")
async def disconnect_rms(user_id: Optional[str] = Query(None, description="User ID")):
    """
    Disconnect from iiko RMS and clear stored credentials
    Implements "Забыть подключение" functionality
    """
    try:
        logger.info(f"Disconnecting RMS for user: {user_id}")
        
        service = get_iiko_rms_service()
        result = service.disconnect_rms(user_id=user_id)
        
        return {
            "status": result["status"],
            "connections_cleared": result["connections_cleared"],
            "message": "Connection cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting RMS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

@router.get("/debug/credentials")
async def debug_get_credentials(user_id: Optional[str] = Query(None, description="User ID")):
    """DEBUG: Check if credentials exist in MongoDB"""
    try:
        service = get_iiko_rms_service()
        query = {"user_id": user_id} if user_id else {}
        credentials = list(service.credentials.find(query, {"password": 0}).limit(5))
        
        # Convert ObjectId to string for JSON serialization
        for cred in credentials:
            if "_id" in cred:
                cred["_id"] = str(cred["_id"])
            if "last_connection" in cred and cred["last_connection"]:
                cred["last_connection"] = cred["last_connection"].isoformat()
            if "session_expires_at" in cred and cred["session_expires_at"]:
                cred["session_expires_at"] = cred["session_expires_at"].isoformat()
            if "created_at" in cred and cred["created_at"]:
                cred["created_at"] = cred["created_at"].isoformat()
            if "updated_at" in cred and cred["updated_at"]:
                cred["updated_at"] = cred["updated_at"].isoformat()
        
        return {
            "count": len(credentials),
            "credentials": credentials,
            "user_id_searched": user_id
        }
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore-connection")
async def restore_rms_connection(user_id: Optional[str] = Query(None, description="User ID")):
    """
    Attempt to restore iiko RMS connection using stored credentials
    Used for sticky connection functionality on app startup
    """
    try:
        logger.info(f"🔍 DEBUG ENDPOINT: Attempting to restore RMS connection for user: {user_id}")
        
        service = get_iiko_rms_service()
        result = service.restore_rms_connection(user_id=user_id)
        
        logger.info(f"🔍 DEBUG ENDPOINT: Restore result status: {result.get('status')}")
        logger.info(f"🔍 DEBUG ENDPOINT: Full result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error restoring RMS connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restore connection: {str(e)}")

@router.get("/connection/status", response_model=RmsConnectionStatusResponse)
async def get_rms_connection_status(
    user_id: Optional[str] = Query(None, description="User ID"),
    auto_restore: bool = Query(True, description="Attempt auto-restore if session expired")
):
    """
    Get RMS connection status for user with optional auto-restore
    Returns current connection information and session details
    Supports sticky connection functionality with auto_restore parameter
    """
    try:
        logger.info(f"Getting RMS connection status for user: {user_id}, auto_restore: {auto_restore}")
        
        service = get_iiko_rms_service()
        status = service.get_rms_connection_status(user_id=user_id, auto_restore=auto_restore)
        
        return RmsConnectionStatusResponse(
            status=status["status"],
            host=status.get("host"),
            login=status.get("login"),
            organization_id=status.get("organization_id"),
            organization_name=status.get("organization_name"),
            last_connection=status.get("last_connection"),
            session_expires_at=status.get("session_expires_at")
        )
        
    except Exception as e:
        logger.error(f"Error getting RMS connection status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# IK-03: Price synchronization endpoint
@router.post("/sync/prices", response_model=SyncRmsPricesResponse)
async def sync_rms_prices(
    request: SyncRmsPricesRequest = SyncRmsPricesRequest(),
    background_tasks: BackgroundTasks = None
):
    """
    IK-03: Synchronize pricing data from iiko RMS
    Idempotent operation that fetches purchase prices and VAT rates
    """
    try:
        logger.info(f"Starting RMS price synchronization for organization: {request.organization_id}")
        
        service = get_iiko_rms_service()
        
        # Check if sync is needed (unless forced)
        if not request.force:
            # Could add logic to check last sync time and skip if recent
            pass
        
        # Perform synchronization
        result = service.sync_prices(organization_id=request.organization_id)
        
        if result["status"] == "success":
            logger.info(f"✅ RMS price sync completed successfully")
            return SyncRmsPricesResponse(
                status=result["status"],
                organization_id=result["organization_id"],
                items_processed=result["items_processed"],
                items_created=result["items_created"],
                items_updated=result["items_updated"],
                sync_timestamp=result["sync_timestamp"],
                message=result["message"]
            )
        elif result["status"] == "no_data":
            return SyncRmsPricesResponse(
                status="no_data",
                organization_id=request.organization_id,
                items_processed=0,
                items_created=0,
                items_updated=0,
                sync_timestamp=datetime.now().isoformat(),
                message="No pricing data available from iiko RMS"
            )
        else:
            # Error case
            raise HTTPException(
                status_code=500, 
                detail=f"Price sync failed: {result.get('error', 'Unknown error')}"
            )
        
    except Exception as e:
        logger.error(f"Error during RMS price synchronization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Price sync failed: {str(e)}")

@router.get("/sync/status")
async def get_rms_sync_status(
    organization_id: str = Query(description="Organization ID"),
    user_id: Optional[str] = Query(None, description="User ID for access control")
):
    """
    Get RMS synchronization status for organization
    Returns information about latest sync operation including detailed statistics
    Supports both authenticated and anonymous access with fallback logic
    """
    try:
        logger.info(f"Getting RMS sync status for organization: {organization_id}, user: {user_id}")
        
        service = get_iiko_rms_service()
        
        # КРИТИЧЕСКИ ВАЖНО: полная изоляция для demo пользователей
        if user_id == 'demo_user' or (user_id and user_id.startswith('demo')):
            # Демо пользователи НИКОГДА не должны видеть реальные данные
            return {
                "status": "demo_mode", 
                "message": "Demo users cannot access sync data",
                "demo": True
            }
        
        # Проверка доступа: если user_id указан и это не 'anonymous', проверяем подключение пользователя
        if user_id and user_id != 'anonymous':
            connection_status = service.get_rms_connection_status(user_id=user_id, auto_restore=False)
            if connection_status.get("status") != "connected":
                raise HTTPException(status_code=403, detail="Active RMS connection required for sync status access")
        else:
            # Для anonymous доступа - строгая проверка что есть активные подключения только для этого user_id
            if not user_id:
                raise HTTPException(status_code=400, detail="user_id is required for data isolation")
        
        status = service.get_rms_sync_status(organization_id, user_id=user_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting RMS sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def rms_health_check():
    """
    Health check endpoint for iiko RMS integration
    Tests connectivity using stored credentials and returns detailed status
    """
    try:
        # Get RMS client using environment credentials
        rms_client = get_iiko_rms_client()
        health_status = rms_client.health_check()
        
        return {
            "service": "iiko RMS Integration",
            "status": health_status["status"],
            "timestamp": datetime.now().isoformat(),
            "details": health_status
        }
        
    except Exception as e:
        logger.error(f"RMS health check failed: {str(e)}")
        return {
            "service": "iiko RMS Integration", 
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }