# 🌅 ДОБРОЕ УТРО, СЕРГЕЙ! БЫСТРЫЙ СТАРТ

## ✅ ЧТО УЖЕ ГОТОВО (вчера сделали):
- ✅ Python зависимости установлены
- ✅ Frontend зависимости установлены  
- ✅ `.env` файлы созданы
- ✅ Backend код готов
- ✅ Frontend код готов
- ✅ Все фиксы в Git

## 🎯 ЧТО НУЖНО ЗАВТРА (10 минут):

### Шаг 1: MongoDB Atlas (5 минут)
1. Открой https://www.mongodb.com/cloud/atlas/register
2. Регистрируйся (через Google - 30 секунд)
3. Create Free Cluster (M0 - бесплатно навсегда)
4. Database Access → Add User (username: `receptor`, пароль придумай)
5. Network Access → Allow Access from Anywhere
6. Clusters → Connect → Connect Your Application → Скопируй строку

**Пример строки:**
```
mongodb+srv://receptor:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/receptor_pro?retryWrites=true&w=majority
```

### Шаг 2: Обновить .env файл (1 минута)
Открой `backend\.env` и замени эту строку:
```
MONGO_URL=mongodb://localhost:27017/receptor_pro
```
На свою строку из Atlas:
```
MONGO_URL=mongodb+srv://receptor:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/receptor_pro?retryWrites=true&w=majority
```

### Шаг 3: Запустить всё (3 минуты)
Открой 2 окна PowerShell:

**Окно 1 - Backend:**
```powershell
cd "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\backend"
& "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Окно 2 - Frontend:**
```powershell
cd "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\frontend"
npm start
```

### Шаг 4: Открыть браузер
👉 http://localhost:3000

---

## 🎉 ГОТОВО! Начинаем тестировать с Testsprite!

---

## 📞 Если что-то не работает:
Пиши мне, я мгновенно помогу!

---

**P.S.** Брат, мы НИЧЕГО не сломали! Просто осталась 1 маленькая вещь - MongoDB креды. Завтра за 10 минут всё взлетит! 🚀

Спи спокойно! 😴

