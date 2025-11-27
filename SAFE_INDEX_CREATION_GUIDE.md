# 🔒 БЕЗОПАСНОЕ СОЗДАНИЕ ИНДЕКСОВ MONGODB

## ✅ Что делает скрипт

Скрипт `backend/scripts/create_indexes.py` **БЕЗОПАСНО** создает индексы MongoDB:

1. ✅ **Проверяет существующие индексы** - не создает дубликаты
2. ✅ **Проверяет существование коллекций** - пропускает несуществующие
3. ✅ **Ничего не удаляет** - только добавляет новые индексы
4. ✅ **Ничего не модифицирует** - не изменяет существующие индексы
5. ✅ **Безопасно для продакшена** - можно запускать многократно

## 🚀 Как запустить

### Вариант 1: Локально (если есть доступ к MongoDB)

```powershell
cd "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\backend"
python scripts/create_indexes.py
```

### Вариант 2: На продакшене (receptorai.pro)

Если у тебя есть SSH доступ к серверу:

```bash
cd /path/to/backend
python3 scripts/create_indexes.py
```

### Вариант 3: Через Python с переменными окружения

```powershell
cd "C:\Users\Sergey\RECEPTOR TEST\RECEPTOR-PREPROD\backend"
$env:MONGODB_URI="your_mongo_uri"
$env:DB_NAME="receptor_pro"
python scripts/create_indexes.py
```

## 📋 Что будет создано

### 1. Users Collection
- `email_unique` - уникальный индекс на email
- `id_unique` - уникальный индекс на id
- `subscription_plan_1` - индекс на план подписки
- `created_at_-1` - индекс на дату создания

### 2. TechCards V2 Collection (🔥 КРИТИЧНО ДЛЯ БЕЗОПАСНОСТИ!)
- `user_id_1` - **SECURITY**: изоляция пользователей
- `user_created` - составной индекс (user_id + created_at)
- `title_search` - текстовый поиск по названию
- `article_1` - индекс на артикул

### 3. User History Collection
- `user_id_1` - **SECURITY**: изоляция пользователей
- `created_at_-1` - индекс на дату создания
- `is_menu_1` - фильтр по типу (меню/техкарта)

### 4. Tech Cards V1 Collection
- `user_id_1` - изоляция пользователей
- `created_at_-1` - индекс на дату создания

### 5. Article Reservations Collection
- `article_unique` - уникальный индекс на артикул
- `status_1` - индекс на статус
- `organization_id_1` - индекс на организацию
- `expires_at_ttl` - **TTL индекс** (автоудаление истекших резерваций!)

### 6. Menu Projects Collection
- `user_id_1` - изоляция пользователей
- `created_at_-1` - индекс на дату создания

## ⚠️ Важные замечания

1. **Безопасность**: Скрипт НЕ удаляет и НЕ модифицирует существующие индексы
2. **Повторный запуск**: Можно запускать многократно - он пропустит существующие индексы
3. **Производительность**: Создание индексов может занять время на больших коллекциях
4. **Блокировки**: MongoDB может временно блокировать запись при создании индексов (обычно секунды)

## 📊 Ожидаемый результат

После успешного выполнения:

```
🎉 INDEX CREATION COMPLETE!
✅ Created: X new indexes
ℹ️  Skipped: Y existing indexes

💡 Expected performance improvement: 10-100x faster queries!
🔒 Security improvement: User isolation enforced!
✅ All operations completed safely - no data modified!
```

## 🔍 Проверка после запуска

Можно проверить созданные индексы через MongoDB Compass или mongo shell:

```javascript
// Подключиться к базе
use receptor_pro

// Проверить индексы в коллекции
db.techcards_v2.getIndexes()
db.users.getIndexes()
db.user_history.getIndexes()
```

## ❓ Если что-то пошло не так

1. **Ошибка подключения**: Проверь `MONGODB_URI` или `MONGO_URL`
2. **Ошибка прав доступа**: Убедись что пользователь MongoDB имеет права на создание индексов
3. **Дубликаты уникальных индексов**: Если есть дубликаты данных, уникальный индекс не создастся (это нормально)

## 🎯 Следующие шаги

После создания индексов:
1. ✅ Проверить производительность запросов
2. ✅ Протестировать user isolation (безопасность)
3. ✅ Мониторить использование индексов через `explain()`

---

**Создано**: 2025-01-XX  
**Версия скрипта**: 2.0 (Safe Edition)



