#!/usr/bin/env python3
"""
Simple Inspiration Endpoint Test
Exactly as requested in the review

ПРОСТОЙ ТЕСТ:
- Endpoint: `/api/generate-inspiration` 
- Данные: {"tech_card": {"name": "Борщ"}, "user_id": "demo_user"}

ЦЕЛЬ: Просто проверить отвечает ли endpoint
"""

import requests
import json
import time

def test_inspiration_simple():
    """Test with exact data from review request"""
    
    # Backend URL
    base_url = "https://cursor-push.preview.emergentagent.com/api"
    
    print("🎯 ПРОСТОЙ ТЕСТ ENDPOINT ВДОХНОВЕНИЯ")
    print("=" * 50)
    print(f"Endpoint: /api/generate-inspiration")
    print("=" * 50)
    
    # Exact test data from review request
    test_data = {
        "tech_card": {"name": "Борщ"},
        "user_id": "demo_user"
    }
    
    print(f"📤 Отправляем запрос:")
    print(f"   URL: {base_url}/generate-inspiration")
    print(f"   Данные: {json.dumps(test_data, ensure_ascii=False)}")
    print()
    
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/generate-inspiration", json=test_data, timeout=60)
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"📥 Ответ получен за {response_time:.2f} секунд")
        print(f"📥 Статус код: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ УСПЕХ: Endpoint отвечает!")
            
            try:
                data = response.json()
                inspiration = data.get('inspiration', '')
                print(f"✅ Получен контент вдохновения: {len(inspiration)} символов")
                
                # Show preview
                print("\n📋 ПРЕВЬЮ КОНТЕНТА:")
                print("-" * 40)
                preview = inspiration[:300] + "..." if len(inspiration) > 300 else inspiration
                print(preview)
                print("-" * 40)
                
                return True
                
            except json.JSONDecodeError:
                print(f"❌ ОШИБКА: Неверный JSON ответ")
                print(f"Сырой ответ: {response.text[:200]}")
                return False
                
        else:
            print(f"❌ ОШИБКА: HTTP {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ОШИБКА: Таймаут запроса (60 секунд)")
        return False
        
    except Exception as e:
        print(f"❌ ОШИБКА: {str(e)}")
        return False

if __name__ == "__main__":
    print("Простой тест endpoint вдохновения")
    print("Как запрошено в review request")
    print()
    
    success = test_inspiration_simple()
    
    print("\n" + "=" * 50)
    print("🎯 РЕЗУЛЬТАТ ТЕСТА")
    print("=" * 50)
    
    if success:
        print("🎉 ENDPOINT РАБОТАЕТ!")
        print("✅ /api/generate-inspiration отвечает корректно")
        print("✅ Данные: {\"tech_card\": {\"name\": \"Борщ\"}, \"user_id\": \"demo_user\"}")
        print("✅ Цель достигнута: endpoint отвечает")
    else:
        print("🚨 ENDPOINT НЕ РАБОТАЕТ!")
        print("❌ Проблема с /api/generate-inspiration")
    
    exit(0 if success else 1)