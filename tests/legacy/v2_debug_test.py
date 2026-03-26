#!/usr/bin/env python3
"""
V2 TechCard Generation Debug Test
Debug the actual response structure from V2 endpoint
"""

import requests
import json
import time

# Backend URL
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def debug_v2_response():
    """Debug the actual V2 response structure"""
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'User-Agent': 'V2-Debug-Tester/1.0'
    })
    
    url = f"{API_BASE}/v1/techcards.v2/generate"
    
    # Test data as specified in review request
    payload = {
        "name": "Борщ классический",
        "user_id": "demo_user",
        "cuisine": "европейская"
    }
    
    print(f"🔍 DEBUG: Testing V2 endpoint with payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    try:
        print(f"📡 Making request to: {url}")
        response = session.post(url, json=payload, timeout=90)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ JSON Response received")
                print(f"📋 Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                print()
                
                print("🔍 FULL RESPONSE STRUCTURE:")
                print("=" * 50)
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print("=" * 50)
                
                # Analyze structure
                if isinstance(data, dict):
                    print("\n📊 STRUCTURE ANALYSIS:")
                    for key, value in data.items():
                        value_type = type(value).__name__
                        if isinstance(value, (list, dict)):
                            length = len(value)
                            print(f"  {key}: {value_type} (length: {length})")
                            
                            # Show nested structure for important fields
                            if key in ['card', 'techcard'] and isinstance(value, dict):
                                print(f"    └─ Nested keys: {list(value.keys())}")
                                
                                # Check for meta and ingredients
                                if 'meta' in value:
                                    meta = value['meta']
                                    if isinstance(meta, dict):
                                        print(f"      └─ meta keys: {list(meta.keys())}")
                                
                                if 'ingredients' in value:
                                    ingredients = value['ingredients']
                                    if isinstance(ingredients, list):
                                        print(f"      └─ ingredients count: {len(ingredients)}")
                                        if len(ingredients) > 0:
                                            print(f"      └─ first ingredient keys: {list(ingredients[0].keys()) if isinstance(ingredients[0], dict) else 'Not a dict'}")
                        else:
                            print(f"  {key}: {value_type} = {value}")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON Decode Error: {str(e)}")
                print(f"📄 Raw Response: {response.text[:500]}...")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {str(e)}")
        return False

if __name__ == "__main__":
    debug_v2_response()