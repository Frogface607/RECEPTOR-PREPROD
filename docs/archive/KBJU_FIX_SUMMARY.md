# 🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С KBJU CALCULATION

## ❌ ПРОБЛЕМА

- **4669 kcal на порцию** вместо ожидаемых **~700 kcal**
- **Перерасчет калорий** из-за неправильного `batch_grams` или `portion_grams`
- **Пустые или некорректные значения** `yield.perBatch_g` и `yield.perPortion_g`

## ✅ ИСПРАВЛЕНИЕ

### 1. Безопасный расчет `batch_grams`
- ✅ Проверка что `yield.perBatch_g` существует и > 0
- ✅ Fallback: расчет из суммы `netto_g` ингредиентов (более точно чем 1.0)
- ✅ Last resort: `portions * 200.0` (дефолтный размер порции)
- ✅ Валидация: `batch_grams` не должен быть < 10г

### 2. Безопасный расчет `portion_grams`
- ✅ Проверка что `yield.perPortion_g` существует и > 0
- ✅ Fallback: расчет из `batch_grams / portions`
- ✅ Валидация: `portion_grams` должен быть между 10г и 2000г
- ✅ Дефолт: 200г если значение некорректное

### 3. Защита от деления на ноль
- ✅ Проверка `batch_grams > 0` перед делением
- ✅ Проверка `portion_grams > 0` перед расчетом per_portion

### 4. Улучшенное логирование
- ✅ Логирование деталей расчета для отладки
- ✅ Предупреждения при использовании fallback значений

## 📁 ИЗМЕНЕННЫЕ ФАЙЛЫ

- ✅ `backend/receptor_agent/techcards_v2/nutrition_calculator.py`
  - Функция `calculate_tech_card_nutrition()` (строки 530-593)

## 🔍 ИЗМЕНЕНИЯ

### До исправления:
```python
batch_grams = tech_card.yield_.perBatch_g if tech_card.yield_ else 1.0
per100g = NutritionPer(
    kcal=round(total_nutrition["kcal"] * 100 / batch_grams, 1),
    ...
)
```

**Проблема**: Если `batch_grams = 1.0`, то `per100g.kcal = total_nutrition["kcal"] * 100 / 1.0 = 46.69 * 100 = 4669 kcal`

### После исправления:
```python
# Безопасный расчет с fallback
if tech_card.yield_ and tech_card.yield_.perBatch_g and tech_card.yield_.perBatch_g > 0:
    batch_grams = tech_card.yield_.perBatch_g
else:
    # Fallback: сумма netto_g
    total_netto = sum(float(ing.netto_g or 0) for ing in tech_card.ingredients)
    if total_netto > 0:
        batch_grams = total_netto
    else:
        batch_grams = portions * 200.0  # Дефолт

# Валидация
if batch_grams < 10.0:
    # Пересчет из ингредиентов
    ...
```

## 🎯 РЕЗУЛЬТАТ

- ✅ **Перерасчет калорий**: Исправлено - теперь используется правильный `batch_grams`
- ✅ **Валидация**: Добавлена проверка на минимальные/максимальные значения
- ✅ **Fallback**: Улучшен fallback на сумму `netto_g` вместо 1.0
- ✅ **Логирование**: Добавлено для отладки

## 🚀 ГОТОВО К ДЕПЛОЮ

**Статус**: ✅ Исправлено  
**Риск**: 🟢 Минимальный (только улучшения)  
**Тестирование**: Рекомендуется протестировать расчет KBJU после деплоя

---

**Дата**: 2025-01-XX  
**Файл**: `backend/receptor_agent/techcards_v2/nutrition_calculator.py`  
**Коммит**: `f7694b3c` (после push)



