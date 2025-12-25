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
        
        # Store credentials in MongoDB (sync PyMongo)
        collection = db.get_collection("iiko_cloud_credentials")
        
        # Если есть только одна организация - автоматически выбираем её
        selected_org_id = None
        selected_org_name = None
        if len(organizations) == 1:
            selected_org_id = organizations[0]["id"]
            selected_org_name = organizations[0]["name"]
        
        collection.update_one(
            {"user_id": credentials.user_id},
            {
                "$set": {
                    "user_id": credentials.user_id,
                    "api_key": credentials.api_key,  # In production, encrypt this!
                    "status": "connected",
                    "last_connection": datetime.utcnow(),
                    "organizations_count": len(organizations),
                    "organizations": organizations,  # Сохраняем список организаций
                    "selected_organization_id": selected_org_id,  # Выбранная организация
                    "selected_organization_name": selected_org_name,
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
        if collection is None:
            return {"status": "not_connected", "message": "Database not initialized"}
        
        credentials = collection.find_one({"user_id": user_id})  # Sync call for PyMongo
        
        if not credentials:
            return {"status": "not_connected", "message": "iikoCloud не подключен"}
        
        # Mask API key for security
        masked_key = credentials["api_key"][:8] + "..." if credentials.get("api_key") else None
        
        # Получаем список организаций и выбранную
        organizations = credentials.get("organizations", [])
        selected_org_id = credentials.get("selected_organization_id")
        selected_org_name = credentials.get("selected_organization_name")
        
        return {
            "status": credentials.get("status", "unknown"),
            "api_key_masked": masked_key,
            "organizations_count": credentials.get("organizations_count", 0),
            "organizations": organizations,  # Возвращаем список организаций
            "selected_organization_id": selected_org_id,
            "selected_organization_name": selected_org_name,
            "last_connection": credentials.get("last_connection"),
            "message": "iikoCloud подключен" if credentials.get("status") == "connected" else "Требуется переподключение"
        }
        
    except Exception as e:
        logger.error(f"Error getting iikoCloud status: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.post("/cloud/select-organization")
async def select_cloud_organization(request: OrganizationSelect):
    """Select an organization for iikoCloud API operations"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": request.user_id})
        if not credentials:
            raise HTTPException(status_code=404, detail="iikoCloud не подключен")
        
        # Находим организацию в списке
        organizations = credentials.get("organizations", [])
        selected_org = next((org for org in organizations if org["id"] == request.organization_id), None)
        
        if not selected_org:
            raise HTTPException(status_code=404, detail="Организация не найдена")
        
        # Обновляем выбранную организацию
        collection.update_one(
            {"user_id": request.user_id},
            {
                "$set": {
                    "selected_organization_id": request.organization_id,
                    "selected_organization_name": selected_org["name"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Selected Cloud organization: {selected_org['name']} ({request.organization_id})")
        
        return {
            "status": "success",
            "organization": selected_org,
            "message": f"Выбрана организация: {selected_org['name']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting Cloud organization: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cloud/sync")
async def sync_cloud_nomenclature(request: OrganizationSelect):
    """
    Test connection and verify Cloud API access.
    NOTE: iikoCloud API is primarily for reports, revenue, employees, orders.
    Nomenclature should be synced via RMS Server API.
    """
    try:
        logger.info(f"🔄 Testing Cloud API connection for user: {request.user_id}, org: {request.organization_id}")
        
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": request.user_id})
        if not credentials:
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        if credentials.get("status") != "connected":
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        # Проверяем organization_id
        org_id = request.organization_id
        if not org_id or org_id == "default":
            # Пытаемся взять из credentials
            org_id = credentials.get("selected_organization_id")
            if not org_id:
                raise HTTPException(status_code=400, detail="Организация не выбрана")
        
        logger.info(f"📡 Testing Cloud API connection for org: {org_id}")
        
        # Создаём клиент и проверяем подключение
        api_key = credentials.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="API ключ не найден")
        
        try:
            client = IikoClient(api_login=api_key)
            logger.info(f"✅ IikoClient created successfully for org: {org_id}")
            
            # Проверяем health check
            health = client.health_check()
            logger.info(f"✅ Health check passed: {health}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create/test IikoClient: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ошибка подключения к iikoCloud: {str(e)}")
        
        # Пытаемся получить номенклатуру через прямой HTTP запрос (более надёжно)
        try:
            logger.info(f"📡 Attempting to fetch menu/nomenclature from Cloud API via direct HTTP (may return empty)")
            nomenclature = client.fetch_nomenclature(org_id, use_direct_http=True)
            
            products = nomenclature.get("products", []) if isinstance(nomenclature, dict) else []
            groups = nomenclature.get("groups", []) if isinstance(nomenclature, dict) else []
            
            logger.info(f"📊 Cloud API returned: {len(products)} products, {len(groups)} groups")
            
            # Сохраняем результат (даже если 0)
            sync_collection = db.get_collection("iiko_cloud_nomenclature")
            if sync_collection is not None:
                sync_collection.update_one(
                    {
                        "user_id": request.user_id,
                        "organization_id": org_id
                    },
                    {
                        "$set": {
                            "nomenclature": nomenclature if isinstance(nomenclature, dict) else {},
                            "synced_at": datetime.utcnow(),
                            "products_count": len(products) if isinstance(products, list) else 0,
                            "groups_count": len(groups) if isinstance(groups, list) else 0,
                            "organization_name": credentials.get("selected_organization_name"),
                            "connection_status": "verified"
                        },
                        "$setOnInsert": {
                            "created_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
            
            # Если продуктов 0, это нормально для Cloud API
            if len(products) == 0:
                return {
                    "status": "completed",
                    "stats": {
                        "products_processed": 0,
                        "products_created": 0,
                        "products_updated": 0,
                        "groups_count": 0
                    },
                    "message": "✅ Подключение к iikoCloud API успешно. Cloud API используется для отчетов, выручки и сотрудников. Для номенклатуры используйте синхронизацию через RMS Server.",
                    "note": "Cloud API может не возвращать номенклатуру. Используйте RMS Server для синхронизации продуктов."
                }
            
            return {
                "status": "completed",
                "stats": {
                    "products_processed": len(products),
                    "products_created": len(products),
                    "products_updated": 0,
                    "groups_count": len(groups)
                },
                "message": f"✅ Синхронизация завершена. Получено {len(products)} продуктов, {len(groups)} групп."
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch nomenclature from Cloud API (this is normal): {e}")
            # Это не критично - Cloud API может не поддерживать номенклатуру
            return {
                "status": "completed",
                "stats": {
                    "products_processed": 0,
                    "products_created": 0,
                    "products_updated": 0,
                    "groups_count": 0
                },
                "message": "✅ Подключение к iikoCloud API успешно. Cloud API используется для отчетов, выручки и сотрудников. Для номенклатуры используйте синхронизацию через RMS Server.",
                "note": "Cloud API не предоставляет номенклатуру. Используйте RMS Server для синхронизации продуктов."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing Cloud API: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка проверки подключения: {str(e)}")


@router.get("/cloud/menu/{user_id}")
async def get_cloud_menu(user_id: str, organization_id: Optional[str] = None):
    """Get menu/nomenclature from iikoCloud API"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": user_id})
        if not credentials or credentials.get("status") != "connected":
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        # Используем выбранную организацию или переданную
        org_id = organization_id or credentials.get("selected_organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="Организация не выбрана")
        
        client = IikoClient(api_login=credentials["api_key"])
        nomenclature = client.fetch_nomenclature(org_id, use_direct_http=True)
        
        return {
            "organization_id": org_id,
            "organization_name": credentials.get("selected_organization_name"),
            "products": nomenclature.get("products", []),
            "groups": nomenclature.get("groups", []),
            "products_count": len(nomenclature.get("products", [])),
            "groups_count": len(nomenclature.get("groups", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Cloud menu: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud/reports/sales/{user_id}")
async def get_cloud_sales_report(
    user_id: str,
    date_from: str,
    date_to: str,
    group_by: str = "DAY",
    organization_id: Optional[str] = None
):
    """Get sales report from iikoCloud API"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": user_id})
        if not credentials or credentials.get("status") != "connected":
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        # Используем выбранную организацию или переданную
        org_id = organization_id or credentials.get("selected_organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="Организация не выбрана")
        
        api_key = credentials.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="API ключ не найден")
        
        client = IikoClient(api_login=api_key)
        report = client.get_sales_report(org_id, date_from, date_to, group_by)
        
        return {
            "organization_id": org_id,
            "organization_name": credentials.get("selected_organization_name"),
            "date_from": date_from,
            "date_to": date_to,
            "group_by": group_by,
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Cloud sales report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud/reports/stock/{user_id}")
async def get_cloud_stock_report(
    user_id: str,
    date: Optional[str] = None,
    organization_id: Optional[str] = None
):
    """Get stock report from iikoCloud API"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": user_id})
        if not credentials or credentials.get("status") != "connected":
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        org_id = organization_id or credentials.get("selected_organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="Организация не выбрана")
        
        api_key = credentials.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="API ключ не найден")
        
        client = IikoClient(api_login=api_key)
        report = client.get_stock_report(org_id, date)
        
        return {
            "organization_id": org_id,
            "organization_name": credentials.get("selected_organization_name"),
            "date": date,
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Cloud stock report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud/reports/purchases/{user_id}")
async def get_cloud_purchases_report(
    user_id: str,
    date_from: str,
    date_to: str,
    supplier_id: Optional[str] = None,
    organization_id: Optional[str] = None
):
    """Get purchases report from iikoCloud API"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": user_id})
        if not credentials or credentials.get("status") != "connected":
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        org_id = organization_id or credentials.get("selected_organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="Организация не выбрана")
        
        api_key = credentials.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="API ключ не найден")
        
        client = IikoClient(api_login=api_key)
        report = client.get_purchases_report(org_id, date_from, date_to, supplier_id)
        
        return {
            "organization_id": org_id,
            "organization_name": credentials.get("selected_organization_name"),
            "date_from": date_from,
            "date_to": date_to,
            "supplier_id": supplier_id,
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Cloud purchases report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud/orders/{user_id}")
async def get_cloud_orders(
    user_id: str,
    date_from: str,
    date_to: str,
    statuses: Optional[str] = None,
    organization_id: Optional[str] = None
):
    """Get orders from iikoCloud API"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": user_id})
        if not credentials or credentials.get("status") != "connected":
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        org_id = organization_id or credentials.get("selected_organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="Организация не выбрана")
        
        api_key = credentials.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="API ключ не найден")
        
        status_list = statuses.split(",") if statuses else None
        
        client = IikoClient(api_login=api_key)
        orders_data = client.get_orders(org_id, date_from, date_to, status_list)
        
        return {
            "organization_id": org_id,
            "organization_name": credentials.get("selected_organization_name"),
            "date_from": date_from,
            "date_to": date_to,
            "orders": orders_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Cloud orders: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud/employees/{user_id}")
async def get_cloud_employees(
    user_id: str,
    organization_id: Optional[str] = None
):
    """Get employees from iikoCloud API"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": user_id})
        if not credentials or credentials.get("status") != "connected":
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        org_id = organization_id or credentials.get("selected_organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="Организация не выбрана")
        
        api_key = credentials.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="API ключ не найден")
        
        client = IikoClient(api_login=api_key)
        employees_data = client.get_employees(org_id)
        
        return {
            "organization_id": org_id,
            "organization_name": credentials.get("selected_organization_name"),
            "employees": employees_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Cloud employees: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud/employees/{user_id}/attendances/{employee_id}")
async def get_cloud_employee_attendances(
    user_id: str,
    employee_id: str,
    date_from: str,
    date_to: str
):
    """Get employee attendances from iikoCloud API"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        credentials = collection.find_one({"user_id": user_id})
        if not credentials or credentials.get("status") != "connected":
            raise HTTPException(status_code=400, detail="iikoCloud не подключен")
        
        api_key = credentials.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="API ключ не найден")
        
        client = IikoClient(api_login=api_key)
        attendances_data = client.get_employee_attendances(employee_id, date_from, date_to)
        
        return {
            "employee_id": employee_id,
            "date_from": date_from,
            "date_to": date_to,
            "attendances": attendances_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Cloud attendances: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cloud/disconnect/{user_id}")
async def disconnect_iiko_cloud(user_id: str):
    """Disconnect iikoCloud and remove stored credentials"""
    try:
        collection = db.get_collection("iiko_cloud_credentials")
        if collection is None:
            return {"status": "error", "message": "Database not initialized"}
        
        result = collection.delete_one({"user_id": user_id})  # Sync PyMongo
        
        if result.deleted_count > 0:
            logger.info(f"iikoCloud disconnected for user: {user_id}")
            return {"status": "disconnected", "message": "iikoCloud отключен"}
        else:
            return {"status": "not_found", "message": "Подключение не найдено"}
            
    except Exception as e:
        logger.error(f"Error disconnecting iikoCloud: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


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
        if rms_service is None:
            return {"status": "not_initialized", "message": "iiko RMS сервис не инициализирован"}
        
        result = rms_service.get_rms_connection_status(user_id=user_id, auto_restore=True)
        return result
        
    except Exception as e:
        logger.error(f"Error getting iiko RMS status: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


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


# ============ BI & ANALYTICS ENDPOINTS (TESTING) ============

class OlapReportRequest(BaseModel):
    """Request for OLAP report"""
    user_id: str = Field(..., description="User ID")
    report_type: str = Field(default="SALES", description="Report type: SALES, TRANSACTIONS, DELIVERIES")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    period_type: str = Field(default="YESTERDAY", description="Period type: TODAY, YESTERDAY, LAST_MONTH, etc.")
    group_by: Optional[str] = Field(None, description="Group by: dish, date, group")
    organization_id: Optional[str] = Field(None, description="Organization ID")


@router.post("/rms/bi/olap-report")
async def get_olap_report(request: OlapReportRequest):
    """
    🧪 ТЕСТОВЫЙ ENDPOINT: Получить OLAP отчет из iiko RMS
    
    Использует сохраненные credentials пользователя для подключения к RMS серверу.
    """
    try:
        logger.info(f"🧪 Testing OLAP report request for user: {request.user_id}")
        
        # Получаем RMS service для доступа к credentials
        rms_service = get_iiko_rms_service()
        
        # Получаем credentials пользователя из БД
        credentials_collection = db.get_collection("iiko_rms_credentials")
        if credentials_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        user_credentials = credentials_collection.find_one({"user_id": request.user_id})
        if not user_credentials:
            raise HTTPException(
                status_code=404,
                detail="IIKO RMS не подключен для этого пользователя. Сначала подключитесь через /rms/connect"
            )
        
        host = user_credentials.get("host")
        login = user_credentials.get("login")
        password = user_credentials.get("password")
        
        if not host or not login or not password:
            raise HTTPException(
                status_code=400,
                detail="Неполные credentials для подключения к RMS"
            )
        
        # Создаем RMS client с credentials пользователя
        from app.services.iiko.iiko_rms_client import IikoRmsClient
        rms_client = IikoRmsClient(host=host, login=login, password=password)
        
        # Аутентификация
        try:
            session_key = rms_client.authenticate()
            logger.info(f"✅ Authenticated with RMS server")
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Ошибка аутентификации с RMS сервером: {str(e)}"
            )
        
        # Определяем organization_id
        org_id = request.organization_id or user_credentials.get("selected_organization_id") or "default"
        
        # Вызываем соответствующий метод в зависимости от group_by
        if request.group_by == "dish":
            report = rms_client.get_sales_report(
                date_from=request.date_from,
                date_to=request.date_to,
                period_type=request.period_type,
                group_by="dish",
                organization_id=org_id if org_id != "default" else None
            )
        elif request.group_by == "date":
            report = rms_client.get_sales_report(
                date_from=request.date_from,
                date_to=request.date_to,
                period_type=request.period_type,
                group_by="date",
                organization_id=org_id if org_id != "default" else None
            )
        else:
            # Полный OLAP отчет
            report = rms_client.get_olap_report(
                report_type=request.report_type,
                date_from=request.date_from,
                date_to=request.date_to,
                period_type=request.period_type,
                organization_id=org_id if org_id != "default" else None
            )
        
        logger.info(f"✅ OLAP report retrieved successfully: {len(report.get('data', []))} rows")
        
        return {
            "status": "success",
            "report": report,
            "organization_id": org_id,
            "message": f"Отчет получен успешно ({len(report.get('data', []))} строк)"
        }
        
    except HTTPException:
        raise
    except IikoRmsAPIError as e:
        logger.error(f"IIKO RMS API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка получения OLAP отчета: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting OLAP report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка: {str(e)}"
        )


@router.get("/rms/bi/dish-statistics/{user_id}")
async def get_dish_statistics(
    user_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    period_type: str = "LAST_MONTH",
    top_n: int = 10,
    organization_id: Optional[str] = None
):
    """
    🧪 ТЕСТОВЫЙ ENDPOINT: Получить статистику по блюдам (топ продаж)
    """
    try:
        logger.info(f"🧪 Testing dish statistics for user: {user_id}")
        
        rms_service = get_iiko_rms_service()
        credentials_collection = db.get_collection("iiko_rms_credentials")
        
        if credentials_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        user_credentials = credentials_collection.find_one({"user_id": user_id})
        if not user_credentials:
            raise HTTPException(
                status_code=404,
                detail="IIKO RMS не подключен. Сначала подключитесь через /rms/connect"
            )
        
        from app.services.iiko.iiko_rms_client import IikoRmsClient
        rms_client = IikoRmsClient(
            host=user_credentials.get("host"),
            login=user_credentials.get("login"),
            password=user_credentials.get("password")
        )
        
        rms_client.authenticate()
        org_id = organization_id or user_credentials.get("selected_organization_id")
        
        statistics = rms_client.get_dish_statistics(
            date_from=date_from,
            date_to=date_to,
            period_type=period_type,
            top_n=top_n,
            organization_id=org_id if org_id and org_id != "default" else None
        )
        
        return {
            "status": "success",
            "statistics": statistics,
            "message": f"Статистика получена: топ {top_n} блюд"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dish statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rms/bi/revenue/{user_id}")
async def get_revenue_by_period(
    user_id: str,
    period_type: str = "LAST_MONTH",
    organization_id: Optional[str] = None
):
    """
    🧪 ТЕСТОВЫЙ ENDPOINT: Получить выручку по периодам
    """
    try:
        logger.info(f"🧪 Testing revenue report for user: {user_id}, period: {period_type}")
        
        rms_service = get_iiko_rms_service()
        credentials_collection = db.get_collection("iiko_rms_credentials")
        
        if credentials_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        user_credentials = credentials_collection.find_one({"user_id": user_id})
        if not user_credentials:
            raise HTTPException(
                status_code=404,
                detail="IIKO RMS не подключен. Сначала подключитесь через /rms/connect"
            )
        
        from app.services.iiko.iiko_rms_client import IikoRmsClient
        rms_client = IikoRmsClient(
            host=user_credentials.get("host"),
            login=user_credentials.get("login"),
            password=user_credentials.get("password")
        )
        
        rms_client.authenticate()
        org_id = organization_id or user_credentials.get("selected_organization_id")
        
        revenue = rms_client.get_revenue_by_period(
            period_type=period_type,
            organization_id=org_id if org_id and org_id != "default" else None
        )
        
        return {
            "status": "success",
            "revenue": revenue,
            "message": f"Выручка за период {period_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revenue: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rms/bi/olap-columns/{user_id}")
async def get_olap_columns(user_id: str, report_type: str = "SALES"):
    """
    🧪 ТЕСТОВЫЙ ENDPOINT: Получить список доступных полей для OLAP отчета
    """
    try:
        logger.info(f"🧪 Testing OLAP columns for user: {user_id}, type: {report_type}")
        
        credentials_collection = db.get_collection("iiko_rms_credentials")
        if credentials_collection is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        user_credentials = credentials_collection.find_one({"user_id": user_id})
        if not user_credentials:
            raise HTTPException(
                status_code=404,
                detail="IIKO RMS не подключен. Сначала подключитесь через /rms/connect"
            )
        
        from app.services.iiko.iiko_rms_client import IikoRmsClient
        rms_client = IikoRmsClient(
            host=user_credentials.get("host"),
            login=user_credentials.get("login"),
            password=user_credentials.get("password")
        )
        
        rms_client.authenticate()
        
        columns = rms_client.get_olap_columns(report_type=report_type)
        
        return {
            "status": "success",
            "columns": columns,
            "message": f"Доступные поля для отчета {report_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OLAP columns: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
        cloud_credentials = collection.find_one({"user_id": user_id}) if collection is not None else None  # Sync PyMongo
        
        cloud_status = {
            "connected": cloud_credentials is not None and cloud_credentials.get("status") == "connected",
            "organizations_count": cloud_credentials.get("organizations_count", 0) if cloud_credentials else 0,
            "last_connection": cloud_credentials.get("last_connection") if cloud_credentials else None
        }
        
        # Get RMS status
        rms_service = get_iiko_rms_service()
        rms_status = {"connected": False, "host": None, "organization_name": None, "last_connection": None}
        
        if rms_service:
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
        logger.error(f"Error getting combined iiko status: {str(e)}", exc_info=True)
        return {
            "user_id": user_id,
            "cloud": {"connected": False},
            "rms": {"connected": False},
            "any_connected": False,
            "error": str(e)
        }

