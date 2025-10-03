# AI-Kitchen Enhancement Plan

## Цель
Активировать все AI-функции и добавить возможность сохранения результатов как V1 рецепты с последующей конвертацией в V2.

## Фаза 1: Активация AI-функций ✅

### Уже работают:
- ✅ Вдохновение (Inspiration)
- ✅ Фудпейринг (Food Pairing)
- ✅ V1 Recipe Generation
- ✅ V1→V2 Conversion

### Нужно активировать:
- ⚙️ Скрипт продаж (Sales Script)
- ⚙️ Финансовый анализ (Financial Analysis)
- ⚙️ Фотопрезентация (Photo Tips)
- ⚙️ Лабораторные эксперименты (Laboratory Experiments)
- ⚙️ Прокачать блюдо (Enhance Dish)

## Фаза 2: Сохранение AI-результатов как V1 ⚙️

### Задачи:
1. Добавить кнопку "Сохранить как V1" в модальные окна AI-функций
2. Создать универсальную функцию `saveAIResultAsV1(resultContent, sourceName)`
3. Сохранять в MongoDB как V1 рецепты с метаданными

## Фаза 3: V1 из истории → AI-Kitchen ⚙️

### Задачи:
1. При клике на V1 рецепт переключать `currentView` на 'aiKitchen'
2. Загружать V1 контент в `aiKitchenRecipe` state
3. Показывать кнопку "Превратить в техкарту" для V1→V2 конвертации
4. Все AI-функции должны работать с загруженным V1 рецептом

## Технические детали

### Backend endpoints:
- ✅ /api/generate-inspiration
- ✅ /api/generate-food-pairing
- ✅ /api/generate-sales-script
- ✅ /api/generate-photo-tips
- ✅ /api/analyze-finances
- ⚠️ /api/conduct-experiment (нужно проверить)
- ⚠️ /api/enhance-dish (нужно создать)

### Frontend state updates:
- Добавить поддержку `aiKitchenRecipe` во все AI-функции
- Создать модальные окна для новых функций
- Добавить логику сохранения как V1
