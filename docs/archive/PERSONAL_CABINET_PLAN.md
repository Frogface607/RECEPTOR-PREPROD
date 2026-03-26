# 🎯 ПЛАН ДОРАБОТКИ ЛИЧНОГО КАБИНЕТА И РЕГИСТРАЦИИ

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### ✅ Что уже есть:

1. **Регистрация**:
   - ✅ `/api/register` endpoint в backend
   - ✅ Google OAuth работает
   - ❌ Email/password регистрация - MOCK (не работает с backend)

2. **Авторизация**:
   - ✅ Google OAuth работает
   - ❌ Email/password авторизация - MOCK (не работает с backend)

3. **Личный кабинет**:
   - ✅ Базовая структура есть
   - ✅ Профиль заведения (venue profile)
   - ✅ IIKO RMS подключение
   - ✅ Подписка и аккаунт (базовая информация)
   - ❌ Редактирование профиля (имя, email, город)
   - ❌ Смена пароля
   - ❌ Настройки уведомлений
   - ❌ История активности
   - ❌ Управление подпиской

---

## 🎯 ЧТО НУЖНО ДОРАБОТАТЬ

### 🔴 ПРИОРИТЕТ 1: РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ

#### 1.1 Email/Password Регистрация
**Проблема**: Сейчас mock, не работает с backend

**Что нужно**:
- ✅ Backend endpoint `/api/register` уже есть
- ❌ Добавить хеширование паролей (bcrypt)
- ❌ Добавить валидацию email и пароля
- ❌ Подключить ModernAuthModal к реальному backend
- ❌ Добавить обработку ошибок

**Файлы**:
- `backend/server.py` - добавить password hashing
- `frontend/src/components/ModernAuthModal.js` - подключить к API
- `frontend/src/App.js` - обновить handleRegister

---

#### 1.2 Email/Password Авторизация
**Проблема**: Сейчас mock, не работает с backend

**Что нужно**:
- ❌ Создать `/api/login` endpoint
- ❌ Добавить JWT токены для сессий
- ❌ Добавить проверку пароля
- ❌ Подключить ModernAuthModal к реальному backend
- ❌ Добавить обработку ошибок

**Файлы**:
- `backend/server.py` - добавить login endpoint
- `frontend/src/components/ModernAuthModal.js` - подключить к API
- `frontend/src/App.js` - обновить handleLogin

---

#### 1.3 Управление сессиями
**Проблема**: Нет системы сессий и токенов

**Что нужно**:
- ❌ JWT токены для авторизации
- ❌ Refresh tokens
- ❌ Middleware для проверки токенов
- ❌ Логика выхода (logout)

**Файлы**:
- `backend/server.py` - добавить JWT логику
- `frontend/src/App.js` - добавить проверку токенов

---

### 🟡 ПРИОРИТЕТ 2: ЛИЧНЫЙ КАБИНЕТ

#### 2.1 Редактирование профиля
**Проблема**: Нет возможности редактировать имя, email, город

**Что нужно**:
- ❌ Форма редактирования профиля
- ❌ Backend endpoint `/api/user/{user_id}/update`
- ❌ Валидация данных
- ❌ Обновление UI после сохранения

**Файлы**:
- `backend/server.py` - добавить update endpoint
- `frontend/src/App.js` - добавить форму редактирования

---

#### 2.2 Смена пароля
**Проблема**: Нет возможности сменить пароль

**Что нужно**:
- ❌ Форма смены пароля
- ❌ Backend endpoint `/api/user/{user_id}/change-password`
- ❌ Проверка старого пароля
- ❌ Хеширование нового пароля

**Файлы**:
- `backend/server.py` - добавить change-password endpoint
- `frontend/src/App.js` - добавить форму смены пароля

---

#### 2.3 Настройки уведомлений
**Проблема**: Нет настроек уведомлений

**Что нужно**:
- ❌ Форма настроек уведомлений
- ❌ Backend endpoint `/api/user/{user_id}/notifications`
- ❌ Сохранение настроек в MongoDB
- ❌ UI для управления настройками

**Файлы**:
- `backend/server.py` - добавить notifications endpoint
- `frontend/src/App.js` - добавить форму настроек

---

#### 2.4 История активности
**Проблема**: Нет истории активности пользователя

**Что нужно**:
- ❌ Отображение истории генераций
- ❌ Фильтры по дате, типу
- ❌ Статистика использования

**Файлы**:
- `frontend/src/App.js` - добавить секцию истории

---

#### 2.5 Управление подпиской
**Проблема**: Нет управления подпиской

**Что нужно**:
- ❌ Отображение текущей подписки
- ❌ Кнопка обновления подписки
- ❌ История платежей
- ❌ Лимиты использования

**Файлы**:
- `frontend/src/App.js` - доработать секцию подписки

---

## 📋 ПЛАН РЕАЛИЗАЦИИ

### Этап 1: Регистрация и авторизация (2-3 часа)
1. ✅ Добавить password hashing в backend
2. ✅ Подключить ModernAuthModal к API
3. ✅ Создать `/api/login` endpoint
4. ✅ Добавить JWT токены
5. ✅ Протестировать регистрацию и авторизацию

### Этап 2: Редактирование профиля (1-2 часа)
1. ✅ Создать форму редактирования
2. ✅ Добавить `/api/user/{user_id}/update` endpoint
3. ✅ Протестировать обновление профиля

### Этап 3: Смена пароля (1 час)
1. ✅ Создать форму смены пароля
2. ✅ Добавить `/api/user/{user_id}/change-password` endpoint
3. ✅ Протестировать смену пароля

### Этап 4: Настройки и история (2-3 часа)
1. ✅ Добавить настройки уведомлений
2. ✅ Добавить историю активности
3. ✅ Доработать управление подпиской

---

## 🔧 ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Backend изменения:

1. **Password Hashing**:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

2. **JWT Tokens**:
```python
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.environ.get("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

3. **User Model Update**:
```python
class User(BaseModel):
    # ... existing fields ...
    password_hash: Optional[str] = None  # For email/password users
    provider: str = "email"  # "email" or "google"
```

---

### Frontend изменения:

1. **ModernAuthModal**:
```javascript
// Подключить к реальному API
const handleEmailAuth = async (e) => {
  e.preventDefault();
  setIsLoading(true);
  
  try {
    if (mode === 'login') {
      const response = await axios.post(`${API}/login`, {
        email,
        password
      });
      localStorage.setItem('receptor_token', response.data.token);
      localStorage.setItem('receptor_user', JSON.stringify(response.data.user));
      onLogin(response.data.user.email, response.data.token);
    } else {
      const response = await axios.post(`${API}/register`, {
        email,
        password,
        name: email.split('@')[0]
      });
      localStorage.setItem('receptor_token', response.data.token);
      localStorage.setItem('receptor_user', JSON.stringify(response.data.user));
      onRegister(response.data.user.email, response.data.token);
    }
  } catch (error) {
    console.error('Auth error:', error);
    alert(error.response?.data?.detail || 'Ошибка авторизации');
  } finally {
    setIsLoading(false);
  }
};
```

2. **Profile Edit Form**:
```javascript
const [editProfile, setEditProfile] = useState({
  name: currentUser?.name || '',
  email: currentUser?.email || '',
  city: currentUser?.city || ''
});

const handleUpdateProfile = async () => {
  try {
    const response = await axios.put(`${API}/user/${currentUser.id}/update`, editProfile);
    setCurrentUser(response.data);
    localStorage.setItem('receptor_user', JSON.stringify(response.data));
    alert('Профиль обновлен!');
  } catch (error) {
    alert('Ошибка обновления профиля');
  }
};
```

---

## 🚀 ГОТОВНОСТЬ К ДЕПЛОЮ

**Статус**: 📋 План готов  
**Приоритет**: 🔴 Высокий (блокирует полноценную работу)  
**Оценка времени**: 6-9 часов

---

**Дата**: 2025-01-XX  
**Статус**: План готов к реализации



