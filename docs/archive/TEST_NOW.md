# ⚡ БЫСТРЫЙ ТЕСТ НА PRODUCTION

**Backend:** https://receptor-preprod-production.up.railway.app  
**Frontend:** https://receptorai.pro

---

## 🚀 ШАГ 1: Закоммить и задеплоить изменения

```bash
git add .
git commit -m "feat: добавить OLAP отчеты для IIKO BI интеграции"
git push origin main
```

Railway автоматически задеплоит изменения (обычно 2-3 минуты).

---

## 🧪 ШАГ 2: Быстрые тесты (после deploy)

**BASE_URL:** `https://receptor-preprod-production.up.railway.app/api/iiko`

### ✅ ТЕСТ 1: Проверка статуса RMS
```
https://receptor-preprod-production.up.railway.app/api/iiko/rms/status/default_user
```
Открой в браузере → должен вернуть статус подключения

### ✅ ТЕСТ 2: Получить поля OLAP отчета
```
https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/olap-columns/default_user?report_type=SALES
```
Открой в браузере → должен вернуть список полей

### ✅ ТЕСТ 3: Отчет по продажам (POST запрос)

**Через curl:**
```bash
curl -X POST "https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/olap-report" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"default_user","period_type":"YESTERDAY","group_by":"dish"}'
```

**Через Postman/Insomnia:**
- Method: `POST`
- URL: `https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/olap-report`
- Body (JSON):
```json
{
  "user_id": "default_user",
  "period_type": "YESTERDAY",
  "group_by": "dish"
}
```

### ✅ ТЕСТ 4: Топ блюд
```
https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/dish-statistics/default_user?period_type=LAST_MONTH&top_n=5
```
Открой в браузере → должен вернуть топ-5 блюд

### ✅ ТЕСТ 5: Выручка
```
https://receptor-preprod-production.up.railway.app/api/iiko/rms/bi/revenue/default_user?period_type=LAST_MONTH
```
Открой в браузере → должен вернуть данные по выручке

---

## 💡 ИЛИ через консоль браузера на receptorai.pro:

1. Открой https://receptorai.pro
2. F12 → Console
3. Вставь и выполни:

```javascript
const API = 'https://receptor-preprod-production.up.railway.app/api/iiko';
const userId = 'default_user';

// Тест 1: Статус
fetch(`${API}/rms/status/${userId}`).then(r=>r.json()).then(console.log);

// Тест 2: Поля
fetch(`${API}/rms/bi/olap-columns/${userId}?report_type=SALES`).then(r=>r.json()).then(console.log);

// Тест 3: Отчет (POST)
fetch(`${API}/rms/bi/olap-report`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: userId, period_type: 'YESTERDAY', group_by: 'dish'})
}).then(r=>r.json()).then(console.log);

// Тест 4: Топ блюд
fetch(`${API}/rms/bi/dish-statistics/${userId}?period_type=LAST_MONTH&top_n=5`).then(r=>r.json()).then(console.log);
```

---

## ✅ ЧТО ОЖИДАЕМ:

- Все запросы возвращают `"status": "success"`
- В ответах есть реальные данные (если были продажи)
- Нет ошибок 500

---

**Поехали тестировать! 🚀**

