"""
Staff management API.
Employees, roles, schedules.
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

STAFF_COLLECTION = "staff"
SCHEDULE_COLLECTION = "staff_schedule"

ROLES = ["admin", "manager", "chef", "cook", "bartender", "waiter", "hostess", "cashier"]


def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid ID: {id_str}")


# ---- Models ----

class StaffCreate(BaseModel):
    user_id: str  # restaurant owner
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., description="Role: admin, manager, chef, cook, bartender, waiter, hostess, cashier")
    phone: Optional[str] = None
    telegram: Optional[str] = None
    salary: Optional[float] = None
    is_active: bool = True

class ScheduleEntry(BaseModel):
    user_id: str
    staff_id: str
    date: str  # YYYY-MM-DD
    shift_start: str  # HH:MM
    shift_end: str    # HH:MM
    note: Optional[str] = None


# ---- Staff CRUD ----

@router.get("/{user_id}")
async def get_staff(user_id: str):
    """Get all staff members for a restaurant."""
    col = db.get_collection(STAFF_COLLECTION)
    staff = list(col.find({"user_id": user_id}).sort("name", 1))
    for s in staff:
        s["_id"] = str(s["_id"])
    return {"staff": staff, "roles": ROLES}


@router.post("/")
async def create_staff_member(data: StaffCreate):
    if data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Use: {', '.join(ROLES)}")
    col = db.get_collection(STAFF_COLLECTION)
    doc = {
        "user_id": data.user_id,
        "name": data.name,
        "role": data.role,
        "phone": data.phone,
        "telegram": data.telegram,
        "salary": data.salary,
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc),
    }
    result = col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@router.put("/{staff_id}")
async def update_staff_member(staff_id: str, data: StaffCreate):
    if data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Use: {', '.join(ROLES)}")
    col = db.get_collection(STAFF_COLLECTION)
    col.update_one(
        {"_id": _oid(staff_id)},
        {"$set": {
            "name": data.name,
            "role": data.role,
            "phone": data.phone,
            "telegram": data.telegram,
            "salary": data.salary,
            "is_active": data.is_active,
        }}
    )
    return {"status": "updated"}


@router.delete("/{staff_id}")
async def delete_staff_member(staff_id: str):
    col = db.get_collection(STAFF_COLLECTION)
    col.delete_one({"_id": _oid(staff_id)})
    return {"status": "deleted"}


# ---- Schedule ----

@router.get("/schedule/{user_id}")
async def get_schedule(user_id: str, week: Optional[str] = None):
    """Get schedule. Optional: filter by week (YYYY-WNN format)."""
    col = db.get_collection(SCHEDULE_COLLECTION)
    query = {"user_id": user_id}
    entries = list(col.find(query).sort("date", 1).limit(100))
    for e in entries:
        e["_id"] = str(e["_id"])
    return {"schedule": entries}


@router.post("/schedule")
async def create_schedule_entry(data: ScheduleEntry):
    col = db.get_collection(SCHEDULE_COLLECTION)
    doc = {
        "user_id": data.user_id,
        "staff_id": data.staff_id,
        "date": data.date,
        "shift_start": data.shift_start,
        "shift_end": data.shift_end,
        "note": data.note,
        "created_at": datetime.now(timezone.utc),
    }
    # Upsert by staff_id + date (one shift per person per day)
    col.update_one(
        {"staff_id": data.staff_id, "date": data.date},
        {"$set": doc},
        upsert=True,
    )
    return {"status": "saved"}


@router.delete("/schedule/{entry_id}")
async def delete_schedule_entry(entry_id: str):
    col = db.get_collection(SCHEDULE_COLLECTION)
    col.delete_one({"_id": _oid(entry_id)})
    return {"status": "deleted"}
