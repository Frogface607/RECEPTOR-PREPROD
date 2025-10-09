#!/usr/bin/env python3
"""
БЫСТРЫЙ ТЕСТ AI-ДОПОЛНЕНИЙ С PRO ДЕМО ПОЛЬЗОВАТЕЛЕМ

Тестирование AI-дополнений после изменения демо пользователя на PRO план.
Проверяем что теперь возвращается 200 вместо 403.

Цель: Убедиться что 403 ошибки исправлены для демо пользователя с PRO планом.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com"

def log_test(message):
    """Log test message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_ai_generate_sales_script():
    """
    Тест основного AI-дополнения: POST /api/generate-sales-script
    Проверяем что demo_user теперь имеет PRO доступ
    """
    log_test("🎯 ТЕСТ 1: AI Generate Sales Script для demo_user")
    
    url = f"{BACKEND_URL}/api/generate-sales-script"
    
    # Payload из review request
    payload = {
        "user_id": "demo_user", 
        "tech_card": "**Название:** Тестовое блюдо\n\n**Ингредиенты:**\n- Мука: 200г\n- Яйца: 2шт\n\n**Приготовление:**\n1. Смешать ингредиенты\n2. Приготовить"
    }
    
    try:
        log_test(f"📤 POST {url}")
        log_test(f"📋 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        log_test(f"📥 Response: {response.status_code}")
        
        if response.status_code == 200:
            log_test("✅ SUCCESS: AI endpoint returns 200 - PRO access confirmed!")
            try:
                data = response.json()
                log_test(f"📄 Response data: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                return True
            except:
                log_test(f"📄 Response text: {response.text[:500]}...")
                return True
        elif response.status_code == 403:
            log_test("❌ FAIL: Still getting 403 - PRO upgrade not working")
            log_test(f"📄 Error: {response.text}")
            return False
        else:
            log_test(f"⚠️ UNEXPECTED: Status {response.status_code}")
            log_test(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        log_test(f"❌ ERROR: {str(e)}")
        return False

def test_subscription_status():
    """
    Проверка статуса подписки demo_user
    Убеждаемся что пользователь теперь считается PRO
    """
    log_test("🎯 ТЕСТ 2: Проверка статуса подписки demo_user")
    
    # Попробуем несколько возможных endpoints для проверки подписки
    possible_endpoints = [
        f"{BACKEND_URL}/api/user/demo_user",
        f"{BACKEND_URL}/api/user-profile/demo_user", 
        f"{BACKEND_URL}/api/subscription/demo_user",
        f"{BACKEND_URL}/api/user-status/demo_user"
    ]
    
    for endpoint in possible_endpoints:
        try:
            log_test(f"📤 GET {endpoint}")
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                log_test(f"✅ Found user endpoint: {endpoint}")
                try:
                    data = response.json()
                    log_test(f"📄 User data: {json.dumps(data, ensure_ascii=False, indent=2)}")
                    
                    # Ищем информацию о подписке
                    subscription_plan = data.get('subscription_plan', 'not_found')
                    if subscription_plan in ['pro', 'business']:
                        log_test(f"✅ SUCCESS: User has PRO subscription: {subscription_plan}")
                        return True
                    else:
                        log_test(f"❌ ISSUE: User subscription: {subscription_plan}")
                        
                except:
                    log_test(f"📄 Response text: {response.text}")
                    
            elif response.status_code == 404:
                log_test(f"⚠️ Endpoint not found: {endpoint}")
            else:
                log_test(f"⚠️ Status {response.status_code}: {endpoint}")
                
        except Exception as e:
            log_test(f"⚠️ Error accessing {endpoint}: {str(e)}")
    
    log_test("⚠️ Could not verify subscription status directly")
    return None

def test_additional_ai_endpoints():
    """
    Тест дополнительных AI endpoints для подтверждения PRO доступа
    """
    log_test("🎯 ТЕСТ 3: Дополнительные AI endpoints")
    
    ai_endpoints = [
        "/api/generate-food-pairing",
        "/api/generate-photo-tips", 
        "/api/generate-inspiration"
    ]
    
    base_payload = {
        "user_id": "demo_user",
        "tech_card": "**Название:** Тестовое блюдо\n\n**Ингредиенты:**\n- Мука: 200г\n- Яйца: 2шт"
    }
    
    success_count = 0
    total_count = len(ai_endpoints)
    
    for endpoint in ai_endpoints:
        try:
            url = f"{BACKEND_URL}{endpoint}"
            log_test(f"📤 POST {url}")
            
            response = requests.post(url, json=base_payload, timeout=20)
            
            if response.status_code == 200:
                log_test(f"✅ SUCCESS: {endpoint} returns 200")
                success_count += 1
            elif response.status_code == 403:
                log_test(f"❌ FAIL: {endpoint} still returns 403")
            else:
                log_test(f"⚠️ {endpoint} returns {response.status_code}")
                
        except Exception as e:
            log_test(f"❌ ERROR testing {endpoint}: {str(e)}")
    
    log_test(f"📊 AI Endpoints Success Rate: {success_count}/{total_count}")
    return success_count > 0

def test_backend_health():
    """
    Проверка общего состояния backend
    """
    log_test("🎯 ТЕСТ 0: Backend Health Check")
    
    try:
        url = f"{BACKEND_URL}/api/health"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            log_test("✅ Backend is healthy")
            return True
        else:
            log_test(f"⚠️ Backend health: {response.status_code}")
            
    except:
        # Try alternative health check
        try:
            url = f"{BACKEND_URL}/api/cities"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                log_test("✅ Backend is accessible")
                return True
        except:
            pass
            
    log_test("❌ Backend health check failed")
    return False

def main():
    """
    Основная функция тестирования
    """
    log_test("🚀 НАЧАЛО ТЕСТИРОВАНИЯ AI-ДОПОЛНЕНИЙ С PRO ДЕМО ПОЛЬЗОВАТЕЛЕМ")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    results = []
    
    # Тест 0: Backend Health
    results.append(("Backend Health", test_backend_health()))
    
    # Тест 1: Основной AI endpoint
    results.append(("AI Generate Sales Script", test_ai_generate_sales_script()))
    
    # Тест 2: Статус подписки
    subscription_result = test_subscription_status()
    results.append(("Subscription Status Check", subscription_result))
    
    # Тест 3: Дополнительные AI endpoints
    results.append(("Additional AI Endpoints", test_additional_ai_endpoints()))
    
    # Результаты
    log_test("=" * 80)
    log_test("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    
    passed = 0
    total = 0
    
    for test_name, result in results:
        if result is True:
            log_test(f"✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            log_test(f"❌ {test_name}: FAILED")
        else:
            log_test(f"⚠️ {test_name}: INCONCLUSIVE")
        total += 1
    
    log_test("=" * 80)
    log_test(f"🎯 ИТОГО: {passed}/{total} тестов пройдено")
    
    if passed >= 2:  # Backend health + основной AI endpoint
        log_test("🎉 УСПЕХ: AI-дополнения работают с PRO пользователем!")
        return True
    else:
        log_test("🚨 ПРОБЛЕМА: AI-дополнения все еще не работают")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)