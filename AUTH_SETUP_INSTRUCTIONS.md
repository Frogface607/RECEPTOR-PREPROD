# 🔐 ИНСТРУКЦИЯ ПО УСТАНОВКЕ АВТОРИЗАЦИИ

## ✅ ЧТО СДЕЛАНО

### Backend:
1. ✅ Добавлен password hashing (bcrypt)
2. ✅ Обновлена User модель для `password_hash` и `provider`
3. ✅ Обновлен `/api/register` endpoint для хеширования паролей
4. ✅ Создан `/api/login` endpoint с JWT токенами
5. ✅ Добавлены функции `hash_password`, `verify_password`, `create_access_token`, `verify_token`

### Frontend:
1. ✅ Обновлен `ModernAuthModal` для работы с реальным API
2. ✅ Обновлен `App.js` для подключения к `/api/login` и `/api/register`
3. ✅ Добавлен автоматический вход после регистрации
4. ✅ Добавлена обработка ошибок

---

## 📦 УСТАНОВКА ЗАВИСИМОСТЕЙ

### Backend зависимости:

```bash
pip install passlib[bcrypt] python-jose[cryptography]
```

Или добавь в `requirements.txt`:
```
passlib[bcrypt]
python-jose[cryptography]
```

### Frontend:
Никаких дополнительных зависимостей не требуется - используется `axios` который уже установлен.

---

## 🔧 НАСТРОЙКА

### Backend:

1. **JWT Secret Key** (важно для продакшена!):
   
   Добавь в `.env`:
   ```env
   JWT_SECRET=your-super-secret-key-change-in-production
   ```
   
   **⚠️ ВАЖНО**: Используй сильный секретный ключ в продакшене!

2. **Проверь что зависимости установлены**:
   ```bash
   python -c "from passlib.context import CryptContext; from jose import jwt; print('✅ Dependencies OK')"
   ```

---

## 🧪 ТЕСТИРОВАНИЕ

### 1. Тест регистрации:

**Через ModernAuthModal:**
1. Открой приложение
2. Нажми "Войти" или "Зарегистрироваться"
3. Выбери "Создать аккаунт"
4. Введи:
   - Email: `test@example.com`
   - Пароль: `test123` (минимум 6 символов)
5. Нажми "Создать аккаунт"
6. Должен произойти автоматический вход

**Ожидаемый результат:**
- ✅ Пользователь зарегистрирован
- ✅ Автоматический вход выполнен
- ✅ Токен сохранен в localStorage
- ✅ Пользователь видит свой профиль

---

### 2. Тест авторизации:

**Через ModernAuthModal:**
1. Открой приложение
2. Нажми "Войти"
3. Введи:
   - Email: `test@example.com`
   - Пароль: `test123`
4. Нажми "Войти"

**Ожидаемый результат:**
- ✅ Вход выполнен успешно
- ✅ Токен сохранен в localStorage
- ✅ Пользователь видит свой профиль

---

### 3. Тест ошибок:

**Неверный пароль:**
- Email: `test@example.com`
- Пароль: `wrongpassword`
- Ожидается: "Invalid email or password"

**Несуществующий пользователь:**
- Email: `nonexistent@example.com`
- Пароль: `anypassword`
- Ожидается: "Invalid email or password"

**Пользователь без пароля (Google OAuth):**
- Если пользователь зарегистрирован через Google
- Попытка входа через email/password
- Ожидается: "This account uses Google OAuth. Please login with Google."

**Слабый пароль:**
- Пароль: `12345` (меньше 6 символов)
- Ожидается: "Password must be at least 6 characters"

**Дубликат email:**
- Попытка зарегистрироваться с существующим email
- Ожидается: "User already registered"

---

## 🔍 ПРОВЕРКА В БАЗЕ ДАННЫХ

### Проверь что пользователь создан:

```javascript
// MongoDB
db.users.findOne({email: "test@example.com"})
```

**Ожидаемые поля:**
- ✅ `email`: "test@example.com"
- ✅ `password_hash`: хешированный пароль (не пустой)
- ✅ `provider`: "email"
- ✅ `id`: UUID
- ✅ `name`: имя пользователя
- ✅ `city`: город

---

## 🐛 ОТЛАДКА

### Проблема: "Authentication not available"

**Решение:**
```bash
pip install passlib[bcrypt] python-jose[cryptography]
```

### Проблема: "Invalid email or password"

**Проверь:**
1. Пользователь существует в базе?
2. Пароль правильный?
3. `password_hash` не пустой?

### Проблема: JWT токен не работает

**Проверь:**
1. `JWT_SECRET` установлен в `.env`?
2. Токен сохраняется в localStorage?
3. Токен передается в заголовках запросов?

---

## 📊 СТРУКТУРА ОТВЕТОВ API

### `/api/register` (POST):
```json
{
  "id": "uuid",
  "email": "test@example.com",
  "name": "test",
  "city": "Москва",
  "subscription_plan": "free",
  "provider": "email",
  "password_hash": "hashed_password",
  ...
}
```

### `/api/login` (POST):
```json
{
  "success": true,
  "token": "jwt_token_here",
  "user": {
    "id": "uuid",
    "email": "test@example.com",
    "name": "test",
    ...
  },
  "message": "Login successful"
}
```

---

## 🚀 ГОТОВНОСТЬ К ДЕПЛОЮ

**Статус**: ✅ Готово к тестированию

**Перед деплоем:**
1. ✅ Установить зависимости: `pip install passlib[bcrypt] python-jose[cryptography]`
2. ✅ Установить `JWT_SECRET` в `.env` (сильный ключ!)
3. ✅ Протестировать регистрацию и авторизацию
4. ✅ Проверить что токены сохраняются и работают

---

**Дата**: 2025-01-XX  
**Статус**: ✅ Готово к тестированию



