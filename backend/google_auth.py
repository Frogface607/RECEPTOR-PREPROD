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
import uuid

# MongoDB connection
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Router for Google OAuth
router = APIRouter(prefix="/api/v1/auth", tags=["Google OAuth"])

# JWT Secret (в продакшене должен быть в .env)
JWT_SECRET = os.getenv("JWT_SECRET", "receptor-pro-secret-key-2024")
JWT_ALGORITHM = "HS256"

# MongoDB connection
mongo_url = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'receptor_pro')]

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
    Принимает данные от Google, создаёт или находит пользователя в MongoDB и создаёт JWT токен
    """
    try:
        # Валидация email
        if not request.email or "@" not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email")
        
        # Ищем существующего пользователя по email
        existing_user = await db.users.find_one({"email": request.email})
        
        if existing_user:
            # Пользователь существует - проверяем provider
            if existing_user.get("provider") == "email":
                # Пользователь зарегистрирован через email/password
                # Можно либо разрешить вход через Google (объединить аккаунты)
                # Либо запретить - пока запрещаем для безопасности
                raise HTTPException(
                    status_code=400, 
                    detail="Этот email уже зарегистрирован через email/password. Пожалуйста, войдите используя пароль или используйте другой Google аккаунт."
                )
            
            # Пользователь уже зарегистрирован через Google - обновляем данные
            user_data = {
                "id": existing_user.get("id", f"google_{request.google_id}"),
                "email": existing_user.get("email", request.email),
                "name": existing_user.get("name", request.name),
                "avatar": request.avatar_url or existing_user.get("avatar"),
                "provider": "google",
                "city": existing_user.get("city", "Москва"),
                "subscription_plan": existing_user.get("subscription_plan", "free"),
                "created_at": existing_user.get("created_at", datetime.utcnow())
            }
            
            # Обновляем данные пользователя (имя, аватар могут измениться)
            await db.users.update_one(
                {"email": request.email},
                {"$set": {
                    "name": request.name,
                    "avatar": request.avatar_url,
                    "provider": "google"
                }}
            )
        else:
            # Новый пользователь - создаём в MongoDB
            user_id = str(uuid.uuid4())
            current_date = datetime.utcnow()
            
            # Инициализация subscription fields
            next_reset = current_date.replace(day=1)
            if next_reset.month == 12:
                next_reset = next_reset.replace(year=next_reset.year + 1, month=1)
            else:
                next_reset = next_reset.replace(month=next_reset.month + 1)
            
            user_data = {
                "id": user_id,
                "email": request.email,
                "name": request.name,
                "city": "Москва",  # Default city
                "avatar": request.avatar_url,
                "provider": "google",
                "subscription_plan": "free",
                "subscription_start_date": current_date,
                "monthly_tech_cards_used": 0,
                "monthly_reset_date": next_reset,
                "kitchen_equipment": [],
                "created_at": current_date
            }
            
            # Сохраняем в MongoDB
            await db.users.insert_one(user_data)
            logger.info(f"New Google user created: {request.email}")
        
        # Создаём JWT токен
        token = create_jwt_token(user_data)
        
        logger.info(f"Google auth successful for {request.email}")
        
        return AuthResponse(
            success=True,
            token=token,
            user=user_data,
            message="Успешная авторизация через Google"
        )
        
    except HTTPException:
        raise
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
