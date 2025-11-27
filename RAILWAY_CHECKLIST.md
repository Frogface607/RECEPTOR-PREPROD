# ✅ ЧЕКЛИСТ ВОССТАНОВЛЕНИЯ RAILWAY

## 🎯 БЫСТРЫЕ ШАГИ

### 1. Активируй план ($5/месяц)
- [ ] Railway Dashboard → Settings → Billing
- [ ] Выбери "Developer" план
- [ ] Добавь карту и активируй

### 2. Проверь сервис
- [ ] Railway Dashboard → Projects → выбери проект
- [ ] Проверь что сервис **Running**
- [ ] Если остановлен → **Deploy** или **Restart**

### 3. Environment Variables (ОБЯЗАТЕЛЬНО!)

**Railway Dashboard** → **Variables** → проверь/добавь:

```
✅ MONGODB_URI=твой_mongodb_uri
✅ JWT_SECRET=случайная_строка_минимум_32_символа
✅ OPENAI_API_KEY=твой_openai_key (опционально, но желательно)
✅ ENVIRONMENT=production
✅ DB_NAME=receptor_pro
```

**Для CORS (один из вариантов):**
```
✅ RAILWAY_PUBLIC_DOMAIN=receptor-preprod-production.up.railway.app
   ИЛИ
✅ CORS_ALLOW_ALL=true  (временно для теста)
```

### 4. Проверь что работает

Открой в браузере:
- [ ] `https://receptor-preprod-production.up.railway.app/` → должен вернуть `{"message": "Receptor AI Backend is running", "status": "ok"}`
- [ ] `https://receptor-preprod-production.up.railway.app/api/health` → должен вернуть `{"status": "healthy", ...}`

### 5. Проверь логи

**Railway Dashboard** → **Deployments** → **View Logs**

Должны быть строки:
- [ ] `🚀 Receptor AI Backend starting up...`
- [ ] `🌐 CORS origins: [...]` (или `⚠️ CORS: Allowing all origins`)
- [ ] `✅ Server startup complete!`

### 6. Обнови Frontend (если URL изменился)

**Vercel Dashboard** → **Environment Variables**:
```
REACT_APP_BACKEND_URL=https://receptor-preprod-production.up.railway.app
```

Или локально в `frontend/.env.local`:
```
REACT_APP_BACKEND_URL=https://receptor-preprod-production.up.railway.app
```

## 🔧 ЧТО УЖЕ НАСТРОЕНО

✅ `railway.json` - конфигурация готова  
✅ `requirements.txt` - все зависимости (включая passlib, python-jose)  
✅ CORS - автоматически поддерживает Railway домены  
✅ Health check - `/api/health` endpoint  
✅ Авторизация - email/password и Google OAuth  

## 🐛 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### Сервис не запускается
1. Проверь логи на ошибки
2. Проверь что все переменные окружения установлены
3. Попробуй **Redeploy** с очисткой кеша

### CORS не работает
1. Временно установи `CORS_ALLOW_ALL=true`
2. Перезапусти сервис
3. Проверь логи - должна быть строка про CORS

### MongoDB не подключается
1. Проверь `MONGODB_URI`
2. Проверь что MongoDB Atlas разрешает подключения

---

**После выполнения всех шагов - все должно заработать!** 🚀



