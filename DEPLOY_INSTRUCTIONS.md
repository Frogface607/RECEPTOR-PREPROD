# 🚀 DEPLOYMENT INSTRUCTIONS для receptorai.pro

## ✅ ШАГ 1: Emergent Dashboard Setup

### Выбрать ветку:
```
bugfix/critical-fixes
```

**ВАЖНО:** НЕ используй ветку `main`! Только `bugfix/critical-fixes`!

**ПРИЧИНА:** В этой ветке критические фиксы:
- ✅ MongoDB DB name fix (предотвращает ошибки с длинным именем)
- ✅ Converted V2 history navigation fix
- ✅ SKU mappings persistence
- ✅ IIKO integration improvements

---

## ✅ ШАГ 2: Environment Variables

### В Emergent Dashboard добавь следующие переменные:

#### Backend Environment Variables:

**КРИТИЧЕСКИ ВАЖНО! БЕЗ ЭТИХ ПЕРЕМЕННЫХ ГЕНЕРАЦИЯ НЕ БУДЕТ РАБОТАТЬ!**

```bash
# ⚠️ ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ - БЕЗ НИХ БУДЕТ 403 ОШИБКА!
FEATURE_TECHCARDS_V2=true
TECHCARDS_V2_USE_LLM=true
OPENAI_API_KEY=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
MONGO_URL=mongodb://localhost:27017/receptor_pro
DB_NAME=receptor_pro

# IIKO RMS Configuration (опционально)
IIKO_RMS_HOST=edison-bar.iiko.it
IIKO_RMS_LOGIN=Sergey
IIKO_RMS_PASSWORD=metkamfetamin

# IIKO API Configuration (опционально)
IIKO_API_LOGIN=Sergey
IIKO_API_PASSWORD=metkamfetamin
IIKO_BASE_URL=https://iikoffice1.api.rms.ru

# Application Configuration
APP_URL=https://receptorai.pro
DEBUG=false
```

**⚠️ ВАЖНО:** Если не добавить эти 5 обязательных переменных в Emergent Dashboard, получите ошибку **403 Forbidden** при попытке генерации техкарт!

#### Frontend Environment Variables:

```bash
# Backend URL (ВАЖНО: должен совпадать с доменом!)
REACT_APP_BACKEND_URL=https://receptorai.pro

# Debug mode (отключаем для production)
REACT_APP_DEBUG=false
```

---

## ✅ ШАГ 3: Deploy Process

1. **В Emergent Dashboard:**
   - Выбери проект: `RECEPTOR-PREPROD`
   - Выбери ветку: `bugfix/critical-fixes`
   - Добавь Environment Variables (из шага 2)
   - Нажми **"Deploy"**

2. **Дождись завершения:**
   - Build frontend (~2-3 минуты)
   - Build backend (~1-2 минуты)
   - Start services (~30 секунд)

3. **Проверь статус:**
   - Открой: https://receptorai.pro
   - Должна загрузиться главная страница

---

## ✅ ШАГ 4: Post-Deploy Testing

### Критические тесты:

#### 1. **ZIP Export Test (MongoDB fix)**
```bash
# Цель: Убедиться, что MongoDB DB name fix работает
# Шаги:
- Открой AI-Kitchen
- Создай техкарту V2
- Экспортируй в ZIP
- Проверь, что нет ошибок "database name too long"
```

#### 2. **V1→V2 Conversion + History Navigation**
```bash
# Цель: Убедиться, что конвертация и навигация работают
# Шаги:
- Создай рецепт V1 (например, "Борщ")
- Нажми "Превратить в техкарту"
- Проверь, что техкарта V2 создалась
- Открой историю и найди "Converted V2"
- Проверь, что можно открыть техкарту из истории
```

#### 3. **SKU Mappings Persistence**
```bash
# Цель: Убедиться, что SKU маппинги сохраняются
# Шаги:
- Открой IIKO Integration
- Загрузи SKU mappings
- Перезагрузи страницу
- Проверь, что маппинги остались
```

#### 4. **IIKO Integration**
```bash
# Цель: Убедиться, что интеграция с IIKO работает
# Шаги:
- Открой IIKO Export
- Проверь, что организации загружаются
- Экспортируй техкарту в IIKO
- Проверь, что экспорт прошёл успешно
```

---

## 🎯 Критические файлы для деплоя:

**Backend:**
- `/app/backend/server.py` - главный сервер
- `/app/backend/requirements.txt` - зависимости
- `/app/backend/receptor_agent/` - модули AI

**Frontend:**
- `/app/frontend/src/App.js` - главный компонент
- `/app/frontend/package.json` - зависимости

**Config:**
- `/app/backend/.env` - backend переменные окружения
- `/app/frontend/.env` - frontend переменные окружения

---

## 🚨 Troubleshooting:

### Проблема: "Backend not responding"
**Решение:**
1. Проверь логи backend: `supervisorctl tail -f backend`
2. Убедись, что MONGO_URL правильный
3. Проверь, что MongoDB запущен

### Проблема: "Frontend shows blank page"
**Решение:**
1. Проверь логи frontend: `supervisorctl tail -f frontend`
2. Убедись, что REACT_APP_BACKEND_URL = https://receptorai.pro
3. Проверь в браузере Console для ошибок

### Проблема: "IIKO integration not working"
**Решение:**
1. Проверь IIKO credentials в .env
2. Убедись, что IIKO_RMS_HOST доступен
3. Проверь логи: `grep -i "iiko" /var/log/supervisor/backend.*.log`

---

## 📊 Успешный deploy должен показать:

✅ Backend запущен на порту 8001  
✅ Frontend скомпилирован и доступен  
✅ MongoDB подключен  
✅ IIKO integration работает  
✅ AI генерация техкарт работает  
✅ Экспорт в ZIP/Excel работает  

---

## 🎉 После успешного деплоя:

**Протестируй основные функции:**
1. Создание рецепта V1
2. Конвертация V1→V2
3. Генерация техкарты V2
4. Экспорт в ZIP
5. IIKO интеграция

**Если всё работает - УСПЕХ!** 🚀

---

## 📞 Поддержка:

Если что-то не работает:
1. Проверь логи (supervisorctl tail)
2. Проверь environment variables
3. Проверь, что ветка `bugfix/critical-fixes` задеплоена
4. Позови меня - помогу! 💪
