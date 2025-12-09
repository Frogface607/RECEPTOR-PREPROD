"""
API routes for iiko integration (both Cloud API and RMS Server)
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.services.iiko.iiko_client import IikoClient, IikoAPIError
from app.services.iiko.iiko_rms_service import get_iiko_rms_service, IikoRmsService
from app.services.iiko.iiko_rms_client import IikoRmsAPIError
from app.core.database import db

logger = logging.getLogger(__name__)
router = APIRouter()


# ============ REQUEST/RESPONSE MODELS ============

class IikoCloudCredentials(BaseModel):
    """Credentials for iikoCloud API"""
    api_key: str = Field(..., min_length=10, description="iikoCloud API key")
    user_id: str = Field(..., description="User ID for credential storage")


class IikoRmsCredentials(BaseModel):
    """Credentials for iiko RMS Server"""
    host: str = Field(..., description="RMS server host (e.g., https://my-server.iiko.it)")
    login: str = Field(..., description="RMS login username")
    password: str = Field(..., description="RMS password")
    user_id: str = Field(..., description="User ID for credential storage")


class OrganizationSelect(BaseModel):
    """Organization selection request"""
    organization_id: str = Field(..., description="Organization ID to select")
    user_id: str = Field(..., description="User ID")


class SyncRequest(BaseModel):
    """Sync request"""
    organization_id: str = Field(default="default", description="Organization ID")
    force: bool = Field(default=False, description="Force sync even if already running")


class ConnectionStatusRequest(BaseModel):
    """Connection status request"""
    user_id: str = Field(..., description="User ID to check status for")


# ============ iiko CLOUD API ENDPOINTS ============

@router.post("/cloud/connect")
async def connect_iiko_cloud(credentials: IikoCloudCredentials):
    """
    Connect to iikoCloud API and test the connection.
    Stores credentials for future use.
    """
    try:
        logger.info(f"Attempting iikoCloud connection for user: {credentials.user_id}")
        
        # Test connection by creating client and fetching organizations
        client = IikoClient(api_login=credentials.api_key)
        health = client.health_check()
        
        if health["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection test failed: {health.get('error', 'Unknown error')}"
            )
        
        # Get organizations
        organizations = client.list_organizations()
        
        # Store credentials in MongoDB
        collection = db.get_collection("iiko_cloud_credentials")
        await collection.update_one(
            {"user_id": credentials.user_id},
            {
                "$set": {
                    "user_id": credentials.user_id,
                    "api_key": credentials.api_key,  # In production, encrypt this!
                    "status": "connected",
                    "last_connection": datetime.utcnow(),
                    "organizations_count": len(organizations),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        logger.info(f"✅ iikoCloud connected successfully for user: {credentials.user_id}")
        
        return {
            "status": "connected",
            "organizations": organizations,
            "organizations_count": len(organizations),
            "response_time": health["response_time"],
            "message": "Успешно подключено к iikoCloud API"
        }
        
    except IikoAPIError as e:
        logger.error(f"iikoCloud API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка подключения к iikoCloud: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error connecting to iikoCloud: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка: {str(e)}"
        )


@router.get("/cloud/status/{user_id}")
async def get_iiko_cloud_status(user_id: str):
    """Get iikoCloud connection status for user"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        credentials = await collection.find_one({"user_id": user_id})
        
        if not credentials:
            return {"status": "not_connected", "message": "iikoCloud не подключен"}
        
        # Mask API key for security
        masked_key = credentials["api_key"][:8] + "..." if credentials.get("api_key") else None
        
        return {
            "status": credentials.get("status", "unknown"),
            "api_key_masked": masked_key,
            "organizations_count": credentials.get("organizations_count", 0),
            "last_connection": credentials.get("last_connection"),
            "message": "iikoCloud подключен" if credentials.get("status") == "connected" else "Требуется переподключение"
        }
        
    except Exception as e:
        logger.error(f"Error getting iikoCloud status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/cloud/disconnect/{user_id}")
async def disconnect_iiko_cloud(user_id: str):
    """Disconnect iikoCloud and remove stored credentials"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        result = await collection.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            logger.info(f"iikoCloud disconnected for user: {user_id}")
            return {"status": "disconnected", "message": "iikoCloud отключен"}
        else:
            return {"status": "not_found", "message": "Подключение не найдено"}
            
    except Exception as e:
        logger.error(f"Error disconnecting iikoCloud: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============ iiko RMS (SERVER) ENDPOINTS ============

@router.post("/rms/connect")
async def connect_iiko_rms(credentials: IikoRmsCredentials):
    """
    Connect to iiko RMS Server and test the connection.
    """
    try:
        logger.info(f"Attempting iiko RMS connection for user: {credentials.user_id}")
        
        # Use the existing RMS service
        rms_service = get_iiko_rms_service()
        result = rms_service.connect_rms(
            host=credentials.host,
            login=credentials.login,
            password=credentials.password,
            user_id=credentials.user_id
        )
        
        logger.info(f"✅ iiko RMS connected successfully for user: {credentials.user_id}")
        
        return {
            "status": "connected",
            "host": credentials.host,
            "organizations": result.get("organizations", []),
            "session_expires_at": result.get("session_expires_at"),
            "message": "Успешно подключено к iiko RMS"
        }
        
    except IikoRmsAPIError as e:
        logger.error(f"iiko RMS API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка подключения к iiko RMS: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error connecting to iiko RMS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка: {str(e)}"
        )


@router.get("/rms/status/{user_id}")
async def get_iiko_rms_status(user_id: str):
    """Get iiko RMS connection status for user"""
    try:
        rms_service = get_iiko_rms_service()
        result = rms_service.get_rms_connection_status(user_id=user_id, auto_restore=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting iiko RMS status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/rms/select-organization")
async def select_rms_organization(request: OrganizationSelect):
    """Select an organization for iiko RMS operations"""
    try:
        rms_service = get_iiko_rms_service()
        result = rms_service.select_rms_organization(
            organization_id=request.organization_id,
            user_id=request.user_id
        )
        
        return result
        
    except IikoRmsAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error selecting organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/rms/sync")
async def sync_rms_nomenclature(request: SyncRequest):
    """Synchronize nomenclature from iiko RMS"""
    try:
        rms_service = get_iiko_rms_service()
        result = rms_service.sync_rms_nomenclature(
            organization_id=request.organization_id,
            force=request.force
        )
        
        return result
        
    except IikoRmsAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error syncing RMS nomenclature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rms/sync-status/{organization_id}")
async def get_rms_sync_status(organization_id: str, user_id: Optional[str] = None):
    """Get sync status for organization"""
    try:
        rms_service = get_iiko_rms_service()
        result = rms_service.get_rms_sync_status(
            organization_id=organization_id,
            user_id=user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/rms/disconnect/{user_id}")
async def disconnect_iiko_rms(user_id: str):
    """Disconnect iiko RMS for user"""
    try:
        rms_service = get_iiko_rms_service()
        result = rms_service.disconnect_rms(user_id=user_id)
        
        return result
        
    except IikoRmsAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error disconnecting RMS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============ PRODUCT SEARCH ENDPOINTS ============

@router.get("/products/search")
async def search_products(
    query: str,
    organization_id: str = "default",
    limit: int = 10
):
    """Search products in synced iiko data"""
    try:
        rms_service = get_iiko_rms_service()
        results = rms_service.search_rms_products_enhanced(
            organization_id=organization_id,
            query=query,
            limit=limit
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============ COMBINED STATUS ENDPOINT ============

@router.get("/status/{user_id}")
async def get_all_iiko_status(user_id: str):
    """Get combined status for all iiko integrations"""
    try:
        # Get Cloud status
        collection = db.get_collection("iiko_cloud_credentials")
        cloud_credentials = await collection.find_one({"user_id": user_id})
        
        cloud_status = {
            "connected": cloud_credentials is not None and cloud_credentials.get("status") == "connected",
            "organizations_count": cloud_credentials.get("organizations_count", 0) if cloud_credentials else 0,
            "last_connection": cloud_credentials.get("last_connection") if cloud_credentials else None
        }
        
        # Get RMS status
        rms_service = get_iiko_rms_service()
        rms_result = rms_service.get_rms_connection_status(user_id=user_id, auto_restore=False)
        
        rms_status = {
            "connected": rms_result.get("status") in ["connected", "restored"],
            "host": rms_result.get("host"),
            "organization_name": rms_result.get("organization_name"),
            "last_connection": rms_result.get("last_connection")
        }
        
        return {
            "user_id": user_id,
            "cloud": cloud_status,
            "rms": rms_status,
            "any_connected": cloud_status["connected"] or rms_status["connected"]
        }
        
    except Exception as e:
        logger.error(f"Error getting combined iiko status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

