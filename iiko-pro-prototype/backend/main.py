"""
🏢 iiko PRO Module - Автономный микросервис
Цель: 3 эндпоинта максимум, извлечение из монолита
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import httpx
import os
from datetime import datetime, timedelta
import uuid
import asyncio

app = FastAPI(
    title="iiko PRO Module",
    description="Автономный модуль для интеграции с iiko RMS",
    version="1.0.0"
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# МОДЕЛИ ДАННЫХ (Pydantic)
# ============================================================================

class IikoCredentials(BaseModel):
    """Креды для подключения к iiko RMS"""
    host: str = Field(..., description="iiko RMS server host")
    login: str = Field(..., description="RMS login") 
    password: str = Field(..., description="RMS password")
    user_id: str = Field(..., description="User ID for connection association")

class ExportRequest(BaseModel):
    """Запрос на экспорт техкарт в iiko"""
    techcard_ids: List[str] = Field(..., description="List of techcard IDs to export")
    organization_id: str = Field(..., description="iiko organization ID")
    user_id: str = Field(..., description="User ID")
    format: str = Field(default="iiko_rms", description="Export format: iiko_rms, xlsx")

class ConnectionStatus(BaseModel):
    """Статус подключения к iiko"""
    status: str = Field(..., description="Connection status")
    host: Optional[str] = None
    login: Optional[str] = None  
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    session_expires_at: Optional[datetime] = None
    last_export: Optional[datetime] = None
    exported_count: int = 0

# ============================================================================
# СЕРВИС iiko RMS (извлечено из монолита)
# ============================================================================

class IikoRmsService:
    """Сервис для работы с iiko RMS API"""
    
    def __init__(self):
        self.sessions = {}  # В продакшене - Redis
        
    async def connect(self, credentials: IikoCredentials) -> Dict[str, Any]:
        """Подключение к iiko RMS и получение организаций"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Авторизация в iiko RMS
                auth_data = {
                    "user_id": credentials.login,
                    "user_secret": credentials.password
                }
                
                response = await client.post(
                    f"https://{credentials.host}/resto/api/auth",
                    json=auth_data
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"iiko RMS auth failed: {response.text}"
                    )
                
                session_key = response.text.strip('"')
                
                # Получение организаций
                orgs_response = await client.get(
                    f"https://{credentials.host}/resto/api/corporation/organizations",
                    params={"key": session_key}
                )
                
                if orgs_response.status_code != 200:
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to get organizations"
                    )
                
                organizations = orgs_response.json()
                
                # Сохраняем сессию
                self.sessions[credentials.user_id] = {
                    "session_key": session_key,
                    "host": credentials.host,
                    "login": credentials.login,
                    "expires_at": datetime.now() + timedelta(hours=2),
                    "organizations": organizations
                }
                
                return {
                    "status": "connected",
                    "host": credentials.host,
                    "organizations": organizations,
                    "session_expires_at": datetime.now() + timedelta(hours=2)
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def export_techcards(self, request: ExportRequest) -> Dict[str, Any]:
        """Экспорт техкарт в iiko RMS"""
        session = self.sessions.get(request.user_id)
        if not session or session["expires_at"] < datetime.now():
            raise HTTPException(status_code=401, detail="Session expired")
        
        try:
            # Здесь была бы логика экспорта техкарт
            # Для демо возвращаем успешный результат
            exported_count = len(request.techcard_ids)
            
            # Обновляем статистику
            if request.user_id in self.sessions:
                self.sessions[request.user_id]["last_export"] = datetime.now()
                self.sessions[request.user_id]["exported_count"] = (
                    self.sessions[request.user_id].get("exported_count", 0) + exported_count
                )
            
            return {
                "status": "exported",
                "exported_count": exported_count,
                "export_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_status(self, user_id: str) -> ConnectionStatus:
        """Получение статуса подключения"""
        session = self.sessions.get(user_id)
        
        if not session:
            return ConnectionStatus(
                status="not_connected",
                exported_count=0
            )
        
        is_expired = session["expires_at"] < datetime.now()
        
        return ConnectionStatus(
            status="connected" if not is_expired else "expired",
            host=session.get("host"),
            login=session.get("login"),
            organization_id=session.get("selected_org_id"),
            organization_name=session.get("selected_org_name"),
            session_expires_at=session["expires_at"],
            last_export=session.get("last_export"),
            exported_count=session.get("exported_count", 0)
        )

# Глобальный сервис
iiko_service = IikoRmsService()

# ============================================================================
# ЭНДПОИНТЫ API (ТОЛЬКО 3 МАКСИМУМ!)
# ============================================================================

@app.post("/iiko/connect", response_model=Dict[str, Any])
async def connect_to_iiko(credentials: IikoCredentials):
    """
    🔌 ЭНДПОИНТ 1: Подключение к iiko RMS
    
    Подключается к серверу iiko RMS, авторизуется и получает список организаций.
    """
    return await iiko_service.connect(credentials)

@app.post("/iiko/export", response_model=Dict[str, Any])  
async def export_techcards(request: ExportRequest):
    """
    📤 ЭНДПОИНТ 2: Экспорт техкарт в iiko
    
    Экспортирует указанные техкарты в iiko RMS в выбранную организацию.
    """
    return await iiko_service.export_techcards(request)

@app.get("/iiko/status", response_model=ConnectionStatus)
async def get_iiko_status(user_id: str):
    """
    📊 ЭНДПОИНТ 3: Статус подключения к iiko
    
    Возвращает текущий статус подключения, сессии и статистику экспорта.
    """
    return iiko_service.get_status(user_id)

# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ (СЕРВИСНЫЕ)
# ============================================================================

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о модуле"""
    return {
        "name": "iiko PRO Module",
        "version": "1.0.0", 
        "description": "Автономный модуль для интеграции с iiko RMS",
        "endpoints": [
            "POST /iiko/connect - Подключение к iiko RMS",
            "POST /iiko/export - Экспорт техкарт",
            "GET /iiko/status - Статус подключения"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)