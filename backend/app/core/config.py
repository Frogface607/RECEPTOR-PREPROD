
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "RECEPTOR CO-PILOT"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB - поддерживаем оба варианта: MONGODB_URI и MONGO_URL
    MONGODB_URI: Optional[str] = None
    MONGO_URL: Optional[str] = None
    DB_NAME: str = "receptor_copilot"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Security
    JWT_SECRET_KEY: str = "dev_secret_key_change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @property
    def mongo_connection_string(self) -> str:
        """Возвращает строку подключения к MongoDB (поддерживает оба варианта)"""
        return self.MONGODB_URI or self.MONGO_URL or "mongodb://localhost:27017/receptor_copilot"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Игнорировать лишние переменные в .env

settings = Settings()

