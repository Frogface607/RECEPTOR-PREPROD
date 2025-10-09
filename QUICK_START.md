# ⚡ QUICK START - Emergent Deploy для receptorai.pro

## 🎯 ДЛЯ ТЕБЯ (БРО!) - БЫСТРАЯ ИНСТРУКЦИЯ

### 1️⃣ Открой Emergent Dashboard

### 2️⃣ Выбери ветку:
```
bugfix/critical-fixes
```

### 3️⃣ Добавь эти 5 переменных в Environment Variables:

```bash
FEATURE_TECHCARDS_V2=true
TECHCARDS_V2_USE_LLM=true
OPENAI_API_KEY=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
MONGO_URL=mongodb://localhost:27017/receptor_pro
DB_NAME=receptor_pro
```

### 4️⃣ Нажми "Deploy"

### 5️⃣ Проверь:
Открой: https://receptorai.pro/api/v1/techcards.v2/status

Должно показать:
```json
{
  "feature_enabled": true,
  "llm_enabled": true
}
```

### 6️⃣ Протестируй генерацию:
1. Зайди на https://receptorai.pro
2. Введи "Омлет"
3. Генерируй!

---

## ❌ Если 403 ошибка:
**Проверь, что ВСЕ 5 переменных добавлены!**

---

## 📚 Подробная документация:
- `EMERGENT_DEPLOY_CHECKLIST.md` - полный чеклист
- `DEPLOY_INSTRUCTIONS.md` - детальная инструкция
- `.env.example` - пример всех переменных

---

**Готово к деплою! 🚀**
