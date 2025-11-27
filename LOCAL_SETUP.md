# 💻 ЛОКАЛЬНЫЙ ЗАПУСК ДЛЯ ТЕСТИРОВАНИЯ

## 🚀 БЫСТРЫЙ СТАРТ

### 1. Backend

```bash
# Перейди в директорию backend
cd backend

# Создай виртуальное окружение (рекомендуется)
python -m venv venv

# Активируй виртуальное окружение
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat

# Установи зависимости
pip install -r requirements.txt

# Создай .env файл
# Скопируй .env.example или создай новый:
```

**Создай `backend/.env`:**
```env
MONGODB_URI=твой_mongodb_uri
JWT_SECRET=твой_секретный_ключ_минимум_32_символа
OPENAI_API_KEY=твой_openai_key (опционально)
ENVIRONMENT=development
DB_NAME=receptor_pro
CORS_ALLOW_ALL=true
```

**Запусти сервер:**
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Backend будет доступен на: `http://localhost:8000`

### 2. Frontend

```bash
# В другом терминале, перейди в директорию frontend
cd frontend

# Установи зависимости (если еще не установлены)
npm install

# Создай .env.local файл
```

**Создай `frontend/.env.local`:**
```env
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=твой_google_client_id (опционально)
```

**Запусти frontend:**
```bash
npm start
```

Frontend будет доступен на: `http://localhost:3000`

## ✅ ПРОВЕРКА

1. **Backend health check:**
   ```
   http://localhost:8000/api/health
   ```

2. **Backend root:**
   ```
   http://localhost:8000/
   ```

3. **Frontend:**
   ```
   http://localhost:3000
   ```

## 🐛 РЕШЕНИЕ ПРОБЛЕМ

### Проблема: "Module not found"

**Решение:**
```bash
pip install -r requirements.txt
```

### Проблема: "Port already in use"

**Решение:**
- Измени порт: `uvicorn server:app --port 8001`
- Или убей процесс на порту 8000

### Проблема: "MongoDB connection failed"

**Решение:**
- Проверь `MONGODB_URI` в `.env`
- Убедись что MongoDB доступен (MongoDB Atlas или локальный)

### Проблема: CORS не работает

**Решение:**
- Убедись что `CORS_ALLOW_ALL=true` в `.env`
- Или добавь `http://localhost:3000` в `allow_origins`

## 💡 СОВЕТЫ

1. **Используй виртуальное окружение** - изолирует зависимости
2. **`.env` файл** - не коммить в git (добавь в `.gitignore`)
3. **`--reload` флаг** - автоматически перезагружает при изменениях
4. **Два терминала** - один для backend, один для frontend

---

**Готово!** Теперь можешь тестировать локально без Railway.



