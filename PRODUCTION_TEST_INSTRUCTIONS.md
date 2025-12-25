# 🚀 ИНСТРУКЦИЯ: ТЕСТИРОВАНИЕ НА PRODUCTION

**Production URL:** https://receptorai.pro  
**Backend:** Railway (автоматический deploy после push)

---

## ✅ ЧТО СДЕЛАНО:

1. ✅ Добавлены методы для OLAP отчетов в `iiko_rms_client.py`
2. ✅ Добавлены тестовые endpoints в `api/iiko.py`
3. ✅ Код готов к deploy

---

## 🚀 ЧТО ДЕЛАТЬ:

### ШАГ 1: Deploy на Railway

**Вариант A: Автоматический deploy (если настроен):**
- Просто закоммить изменения и запушить в репозиторий
- Railway автоматически задеплоит

**Вариант B: Ручной deploy:**
```bash
# Закоммить изменения
git add .
git commit -m "feat: добавить OLAP отчеты для IIKO BI"
git push origin main
```

### ШАГ 2: Убедись что backend задеплоился

Проверь что backend работает:
```bash
curl https://receptor-preprod-production.up.railway.app/
```

Должен вернуться:
```json
{"message": "Welcome to RECEPTOR CO-PILOT API v2.0", "status": "online"}
```

### ШАГ 3: Проверь что у тебя есть IIKO RMS подключение

Открой сайт: **https://receptorai.pro**

1. Зайди в настройки/интеграции
2. Проверь что IIKO RMS подключен
3. Запомни `user_id` (или используй тот который у тебя есть)

### ШАГ 4: Протестируй новые endpoints

**BASE URL:** `https://receptor-preprod-production.up.railway.app/api/iiko`  
**Frontend:** https://receptorai.pro

**Важно:** Используй `default_user` как user_id (или тот который у тебя есть)

---

## 🧪 ТЕСТЫ НА PRODUCTION:

### ТЕСТ 1: Проверка статуса RMS подключения

```bash
curl "https://receptor-preprod-production.up.railway.app/api/iiko/rms/status/твой-user-id"
```

**Или через браузер:**
```
https://receptor-preprod-production.up.railway.app/api/iiko/rms/status/твой-user-id
```

✅ **Ожидаем:** `{"status": "connected", ...}`

---

### ТЕСТ 2: Получить доступные поля OLAP отчета

```bash
curl "https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/olap-columns/твой-user-id?report_type=SALES"
```

**Или через браузер:**
```
https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/olap-columns/твой-user-id?report_type=SALES
```

✅ **Ожидаем:** Список полей с их типами и описаниями

---

### ТЕСТ 3: Получить отчет по продажам за вчера

```bash
curl -X POST "https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/olap-report" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "твой-user-id",
    "report_type": "SALES",
    "period_type": "YESTERDAY",
    "group_by": "dish"
  }'
```

✅ **Ожидаем:** Отчет с данными по блюдам и продажам

---

### ТЕСТ 4: Получить топ-5 блюд за месяц

```bash
curl "https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/dish-statistics/твой-user-id?period_type=LAST_MONTH&top_n=5"
```

**Или через браузер:**
```
https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/dish-statistics/твой-user-id?period_type=LAST_MONTH&top_n=5
```

✅ **Ожидаем:** Топ-5 блюд с количеством продаж и выручкой

---

### ТЕСТ 5: Получить выручку за месяц

```bash
curl "https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/revenue/твой-user-id?period_type=LAST_MONTH"
```

**Или через браузер:**
```
https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/revenue/твой-user-id?period_type=LAST_MONTH
```

✅ **Ожидаем:** Данные по выручке с группировкой по датам

---

## 🔧 АЛЬТЕРНАТИВА: Тестирование через Frontend (если нужно)

Можешь также протестировать через консоль браузера на receptorai.pro:

1. Открой **https://receptorai.pro**
2. Открой DevTools (F12)
3. В консоли выполни:

```javascript
// Замени 'твой-user-id' на реальный
const userId = 'твой-user-id';
const API_URL = 'https://receptor-preprod-production.up.railway.app/api/iiko';

// Тест 1: Статус
fetch(`${API_URL}/rms/status/${userId}`)
  .then(r => r.json())
  .then(console.log);

// Тест 2: Поля OLAP
fetch(`${API_URL}/rms/bi/olap-columns/${userId}?report_type=SALES`)
  .then(r => r.json())
  .then(console.log);

// Тест 3: Отчет по продажам
fetch(`${API_URL}/rms/bi/olap-report`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: userId,
    period_type: 'YESTERDAY',
    group_by: 'dish'
  })
})
  .then(r => r.json())
  .then(console.log);

// Тест 4: Топ блюд
fetch(`${API_URL}/rms/bi/dish-statistics/${userId}?period_type=LAST_MONTH&top_n=5`)
  .then(r => r.json())
  .then(console.log);
```

---

## 📋 ЧТО ПРОВЕРИТЬ:

✅ Все запросы возвращают `"status": "success"`  
✅ В отчетах есть реальные данные (если были продажи в указанный период)  
✅ Нет ошибок 500 в ответах  
✅ Время выполнения запросов разумное (< 15 секунд для production)

---

## ⚠️ ВОЗМОЖНЫЕ ПРОБЛЕМЫ:

### Проблема 1: Backend не задеплоился
**Решение:** 
- Проверь Railway dashboard - есть ли ошибки сборки
- Проверь логи в Railway

### Проблема 2: CORS ошибки
**Решение:**
- Backend уже настроен на CORS для всех origins
- Если есть проблемы - проверь `backend/app/main.py`

### Проблема 3: 404 Not Found
**Решение:**
- Убедись что используешь правильный URL Railway
- Проверь что endpoint существует в `api/iiko.py`

### Проблема 4: RMS не подключен
**Решение:**
- Подключись через UI на receptorai.pro
- Или используй endpoint `/api/iiko/rms/connect`

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ:

После успешного тестирования:

1. ✅ Зафиксируй результаты
2. ✅ Если все работает - переходим к Этапу 2 (хранение в MongoDB)
3. ✅ Если есть ошибки - пиши, исправлю!

---

**Готово! Тестируй на production! 🚀**

Если нужна помощь с deploy или что-то не работает - пиши!

