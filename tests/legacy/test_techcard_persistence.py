#!/usr/bin/env python3
"""
CLEANUP TECH CARD DATA & UI - Test Tech Card Persistence
Проверяем что техкарты сохраняются с user_id и доступны через API
"""

import requests
import json
import time
import os
from pymongo import MongoClient

# URLs
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# MongoDB connection (for direct validation)
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')

def test_techcard_generation_and_storage():
    """Тестируем генерацию и сохранение техkарты"""
    print("🔍 Тестируем генерацию и сохранение техkарты...")
    
    test_user_id = "test_cleanup_user_123"
    test_dish = "Борщ украинский тестовый"
    
    # 1. Генерируем техkарту
    print(f"   Генерируем техkарту: {test_dish}")
    try:
        response = requests.post(
            f"{API_BASE}/v1/techcards.v2/generate",
            json={
                "name": test_dish,
                "user_id": test_user_id
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            card = data.get('card', {})
            card_id = card.get('meta', {}).get('id') if card else None
            
            print(f"      ✅ Техkарта сгенерирована - Status: {status}, ID: {card_id}")
            
            if status == "READY" and card_id:
                return test_user_id, card_id, test_dish
            else:
                print(f"      ❌ Проблема с генерацией - Status: {status}, Card: {bool(card)}")
                return None, None, None
        else:
            print(f"      ❌ HTTP {response.status_code}")
            return None, None, None
            
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None, None, None

def test_user_history_api(user_id):
    """Тестируем API получения истории пользователя"""
    print(f"🔍 Тестируем API user-history для user_id: {user_id}")
    
    try:
        response = requests.get(
            f"{API_BASE}/user-history/{user_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            history = data.get('history', [])
            
            print(f"      ✅ API ответил - История содержит {len(history)} записей")
            
            # Показываем последние записи
            for i, record in enumerate(history[:3]):
                dish_name = record.get('dish_name', 'Unknown')
                created_at = record.get('created_at', 'Unknown')
                is_menu = record.get('is_menu', False)
                status = record.get('status', 'Unknown')
                print(f"         {i+1}. {dish_name} ({status}) - {'Menu' if is_menu else 'TechCard'} - {created_at}")
            
            return len(history)
        else:
            print(f"      ❌ API error: HTTP {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"      ❌ API error: {e}")
        return 0

def test_database_direct_check(user_id, expected_dish_name):
    """Прямая проверка базы данных"""
    print(f"🔍 Прямая проверка MongoDB для user_id: {user_id}")
    
    try:
        client = MongoClient(MONGO_URL)
        db = client.receptor_pro  # Правильное имя базы из .env
        
        # Проверяем коллекцию user_history
        user_history_count = db.user_history.count_documents({"user_id": user_id})
        print(f"      📊 user_history коллекция: {user_history_count} записей для user_id")
        
        # Ищем нашу тестовую техkарту
        test_record = db.user_history.find_one({
            "user_id": user_id,
            "dish_name": expected_dish_name,
            "is_menu": False
        })
        
        if test_record:
            print(f"      ✅ Найдена тестовая техkарта: {test_record.get('dish_name')}")
            print(f"         ID: {test_record.get('id')}")
            print(f"         Status: {test_record.get('status')}")
            print(f"         Created: {test_record.get('created_at')}")
            return True
        else:
            print(f"      ❌ Тестовая техkарта НЕ найдена в БД")
            
            # Показываем что есть в БД для этого пользователя
            all_records = list(db.user_history.find({"user_id": user_id}).limit(5))
            print(f"         Всего записей для пользователя: {len(all_records)}")
            for record in all_records:
                print(f"         - {record.get('dish_name')} ({record.get('status', 'no status')})")
            
            return False
            
        client.close()
        
    except Exception as e:
        print(f"      ❌ Database error: {e}")
        return False

def main():
    print("=" * 70)
    print("🎯 CLEANUP TECH CARD DATA & UI - Tech Card Persistence Test")
    print("=" * 70)
    
    # Тест 1: Генерация техkарты
    user_id, card_id, dish_name = test_techcard_generation_and_storage()
    
    if not user_id:
        print("❌ Генерация не удалась, дальнейшие тесты невозможны")
        return
    
    # Небольшая пауза для сохранения в БД
    print("   ⏳ Пауза 3 секунды для сохранения в БД...")
    time.sleep(3)
    
    # Тест 2: API user-history
    history_count = test_user_history_api(user_id)
    
    # Тест 3: Прямая проверка БД
    db_found = test_database_direct_check(user_id, dish_name)
    
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Генерация техkарты: {'OK' if card_id else 'FAIL'}")
    print(f"✅ API user-history: {'OK' if history_count > 0 else 'FAIL'} ({history_count} записей)")
    print(f"✅ База данных: {'OK' if db_found else 'FAIL'}")
    
    if card_id and history_count > 0 and db_found:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Техkарты сохраняются корректно.")
        print("✅ CLEANUP TECH CARD DATA & UI: Проблема persistence ИСПРАВЛЕНА!")
    else:
        print("\n⚠️ Есть проблемы с сохранением техkарт.")
        print("❌ Требуется дополнительная отладка.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()