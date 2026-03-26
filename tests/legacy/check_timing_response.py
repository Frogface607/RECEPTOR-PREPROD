#!/usr/bin/env python3
"""
Check timing instrumentation in TechCardV2 response
"""

import os
import requests
import json

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def check_timing_response():
    """Check timing instrumentation in response"""
    print("🔄 Checking timing instrumentation...")
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8'
    })
    
    # Test with a simple dish
    test_dish = "Борщ украинский"
    
    try:
        response = session.post(
            f"{API_BASE}/v1/techcards.v2/generate",
            json={"name": test_dish},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("Full response structure:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            card = data.get('card')
            if card:
                meta = card.get('meta', {})
                timings = meta.get('timings', {})
                
                print(f"\nMeta keys: {list(meta.keys())}")
                print(f"Timings keys: {list(timings.keys())}")
                print(f"Timings content: {timings}")
                
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_timing_response()