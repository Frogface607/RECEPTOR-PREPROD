# 🚀 БЫСТРАЯ НАСТРОЙКА GOOGLE OAUTH

## ✅ ЧТО УЖЕ ГОТОВО

✅ **Backend** - полностью готов:
- Endpoint `/api/v1/auth/google` работает
- Сохранение пользователей в MongoDB
- JWT токены
- Обработка новых и существующих пользователей

✅ **Frontend** - полностью готов:
- Компонент GoogleAuth
- Интеграция с ModernAuthModal
- Обработка ошибок

## 🔧 ЧТО НУЖНО СДЕЛАТЬ

### ШАГ 1: Получить Google Client ID

1. Перейди в [Google Cloud Console](https://console.cloud.google.com/)
2. Создай новый проект или выбери существующий
3. Включи **Google+ API** (или **Google Identity Services API**)
4. Перейди в **APIs & Services** → **Credentials**
5. Нажми **Create Credentials** → **OAuth 2.0 Client IDs**
6. Выбери **Web application**
7. Настрой:
   - **Name**: RECEPTOR PRO (или любое имя)
   - **Authorized JavaScript origins**:
     - `http://localhost:3000` (для локальной разработки)
     - `https://receptorai.pro` (для продакшена)
     - `https://www.receptorai.pro` (если используешь www)
   - **Authorized redirect URIs**:
     - `http://localhost:3000` (для локальной разработки)
     - `https://receptorai.pro` (для продакшена)
8. Скопируй **Client ID** (формат: `xxxxx-xxxxx.apps.googleusercontent.com`)

### ШАГ 2: Настроить Frontend

Создай файл `frontend/.env` (если его нет):

```env
REACT_APP_GOOGLE_CLIENT_ID=твой-client-id-здесь.apps.googleusercontent.com
REACT_APP_BACKEND_URL=http://localhost:8002
```

**ВАЖНО:**
- Перезапусти frontend после создания/изменения `.env` файла!
- React не подхватывает изменения `.env` без перезапуска

### ШАГ 3: Проверить работу

1. Запусти backend: `cd backend && uvicorn server:app --host 127.0.0.1 --port 8002`
2. Запусти frontend: `cd frontend && npm start`
3. Открой http://localhost:3000
4. Нажми "Войти" → "Войти через Google"
5. Должна появиться кнопка Google
6. При клике откроется окно авторизации Google

## 🐛 ЕСЛИ НЕ РАБОТАЕТ

### Кнопка Google не показывается:
- Проверь что `REACT_APP_GOOGLE_CLIENT_ID` установлен в `.env`
- Проверь что значение не равно `'your-google-client-id.apps.googleusercontent.com'`
- Перезапусти frontend после изменения `.env`

### Ошибка "Invalid origin":
- Проверь что в Google Console добавлен правильный origin (http://localhost:3000)
- Для продакшена добавь реальный домен

### Ошибка "Missing required parameter: client_id":
- Проверь что `.env` файл в папке `frontend/`
- Проверь что переменная называется `REACT_APP_GOOGLE_CLIENT_ID` (с префиксом REACT_APP_)
- Перезапусти frontend

## 📝 ДЛЯ ПРОДАКШЕНА

В переменных окружения платформы (Railway, Vercel, Render и т.д.) добавь:

```
REACT_APP_GOOGLE_CLIENT_ID=твой-client-id.apps.googleusercontent.com
```

И убедись что в Google Console добавлен правильный домен в **Authorized JavaScript origins**.

## ✅ ТЕКУЩИЙ СТАТУС

- ✅ Backend готов
- ✅ Frontend готов
- ⚠️ Требуется настройка Google Client ID
- ⚠️ Требуется создание `.env` файла

После настройки Google OAuth будет работать полностью!



