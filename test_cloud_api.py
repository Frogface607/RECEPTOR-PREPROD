#!/usr/bin/env python3
"""
Тестовый скрипт для проверки iikoCloud API интеграции
Тестирует все новые BI endpoints и получение номенклатуры
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Настройки
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000')
API_BASE = f"{BACKEND_URL}/api/iiko"
USER_ID = os.environ.get('TEST_USER_ID', 'default_user')

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name: str):
    """Вывести заголовок теста"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}🧪 {name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def print_success(message: str):
    """Вывести успешный результат"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message: str):
    """Вывести ошибку"""
    print(f"{RED}❌ {message}{RESET}")

def print_info(message: str):
    """Вывести информацию"""
    print(f"{YELLOW}ℹ️  {message}{RESET}")

def test_endpoint(name: str, method: str, url: str, **kwargs) -> tuple[bool, Dict[str, Any] | None]:
    """Тестировать endpoint"""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=30, **kwargs)
        elif method.upper() == 'POST':
            response = requests.post(url, timeout=30, **kwargs)
        else:
            return False, None
        
        if response.status_code == 200:
            try:
                data = response.json()
                print_success(f"{name}: {response.status_code}")
                return True, data
            except:
                print_success(f"{name}: {response.status_code} (non-JSON)")
                return True, {"text": response.text[:200]}
        else:
            print_error(f"{name}: {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print_error(f"{name}: Exception - {str(e)}")
        return False, None

def main():
    """Основная функция тестирования"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}🚀 ТЕСТИРОВАНИЕ IIKO CLOUD API ИНТЕГРАЦИИ{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"User ID: {USER_ID}")
    
    # 1. Проверка статуса подключения Cloud API
    print_test("1. Статус подключения Cloud API")
    success, data = test_endpoint(
        "GET /api/iiko/cloud/status/{user_id}",
        "GET",
        f"{API_BASE}/cloud/status/{USER_ID}"
    )
    
    if success and data:
        status = data.get("status", "unknown")
        if status == "connected":
            print_success(f"Cloud API подключен")
            org_name = data.get("organization_name", "N/A")
            org_id = data.get("organization_id", "N/A")
            print_info(f"Организация: {org_name} ({org_id})")
        else:
            print_error(f"Cloud API не подключен: {status}")
            print_info("⚠️  Для продолжения тестов нужно подключить Cloud API")
            print_info("   Используйте: POST /api/iiko/cloud/connect")
            return
    
    # 2. Получение номенклатуры через прямой HTTP
    print_test("2. Получение номенклатуры (для техкарт)")
    success, data = test_endpoint(
        "GET /api/iiko/cloud/menu/{user_id}",
        "GET",
        f"{API_BASE}/cloud/menu/{USER_ID}"
    )
    
    if success and data:
        products_count = data.get("products_count", 0)
        groups_count = data.get("groups_count", 0)
        print_info(f"Продуктов: {products_count}")
        print_info(f"Групп: {groups_count}")
        
        if products_count > 0:
            print_success("Номенклатура получена успешно!")
            # Показываем первые 3 продукта
            products = data.get("products", [])[:3]
            for product in products:
                print_info(f"  - {product.get('name', 'N/A')}")
        else:
            print_error("Номенклатура пуста (0 продуктов)")
    
    # 3. Отчёт по продажам
    print_test("3. Отчёт по продажам (BI)")
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    success, data = test_endpoint(
        "GET /api/iiko/cloud/reports/sales/{user_id}",
        "GET",
        f"{API_BASE}/cloud/reports/sales/{USER_ID}",
        params={
            "date_from": date_from,
            "date_to": date_to,
            "group_by": "DAY"
        }
    )
    
    if success and data:
        report = data.get("report", {})
        total_revenue = report.get("totalRevenue", 0)
        total_checks = report.get("totalChecks", 0)
        avg_check = report.get("averageCheck", 0)
        
        print_info(f"Период: {date_from} - {date_to}")
        print_info(f"Выручка: {total_revenue:,.2f} ₽")
        print_info(f"Чеков: {total_checks}")
        print_info(f"Средний чек: {avg_check:,.2f} ₽")
    
    # 4. Отчёт по остаткам
    print_test("4. Отчёт по остаткам (BI)")
    success, data = test_endpoint(
        "GET /api/iiko/cloud/reports/stock/{user_id}",
        "GET",
        f"{API_BASE}/cloud/reports/stock/{USER_ID}",
        params={"date": date_to}
    )
    
    if success and data:
        print_success("Отчёт по остаткам получен")
        report = data.get("report", {})
        print_info(f"Данные: {json.dumps(report, indent=2, ensure_ascii=False)[:300]}...")
    
    # 5. Отчёт по закупкам
    print_test("5. Отчёт по закупкам (BI)")
    success, data = test_endpoint(
        "GET /api/iiko/cloud/reports/purchases/{user_id}",
        "GET",
        f"{API_BASE}/cloud/reports/purchases/{USER_ID}",
        params={
            "date_from": date_from,
            "date_to": date_to
        }
    )
    
    if success and data:
        print_success("Отчёт по закупкам получен")
        report = data.get("report", {})
        print_info(f"Данные: {json.dumps(report, indent=2, ensure_ascii=False)[:300]}...")
    
    # 6. Получение заказов
    print_test("6. Получение заказов (BI)")
    success, data = test_endpoint(
        "GET /api/iiko/cloud/orders/{user_id}",
        "GET",
        f"{API_BASE}/cloud/orders/{USER_ID}",
        params={
            "date_from": date_from,
            "date_to": date_to
        }
    )
    
    if success and data:
        orders_data = data.get("orders", {})
        orders_count = orders_data.get("count", 0)
        print_info(f"Заказов: {orders_count}")
        if orders_count > 0:
            print_success("Заказы получены успешно!")
    
    # 7. Получение сотрудников
    print_test("7. Получение сотрудников (BI)")
    success, data = test_endpoint(
        "GET /api/iiko/cloud/employees/{user_id}",
        "GET",
        f"{API_BASE}/cloud/employees/{USER_ID}"
    )
    
    if success and data:
        employees_data = data.get("employees", {})
        employees_count = employees_data.get("count", 0)
        print_info(f"Сотрудников: {employees_count}")
        if employees_count > 0:
            print_success("Сотрудники получены успешно!")
            # Показываем первых 3 сотрудников
            employees = employees_data.get("employees", [])[:3]
            for emp in employees:
                name = emp.get("name", "N/A") if isinstance(emp, dict) else str(emp)
                print_info(f"  - {name}")
    
    # 8. Тест через чат (если нужно)
    print_test("8. Тест через чат")
    print_info("Для тестирования через чат используйте следующие запросы:")
    print_info("  - 'Покажи отчёт по продажам за неделю'")
    print_info("  - 'Какие продукты есть в iiko?'")
    print_info("  - 'Покажи сотрудников'")
    print_info("  - 'Получи заказы за сегодня'")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{GREEN}✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

if __name__ == "__main__":
    main()

