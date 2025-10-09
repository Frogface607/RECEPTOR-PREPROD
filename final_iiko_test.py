#!/usr/bin/env python3
"""
ОКОНЧАТЕЛЬНОЕ ТЕСТИРОВАНИЕ: IIKo Integration - Create Product/Dish с минимальной корректной структурой

ЗАДАЧИ ДЛЯ ОКОНЧАТЕЛЬНОГО ТЕСТИРОВАНИЯ:
1. Протестируй минимальную структуру `/api/iiko/products/create-complete-dish`
2. Проверь, что НЕТ ошибок "Unrecognized field measureUnit/code/price"
3. Подтверди прогресс: HTTP 200 response и success: true для dish_product
4. Если все работает - это РЕШЕНИЕ основной проблемы!
"""

import requests
import json
import time
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test(message):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_create_complete_dish_minimal():
    """Test POST /api/iiko/products/create-complete-dish with minimal structure"""
    log_test("🍽️ ОКОНЧАТЕЛЬНОЕ ТЕСТИРОВАНИЕ: Минимальная структура DISH")
    
    # Test data as specified in review request
    test_data = {
        "name": "Минимальное тестовое блюдо",
        "organization_id": "default-org-001", 
        "description": "Тест минимальной структуры только с known properties",
        "ingredients": [{"name": "Мука", "quantity": 100, "unit": "г"}],
        "preparation_steps": ["Минимальный тест"],
        "weight": 200.0,
        "price": 300.0
    }
    
    log_test(f"📝 Test dish: {test_data['name']}")
    log_test(f"📋 Organization: {test_data['organization_id']}")
    log_test(f"🥬 Ingredients: {test_data['ingredients']}")
    log_test(f"⚖️ Weight: {test_data['weight']}г")
    log_test(f"💰 Price: {test_data['price']}₽")
    
    log_test("\n🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:")
    log_test("✅ HTTP 200 response")
    log_test("✅ НЕТ ошибок 'Unrecognized field measureUnit'")
    log_test("✅ НЕТ ошибок 'Unrecognized field code'")
    log_test("✅ НЕТ ошибок 'Unrecognized field price'")
    log_test("✅ success: true для dish_product")
    log_test("✅ Дошло дальше в процессе создания DISH")
    
    try:
        url = f"{API_BASE}/iiko/products/create-complete-dish"
        log_test(f"\n🌐 Making request to: {url}")
        
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=60)
        response_time = time.time() - start_time
        
        log_test(f"📊 Response status: {response.status_code}")
        log_test(f"⏱️ Response time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            log_test("✅ HTTP 200 - Request successful!")
            
            # Print full response for analysis
            log_test("\n📋 ПОЛНЫЙ ОТВЕТ ОТ BACKEND:")
            log_test(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Analyze specific sections
            log_test("\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ОТВЕТА:")
            
            # Check overall success
            if 'success' in data:
                log_test(f"📊 Overall success: {data['success']}")
            
            # Check assembly chart
            if 'assembly_chart' in data:
                assembly = data['assembly_chart']
                log_test(f"\n🔨 ASSEMBLY CHART:")
                log_test(f"   - Success: {assembly.get('success', 'Unknown')}")
                if assembly.get('success'):
                    log_test(f"   - ID: {assembly.get('assembly_chart_id', 'Unknown')}")
                    log_test(f"   - Name: {assembly.get('name', 'Unknown')}")
                else:
                    log_test(f"   - Error: {assembly.get('error', 'Unknown')}")
            
            # Check dish product - CRITICAL
            if 'dish_product' in data:
                dish = data['dish_product']
                log_test(f"\n🍽️ DISH PRODUCT (КРИТИЧЕСКИЙ ТЕСТ):")
                log_test(f"   - Success: {dish.get('success', 'Unknown')}")
                
                if dish.get('success'):
                    log_test(f"   🎉 DISH PRODUCT СОЗДАН УСПЕШНО!")
                    log_test(f"   - Product ID: {dish.get('product_id', 'Unknown')}")
                    log_test(f"   - Product Name: {dish.get('product_name', 'Unknown')}")
                    log_test(f"   - Product Type: {dish.get('product_type', 'Unknown')}")
                    log_test(f"   - Category ID: {dish.get('category_id', 'Unknown')}")
                    log_test(f"   - Message: {dish.get('message', 'No message')}")
                else:
                    log_test(f"   ❌ DISH PRODUCT FAILED")
                    error_msg = dish.get('error', 'Unknown error')
                    log_test(f"   - Error: {error_msg}")
                    
                    # Check for structure errors
                    log_test(f"\n🚨 ПРОВЕРКА СТРУКТУРНЫХ ОШИБОК:")
                    if 'Unrecognized field measureUnit' in error_msg:
                        log_test(f"   ❌ measureUnit field error (должно быть убрано)")
                    else:
                        log_test(f"   ✅ NO measureUnit error")
                    
                    if 'Unrecognized field code' in error_msg:
                        log_test(f"   ❌ code field error (должно быть 'num')")
                    else:
                        log_test(f"   ✅ NO code error")
                    
                    if 'Unrecognized field price' in error_msg:
                        log_test(f"   ❌ price field error (должно быть 'defaultSalePrice')")
                    else:
                        log_test(f"   ✅ NO price error")
                    
                    if 'dish is not a valid enum value' in error_msg.lower():
                        log_test(f"   ❌ Case sensitivity error (должно быть 'DISH')")
                    else:
                        log_test(f"   ✅ NO case sensitivity error")
            
            # Check category
            if 'category' in data:
                category = data['category']
                log_test(f"\n📂 CATEGORY:")
                log_test(f"   - Category ID: {category.get('category_id', 'Unknown')}")
                log_test(f"   - Category Name: {category.get('category_name', 'Unknown')}")
                log_test(f"   - Status: {category.get('status', 'Unknown')}")
            
            # Final assessment
            dish_success = data.get('dish_product', {}).get('success', False)
            assembly_success = data.get('assembly_chart', {}).get('success', False)
            
            log_test(f"\n🎯 ОКОНЧАТЕЛЬНАЯ ОЦЕНКА:")
            log_test(f"✅ HTTP 200 response: ДА")
            log_test(f"✅ DISH product success: {'ДА' if dish_success else 'НЕТ'}")
            log_test(f"✅ Assembly chart success: {'ДА' if assembly_success else 'НЕТ'}")
            
            if dish_success:
                log_test(f"\n🎉 ОКОНЧАТЕЛЬНЫЙ УСПЕХ!")
                log_test(f"✅ Минимальная структура работает")
                log_test(f"✅ DISH продукты создаются")
                log_test(f"✅ Блюда должны появляться в меню IIKo")
                log_test(f"✅ ПРОБЛЕМА РЕШЕНА!")
                
                return {
                    'success': True,
                    'dish_success': True,
                    'assembly_success': assembly_success,
                    'data': data,
                    'final_result': 'SUCCESS - Problem solved!'
                }
            else:
                log_test(f"\n⚠️ ЧАСТИЧНЫЙ УСПЕХ:")
                log_test(f"✅ HTTP 200 достигнут")
                log_test(f"❌ DISH creation все еще не работает")
                
                return {
                    'success': True,  # HTTP 200 is progress
                    'dish_success': False,
                    'assembly_success': assembly_success,
                    'data': data,
                    'final_result': 'PARTIAL - HTTP 200 but DISH creation failed'
                }
            
        else:
            log_test(f"❌ Request failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log_test(f"📋 Error details: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                log_test(f"📋 Raw error response: {response.text[:500]}")
            
            return {
                'success': False,
                'dish_success': False,
                'error': f"HTTP {response.status_code}",
                'response': response.text,
                'final_result': 'FAILED - HTTP error'
            }
            
    except Exception as e:
        log_test(f"❌ Error testing dish creation: {str(e)}")
        return {
            'success': False,
            'dish_success': False,
            'error': str(e),
            'final_result': 'FAILED - Exception'
        }

def main():
    """Main testing function"""
    log_test("🚀 ОКОНЧАТЕЛЬНОЕ ТЕСТИРОВАНИЕ: IIKo Integration - Create Product/Dish")
    log_test("🎯 Focus: Минимальная корректная структура с исправлениями")
    log_test(f"🌐 Backend URL: {BACKEND_URL}")
    log_test("=" * 80)
    
    # Test the minimal structure
    result = test_create_complete_dish_minimal()
    
    # Summary
    log_test("\n" + "=" * 80)
    log_test("📋 ОКОНЧАТЕЛЬНОЕ ТЕСТИРОВАНИЕ SUMMARY:")
    log_test(f"✅ HTTP Response: {'SUCCESS' if result.get('success') else 'FAILED'}")
    log_test(f"✅ DISH Creation: {'SUCCESS' if result.get('dish_success') else 'FAILED'}")
    log_test(f"✅ Assembly Chart: {'SUCCESS' if result.get('assembly_success') else 'FAILED'}")
    
    log_test(f"\n🎯 FINAL RESULT: {result.get('final_result', 'UNKNOWN')}")
    
    if result.get('dish_success'):
        log_test("\n🎉 ОКОНЧАТЕЛЬНОЕ ТЕСТИРОВАНИЕ УСПЕШНО!")
        log_test("✅ Минимальная корректная структура работает")
        log_test("✅ Блюда создаются в IIKo с правильной структурой")
        log_test("✅ Нет ошибок 'Unrecognized field'")
        log_test("✅ HTTP 200 response и success: true достигнуты")
        log_test("🎊 ПРОБЛЕМА РЕШЕНА - DISH продукты теперь создаются!")
    elif result.get('success'):
        log_test("\n✅ ПРОГРЕСС ДОСТИГНУТ!")
        log_test("✅ HTTP 200 response получен")
        log_test("⚠️ DISH creation все еще имеет проблемы")
        log_test("💡 Требуется дополнительная отладка")
    else:
        log_test("\n❌ Тестирование выявило проблемы:")
        if 'error' in result:
            log_test(f"   - Error: {result['error']}")
        log_test("💡 Требуется исправление backend кода")
    
    log_test("=" * 80)
    
    return result

if __name__ == "__main__":
    main()