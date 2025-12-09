
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import db
from app.api import chat, venue

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    db.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close()

@app.get("/")
async def root():
    return {"message": "Welcome to RECEPTOR CO-PILOT API v2.0", "status": "online"}

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(venue.router, prefix="/api/venue", tags=["venue"])
