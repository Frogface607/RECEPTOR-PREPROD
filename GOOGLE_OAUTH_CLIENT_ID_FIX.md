# 🔧 ИСПРАВЛЕНИЕ GOOGLE OAUTH CLIENT_ID

## ❌ ПРОБЛЕМА

**Ошибка в консоли:**
```
[GSI_LOGGER]: Missing required parameter: client_id.
```

**Причина:**
1. `REACT_APP_GOOGLE_CLIENT_ID` не установлен в переменных окружения
2. Google OAuth инициализировался дважды (в `initGoogleAuth()` и в `handleRealGoogleAuth()`)
3. Использовался `process.env.REACT_APP_GOOGLE_CLIENT_ID` напрямую вместо `GOOGLE_CLIENT_ID` из конфига

---

## ✅ ЧТО ИСПРАВЛЕНО

### Frontend (`frontend/src/components/GoogleAuth.js`):

1. ✅ Убрана двойная инициализация Google OAuth
2. ✅ Используется `GOOGLE_CLIENT_ID` из `googleAuth.js` (с fallback)
3. ✅ Проверка что `GOOGLE_CLIENT_ID` настроен перед инициализацией
4. ✅ Инициализация происходит только один раз в `useEffect`
5. ✅ Кнопка не показывается если `GOOGLE_CLIENT_ID` не настроен

### Frontend (`frontend/src/config/googleAuth.js`):

1. ✅ `initGoogleAuth()` помечен как deprecated (теперь инициализация в компоненте)

---

## 🔧 КАК НАСТРОИТЬ

### 1. Установить `REACT_APP_GOOGLE_CLIENT_ID`:

**В `.env` файле (frontend/.env):**
```env
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

**Или в переменных окружения продакшена:**
- Railway: Settings → Variables → Add Variable
- Heroku: Settings → Config Vars → Add
- Vercel: Settings → Environment Variables → Add

---

### 2. Получить Google Client ID:

1. Перейди в [Google Cloud Console](https://console.cloud.google.com/)
2. Создай проект или выбери существующий
3. Включи **Google+ API**
4. Перейди в **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Выбери **Web application**
6. Добавь **Authorized JavaScript origins**:
   - `https://receptorai.pro` (для продакшена)
   - `https://receptor-preprod-production.up.railway.app` (если используется Railway)
7. Добавь **Authorized redirect URIs**:
   - `https://receptorai.pro`
   - `https://receptor-preprod-production.up.railway.app`
8. Скопируй **Client ID** (формат: `xxxxx.apps.googleusercontent.com`)

---

## 🧪 ПРОВЕРКА

### После настройки:

1. Перезапусти frontend (чтобы загрузить новые переменные окружения)
2. Открой приложение
3. Нажми "Войти" → "Войти через Google"
4. Должна появиться кнопка Google (без ошибок в консоли)
5. При клике должен открыться Google OAuth

### Если кнопка не показывается:

- Проверь что `REACT_APP_GOOGLE_CLIENT_ID` установлен
- Проверь что значение не равно `'your-google-client-id.apps.googleusercontent.com'`
- Перезапусти frontend после изменения `.env`

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

**Статус**: ✅ Исправлено  
**Проблема**: Google OAuth не получал `client_id`  
**Решение**: 
- Убрана двойная инициализация
- Добавлена проверка `GOOGLE_CLIENT_ID`
- Кнопка не показывается если `client_id` не настроен

---

**Дата**: 2025-01-XX  
**Статус**: ✅ Готово к настройке



