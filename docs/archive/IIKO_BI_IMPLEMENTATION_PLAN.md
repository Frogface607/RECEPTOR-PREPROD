# 🎯 ПЛАН РЕАЛИЗАЦИИ IIKO BI ИНТЕГРАЦИИ

**Дата:** 2025-01-XX  
**Цель:** Научить копайлота получать любую информацию из IIKO + BI Dashboard

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### ✅ Что уже работает:
1. **IIKO Cloud API** - подключение, номенклатура, отчеты
   - `get_sales_report()` - продажи
   - `get_orders()` - заказы
   - `get_employees()` - сотрудники
   - `get_stock_report()` - остатки
   - `get_purchases_report()` - закупки

2. **IIKO RMS Server** - подключение, номенклатура
   - Нужно добавить: OLAP отчеты, продажи, аналитика

3. **Chat Memory** - базовая:
   - История сообщений передается в LLM
   - Профиль заведения
   - Deep research данные

### ❌ Что нужно добавить:
1. **RMS OLAP API** - отчеты через `/resto/api/v2/reports/olap`
2. **Ежедневная синхронизация** - background job для подтягивания данных
3. **Хранение аналитики** - MongoDB коллекции для отчетов
4. **Контекст в чате** - интеграция аналитики в память
5. **BI Dashboard Frontend** - вкладка с отчетами

---

## 🏗️ АРХИТЕКТУРА

```
┌─────────────────────────────────────────┐
│         RECEPTOR CO-PILOT               │
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │ Chat (LLM)   │◄───┤ BI Context   │  │
│  │ + Memory     │    │ + Analytics  │  │
│  └──────────────┘    └──────────────┘  │
│         │                    │          │
│         └────────┬───────────┘          │
│                  │                      │
│         ┌────────▼──────────┐           │
│         │ BI Service        │           │
│         │ - Fetch data      │           │
│         │ - Store reports   │           │
│         │ - Daily sync      │           │
│         └────────┬──────────┘           │
└──────────────────┼──────────────────────┘
                   │
       ┌───────────┴───────────┐
       │                       │
┌──────▼──────┐      ┌────────▼──────┐
│ IIKO Cloud  │      │ IIKO RMS      │
│ API         │      │ OLAP API      │
│             │      │               │
│ - Reports   │      │ - Sales       │
│ - Orders    │      │ - Analytics   │
│ - Employees │      │ - Inventory   │
└─────────────┘      └───────────────┘
```

---

## 📋 ПЛАН РЕАЛИЗАЦИИ

### **ЭТАП 1: Расширение IIKO RMS Client** ⏱️ 2-3 часа

**Задачи:**
1. Добавить методы в `iiko_rms_client.py`:
   - `get_olap_report()` - получение OLAP отчетов
   - `get_sales_report()` - отчет по продажам через OLAP
   - `get_dish_statistics()` - статистика по блюдам
   - `get_revenue_by_period()` - выручка по периодам

2. Изучить OLAP API документацию
3. Реализовать парсинг OLAP ответов

**Файлы:**
- `backend/app/services/iiko/iiko_rms_client.py` - расширение
- `backend/data/knowledge_base/iiko_api_full_documentation.md` - документация

---

### **ЭТАП 2: Хранение аналитических данных** ⏱️ 2 часа

**Структура MongoDB коллекций:**

```javascript
// iiko_analytics_reports
{
  user_id: String,
  organization_id: String,
  report_type: String, // "sales", "revenue", "dishes", "inventory"
  date_from: Date,
  date_to: Date,
  data: Object, // сырые данные из IIKO
  metrics: Object, // обработанные метрики
  synced_at: Date,
  created_at: Date
}

// iiko_daily_sync_log
{
  user_id: String,
  organization_id: String,
  sync_date: Date,
  reports_synced: [String], // типы отчетов
  status: String, // "success", "failed", "partial"
  error: String,
  synced_at: Date
}
```

**Задачи:**
1. Создать модели данных (Pydantic)
2. Создать сервис для сохранения отчетов
3. Индексы для быстрого поиска

**Файлы:**
- `backend/app/services/iiko/bi_storage_service.py` - новый файл
- `backend/app/services/iiko/iiko_models.py` - модели

---

### **ЭТАП 3: Ежедневная синхронизация** ⏱️ 3-4 часа

**Background Job для синхронизации:**

1. **Celery/APScheduler** - планировщик задач
2. **Daily Sync Task:**
   - Для каждого пользователя с подключенным IIKO
   - Получить отчеты за вчерашний день
   - Сохранить в MongoDB
   - Обновить метрики

**Задачи:**
1. Выбрать планировщик (APScheduler проще для начала)
2. Создать sync service
3. Настроить ежедневный запуск (например, в 02:00)
4. Обработка ошибок и retry логика

**Файлы:**
- `backend/app/services/iiko/bi_sync_service.py` - новый файл
- `backend/app/main.py` - запуск планировщика

---

### **ЭТАП 4: Интеграция в Chat Context** ⏱️ 2-3 часа

**Улучшение памяти копайлота:**

1. **Загрузка аналитики в контекст:**
   - При запросах про продажи/выручку - загружать последние отчеты
   - Добавлять в system prompt контекст с метриками
   - Упоминать доступные данные в ответах

2. **Intent Detection расширение:**
   - Распознавать запросы про аналитику
   - Определять, какие отчеты нужны
   - Автоматически подтягивать данные

**Задачи:**
1. Расширить `detect_intent()` в `chat.py`
2. Создать функцию загрузки аналитики для контекста
3. Обновить system prompt с информацией об отчетах

**Файлы:**
- `backend/app/api/chat.py` - расширение
- `backend/app/services/iiko/bi_context_service.py` - новый файл

---

### **ЭТАП 5: BI Dashboard API** ⏱️ 3-4 часа

**Endpoints для фронтенда:**

```python
GET /api/iiko/bi/dashboard/{user_id}
  - Возвращает сводные метрики за период

GET /api/iiko/bi/reports/{user_id}
  - Список доступных отчетов
  - Фильтры: date_from, date_to, report_type

GET /api/iiko/bi/metrics/{user_id}
  - Ключевые метрики (выручка, средний чек, топ блюда)

POST /api/iiko/bi/sync-now/{user_id}
  - Принудительная синхронизация отчетов
```

**Задачи:**
1. Создать новый router `bi.py`
2. Реализовать endpoints
3. Агрегация метрик
4. Кэширование для производительности

**Файлы:**
- `backend/app/api/bi.py` - новый файл
- `backend/app/main.py` - подключение router

---

### **ЭТАП 6: Frontend BI Dashboard** ⏱️ 4-6 часов

**UI компоненты:**

1. **Вкладка "BI"** в боковом меню
2. **Dashboard виджеты:**
   - Выручка (график по дням/неделям)
   - Средний чек
   - Топ-10 блюд
   - Часы пик
   - Остатки на складе

3. **Фильтры:**
   - Период (сегодня, неделя, месяц)
   - Тип отчета

**Задачи:**
1. Создать компонент `BIDashboard.jsx`
2. Подключить к API
3. Визуализация (Chart.js или Recharts)
4. Адаптивный дизайн

**Файлы:**
- `frontend/src/components/BIDashboard.jsx` - новый файл
- `frontend/src/App.js` - добавление вкладки

---

## 📊 ПРИОРИТИЗАЦИЯ

### **Week 1: Backend Foundation**
- [x] Этап 1: Расширение RMS Client (OLAP)
- [x] Этап 2: Хранение данных
- [x] Этап 3: Daily Sync

### **Week 2: Integration & Frontend**
- [ ] Этап 4: Chat Context
- [ ] Этап 5: BI API
- [ ] Этап 6: Frontend Dashboard

---

## 🔧 ТЕХНИЧЕСКИЕ ДЕТАЛИ

### **OLAP API Endpoints (RMS Server):**

```
POST /resto/api/v2/reports/olap
Body: {
  "reportType": "SALES", // SALES, REVENUE, DISHES
  "buildSummary": true,
  "from": "2025-01-01 00:00:00",
  "to": "2025-01-31 23:59:59",
  "filters": {...}
}
```

### **Cloud API Endpoints (уже реализованы):**
- `/api/v1/deliveries/by_delivery_date_and_phone` - доставки
- `/api/v1/orders` - заказы
- `/api/v1/reports` - отчеты

---

## 🎯 SUCCESS METRICS

1. ✅ Копайлот отвечает на вопросы про продажи с реальными данными
2. ✅ Данные обновляются раз в день автоматически
3. ✅ BI Dashboard показывает актуальные метрики
4. ✅ Пользователи могут задавать вопросы типа "Какая выручка за неделю?"

---

## 🚀 NEXT STEPS

Начинаем с **ЭТАПА 1** - расширение RMS Client для OLAP отчетов!

