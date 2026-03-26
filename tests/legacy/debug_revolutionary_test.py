#!/usr/bin/env python3

import asyncio
import httpx
import json
import os
import time
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def debug_tech_card_generation():
    """Debug tech card generation to understand response structure"""
    
    test_user_id = f"debug_test_{str(uuid.uuid4())[:8]}"
    test_dish_name = "Борщ украинский с говядиной"
    
    print(f"🔍 DEBUG: Testing tech card generation for '{test_dish_name}'")
    print(f"🔍 DEBUG: User ID: {test_user_id}")
    print(f"🔍 DEBUG: API Base: {API_BASE}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            start_time = time.time()
            
            # Generate tech card with real LLM
            response = await client.post(
                f"{API_BASE}/v1/techcards.v2/generate?use_llm=true",
                json={
                    "name": test_dish_name,
                    "user_id": test_user_id
                }
            )
            
            generation_time = time.time() - start_time
            
            print(f"🔍 DEBUG: Response status: {response.status_code}")
            print(f"🔍 DEBUG: Generation time: {generation_time:.1f}s")
            print(f"🔍 DEBUG: Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"🔍 DEBUG: Response keys: {list(data.keys())}")
                
                # Print full response structure (truncated)
                print(f"🔍 DEBUG: Full response structure:")
                for key, value in data.items():
                    if key == 'card' and isinstance(value, dict):
                        print(f"  {key}: dict with keys {list(value.keys())}")
                        if 'id' in value:
                            print(f"    id: {value['id']}")
                        if 'article' in value:
                            print(f"    article: {value['article']}")
                        if 'status' in value:
                            print(f"    status: {value['status']}")
                        if 'ingredients' in value:
                            ingredients = value['ingredients']
                            print(f"    ingredients: {len(ingredients)} items")
                            for i, ing in enumerate(ingredients[:3]):  # Show first 3
                                print(f"      [{i}]: {ing.get('name', 'N/A')} - product_code: {ing.get('product_code', 'N/A')}")
                    else:
                        print(f"  {key}: {type(value).__name__} = {str(value)[:100]}")
                
                # Test user history
                print(f"\n🔍 DEBUG: Testing user history...")
                history_response = await client.get(f"{API_BASE}/user-history/{test_user_id}")
                print(f"🔍 DEBUG: History response status: {history_response.status_code}")
                
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    print(f"🔍 DEBUG: History keys: {list(history_data.keys())}")
                    history = history_data.get('history', [])
                    print(f"🔍 DEBUG: History count: {len(history)}")
                    
                    for i, item in enumerate(history):
                        print(f"  [{i}]: id={item.get('id', 'N/A')}, name={item.get('name', 'N/A')}")
                
            else:
                print(f"🔍 DEBUG: Error response: {response.text}")
                
    except Exception as e:
        print(f"🔍 DEBUG: Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_tech_card_generation())