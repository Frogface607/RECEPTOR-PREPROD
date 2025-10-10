# 🚀 Как запустить RECEPTOR локально

## ✅ ШАГ 1: Запустить MongoDB
Открой **PowerShell #1** и выполни:
```powershell
mongod --dbpath C:\data\db
```
Должно появиться: `waiting for connections on port 27017`

---

## ✅ ШАГ 2: Запустить Backend
Открой **PowerShell #2** и выполни:
```powershell
cd "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\backend"
& "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```
Должно появиться: `Uvicorn running on http://0.0.0.0:8001`

---

## ✅ ШАГ 3: Запустить Frontend
Открой **PowerShell #3** и выполни:
```powershell
cd "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\frontend"
npm start
```
Должен открыться браузер на `http://localhost:3000`

---

## 🧪 Проверка
- Backend: http://localhost:8001/docs
- Frontend: http://localhost:3000

---

## 🛑 Остановка
В каждом окне PowerShell нажми **Ctrl+C**

