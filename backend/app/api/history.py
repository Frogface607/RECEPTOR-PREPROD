"""
Chat History API для RECEPTOR CO-PILOT
Сохранение и загрузка истории чатов + продвинутые фишки
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import logging
import json
import re

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
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = None


class ChatResponse(BaseModel):
    id: str
    user_id: str
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    message_count: int
    is_favorite: Optional[bool] = False
    tags: Optional[List[str]] = []


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
        "message_count": len(chat.get("messages", [])),
        "is_favorite": chat.get("is_favorite", False),
        "tags": chat.get("tags", [])
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
            "updated_at": datetime.utcnow(),
            "is_favorite": False,
            "tags": []
        }
        
        result = collection.insert_one(chat_doc)
        chat_doc["_id"] = result.inserted_id
        
        logger.info(f"✅ Created chat {result.inserted_id} for user {chat_data.user_id}")
        return serialize_chat(chat_doc)
        
    except Exception as e:
        logger.error(f"Error creating chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/{user_id}", response_model=List[ChatResponse])
async def get_user_chats(
    user_id: str, 
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    search: Optional[str] = None,
    favorite_only: bool = Query(False),
    tag: Optional[str] = None
):
    """Получить список чатов пользователя с фильтрами и поиском"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        # Базовый фильтр
        query = {"user_id": user_id}
        
        # Фильтр по избранному
        if favorite_only:
            query["is_favorite"] = True
        
        # Фильтр по тегу
        if tag:
            query["tags"] = {"$in": [tag]}
        
        # Поиск по названию или содержимому
        if search:
            search_regex = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [
                {"title": search_regex},
                {"messages.content": search_regex}
            ]
        
        chats_cursor = collection.find(query).sort("updated_at", -1).skip(skip).limit(limit)
        
        chats = [serialize_chat(chat) for chat in chats_cursor]
        
        logger.info(f"📋 Found {len(chats)} chats for user {user_id} (search: {search}, favorite: {favorite_only})")
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
        
        if update_data.is_favorite is not None:
            update_fields["is_favorite"] = update_data.is_favorite
        
        if update_data.tags is not None:
            update_fields["tags"] = update_data.tags
        
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


# ============ ПРОДВИНУТЫЕ ФИШКИ ============

@router.get("/chat/{chat_id}/export")
async def export_chat(chat_id: str, format: str = Query("markdown", regex="^(markdown|json)$")):
    """Экспортировать чат в Markdown или JSON"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        chat = collection.find_one({"_id": ObjectId(chat_id)})
        
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")
        
        if format == "markdown":
            # Генерируем Markdown
            md_content = f"# {chat.get('title', 'Чат')}\n\n"
            md_content += f"**Создан:** {chat.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')}\n"
            md_content += f"**Обновлён:** {chat.get('updated_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')}\n\n"
            md_content += "---\n\n"
            
            for msg in chat.get("messages", []):
                role_emoji = "👤" if msg["role"] == "user" else "🤖"
                role_name = "Пользователь" if msg["role"] == "user" else "RECEPTOR"
                timestamp = ""
                if msg.get("timestamp"):
                    ts = msg["timestamp"]
                    if isinstance(ts, str):
                        timestamp = f" *({ts})*"
                    else:
                        timestamp = f" *({ts.strftime('%H:%M')})*"
                
                md_content += f"## {role_emoji} {role_name}{timestamp}\n\n"
                md_content += f"{msg.get('content', '')}\n\n"
                md_content += "---\n\n"
            
            return Response(
                content=md_content,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f'attachment; filename="chat_{chat_id}.md"'
                }
            )
        
        elif format == "json":
            # Генерируем JSON
            export_data = {
                "id": str(chat["_id"]),
                "title": chat.get("title", "Чат"),
                "created_at": chat.get("created_at", datetime.utcnow()).isoformat(),
                "updated_at": chat.get("updated_at", datetime.utcnow()).isoformat(),
                "messages": [
                    {
                        "role": msg.get("role"),
                        "content": msg.get("content"),
                        "timestamp": msg.get("timestamp").isoformat() if isinstance(msg.get("timestamp"), datetime) else msg.get("timestamp")
                    }
                    for msg in chat.get("messages", [])
                ]
            }
            
            return Response(
                content=json.dumps(export_data, ensure_ascii=False, indent=2),
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="chat_{chat_id}.json"'
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting chat {chat_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/{user_id}/stats")
async def get_chat_stats(user_id: str):
    """Получить статистику по чатам пользователя"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        total_chats = collection.count_documents({"user_id": user_id})
        favorite_chats = collection.count_documents({"user_id": user_id, "is_favorite": True})
        
        # Подсчитываем общее количество сообщений
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$project": {"message_count": {"$size": "$messages"}}},
            {"$group": {"_id": None, "total_messages": {"$sum": "$message_count"}}}
        ]
        result = list(collection.aggregate(pipeline))
        total_messages = result[0]["total_messages"] if result else 0
        
        # Самый активный чат
        most_active = collection.find_one(
            {"user_id": user_id},
            sort=[("messages", -1)]
        )
        
        # Теги
        pipeline_tags = [
            {"$match": {"user_id": user_id, "tags": {"$exists": True, "$ne": []}}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_tags = list(collection.aggregate(pipeline_tags))
        
        stats = {
            "total_chats": total_chats,
            "favorite_chats": favorite_chats,
            "total_messages": total_messages,
            "top_tags": [{"tag": t["_id"], "count": t["count"]} for t in top_tags],
            "most_active_chat": {
                "id": str(most_active["_id"]),
                "title": most_active.get("title"),
                "message_count": len(most_active.get("messages", []))
            } if most_active else None
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/{chat_id}/favorite")
async def toggle_favorite(chat_id: str):
    """Переключить избранное для чата"""
    try:
        collection = db.get_collection(CHATS_COLLECTION)
        
        chat = collection.find_one({"_id": ObjectId(chat_id)})
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")
        
        new_favorite = not chat.get("is_favorite", False)
        collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {"is_favorite": new_favorite, "updated_at": datetime.utcnow()}}
        )
        
        return {"status": "ok", "is_favorite": new_favorite}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

