#!/usr/bin/env python3
"""
КРИТИЧЕСКИЙ ТЕСТ: ИСПРАВЛЕНИЕ DISH-SKELETONS WRITER
Тестирование исправления функции create_dish_skeletons_xlsx после обновления.

ПРОБЛЕМА БЫЛА: Dish-Skeletons.xlsx создавался пустым (только заголовки) несмотря на missing dishes > 0

ИСПРАВЛЕНИЯ СДЕЛАНЫ:
1. ✅ _create_dish_skeletons_xlsx теперь создает dishes_data из missing_dishes
2. ✅ create_dish_skeletons_xlsx поддерживает dishes_data формат
3. ✅ Данные блюд передаются напрямую без необходимости техкарт

WORKFLOW:
1. Сгенерировать техкарту "Щи зеленые с говядиной"
2. Запустить preflight (должен обнаружить missing блюдо)
3. Запустить ZIP экспорт
4. **КРИТИЧЕСКИ**: Проверить что Dish-Skeletons.xlsx содержит данные блюда
5. Убедиться что артикулы правильно отформатированы
"""

import asyncio
import json
import os
import sys
import time
import traceback
import zipfile
import io
from datetime import datetime
from typing import Dict, List, Any, Optional

import httpx
import openpyxl
from pymongo import MongoClient

# Test Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cursor-push.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api/v1"
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
DB_NAME = os.getenv('DB_NAME', 'receptor_pro')

class DishSkeletonsWriterTester:
    """Критический тест исправления Dish-Skeletons Writer"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        self.organization_id = "test-org-dish-skeletons"
        self.generated_techcard_id = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0.0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.3f}s" if response_time > 0 else "N/A"
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} ({response_time:.3f}s) - {details}")
    
    async def test_step1_generate_techcard(self):
        """Шаг 1: Сгенерировать техкарту 'Щи зеленые с говядиной'"""
        print("\n🎯 ШАГ 1: Генерация техкарты 'Щи зеленые с говядиной'")
        
        try:
            start_time = time.time()
            
            payload = {
                "name": "Щи зеленые с говядиной",
                "cuisine": "русская",
                "equipment": [],
                "budget": None,
                "dietary": []
            }
            
            response = await self.client.post(f"{API_BASE}/techcards.v2/generate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Извлечь ID техкарты
                if data.get("status") in ["success", "draft"] and data.get("card"):
                    techcard = data["card"]
                    # ID находится в meta.id
                    self.generated_techcard_id = techcard.get("meta", {}).get("id")
                    
                    if self.generated_techcard_id:
                        self.log_test("Генерация техкарты", True,
                                    f"ID: {self.generated_techcard_id}, Название: {techcard.get('meta', {}).get('title', 'N/A')}", 
                                    response_time)
                        
                        # Проверить что техкарта сохранена в базу
                        await self.verify_techcard_in_database()
                        
                        return True
                    else:
                        self.log_test("Генерация техкарты", False,
                                    f"Техкарта создана но ID не найден в meta", response_time)
                else:
                    self.log_test("Генерация техкарты", False,
                                f"Неуспешный ответ: {data.get('status', 'Unknown status')}, {data.get('message', 'No message')}", response_time)
            else:
                self.log_test("Генерация техкарты", False,
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            self.log_test("Генерация техкарты", False, f"Exception: {str(e)}", 0.0)
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
        
        return False
    
    async def verify_techcard_in_database(self):
        """Проверить что техкарта сохранена в MongoDB"""
        try:
            start_time = time.time()
            
            client = MongoClient(MONGO_URL)
            db = client[DB_NAME.strip('"')]
            techcards_collection = db.techcards
            
            # Найти техкарту по ID
            techcard_doc = techcards_collection.find_one({"id": self.generated_techcard_id})
            response_time = time.time() - start_time
            
            if techcard_doc:
                ingredients_count = len(techcard_doc.get("ingredients", []))
                self.log_test("Техкарта в базе данных", True,
                            f"Найдена техкарта с {ingredients_count} ингредиентами", response_time)
            else:
                self.log_test("Техкарта в базе данных", False,
                            f"Техкарта с ID {self.generated_techcard_id} не найдена", response_time)
            
            client.close()
            
        except Exception as e:
            self.log_test("Техкарта в базе данных", False, f"Exception: {str(e)}", 0.0)
    
    async def test_step2_run_preflight(self):
        """Шаг 2: Запустить preflight (должен обнаружить missing блюдо)"""
        print("\n🎯 ШАГ 2: Запуск preflight для обнаружения missing блюда")
        
        if not self.generated_techcard_id:
            self.log_test("Preflight Check", False, "Нет ID техкарты для тестирования", 0.0)
            return None
        
        try:
            start_time = time.time()
            
            payload = {
                "techcardIds": [self.generated_techcard_id],
                "organization_id": self.organization_id
            }
            
            response = await self.client.post(f"{API_BASE}/export/preflight", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверить структуру ответа
                missing_dishes = data.get("missing", {}).get("dishes", [])
                missing_products = data.get("missing", {}).get("products", [])
                ttk_date = data.get("ttkDate")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: должно быть обнаружено 1 missing блюдо
                if len(missing_dishes) >= 1:
                    dish = missing_dishes[0]
                    dish_name = dish.get("name", "")
                    dish_article = dish.get("article", "")
                    
                    # Проверить что это наше блюдо
                    is_correct_dish = "Щи зеленые с говядиной" in dish_name
                    has_article = dish_article and len(dish_article) == 5 and dish_article.isdigit()
                    
                    if is_correct_dish and has_article:
                        self.log_test("Preflight Missing Dish Detection", True,
                                    f"Обнаружено блюдо: {dish_name}, Артикул: {dish_article}", response_time)
                        
                        # Сохранить данные preflight для следующего шага
                        self.preflight_data = data
                        return data
                    else:
                        self.log_test("Preflight Missing Dish Detection", False,
                                    f"Неправильное блюдо или артикул: {dish_name}, {dish_article}", response_time)
                else:
                    self.log_test("Preflight Missing Dish Detection", False,
                                f"Missing dishes не обнаружены: {len(missing_dishes)} блюд", response_time)
                
                # Дополнительная информация
                self.log_test("Preflight Response Structure", True,
                            f"TTK Date: {ttk_date}, Missing Products: {len(missing_products)}", response_time)
                
            else:
                self.log_test("Preflight Check", False,
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            self.log_test("Preflight Check", False, f"Exception: {str(e)}", 0.0)
        
        return None
    
    async def test_step3_run_zip_export(self):
        """Шаг 3: Запустить ZIP экспорт"""
        print("\n🎯 ШАГ 3: Запуск ZIP экспорта")
        
        if not hasattr(self, 'preflight_data') or not self.preflight_data:
            self.log_test("ZIP Export", False, "Нет данных preflight для экспорта", 0.0)
            return None
        
        try:
            start_time = time.time()
            
            payload = {
                "techcardIds": [self.generated_techcard_id],
                "operational_rounding": True,
                "organization_id": self.organization_id,
                "preflight_result": self.preflight_data
            }
            
            response = await self.client.post(f"{API_BASE}/export/zip", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Проверить что это ZIP файл
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                is_zip = response.content.startswith(b'PK')
                
                if is_zip and content_length > 0:
                    self.log_test("ZIP Export Generation", True,
                                f"ZIP файл создан: {content_length} байт", response_time)
                    
                    # Сохранить ZIP для анализа
                    self.zip_content = response.content
                    return response.content
                else:
                    self.log_test("ZIP Export Generation", False,
                                f"Неверный ZIP: content-type={content_type}, size={content_length}", response_time)
            else:
                self.log_test("ZIP Export Generation", False,
                            f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                
        except Exception as e:
            self.log_test("ZIP Export Generation", False, f"Exception: {str(e)}", 0.0)
        
        return None
    
    async def test_step4_critical_dish_skeletons_validation(self):
        """Шаг 4: КРИТИЧЕСКАЯ ПРОВЕРКА - Dish-Skeletons.xlsx содержит данные блюда"""
        print("\n🎯 ШАГ 4: КРИТИЧЕСКАЯ ПРОВЕРКА - Содержимое Dish-Skeletons.xlsx")
        
        if not hasattr(self, 'zip_content') or not self.zip_content:
            self.log_test("Dish-Skeletons Content Validation", False, "Нет ZIP файла для анализа", 0.0)
            return False
        
        try:
            start_time = time.time()
            
            # Открыть ZIP файл
            with zipfile.ZipFile(io.BytesIO(self.zip_content), 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # Проверить что Dish-Skeletons.xlsx присутствует
                dish_skeletons_file = None
                for filename in file_list:
                    if 'Dish-Skeletons.xlsx' in filename:
                        dish_skeletons_file = filename
                        break
                
                if not dish_skeletons_file:
                    self.log_test("Dish-Skeletons File Presence", False,
                                f"Dish-Skeletons.xlsx не найден в ZIP. Файлы: {file_list}", 0.0)
                    return False
                
                self.log_test("Dish-Skeletons File Presence", True,
                            f"Найден файл: {dish_skeletons_file}", 0.0)
                
                # Открыть и проанализировать Excel файл
                with zip_file.open(dish_skeletons_file) as excel_file:
                    workbook = openpyxl.load_workbook(excel_file)
                    worksheet = workbook.active
                    
                    # Получить все данные
                    all_rows = list(worksheet.iter_rows(values_only=True))
                    response_time = time.time() - start_time
                    
                    if len(all_rows) < 2:
                        self.log_test("Dish-Skeletons Content Validation", False,
                                    f"Файл содержит только заголовки: {len(all_rows)} строк", response_time)
                        return False
                    
                    # Проверить заголовки
                    headers = all_rows[0] if all_rows else []
                    expected_headers = ["Артикул", "Наименование", "Тип", "Ед. выпуска", "Выход"]
                    
                    headers_valid = all(header in headers for header in expected_headers)
                    
                    if not headers_valid:
                        self.log_test("Dish-Skeletons Headers", False,
                                    f"Неправильные заголовки: {headers}", response_time)
                    else:
                        self.log_test("Dish-Skeletons Headers", True,
                                    f"Заголовки корректны: {len(headers)} колонок", response_time)
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА: данные блюда
                    data_rows = all_rows[1:]  # Пропустить заголовки
                    
                    if len(data_rows) == 0:
                        self.log_test("Dish-Skeletons Data Content", False,
                                    "КРИТИЧЕСКАЯ ОШИБКА: Файл содержит только заголовки, нет данных блюда!", response_time)
                        return False
                    
                    # Проверить первую строку данных
                    first_row = data_rows[0]
                    
                    if len(first_row) >= 5:
                        article = str(first_row[0]) if first_row[0] else ""
                        name = str(first_row[1]) if first_row[1] else ""
                        dish_type = str(first_row[2]) if first_row[2] else ""
                        unit = str(first_row[3]) if first_row[3] else ""
                        yield_value = first_row[4] if first_row[4] else ""
                        
                        # Проверить артикул (5-значный)
                        article_valid = len(article) == 5 and article.isdigit()
                        
                        # Проверить название блюда
                        name_valid = "Щи зеленые с говядиной" in name
                        
                        # Проверить тип (более гибкая проверка)
                        type_valid = dish_type.lower() in ["блюдо", "dish"]
                        
                        # Проверить единицу (более гибкая проверка)
                        unit_valid = unit.lower() in ["порц.", "порц", "pcs", "шт"]
                        
                        # Проверить выход
                        yield_valid = isinstance(yield_value, (int, float)) and yield_value > 0
                        
                        all_valid = article_valid and name_valid and type_valid and unit_valid and yield_valid
                        
                        details = f"Артикул: {article} ({'✅' if article_valid else '❌'}), " \
                                f"Название: {name[:30]}... ({'✅' if name_valid else '❌'}), " \
                                f"Тип: {dish_type} ({'✅' if type_valid else '❌'}), " \
                                f"Единица: {unit} ({'✅' if unit_valid else '❌'}), " \
                                f"Выход: {yield_value} ({'✅' if yield_valid else '❌'})"
                        
                        self.log_test("Dish-Skeletons Data Content", all_valid,
                                    f"КРИТИЧЕСКИЙ ТЕСТ: {details}", response_time)
                        
                        if all_valid:
                            self.log_test("Dish-Skeletons Writer Fix Verification", True,
                                        f"✅ ИСПРАВЛЕНИЕ ПОДТВЕРЖДЕНО: Dish-Skeletons.xlsx содержит корректные данные блюда", response_time)
                            return True
                        else:
                            self.log_test("Dish-Skeletons Writer Fix Verification", False,
                                        f"❌ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ: Данные блюда некорректны", response_time)
                    else:
                        self.log_test("Dish-Skeletons Data Content", False,
                                    f"Недостаточно колонок в данных: {len(first_row)}", response_time)
                    
                    # Дополнительная информация
                    self.log_test("Dish-Skeletons File Analysis", True,
                                f"Всего строк: {len(all_rows)}, Строк данных: {len(data_rows)}", response_time)
                    
        except Exception as e:
            self.log_test("Dish-Skeletons Content Validation", False, f"Exception: {str(e)}", 0.0)
        
        return False
    
    async def test_step5_article_formatting_verification(self):
        """Шаг 5: Проверить правильное форматирование артикулов"""
        print("\n🎯 ШАГ 5: Проверка форматирования артикулов")
        
        if not hasattr(self, 'preflight_data') or not self.preflight_data:
            self.log_test("Article Formatting", False, "Нет данных preflight для проверки", 0.0)
            return
        
        try:
            start_time = time.time()
            
            # Проверить артикулы из preflight
            missing_dishes = self.preflight_data.get("missing", {}).get("dishes", [])
            missing_products = self.preflight_data.get("missing", {}).get("products", [])
            
            all_articles = []
            
            # Собрать все артикулы
            for dish in missing_dishes:
                article = dish.get("article")
                if article:
                    all_articles.append(("dish", article, dish.get("name", "Unknown")))
            
            for product in missing_products:
                article = product.get("article")
                if article:
                    all_articles.append(("product", article, product.get("name", "Unknown")))
            
            response_time = time.time() - start_time
            
            if not all_articles:
                self.log_test("Article Formatting", False, "Нет артикулов для проверки", response_time)
                return
            
            # Проверить форматирование каждого артикула
            format_valid = True
            format_details = []
            
            for item_type, article, name in all_articles:
                # Проверить 5-значный формат
                is_valid = len(article) == 5 and article.isdigit()
                
                if not is_valid:
                    format_valid = False
                
                format_details.append(f"{item_type}: {article} ({'✅' if is_valid else '❌'}) - {name[:20]}...")
            
            self.log_test("Article Formatting Validation", format_valid,
                        f"Проверено {len(all_articles)} артикулов: {'; '.join(format_details[:3])}", response_time)
            
            # Проверить что артикулы начинаются с правильных префиксов
            dish_articles = [article for item_type, article, name in all_articles if item_type == "dish"]
            product_articles = [article for item_type, article, name in all_articles if item_type == "product"]
            
            if dish_articles:
                # Блюда должны начинаться с 10000+
                dish_range_valid = all(int(article) >= 10000 for article in dish_articles if article.isdigit())
                self.log_test("Dish Article Range", dish_range_valid,
                            f"Артикулы блюд: {dish_articles}", response_time)
            
            if product_articles:
                # Продукты могут начинаться с любого диапазона
                self.log_test("Product Article Range", True,
                            f"Артикулы продуктов: {product_articles[:3]}", response_time)
            
        except Exception as e:
            self.log_test("Article Formatting", False, f"Exception: {str(e)}", 0.0)
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("🚨 КРИТИЧЕСКИЙ ТЕСТ: ИСПРАВЛЕНИЕ DISH-SKELETONS WRITER")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   Пройдено: {passed_tests} ✅")
        print(f"   Провалено: {failed_tests} ❌")
        print(f"   Успешность: {success_rate:.1f}%")
        
        # Критические тесты
        critical_tests = [
            "Генерация техкарты",
            "Preflight Missing Dish Detection", 
            "ZIP Export Generation",
            "Dish-Skeletons Content Validation",
            "Dish-Skeletons Writer Fix Verification"
        ]
        
        print(f"\n🎯 КРИТИЧЕСКИЕ ПРОВЕРКИ:")
        critical_passed = 0
        
        for test_name in critical_tests:
            result = next((r for r in self.test_results if r["test"] == test_name), None)
            if result:
                status = "✅" if result["success"] else "❌"
                print(f"   {status} {test_name}: {result['details']}")
                if result["success"]:
                    critical_passed += 1
            else:
                print(f"   ⚠️  {test_name} (не выполнен)")
        
        critical_success_rate = (critical_passed / len(critical_tests) * 100)
        
        print(f"\n🎯 КРИТИЧЕСКИЙ РЕЗУЛЬТАТ:")
        if critical_success_rate >= 80:
            print(f"✅ ИСПРАВЛЕНИЕ DISH-SKELETONS WRITER ПОДТВЕРЖДЕНО ({critical_success_rate:.1f}%)")
            print(f"   Dish-Skeletons.xlsx теперь содержит данные блюд вместо пустых файлов")
        else:
            print(f"❌ ИСПРАВЛЕНИЕ DISH-SKELETONS WRITER НЕ РАБОТАЕТ ({critical_success_rate:.1f}%)")
            print(f"   Требуется дополнительная отладка функции create_dish_skeletons_xlsx")
        
        if failed_tests > 0:
            print(f"\n❌ ПРОВАЛЕННЫЕ ТЕСТЫ:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        return critical_success_rate >= 80


async def main():
    """Main test execution"""
    print("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТА: ИСПРАВЛЕНИЕ DISH-SKELETONS WRITER")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"MongoDB URL: {MONGO_URL}")
    print(f"Database: {DB_NAME}")
    print("\n" + "="*80)
    print("WORKFLOW ТЕСТИРОВАНИЯ:")
    print("1. Сгенерировать техкарту 'Щи зеленые с говядиной'")
    print("2. Запустить preflight (должен обнаружить missing блюдо)")
    print("3. Запустить ZIP экспорт")
    print("4. КРИТИЧЕСКИ: Проверить что Dish-Skeletons.xlsx содержит данные блюда")
    print("5. Убедиться что артикулы правильно отформатированы")
    print("="*80)
    
    async with DishSkeletonsWriterTester() as tester:
        # Выполнить все шаги тестирования
        success_step1 = await tester.test_step1_generate_techcard()
        
        if success_step1:
            preflight_data = await tester.test_step2_run_preflight()
            
            if preflight_data:
                zip_content = await tester.test_step3_run_zip_export()
                
                if zip_content:
                    await tester.test_step4_critical_dish_skeletons_validation()
                    await tester.test_step5_article_formatting_verification()
        
        # Печать итогового отчета
        success = tester.print_summary()
        
        if success:
            print(f"\n🎉 КРИТИЧЕСКИЙ ТЕСТ ПРОЙДЕН УСПЕШНО!")
            print(f"Исправление Dish-Skeletons writer работает корректно.")
            print(f"Dish-Skeletons.xlsx теперь содержит данные блюд вместо пустых файлов.")
        else:
            print(f"\n⚠️  КРИТИЧЕСКИЙ ТЕСТ ПРОВАЛЕН")
            print(f"Исправление Dish-Skeletons writer требует дополнительной отладки.")
            print(f"Проблема с пустыми Dish-Skeletons.xlsx файлами не решена.")
        
        return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Тестирование провалено с исключением: {e}")
        traceback.print_exc()
        sys.exit(1)