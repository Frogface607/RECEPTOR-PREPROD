# МОДУЛЬ 06: IIKO TECHNICAL INTEGRATION
## Техническая документация для интеграции с iiko 2024

---

## 🏗️ АРХИТЕКТУРА IIKO

### ОСНОВНЫЕ МОДУЛИ

#### 1. **iikoFront** (фронт-офис)
```
Назначение: POS-система для кассиров и официантов
Функции:
  - Прием заказов
  - Работа с чеками
  - Управление столами
  - Интеграция с фискальным регистратором

Платформа: Windows (desktop)
Лицензия: от 15 000 руб/терминал
Официальная документация: https://ru.iiko.help/smart/project-iikofront
```

#### 2. **iikoOffice** (back-офис)
```
Назначение: Управление рестораном (менеджмент)
Функции:
  - Управление меню
  - Складской учет
  - Финансовая отчетность
  - HR (графики, зарплаты)
  - Аналитика

Платформа: Windows (desktop) / Web
Лицензия: включена в основной пакет
```

#### 3. **iikoChain** (сетевое управление)
```
Назначение: Управление сетью ресторанов
Функции:
  - Централизованное меню
  - Консолидированная отчетность
  - Управление поставщиками
  - Франчайзинг

Для: 2+ точек
Лицензия: от 100 000 руб/год
```

#### 4. **iikoDelivery** (доставка)
```
Назначение: Управление доставкой
Функции:
  - Call-центр
  - Курьерская служба
  - Интеграция с агрегаторами
  - Tracking заказов

Лицензия: от 30 000 руб/год
```

#### 5. **iikoCard** (лояльность)
```
Назначение: Программа лояльности
Функции:
  - Бонусная система
  - Скидки/промокоды
  - CRM (база гостей)
  - SMS/Email рассылки

Лицензия: от 20 000 руб/год
```

---

## 🔌 API ЭКОСИСТЕМА IIKO

### 1. iikoWeb Public API (REST)

**Базовый URL:** `https://api-ru.iiko.services`

**Версия:** API v2 (актуальная)

**Документация:** https://api-ru.iiko.services/docs

**Postman Collection:** https://documenter.getpostman.com/view/2896430/TVemBpmn

---

#### АУТЕНТИФИКАЦИЯ

**Endpoint:** `POST /api/1/access_token`

**Тело запроса:**
```json
{
  "apiLogin": "your_api_login"
}
```

**Ответ:**
```json
{
  "correlationId": "uuid",
  "token": "access_token_here",
  "expiresAt": "2024-11-28T15:30:00Z"
}
```

**Python пример:**
```python
import requests

API_URL = "https://api-ru.iiko.services/api/1"
API_LOGIN = "your_api_login"

def get_access_token():
    response = requests.post(
        f"{API_URL}/access_token",
        json={"apiLogin": API_LOGIN}
    )
    return response.json()["token"]

token = get_access_token()
headers = {"Authorization": f"Bearer {token}"}
```

---

#### ОСНОВНЫЕ ENDPOINTS

##### 1. Получение меню:

```
GET /api/1/nomenclature
```

**Параметры:**
```json
{
  "organizationId": "uuid",
  "startRevision": 0
}
```

**Ответ:**
```json
{
  "products": [
    {
      "id": "uuid",
      "name": "Паста Карбонара",
      "description": "Классическая итальянская паста",
      "price": 750.00,
      "category": "Основные блюда",
      "images": ["url1", "url2"],
      "nutritionalInfo": {
        "calories": 650,
        "proteins": 25,
        "fats": 30,
        "carbohydrates": 70
      }
    }
  ]
}
```

##### 2. Создание заказа:

```
POST /api/1/order/create
```

**Тело:**
```json
{
  "organizationId": "uuid",
  "order": {
    "phone": "+79991234567",
    "items": [
      {
        "productId": "uuid",
        "amount": 1,
        "modifiers": []
      }
    ],
    "payments": [
      {
        "sum": 750.00,
        "paymentTypeId": "uuid",
        "isProcessedExternally": true
      }
    ]
  }
}
```

##### 3. Получение отчетов:

```
POST /api/1/reports/olap
```

**Пример (выручка за день):**
```json
{
  "reportType": "SALES",
  "organizationId": "uuid",
  "dateFrom": "2024-11-28T00:00:00",
  "dateTo": "2024-11-28T23:59:59",
  "groupByColFields": ["OrderType"]
}
```

---

### 2. iikoFront API SDK (C# плагины)

**GitHub:** https://github.com/iiko/front.api.sdk

**Назначение:** Разработка плагинов для iikoFront

**Язык:** C# (.NET Framework 4.7.2+)

**Возможности:**
- Кастомные экраны
- Интеграция с внешними устройствами
- Обработка событий (новый заказ, оплата)
- Модификация UI

**Пример плагина (Hello World):**
```csharp
using Resto.Front.Api;
using Resto.Front.Api.Attributes;

[PluginLicenseModuleId(00000000-0000-0000-0000-000000000000)]
public sealed class SamplePlugin : IFrontPlugin
{
    public SamplePlugin()
    {
        PluginContext.Log.Info("Plugin loaded!");
        
        PluginContext.Operations.AddNotificationHandler(
            (order) => {
                PluginContext.Log.Info($"New order: {order.Number}");
            }
        );
    }
    
    public void Dispose() { }
}
```

**Развертывание:**
```
1. Скомпилировать .dll
2. Положить в: C:\Program Files\iiko\iikoFront\Plugins\
3. Перезапустить iikoFront
```

---

### 3. iikoTransport API (legacy, устаревший)

**Документация:** https://docs.google.com/document/d/1kuhs94UV_0oUkI2CI3uOsNo_dydmh9Q0LxzYEek_8WQ

**Статус:** Deprecated, мигрировать на iikoWeb API

**Использование:** Только для старых интеграций

---

### 4. iiko Cloud API (для SaaS iiko)

**Базовый URL:** `https://api-ru.iiko.services/cloud`

**Отличия от iikoWeb:**
- Облачная инфраструктура (без локального сервера)
- Subscription-модель
- Автообновления

---

## 🛠️ ИНТЕГРАЦИОННЫЕ ПРИМЕРЫ

### PYTHON: Получение меню и создание заказа

```python
import requests
from typing import Dict, List

class IikoAPI:
    def __init__(self, api_login: str):
        self.base_url = "https://api-ru.iiko.services/api/1"
        self.api_login = api_login
        self.token = None
        self.authenticate()
    
    def authenticate(self):
        """Получение access token"""
        response = requests.post(
            f"{self.base_url}/access_token",
            json={"apiLogin": self.api_login}
        )
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def get_organizations(self) -> List[Dict]:
        """Получение списка организаций"""
        response = requests.post(
            f"{self.base_url}/organizations",
            headers=self.headers
        )
        return response.json()["organizations"]
    
    def get_menu(self, org_id: str) -> Dict:
        """Получение меню организации"""
        response = requests.post(
            f"{self.base_url}/nomenclature",
            headers=self.headers,
            json={"organizationId": org_id}
        )
        return response.json()
    
    def calculate_food_cost(self, org_id: str, product_id: str) -> float:
        """Расчет food-cost блюда"""
        menu = self.get_menu(org_id)
        
        product = next(
            (p for p in menu["products"] if p["id"] == product_id),
            None
        )
        
        if not product:
            return 0.0
        
        # Себестоимость из модификаторов/ингредиентов
        cost = sum(
            ing["price"] * ing["amount"]
            for ing in product.get("modifiers", [])
        )
        
        food_cost_percent = (cost / product["price"]) * 100
        return food_cost_percent

# Использование
api = IikoAPI("your_api_login")
orgs = api.get_organizations()
org_id = orgs[0]["id"]

food_cost = api.calculate_food_cost(org_id, "product_uuid")
print(f"Food-cost: {food_cost:.2f}%")
```

---

### PHP: Интеграция с доставкой

**Библиотека:** `russianprotein/iiko-transport`

**GitHub:** https://github.com/RussianProtein/iikoTransport

```php
<?php

use RussianProtein\IikoTransport\Client;

$client = new Client([
    'login' => 'your_login',
    'password' => 'your_password'
]);

// Получение меню
$nomenclature = $client->nomenclature()->get();

// Создание заказа доставки
$order = $client->orders()->create([
    'phone' => '+79991234567',
    'address' => [
        'street' => 'Ленина',
        'house' => '10',
        'flat' => '25'
    ],
    'items' => [
        [
            'id' => 'product_uuid',
            'amount' => 2
        ]
    ],
    'payment' => [
        'type' => 'card',
        'sum' => 1500.00
    ]
]);

echo "Order ID: " . $order['orderId'];
?>
```

---

### GO: Real-time мониторинг заказов

**Библиотека:** `iiko-go`

**Документация:** https://pkg.go.dev/github.com/wollzy/iiko-go

```go
package main

import (
    "fmt"
    "github.com/wollzy/iiko-go"
)

func main() {
    client := iiko.NewClient("your_api_login")
    
    // Авторизация
    err := client.Authenticate()
    if err != nil {
        panic(err)
    }
    
    // Получение организаций
    orgs, _ := client.GetOrganizations()
    orgID := orgs[0].ID
    
    // Мониторинг заказов (каждые 30 сек)
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        orders, _ := client.GetOrders(orgID, time.Now().Add(-1*time.Hour))
        
        for _, order := range orders {
            fmt.Printf("Order %s: %s (%.2f руб)\n",
                order.Number,
                order.Status,
                order.Sum)
        }
    }
}
```

---

## 🎯 КЕЙСЫ ИНТЕГРАЦИИ ДЛЯ RECEPTOR

### 1. АВТОМАТИЧЕСКИЙ FOOD-COST КАЛЬКУЛЯТОР

**Задача:** Рассчитывать food-cost каждого блюда в реальном времени

**Схема:**
```
iiko (номенклатура + цены) 
    ↓ API
RECEPTOR Backend
    ↓ Расчет
    ├─ Себестоимость ингредиентов
    ├─ Цена продажи
    └─ Food-cost %
    ↓
Dashboard (веб)
    └─ Алерты: food-cost > 35%
```

**Технологии:**
- Python/FastAPI (backend)
- iiko Web API (данные)
- PostgreSQL (хранение истории)
- Grafana (визуализация)

---

### 2. HR PERFORMANCE DASHBOARD

**Задача:** Отслеживание эффективности официантов

**Схема:**
```
iiko (заказы по официантам)
    ↓ API
RECEPTOR Analytics
    ├─ Продажи на официанта
    ├─ Средний чек
    ├─ Время обслуживания
    └─ Upsell эффективность
    ↓
Дашборд управляющего
    └─ KPI + автоматические премии
```

**Метрики:**
```python
def calculate_waiter_kpi(waiter_id: str, date: str):
    orders = iiko_api.get_orders_by_waiter(waiter_id, date)
    
    total_sales = sum(o["sum"] for o in orders)
    avg_check = total_sales / len(orders)
    upsell_rate = sum(
        1 for o in orders if "dessert" in o["items"]
    ) / len(orders)
    
    return {
        "sales": total_sales,
        "avg_check": avg_check,
        "upsell": upsell_rate * 100
    }
```

---

### 3. INVENTORY OPTIMIZATION

**Задача:** Прогнозировать закупки на основе продаж

**Схема:**
```
iiko (история продаж за 90 дней)
    ↓ API
ML Model (Prophet/ARIMA)
    ├─ Прогноз продаж на неделю
    ├─ Расчет необходимого запаса
    └─ Сезонность + тренды
    ↓
Закупочный лист
    └─ Автоматическая отправка поставщикам
```

---

### 4. MARKETING AUTOMATION

**Задача:** Персонализированные предложения на основе истории заказов

**Схема:**
```
iiko (заказы + телефоны гостей)
    ↓ API + iikoCard
RECEPTOR CRM
    ├─ Сегментация гостей
    ├─ RFM-анализ
    └─ Триггерные сценарии
    ↓
SMS/Email/Push
    └─ "Вы не заказывали пасту 2 недели, вот -20%"
```

---

### 5. COMPLIANCE MONITORING (HACCP)

**Задача:** Контроль соблюдения HACCP через iiko

**Схема:**
```
iiko (температура, сроки годности)
    ↓ API + IoT датчики
RECEPTOR HACCP Module
    ├─ Проверка температур
    ├─ Контроль сроков
    └─ Автоматические алерты
    ↓
Уведомления управляющему
    └─ "Холодильник #3: +8°C (норма 0-6°C)"
```

---

## 🔐 БЕЗОПАСНОСТЬ

### BEST PRACTICES

1. **Хранение токенов:**
```python
# ❌ Плохо
token = "hardcoded_token_here"

# ✅ Хорошо
import os
token = os.getenv("IIKO_API_TOKEN")
```

2. **Rate limiting:**
```python
# iiko API: максимум 100 запросов/минуту
from ratelimit import limits

@limits(calls=100, period=60)
def call_iiko_api():
    pass
```

3. **Обработка ошибок:**
```python
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        # Токен истек, переавторизация
        authenticate()
    elif e.response.status_code == 429:
        # Rate limit, ждем
        time.sleep(60)
```

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

### Официальная документация:
- **iiko Help Center:** https://ru.iiko.help
- **API Reference:** https://api-ru.iiko.services/docs
- **SDK GitHub:** https://github.com/iiko

### Сообщество:
- **Telegram:** @iiko_developers
- **Форум:** https://forum.iiko.ru

### Обучение:
- **iiko Academy:** https://academy.iiko.ru (видеокурсы)
- **Вебинары:** Еженедельно (анонсы на сайте)

---

## 🚀 ROADMAP ИНТЕГРАЦИИ

### ФАЗА 1: MVP (2 недели)
```
✅ Авторизация + получение меню
✅ Базовый food-cost калькулятор
✅ Дашборд с 3 метриками
```

### ФАЗА 2: ADVANCED (1 месяц)
```
✅ HR Performance Dashboard
✅ Inventory прогнозирование
✅ SMS-уведомления
```

### ФАЗА 3: SCALE (3 месяца)
```
✅ Multi-tenant (для сети ресторанов)
✅ ML прогнозы
✅ Мобильное приложение
```

---

## 🔄 ИСТОРИЯ ВЕРСИЙ

**Версия:** 1.0  
**Дата:** 2024-11-28  
**Источников:** 50+ технических документов  
**Следующее обновление:** Ежеквартально (API changes)

---

**ТЕГИ:** `#iiko` `#API` `#Integration` `#POS` `#Technical` `#SDK` `#REST`
