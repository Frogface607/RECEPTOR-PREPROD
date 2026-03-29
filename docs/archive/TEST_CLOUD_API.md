# 🧪 Тестирование iikoCloud API интеграции

## Быстрый старт

### 1. Через Python скрипт (рекомендуется)

```bash
# Установите зависимости
pip install requests

# Запустите тест
python test_cloud_api.py

# Или с кастомными параметрами
BACKEND_URL=https://receptor-preprod-production.up.railway.app \
TEST_USER_ID=default_user \
python test_cloud_api.py
```

### 2. Через curl (для быстрой проверки)

```bash
# Сделайте скрипт исполняемым
chmod +x test_cloud_api_curl.sh

# Запустите
./test_cloud_api_curl.sh

# Или с кастомными параметрами
BACKEND_URL=https://receptor-preprod-production.up.railway.app \
TEST_USER_ID=default_user \
./test_cloud_api_curl.sh
```

### 3. Через Postman/Insomnia

Импортируйте следующие запросы:

#### Статус подключения
```
GET {{BACKEND_URL}}/api/iiko/cloud/status/{{USER_ID}}
```

#### Номенклатура
```
GET {{BACKEND_URL}}/api/iiko/cloud/menu/{{USER_ID}}
```

#### Отчёт по продажам
```
GET {{BACKEND_URL}}/api/iiko/cloud/reports/sales/{{USER_ID}}?date_from=2025-01-01&date_to=2025-01-08&group_by=DAY
```

#### Отчёт по остаткам
```
GET {{BACKEND_URL}}/api/iiko/cloud/reports/stock/{{USER_ID}}?date=2025-01-08
```

#### Отчёт по закупкам
```
GET {{BACKEND_URL}}/api/iiko/cloud/reports/purchases/{{USER_ID}}?date_from=2025-01-01&date_to=2025-01-08
```

#### Заказы
```
GET {{BACKEND_URL}}/api/iiko/cloud/orders/{{USER_ID}}?date_from=2025-01-01&date_to=2025-01-08
```

#### Сотрудники
```
GET {{BACKEND_URL}}/api/iiko/cloud/employees/{{USER_ID}}
```

#### Явки сотрудника
```
GET {{BACKEND_URL}}/api/iiko/cloud/employees/{{USER_ID}}/attendances/{{EMPLOYEE_ID}}?date_from=2025-01-01&date_to=2025-01-08
```

### 4. Через чат (интеграция с AI)

Откройте чат и попробуйте следующие запросы:

- **"Покажи отчёт по продажам за неделю"**
- **"Какие продукты есть в iiko?"**
- **"Покажи сотрудников"**
- **"Получи заказы за сегодня"**
- **"Покажи остатки на складе"**
- **"Отчёт по закупкам за месяц"**
- **"Покажи явки сотрудника [имя] за декабрь"**

## Проверка логов

### Локально
```bash
# Запустите сервер с подробными логами
uvicorn app.main:app --reload --log-level debug
```

### На Railway
```bash
# Просмотр логов через Railway CLI
railway logs

# Или через веб-интерфейс Railway
# Перейдите в раздел "Logs" вашего сервиса
```

## Ожидаемые результаты

### ✅ Успешные ответы

1. **Статус подключения**: `{"status": "connected", "organization_name": "...", ...}`
2. **Номенклатура**: `{"products_count": >0, "groups_count": >0, ...}`
3. **Отчёты**: Данные в формате JSON с метриками (выручка, чеки, и т.д.)
4. **Заказы**: Список заказов с деталями
5. **Сотрудники**: Список сотрудников с их данными

### ❌ Возможные ошибки

1. **Cloud API не подключен**: 
   - Ошибка: `{"status": "not_connected"}`
   - Решение: Подключите Cloud API через `/api/iiko/cloud/connect`

2. **Организация не выбрана**:
   - Ошибка: `{"detail": "Организация не выбрана"}`
   - Решение: Выберите организацию через `/api/iiko/cloud/select-organization`

3. **API ключ недействителен**:
   - Ошибка: `401 Unauthorized` или `403 Forbidden`
   - Решение: Проверьте API ключ в настройках iikoWeb

4. **Номенклатура пуста (0 продуктов)**:
   - Это нормально для Cloud API, если номенклатура не настроена
   - Используйте RMS Server для синхронизации номенклатуры

5. **Endpoint не найден (404)**:
   - Проверьте, что сервер запущен и URL правильный
   - Проверьте, что endpoint существует в документации

## Отладка

### Проверка подключения к базе данных
```bash
# Проверьте, что MongoDB доступна
curl http://localhost:8000/
```

### Проверка структуры ответа
```python
import requests
import json

response = requests.get("http://localhost:8000/api/iiko/cloud/status/default_user")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

### Проверка прямого HTTP запроса к iikoCloud API
```python
from app.services.iiko.iiko_client import IikoClient

client = IikoClient(api_login="YOUR_API_KEY")
# Тест получения токена
token_info = client.get_access_token()
print(f"Token: {token_info}")

# Тест получения организаций
orgs = client.list_organizations()
print(f"Organizations: {orgs}")

# Тест получения номенклатуры
nomenclature = client.fetch_nomenclature_direct_http("ORG_ID")
print(f"Products: {len(nomenclature.get('products', []))}")
```

## Чеклист тестирования

- [ ] Cloud API подключен и статус = "connected"
- [ ] Организация выбрана
- [ ] Номенклатура получается (может быть 0, это нормально)
- [ ] Отчёт по продажам работает
- [ ] Отчёт по остаткам работает
- [ ] Отчёт по закупкам работает
- [ ] Заказы получаются
- [ ] Сотрудники получаются
- [ ] Явки сотрудников получаются
- [ ] Чат может работать с iiko данными
- [ ] Логи не показывают ошибок

## Полезные ссылки

- [Документация iikoCloud API](backend/data/knowledge_base/iiko_api_full_documentation.md)
- [Быстрая справка](backend/data/knowledge_base/iiko_api_quick_reference.md)
- [Практические примеры](backend/data/knowledge_base/iiko_api_practical_examples.md)

