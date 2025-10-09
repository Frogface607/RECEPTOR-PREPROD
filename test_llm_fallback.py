#!/usr/bin/env python3
"""
Test LLM Fallback Mechanism by temporarily disabling OpenAI API
"""

import os
import requests
import json
import time

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_llm_fallback():
    """Test fallback mechanism when LLM is unavailable"""
    print("🔄 Testing LLM fallback mechanism...")
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8'
    })
    
    # Test with a simple dish
    test_dish = "Простое тестовое блюдо"
    
    try:
        response = session.post(
            f"{API_BASE}/v1/techcards.v2/generate",
            json={"name": test_dish},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response data keys: {list(data.keys())}")
                
                status = data.get('status')
                print(f"Status: {status}")
                
                card = data.get('card')
                if card:
                    print(f"Card keys: {list(card.keys())}")
                    
                    # Check skeleton structure
                    portions = card.get('portions', 0)
                    yield_info = card.get('yield', {})
                    ingredients = card.get('ingredients', [])
                    process = card.get('process', [])
                    
                    print(f"Portions: {portions}")
                    print(f"Yield: {yield_info}")
                    print(f"Ingredients count: {len(ingredients)}")
                    print(f"Process steps: {len(process)}")
                    
                    if process:
                        print(f"First process step: {process[0]}")
                
                issues = data.get('issues', [])
                print(f"Issues count: {len(issues)}")
                for i, issue in enumerate(issues):
                    if isinstance(issue, dict):
                        print(f"  Issue {i}: {issue.get('type')} - {issue.get('level')} - {issue.get('message', '')}")
                    else:
                        print(f"  Issue {i}: {issue} (type: {type(issue)})")
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Raw response: {response.text[:500]}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_llm_fallback()