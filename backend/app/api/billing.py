"""
Billing, payments & referral API endpoints.
"""

from fastapi import APIRouter, HTTPException, Request
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
from app.services.payments import (
    create_payment,
    process_webhook,
    get_payment_status,
    PLAN_PRICES,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ReferralApplyRequest(BaseModel):
    user_id: str = Field(..., description="User applying the code")
    code: str = Field(..., min_length=4, max_length=20, description="Referral code")


class PaymentRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    plan: str = Field(..., description="Plan to purchase: starter, business, pro")


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


# ============ PAYMENTS ============

@router.post("/pay")
async def create_subscription_payment(request: PaymentRequest):
    """Create YooKassa payment and return redirect URL."""
    if request.plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Неизвестный тариф: {request.plan}")

    result = create_payment(
        user_id=request.user_id,
        plan=request.plan,
        return_url="https://receptorai.pro"
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/webhook/yokassa")
async def yokassa_webhook(request: Request):
    """YooKassa webhook — processes payment notifications."""
    try:
        body = await request.json()
        result = process_webhook(body)
        return result
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"status": "error"}


@router.get("/payment/{payment_id}")
async def check_payment(payment_id: str):
    """Check payment status."""
    return get_payment_status(payment_id)


# ============ REFERRALS ============

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
