
# ==========================================
# BILLING & MONETIZATION (2025)
# ==========================================

PRICING_PLANS = {
    "free": {
        "name": "Start",
        "price": 0,
        "tokens": 50,
        "limits": {"storage": 10, "export": "watermark"}
    },
    "pro": {
        "name": "Pro Chef",
        "price": 2990,
        "tokens": 1000,
        "limits": {"storage": float('inf'), "export": "clean"}
    },
    "business": {
        "name": "Restaurateur",
        "price": 5990,
        "tokens": 3000,
        "limits": {"storage": float('inf'), "export": "clean", "api": True}
    }
}

TOKEN_COSTS = {
    "techcard_generate": 10,
    "techcard_v2_convert": 5,
    "ai_kitchen_recipe": 5,
    "complex_search": 15,
    "menu_audit": 50
}

class PaymentRequest(BaseModel):
    plan_id: Optional[str] = None # 'pro', 'business'
    token_pack_id: Optional[str] = None # 'pack_100', 'pack_500'
    amount: float
    user_id: str

@app.post("/api/billing/create-payment")
async def create_payment(payment: PaymentRequest):
    """
    Mock endpoint to simulate payment creation.
    In production, this would call YooKassa API to get a payment_url.
    """
    # Simulate YooKassa response
    payment_id = str(uuid.uuid4())
    
    # For now, we just auto-approve it for testing
    # In real life, we would return { "payment_url": "https://yoomoney.ru/..." }
    
    user = await db.users.find_one({"_id": payment.user_id})
    if not user:
         # Fallback for demo user or by email
         user = await db.users.find_one({"email": payment.user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update User Balance (Instant delivery for mock)
    tokens_to_add = 0
    new_plan = user.get("subscription_plan", "free")
    
    if payment.plan_id:
        if payment.plan_id in PRICING_PLANS:
            new_plan = payment.plan_id
            tokens_to_add = PRICING_PLANS[payment.plan_id]["tokens"]
    
    if payment.token_pack_id:
        # Example logic for packs
        if payment.token_pack_id == 'pack_100': tokens_to_add += 100
        elif payment.token_pack_id == 'pack_500': tokens_to_add += 500
        elif payment.token_pack_id == 'pack_1000': tokens_to_add += 1000

    current_balance = user.get("tokens_balance", 0)
    new_balance = current_balance + tokens_to_add
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "subscription_plan": new_plan,
                "tokens_balance": new_balance,
                "subscription_updated_at": datetime.utcnow().isoformat()
            },
            "$push": {
                "payment_history": {
                    "payment_id": payment_id,
                    "amount": payment.amount,
                    "date": datetime.utcnow().isoformat(),
                    "items": payment.plan_id or payment.token_pack_id
                }
            }
        }
    )
    
    return {
        "success": True,
        "payment_id": payment_id,
        "new_balance": new_balance,
        "new_plan": new_plan,
        "message": "Payment successful (Mock)"
    }

@app.get("/api/user/{email}/balance")
async def get_user_balance(email: str):
    user = await db.users.find_one({"email": email})
    if not user:
        return {"tokens": 0, "plan": "free"}
    return {
        "tokens": user.get("tokens_balance", 0),
        "plan": user.get("subscription_plan", "free")
    }


