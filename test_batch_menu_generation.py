"""
Тестирование новых endpoints батчевой генерации меню
"""
import requests
import json
import time
import sys
import io
from datetime import datetime

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Конфигурация
BACKEND_URL = "http://localhost:8000/api"
TEST_USER_ID = "test_user_batch_menu"

def log_test(message, status="INFO"):
    """Логирование тестов"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    emoji = "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "🔍"
    print(f"[{timestamp}] {emoji} {message}")

def test_menu_generation():
    """Тест 1: Генерация тестового меню"""
    log_test("ТЕСТ 1: Генерация тестового меню")
    
    menu_request = {
        "user_id": TEST_USER_ID,
        "menu_profile": {
            "menuType": "restaurant",
            "dishCount": 6,  # Небольшое меню для теста
            "averageCheck": "800-1200",
            "cuisineStyle": "european",
            "useConstructor": True,
            "categories": {
                "salads": 2,
                "soups": 1,
                "main_dishes": 2,
                "desserts": 1
            }
        },
        "venue_profile": {
            "venue_name": "Тестовый ресторан",
            "venue_type": "family_restaurant",
            "cuisine_type": "европейская",
            "average_check": "800-1200"
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate-menu",
            json=menu_request,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                menu_id = data.get("menu_id")
                log_test(f"✅ Меню успешно создано! ID: {menu_id}", "SUCCESS")
                return menu_id
            else:
                log_test(f"❌ Ошибка генерации: {data.get('error')}", "ERROR")
                return None
        elif response.status_code == 403:
            log_test("⚠️ Требуется PRO подписка. Используем demo_user", "INFO")
            # Попробуем с demo_user
            menu_request["user_id"] = "demo_user"
            response = requests.post(
                f"{BACKEND_URL}/generate-menu",
                json=menu_request,
                timeout=120
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    menu_id = data.get("menu_id")
                    log_test(f"✅ Меню создано с demo_user! ID: {menu_id}", "SUCCESS")
                    return menu_id, "demo_user"
            return None
        else:
            log_test(f"❌ HTTP {response.status_code}: {response.text}", "ERROR")
            return None
            
    except Exception as e:
        log_test(f"❌ Ошибка: {str(e)}", "ERROR")
        return None

def test_parse_menu_items(menu_id, user_id=None):
    """Тест 2: Парсинг меню на позиции"""
    log_test("ТЕСТ 2: Парсинг меню на позиции")
    
    if user_id is None:
        user_id = TEST_USER_ID
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/menu/{menu_id}/parse-items",
            params={"user_id": user_id},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                items = data.get("items", [])
                log_test(f"✅ Парсинг успешен! Найдено позиций: {len(items)}", "SUCCESS")
                
                # Показываем первые 3 позиции
                for i, item in enumerate(items[:3]):
                    log_test(f"  {i+1}. {item.get('name')} (ID: {item.get('id')[:8]}...)")
                    log_test(f"     Категория: {item.get('category')}")
                    log_test(f"     Статус V1: {'✅' if item.get('metadata', {}).get('converted_to_v1') else '⚪'}")
                    log_test(f"     Статус V2: {'✅' if item.get('metadata', {}).get('converted_to_v2') else '⚪'}")
                
                return items
            else:
                log_test(f"❌ Ошибка парсинга: {data.get('error')}", "ERROR")
                return None
        else:
            log_test(f"❌ HTTP {response.status_code}: {response.text}", "ERROR")
            return None
            
    except Exception as e:
        log_test(f"❌ Ошибка: {str(e)}", "ERROR")
        return None

def test_convert_item_to_v1(menu_id, item_id, user_id=None):
    """Тест 3: Конвертация позиции в V1"""
    log_test("ТЕСТ 3: Конвертация позиции в V1 рецепт")
    
    if user_id is None:
        user_id = TEST_USER_ID
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/menu/{menu_id}/items/{item_id}/convert",
            json={
                "user_id": user_id,
                "target_format": "v1",
                "options": {
                    "generate_techcard": True,
                    "save_to_history": True
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                recipe_id = data.get("recipe_id")
                content_preview = data.get("content", "")[:100] + "..."
                log_test(f"✅ V1 рецепт создан! ID: {recipe_id}", "SUCCESS")
                log_test(f"   Превью: {content_preview}")
                return recipe_id
            else:
                log_test(f"❌ Ошибка конвертации: {data.get('error')}", "ERROR")
                return None
        else:
            log_test(f"❌ HTTP {response.status_code}: {response.text}", "ERROR")
            return None
            
    except Exception as e:
        log_test(f"❌ Ошибка: {str(e)}", "ERROR")
        return None

def test_convert_item_to_v2(menu_id, item_id, user_id=None):
    """Тест 4: Конвертация позиции в V2"""
    log_test("ТЕСТ 4: Конвертация позиции в V2 техкарту")
    
    if user_id is None:
        user_id = TEST_USER_ID
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/menu/{menu_id}/items/{item_id}/convert",
            json={
                "user_id": user_id,
                "target_format": "v2",
                "options": {
                    "generate_techcard": True,
                    "save_to_history": True
                }
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                techcard_id = data.get("techcard_id")
                techcard = data.get("techcard", {})
                name = techcard.get("meta", {}).get("name", "N/A")
                log_test(f"✅ V2 техкарта создана! ID: {techcard_id}", "SUCCESS")
                log_test(f"   Название: {name}")
                return techcard_id
            else:
                log_test(f"❌ Ошибка конвертации: {data.get('error')}", "ERROR")
                return None
        else:
            log_test(f"❌ HTTP {response.status_code}: {response.text}", "ERROR")
            return None
            
    except Exception as e:
        log_test(f"❌ Ошибка: {str(e)}", "ERROR")
        return None

def test_batch_convert(menu_id, item_ids, user_id=None):
    """Тест 5: Батчевая конвертация"""
    log_test(f"ТЕСТ 5: Батчевая конвертация {len(item_ids)} позиций в V1")
    
    if user_id is None:
        user_id = TEST_USER_ID
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/menu/{menu_id}/items/batch-convert",
            json={
                "user_id": user_id,
                "item_ids": item_ids,
                "target_format": "v1",
                "options": {
                    "generate_techcard": True,
                    "save_to_history": True
                }
            },
            timeout=300  # 5 минут для батчевой операции
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                successful = data.get("successful", 0)
                failed = data.get("failed", 0)
                log_test(f"✅ Батчевая конвертация завершена за {elapsed:.1f}с!", "SUCCESS")
                log_test(f"   Успешно: {successful}, Ошибок: {failed}")
                return True
            else:
                log_test(f"❌ Ошибка: {data.get('error')}", "ERROR")
                return False
        else:
            log_test(f"❌ HTTP {response.status_code}: {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ Ошибка: {str(e)}", "ERROR")
        return False

def test_parse_after_conversion(menu_id, user_id=None):
    """Тест 6: Проверка статуса после конвертации"""
    log_test("ТЕСТ 6: Проверка статуса конвертации после операций")
    
    if user_id is None:
        user_id = TEST_USER_ID
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/menu/{menu_id}/parse-items",
            params={"user_id": user_id},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            v1_count = sum(1 for item in items if item.get("metadata", {}).get("converted_to_v1"))
            v2_count = sum(1 for item in items if item.get("metadata", {}).get("converted_to_v2"))
            
            log_test(f"✅ Статус обновлен!", "SUCCESS")
            log_test(f"   Всего позиций: {len(items)}")
            log_test(f"   Конвертировано в V1: {v1_count}")
            log_test(f"   Конвертировано в V2: {v2_count}")
            
            return True
        else:
            log_test(f"❌ HTTP {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ Ошибка: {str(e)}", "ERROR")
        return False

def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ БАТЧЕВОЙ ГЕНЕРАЦИИ МЕНЮ")
    print("=" * 60)
    print()
    
    # Проверка доступности backend
    try:
        # Пробуем несколько вариантов health check
        health_urls = [
            f"{BACKEND_URL.replace('/api', '')}/health",
            "http://localhost:8000/health",
            "http://127.0.0.1:8000/health"
        ]
        
        backend_available = False
        for url in health_urls:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    log_test(f"✅ Backend доступен на {url}", "SUCCESS")
                    backend_available = True
                    break
            except:
                continue
        
        if not backend_available:
            log_test("⚠️ Backend не отвечает на /health, но продолжаем тесты...", "INFO")
            log_test("   Убедитесь, что сервер запущен: cd backend && python -m uvicorn server:app --port 8000", "INFO")
    except Exception as e:
        log_test(f"⚠️ Ошибка проверки backend: {str(e)}", "INFO")
        log_test("   Продолжаем тесты...", "INFO")
    
    print()
    
    # Тест 1: Генерация меню
    result = test_menu_generation()
    if result is None:
        log_test("❌ Не удалось создать меню. Тесты остановлены.", "ERROR")
        return
    
    if isinstance(result, tuple):
        menu_id, user_id = result
    else:
        menu_id = result
        user_id = TEST_USER_ID
    
    print()
    time.sleep(2)
    
    # Тест 2: Парсинг позиций
    items = test_parse_menu_items(menu_id, user_id)
    if items is None or len(items) == 0:
        log_test("❌ Не удалось распарсить меню. Тесты остановлены.", "ERROR")
        return
    
    print()
    time.sleep(1)
    
    # Тест 3: Конвертация первой позиции в V1
    if len(items) > 0:
        first_item_id = items[0].get("id")
        test_convert_item_to_v1(menu_id, first_item_id, user_id)
        print()
        time.sleep(2)
    
    # Тест 4: Конвертация второй позиции в V2
    if len(items) > 1:
        second_item_id = items[1].get("id")
        test_convert_item_to_v2(menu_id, second_item_id, user_id)
        print()
        time.sleep(2)
    
    # Тест 5: Батчевая конвертация (оставшиеся позиции)
    if len(items) > 2:
        remaining_ids = [item.get("id") for item in items[2:4]]  # Берем 2 позиции для теста
        test_batch_convert(menu_id, remaining_ids, user_id)
        print()
        time.sleep(2)
    
    # Тест 6: Проверка финального статуса
    test_parse_after_conversion(menu_id, user_id)
    
    print()
    print("=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
    print(f"📋 Menu ID для дальнейших тестов: {menu_id}")
    print(f"👤 User ID: {user_id}")

if __name__ == "__main__":
    main()

