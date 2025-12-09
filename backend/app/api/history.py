"""
Chat History API для RECEPTOR CO-PILOT
Сохранение и загрузка истории чатов
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import logging

from app.core.database import db

logger = logging.getLogger(__name__)
router = APIRouter()

CHATS_COLLECTION = "chat_history"


# ============ MODELS ============

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class ChatCreate(BaseModel):
    user_id: str
    title: Optional[str] = None
    messages: List[Message] = []


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Message]] = None


class ChatResponse(BaseModel):
    id: str
    user_id: str
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    message_count: int


# ============ HELPER FUNCTIONS ============

def generate_chat_title(messages: List[Message]) -> str:
    """Генерирует название чата из первого сообщения пользователя"""
    for msg in messages:
        if msg.role == "user" and msg.content:
            # Берём первые 50 символов
            title = msg.content[:50]
            if len(msg.content) > 50:
                title += "..."
            return title
    return "Новый чат"


def serialize_chat(chat: dict) -> dict:
    """Конвертирует MongoDB документ в JSON-совместимый формат"""
    return {
        "id": str(chat["_id"]),
        "user_id": chat["user_id"],
        "title": chat.get("title", "Новый чат"),
        "messages": chat.get("messages", []),
        "created_at": chat.get("created_at", datetime.utcnow()),
        "updated_at": chat.get("updated_at", datetime.utcnow()),
        "message_count": len(chat.get("messages", []))
    }


# ============ API ENDPOINTS ============

@router.post("/chats", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate):
    """Создать новый чат"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        # Генерируем название если не указано
        title = chat_data.title or generate_chat_title(chat_data.messages)
        
        # Добавляем timestamps к сообщениям
        messages = []
        for msg in chat_data.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp or datetime.utcnow()
            })
        
        chat_doc = {
            "user_id": chat_data.user_id,
            "title": title,
            "messages": messages,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = collection.insert_one(chat_doc)
        chat_doc["_id"] = result.inserted_id
        
        logger.info(f"✅ Created chat {result.inserted_id} for user {chat_data.user_id}")
        return serialize_chat(chat_doc)
        
    except Exception as e:
        logger.error(f"Error creating chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/{user_id}", response_model=List[ChatResponse])
async def get_user_chats(user_id: str, limit: int = 20):
    """Получить список чатов пользователя"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        chats_cursor = collection.find(
            {"user_id": user_id}
        ).sort("updated_at", -1).limit(limit)
        
        chats = [serialize_chat(chat) for chat in chats_cursor]
        
        logger.info(f"📋 Found {len(chats)} chats for user {user_id}")
        return chats
        
    except Exception as e:
        logger.error(f"Error getting chats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{chat_id}")
async def get_chat(chat_id: str):
    """Получить конкретный чат по ID"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        chat = collection.find_one({"_id": ObjectId(chat_id)})
        
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")
        
        return serialize_chat(chat)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/chat/{chat_id}")
async def update_chat(chat_id: str, update_data: ChatUpdate):
    """Обновить чат (добавить сообщения, изменить название)"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        update_fields = {"updated_at": datetime.utcnow()}
        
        if update_data.title is not None:
            update_fields["title"] = update_data.title
        
        if update_data.messages is not None:
            messages = []
            for msg in update_data.messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp or datetime.utcnow()
                })
            update_fields["messages"] = messages
            
            # Обновляем название если это первое сообщение
            if not update_data.title:
                update_fields["title"] = generate_chat_title(update_data.messages)
        
        result = collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Чат не найден")
        
        # Возвращаем обновлённый чат
        chat = collection.find_one({"_id": ObjectId(chat_id)})
        return serialize_chat(chat)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/{chat_id}/message")
async def add_message_to_chat(chat_id: str, message: Message):
    """Добавить сообщение в существующий чат"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        msg_data = {
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp or datetime.utcnow()
        }
        
        result = collection.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$push": {"messages": msg_data},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Чат не найден")
        
        return {"status": "ok", "message": "Сообщение добавлено"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message to chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: str):
    """Удалить чат"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        result = collection.delete_one({"_id": ObjectId(chat_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Чат не найден")
        
        logger.info(f"🗑️ Deleted chat {chat_id}")
        return {"status": "ok", "message": "Чат удалён"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

