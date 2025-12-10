# IIKO API - ПРАКТИЧЕСКИЕ ПРИМЕРЫ И РЕЦЕПТЫ

## 1. ПОЛУЧЕНИЕ ЯВОК СОТРУДНИКОВ И ВЫГРУЗКА В ТАБЛИЦУ

### Задача
Получить явки сотрудников за месяц и выгрузить в Google Sheets для расчета зарплаты.

### Решение через N8N

```json
{
  "workflow": {
    "steps": [
      {
        "name": "Get Employees",
        "operation": "iiko_get_employees",
        "params": {
          "organizationId": "{{ORG_ID}}",
          "apiKey": "{{API_KEY}}"
        }
      },
      {
        "name": "Get Attendances",
        "operation": "iiko_get_attendances",
        "params": {
          "employeeIds": "{{Get Employees.ids}}",
          "dateFrom": "2025-12-01",
          "dateTo": "2025-12-31"
        }
      },
      {
        "name": "Transform Data",
        "operation": "transform",
        "params": {
          "mapping": {
            "employee_name": "{{name}}",
            "date": "{{date}}",
            "hours_worked": "{{(closeTime - openTime) / 3600}}",
            "attendance_type": "{{type}}"
          }
        }
      },
      {
        "name": "Send to Google Sheets",
        "operation": "google_sheets_append_rows",
        "params": {
          "spreadsheetId": "{{SHEET_ID}}",
          "range": "Явки!A:D",
          "values": "{{Transform Data.output}}"
        }
      }
    ]
  }
}
```

### Python скрипт для получения явок

```python
import requests
from datetime import datetime, timedelta
import csv

API_KEY = "your_api_key"
API_URL = "https://api.iiko.ru/api/v1"
ORG_ID = "your_org_id"

def get_all_employees():
    """Получить список всех сотрудников"""
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(
        f"{API_URL}/employees",
        headers=headers,
        params={'organizationId': ORG_ID}
    )
    return response.json()['employees']

def get_attendances(employee_id, month="12-2025"):
    """Получить явки сотрудника за месяц"""
    year, month = month.split("-")
    date_from = f"{year}-{month}-01"
    
    # Расчет последнего дня месяца
    from calendar import monthrange
    _, last_day = monthrange(int(year), int(month))
    date_to = f"{year}-{month}-{last_day}"
    
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(
        f"{API_URL}/employees/{employee_id}/attendances",
        headers=headers,
        params={
            'dateFrom': date_from,
            'dateTo': date_to
        }
    )
    return response.json()['attendances']

def export_to_csv(employees, filename="attendances.csv"):
    """Экспортировать явки в CSV"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ФИ Сотрудника', 'Дата', 'Начало', 'Окончание', 'Часов', 'Тип'])
        
        for emp in employees:
            emp_name = emp['name']
            attendances = get_attendances(emp['id'])
            
            for att in attendances:
                open_time = datetime.fromisoformat(att['openTime'])
                close_time = datetime.fromisoformat(att['closeTime'])
                hours = (close_time - open_time).total_seconds() / 3600
                
                writer.writerow([
                    emp_name,
                    att['date'],
                    open_time.strftime("%H:%M"),
                    close_time.strftime("%H:%M"),
                    f"{hours:.1f}",
                    att.get('attendanceType', 'РАБОТА')
                ])

# Использование
if __name__ == "__main__":
    employees = get_all_employees()
    export_to_csv(employees)
    print("Явки экспортированы в attendances.csv")
```

---

## 2. СИНХРОНИЗАЦИЯ ТЕХКАРТ С GOOGLE SHEETS

### Задача
Вести техкарты в Google Sheets и синхронизировать в IIKO.

### Решение через N8N

```json
{
  "workflow": {
    "trigger": "schedule",
    "schedule": "daily",
    "steps": [
      {
        "name": "Read from Google Sheets",
        "operation": "google_sheets_read_rows",
        "params": {
          "spreadsheetId": "{{TECH_CARDS_SHEET_ID}}",
          "range": "Техкарты!A:E"
        }
      },
      {
        "name": "Parse Tech Cards",
        "operation": "transform",
        "params": {
          "mapping": {
            "dishName": "{{row[0]}}",
            "ingredient": "{{row[1]}}",
            "quantity": "{{parseFloat(row[2])}}",
            "unit": "{{row[3]}}",
            "notes": "{{row[4]}}"
          }
        }
      },
      {
        "name": "Get Dish ID from IIKO",
        "operation": "iiko_get_menu",
        "params": {
          "organizationId": "{{ORG_ID}}",
          "search": "{{Parse Tech Cards.dishName}}"
        }
      },
      {
        "name": "Update Tech Card in IIKO",
        "operation": "iiko_update_tech_card",
        "params": {
          "dishId": "{{Get Dish ID.id}}",
          "ingredients": "{{Parse Tech Cards.output}}",
          "startDate": "{{TODAY()}}"
        }
      },
      {
        "name": "Log Changes",
        "operation": "send_email",
        "params": {
          "to": "manager@restaurant.ru",
          "subject": "Техкарты синхронизированы",
          "body": "Обновлено {{Update Tech Card.count}} техкарт"
        }
      }
    ]
  }
}
```

---

## 3. АВТОМАТИЧЕСКИЙ ОТЧЕТ ПО ПРОДАЖАМ

### Задача
Каждый день получать отчет о продажах и отправлять менеджеру.

### Решение на Python + Cron

```python
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import json

class IIKOReporter:
    def __init__(self, api_key, org_id):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = "https://api.iiko.ru/api/v1"
        self.headers = {'Authorization': f'Bearer {api_key}'}
    
    def get_daily_sales(self, date=None):
        """Получить продажи за день"""
        if date is None:
            date = datetime.now().date()
        
        response = requests.get(
            f"{self.base_url}/reports/sales",
            headers=self.headers,
            params={
                'organizationId': self.org_id,
                'dateFrom': str(date),
                'dateTo': str(date),
                'groupBy': 'HOUR'
            }
        )
        return response.json()
    
    def format_report(self, sales_data):
        """Форматировать отчет"""
        html = """
        <html>
        <head>
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid black; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                .total { font-weight: bold; background-color: #f0f0f0; }
            </style>
        </head>
        <body>
            <h2>Отчет по продажам за {date}</h2>
            <table>
                <tr>
                    <th>Время</th>
                    <th>Выручка</th>
                    <th>Чеков</th>
                    <th>Средний чек</th>
                </tr>
        """.format(date=datetime.now().strftime("%d.%m.%Y"))
        
        total_revenue = 0
        total_checks = 0
        
        for hour_data in sales_data['data']:
            revenue = hour_data['revenue']
            checks = hour_data['checkCount']
            avg_check = revenue / checks if checks > 0 else 0
            
            html += f"""
                <tr>
                    <td>{hour_data['hour']}:00</td>
                    <td>{revenue:.2f} ₽</td>
                    <td>{checks}</td>
                    <td>{avg_check:.2f} ₽</td>
                </tr>
            """
            
            total_revenue += revenue
            total_checks += checks
        
        avg_check_total = total_revenue / total_checks if total_checks > 0 else 0
        
        html += f"""
                <tr class="total">
                    <td>ИТОГО</td>
                    <td>{total_revenue:.2f} ₽</td>
                    <td>{total_checks}</td>
                    <td>{avg_check_total:.2f} ₽</td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return html
    
    def send_email(self, recipient, subject, html_body):
        """Отправить отчет по email"""
        msg = MIMEText(html_body, 'html', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = 'reports@restaurant.ru'
        msg['To'] = recipient
        
        # Настройте параметры вашего SMTP сервера
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login('your_email@gmail.com', 'your_password')
            server.send_message(msg)

# Использование (добавить в crontab для ежедневного запуска)
if __name__ == "__main__":
    reporter = IIKOReporter(
        api_key="your_api_key",
        org_id="your_org_id"
    )
    
    sales = reporter.get_daily_sales()
    html = reporter.format_report(sales)
    reporter.send_email(
        recipient="manager@restaurant.ru",
        subject=f"Отчет по продажам за {datetime.now().strftime('%d.%m.%Y')}",
        html_body=html
    )
    
    print("Отчет отправлен")

# Crontab запись:
# 0 18 * * * /usr/bin/python3 /path/to/iiko_daily_report.py
```

---

## 4. КОНТРОЛЬ ОСТАТКОВ НА СКЛАДЕ

### Задача
Отслеживать остатки товаров и отправлять уведомление при низких запасах.

### Решение

```python
import requests
from typing import List, Dict

class StockMonitor:
    def __init__(self, api_key, org_id):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = "https://api.iiko.ru/api/v1"
        self.headers = {'Authorization': f'Bearer {api_key}'}
        
        # Минимальные остатки (изменить под свои нужды)
        self.min_stock = {
            "Помидоры кг": 5,
            "Огурцы кг": 3,
            "Масло подсолнечное л": 10,
            "Уксус л": 2
        }
    
    def get_stock(self) -> Dict:
        """Получить остатки на всех складах"""
        response = requests.get(
            f"{self.base_url}/stock/report",
            headers=self.headers,
            params={'organizationId': self.org_id}
        )
        return response.json()
    
    def check_low_stock(self) -> List[Dict]:
        """Проверить товары с низкими остатками"""
        stock = self.get_stock()
        low_items = []
        
        for item in stock['items']:
            item_name = item['name']
            quantity = item['quantity']
            unit = item['unit']
            
            # Проверка по названию с единицей
            check_name = f"{item_name} {unit}"
            
            if check_name in self.min_stock:
                min_qty = self.min_stock[check_name]
                if quantity < min_qty:
                    low_items.append({
                        'name': item_name,
                        'current': quantity,
                        'minimum': min_qty,
                        'unit': unit,
                        'cost': item.get('cost', 0)
                    })
        
        return low_items
    
    def format_alert(self, low_items: List[Dict]) -> str:
        """Форматировать уведомление"""
        if not low_items:
            return "Все товары в норме ✓"
        
        alert = "⚠️ ВНИМАНИЕ: Низкие остатки на складе!\n\n"
        
        for item in low_items:
            alert += f"📦 {item['name']}\n"
            alert += f"   Текущие: {item['current']} {item['unit']}\n"
            alert += f"   Минимум: {item['minimum']} {item['unit']}\n"
            alert += f"   Стоимость: {item['cost']} ₽\n\n"
        
        return alert
    
    def send_telegram(self, token: str, chat_id: str, message: str):
        """Отправить уведомление в Telegram"""
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                'chat_id': chat_id,
                'text': message
            }
        )

# Использование
if __name__ == "__main__":
    monitor = StockMonitor(
        api_key="your_api_key",
        org_id="your_org_id"
    )
    
    low_items = monitor.check_low_stock()
    alert = monitor.format_alert(low_items)
    
    print(alert)
    
    # Отправить в Telegram
    if low_items:
        monitor.send_telegram(
            token="your_telegram_bot_token",
            chat_id="your_chat_id",
            message=alert
        )
```

---

## 5. КАСТОМНЫЙ ОТЧЕТ ПО СОТРУДНИКАМ

### Задача
Получить детальный отчет о производительности каждого сотрудника.

### Решение

```python
import requests
from datetime import datetime, timedelta
from collections import defaultdict

class EmployeeAnalytics:
    def __init__(self, api_key, org_id):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = "https://api.iiko.ru/api/v1"
        self.headers = {'Authorization': f'Bearer {api_key}'}
    
    def get_employee_data(self, days=30):
        """Получить данные о всех сотрудниках за период"""
        employees = self.get_employees()
        data = {}
        
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")
        
        for emp in employees:
            attendances = self.get_attendances(emp['id'], date_from, date_to)
            
            # Расчет метрик
            total_hours = sum([
                (datetime.fromisoformat(a['closeTime']) - 
                 datetime.fromisoformat(a['openTime'])).total_seconds() / 3600
                for a in attendances
            ])
            
            data[emp['id']] = {
                'name': emp['name'],
                'position': emp.get('position', 'N/A'),
                'hours': total_hours,
                'shifts': len(attendances),
                'attendance_rate': (len(attendances) / days * 100) if days > 0 else 0
            }
        
        return data
    
    def get_employees(self):
        """Получить список сотрудников"""
        response = requests.get(
            f"{self.base_url}/employees",
            headers=self.headers,
            params={'organizationId': self.org_id}
        )
        return response.json().get('employees', [])
    
    def get_attendances(self, employee_id, date_from, date_to):
        """Получить явки сотрудника"""
        response = requests.get(
            f"{self.base_url}/employees/{employee_id}/attendances",
            headers=self.headers,
            params={'dateFrom': date_from, 'dateTo': date_to}
        )
        return response.json().get('attendances', [])
    
    def generate_report(self, days=30):
        """Генерировать отчет"""
        data = self.get_employee_data(days)
        
        report = f"📊 ОТЧЕТ ПО СОТРУДНИКАМ (за {days} дней)\n"
        report += "=" * 60 + "\n\n"
        
        # Сортировка по часам работы
        sorted_data = sorted(
            data.items(),
            key=lambda x: x[1]['hours'],
            reverse=True
        )
        
        for emp_id, emp_data in sorted_data:
            report += f"👤 {emp_data['name']} ({emp_data['position']})\n"
            report += f"   ⏱️  Часов работы: {emp_data['hours']:.1f}\n"
            report += f"   📅 Смен: {emp_data['shifts']}\n"
            report += f"   📈 Явка: {emp_data['attendance_rate']:.1f}%\n"
            report += f"   ➡️  Среднее в смену: {emp_data['hours']/emp_data['shifts']:.1f} часов\n"
            report += "\n"
        
        return report

# Использование
if __name__ == "__main__":
    analytics = EmployeeAnalytics(
        api_key="your_api_key",
        org_id="your_org_id"
    )
    
    report = analytics.generate_report(days=30)
    print(report)
    
    # Сохранить в файл
    with open('employee_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
```

---

## 6. ЭКСПОРТ ДАННЫХ В EXCEL

### Задача
Выгрузить данные по технологическим картам в Excel для анализа.

```python
import requests
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

class TechCardExporter:
    def __init__(self, api_key, org_id):
        self.api_key = api_key
        self.org_id = org_id
        self.base_url = "https://api.iiko.ru/api/v1"
        self.headers = {'Authorization': f'Bearer {api_key}'}
    
    def get_menu(self):
        """Получить меню с техкартами"""
        response = requests.get(
            f"{self.base_url}/menu",
            headers=self.headers,
            params={'organizationId': self.org_id}
        )
        return response.json()
    
    def export_to_excel(self, filename='tech_cards.xlsx'):
        """Экспортировать в Excel"""
        menu = self.get_menu()
        wb = Workbook()
        ws = wb.active
        ws.title = "Техкарты"
        
        # Заголовок
        headers = ['Блюдо', 'Ингредиент', 'Количество', 'Единица', 'Себестоимость', 'Категория']
        ws.append(headers)
        
        # Стилизация заголовка
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        # Заполнение данных
        row = 2
        for dish in menu.get('dishes', []):
            dish_name = dish['name']
            tech_cards = dish.get('technologicalCards', [])
            
            if tech_cards:
                for card in tech_cards:
                    for ingredient in card.get('ingredients', []):
                        ws[f'A{row}'] = dish_name
                        ws[f'B{row}'] = ingredient['name']
                        ws[f'C{row}'] = ingredient['quantity']
                        ws[f'D{row}'] = ingredient['unit']
                        ws[f'E{row}'] = ingredient.get('cost', 0)
                        ws[f'F{row}'] = dish.get('category', 'N/A')
                        row += 1
        
        # Автоширина колонок
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Сохранение
        wb.save(filename)
        print(f"✓ Файл сохранен: {filename}")

# Использование
if __name__ == "__main__":
    exporter = TechCardExporter(
        api_key="your_api_key",
        org_id="your_org_id"
    )
    
    exporter.export_to_excel()
```

---

## ПОЛЕЗНЫЕ СОВЕТЫ

### 1. Обработка ошибок API
```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Ошибка: {e.response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Ошибка запроса: {e}")
```

### 2. Кэширование данных
```python
import json
import time
from functools import wraps

def cache_result(ttl=3600):
    def decorator(func):
        cache = {}
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator
```

### 3. Логирование операций
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iiko_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Начало операции получения данных")
```

---

## ЗАКЛЮЧЕНИЕ

Эти примеры можно адаптировать под ваши конкретные потребности. Основные компоненты для любой интеграции:

1. **Получение данных** из IIKO API
2. **Трансформация** данных в нужный формат
3. **Загрузка** в целевую систему (Excel, Google Sheets, 1С, etc.)
4. **Логирование** и **обработка ошибок**

**Успешной разработки!**

