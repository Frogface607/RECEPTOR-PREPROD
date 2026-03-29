# 🚀 ДЕПЛОЙ НА RENDER.COM (БЕСПЛАТНО)

## ✅ ПРЕИМУЩЕСТВА RENDER

- ✅ **Бесплатный tier** - 750 часов/месяц (достаточно для тестирования)
- ✅ **Автоматический деплой** из GitHub
- ✅ **HTTPS** из коробки
- ✅ **Переменные окружения** через UI
- ✅ **Логи** в реальном времени
- ✅ **Health checks** автоматически

## 📋 ШАГИ ДЕПЛОЯ

### 1. Подготовка

1. **Создай аккаунт на Render.com:**
   - Зайди на https://render.com
   - Зарегистрируйся через GitHub (проще всего)

2. **Подключи репозиторий:**
   - Render Dashboard → New → Web Service
   - Подключи GitHub репозиторий
   - Выбери ветку `main`

### 2. Настройка сервиса

**Используй эти настройки:**

- **Name:** `receptor-backend` (или любое другое)
- **Region:** `Frankfurt` (ближе к России) или `Oregon` (если нужна скорость)
- **Branch:** `main`
- **Root Directory:** `backend` (важно!)
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info`

### 3. Переменные окружения

Добавь в Render Dashboard → Environment:

```
MONGODB_URI=твой_mongodb_uri
JWT_SECRET=твой_секретный_ключ_минимум_32_символа
OPENAI_API_KEY=твой_openai_key (опционально)
ENVIRONMENT=production
DB_NAME=receptor_pro
CORS_ALLOW_ALL=false
```

**Важно:**
- `MONGODB_URI` - можно использовать MongoDB Atlas (бесплатный tier)
- `JWT_SECRET` - сгенерируй случайную строку (минимум 32 символа)
- `CORS_ALLOW_ALL=false` - для безопасности, или `true` для тестирования

### 4. Деплой

1. Нажми **"Create Web Service"**
2. Render автоматически:
   - Установит зависимости
   - Запустит сервер
   - Проверит health check

3. Дождись завершения деплоя (обычно 2-5 минут)

### 5. Получи URL

После деплоя Render даст тебе URL вида:
```
https://receptor-backend-xxxx.onrender.com
```

**Сохрани этот URL!** Он понадобится для frontend.

## 🔧 НАСТРОЙКА FRONTEND

После деплоя backend, обнови frontend:

1. **В Vercel Dashboard** (или где у тебя frontend):
   - Environment Variables → `REACT_APP_BACKEND_URL`
   - Установи значение: `https://receptor-backend-xxxx.onrender.com`

2. **Или локально в `.env.local`:**
   ```
   REACT_APP_BACKEND_URL=https://receptor-backend-xxxx.onrender.com
   ```

3. **Перезапусти frontend** (если локально)

## 🐛 РЕШЕНИЕ ПРОБЛЕМ

### Проблема: "Build failed"

**Решение:**
- Проверь что `requirements.txt` существует в `backend/`
- Проверь логи в Render Dashboard
- Убедись что Python версия правильная (3.11)

### Проблема: "Service crashed"

**Решение:**
- Проверь логи в Render Dashboard
- Убедись что все environment variables установлены
- Проверь что MongoDB URI правильный

### Проблема: "Health check failed"

**Решение:**
- Проверь что `/api/health` endpoint работает
- Проверь что порт правильный (`$PORT` используется автоматически)
- Проверь логи на ошибки

### Проблема: CORS все еще не работает

**Решение:**
1. В Render Dashboard → Environment:
   ```
   CORS_ALLOW_ALL=true
   ```
2. Перезапусти сервис (Manual Deploy → Clear build cache & deploy)
3. Проверь логи - должна быть строка: `🌐 CORS origins: [...]`

## ⚠️ ОГРАНИЧЕНИЯ БЕСПЛАТНОГО TIER

- **750 часов/месяц** - если превысишь, сервис остановится
- **Спит после 15 минут неактивности** - первый запрос может быть медленным (~30 сек)
- **512 MB RAM** - достаточно для большинства случаев
- **0.1 CPU** - может быть медленнее чем Railway

## 💡 СОВЕТЫ

1. **Для тестирования:** Используй `CORS_ALLOW_ALL=true` временно
2. **Для production:** Установи конкретные origins в коде
3. **Мониторинг:** Проверяй логи регулярно в Render Dashboard
4. **Backup:** MongoDB Atlas автоматически делает backup (если используешь)

## 🔄 АЛЬТЕРНАТИВЫ

Если Render не подходит, можно использовать:

1. **Fly.io** - бесплатный tier, быстрый старт
2. **Heroku** - платный, но стабильный
3. **Vercel Serverless** - для serverless функций (нужно переписать)
4. **Локальный сервер** - для разработки

---

**Готово!** После деплоя проверь:
- ✅ Health check: `https://your-app.onrender.com/api/health`
- ✅ Root: `https://your-app.onrender.com/`
- ✅ CORS работает с frontend



