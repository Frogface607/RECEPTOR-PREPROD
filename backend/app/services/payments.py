"""
YooKassa payment integration for RECEPTOR subscriptions.
Handles: payment creation, webhook processing, subscription management.
"""

import os
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from yookassa import Configuration, Payment
from app.core.database import db

logger = logging.getLogger(__name__)

# Plan configs
PLAN_PRICES = {
    "starter": {"amount": "990.00", "description": "RECEPTOR Starter — 1 месяц"},
    "business": {"amount": "2990.00", "description": "RECEPTOR Business — 1 месяц"},
    "pro": {"amount": "5990.00", "description": "RECEPTOR Pro — 1 месяц"},
}

PLAN_DURATION_DAYS = 30


def _configure():
    """Configure YooKassa with env vars."""
    shop_id = os.getenv("YOKASSA_SHOP_ID")
    secret_key = os.getenv("YOKASSA_SECRET_KEY")
    if not shop_id or not secret_key:
        logger.warning("YooKassa not configured: YOKASSA_SHOP_ID or YOKASSA_SECRET_KEY missing")
        return False
    Configuration.account_id = shop_id
    Configuration.secret_key = secret_key
    return True


def create_payment(user_id: str, plan: str, return_url: str = "https://receptorai.pro") -> Dict[str, Any]:
    """
    Create a YooKassa payment for a subscription plan.
    Returns payment URL for redirect.
    """
    if not _configure():
        return {"error": "Платежная система не настроена. Обратитесь к администратору."}

    if plan not in PLAN_PRICES:
        return {"error": f"Неизвестный тариф: {plan}"}

    price = PLAN_PRICES[plan]
    idempotency_key = str(uuid.uuid4())

    try:
        payment = Payment.create({
            "amount": {
                "value": price["amount"],
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"{return_url}?payment=success&plan={plan}"
            },
            "capture": True,
            "description": price["description"],
            "metadata": {
                "user_id": user_id,
                "plan": plan,
            }
        }, idempotency_key)

        # Store payment record
        payments_col = db.get_collection("payments")
        payments_col.insert_one({
            "payment_id": payment.id,
            "user_id": user_id,
            "plan": plan,
            "amount": price["amount"],
            "status": payment.status,
            "created_at": datetime.now(timezone.utc),
        })

        logger.info(f"Payment created: {payment.id} for user {user_id}, plan {plan}")

        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status,
        }

    except Exception as e:
        logger.error(f"Payment creation failed: {e}")
        return {"error": f"Ошибка создания платежа: {str(e)}"}


def process_webhook(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process YooKassa webhook notification.
    Activates subscription on successful payment.
    """
    event_type = event_data.get("event")
    payment_data = event_data.get("object", {})
    payment_id = payment_data.get("id")
    status = payment_data.get("status")

    logger.info(f"Webhook received: {event_type}, payment {payment_id}, status {status}")

    if event_type != "payment.succeeded" or status != "succeeded":
        return {"status": "ignored", "reason": f"Event type: {event_type}"}

    # Get metadata
    metadata = payment_data.get("metadata", {})
    user_id = metadata.get("user_id")
    plan = metadata.get("plan")

    if not user_id or not plan:
        logger.error(f"Webhook missing metadata: {metadata}")
        return {"status": "error", "reason": "Missing user_id or plan in metadata"}

    # Update payment record
    payments_col = db.get_collection("payments")
    payments_col.update_one(
        {"payment_id": payment_id},
        {"$set": {"status": "succeeded", "paid_at": datetime.now(timezone.utc)}}
    )

    # Activate subscription
    from app.services.billing import get_or_create_user, _users
    user = get_or_create_user(user_id)
    now = datetime.now(timezone.utc)

    # Extend existing plan or start new
    current_expires = user.get("plan_expires_at")
    if current_expires and isinstance(current_expires, datetime) and current_expires > now:
        new_expires = current_expires + timedelta(days=PLAN_DURATION_DAYS)
    else:
        new_expires = now + timedelta(days=PLAN_DURATION_DAYS)

    _users().update_one(
        {"user_id": user_id},
        {"$set": {
            "plan": plan,
            "plan_expires_at": new_expires,
            "last_payment_id": payment_id,
            "last_payment_at": now,
        }}
    )

    logger.info(f"Subscription activated: user={user_id}, plan={plan}, expires={new_expires}")

    return {
        "status": "success",
        "user_id": user_id,
        "plan": plan,
        "expires_at": new_expires.isoformat(),
    }


def get_payment_status(payment_id: str) -> Dict[str, Any]:
    """Check payment status."""
    if not _configure():
        return {"error": "YooKassa not configured"}

    try:
        payment = Payment.find_one(payment_id)
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "amount": payment.amount.value,
            "paid": payment.paid,
        }
    except Exception as e:
        return {"error": str(e)}
