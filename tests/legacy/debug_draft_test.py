#!/usr/bin/env python3
"""
Debug draft test
"""

import requests
import json

BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def create_draft_techcard():
    """Create draft TechCardV2 with validation issues"""
    return {
        "meta": {
            "title": "Draft Card",
            "version": "2.0"
        },
        "portions": 1,
        "yield": {
            "perPortion_g": 100.0,
            "perBatch_g": 200.0  # Mismatch with ingredients to trigger validation failure
        },
        "ingredients": [
            {
                "name": "Test Ingredient",
                "unit": "g",
                "brutto_g": 100.0,
                "loss_pct": 0.0,
                "netto_g": 100.0
            }
        ],
        "process": [
            {
                "n": 1,
                "action": "Step 1"
            },
            {
                "n": 2,
                "action": "Step 2"
            },
            {
                "n": 3,
                "action": "Step 3"
            }
        ],
        "storage": {
            "conditions": "Test storage",
            "shelfLife_hours": 24.0
        }
    }

def test_draft():
    """Test the print endpoint with draft card"""
    test_card = create_draft_techcard()
    
    print("Testing print endpoint with draft card...")
    print(f"Request data: {json.dumps(test_card, indent=2)}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/v1/techcards.v2/print",
            json=test_card,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! HTML generated")
            html = response.text
            print(f"HTML length: {len(html)} characters")
            has_watermark = 'ЧЕРНОВИК' in html
            print(f"Has watermark: {has_watermark}")
            if has_watermark:
                print("Watermark found in HTML!")
            else:
                print("No watermark found")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print("Response text:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_draft()