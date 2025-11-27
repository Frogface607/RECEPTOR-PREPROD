# ✅ Чеклист тестирования YooKassa

## 🔍 Перед тестированием - проверьте:

- [ ] Environment Variables добавлены в Railway:
  - `YOOKASSA_SHOP_ID=1163540`
  - `YOOKASSA_SECRET_KEY=test_HmKz8QaGiGvTChyLIX9S32SAahBKChcNt6qTHdqxbNM`
  - `YOOKASSA_RETURN_URL=https://receptor-preprod-production.up.railway.app/pricing?status=success`
- [ ] Railway сервис перезапущен после добавления переменных
- [ ] Webhook настроен в YooKassa (тестовый режим):
  - URL: `https://receptor-preprod-production.up.railway.app/api/yookassa/webhook`
  - События: `payment.succeeded` и `payment.canceled`
- [ ] Вы в тестовом режиме в личном кабинете YooKassa

## 🧪 Шаги тестирования:

### 1. Проверка доступности endpoints:

Откройте в браузере:
```
https://receptor-preprod-production.up.railway.app/api/yookassa/plans
```

Должен вернуться JSON с тарифами:
```json
{
  "plans": [
    {
      "id": "pro_monthly_ru",
      "name": "PRO Ежемесячно",
      "amount": "1990.00",
      "currency": "RUB",
      ...
    },
    {
      "id": "pro_annual_ru",
      "name": "PRO Ежегодно",
      "amount": "19900.00",
      ...
    }
  ],
  "currency": "RUB",
  "market": "RU"
}
```

### 2. Тестирование полного flow:

1. **Откройте приложение:**
   - Войдите в личный кабинет (или зарегистрируйтесь)
   - Нажмите на имя пользователя вверху → "Личный кабинет"

2. **Откройте страницу тарифов:**
   - В разделе "💳 Подписка и аккаунт"
   - Нажмите кнопку "💎 Улучшить план"

3. **Выберите тариф:**
   - PRO Ежемесячно (1990₽) или PRO Ежегодно (19900₽)
   - Нажмите "Upgrade to PRO"

4. **Совершите тестовый платеж:**
   - Вас перенаправит на страницу оплаты YooKassa
   - Используйте тестовую карту: `5555 5555 5555 4444`
   - Срок действия: любой (например, `12/25`)
   - CVV: любой (например, `123`)
   - Нажмите "Оплатить"

5. **Проверьте результат:**
   - ✅ Должно перенаправить обратно на страницу с `?status=success`
   - ✅ Должно появиться сообщение "🎉 Оплата прошла успешно! PRO активируется..."
   - ✅ Через несколько секунд должно появиться "✅ PRO подписка активирована!"
   - ✅ В личном кабинете должен отображаться статус "PRO"

### 3. Проверка логов:

В Railway → Deployments → View Logs проверьте:
- `✅ YooKassa configured successfully`
- `🔵 Google OAuth callback received` (если использовали Google авторизацию)
- `✅ Subscription activated for user ...`

### 4. Проверка в базе данных (опционально):

Если есть доступ к MongoDB, проверьте:
- В коллекции `users` - поле `subscription_plan` должно быть `"pro"`
- В коллекции `payments` - должна быть запись о платеже со статусом `"succeeded"`

## 🐛 Возможные проблемы:

### Проблема: "YooKassa SDK not available"
**Решение:** Проверьте, что библиотека установлена:
```bash
pip install yookassa==3.0.0
```

### Проблема: "YooKassa not configured"
**Решение:** Проверьте Environment Variables в Railway

### Проблема: Webhook не срабатывает
**Решение:** 
- Проверьте, что webhook URL правильный
- Проверьте логи в Railway на наличие ошибок
- Используйте fallback метод `/api/yookassa/confirm?payment_id=...`

### Проблема: Платеж прошел, но PRO не активировался
**Решение:**
- Проверьте логи webhook в Railway
- Проверьте, что webhook настроен правильно
- Попробуйте использовать fallback: откройте в браузере:
  ```
  https://receptor-preprod-production.up.railway.app/api/yookassa/confirm?payment_id=ID_ПЛАТЕЖА
  ```

## ✅ Успешное тестирование:

Если все работает:
- ✅ Платеж проходит успешно
- ✅ PRO подписка активируется автоматически
- ✅ Пользователь видит статус "PRO" в личном кабинете
- ✅ В логах нет ошибок

**Готово к продакшену!** 🚀


