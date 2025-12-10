# IIKO API - БЫСТРАЯ СПРАВКА И ЧЕКЛИСТ

## БЫСТРЫЙ СТАРТ

### Шаг 1: Получение API-ключа (5 минут)

```
1. Откройте iikoOffice
2. Обмен данными → Настройка iikoTransport
3. API интеграции → Добавить
4. Введите имя (например: "Receptor")
5. Скопируйте сгенерированный API-ключ
6. Установите галочку "Активный"
```

### Шаг 2: Выбор нужного API

| Задача | API | Документация |
|--------|-----|--------------|
| Плагин для кассы | iikoFront API V8/V9 | https://iiko.github.io/front.api.doc/ |
| Получение данных | iikoCloud API | В аккаунте iiko |
| Бонусные карты | iikoCard API | Отдельный документ |
| Интеграция с доставкой | iikoDelivery API | help.iiko.ru |

### Шаг 3: Первый запрос

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://api.iiko.ru/api/v1/organizations"
```

---

## ОСНОВНЫЕ ENDPOINT'Ы

### Сотрудники
```
GET  /api/v1/employees                          # Получить список
GET  /api/v1/employees/{id}                     # Один сотрудник
POST /api/v1/employees                          # Создать
PUT  /api/v1/employees/{id}                     # Обновить
```

### Явки
```
GET /api/v1/employees/{id}/attendances         # История явок
GET /api/v1/employees/{id}/attendances?dateFrom=2025-12-01&dateTo=2025-12-31
POST /api/v1/employees/{id}/attendances        # Добавить явку
```

### Меню и номенклатура
```
GET /api/v1/menu                                # Всё меню
GET /api/v1/menu?includeArchived=false          # Активное
GET /api/v1/dishes/{id}                         # Информация о блюде
GET /api/v1/stock                               # Остатки на складе
```

### Отчеты
```
GET /api/v1/reports/sales                       # По продажам
GET /api/v1/stock/report                        # По остаткам
GET /api/v1/reports/purchases                   # По закупкам
```

### Заказы
```
GET /api/v1/orders                              # Список заказов
GET /api/v1/orders?dateFrom=2025-12-01&dateTo=2025-12-31
GET /api/v1/orders/{id}                         # Один заказ
```

---

## ПАРАМЕТРЫ ЗАПРОСОВ

### Обязательные параметры для всех запросов
```
Headers:
  Authorization: Bearer {API_KEY}
  Content-Type: application/json
```

### Часто используемые параметры
```
organizationId    - ID организации/ресторана
dateFrom         - Начало периода (YYYY-MM-DD)
dateTo           - Конец периода (YYYY-MM-DD)
includeArchived  - Включить архивные элементы (true/false)
limit            - Количество записей
offset           - Смещение (для пагинации)
groupBy          - Группировка (HOUR, DAY, WEEK, MONTH)
```

---

## ПРИМЕРЫ РЕАЛЬНЫХ ЗАПРОСОВ

### 1. Получить всех сотрудников
```bash
curl -X GET "https://api.iiko.ru/api/v1/employees" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

### 2. Получить явки за декабрь 2025
```bash
curl -X GET "https://api.iiko.ru/api/v1/employees/employee_id_123/attendances?dateFrom=2025-12-01&dateTo=2025-12-31" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 3. Получить продажи за день
```bash
curl -X GET "https://api.iiko.ru/api/v1/reports/sales?organizationId=org_123&dateFrom=2025-12-10&dateTo=2025-12-10&groupBy=HOUR" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 4. Получить все блюда с ценами
```bash
curl -X GET "https://api.iiko.ru/api/v1/menu?organizationId=org_123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 5. Получить остатки на складе
```bash
curl -X GET "https://api.iiko.ru/api/v1/stock?organizationId=org_123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## РАБОТА С ТЕХКАРТАМИ

### Структура техкарты в API
```json
{
  "id": "tc_001",
  "dishId": "dish_001",
  "dishName": "Борщ",
  "startDate": "2025-12-01",
  "endDate": "2099-12-31",
  "ingredients": [
    {
      "id": "ing_001",
      "name": "Свёкла",
      "quantity": 150,
      "unit": "гр",
      "cost": 45.50
    },
    {
      "id": "ing_002",
      "name": "Говядина",
      "quantity": 200,
      "unit": "гр",
      "cost": 320.00
    }
  ],
  "totalCost": 365.50
}
```

### Получить техкарты блюда
```bash
curl -X GET "https://api.iiko.ru/api/v1/dishes/dish_001/technologicalCards" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Создать новую техкарту
```bash
curl -X POST "https://api.iiko.ru/api/v1/dishes/dish_001/technologicalCards" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "startDate": "2025-12-01",
    "endDate": "2099-12-31",
    "ingredients": [
      {
        "name": "Свёкла",
        "quantity": 150,
        "unit": "гр"
      }
    ]
  }'
```

---

## ОШИБКИ И КОД РЕШЕНИЙ

| Код | Ошибка | Решение |
|-----|--------|---------|
| 401 | Unauthorized | Проверьте API-ключ, истекла ли лицензия |
| 403 | Forbidden | У ключа нет доступа к этому ресурсу |
| 404 | Not Found | Неверный ID или endpoint не существует |
| 429 | Too Many Requests | Превышен лимит запросов (обычно 1000/мин) |
| 500 | Internal Server Error | Проблема на сервере, свяжитесь с api@iiko.ru |

### Типичные ошибки и их решения

**Ошибка: "organizationId not found"**
- Решение: Получите правильный ID организации через GET /organizations

**Ошибка: "Invalid date format"**
- Решение: Используйте формат YYYY-MM-DD (например: 2025-12-10)

**Ошибка: "API key expired"**
- Решение: Проверьте лицензию, создайте новый ключ в iikoOffice

---

## ПОЛЕЗНЫЕ ИНСТРУМЕНТЫ

### Для тестирования API
- **Postman** - графический клиент для тестирования API
- **Insomnia** - альтернатива Postman
- **curl** - командная строка

### Для мониторинга
- **DataDog** - мониторинг интеграций
- **New Relic** - APM и аналитика

### Для автоматизации
- **N8N** - no-code автоматизация (рекомендую!)
- **Zapier** - интеграция с облачными сервисами
- **IFTTT** - простые сценарии

### Для разработки
- **VS Code** - редактор кода
- **Python** - язык для скриптов
- **Node.js** - для JavaScript интеграций

---

## ЧЕКЛИСТ ПЕРЕД ЗАПУСКОМ В PRODUCTION

- [ ] API-ключ создан и активен
- [ ] Протестированы все основные endpoint'ы
- [ ] Реализована обработка ошибок (retry, exponential backoff)
- [ ] Логирование всех операций включено
- [ ] Настроены уведомления об ошибках (email, Telegram)
- [ ] Кэширование настроено для снижения нагрузки
- [ ] Защита API-ключа (не хранится в коде)
- [ ] Проведено тестирование на production данных
- [ ] Документация интеграции написана
- [ ] План rollback подготовлен
- [ ] Мониторинг настроен

---

## ОПТИМИЗАЦИЯ И BEST PRACTICES

### 1. Кэширование
```python
# Кэшируйте медленные запросы (например, меню)
cache_ttl = 3600  # 1 час
if cache_valid:
    return cached_data
```

### 2. Batch запросы
```python
# Вместо 100 запросов по 1 сотруднику
# Сделайте 1 запрос на всех сотрудников
GET /employees  # Лучше!
GET /employees/id_1, /employees/id_2... # Плохо
```

### 3. Pagination
```bash
# Для больших наборов данных
GET /reports/sales?limit=100&offset=0
GET /reports/sales?limit=100&offset=100
```

### 4. Retry логика
```python
max_retries = 3
backoff_factor = 2  # 2 сек, 4 сек, 8 сек
```

### 5. Rate limiting
```python
# Не более 1000 запросов в минуту
import time
time.sleep(0.1)  # 100ms между запросами
```

---

## КОНТАКТЫ И ПОДДЕРЖКА

**Email**: api@iiko.ru  
**Телефон**: +7 (812) 313-2000  
**Help Center**: help.iiko.ru  
**GitHub**: github.com/iiko  
**Status**: status.iiko.ru  

**Часы поддержки**: Пн-Пт, 9:00-18:00 (MSK)

---

## РЕСУРСЫ

- [Официальная документация](https://iiko.github.io/front.api.doc/)
- [GitHub SDK](https://github.com/iiko/front.api.sdk)
- [Примеры интеграций](https://help.iiko.ru)
- [Форум разработчиков](https://community.iiko.ru)

---

## АББРЕВИАТУРЫ

| Аббревиатура | Значение |
|--------------|----------|
| API | Application Programming Interface |
| SDK | Software Development Kit |
| REST | Representational State Transfer |
| JSON | JavaScript Object Notation |
| HTTP | HyperText Transfer Protocol |
| HTTPS | HTTP Secure |
| OAuth | Open Authorization |
| JWT | JSON Web Token |
| TTL | Time To Live (время кэширования) |
| RPS | Requests Per Second |
| SLA | Service Level Agreement |
| CSV | Comma-Separated Values |
| XML | eXtensible Markup Language |

---

## ВЕРСИОНИРОВАНИЕ

- **API v1** - текущая версия
- **iikoFront API V8** - стабильная версия для плагинов
- **iikoFront API V9** - preview версия (новые возможности)

Все примеры в этой справке актуальны для версии v1 iikoCloud API и V8 iikoFront API.

---

**Последнее обновление**: 10 декабря 2025  
**Автор**: IIKO Support Team  
**Лицензия**: Используется в соответствии с условиями лицензии IIKO

