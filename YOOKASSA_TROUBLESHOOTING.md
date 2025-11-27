# 🔧 Диагностика ошибки 500 при создании платежа YooKassa

## ❌ Ошибка:
```
POST /api/yookassa/checkout 500 (Internal Server Error)
```

## 🔍 Возможные причины и решения:

### 1. Переменные окружения не установлены в Railway

**Проверка:**
- Откройте Railway → Settings → Environment Variables
- Убедитесь, что установлены:
  ```
  YOOKASSA_SHOP_ID=1163540
  YOOKASSA_SECRET_KEY=test_HmKz8QaGiGvTChyLIX9S32SAahBKChcNt6qTHdqxbNM
  YOOKASSA_RETURN_URL=https://receptor-preprod-production.up.railway.app/pricing?status=success
  ```

**Решение:**
1. Добавьте переменные, если их нет
2. **ВАЖНО:** После добавления переменных **перезапустите сервис** в Railway:
   - Railway → Deployments → нажмите "Redeploy" или "Restart"

### 2. Библиотека yookassa не установлена

**Проверка:**
- Откройте Railway → Deployments → View Logs
- Ищите сообщение: `⚠️ YooKassa SDK not available`

**Решение:**
- Убедитесь, что в `backend/requirements.txt` есть строка: `yookassa==3.0.0`
- Railway должен автоматически установить зависимости при деплое

### 3. Ошибка при вызове YooKassa API

**Проверка:**
- Откройте Railway → Deployments → View Logs
- Ищите сообщения с `❌` или `Failed to create YooKassa payment`

**Возможные причины:**
- Неправильный Shop ID или Secret Key
- Проблемы с сетью при обращении к YooKassa API
- Неправильный формат данных платежа

**Решение:**
- Проверьте, что Shop ID и Secret Key правильные (тестовые ключи)
- Проверьте логи на детальную ошибку

### 4. Проблема с MongoDB

**Проверка:**
- Откройте Railway → Deployments → View Logs
- Ищите сообщения: `❌ User not found` или ошибки MongoDB

**Решение:**
- Убедитесь, что MongoDB подключен и доступен
- Проверьте переменную окружения `MONGODB_URI`

## 📋 Пошаговая диагностика:

### Шаг 1: Проверьте логи Railway

1. Откройте Railway → Deployments
2. Нажмите на последний деплой
3. Откройте "View Logs"
4. Ищите сообщения, начинающиеся с:
   - `🔵` - информационные сообщения
   - `✅` - успешные операции
   - `❌` - ошибки
   - `⚠️` - предупреждения

### Шаг 2: Проверьте переменные окружения

В логах при старте сервера должно быть:
```
✅ YooKassa configured successfully
```

Если видите:
```
⚠️ YooKassa not configured. Set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY
```

То переменные не установлены или сервис не перезапущен.

### Шаг 3: Проверьте детальные логи при создании платежа

При попытке создать платеж в логах должно быть:
```
🔵 Creating checkout for user {user_id}, package {package_id}
✅ YooKassa configured. Shop ID: 1163...
✅ Package found: PRO Ежемесячно, amount: 1990.0
✅ User found: {email}
✅ Creating payment with email: {email}
🔵 Payment data prepared, calling YooKassa API...
✅ Payment created: {payment_id}, status: pending
```

Если видите ошибку на каком-то шаге, это укажет на проблему.

## 🚀 Быстрое решение:

1. **Убедитесь, что переменные установлены в Railway**
2. **Перезапустите сервис** (Redeploy в Railway)
3. **Попробуйте снова создать платеж**
4. **Проверьте логи** на детальную ошибку

## 📞 Если проблема не решена:

Пришлите:
1. Логи из Railway (последние 50-100 строк)
2. Сообщение об ошибке из консоли браузера (F12)
3. Подтверждение, что переменные окружения установлены

---

**После исправления:** Попробуйте снова создать платеж и проверьте логи.

