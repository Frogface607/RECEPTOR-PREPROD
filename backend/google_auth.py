"""
Google OAuth integration for RECEPTOR PRO
Простая реализация для современной авторизации
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Router for Google OAuth
router = APIRouter(prefix="/api/v1/auth", tags=["Google OAuth"])

# JWT Secret (в продакшене должен быть в .env)
JWT_SECRET = os.getenv("JWT_SECRET", "receptor-pro-secret-key-2024")
JWT_ALGORITHM = "HS256"

class GoogleAuthRequest(BaseModel):
    email: str
    name: str
    google_id: str
    avatar_url: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    token: str
    user: dict
    message: str

def create_jwt_token(user_data: dict) -> str:
    """Создаём JWT токен для пользователя"""
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "name": user_data["name"],
        "exp": datetime.utcnow() + timedelta(days=30),  # 30 дней
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest):
    """
    Google OAuth авторизация
    Принимает данные от Google и создаёт JWT токен
    """
    try:
        # Валидация email
        if not request.email or "@" not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email")
        
        # Создаём или находим пользователя
        user_data = {
            "id": f"google_{request.google_id}",
            "email": request.email,
            "name": request.name,
            "avatar": request.avatar_url,
            "provider": "google",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Создаём JWT токен
        token = create_jwt_token(user_data)
        
        logger.info(f"Google auth successful for {request.email}")
        
        return AuthResponse(
            success=True,
            token=token,
            user=user_data,
            message="Успешная авторизация через Google"
        )
        
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auth error: {str(e)}")

@router.post("/verify-token")
async def verify_token(token: str):
    """
    Проверка JWT токена
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "name": payload.get("name")
        }
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}
