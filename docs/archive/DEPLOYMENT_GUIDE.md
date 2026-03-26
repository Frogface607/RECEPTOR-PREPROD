# 🚀 ДЕПЛОЙ РЕЦЕПТОР AI - VERCEL + RAILWAY

## 📋 ПОШАГОВАЯ ИНСТРУКЦИЯ

### **ШАГ 1: Подготовка GitHub**

1. **Коммитим изменения:**
   ```bash
   git commit -m "🚀 Подготовка к деплою: добавлены конфигурации Vercel + Railway"
   git push origin main
   ```

### **ШАГ 2: Деплой Backend на Railway**

1. **Переходим на [Railway.app](https://railway.app)**
2. **Входим через GitHub**
3. **Создаем новый проект:** "New Project" → "Deploy from GitHub repo"
4. **Выбираем наш репозиторий**
5. **Выбираем папку:** `backend`
6. **Настраиваем переменные окружения:**
   - `MONGODB_URI` = твой MongoDB Atlas connection string
   - `OPENAI_API_KEY` = твой OpenAI API ключ
   - `FEATURE_TECHCARDS_V2` = `true`
   - `JWT_SECRET_KEY` = случайная строка (например: `your-secret-key-here`)

7. **Деплоим:** Railway автоматически соберет и запустит backend
8. **Копируем URL:** например `https://receptor-ai-backend.railway.app`

### **ШАГ 3: Деплой Frontend на Vercel**

1. **Переходим на [Vercel.com](https://vercel.com)**
2. **Входим через GitHub**
3. **Импортируем проект:** "New Project" → выбираем репозиторий
4. **Настраиваем:**
   - **Root Directory:** `frontend`
   - **Framework Preset:** Create React App
   - **Build Command:** `npm run build`
   - **Output Directory:** `build`

5. **Добавляем переменные окружения:**
   - `REACT_APP_BACKEND_URL` = URL твоего Railway backend (из шага 2)

6. **Деплоим:** Vercel автоматически соберет и задеплоит frontend
7. **Получаем URL:** например `https://receptor-ai.vercel.app`

### **ШАГ 4: Настройка Google OAuth (опционально)**

1. **Переходим в [Google Cloud Console](https://console.cloud.google.com)**
2. **Создаем новый проект или выбираем существующий**
3. **Включаем Google+ API**
4. **Создаем OAuth 2.0 credentials:**
   - **Application type:** Web application
   - **Authorized JavaScript origins:** `https://receptor-ai.vercel.app`
   - **Authorized redirect URIs:** `https://receptor-ai.vercel.app/auth/google/callback`

5. **Копируем Client ID и добавляем в Railway:**
   - `GOOGLE_CLIENT_ID` = твой Client ID
   - `GOOGLE_CLIENT_SECRET` = твой Client Secret

### **ШАГ 5: Тестирование**

1. **Открываем Vercel URL**
2. **Проверяем:**
   - ✅ Создание техкарт работает
   - ✅ IIKO интеграция работает
   - ✅ Онбординг показывается
   - ✅ История сохраняется

### **🎉 ГОТОВО!**

Твой **Рецептор AI** теперь доступен всему миру!

## 🔧 Troubleshooting

**Если что-то не работает:**

1. **Проверь логи в Railway Dashboard**
2. **Проверь переменные окружения**
3. **Убедись что MongoDB Atlas доступен извне**
4. **Проверь что все API ключи корректны**

## 📞 Поддержка

Если нужна помощь - пиши! 🚀

