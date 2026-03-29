"""
User plans, usage tracking, and referral system.
Handles: free/pro tiers, daily message limits, referral codes & bonuses.
"""

import logging
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from app.core.database import db

logger = logging.getLogger(__name__)

USERS_COLLECTION = "users"
REFERRALS_COLLECTION = "referrals"

# ---- Plan definitions ----

PLANS = {
    "free": {
        "name": "Free",
        "messages_per_day": 5,
        "deep_research_per_month": 0,
        "bi_export": False,
        "staff_management": False,
        "iiko_integration": False,
        "price_rub": 0,
    },
    "starter": {
        "name": "Starter",
        "messages_per_day": -1,  # unlimited
        "deep_research_per_month": 2,
        "bi_export": True,
        "staff_management": False,
        "iiko_integration": False,
        "price_rub": 990,
    },
    "business": {
        "name": "Business",
        "messages_per_day": -1,
        "deep_research_per_month": 5,
        "bi_export": True,
        "staff_management": True,
        "iiko_integration": False,
        "price_rub": 2990,
    },
    "pro": {
        "name": "Pro",
        "messages_per_day": -1,
        "deep_research_per_month": -1,
        "bi_export": True,
        "staff_management": True,
        "iiko_integration": True,
        "price_rub": 5990,
    },
}

REFERRAL_BONUS_DAYS = 14  # 14 days of Pro for each referral


def _users():
    return db.get_collection(USERS_COLLECTION)


def _referrals():
    return db.get_collection(REFERRALS_COLLECTION)


def _generate_referral_code() -> str:
    """Generate a unique 8-char referral code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(chars) for _ in range(8))
        if not _referrals().find_one({"code": code}):
            return code


# ---- User management ----

def get_or_create_user(user_id: str) -> Dict[str, Any]:
    """Get existing user or create a new free-tier user."""
    collection = _users()
    user = collection.find_one({"user_id": user_id})

    if user:
        user["_id"] = str(user["_id"])
        return user

    # New user
    referral_code = _generate_referral_code()
    new_user = {
        "user_id": user_id,
        "plan": "free",
        "plan_expires_at": None,
        "referral_code": referral_code,
        "referred_by": None,
        "messages_today": 0,
        "messages_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "deep_research_this_month": 0,
        "deep_research_month": datetime.now(timezone.utc).strftime("%Y-%m"),
        "created_at": datetime.now(timezone.utc),
    }
    result = collection.insert_one(new_user)
    new_user["_id"] = str(result.inserted_id)
    logger.info(f"Created new user: {user_id}, referral code: {referral_code}")
    return new_user


def get_user_plan(user_id: str) -> Dict[str, Any]:
    """Get user's current plan with limits and usage info."""
    user = get_or_create_user(user_id)
    plan_key = user.get("plan", "free")

    # Check if paid plan expired
    expires = user.get("plan_expires_at")
    if expires and plan_key != "free":
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires)
        if expires < datetime.now(timezone.utc):
            # Plan expired — downgrade to free
            _users().update_one(
                {"user_id": user_id},
                {"$set": {"plan": "free", "plan_expires_at": None}}
            )
            plan_key = "free"
            user["plan"] = "free"

    plan = PLANS.get(plan_key, PLANS["free"])

    # Reset daily counter if new day
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if user.get("messages_date") != today:
        _users().update_one(
            {"user_id": user_id},
            {"$set": {"messages_today": 0, "messages_date": today}}
        )
        user["messages_today"] = 0

    # Reset monthly counter if new month
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    if user.get("deep_research_month") != this_month:
        _users().update_one(
            {"user_id": user_id},
            {"$set": {"deep_research_this_month": 0, "deep_research_month": this_month}}
        )
        user["deep_research_this_month"] = 0

    return {
        "user_id": user_id,
        "plan": plan_key,
        "plan_name": plan["name"],
        "price_rub": plan["price_rub"],
        "messages_today": user.get("messages_today", 0),
        "messages_limit": plan["messages_per_day"],
        "messages_remaining": (
            plan["messages_per_day"] - user.get("messages_today", 0)
            if plan["messages_per_day"] > 0 else -1
        ),
        "deep_research_this_month": user.get("deep_research_this_month", 0),
        "deep_research_limit": plan["deep_research_per_month"],
        "bi_export": plan["bi_export"],
        "referral_code": user.get("referral_code", ""),
        "plan_expires_at": user.get("plan_expires_at"),
    }


def check_message_limit(user_id: str) -> Dict[str, Any]:
    """Check if user can send a message. Returns allowed: True/False + info."""
    info = get_user_plan(user_id)
    limit = info["messages_limit"]

    if limit == -1:
        return {"allowed": True, **info}

    if info["messages_today"] >= limit:
        return {
            "allowed": False,
            "reason": f"Лимит {limit} сообщений в день исчерпан. Перейдите на тариф Pro для безлимитного общения.",
            **info,
        }

    return {"allowed": True, **info}


def increment_message_count(user_id: str):
    """Increment today's message counter."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _users().update_one(
        {"user_id": user_id},
        {
            "$inc": {"messages_today": 1},
            "$set": {"messages_date": today},
        },
        upsert=True,
    )


def check_research_limit(user_id: str) -> Dict[str, Any]:
    """Check if user can start Deep Research."""
    info = get_user_plan(user_id)
    limit = info["deep_research_limit"]

    if limit == -1:
        return {"allowed": True, **info}
    if limit == 0:
        return {
            "allowed": False,
            "reason": "Deep Research доступен на тарифе Pro.",
            **info,
        }
    if info["deep_research_this_month"] >= limit:
        return {
            "allowed": False,
            "reason": f"Лимит {limit} исследований в месяц исчерпан.",
            **info,
        }
    return {"allowed": True, **info}


def increment_research_count(user_id: str):
    """Increment this month's research counter."""
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    _users().update_one(
        {"user_id": user_id},
        {
            "$inc": {"deep_research_this_month": 1},
            "$set": {"deep_research_month": this_month},
        },
        upsert=True,
    )


# ---- Referral system ----

def apply_referral_code(user_id: str, code: str) -> Dict[str, Any]:
    """Apply a referral code: bonus for both referrer and referee."""
    user = get_or_create_user(user_id)

    if user.get("referred_by"):
        return {"success": False, "error": "Вы уже использовали реферальный код."}

    if user.get("referral_code") == code:
        return {"success": False, "error": "Нельзя использовать свой собственный код."}

    # Find referrer
    referrer = _users().find_one({"referral_code": code})
    if not referrer:
        return {"success": False, "error": "Код не найден."}

    now = datetime.now(timezone.utc)
    bonus_until = now + timedelta(days=REFERRAL_BONUS_DAYS)

    # Bonus for referee (new user) — 14 days of Pro
    ref_expires = user.get("plan_expires_at")
    if ref_expires and isinstance(ref_expires, datetime) and ref_expires > now:
        new_expires = ref_expires + timedelta(days=REFERRAL_BONUS_DAYS)
    else:
        new_expires = bonus_until

    _users().update_one(
        {"user_id": user_id},
        {"$set": {
            "referred_by": code,
            "plan": "pro",
            "plan_expires_at": new_expires,
        }}
    )

    # Bonus for referrer — extend Pro by 14 days
    ref_plan_expires = referrer.get("plan_expires_at")
    if ref_plan_expires and isinstance(ref_plan_expires, datetime) and ref_plan_expires > now:
        referrer_new_expires = ref_plan_expires + timedelta(days=REFERRAL_BONUS_DAYS)
    else:
        referrer_new_expires = bonus_until

    _users().update_one(
        {"user_id": referrer["user_id"]},
        {"$set": {
            "plan": "pro",
            "plan_expires_at": referrer_new_expires,
        }}
    )

    # Track referral
    _referrals().insert_one({
        "code": code,
        "referrer_id": referrer["user_id"],
        "referee_id": user_id,
        "bonus_days": REFERRAL_BONUS_DAYS,
        "created_at": now,
    })

    logger.info(f"Referral applied: {user_id} used code {code} from {referrer['user_id']}")

    return {
        "success": True,
        "message": f"Код применён! Вам и пригласившему начислено {REFERRAL_BONUS_DAYS} дней Pro.",
        "plan": "pro",
        "plan_expires_at": new_expires.isoformat(),
    }


def get_referral_stats(user_id: str) -> Dict[str, Any]:
    """Get referral stats for a user."""
    user = get_or_create_user(user_id)
    referrals = list(_referrals().find(
        {"referrer_id": user_id},
        {"_id": 0, "referee_id": 1, "created_at": 1}
    ))

    return {
        "referral_code": user.get("referral_code", ""),
        "total_referrals": len(referrals),
        "bonus_days_earned": len(referrals) * REFERRAL_BONUS_DAYS,
        "referrals": referrals,
    }
