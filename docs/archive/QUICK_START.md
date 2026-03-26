# ⚡ БЫСТРЫЙ СТАРТ ПОСЛЕ RAILWAY

Railway закончился? Вот что делать:

## 🎯 ВАРИАНТ 1: Render.com (РЕКОМЕНДУЮ)

**5 минут до запуска:**

1. Зайди на https://render.com → Sign Up (через GitHub)
2. New → Web Service → Подключи репозиторий
3. Настройки:
   - **Root Directory:** `backend`
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Environment Variables:
   ```
   MONGODB_URI=твой_mongodb_uri
   JWT_SECRET=случайная_строка_32_символа
   ENVIRONMENT=production
   CORS_ALLOW_ALL=true  # временно для теста
   ```
5. Deploy! 🚀

**После деплоя:**
- Получишь URL: `https://your-app.onrender.com`
- Обнови frontend: `REACT_APP_BACKEND_URL=https://your-app.onrender.com`

📖 **Подробная инструкция:** `DEPLOY_RENDER.md`

---

## 💻 ВАРИАНТ 2: Локально (ДЛЯ ТЕСТА)

**2 минуты до запуска:**

```bash
# Backend
cd backend
pip install -r requirements.txt
# Создай .env с MONGODB_URI, JWT_SECRET
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Frontend (в другом терминале)
cd frontend
# Создай .env.local: REACT_APP_BACKEND_URL=http://localhost:8000
npm start
```

📖 **Подробная инструкция:** `LOCAL_SETUP.md`

---

## 🔵 ВАРИАНТ 3: Fly.io

**10 минут до запуска:**

```bash
# Установи CLI
iwr https://fly.io/install.ps1 -useb | iex

# Логин
flyctl auth login

# Создай приложение
cd backend
flyctl launch

# Настрой secrets
flyctl secrets set MONGODB_URI="..."
flyctl secrets set JWT_SECRET="..."

# Deploy
flyctl deploy
```

📖 **Подробная инструкция:** `DEPLOY_FLY.md`

---

## 📋 ЧТО ИСПРАВЛЕНО

✅ **CORS** - теперь поддерживает Render, Fly.io, Railway  
✅ **Автоматическое определение** доменов через environment variables  
✅ **Режим разработки** - `CORS_ALLOW_ALL=true` для тестирования  

---

## 🚀 ЧТО ДАЛЬШЕ?

1. **Выбери вариант** (рекомендую Render.com)
2. **Следуй инструкции**
3. **Обнови frontend** с новым URL
4. **Протестируй** все функции

**Вопросы?** См. `DEPLOYMENT_OPTIONS.md` для сравнения всех вариантов.



