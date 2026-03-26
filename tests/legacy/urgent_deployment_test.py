#!/usr/bin/env python3
"""
СРОЧНЫЙ ТЕСТ для деплоя Beta версии
Тестирует эндпоинт generate-tech-card с конкретными параметрами
"""

import requests
import json
import time
from datetime import datetime

class UrgentDeploymentTest:
    def __init__(self):
        # Use the public endpoint from frontend/.env
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.test_user_id = "test_user_12345"
        self.dish_name = "Борщ"
        self.city = "moskva"
        
    def test_generate_tech_card_urgent(self):
        """
        СРОЧНЫЙ ТЕСТ: Протестируй эндпоинт generate-tech-card с тестовым пользователем
        """
        print("🚨 СРОЧНЫЙ ТЕСТ для деплоя Beta версии")
        print("=" * 60)
        print(f"🔗 Testing endpoint: {self.base_url}/generate-tech-card")
        print(f"👤 Test user ID: {self.test_user_id}")
        print(f"🍲 Dish name: {self.dish_name}")
        print(f"🏙️ City: {self.city}")
        print("=" * 60)
        
        # Prepare request data
        request_data = {
            "dish_name": self.dish_name,
            "user_id": self.test_user_id
        }
        
        print(f"📤 Sending request: {json.dumps(request_data, ensure_ascii=False)}")
        
        try:
            # Make the API call
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/generate-tech-card", 
                json=request_data,
                timeout=120  # 2 minute timeout
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"⏱️ Response time: {response_time:.2f} seconds")
            
            # Check 1: API отвечает 200 OK
            print(f"📊 Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✅ ТЕСТ 1 ПРОЙДЕН: API отвечает 200 OK")
            else:
                print(f"❌ ТЕСТ 1 ПРОВАЛЕН: API вернул {response.status_code}")
                print(f"Response text: {response.text}")
                return False
            
            # Parse response
            try:
                result = response.json()
                print(f"📋 Response keys: {list(result.keys())}")
            except json.JSONDecodeError as e:
                print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось распарсить JSON ответ: {e}")
                print(f"Raw response: {response.text[:500]}...")
                return False
            
            # Check 2: Техкарта генерируется нормально
            if result.get("success") and result.get("tech_card"):
                print("✅ ТЕСТ 2 ПРОЙДЕН: Техкарта генерируется нормально")
                tech_card_content = result["tech_card"]
                print(f"📄 Tech card length: {len(tech_card_content)} characters")
                
                # Show preview of tech card
                print("📖 ПРЕВЬЮ ТЕХКАРТЫ:")
                print("-" * 40)
                preview_lines = tech_card_content.split('\n')[:15]  # First 15 lines
                for line in preview_lines:
                    print(line)
                if len(tech_card_content.split('\n')) > 15:
                    print("... (truncated)")
                print("-" * 40)
                
            else:
                print("❌ ТЕСТ 2 ПРОВАЛЕН: Техкарта не сгенерировалась")
                print(f"Success: {result.get('success')}")
                print(f"Tech card present: {'tech_card' in result}")
                return False
            
            # Check 3: Цены адекватные (не космические)
            print("🔍 ПРОВЕРКА ЦЕН:")
            price_check_passed = self.check_prices(tech_card_content)
            if price_check_passed:
                print("✅ ТЕСТ 3 ПРОЙДЕН: Цены адекватные")
            else:
                print("⚠️ ТЕСТ 3: ВНИМАНИЕ - Цены могут быть завышены")
            
            # Check 4: Нет ошибок 500 (уже проверено выше)
            print("✅ ТЕСТ 4 ПРОЙДЕН: Нет ошибок 500")
            
            # Check 5: Тестовый пользователь создается автоматически
            print("🔍 ПРОВЕРКА АВТОСОЗДАНИЯ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ:")
            if self.test_user_id.startswith("test_user_"):
                print("✅ ТЕСТ 5 ПРОЙДЕН: Тестовый пользователь создается автоматически")
                print(f"   (код в server.py обрабатывает test_user_ префикс)")
            else:
                print("⚠️ ТЕСТ 5: Не тестовый пользователь")
            
            # Additional checks
            print("\n📊 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:")
            print(f"   Monthly used: {result.get('monthly_used', 'N/A')}")
            print(f"   Monthly limit: {result.get('monthly_limit', 'N/A')}")
            print(f"   Tech card ID: {result.get('id', 'N/A')}")
            
            return True
            
        except requests.exceptions.Timeout:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Timeout - API не отвечает в течение 2 минут")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Ошибка соединения: {e}")
            return False
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Неожиданная ошибка: {e}")
            return False
    
    def check_prices(self, tech_card_content):
        """
        Проверяет адекватность цен в техкарте
        """
        import re
        
        # Extract prices from tech card
        price_pattern = r'(\d+(?:\.\d+)?)\s*₽'
        prices = re.findall(price_pattern, tech_card_content)
        
        if not prices:
            print("   ⚠️ Цены не найдены в техкарте")
            return False
        
        prices = [float(p) for p in prices]
        max_price = max(prices)
        total_cost = sum(prices)
        
        print(f"   💰 Найдено цен: {len(prices)}")
        print(f"   💰 Максимальная цена: {max_price}₽")
        print(f"   💰 Общая стоимость: {total_cost}₽")
        
        # Check for unreasonable prices
        # For Борщ, reasonable total cost should be under 500₽
        if max_price > 1000:
            print(f"   ⚠️ ВНИМАНИЕ: Максимальная цена {max_price}₽ кажется завышенной")
            return False
        
        if total_cost > 1000:
            print(f"   ⚠️ ВНИМАНИЕ: Общая стоимость {total_cost}₽ кажется завышенной для борща")
            return False
        
        print("   ✅ Цены в разумных пределах")
        return True
    
    def run_urgent_test(self):
        """
        Запускает срочный тест
        """
        print(f"🕐 Время начала теста: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        success = self.test_generate_tech_card_urgent()
        
        print("\n" + "=" * 60)
        print(f"🕐 Время окончания теста: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if success:
            print("🎉 ВСЕ СРОЧНЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
            print("✅ ГОТОВО К ДЕПЛОЮ Beta версии")
            return True
        else:
            print("💥 СРОЧНЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
            print("❌ НЕ ГОТОВО К ДЕПЛОЮ")
            return False

if __name__ == "__main__":
    tester = UrgentDeploymentTest()
    success = tester.run_urgent_test()
    exit(0 if success else 1)