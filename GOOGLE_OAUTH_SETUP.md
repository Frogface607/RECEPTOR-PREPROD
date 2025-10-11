# 🔐 Google OAuth Setup Guide

## Настройка Google OAuth для RECEPTOR PRO

### 1. Создание Google OAuth App

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите **Google+ API**
4. Перейдите в **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Выберите **Web application**
6. Добавьте **Authorized JavaScript origins**:
   - `https://yourdomain.com` (для продакшена)
   - **НЕ используйте localhost** - Google его не поддерживает!
7. Добавьте **Authorized redirect URIs**:
   - `https://yourdomain.com`
   - **НЕ используйте localhost** - Google его не поддерживает!

### 🚨 ВАЖНО: Localhost НЕ поддерживается!

Google Cloud Console **НЕ принимает localhost** в Authorized origins. Для разработки используйте:

**ВАРИАНТ A: ngrok (рекомендуется)**
```bash
# Установите ngrok
npm install -g ngrok

# Создайте туннель к localhost:3000
ngrok http 3000

# Используйте полученный URL в Google Console:
# https://abc123.ngrok.io
```

**ВАРИАНТ B: Используйте домен для разработки**
- `http://receptorai.pro` (как у тебя уже настроено) ✅
- Настройте hosts файл: `127.0.0.1 receptorai.pro`

### 2. Настройка Frontend

Создайте файл `frontend/.env`:

```env
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
REACT_APP_BACKEND_URL=http://localhost:8002
```

### 3. Настройка Backend

Создайте файл `backend/.env`:

```env
JWT_SECRET=your-super-secret-jwt-key-here
MONGO_URL=your-mongodb-connection-string
DB_NAME=receptor_pro
```

### 4. Тестирование

1. Запустите backend: `cd backend && uvicorn server:app --host 127.0.0.1 --port 8002`
2. Запустите frontend: `cd frontend && npm start`
3. Откройте http://localhost:3000
4. Кликните "Войти" → "Войти через Google"

### 5. Fallback режим

Если Google OAuth не настроен, система автоматически использует **mock авторизацию** для тестирования.

## Текущий статус

✅ **Mock авторизация** - работает  
🔄 **Google OAuth** - требует настройки Google Client ID  
✅ **Backend API** - готов к приёму Google OAuth запросов

