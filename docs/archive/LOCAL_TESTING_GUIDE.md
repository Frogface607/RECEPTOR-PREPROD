# 🚀 LOCAL TESTING GUIDE
## Быстрый запуск локального окружения + Testsprite

**Создано:** 2025-10-08  
**Цель:** Турбо-режим для тестирования и фиксов

---

## 📋 PREREQUISITES

### **1. Установленное ПО:**
```bash
# Backend
Python 3.9+
pip

# Frontend
Node.js 16+
yarn (или npm)

# Database
MongoDB 5.0+
```

### **2. Environment Variables:**

**Backend (.env в папке /backend):**
```bash
MONGO_URL=mongodb://localhost:27017/receptor_pro
DB_NAME=receptor_pro
OPENAI_API_KEY=sk-your-key-here
EMERGENT_LLM_KEY=emg-your-key-here
IIKO_API_LOGIN=your_iiko_login
IIKO_API_PASSWORD=your_iiko_password
```

**Frontend (.env в папке /frontend):**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## 🏃 QUICK START (3 COMMANDS)

### **Terminal 1: MongoDB**
```bash
# Запуск MongoDB
mongod --dbpath ./data/db

# Или если установлен как сервис:
# Windows:
net start MongoDB

# macOS/Linux:
sudo systemctl start mongodb
```

### **Terminal 2: Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Проверка:** Открой http://localhost:8001/docs (Swagger UI)

### **Terminal 3: Frontend**
```bash
cd frontend
yarn install
yarn start
```

**Проверка:** Открой http://localhost:3000

---

## 🧪 TESTSPRITE INTEGRATION

### **Запуск Testsprite для Backend Testing:**

```bash
# Testsprite bootstrap для backend
testsprite bootstrap \
  --localPort 8001 \
  --type backend \
  --projectPath "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD" \
  --testScope codebase
```

### **Запуск Testsprite для Frontend Testing:**

```bash
# Testsprite bootstrap для frontend
testsprite bootstrap \
  --localPort 3000 \
  --type frontend \
  --projectPath "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD" \
  --testScope codebase
```

---

## 🎯 TESTING WORKFLOW

### **Сценарий 1: Фикс SKU Persistence Bug**

```bash
# 1. Запусти локально (Backend + Frontend + MongoDB)
# 2. Открой http://localhost:3000
# 3. Зайди с реальным аккаунтом (607orlov@gmail.com)
# 4. Тестируй SKU маппинг:
#    - Создай/открой техкарту
#    - Сделай auto-mapping
#    - Reload страницы
#    - Проверь: сохранились ли маппинги?

# 5. Если баг воспроизводится, фиксим:
# Модифицируй код → Save → Backend автоперезагрузится (--reload)
# Frontend автообновится (yarn start hot reload)

# 6. Verify fix сразу на localhost!
```

### **Сценарий 2: КБЖУ Overcalculation Fix**

```bash
# 1. Открой техкарту "Паста Карбонара"
# 2. Проверь КБЖУ: показывает 4669 kcal?
# 3. Ищем проблему:
cd backend
grep -r "nutrition_calculator" receptor_agent/

# 4. Фиксим расчет
# 5. Backend перезагрузится автоматически
# 6. Regenerate техкарту → Verify КБЖУ ~700 kcal
```

### **Сценарий 3: Auto-Mapping UI Update**

```bash
# 1. Открой техкарту с unmapped ingredients
# 2. Жми "Автомаппинг"
# 3. Смотри console.log (DevTools)
# 4. Backend возвращает успех?
# 5. UI обновляется?

# Если UI не обновляется:
# → Открой frontend/src/App.js
# → Найди auto-mapping handler
# → Добавь setTcV2(updatedTechcard)
# → Save → Frontend hot reload
# → Verify сразу!
```

---

## 🔍 DEBUGGING TIPS

### **Backend Logs:**
```bash
# Backend с verbose logging:
uvicorn server:app --host 0.0.0.0 --port 8001 --reload --log-level debug
```

### **Frontend Console:**
```javascript
// В App.js добавь debug логи:
console.log('🔍 AUTO-MAPPING RESPONSE:', response.data);
console.log('🔍 CURRENT STATE:', tcV2);
```

### **MongoDB Queries:**
```bash
# Подключись к MongoDB:
mongosh

# Проверь техкарту:
use receptor_pro
db.techcards_v2.findOne({_id: "your-techcard-id"})

# Проверь есть ли product_code в ingredients:
db.techcards_v2.findOne(
  {_id: "your-techcard-id"},
  {"ingredients.product_code": 1, "ingredients.name": 1}
)
```

---

## ⚡ TESTSPRITE AUTO-TESTING

### **После локального запуска можем использовать Testsprite MCP:**

**В Cursor AI:**
```
Testsprite, please test the following scenarios on localhost:8001:

1. SKU mapping persistence:
   - Create techcard
   - Run auto-mapping
   - Reload techcard from DB
   - Verify product_code is saved

2. КБЖУ calculation:
   - Generate "Pasta Carbonara"
   - Check nutrition.energy_kcal
   - Expected: ~700 kcal
   - Actual: check value

3. Auto-mapping UI update:
   - Open techcard with unmapped ingredients
   - Click "Автомаппинг"
   - Verify UI updates without refresh
```

---

## 🔧 TROUBLESHOOTING

### **Backend не запускается:**
```bash
# Проверь зависимости:
pip install -r requirements.txt

# Проверь .env:
cat backend/.env

# Проверь порт:
netstat -an | grep 8001  # Windows
lsof -i :8001           # macOS/Linux
```

### **Frontend не собирается:**
```bash
# Очисти кэш:
cd frontend
rm -rf node_modules
rm yarn.lock
yarn install

# Или используй npm:
npm install
npm start
```

### **MongoDB не подключается:**
```bash
# Проверь статус:
mongosh --eval "db.adminCommand('ping')"

# Если нет MongoDB, установи:
# macOS: brew install mongodb-community
# Ubuntu: sudo apt-get install mongodb
# Windows: https://www.mongodb.com/try/download/community
```

---

## 📊 TESTSPRITE TEST PLAN

**После запуска локально, запустим Testsprite для:**

### **Backend Tests (port 8001):**
1. ✅ Article allocation endpoint
2. ✅ Preflight check endpoint
3. ✅ SKU mapping persistence
4. ✅ Auto-mapping accuracy
5. ✅ ZIP export (after MongoDB fix)

### **Frontend Tests (port 3000):**
1. ✅ V1 recipe generation
2. ✅ V1→V2 conversion
3. ✅ Auto-mapping UI update
4. ✅ History navigation
5. ✅ IIKO export modal

---

## 🎯 BENEFITS ЛОКАЛЬНОГО ТЕСТИРОВАНИЯ

### **Скорость:**
- ⚡ Hot reload (no deploy wait!)
- 🔧 Instant fixes
- 🧪 Immediate verification

### **Контроль:**
- 🔍 Full debugging access
- 📊 Console logs visible
- 🗄️ Direct MongoDB access

### **Безопасность:**
- 🛡️ No production impact
- 🧪 Safe experimentation
- 🔄 Easy rollback

---

## 🚀 NEXT STEPS

**После успешного локального запуска:**

1. ✅ Запустить Testsprite backend tests
2. ✅ Запустить Testsprite frontend tests
3. ✅ Фиксить bugs one by one
4. ✅ Verify fixes локально
5. ✅ Commit & Deploy на prod
6. ✅ Final verification на receptorai.pro

---

## 💡 PRO TIPS

### **Быстрый restart всего:**
```bash
# Kill all
pkill -f "uvicorn"
pkill -f "yarn"
pkill -f "mongod"

# Start fresh
mongod --dbpath ./data/db &
cd backend && uvicorn server:app --port 8001 --reload &
cd frontend && yarn start &
```

### **Watch режим для backend:**
```bash
# Auto-reload при изменениях:
watchmedo auto-restart --directory=./backend --pattern="*.py" --recursive \
  -- uvicorn server:app --host 0.0.0.0 --port 8001
```

### **Parallel testing:**
```bash
# Одновременно тестировать на localhost и prod:
# Terminal 1: localhost:3000 (local testing)
# Terminal 2: receptorai.pro (production verification)
```

---

**ГОТОВ К ТУРБО-ТЕСТИРОВАНИЮ! 🚀**

Запускай локально → фиксируй баги → verify → deploy → profit! 💪


