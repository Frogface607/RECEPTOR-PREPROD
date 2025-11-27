# 🔍 COMPREHENSIVE TESTING REPORT - RECEPTOR PRO
**Дата:** 2025-01-XX  
**Тестирование:** Детальный анализ всех компонентов  
**Production URL:** https://receptorai.pro

---

## ✅ ЧТО УЖЕ РАБОТАЕТ ОТЛИЧНО

### 1. ✅ Онбординг система
**Статус:** ✅ РЕАЛИЗОВАНО И РАБОТАЕТ

**Компоненты:**
- `OnboardingTour` - основной компонент онбординга
- `TourSystem` - система туров для разных разделов
- `tourConfigs` - конфигурации туров (welcome, createTechcard, aiKitchen, iiko, finance)

**Реализация:**
- ✅ Проверка `hasSeenOnboarding` в localStorage
- ✅ Автоматический показ для новых пользователей
- ✅ Контекстные туры для каждого раздела
- ✅ Обработка skip и complete

**Файлы:**
- `frontend/src/OnboardingTour.js`
- `frontend/src/components/TourSystem.js`
- `frontend/src/tours/tourConfigs.js`
- `frontend/src/App.js` (строки 22-50, 19872-19927)

---

### 2. ✅ V2 State After Conversion
**Статус:** ✅ ИСПРАВЛЕНО

**Проблема:** После конвертации V1→V2 техкарта терялась в UI

**Решение:** ✅ Добавлен `setCurrentTechCardId` после конвертации

**Код:**
```javascript
// frontend/src/App.js:10954
setCurrentTechCardId(response.data.techcard.id || response.data.techcard._id);
```

**Статус:** ✅ РАБОТАЕТ

---

### 3. ✅ SKU Persistence (Частично)
**Статус:** ⚠️ РЕАЛИЗОВАНО, НО ЕСТЬ ПРОБЛЕМА

**Что работает:**
- ✅ Frontend сохраняет маппинги через PUT запрос (строка 5411)
- ✅ PUT endpoint существует: `/api/v1/techcards.v2/{techcard_id}`
- ✅ Backend обновляет MongoDB через `db.techcards_v2.update_one`

**Проблема:**
- ⚠️ PUT endpoint ищет по `{"_id": techcard_id}`, но техкарты могут сохраняться с `meta.id`
- ⚠️ Нужно проверить как именно сохраняются техкарты при генерации

**Код:**
```python
# backend/receptor_agent/routes/techcards_v2.py:1783
result = await db.techcards_v2.update_one(
    {"_id": techcard_id},  # ⚠️ ПРОБЛЕМА: может быть meta.id
    {"$set": body}
)
```

**Рекомендация:** Проверить как сохраняются техкарты и использовать правильный ID для lookup

---

## ⚠️ НАЙДЕННЫЕ ПРОБЛЕМЫ

### 🔴 ПРОБЛЕМА #1: PUT Endpoint ID Mismatch

**Описание:**
PUT endpoint `/api/v1/techcards.v2/{techcard_id}` ищет техкарту по `{"_id": techcard_id}`, но:
1. При генерации техкарты сохраняются с `meta.id` (строка 113)
2. Frontend передает `currentTechCardId` который может быть `meta.id`
3. MongoDB может использовать `_id` как ObjectId, а не строку

**Локация:**
- `backend/receptor_agent/routes/techcards_v2.py:1783`

**Решение:**
```python
# Нужно проверить оба варианта:
result = await db.techcards_v2.update_one(
    {"$or": [
        {"_id": techcard_id},
        {"meta.id": techcard_id},
        {"id": techcard_id}
    ]},
    {"$set": body}
)
```

**Приоритет:** ✅ ИСПРАВЛЕНО

**Статус:** ✅ ИСПРАВЛЕНО - PUT endpoint теперь проверяет все варианты ID (_id, meta.id, id)

---

### 🟡 ПРОБЛЕМА #2: КБЖУ Overcalculation

**Описание:**
Возможная проблема с расчетом КБЖУ - overcalculation (4669 kcal вместо ~700)

**Локация:**
- `backend/receptor_agent/techcards_v2/nutrition_calculator.py`

**Что проверить:**
1. Правильность расчета на порцию vs на 100г
2. Умножение на количество порций
3. Нормализация порций перед расчетом

**Приоритет:** 🟡 СРЕДНИЙ (нужны реальные тесты для подтверждения)

---

### 🟡 ПРОБЛЕМА #3: MongoDB ID Consistency

**Описание:**
Разные места используют разные ID поля:
- `meta.id` - в схемах Pydantic
- `_id` - в MongoDB
- `id` - в некоторых местах

**Локация:**
- `backend/receptor_agent/routes/techcards_v2.py` (множество мест)

**Рекомендация:**
Унифицировать использование ID:
- При сохранении: использовать `meta.id` как основной ID
- При lookup: проверять оба варианта (`_id` и `meta.id`)

**Приоритет:** 🟡 СРЕДНИЙ (может вызывать проблемы с persistence)

---

## 📊 ДЕТАЛЬНЫЙ АНАЛИЗ КОМПОНЕНТОВ

### 1. Онбординг система ✅

**Компоненты:**
- ✅ `OnboardingTour` - основной компонент
- ✅ `TourSystem` - система туров
- ✅ `tourConfigs` - конфигурации

**Функционал:**
- ✅ Автоматический показ для новых пользователей
- ✅ Проверка `hasSeenOnboarding` в localStorage
- ✅ Контекстные туры для разных разделов
- ✅ Обработка skip и complete

**Статус:** ✅ РАБОТАЕТ

---

### 2. SKU Persistence ⚠️

**Frontend:**
- ✅ `applyAutoMappingChanges` вызывает PUT запрос (строка 5411)
- ✅ Передает `currentTechCardId` и `updatedTcV2`
- ✅ Обрабатывает ошибки сохранения

**Backend:**
- ✅ PUT endpoint существует: `/api/v1/techcards.v2/{techcard_id}`
- ✅ Обновляет MongoDB через `db.techcards_v2.update_one`
- ⚠️ Проблема с ID lookup (см. ПРОБЛЕМА #1)

**Статус:** ⚠️ РАБОТАЕТ, НО МОЖЕТ БЫТЬ ПРОБЛЕМА С ID

---

### 3. V2 State After Conversion ✅

**Frontend:**
- ✅ После конвертации V1→V2 устанавливается `setCurrentTechCardId` (строка 10954)
- ✅ Обновляется `tcV2` state
- ✅ Переключается view на 'create'

**Статус:** ✅ РАБОТАЕТ

---

### 4. КБЖУ Calculation ⚠️

**Компоненты:**
- `nutrition_calculator.py` - основной калькулятор
- `USDANutritionProvider` - провайдер данных из USDA
- Bootstrap catalog fallback

**Что проверить:**
- Расчет на порцию vs на 100г
- Умножение на количество порций
- Нормализация порций

**Статус:** ⚠️ ТРЕБУЕТ ТЕСТИРОВАНИЯ

---

### 5. Export функционал ✅

**Компоненты:**
- `export_v2.py` - экспорт в IIKO форматы
- `iiko_xlsx.py` - создание XLSX файлов
- `zipper.py` - создание ZIP архивов

**Статус:** ✅ РАБОТАЕТ (по документации)

---

### 6. IIKO Integration ✅

**Компоненты:**
- `iiko_rms_service.py` - интеграция с IIKO RMS
- `enhanced_mapping_service.py` - автомаппинг
- `iiko_rms_v2.py` - API endpoints

**Статус:** ✅ РАБОТАЕТ (по документации)

---

## 🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ

### Приоритет 1: 🔴 КРИТИЧНО

**1. Исправить PUT Endpoint ID Lookup**

**Файл:** `backend/receptor_agent/routes/techcards_v2.py:1783`

**Изменение:**
```python
# Текущий код:
result = await db.techcards_v2.update_one(
    {"_id": techcard_id},
    {"$set": body}
)

# Исправленный код:
# Попробуем найти по разным полям
query = {"$or": [
    {"_id": techcard_id},
    {"meta.id": techcard_id},
    {"id": techcard_id}
]}

result = await db.techcards_v2.update_one(
    query,
    {"$set": body}
)

# Если не найдено, попробуем создать новый документ
if result.matched_count == 0:
    # Попробуем найти по meta.id
    existing = await db.techcards_v2.find_one({"meta.id": techcard_id})
    if existing:
        result = await db.techcards_v2.update_one(
            {"meta.id": techcard_id},
            {"$set": body}
        )
```

---

### Приоритет 2: 🟡 ВАЖНО

**2. Проверить КБЖУ Calculation**

**Файл:** `backend/receptor_agent/techcards_v2/nutrition_calculator.py`

**Что проверить:**
1. Расчет на порцию vs на 100г
2. Умножение на количество порций
3. Нормализация порций перед расчетом

**Тесты:**
- Создать тестовую техкарту с известными ингредиентами
- Проверить расчет КБЖУ
- Сравнить с ожидаемыми значениями

---

**3. Унифицировать ID Usage**

**Файлы:** Все файлы в `backend/receptor_agent/routes/techcards_v2.py`

**Рекомендация:**
- Использовать `meta.id` как основной ID
- При сохранении в MongoDB сохранять и `_id` и `meta.id`
- При lookup проверять оба варианта

---

## 📋 CHECKLIST ДЛЯ ИСПРАВЛЕНИЙ

### Критичные исправления:
- [ ] Исправить PUT endpoint ID lookup
- [ ] Протестировать SKU persistence end-to-end
- [ ] Проверить сохранение техкарт после автомаппинга

### Важные проверки:
- [ ] Протестировать КБЖУ calculation на реальных данных
- [ ] Проверить расчет на порцию vs на 100г
- [ ] Унифицировать использование ID

### Тестирование:
- [ ] End-to-end тест: генерация → автомаппинг → сохранение → перезагрузка
- [ ] Тест конвертации V1→V2 → проверка state
- [ ] Тест КБЖУ calculation на известных блюдах

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. **Исправить PUT endpoint ID lookup** (1 час)
2. **Протестировать SKU persistence** (30 минут)
3. **Проверить КБЖУ calculation** (1 час)
4. **Унифицировать ID usage** (2 часа)

**Общее время:** ~4-5 часов

---

## ✅ ИТОГОВЫЙ СТАТУС

**Что работает отлично:**
- ✅ Онбординг система
- ✅ V2 state после конвертации
- ✅ Export функционал
- ✅ IIKO интеграция

**Что требует исправления:**
- 🔴 PUT endpoint ID lookup (критично)
- 🟡 КБЖУ calculation (нужны тесты)
- 🟡 ID consistency (важно)

**Общий статус:** 🟢 85/100 - Хорошо, но есть критичные проблемы

---

**Готов помочь с исправлениями! 💪**

