#!/usr/bin/env python3
"""
Debug script to examine menu generation response structure
"""

import requests
import json

BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def debug_menu_structure():
    user_id = "505d1cb4-4ed3-460a-ad25-3608b58cbf24"  # Existing PRO user
    
    menu_request = {
        "user_id": user_id,
        "menu_profile": {
            "menuType": "restaurant",
            "dishCount": 8,  # Smaller number for debugging
            "averageCheck": "high",
            "cuisineStyle": "european",
            "targetAudience": "gourmet"
        },
        "venue_profile": {
            "venue_name": "Debug Restaurant",
            "venue_type": "fine_dining",
            "cuisine_type": "european"
        }
    }
    
    print("🔍 Отправка запроса на генерацию меню для отладки...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/generate-menu", json=menu_request, timeout=120)
        
        if response.status_code == 200:
            menu_data = response.json()
            print("✅ Меню сгенерировано успешно")
            print("\n📋 ПОЛНАЯ СТРУКТУРА ОТВЕТА:")
            print(json.dumps(menu_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    debug_menu_structure()