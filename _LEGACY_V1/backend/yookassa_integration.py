"""
YooKassa payment integration for RECEPTOR PRO
Интеграция платежей для российского рынка
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

# MongoDB connection
from motor.motor_asyncio import AsyncIOMotorClient

# YooKassa SDK
try:
    from yookassa import Configuration, Payment
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    print("⚠️ YooKassa SDK not available. Install: pip install yookassa")

logger = logging.getLogger(__name__)

# Router for YooKassa
router = APIRouter(prefix="/api/yookassa", tags=["YooKassa Payments"])

# YooKassa Configuration
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")

# Initialize YooKassa if credentials are available
if YOOKASSA_AVAILABLE and YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY
    logger.info("✅ YooKassa configured successfully")
else:
    logger.warning("⚠️ YooKassa not configured. Set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY")

# MongoDB connection
mongo_url = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'receptor_pro')]

# Subscription plans with prices
SUBSCRIPTION_PLANS = {
    "pro_monthly_ru": {
        "id": "pro_monthly_ru",
        "name": "PRO Ежемесячно",
        "amount": 1990.00,
        "currency": "RUB",
        "billing_period": "monthly",
        "subscription_plan": "pro",
        "duration_days": 30,
        "description": "PRO подписка Receptor - доступ ко всем функциям на 1 месяц"
    },
    "pro_annual_ru": {
        "id": "pro_annual_ru",
        "name": "PRO Ежегодно",
        "amount": 19900.00,
        "currency": "RUB",
        "billing_period": "annual",
        "subscription_plan": "pro",
        "duration_days": 365,
        "description": "PRO подписка Receptor - доступ ко всем функциям на 1 год (экономия 2 месяца)"
    }
}

class CheckoutRequest(BaseModel):
    package_id: str
    user_id: str
    user_email: Optional[str] = None

class WebhookRequest(BaseModel):
    type: str
    event: str
    object: Dict[str, Any]

@router.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    plans = [
        {
            "id": plan["id"],
            "name": plan["name"],
            "amount": str(plan["amount"]),
            "currency": plan["currency"],
            "billing_period": plan["billing_period"],
            "description": plan["description"]
        }
        for plan in SUBSCRIPTION_PLANS.values()
    ]
    return {
        "plans": plans,
        "currency": "RUB",
        "market": "RU"
    }

@router.post("/checkout")
async def create_checkout(request: CheckoutRequest):
    """Create YooKassa payment session"""
    try:
        logger.info(f"🔵 Creating checkout for user {request.user_id}, package {request.package_id}")
        
        if not YOOKASSA_AVAILABLE:
            logger.error("❌ YooKassa SDK not available")
            raise HTTPException(status_code=503, detail="YooKassa SDK not available")
        
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            logger.error(f"❌ YooKassa not configured. Shop ID: {bool(YOOKASSA_SHOP_ID)}, Secret Key: {bool(YOOKASSA_SECRET_KEY)}")
            raise HTTPException(status_code=503, detail="YooKassa not configured. Set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY")
        
        logger.info(f"✅ YooKassa configured. Shop ID: {YOOKASSA_SHOP_ID[:4]}...")
        
        # Validate package
        if request.package_id not in SUBSCRIPTION_PLANS:
            logger.error(f"❌ Invalid package_id: {request.package_id}")
            raise HTTPException(status_code=400, detail=f"Invalid package_id: {request.package_id}")
        
        package = SUBSCRIPTION_PLANS[request.package_id]
        logger.info(f"✅ Package found: {package['name']}, amount: {package['amount']}")
        
        # Get user
        user = await db.users.find_one({"id": request.user_id})
        if not user:
            logger.error(f"❌ User not found: {request.user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ User found: {user.get('email', 'N/A')}")
        
        # Get user email
        user_email = request.user_email or user.get("email")
        if not user_email:
            logger.error(f"❌ User email is required for user {request.user_id}")
            raise HTTPException(status_code=400, detail="User email is required")
        
        logger.info(f"✅ Creating payment with email: {user_email}")
        
        # Create payment in YooKassa
        payment_idempotence_key = str(uuid.uuid4())
        logger.info(f"🔵 Payment idempotence key: {payment_idempotence_key}")
        
        payment_data = {
            "amount": {
                "value": f"{package['amount']:.2f}",
                "currency": package["currency"]
            },
            "confirmation": {
                "type": "redirect",
                "return_url": os.getenv("YOOKASSA_RETURN_URL", "https://receptorai.pro/pricing?status=success")
            },
            "capture": True,
            "description": package["description"],
            "metadata": {
                "user_id": request.user_id,
                "package_id": request.package_id,
                "subscription_plan": package["subscription_plan"],
                "duration_days": package["duration_days"]
            },
            "receipt": {
                "customer": {
                    "email": user_email
                },
                "items": [
                    {
                        "description": package["name"],
                        "quantity": "1",
                        "amount": {
                            "value": f"{package['amount']:.2f}",
                            "currency": package["currency"]
                        },
                        "vat_code": 1  # НДС не облагается
                    }
                ]
            }
        }
        
        logger.info(f"🔵 Payment data prepared, calling YooKassa API...")
        payment = Payment.create(payment_data, payment_idempotence_key)
        logger.info(f"✅ Payment created: {payment.id}, status: {payment.status}")
        
        # Save payment to database
        payment_record = {
            "payment_id": payment.id,
            "user_id": request.user_id,
            "package_id": request.package_id,
            "subscription_plan": package["subscription_plan"],
            "amount": package["amount"],
            "currency": package["currency"],
            "status": payment.status,
            "created_at": datetime.utcnow(),
            "metadata": payment.metadata
        }
        await db.payments.insert_one(payment_record)
        
        return {
            "success": True,
            "confirmation_url": payment.confirmation.confirmation_url,
            "payment_id": payment.id,
            "status": payment.status,
            "amount": {
                "value": f"{package['amount']:.2f}",
                "currency": package["currency"]
            },
            "expires_in": "24 hours",
            "package": {
                "id": package["id"],
                "name": package["name"],
                "billing_period": package["billing_period"]
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Failed to create YooKassa payment: {e}")
        logger.error(f"❌ Error traceback: {error_trace}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create payment: {str(e)}. Check server logs for details."
        )

@router.post("/webhook")
async def handle_webhook(request: Request):
    """Handle YooKassa webhook notifications"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        headers = dict(request.headers)
        
        # Parse webhook data
        webhook_data = await request.json()
        
        logger.info(f"Received YooKassa webhook: {webhook_data.get('type')} - {webhook_data.get('event')}")
        
        # Handle payment.succeeded event
        if webhook_data.get("event") == "payment.succeeded":
            payment_object = webhook_data.get("object", {})
            payment_id = payment_object.get("id")
            metadata = payment_object.get("metadata", {})
            user_id = metadata.get("user_id")
            subscription_plan = metadata.get("subscription_plan", "pro")
            duration_days = metadata.get("duration_days", 30)
            
            if not payment_id or not user_id:
                logger.error(f"Missing payment_id or user_id in webhook: {webhook_data}")
                return {"status": "error", "message": "Missing required fields"}
            
            # Update payment status
            await db.payments.update_one(
                {"payment_id": payment_id},
                {
                    "$set": {
                        "status": "succeeded",
                        "paid_at": datetime.utcnow(),
                        "webhook_received_at": datetime.utcnow()
                    }
                }
            )
            
            # Activate subscription for user
            subscription_end_date = datetime.utcnow() + timedelta(days=duration_days)
            
            await db.users.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "subscription_plan": subscription_plan,
                        "subscription_start_date": datetime.utcnow(),
                        "subscription_end_date": subscription_end_date,
                        "subscription_status": "active"
                    }
                }
            )
            
            logger.info(f"✅ Subscription activated for user {user_id}: {subscription_plan} until {subscription_end_date}")
            
            return {"status": "success", "message": "Subscription activated"}
        
        # Handle payment.canceled event
        elif webhook_data.get("event") == "payment.canceled":
            payment_object = webhook_data.get("object", {})
            payment_id = payment_object.get("id")
            
            if payment_id:
                await db.payments.update_one(
                    {"payment_id": payment_id},
                    {
                        "$set": {
                            "status": "canceled",
                            "canceled_at": datetime.utcnow()
                        }
                    }
                )
            
            return {"status": "success", "message": "Payment canceled"}
        
        return {"status": "success", "message": "Webhook processed"}
    
    except Exception as e:
        logger.error(f"Error processing YooKassa webhook: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/payment/{payment_id}")
async def get_payment_status(payment_id: str):
    """Get payment status from YooKassa"""
    if not YOOKASSA_AVAILABLE:
        raise HTTPException(status_code=503, detail="YooKassa SDK not available")
    
    try:
        # Get payment from YooKassa
        payment = Payment.find_one(payment_id)  # YooKassa SDK method
        
        # Get payment from database
        payment_record = await db.payments.find_one({"payment_id": payment_id})
        
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "amount": {
                "value": payment.amount.value,
                "currency": payment.amount.currency
            },
            "description": payment.description,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "paid_at": payment_record.get("paid_at").isoformat() if payment_record and payment_record.get("paid_at") else None,
            "metadata": payment.metadata,
            "local_transaction": True
        }
    except Exception as e:
        logger.error(f"Failed to get payment status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")

@router.post("/confirm")
async def confirm_payment(payment_id: str):
    """Confirm payment and activate subscription (fallback method)"""
    try:
        # Get payment from database
        payment_record = await db.payments.find_one({"payment_id": payment_id})
        if not payment_record:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check if already processed
        if payment_record.get("status") == "succeeded":
            user_id = payment_record.get("user_id")
            user = await db.users.find_one({"id": user_id})
            
            if user and user.get("subscription_plan") == "pro":
                return {
                    "status": "success",
                    "action": "pro_activated",
                    "user_id": user_id,
                    "message": "Subscription already activated"
                }
        
        # Get payment status from YooKassa
        if YOOKASSA_AVAILABLE:
            try:
                payment = Payment.find_one(payment_id)
                
                if payment.status == "succeeded":
                    # Activate subscription
                    user_id = payment_record.get("user_id")
                    subscription_plan = payment_record.get("subscription_plan", "pro")
                    duration_days = payment_record.get("metadata", {}).get("duration_days", 30)
                    
                    subscription_end_date = datetime.utcnow() + timedelta(days=duration_days)
                    
                    await db.users.update_one(
                        {"id": user_id},
                        {
                            "$set": {
                                "subscription_plan": subscription_plan,
                                "subscription_start_date": datetime.utcnow(),
                                "subscription_end_date": subscription_end_date,
                                "subscription_status": "active"
                            }
                        }
                    )
                    
                    await db.payments.update_one(
                        {"payment_id": payment_id},
                        {
                            "$set": {
                                "status": "succeeded",
                                "paid_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    return {
                        "status": "success",
                        "action": "pro_activated",
                        "user_id": user_id,
                        "message": "Subscription activated successfully"
                    }
                else:
                    return {
                        "status": "pending",
                        "payment_status": payment.status,
                        "message": f"Payment status: {payment.status}"
                    }
            except Exception as e:
                logger.error(f"Failed to check payment in YooKassa: {e}")
                return {
                    "status": "pending",
                    "message": "Could not verify payment status"
                }
        else:
            return {
                "status": "pending",
                "message": "YooKassa SDK not available"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm payment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm payment: {str(e)}")

