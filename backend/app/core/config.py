
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "RECEPTOR CO-PILOT"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB
    MONGODB_URI: str
    DB_NAME: str = "receptor_copilot"
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

