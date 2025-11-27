# 🚀 ПЛАН ДЕПЛОЯ - ЭТАПЫ 1-2

## 📋 ОБЗОР

**Production URL**: https://receptorai.pro  
**Backend**: kitchen-ai.emergent.host (или receptorai.pro)  
**Статус**: ✅ Готово к деплою

---

## ✅ ЭТАП 1: ДЕПЛОЙ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ

### Что деплоим:
- ✅ Исправления безопасности в `backend/server.py`
- ✅ 3 endpoints с проверкой `user_id`:
  - `/menu/{menu_id}/tech-cards`
  - `/menu-project/{project_id}/content`
  - `/menu-project/{project_id}/analytics`

### Файлы для деплоя:
- ✅ `backend/server.py` (строки 4645-4671, 5255-5310, 5405-5444)

### Шаги деплоя:

#### 1. Проверка перед деплоем
```bash
# Проверить что файлы готовы
git status
git diff backend/server.py
```

#### 2. Коммит изменений
```bash
git add backend/server.py
git commit -m "🔒 Security fix: Add user_id validation to GET endpoints"
git push origin main
```

#### 3. Деплой на продакшен
**Вариант A: Если используется Git-based деплой (автоматический)**
- Изменения автоматически задеплоятся после push

**Вариант B: Если нужно деплоить вручную**
```bash
# SSH на сервер
ssh user@receptorai.pro

# Перейти в директорию проекта
cd /path/to/backend

# Pull изменений
git pull origin main

# Перезапустить сервис (зависит от системы)
# Если используется systemd:
sudo systemctl restart receptor-backend

# Если используется supervisor:
supervisorctl restart receptor-backend

# Если используется Docker:
docker-compose restart backend
```

#### 4. Проверка после деплоя
```bash
# Проверить что сервер запустился
curl https://receptorai.pro/api/health

# Проверить логи
tail -f /var/log/receptor-backend.log
```

---

## ✅ ЭТАП 2: ЗАПУСК СКРИПТА СОЗДАНИЯ ИНДЕКСОВ

### Что деплоим:
- ✅ Скрипт `backend/scripts/create_indexes.py`
- ✅ 18 индексов для 6 коллекций MongoDB

### Файлы для деплоя:
- ✅ `backend/scripts/create_indexes.py` (новый файл)

### Шаги деплоя:

#### 1. Проверка перед запуском
```bash
# Проверить что скрипт готов
ls -la backend/scripts/create_indexes.py

# Проверить переменные окружения
echo $MONGODB_URI
echo $DB_NAME
```

#### 2. Коммит скрипта (если еще не закоммичен)
```bash
git add backend/scripts/create_indexes.py
git commit -m "🔧 Add safe MongoDB index creation script"
git push origin main
```

#### 3. Запуск скрипта на продакшене

**Вариант A: Локально (если есть доступ к MongoDB)**
```bash
cd backend
python scripts/create_indexes.py
```

**Вариант B: На сервере (SSH)**
```bash
# SSH на сервер
ssh user@receptorai.pro

# Перейти в директорию проекта
cd /path/to/backend

# Активировать виртуальное окружение (если есть)
source venv/bin/activate  # или .venv/bin/activate

# Запустить скрипт
python scripts/create_indexes.py
```

**Вариант C: Через Python с переменными окружения**
```bash
cd backend
MONGODB_URI="your_mongo_uri" DB_NAME="receptor_pro" python scripts/create_indexes.py
```

#### 4. Проверка после запуска
```bash
# Скрипт выведет статистику:
# ✅ Created: X new indexes
# ℹ️  Skipped: Y existing indexes

# Проверить индексы в MongoDB (опционально)
# Через MongoDB Compass или mongo shell:
# db.techcards_v2.getIndexes()
# db.users.getIndexes()
```

---

## 🔍 ЧЕКЛИСТ ДЕПЛОЯ

### Перед деплоем:
- [ ] Все изменения закоммичены в Git
- [ ] Тесты пройдены (синтаксис, логика)
- [ ] Резервная копия базы данных создана (рекомендуется)
- [ ] Переменные окружения проверены

### Деплой Этапа 1 (Security Fixes):
- [ ] `backend/server.py` обновлен
- [ ] Сервер перезапущен
- [ ] Health check пройден
- [ ] Логи проверены (нет ошибок)

### Деплой Этапа 2 (Indexes):
- [ ] `backend/scripts/create_indexes.py` доступен
- [ ] MongoDB connection работает
- [ ] Скрипт запущен
- [ ] Индексы созданы (проверено в логах)
- [ ] Производительность улучшена (опционально)

### После деплоя:
- [ ] Все endpoints работают
- [ ] User isolation работает (протестировано)
- [ ] Нет ошибок в логах
- [ ] Производительность улучшена

---

## ⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ

### Безопасность:
1. ✅ **Обратная совместимость**: Сохранена - старый код продолжит работать
2. ✅ **Индексы**: Безопасны - не удаляют и не модифицируют существующие
3. ✅ **Повторный запуск**: Можно запускать многократно

### Производительность:
1. ⚠️ **Создание индексов**: Может занять время на больших коллекциях (обычно секунды-минуты)
2. ⚠️ **Блокировки**: MongoDB может временно блокировать запись при создании индексов
3. ✅ **Рекомендуется**: Запускать в период низкой нагрузки

### Откат (если что-то пошло не так):
1. **Этап 1**: Откатить `backend/server.py` к предыдущей версии
2. **Этап 2**: Индексы можно удалить вручную через MongoDB (но не рекомендуется)

---

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### После Этапа 1:
- ✅ User isolation работает
- ✅ Безопасность улучшена
- ✅ Обратная совместимость сохранена

### После Этапа 2:
- ✅ 10-100x ускорение запросов
- ✅ Улучшение безопасности (user isolation enforced)
- ✅ Автоматическая очистка истекших резерваций
- ✅ Быстрый поиск по названиям

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

После успешного деплоя:
1. ✅ Протестировать endpoints с `user_id`
2. ✅ Обновить фронтенд для передачи `user_id` (рекомендуется)
3. ✅ Мониторить производительность
4. ✅ Перейти к Этапу 3 (KBJU Calculation)

---

**Дата создания**: 2025-01-XX  
**Статус**: ✅ Готово к деплою  
**Риск**: 🟢 Минимальный



