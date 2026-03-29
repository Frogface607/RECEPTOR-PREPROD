# 🔍 ДИАГНОСТИКА RAILWAY И CORS

## ❌ ПРОБЛЕМА

Все запросы блокируются CORS ошибками:
```
Access to XMLHttpRequest at 'https://receptor-preprod-production.up.railway.app/api/...' 
from origin 'https://www.receptorai.pro' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## 🔧 ЧТО ИСПРАВЛЕНО

1. ✅ **CORS настройки** - теперь используется функция `get_cors_origins()` вместо хардкода
2. ✅ **Добавлен Railway domain** - автоматически добавляется если есть `RAILWAY_PUBLIC_DOMAIN`
3. ✅ **Режим разработки** - можно включить `CORS_ALLOW_ALL=true` для тестирования
4. ✅ **Логирование** - теперь логирует какие origins разрешены

## 🚀 КАК ПРОВЕРИТЬ

### 1. Проверь что сервер запущен на Railway

Открой в браузере:
```
https://receptor-preprod-production.up.railway.app/
```

**Ожидаемый ответ:**
```json
{
  "message": "Receptor AI Backend is running",
  "status": "ok"
}
```

**Если не работает:**
- ❌ Railway может быть остановлен (закончился free tier)
- ❌ Нужно проверить логи в Railway dashboard
- ❌ Возможно нужно перезапустить сервис

### 2. Проверь health check

```
https://receptor-preprod-production.up.railway.app/api/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-XX...",
  "service": "receptor-ai-backend"
}
```

### 3. Временное решение: Разрешить все origins

Если нужно быстро протестировать, добавь в Railway environment variables:

```
CORS_ALLOW_ALL=true
```

Это разрешит все origins (только для тестирования!).

### 4. Проверь CORS headers

Открой DevTools → Network → выбери любой запрос → Headers → Response Headers

**Должны быть:**
```
Access-Control-Allow-Origin: https://www.receptorai.pro
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
```

## 🔄 ЧТО ДЕЛАТЬ ДАЛЬШЕ

### Вариант 1: Railway работает, но CORS не работает

1. Проверь что в Railway environment variables есть:
   - `MONGODB_URI` - подключение к MongoDB
   - `JWT_SECRET` - секретный ключ для JWT
   - `OPENAI_API_KEY` - ключ OpenAI (опционально)

2. Перезапусти сервис в Railway:
   - Railway Dashboard → Deployments → Redeploy

3. Проверь логи в Railway:
   - Railway Dashboard → Deployments → View Logs
   - Ищи строку: `🌐 CORS origins: [...]`

### Вариант 2: Railway не работает (закончился free tier)

1. **Проверь статус Railway:**
   - Зайди в Railway Dashboard
   - Проверь есть ли активные сервисы
   - Проверь usage/billing

2. **Альтернативы:**
   - **Render.com** - бесплатный tier с автоматическим деплоем
   - **Fly.io** - бесплатный tier
   - **Heroku** - платный, но стабильный
   - **Vercel** - для frontend, но можно использовать serverless functions

3. **Локальный запуск для тестирования:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn server:app --host 0.0.0.0 --port 8000
   ```

## 📝 ПРОВЕРКА ЛОКально

Если Railway не работает, можно запустить локально:

1. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   # Создай .env файл с переменными:
   # MONGODB_URI=...
   # JWT_SECRET=...
   # ENVIRONMENT=development
   uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   # В .env.local:
   # REACT_APP_BACKEND_URL=http://localhost:8000
   npm start
   ```

3. **Проверь CORS:**
   - Backend должен быть на `http://localhost:8000`
   - Frontend должен быть на `http://localhost:3000`
   - CORS автоматически разрешит `localhost:3000` в development режиме

## 🐛 ИЗВЕСТНЫЕ ПРОБЛЕМЫ

### Проблема: CORS все еще не работает после исправления

**Решение:**
1. Убедись что изменения задеплоены на Railway
2. Проверь что сервер перезапустился
3. Очисти кеш браузера (Ctrl+Shift+R)
4. Проверь логи Railway на наличие ошибок

### Проблема: 404 ошибки на всех endpoints

**Причина:** Сервер не запущен или неправильно настроен

**Решение:**
1. Проверь Railway logs
2. Проверь что `railway.json` правильно настроен
3. Проверь что `requirements.txt` содержит все зависимости
4. Проверь что MongoDB подключение работает

## ✅ ЧЕКЛИСТ

- [ ] Сервер отвечает на `https://receptor-preprod-production.up.railway.app/`
- [ ] Health check работает: `/api/health`
- [ ] CORS headers присутствуют в ответах
- [ ] Railway logs показывают `🌐 CORS origins: [...]`
- [ ] Нет ошибок в Railway logs
- [ ] MongoDB подключение работает
- [ ] Environment variables настроены в Railway

---

**Дата:** 2025-01-XX  
**Статус:** Готово к проверке



