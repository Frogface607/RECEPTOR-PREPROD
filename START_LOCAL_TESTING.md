# 🚀 START LOCAL TESTING - ПОШАГОВАЯ ИНСТРУКЦИЯ

**Дата:** 2025-10-08  
**Цель:** Запустить локально Backend + Frontend + Testsprite

---

## ✅ БЫСТРЫЙ СТАРТ (3 ТЕРМИНАЛА)

### **TERMINAL 1: MongoDB**

```bash
# Проверь запущен ли MongoDB:
mongosh --eval "db.adminCommand('ping')"

# Если ошибка - запусти:
mongod --dbpath "C:\data\db"

# Или как сервис:
net start MongoDB
```

**Проверка:** Должно быть `{ ok: 1 }`

---

### **TERMINAL 2: Backend (FastAPI)**

```bash
cd "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\backend"

# Проверь что .env файл существует:
cat .env

# Запусти backend:
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Ожидаемый результат:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using StatReload
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Проверка:** Открой в браузере:
- http://localhost:8001/docs (Swagger UI)
- http://localhost:8001/api/health (должен вернуть `{"status":"ok"}`)

**Если ошибка:**
- `Could not import module "server"` → проверь что ты в директории `/backend`
- `ModuleNotFoundError` → запусти `pip install -r requirements.txt` (пропусти emergentintegrations)
- `MongoDB connection error` → проверь что MongoDB запущен (Terminal 1)

---

### **TERMINAL 3: Frontend (React)**

```bash
cd "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\frontend"

# Проверь .env:
cat .env
# Должно быть: REACT_APP_BACKEND_URL=http://localhost:8001

# Установи зависимости (если еще не установлены):
yarn install

# Запусти frontend:
yarn start
```

**Ожидаемый результат:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

**Проверка:** Браузер автоматически откроет http://localhost:3000

---

## 🧪 TESTSPRITE ЗАПУСК

### **После того как Backend и Frontend работают:**

**В Cursor AI (этот чат):**

```
Бро, backend работает на localhost:8001! 
Запускай Testsprite! 🚀
```

И я запущу:
```javascript
mcp_TestSprite_testsprite_bootstrap_tests({
  localPort: 8001,
  type: "backend",
  projectPath: "C:\\Users\\Sergey\\RECEPTOR TEST\\RECEPTOR-PREPROD",
  testScope: "codebase"
})
```

---

## 🐛 TROUBLESHOOTING

### **Problem: Backend не запускается**

**Solution 1: Проверь зависимости**
```bash
cd backend
pip list | findstr "fastapi uvicorn motor pymongo"
```

Должны быть установлены:
- fastapi
- uvicorn
- motor
- pymongo
- python-dotenv
- openai

**Solution 2: Проверь MongoDB**
```bash
mongosh
# Если подключился → MongoDB работает
# Если ошибка → запусти mongod
```

**Solution 3: Проверь .env файл**
```bash
cd backend
cat .env
```

Должно быть:
```
MONGO_URL=mongodb://localhost:27017/receptor_pro
DB_NAME=receptor_pro
OPENAI_API_KEY=sk-proj-RGM... (твой ключ)
IIKO_API_LOGIN=Sergey
IIKO_API_PASSWORD=metkamfetamin
```

---

### **Problem: Frontend не запускается**

**Solution 1: Очисти кэш**
```bash
cd frontend
rm -rf node_modules
rm yarn.lock
yarn install
```

**Solution 2: Проверь Node.js версию**
```bash
node --version
# Должна быть >= 16.x
```

**Solution 3: Используй npm вместо yarn**
```bash
npm install
npm start
```

---

### **Problem: Testsprite не может подключиться**

**Solution:** Проверь что backend **реально работает**:

```bash
# Проверь порт:
netstat -ano | findstr :8001

# Должно быть:
# TCP    0.0.0.0:8001           0.0.0.0:0              LISTENING       XXXXX

# Проверь в браузере:
# http://localhost:8001/docs
```

---

## 📊 ЧТО TESTSPRITE БУДЕТ ТЕСТИРОВАТЬ

После успешного запуска Testsprite протестирует:

### **Backend Tests:**
1. ✅ Article Allocation (MongoDB fix applied)
2. ✅ Preflight Check
3. ✅ SKU Mapping persistence
4. ✅ Auto-mapping accuracy
5. ✅ ZIP Export
6. ✅ IIKO RMS integration
7. ✅ V1 recipe generation
8. ✅ V1→V2 conversion
9. ✅ Nutrition calculation
10. ✅ Cost calculation

### **Critical Bugs to Test:**
- 🔥 SKU mappings not persisting in MongoDB
- ⚠️ КБЖУ overcalculation (4669 kcal)
- 🐛 Auto-mapping UI not updating
- 🐛 Converted V2 техкарта lost on history click

---

## 💡 PRO TIPS

### **Быстрый restart всех сервисов:**
```bash
# Kill all (в PowerShell):
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process

# Start fresh (в 3 терминалах):
# 1. mongod
# 2. cd backend && python -m uvicorn server:app --port 8001 --reload
# 3. cd frontend && yarn start
```

### **Логи backend для debugging:**
```bash
# Добавь в server.py:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Тест API без браузера:**
```bash
# Health check:
curl http://localhost:8001/api/health

# Docs:
curl http://localhost:8001/docs
```

---

## 🎯 ГОТОВ К ТЕСТИРОВАНИЮ!

**Когда все 3 сервиса запущены:**
1. ✅ MongoDB (Terminal 1)
2. ✅ Backend на :8001 (Terminal 2)
3. ✅ Frontend на :3000 (Terminal 3)

**→ Скажи мне и я запущу Testsprite!** 🚀

---

**УДАЧИ, БРО!** 💪

P.S. Если что-то не получается - скопируй мне **полный текст ошибки** и я помогу! 🔧


