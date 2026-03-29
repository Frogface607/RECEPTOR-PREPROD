"""
Restaurant menu management API.
CRUD operations for categories and menu items.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import logging

from app.core.database import db

logger = logging.getLogger(__name__)
router = APIRouter()

CATEGORIES_COLLECTION = "menu_categories"
ITEMS_COLLECTION = "menu_items"


def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid ID: {id_str}")


# ---- Models ----

class CategoryCreate(BaseModel):
    user_id: str
    name: str = Field(..., min_length=1, max_length=100)
    sort_order: int = 0

class ItemCreate(BaseModel):
    user_id: str
    category_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    weight: Optional[str] = None  # "200г", "350мл"
    is_available: bool = True
    sort_order: int = 0


# ---- Categories ----

@router.get("/categories/{user_id}")
async def get_categories(user_id: str):
    """Get all menu categories for a user."""
    col = db.get_collection(CATEGORIES_COLLECTION)
    cats = list(col.find({"user_id": user_id}).sort("sort_order", 1))
    for c in cats:
        c["_id"] = str(c["_id"])
    return {"categories": cats}


@router.post("/categories")
async def create_category(data: CategoryCreate):
    col = db.get_collection(CATEGORIES_COLLECTION)
    doc = {
        "user_id": data.user_id,
        "name": data.name,
        "sort_order": data.sort_order,
        "created_at": datetime.now(timezone.utc),
    }
    result = col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@router.put("/categories/{cat_id}")
async def update_category(cat_id: str, data: CategoryCreate):
    col = db.get_collection(CATEGORIES_COLLECTION)
    col.update_one(
        {"_id": _oid(cat_id)},
        {"$set": {"name": data.name, "sort_order": data.sort_order}}
    )
    return {"status": "updated"}


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: str):
    col = db.get_collection(CATEGORIES_COLLECTION)
    col.delete_one({"_id": _oid(cat_id)})
    # Also delete items in this category
    items_col = db.get_collection(ITEMS_COLLECTION)
    items_col.delete_many({"category_id": cat_id})
    return {"status": "deleted"}


# ---- Items ----

@router.get("/items/{user_id}")
async def get_items(user_id: str, category_id: Optional[str] = None):
    """Get menu items, optionally filtered by category."""
    col = db.get_collection(ITEMS_COLLECTION)
    query = {"user_id": user_id}
    if category_id:
        query["category_id"] = category_id
    items = list(col.find(query).sort("sort_order", 1))
    for item in items:
        item["_id"] = str(item["_id"])
    return {"items": items}


@router.post("/items")
async def create_item(data: ItemCreate):
    col = db.get_collection(ITEMS_COLLECTION)
    doc = {
        "user_id": data.user_id,
        "category_id": data.category_id,
        "name": data.name,
        "description": data.description,
        "price": data.price,
        "weight": data.weight,
        "is_available": data.is_available,
        "sort_order": data.sort_order,
        "created_at": datetime.now(timezone.utc),
    }
    result = col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@router.put("/items/{item_id}")
async def update_item(item_id: str, data: ItemCreate):
    col = db.get_collection(ITEMS_COLLECTION)
    col.update_one(
        {"_id": _oid(item_id)},
        {"$set": {
            "name": data.name,
            "description": data.description,
            "price": data.price,
            "weight": data.weight,
            "is_available": data.is_available,
            "category_id": data.category_id,
            "sort_order": data.sort_order,
        }}
    )
    return {"status": "updated"}


@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    col = db.get_collection(ITEMS_COLLECTION)
    col.delete_one({"_id": _oid(item_id)})
    return {"status": "deleted"}
