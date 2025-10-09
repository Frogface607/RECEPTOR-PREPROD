# 🚀 Emergent Deploy Checklist для receptorai.pro

## ⚠️ ОБЯЗАТЕЛЬНЫЕ ШАГИ (БЕЗ НИХ НЕ БУДЕТ РАБОТАТЬ!)

### ✅ ШАГ 1: Выбрать ветку
```
bugfix/critical-fixes
```
**НЕ** используй `main`!

---

### ✅ ШАГ 2: Добавить Environment Variables в Emergent Dashboard

**Перейди в:** Emergent Dashboard → Settings → Environment Variables

**Добавь ВСЕ эти переменные (копируй построчно):**

```bash
FEATURE_TECHCARDS_V2=true
TECHCARDS_V2_USE_LLM=true
OPENAI_API_KEY=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
MONGO_URL=mongodb://localhost:27017/receptor_pro
DB_NAME=receptor_pro
```

**⚠️ КРИТИЧЕСКИ ВАЖНО:**
- Без этих переменных получишь **403 Forbidden** при генерации!
- Копируй ТОЧНО как написано (без лишних пробелов/кавычек)
- Все 5 переменных обязательны!

---

### ✅ ШАГ 3: Deploy

Нажми **"Deploy"** в Emergent Dashboard

**Ожидаемое время:**
- Build: 2-4 минуты
- Start: 30-60 секунд
- **Итого:** ~5 минут

---

### ✅ ШАГ 4: Проверка после деплоя

**4.1. Открой:** https://receptorai.pro

**4.2. Проверь генерацию V2:**
1. Введи название блюда (например: "Омлет")
2. Нажми кнопку генерации
3. Дождись результата (~15-30 секунд)

**✅ УСПЕХ:** Если техкарта создалась - всё работает!
**❌ ОШИБКА:** Если "403 Forbidden" - проверь переменные в Step 2

**4.3. Проверь статус V2:**
```bash
curl https://receptorai.pro/api/v1/techcards.v2/status
```

**Ожидаемый ответ:**
```json
{
  "feature_enabled": true,
  "llm_enabled": true,
  "model": "gpt-4o-mini"
}
```

---

## 🔧 Troubleshooting

### Проблема: "403 Forbidden" при генерации

**Причина:** Environment variables не добавлены или добавлены неправильно

**Решение:**
1. Открой Emergent Dashboard → Settings → Environment Variables
2. Проверь, что ВСЕ 5 переменных добавлены:
   - ✅ `FEATURE_TECHCARDS_V2=true`
   - ✅ `TECHCARDS_V2_USE_LLM=true`
   - ✅ `OPENAI_API_KEY=sk-proj-...`
   - ✅ `MONGO_URL=mongodb://localhost:27017/receptor_pro`
   - ✅ `DB_NAME=receptor_pro`
3. Если что-то пропущено - добавь и **редеплой**
4. Подожди 2-3 минуты после редеплоя

---

### Проблема: "feature_enabled: false"

**Причина:** Переменная `FEATURE_TECHCARDS_V2` не установлена или = `false`

**Решение:**
1. Добавь в Environment Variables: `FEATURE_TECHCARDS_V2=true`
2. Редеплой приложение
3. Проверь через `/api/v1/techcards.v2/status`

---

### Проблема: "llm_enabled: false"

**Причина:** Не установлены `TECHCARDS_V2_USE_LLM` или `OPENAI_API_KEY`

**Решение:**
1. Добавь обе переменные:
   - `TECHCARDS_V2_USE_LLM=true`
   - `OPENAI_API_KEY=sk-proj-...` (полный ключ)
2. Редеплой
3. Проверь статус

---

### Проблема: "MongoDB connection error"

**Причина:** Неправильный `MONGO_URL` или `DB_NAME`

**Решение:**
1. Проверь переменные:
   - `MONGO_URL=mongodb://localhost:27017/receptor_pro` (без кавычек!)
   - `DB_NAME=receptor_pro` (без кавычек!)
2. Убедись, что MongoDB запущен в Emergent окружении
3. Редеплой

---

## 📝 Quick Reference

**Репозиторий:** https://github.com/Frogface607/RECEPTOR-PREPROD.git

**Ветка:** `bugfix/critical-fixes`

**Домен:** https://receptorai.pro

**Backend:** https://receptorai.pro/api/

**Status endpoint:** https://receptorai.pro/api/v1/techcards.v2/status

---

## 🎯 Критические файлы

- `/app/backend/.env` - backend переменные (локально)
- `/app/frontend/.env` - frontend переменные (локально)
- `/app/backend/server.py` - главный сервер
- `/app/backend/receptor_agent/routes/techcards_v2.py` - V2 роутер

---

## ✅ Финальный чек-лист

Перед тем как завершить:

- [ ] Ветка `bugfix/critical-fixes` выбрана
- [ ] Все 5 environment variables добавлены в Dashboard
- [ ] Deploy успешно завершён
- [ ] https://receptorai.pro открывается
- [ ] `/api/v1/techcards.v2/status` возвращает `feature_enabled: true`
- [ ] Генерация техкарт работает (тест с "Омлет")
- [ ] Нет 403 ошибок в консоли браузера

**Если все галочки ✅ - ПОЗДРАВЛЯЮ, ДЕПЛОЙ УСПЕШЕН!** 🎉

---

**Дата:** 2025-10-09  
**Версия:** 1.0  
**Автор:** Emergent Agent
