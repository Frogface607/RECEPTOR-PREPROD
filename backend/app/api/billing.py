"""
Billing & referral API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.services.billing import (
    get_user_plan,
    check_message_limit,
    apply_referral_code,
    get_referral_stats,
    PLANS,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ReferralApplyRequest(BaseModel):
    user_id: str = Field(..., description="User applying the code")
    code: str = Field(..., min_length=4, max_length=20, description="Referral code")


@router.get("/plan/{user_id}")
async def get_plan(user_id: str):
    """Get user's current plan, limits, and usage."""
    return get_user_plan(user_id)


@router.get("/plans")
async def list_plans():
    """Get all available plans with pricing."""
    return {
        "plans": [
            {"key": key, **plan}
            for key, plan in PLANS.items()
        ]
    }


@router.get("/usage/{user_id}")
async def get_usage(user_id: str):
    """Check if user can send messages (quick check for frontend)."""
    return check_message_limit(user_id)


@router.post("/referral/apply")
async def apply_referral(request: ReferralApplyRequest):
    """Apply a referral code. Gives 14 days Pro to both parties."""
    result = apply_referral_code(request.user_id, request.code.upper().strip())
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/referral/{user_id}")
async def get_referrals(user_id: str):
    """Get user's referral code and stats."""
    return get_referral_stats(user_id)
