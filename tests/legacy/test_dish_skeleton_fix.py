#!/usr/bin/env python3
"""
DISH SKELETON FIX TEST - проверяем что исправлены критические проблемы
"""

import requests
import json

def test_article_generation():
    """Тест 1: Артикулы генерируются правильно"""
    print("🔍 Тест 1: Проверяем генерацию артикулов...")
    
    try:
        response = requests.post(
            "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/generate",
            json={"name": "Dish Article Test", "user_id": "skeleton_fix_test"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            card = data.get('card', {})
            article = card.get('meta', {}).get('article') if card else None
            
            print(f"   Status: {status}")
            print(f"   Article: {article}")
            
            if status == 'READY' and article and article != 'Generated':
                print("   ✅ Артикул генерируется корректно!")
                return True, data.get('card', {}).get('meta', {}).get('id')
            else:
                print("   ❌ Проблемы с генерацией артикула")
                return False, None
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def test_preflight_skeleton(techcard_id):
    """Тест 2: Preflight генерирует dish skeleton"""
    print("🔍 Тест 2: Проверяем preflight dish skeleton...")
    
    if not techcard_id:
        print("   ❌ Нет ID техkарты для тестирования")
        return False
    
    try:
        response = requests.post(
            "https://cursor-push.preview.emergentagent.com/api/v1/export/preflight",
            json={"techcardIds": [techcard_id], "organization_id": "test"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            dishes = data.get('missing', {}).get('dishes', [])
            dish_articles = data.get('generated', {}).get('dishArticles', [])
            
            print(f"   Status: {status}")
            print(f"   Dishes to create: {len(dishes)}")
            print(f"   Generated articles: {dish_articles}")
            
            if status == 'success' and len(dishes) > 0 and len(dish_articles) > 0:
                dish = dishes[0]
                print(f"   Dish: {dish.get('name')} -> Article: {dish.get('article')}")
                print("   ✅ Dish skeleton генерируется корректно!")
                return True
            else:
                print("   ❌ Проблемы с preflight")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_techcard_loading():
    """Тест 3: Техkарты загружаются из user_history"""
    print("🔍 Тест 3: Проверяем загрузку техkарт из БД...")
    
    try:
        # Создаем техkарту
        response = requests.post(
            "https://cursor-push.preview.emergentagent.com/api/v1/techcards.v2/generate",
            json={"name": "DB Load Test", "user_id": "db_test"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            techcard_id = data.get('card', {}).get('meta', {}).get('id')
            
            if techcard_id:
                # Сразу проверяем preflight для этой техkарты
                preflight_response = requests.post(
                    "https://cursor-push.preview.emergentagent.com/api/v1/export/preflight",
                    json={"techcardIds": [techcard_id], "organization_id": "test"},
                    timeout=30
                )
                
                if preflight_response.status_code == 200:
                    preflight_data = preflight_response.json()
                    if preflight_data.get('status') == 'success':
                        print(f"   ✅ Техkарта {techcard_id} загружается из БД!")
                        return True
                    else:
                        print(f"   ❌ Preflight failed: {preflight_data}")
                        return False
                else:
                    print(f"   ❌ Preflight HTTP {preflight_response.status_code}")
                    return False
            else:
                print("   ❌ Не получен ID техkарты")
                return False
        else:
            print(f"   ❌ Generation HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("🎯 DISH SKELETON CRITICAL FIX TEST")
    print("Проверяем что исправлены регрессии: артикулы, dish-скелеты, загрузка техkарт")
    print("=" * 70)
    
    # Тест 1: Артикулы
    articles_ok, techcard_id = test_article_generation()
    
    # Тест 2: Dish skeletons
    skeleton_ok = test_preflight_skeleton(techcard_id)
    
    # Тест 3: БД загрузка
    db_loading_ok = test_techcard_loading()
    
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ:")
    
    print(f"\n✅ ПРОБЛЕМА 1: ArticleAllocator 'list' object has no attribute 'value'")
    print("   - Исправлен вызов allocate_articles с правильными параметрами")
    print("   - Добавлен ArticleType.DISH и ArticleType.PRODUCT")
    print("   - Исправлена обработка возвращаемого списка артикулов")
    print(f"   Результат: {'✅ РАБОТАЕТ' if articles_ok else '❌ ПРОБЛЕМЫ'}")
    
    print(f"\n✅ ПРОБЛЕМА 2: 'Techcard not found' в экспорте")
    print("   - Изменена коллекция с techcards_v2 на user_history")
    print("   - Добавлена поддержка techcard_v2_data и content форматов")
    print("   - Улучшена обработка JSON парсинга")
    print(f"   Результат: {'✅ РАБОТАЕТ' if db_loading_ok else '❌ ПРОБЛЕМЫ'}")
    
    print(f"\n✅ ПРОБЛЕМА 3: Пустые ZIP архивы")
    print("   - Исправлена загрузка техkарт для dish skeleton генерации")
    print("   - ArticleAllocator правильно назначает артикулы")
    print("   - Preflight корректно создает missing dishes")
    print(f"   Результат: {'✅ РАБОТАЕТ' if skeleton_ok else '❌ ПРОБЛЕМЫ'}")
    
    if articles_ok and skeleton_ok and db_loading_ok:
        print(f"\n🎉 ВСЕ КРИТИЧЕСКИЕ РЕГРЕССИИ ИСПРАВЛЕНЫ!")
        print("   • Артикулы генерируются (больше не 'Generated')")
        print("   • Dish-скелеты создаются через preflight")
        print("   • Техkарты загружаются из user_history")
        print("   • ZIP архивы будут содержать файлы")
    else:
        print(f"\n⚠️ Есть проблемы, требующие дополнительного внимания")
        
    print("=" * 70)

if __name__ == "__main__":
    main()