# 🧪 Инструкция по тестированию батчевой генерации меню

## 📋 Подготовка

### 1. Запуск Backend

```bash
# Перейти в директорию backend
cd backend

# Запустить сервер (зависит от вашей настройки)
# Например:
python server.py
# или
uvicorn server:app --reload --port 8000
```

Убедитесь, что сервер запущен на `http://localhost:8000`

### 2. Проверка доступности

```bash
curl http://localhost:8000/health
# или откройте в браузере
```

---

## 🚀 Запуск тестов

### Автоматическое тестирование

```bash
python test_batch_menu_generation.py
```

Тест проверит:
1. ✅ Генерацию тестового меню (6 блюд)
2. ✅ Парсинг меню на позиции
3. ✅ Конвертацию позиции в V1 рецепт
4. ✅ Конвертацию позиции в V2 техкарту
5. ✅ Батчевую конвертацию нескольких позиций
6. ✅ Проверку статуса после конвертации

---

## 🔧 Ручное тестирование через API

### 1. Создать меню

```bash
POST http://localhost:8000/api/generate-menu
Content-Type: application/json

{
  "user_id": "test_user",
  "menu_profile": {
    "menuType": "restaurant",
    "dishCount": 6,
    "averageCheck": "800-1200",
    "cuisineStyle": "european",
    "useConstructor": true,
    "categories": {
      "salads": 2,
      "soups": 1,
      "main_dishes": 2,
      "desserts": 1
    }
  },
  "venue_profile": {
    "venue_name": "Тестовый ресторан",
    "venue_type": "family_restaurant",
    "cuisine_type": "европейская",
    "average_check": "800-1200"
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "menu_id": "uuid-here",
  "menu": {...}
}
```

### 2. Парсинг позиций меню

```bash
GET http://localhost:8000/api/menu/{menu_id}/parse-items?user_id=test_user
```

**Ответ:**
```json
{
  "success": true,
  "menu_id": "...",
  "menu_name": "...",
  "items": [
    {
      "id": "item-uuid",
      "index": 0,
      "name": "Название блюда",
      "category": "Салаты",
      "metadata": {
        "can_convert_to_v1": true,
        "can_convert_to_v2": true,
        "has_techcard": false,
        "converted_to_v1": false,
        "converted_to_v2": false
      }
    }
  ],
  "total_items": 6
}
```

### 3. Конвертация позиции в V1

```bash
POST http://localhost:8000/api/menu/{menu_id}/items/{item_id}/convert
Content-Type: application/json

{
  "user_id": "test_user",
  "target_format": "v1",
  "options": {
    "generate_techcard": true,
    "save_to_history": true
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "format": "v1",
  "recipe_id": "uuid",
  "content": "Рецепт...",
  "message": "Рецепт V1 успешно создан!"
}
```

### 4. Конвертация позиции в V2

```bash
POST http://localhost:8000/api/menu/{menu_id}/items/{item_id}/convert
Content-Type: application/json

{
  "user_id": "test_user",
  "target_format": "v2",
  "options": {
    "generate_techcard": true,
    "save_to_history": true
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "format": "v2",
  "techcard_id": "uuid",
  "techcard": {...},
  "message": "Техкарта V2 успешно создана!"
}
```

### 5. Батчевая конвертация

```bash
POST http://localhost:8000/api/menu/{menu_id}/items/batch-convert
Content-Type: application/json

{
  "user_id": "test_user",
  "item_ids": ["item-id-1", "item-id-2", "item-id-3"],
  "target_format": "v1",
  "options": {
    "generate_techcard": true,
    "save_to_history": true
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "total_items": 3,
  "successful": 3,
  "failed": 0,
  "results": [...],
  "failed_items": [],
  "message": "Обработано 3 из 3 позиций"
}
```

---

## 🐛 Известные проблемы

1. **Требуется PRO подписка**
   - Если тест падает с 403, используйте `demo_user` или создайте пользователя с PRO подпиской

2. **Таймауты**
   - Генерация меню может занять 30-60 секунд
   - Конвертация V2 может занять 30-45 секунд
   - Батчевая конвертация: ~1 минута на позицию

3. **Кодировка Windows**
   - Скрипт автоматически исправляет кодировку для Windows
   - Если проблемы остаются, запустите: `chcp 65001` перед запуском

---

## ✅ Ожидаемые результаты

После успешного тестирования:

1. ✅ Меню создано с `item_id` для каждой позиции
2. ✅ Парсинг возвращает все позиции с метаданными
3. ✅ V1 рецепты создаются и сохраняются
4. ✅ V2 техкарты создаются и сохраняются
5. ✅ Статус конвертации обновляется в метаданных
6. ✅ Батчевая конвертация обрабатывает несколько позиций

---

## 📝 Проверка в БД

После тестирования можно проверить в MongoDB:

```javascript
// Найти меню
db.user_history.findOne({id: "menu_id", is_menu: true})

// Найти созданные рецепты/техкарты
db.user_history.find({
  from_menu_id: "menu_id",
  is_menu: false
})

// Проверить связь через item_id
db.user_history.find({
  from_menu_item_id: "item_id"
})
```

---

**Готово к тестированию!** 🚀







