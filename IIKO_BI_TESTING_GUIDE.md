# 🧪 РУКОВОДСТВО ПО ТЕСТИРОВАНИЮ IIKO BI ИНТЕГРАЦИИ

**Дата:** 2025-01-XX  
**Цель:** Протестировать новые методы для получения OLAP отчетов из IIKO RMS

---

## 📋 ПРЕДВАРИТЕЛЬНЫЕ УСЛОВИЯ

### 1. Убедись что Backend запущен:
```bash
cd backend
# Если нет виртуального окружения - создай
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Установи зависимости
pip install -r requirements.txt

# Запусти backend
uvicorn app.main:app --reload --port 8000
```

### 2. Проверь подключение к MongoDB:
- Убедись что MongoDB доступна
- Проверь переменные окружения в `backend/.env`:
  ```
  MONGODB_URI=...
  DB_NAME=receptor_copilot
  ```

### 3. Убедись что у тебя есть IIKO RMS credentials:
- Host (например: `edison-bar.iiko.it`)
- Login
- Password

---

## 🚀 ШАГИ ДЛЯ ТЕСТИРОВАНИЯ

### ШАГ 1: Подключение к IIKO RMS (если еще не подключен)

**Endpoint:** `POST /api/iiko/rms/connect`

**Request Body:**
```json
{
  "host": "твой-host.iiko.it",
  "login": "твой-логин",
  "password": "твой-пароль",
  "user_id": "default_user"
}
```

**cURL команда:**
```bash
curl -X POST http://localhost:8000/api/iiko/rms/connect \
  -H "Content-Type: application/json" \
  -d '{
    "host": "edison-bar.iiko.it",
    "login": "твой-логин",
    "password": "твой-пароль",
    "user_id": "default_user"
  }'
```

**Ожидаемый ответ:**
```json
{
  "status": "connected",
  "host": "edison-bar.iiko.it",
  "organizations": [...],
  "message": "Успешно подключено к iiko RMS"
}
```

✅ **Проверка:** Если получил `"status": "connected"` - переходи к следующему шагу!

---

### ШАГ 2: Проверка статуса подключения

**Endpoint:** `GET /api/iiko/rms/status/{user_id}`

**cURL команда:**
```bash
curl http://localhost:8000/api/iiko/rms/status/default_user
```

**Ожидаемый ответ:**
```json
{
  "status": "connected",
  "host": "...",
  "organization_name": "..."
}
```

✅ **Проверка:** Статус должен быть `"connected"`

---

### ШАГ 3: Получить доступные поля OLAP отчета (ТЕСТ 1)

**Endpoint:** `GET /api/iiko/rms/bi/olap-columns/{user_id}?report_type=SALES`

**cURL команда:**
```bash
curl "http://localhost:8000/api/iiko/rms/bi/olap-columns/default_user?report_type=SALES"
```

**Что проверяем:**
- ✅ Запрос выполняется без ошибок
- ✅ В ответе есть поле `columns` с описанием доступных полей
- ✅ Есть поля типа `DishName`, `DishSumInt`, `DishAmountInt`

**Пример успешного ответа:**
```json
{
  "status": "success",
  "columns": {
    "DishName": {
      "name": "Название блюда",
      "type": "STRING",
      "groupingAllowed": true
    },
    "DishSumInt": {
      "name": "Сумма продаж",
      "type": "MONEY",
      "aggregationAllowed": true
    }
  },
  "message": "Доступные поля для отчета SALES"
}
```

---

### ШАГ 4: Получить отчет по продажам за вчера (ТЕСТ 2)

**Endpoint:** `POST /api/iiko/rms/bi/olap-report`

**Request Body:**
```json
{
  "user_id": "default_user",
  "report_type": "SALES",
  "period_type": "YESTERDAY",
  "group_by": "dish"
}
```

**cURL команда:**
```bash
curl -X POST http://localhost:8000/api/iiko/rms/bi/olap-report \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "default_user",
    "report_type": "SALES",
    "period_type": "YESTERDAY",
    "group_by": "dish"
  }'
```

**Что проверяем:**
- ✅ Запрос выполняется без ошибок
- ✅ В ответе есть поле `report.data` с массивом строк отчета
- ✅ Каждая строка содержит `DishName`, `DishSumInt`, `DishAmountInt`
- ✅ Есть поле `summary` с итогами

**Пример успешного ответа:**
```json
{
  "status": "success",
  "report": {
    "report_type": "SALES",
    "data": [
      {
        "DishName": "Борщ украинский",
        "DishGroup": "Супы",
        "DishAmountInt": 15,
        "DishSumInt": 4500
      }
    ],
    "summary": [...],
    "row_count": 10
  },
  "message": "Отчет получен успешно (10 строк)"
}
```

---

### ШАГ 5: Получить выручку за месяц (ТЕСТ 3)

**Endpoint:** `GET /api/iiko/rms/bi/revenue/{user_id}?period_type=LAST_MONTH`

**cURL команда:**
```bash
curl "http://localhost:8000/api/iiko/rms/bi/revenue/default_user?period_type=LAST_MONTH"
```

**Что проверяем:**
- ✅ Запрос выполняется без ошибок
- ✅ В ответе есть данные по выручке
- ✅ Данные сгруппированы по датам (если `group_by_row_fields` = `["OpenDate.Typed"]`)

---

### ШАГ 6: Получить топ блюд (ТЕСТ 4)

**Endpoint:** `GET /api/iiko/rms/bi/dish-statistics/{user_id}?period_type=LAST_MONTH&top_n=5`

**cURL команда:**
```bash
curl "http://localhost:8000/api/iiko/rms/bi/dish-statistics/default_user?period_type=LAST_MONTH&top_n=5"
```

**Что проверяем:**
- ✅ Запрос выполняется без ошибок
- ✅ В ответе есть топ-N блюд
- ✅ Блюда отсортированы по сумме продаж (от большего к меньшему)

**Пример успешного ответа:**
```json
{
  "status": "success",
  "statistics": {
    "report_type": "SALES",
    "data": [
      {
        "DishName": "Борщ",
        "DishSumInt": 45000,
        "DishAmountInt": 150
      },
      {
        "DishName": "Паста карбонара",
        "DishSumInt": 32000,
        "DishAmountInt": 80
      }
    ],
    "top_n": 5
  },
  "message": "Статистика получена: топ 5 блюд"
}
```

---

## 🧪 АЛЬТЕРНАТИВНО: Тестирование через Postman/Insomnia

### 1. Импорт коллекции

Создай коллекцию со следующими запросами:

**1. Connect RMS:**
- Method: `POST`
- URL: `http://localhost:8000/api/iiko/rms/connect`
- Body (JSON):
```json
{
  "host": "твой-host",
  "login": "твой-логин",
  "password": "твой-пароль",
  "user_id": "default_user"
}
```

**2. Get OLAP Columns:**
- Method: `GET`
- URL: `http://localhost:8000/api/iiko/rms/bi/olap-columns/default_user?report_type=SALES`

**3. Get Sales Report:**
- Method: `POST`
- URL: `http://localhost:8000/api/iiko/rms/bi/olap-report`
- Body (JSON):
```json
{
  "user_id": "default_user",
  "period_type": "YESTERDAY",
  "group_by": "dish"
}
```

---

## ⚠️ ВОЗМОЖНЫЕ ОШИБКИ И РЕШЕНИЯ

### Ошибка 1: "IIKO RMS не подключен"
**Решение:**
- Выполни ШАГ 1 (подключение к RMS)
- Проверь что `user_id` совпадает во всех запросах

### Ошибка 2: "Authentication failed"
**Решение:**
- Проверь правильность credentials (host, login, password)
- Убедись что сервер RMS доступен
- Проверь что у пользователя есть права на получение отчетов

### Ошибка 3: "Invalid OLAP request"
**Решение:**
- Проверь формат дат (YYYY-MM-DD)
- Убедись что указан фильтр по дате
- Проверь названия полей в `group_by_row_fields` и `aggregate_fields`

### Ошибка 4: Пустой отчет (data: [])
**Это нормально если:**
- В указанный период не было продаж
- Период слишком короткий
- Организация не выбрана или указана неверная

---

## 📊 ПРОВЕРКА РЕЗУЛЬТАТОВ

### ✅ Что должно работать:

1. ✅ Подключение к RMS успешно
2. ✅ Получение списка полей OLAP работает
3. ✅ Отчет по продажам возвращает данные
4. ✅ Статистика по блюдам работает
5. ✅ Выручка по периодам работает

### 📝 Что записать в результаты:

- [ ] Какие endpoints работают
- [ ] Какие данные возвращаются
- [ ] Время выполнения запросов
- [ ] Ошибки (если есть)
- [ ] Формат данных в ответах

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ ПОСЛЕ ТЕСТИРОВАНИЯ

После успешного тестирования:

1. ✅ Зафиксируй результаты тестирования
2. ✅ Если есть ошибки - сообщи, исправлю!
3. ✅ Переходим к Этапу 2 (хранение данных в MongoDB)
4. ✅ Или сразу к интеграции в чат

---

## 💡 БЫСТРЫЙ ТЕСТ (все в одной команде)

Если у тебя уже подключен RMS, можно протестировать все сразу:

```bash
# 1. Проверка статуса
curl http://localhost:8000/api/iiko/rms/status/default_user

# 2. Получить поля
curl "http://localhost:8000/api/iiko/rms/bi/olap-columns/default_user?report_type=SALES"

# 3. Получить отчет за вчера
curl -X POST http://localhost:8000/api/iiko/rms/bi/olap-report \
  -H "Content-Type: application/json" \
  -d '{"user_id":"default_user","period_type":"YESTERDAY","group_by":"dish"}'

# 4. Топ блюд
curl "http://localhost:8000/api/iiko/rms/bi/dish-statistics/default_user?period_type=LAST_MONTH&top_n=5"
```

---

**Удачи с тестированием! 🚀**

Если что-то не работает - пиши, разберемся! 💪

