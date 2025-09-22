#!/usr/bin/env python3
"""
Quick AI endpoints test to identify 403 vs other errors
"""

import asyncio
import httpx
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://menupro-revival.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def quick_test():
    """Quick test of AI endpoints"""
    
    # Test with demo_user (existing user)
    user_id = "demo_user"
    
    # Sample tech card in STRING format
    tech_card_string = """**Название:** Тестовое блюдо

**Ингредиенты:**
- Мука: 200 г
- Яйца: 2 шт

**Описание:** Простое блюдо для тестирования
"""
    
    endpoints = [
        ('/generate-sales-script', {'user_id': user_id, 'tech_card': tech_card_string}),
        ('/generate-food-pairing', {'user_id': user_id, 'tech_card': tech_card_string}),
        ('/laboratory-experiment', {'user_id': user_id, 'experiment_type': 'random', 'base_dish': 'Тестовое блюдо'})
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for path, payload in endpoints:
            try:
                print(f"\n🔍 Testing {path}")
                response = await client.post(f"{API_BASE}{path}", json=payload)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 403:
                    print(f"   🚫 FORBIDDEN: {response.json()}")
                elif response.status_code == 200:
                    print(f"   ✅ SUCCESS")
                elif response.status_code == 500:
                    print(f"   💥 SERVER ERROR")
                else:
                    print(f"   🔍 OTHER: {response.status_code}")
                    
            except Exception as e:
                print(f"   ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(quick_test())