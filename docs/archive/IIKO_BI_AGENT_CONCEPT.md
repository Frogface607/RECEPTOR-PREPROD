# IIKO Business Intelligence Agent - Концепция

## 🎯 Цель
Создать AI-агента, который напрямую работает с iiko API для получения реальных данных и предоставления бизнес-аналитики, дашбордов и отчетов.

## 📊 Источники данных (через iiko API)

### 1. iiko RMS API (прямое подключение к серверу)
- ✅ Организации (`get_organizations`)
- ✅ Номенклатура (`fetch_nomenclature`) - товары, блюда, группы
- ✅ Цены (`fetch_prices`) - актуальные цены по организациям
- 🔄 **Нужно добавить:**
  - Продажи/заказы (`/resto/api/v2/reports/olap`)
  - Выручка по периодам
  - Популярные блюда
  - Средний чек
  - Оборот по категориям
  - Статистика по времени (часы пик)
  - Складские остатки
  - Движение товаров

### 2. iikoCloud API (облачный)
- ✅ Организации
- ✅ Товары и группы
- 🔄 **Нужно добавить:**
  - Отчеты по продажам
  - Аналитика
  - Финансовые данные

## 🏗️ Архитектура BI-агента

```
┌─────────────────────────────────────────┐
│         BI Agent (AI Assistant)         │
│  - Понимает запросы на русском          │
│  - Определяет какие данные нужны        │
│  - Формирует запросы к API              │
│  - Анализирует результаты               │
│  - Генерирует отчеты/дашборды           │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────────┐
│ iiko RMS    │  │ iikoCloud API   │
│ Service     │  │ Service         │
│             │  │                 │
│ - Orders    │  │ - Reports       │
│ - Sales     │  │ - Analytics     │
│ - Inventory │  │ - Financials    │
└─────────────┘  └─────────────────┘
```

## 🔧 Компоненты

### 1. `iiko_bi_agent.py` - Основной агент
```python
class IikoBIAgent:
    """
    AI-агент для бизнес-аналитики iiko
    Использует LLM для понимания запросов и генерации отчетов
    """
    
    def __init__(self):
        self.rms_service = get_iiko_rms_service()
        self.iiko_service = get_iiko_service()
        self.llm_client = get_openai_client()
    
    async def process_query(self, query: str, user_id: str, organization_id: str):
        """
        Обрабатывает запрос пользователя:
        1. Определяет тип запроса (продажи, меню, аналитика)
        2. Выбирает нужные API endpoints
        3. Получает данные из iiko
        4. Анализирует с помощью LLM
        5. Генерирует отчет/дашборд
        """
        pass
    
    async def get_sales_report(self, org_id: str, date_from: datetime, date_to: datetime):
        """Получить отчет по продажам"""
        pass
    
    async def get_popular_dishes(self, org_id: str, period: str):
        """Топ блюд за период"""
        pass
    
    async def get_revenue_analytics(self, org_id: str, period: str):
        """Аналитика по выручке"""
        pass
```

### 2. `iiko_analytics_client.py` - Расширение RMS клиента
```python
class IikoAnalyticsClient(IikoRmsClient):
    """
    Расширенный клиент для получения аналитических данных
    """
    
    def get_sales_report(self, organization_id: str, date_from: datetime, date_to: datetime):
        """Получить отчет по продажам через OLAP API"""
        # /resto/api/v2/reports/olap
        pass
    
    def get_orders(self, organization_id: str, date_from: datetime, date_to: datetime):
        """Получить заказы за период"""
        # /resto/api/v2/orders
        pass
    
    def get_revenue_by_period(self, organization_id: str, period: str):
        """Выручка по периодам"""
        pass
    
    def get_dish_statistics(self, organization_id: str, date_from: datetime, date_to: datetime):
        """Статистика по блюдам"""
        pass
```

### 3. `bi_dashboard_generator.py` - Генератор дашбордов
```python
class BIDashboardGenerator:
    """
    Генерирует дашборды и визуализации на основе данных iiko
    """
    
    def generate_sales_dashboard(self, data: Dict):
        """Генерация дашборда продаж"""
        pass
    
    def generate_revenue_chart(self, data: List[Dict]):
        """График выручки"""
        pass
    
    def generate_dish_popularity_chart(self, data: List[Dict]):
        """График популярности блюд"""
        pass
```

## 📋 Функциональность

### Запросы, которые должен понимать агент:

1. **Продажи:**
   - "Покажи продажи за сегодня"
   - "Какая выручка за последнюю неделю?"
   - "Сравни продажи этого месяца с прошлым"

2. **Меню:**
   - "Какие блюда самые популярные?"
   - "Что продается хуже всего?"
   - "Средний чек за сегодня"

3. **Аналитика:**
   - "В какое время больше всего заказов?"
   - "Какие категории приносят больше всего прибыли?"
   - "Динамика продаж по дням недели"

4. **Склад:**
   - "Какие товары заканчиваются?"
   - "Остатки на складе"
   - "Движение товаров за период"

5. **Финансы:**
   - "Прибыль за месяц"
   - "Себестоимость блюд"
   - "Маржинальность меню"

## 🛠️ Реализация (поэтапно)

### Этап 1: Расширение RMS клиента
- Добавить методы для получения отчетов через OLAP API
- Реализовать получение заказов и продаж
- Добавить кэширование данных

### Этап 2: Создание BI-агента
- Интеграция с LLM для понимания запросов
- Определение типа запроса и выбор API endpoints
- Получение и обработка данных

### Этап 3: Генерация отчетов
- Создание структурированных отчетов
- Генерация графиков и визуализаций
- Экспорт в различные форматы (PDF, Excel, JSON)

### Этап 4: Дашборды
- Интерактивные дашборды
- Автоматическое обновление данных
- Настраиваемые виджеты

## 📚 Документация iiko API (для справки)

Используется для понимания доступных endpoints:
- `backend/data/knowledge_base/receptor_iiko_technical.md` - техническая документация
- Официальная документация: https://api-ru.iiko.services/docs
- RMS API: https://ru.iiko.help/articles/#!api-docs

## 🔐 Безопасность

- Все запросы через существующие сервисы (уже есть авторизация)
- Изоляция данных по user_id
- Кэширование для снижения нагрузки на API
- Rate limiting для защиты от перегрузки

## 🚀 Интеграция с существующей системой

- Использует `IikoRmsService` и `IikoService`
- Интегрируется с ассистентом через tool-calling
- Сохраняет отчеты в MongoDB
- Предоставляет API endpoints для фронтенда

