#!/usr/bin/env python3
"""
Fix Demo User PRO Subscription

This script checks and updates the demo_user to have PRO subscription
so that AI extensions work properly.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'receptor_pro')]

async def check_and_fix_demo_user():
    """Check demo_user status and upgrade to PRO if needed"""
    
    print("🔍 Checking demo_user status...")
    
    # Check if demo_user exists
    user = await db.users.find_one({"id": "demo_user"})
    
    if user:
        print(f"✅ Found demo_user: {user}")
        current_plan = user.get('subscription_plan', 'free')
        print(f"📋 Current subscription: {current_plan}")
        
        if current_plan in ['pro', 'business']:
            print("✅ Demo user already has PRO subscription!")
            return True
        else:
            print("🔧 Upgrading demo_user to PRO subscription...")
            # Update to PRO
            result = await db.users.update_one(
                {"id": "demo_user"},
                {"$set": {"subscription_plan": "pro"}}
            )
            if result.modified_count > 0:
                print("✅ Successfully upgraded demo_user to PRO!")
                return True
            else:
                print("❌ Failed to upgrade demo_user")
                return False
    else:
        print("🔧 Creating demo_user with PRO subscription...")
        # Create demo_user with PRO subscription
        demo_user = {
            "id": "demo_user",
            "email": "demo@example.com",
            "name": "Demo User",
            "city": "moskva",
            "subscription_plan": "pro",
            "monthly_tech_cards_used": 0,
            "created_at": datetime.now(),
            "venue_type": "family_restaurant",
            "venue_name": "Demo Restaurant",
            "average_check": 800
        }
        
        result = await db.users.insert_one(demo_user)
        if result.inserted_id:
            print("✅ Successfully created demo_user with PRO subscription!")
            return True
        else:
            print("❌ Failed to create demo_user")
            return False

async def verify_fix():
    """Verify that the fix worked"""
    print("\n🔍 Verifying fix...")
    
    user = await db.users.find_one({"id": "demo_user"})
    if user:
        subscription_plan = user.get('subscription_plan', 'free')
        print(f"📋 Demo user subscription: {subscription_plan}")
        
        if subscription_plan in ['pro', 'business']:
            print("✅ VERIFICATION PASSED: Demo user has PRO subscription!")
            return True
        else:
            print("❌ VERIFICATION FAILED: Demo user still doesn't have PRO subscription")
            return False
    else:
        print("❌ VERIFICATION FAILED: Demo user not found")
        return False

async def main():
    """Main function"""
    print("🚀 FIXING DEMO USER PRO SUBSCRIPTION")
    print("=" * 50)
    
    try:
        # Fix demo user
        fix_success = await check_and_fix_demo_user()
        
        if fix_success:
            # Verify fix
            verify_success = await verify_fix()
            
            if verify_success:
                print("\n🎉 SUCCESS: Demo user is now PRO and AI extensions should work!")
                return True
            else:
                print("\n🚨 FAILED: Verification failed")
                return False
        else:
            print("\n🚨 FAILED: Could not fix demo user")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)