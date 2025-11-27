# 🔑 КАК ПОЛУЧИТЬ GOOGLE CLIENT ID - ПОШАГОВАЯ ИНСТРУКЦИЯ

## 📋 ШАГ 1: Войти в Google Cloud Console

1. Перейди на https://console.cloud.google.com/
2. Войди в свой Google аккаунт (если не вошёл)

---

## 📋 ШАГ 2: Создать проект (если его нет)

1. Вверху страницы нажми на выпадающий список с названием проекта
2. Нажми **"NEW PROJECT"** (Новый проект)
3. Введи название проекта: `RECEPTOR PRO` (или любое другое)
4. Нажми **"CREATE"** (Создать)
5. Дождись создания проекта (обычно 10-30 секунд)

---

## 📋 ШАГ 3: Включить Google Identity API

1. В левом меню нажми **"APIs & Services"** → **"Library"** (Библиотека)
2. В поиске введи: **"Google Identity Services API"** или **"Google+ API"**
3. Нажми на найденный API
4. Нажми кнопку **"ENABLE"** (Включить)
5. Дождись активации (обычно несколько секунд)

**Альтернатива:** Можно пропустить этот шаг - Google OAuth будет работать и без явного включения API.

---

## 📋 ШАГ 4: Создать OAuth 2.0 Client ID

1. В левом меню нажми **"APIs & Services"** → **"Credentials"** (Учетные данные)
2. Вверху страницы нажми **"+ CREATE CREDENTIALS"** (Создать учетные данные)
3. Выбери **"OAuth client ID"** (OAuth клиентский ID)

---

## 📋 ШАГ 5: Настроить OAuth consent screen (если первый раз)

Если видишь сообщение "To create an OAuth client ID, you must first configure the consent screen":

1. Нажми **"CONFIGURE CONSENT SCREEN"** (Настроить экран согласия)
2. Выбери **"External"** (Внешний) → Нажми **"CREATE"**
3. Заполни обязательные поля:
   - **App name** (Название приложения): `RECEPTOR PRO`
   - **User support email** (Email поддержки): твой email
   - **Developer contact information** (Контакт разработчика): твой email
4. Нажми **"SAVE AND CONTINUE"** (Сохранить и продолжить)
5. На следующем экране нажми **"SAVE AND CONTINUE"** (можно пропустить Scopes)
6. На экране Test users нажми **"SAVE AND CONTINUE"** (можно пропустить)
7. Нажми **"BACK TO DASHBOARD"** (Вернуться к панели)
8. Теперь вернись к шагу 4 (APIs & Services → Credentials → CREATE CREDENTIALS → OAuth client ID)

---

## 📋 ШАГ 6: Создать OAuth Client ID

1. В выпадающем списке **"Application type"** (Тип приложения) выбери **"Web application"** (Веб-приложение)
2. В поле **"Name"** (Название) введи: `RECEPTOR PRO Web Client` (или любое другое)
3. В разделе **"Authorized JavaScript origins"** (Разрешенные источники JavaScript) нажми **"+ ADD URI"** и добавь:
   - `http://localhost:3000` (для локальной разработки)
   - `https://receptorai.pro` (для продакшена, если есть)
   - `https://www.receptorai.pro` (если используешь www)
4. В разделе **"Authorized redirect URIs"** (Разрешенные URI перенаправления) нажми **"+ ADD URI"** и добавь те же самые URL:
   - `http://localhost:3000`
   - `https://receptorai.pro` (если есть)
   - `https://www.receptorai.pro` (если используешь www)
5. Нажми **"CREATE"** (Создать)

---

## 📋 ШАГ 7: Скопировать Client ID

После создания ты увидишь модальное окно с информацией:

1. **Client ID** - это то, что тебе нужно! Скопируй его (формат: `xxxxx-xxxxx.apps.googleusercontent.com`)
2. **Client secret** - не нужен для нашего случая (можно закрыть окно)

---

## 📋 ШАГ 8: Добавить в проект

1. Открой файл `frontend/.env` (создай его, если нет)
2. Добавь строку:
   ```env
   REACT_APP_GOOGLE_CLIENT_ID=вставь-сюда-скопированный-client-id
   ```
3. Сохрани файл
4. **ВАЖНО:** Перезапусти frontend (React не подхватывает изменения .env без перезапуска)

---

## ✅ ПРОВЕРКА

После настройки:

1. Перезапусти frontend: `cd frontend && npm start`
2. Открой http://localhost:3000
3. Нажми "Войти" → "Войти через Google"
4. Должна появиться кнопка Google
5. При клике откроется окно авторизации Google

---

## 🐛 ЧАСТЫЕ ПРОБЛЕМЫ

### "Error 400: redirect_uri_mismatch"
- Проверь, что в Google Console добавлен правильный URL в "Authorized redirect URIs"
- URL должен точно совпадать (включая http/https, порт, слеш в конце)

### Кнопка Google не показывается
- Проверь, что `REACT_APP_GOOGLE_CLIENT_ID` добавлен в `.env`
- Проверь, что перезапустил frontend после изменения `.env`
- Проверь консоль браузера на ошибки

### "Invalid client"
- Проверь, что Client ID скопирован полностью (включая `.apps.googleusercontent.com`)
- Проверь, что нет лишних пробелов в `.env` файле

---

## 📸 ВИЗУАЛЬНАЯ ПОДСКАЗКА

**Где найти Credentials:**
```
Google Cloud Console
  └─ APIs & Services (в левом меню)
      └─ Credentials
          └─ + CREATE CREDENTIALS
              └─ OAuth client ID
```

**Формат Client ID:**
```
123456789-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com
```

---

## 🎯 БЫСТРАЯ ССЫЛКА

Прямая ссылка на создание OAuth Client ID (после настройки consent screen):
https://console.cloud.google.com/apis/credentials/oauthclient

---

**Готово!** Теперь у тебя есть Google Client ID и Google OAuth должен работать! 🚀

