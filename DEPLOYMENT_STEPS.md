# 🚀 ШАГИ ДЕПЛОЯ - ЭТАПЫ 1-2

## ✅ ШАГ 1: КОММИТ И PUSH - ВЫПОЛНЕНО

- ✅ Коммит создан: `86c68283`
- ✅ Сообщение: "Security: Add user_id validation to GET endpoints and safe MongoDB index creation script"
- ✅ Файлы в коммите:
  - `backend/server.py` - исправления безопасности
  - `backend/scripts/create_indexes.py` - скрипт создания индексов

---

## 🔄 ШАГ 2: PUSH В РЕПОЗИТОРИЙ - В ПРОЦЕССЕ

```bash
git push origin main
```

**После push:**
- Если используется автоматический деплой → изменения задеплоятся автоматически
- Если ручной деплой → нужно задеплоить вручную

---

## 🚀 ШАГ 3: ДЕПЛОЙ НА ПРОДАКШЕН

### Вариант A: Автоматический деплой
- ✅ Изменения автоматически задеплоятся после push

### Вариант B: Ручной деплой
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

---

## 🔧 ШАГ 4: ЗАПУСК СКРИПТА СОЗДАНИЯ ИНДЕКСОВ

```bash
# На сервере или локально (если есть доступ к MongoDB)
cd backend
python scripts/create_indexes.py
```

**Ожидаемый результат:**
```
🎉 INDEX CREATION COMPLETE!
✅ Created: X new indexes
ℹ️  Skipped: Y existing indexes
```

---

## ✅ ШАГ 5: ПРОВЕРКА ПОСЛЕ ДЕПЛОЯ

### 1. Проверить health endpoint
```bash
curl https://receptorai.pro/api/health
```

### 2. Проверить логи
```bash
tail -f /var/log/receptor-backend.log
```

### 3. Проверить endpoints с user_id
- `/menu/{menu_id}/tech-cards?user_id=test_user_1`
- `/menu-project/{project_id}/content?user_id=test_user_1`
- `/menu-project/{project_id}/analytics?user_id=test_user_1`

### 4. Проверить индексы (опционально)
- Проверить логи скрипта создания индексов
- Проверить производительность запросов

---

## 📋 ЧЕКЛИСТ

- [x] Коммит создан
- [ ] Push в репозиторий
- [ ] Деплой на продакшен
- [ ] Запуск скрипта создания индексов
- [ ] Проверка health endpoint
- [ ] Проверка логов
- [ ] Проверка endpoints с user_id

---

**Статус**: 🟡 В процессе  
**Текущий шаг**: Push в репозиторий



