#!/usr/bin/env python3
"""
Detailed IIKO Credentials Testing - Specific Review Request Tests
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def test_specific_endpoints():
    """Test the specific endpoints mentioned in the review request"""
    print("🎯 DETAILED IIKO CREDENTIALS TESTING")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Test restore connection endpoint
        print("\n1️⃣ POST /api/v1/iiko/rms/restore-connection?user_id=demo_user")
        print("-" * 60)
        try:
            response = await client.post(
                f"{API_BASE}/v1/iiko/rms/restore-connection",
                params={"user_id": "demo_user"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # 2. Test connection status endpoint
        print("\n2️⃣ GET /api/v1/iiko/rms/connection/status?user_id=demo_user&auto_restore=true")
        print("-" * 60)
        try:
            response = await client.get(
                f"{API_BASE}/v1/iiko/rms/connection/status",
                params={"user_id": "demo_user", "auto_restore": "true"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # 3. Test general RMS status
        print("\n3️⃣ GET /api/v1/iiko/rms/status")
        print("-" * 60)
        try:
            response = await client.get(f"{API_BASE}/v1/iiko/rms/status")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            else:
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        # 4. Test health endpoints for comparison
        print("\n4️⃣ GET /api/v1/iiko/rms/health (for comparison)")
        print("-" * 60)
        try:
            response = await client.get(f"{API_BASE}/v1/iiko/rms/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # 5. Test credential management endpoints
        print("\n5️⃣ Testing credential management endpoints")
        print("-" * 60)
        
        # Test getting credentials for demo_user
        try:
            response = await client.get(
                f"{API_BASE}/v1/iiko/rms/credentials/get",
                params={"user_id": "demo_user"}
            )
            print(f"GET credentials - Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            else:
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"GET credentials error: {e}")
        
        # 6. Test with different user to verify isolation
        print("\n6️⃣ Testing with different user (user isolation)")
        print("-" * 60)
        try:
            response = await client.get(
                f"{API_BASE}/v1/iiko/rms/connection/status",
                params={"user_id": "test_user_123", "auto_restore": "false"}
            )
            print(f"Different user status - Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Different user error: {e}")

if __name__ == "__main__":
    asyncio.run(test_specific_endpoints())