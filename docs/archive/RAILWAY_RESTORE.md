# 🚂 ВОССТАНОВЛЕНИЕ RAILWAY ($5/месяц)

## ✅ ПРЕИМУЩЕСТВА

- ✅ **Уже все настроено** - `railway.json` готов
- ✅ **Знакомая платформа** - не нужно переучиваться
- ✅ **Стабильность** - не спит, всегда доступен
- ✅ **Масштабируемость** - легко добавлять новые сервисы
- ✅ **$5/месяц** - дешево для production

## 🚀 БЫСТРЫЙ СТАРТ

### 1. Активируй платный план

1. Зайди в **Railway Dashboard**: https://railway.app
2. Перейди в **Settings** → **Billing**
3. Выбери план **"Developer" ($5/месяц)**
4. Добавь карту и активируй

### 2. Проверь что сервис запущен

1. **Railway Dashboard** → **Projects** → выбери проект
2. Проверь что сервис **"receptor-backend"** (или как он называется) **Running**
3. Если остановлен → нажми **"Deploy"** или **"Restart"**

### 3. Проверь Environment Variables

**Railway Dashboard** → **Variables** → проверь что есть:

```
✅ MONGODB_URI=твой_mongodb_uri
✅ JWT_SECRET=твой_секретный_ключ
✅ OPENAI_API_KEY=твой_openai_key (опционально)
✅ ENVIRONMENT=production
✅ DB_NAME=receptor_pro
```

**Если чего-то нет - добавь!**

### 4. Проверь CORS настройки

**Вариант А: Автоматический (рекомендую)**

Railway автоматически создает переменную `RAILWAY_PUBLIC_DOMAIN` при деплое.  
Код уже поддерживает это - ничего делать не нужно! ✅

**Вариант Б: Вручную (если нужно)**

Если домен не определяется автоматически, добавь в Variables:

```
RAILWAY_PUBLIC_DOMAIN=receptor-preprod-production.up.railway.app
```

**Вариант В: Временно разрешить все (для теста)**

```
CORS_ALLOW_ALL=true
```

### 5. Получи URL сервиса

1. **Railway Dashboard** → **Settings** → **Networking**
2. Скопируй **Public Domain** (например: `receptor-preprod-production.up.railway.app`)
3. URL будет: `https://receptor-preprod-production.up.railway.app`

### 6. Проверь что работает

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

Health check:
```
https://receptor-preprod-production.up.railway.app/api/health
```

### 7. Обнови Frontend (если нужно)

Если URL изменился, обнови в frontend:

**Vercel Dashboard** → **Environment Variables**:
```
REACT_APP_BACKEND_URL=https://receptor-preprod-production.up.railway.app
```

Или локально в `.env.local`:
```
REACT_APP_BACKEND_URL=https://receptor-preprod-production.up.railway.app
```

## 🔧 ЧТО УЖЕ НАСТРОЕНО

✅ **railway.json** - конфигурация деплоя готова  
✅ **CORS** - автоматически поддерживает Railway домены  
✅ **Health check** - `/api/health` endpoint готов  
✅ **Startup логи** - показывают статус при запуске  

## 📋 ЧЕКЛИСТ ВОССТАНОВЛЕНИЯ

- [ ] Активирован платный план ($5/месяц)
- [ ] Сервис запущен (Status: Running)
- [ ] Все Environment Variables на месте
- [ ] URL сервиса получен
- [ ] Root endpoint отвечает (`/`)
- [ ] Health check работает (`/api/health`)
- [ ] CORS настроен (проверь логи: `🌐 CORS origins: [...]`)
- [ ] Frontend обновлен с новым URL (если изменился)

## 🐛 РЕШЕНИЕ ПРОБЛЕМ

### Проблема: Сервис не запускается

**Решение:**
1. Проверь логи: **Railway Dashboard** → **Deployments** → **View Logs**
2. Проверь что все переменные окружения установлены
3. Проверь что `requirements.txt` содержит все зависимости
4. Попробуй **Redeploy** с очисткой кеша

### Проблема: CORS не работает

**Решение:**
1. Проверь логи - должна быть строка: `🌐 CORS origins: [...]`
2. Временно установи `CORS_ALLOW_ALL=true` для теста
3. Проверь что `RAILWAY_PUBLIC_DOMAIN` установлен (если нужно)
4. Перезапусти сервис после изменения переменных

### Проблема: MongoDB не подключается

**Решение:**
1. Проверь что `MONGODB_URI` правильный
2. Проверь что MongoDB Atlas разрешает подключения с Railway IP
3. Проверь логи на ошибки подключения

### Проблема: 404 на всех endpoints

**Решение:**
1. Проверь что `railway.json` правильно настроен
2. Проверь что `startCommand` правильный: `uvicorn server:app --host 0.0.0.0 --port $PORT`
3. Проверь что сервер запустился (логи)

## 💡 СОВЕТЫ

1. **Мониторинг:** Регулярно проверяй логи в Railway Dashboard
2. **Backup:** MongoDB Atlas автоматически делает backup
3. **Scaling:** При необходимости можно увеличить ресурсы в Railway
4. **Custom Domain:** Можно подключить свой домен в Railway Settings

## 🎯 ПОСЛЕ ВОССТАНОВЛЕНИЯ

1. ✅ Протестируй все функции
2. ✅ Проверь авторизацию (email/password и Google OAuth)
3. ✅ Проверь создание техкарт
4. ✅ Проверь экспорт
5. ✅ Проверь личный кабинет

---

**Готово!** После активации плана все должно заработать автоматически. 🚀



