# iiko Server API Reference

> Справочник по iiko Server API для интеграции с RECEPTOR CO-PILOT.
> Источник: Официальная документация iiko (https://ru.iiko.help/articles/#!api-documentations/iikoserver-api)

---

## 0. Принципы работы API

### Форматы данных
1. **Отдельные сущности** — XML-документ
2. **Списки сущностей** — XML-документ, корневой элемент содержит XML-элементы сущностей
3. **JSON** — используется для OLAP-отчётов и некоторых v2 endpoints

### HTTP методы

| Метод | Content-Type | Описание |
|-------|--------------|----------|
| **POST** | `application/x-www-form-urlencoded` | Создание/изменение через параметры запроса. Можно передать только изменяемые поля. |
| **PUT** | `application/xml` | Создание/изменение через тело запроса. Отсутствующие поля = значение по умолчанию (создание) или сохранят значения (обновление). |
| **GET** | — | Получение данных |

### HTTP статусы ответов
| Статус | Описание |
|--------|----------|
| `200 OK` | Успешное обновление сущности |
| `201 Created` | Успешное создание сущности |
| `400 Bad Request` | Ошибка в запросе |
| `401 Unauthorized` | Не авторизован / истёк токен |
| `403 Forbidden` | Нет прав доступа |
| `404 Not Found` | Сущность не найдена |
| `500 Internal Server Error` | Ошибка сервера |

---

## 1. Авторизация

> ⚠️ **Важно:** При авторизации вы занимаете один слот лицензии! Токен можно использовать пока он работает. Если у вас только одна лицензия и вы уже получили токен — следующий запрос на авторизацию вызовет ошибку. Рекомендуется разлогиниться после работы.

### Получение токена доступа
```
POST https://host:port/resto/api/auth?login=[login]&pass=[sha1passwordhash]
```

**Параметры:**
| Параметр | Описание |
|----------|----------|
| `login` | Логин пользователя |
| `pass` | **SHA1 hash от пароля** |

**Как получить SHA1 hash пароля (bash):**
```bash
printf "resto#test" | sha1sum
# Результат: 2155245b2c002a1986d3f384af93be813537a476
```

**Пример запроса:**
```
POST https://localhost:8080/resto/api/auth?login=admin&pass=2155245b2c002a1986d3f384af93be813537a476
```

**Ответ:** Строка-токен, который нужно передавать:
- Как cookie с именем `key`
- Или как параметр `key` всех запросов

> 💡 Начиная с версии 4.3 сервер сам устанавливает cookie `key`.

### Выход (освобождение лицензии)
```
POST https://host:port/resto/api/logout?key=[token]
```

**Пример:**
```
https://localhost:8080/resto/api/logout?key=b354d18c-3d3a-e1a6-c3b9-9ef7b5055318
```
или с cookie:
```
https://localhost:8080/resto/api/logout (с cookie key=c0508074-a052-6276-bf72-871f7acb865e)
```

---

## 2. Справочники (Entities)

### Получение справочной информации
```
GET https://host:port/resto/api/v2/entities/list
```

**Параметры:**
| Параметр | Значения | Описание |
|----------|----------|----------|
| `rootType` | См. таблицу ниже | Тип справочника |
| `includeDeleted` | true/false | Включать удалённые (по умолчанию true) |
| `revisionFrom` | число | Фильтр по ревизии |

**Доступные типы справочников (rootType):**

| Код | Версия iiko | Описание |
|-----|-------------|----------|
| `Account` | 5.0 | Счета (в том числе склады) |
| `AccountingCategory` | 5.0 | Бухгалтерская категория номенклатуры |
| `AlcoholClass` | 5.0 | Класс алкогольной продукции |
| `AllergenGroup` | 7.1.2 | Группа аллергенов |
| `AttendanceType` | 6.4 | Тип явки сотрудника |
| `Conception` | 7.8.1 | Концепция |
| `CookingPlaceType` | 7.0.2 | Тип места приготовления |
| `DiscountType` | 5.0 | Тип скидки |
| `MeasureUnit` | 5.0 | Единица измерения |
| `OrderType` | 6.4 | Тип заказа |
| `PaymentType` | 5.0 | Тип оплаты |
| `ProductCategory` | 5.0 | Пользовательская категория номенклатуры |
| `ProductScale` | 6.4 | Шкала размеров |
| `ProductSize` | 6.4 | Размер продукта |
| `ScheduleType` | 6.4 | Тип смены |
| `TaxCategory` | 6.2.2 | Налоговая категория |

**Формат ответа:**
```json
{
    "id": "UUID объекта",
    "rootType": "тип справочника",
    "deleted": false,
    "code": "артикул/код",
    "name": "Название"
}
```

### Получение ID сущностей
```
GET https://host:port/resto/api/v2/entities/{entityType}/ids
```

---

## 3. OLAP-отчёты

### Типы отчётов
| Тип | Описание |
|-----|----------|
| `SALES` | По продажам |
| `TRANSACTIONS` | По проводкам/транзакциям |
| `DELIVERIES` | По доставкам |

### Получение полей отчёта
```
GET https://host:port/resto/api/v2/reports/olap/columns?reportType=SALES
```

**Структура поля:**
```json
{
    "FieldName": {
        "name": "Название в iikoOffice",
        "type": "MONEY|INTEGER|STRING|DATETIME|PERCENT|AMOUNT",
        "aggregationAllowed": true,
        "groupingAllowed": true,
        "filteringAllowed": true,
        "tags": ["Оплата", "Доставка"]
    }
}
```

### Построение OLAP-отчёта
```
POST https://host:port/resto/api/reports/olap
Content-Type: application/json
```

**Тело запроса:**
```json
{
    "reportType": "SALES",
    "buildSummary": true,
    "groupByRowFields": ["DishName", "DishGroup"],
    "groupByColFields": [],
    "aggregateFields": ["DishAmountInt", "DishSumInt"],
    "filters": {
        "OpenDate.Typed": {
            "filterType": "DateRange",
            "periodType": "CUSTOM",
            "from": "2024-01-01T00:00:00.000",
            "to": "2024-01-31T23:59:59.000",
            "includeLow": true,
            "includeHigh": true
        }
    }
}
```

**Типы периодов (periodType):**
| Код | Описание |
|-----|----------|
| `CUSTOM` | Вручную (from/to) |
| `OPEN_PERIOD` | Текущий открытый период |
| `TODAY` | Сегодня |
| `YESTERDAY` | Вчера |
| `CURRENT_WEEK` | Текущая неделя |
| `CURRENT_MONTH` | Текущий месяц |
| `CURRENT_YEAR` | Текущий год |
| `LAST_WEEK` | Прошлая неделя |
| `LAST_MONTH` | Прошлый месяц |
| `LAST_YEAR` | Прошлый год |

**Ответ:**
```json
{
    "data": [
        {
            "DishName": "Борщ",
            "DishGroup": "Супы",
            "DishAmountInt": 150,
            "DishSumInt": 45000
        }
    ],
    "summary": [...]
}
```

---

## 4. Коды базовых типов

### Типы документов
| Код | Название | Сокращение |
|-----|----------|------------|
| `INCOMING_INVOICE` | Приходная накладная | п/н |
| `INCOMING_INVENTORY` | Инвентаризация | инв |
| `WRITEOFF_DOCUMENT` | Акт списания | а/с |
| `SALES_DOCUMENT` | Акт реализации | а/р |
| `INTERNAL_TRANSFER` | Внутреннее перемещение | в/п |
| `OUTGOING_INVOICE` | Расходная накладная | р/н |
| `RETURNED_INVOICE` | Возвратная накладная | в/н |
| `PRODUCTION_DOCUMENT` | Акт приготовления | а/пр |
| `TRANSFORMATION_DOCUMENT` | Акт переработки | а/пб |
| `PRODUCTION_ORDER` | Заказ в производство | з/п |
| `MENU_CHANGE` | Приказ об изменении прейскуранта | п/и |
| `INCOMING_CASH_ORDER` | Приходный кассовый ордер | п/ко |
| `OUTGOING_CASH_ORDER` | Расходный кассовый ордер | р/ко |

### Типы транзакций
| Код | Название |
|-----|----------|
| `OPENING_BALANCE` | Начальный баланс |
| `CASH` | Продажа за наличные |
| `CARD` | Выручка по картам |
| `CREDIT` | Выручка в кредит |
| `PREPAY` | Предоплата |
| `PREPAY_RETURN` | Возврат предоплаты |
| `DISCOUNT` | Скидка |
| `PAYIN` | Внесенная сумма |
| `PAYOUT` | Изъятая сумма |
| `PAY_COLLECTION` | Снятая выручка |
| `INVENTORY_CORRECTION` | Инвентаризация |
| `WRITEOFF` | Списание |
| `SESSION_WRITEOFF` | Реализация товаров |
| `TRANSFER` | Внутреннее перемещение |
| `PRODUCTION` | Акт приготовления |

### Типы элементов номенклатуры
| Код | Название |
|-----|----------|
| `GOODS` | Товар (сырьё) |
| `DISH` | Блюдо |
| `PREPARED` | Заготовка (полуфабрикат) |
| `SERVICE` | Услуга |
| `MODIFIER` | Модификатор |
| `OUTER` | Внешние товары |
| `RATE` | Тариф |

### Типы контрагентов
| Код | Название |
|-----|----------|
| `NONE` | Нет |
| `COUNTERAGENT` | Все |
| `EMPLOYEE` | Сотрудник |
| `SUPPLIER` | Поставщик |
| `CLIENT` | Гость |
| `INTERNAL_SUPPLIER` | Внутренний поставщик |

### Группы счетов
| Код | Название |
|-----|----------|
| `ASSETS` | Активы |
| `LIABILITIES` | Обязательства |
| `EQUITY` | Капитал |
| `INCOME_EXPENSES` | Доходы/Расходы |

### Типы счетов
| Код | Название |
|-----|----------|
| `CASH` | Денежные средства |
| `ACCOUNTS_RECEIVABLE` | Задолженность покупателей |
| `DEBTS_OF_EMPLOYEES` | Задолженность сотрудников |
| `INVENTORY_ASSETS` | Складские запасы |
| `EMPLOYEES_LIABILITY` | Расчеты с сотрудниками |
| `ACCOUNTS_PAYABLE` | Расчеты с поставщиками |
| `CLIENTS_LIABILITY` | Расчеты с гостями |
| `COST_OF_GOODS_SOLD` | Прямые издержки (себестоимость) |
| `INCOME` | Доходы |
| `EXPENSES` | Расходы |

### Группы оплаты
| Код | Название |
|-----|----------|
| `CASH` | Оплата наличными |
| `CARD` | Банковские карты |
| `WRITEOFF` | Без выручки |
| `NON_CASH` | Безналичный расчет |

### Типы подразделений
| Код | Название |
|-----|----------|
| `CORPORATION` | Корпорация |
| `JURPERSON` | Юридическое лицо |
| `ORGDEVELOPMENT` | Структурное подразделение |
| `DEPARTMENT` | Торговое предприятие |
| `MANUFACTURE` | Производство |
| `CENTRALSTORE` | Центральный склад |
| `CENTRALOFFICE` | Центральный офис |
| `SALEPOINT` | Точка продаж |
| `STORE` | Склад |

---

## 5. Типы данных полей

| Тип | Описание |
|-----|----------|
| `ENUM` | Перечислимые значения |
| `STRING` | Строка |
| `ID` | Внутренний идентификатор UUID |
| `DATETIME` | Дата и время |
| `INTEGER` | Целое число |
| `PERCENT` | Процент (от 0 до 1) |
| `DURATION_IN_SECONDS` | Длительность в секундах |
| `AMOUNT` | Количество |
| `MONEY` | Денежная сумма |

---

## 6. Примеры использования

### Пример: Получить все типы скидок и оплат
```
GET /resto/api/v2/entities/list?rootType=DiscountType&rootType=PaymentType&includeDeleted=false
```

### Пример: OLAP отчёт по продажам за месяц
```json
{
    "reportType": "SALES",
    "groupByRowFields": ["DishName", "DishGroup"],
    "aggregateFields": ["DishAmountInt", "DishSumInt", "ProductCostBase.ProductCost"],
    "filters": {
        "OpenDate.Typed": {
            "filterType": "DateRange",
            "periodType": "LAST_MONTH",
            "from": "2024-01-01"
        }
    }
}
```

### Пример: Выручка по дням
```json
{
    "reportType": "SALES",
    "groupByRowFields": ["OpenDate.Typed"],
    "aggregateFields": ["DishSumInt", "DiscountSum"],
    "filters": {
        "OpenDate.Typed": {
            "filterType": "DateRange",
            "periodType": "CURRENT_MONTH",
            "from": "2024-01-01"
        }
    }
}
```

---

## 7. Важные замечания

1. **Обязательный фильтр по дате** — начиная с версии iiko 5.5, каждый OLAP-запрос должен содержать фильтр по дате.

2. **Поля для фильтрации по дате:**
   - OLAP по продажам/доставкам: `OpenDate.Typed`
   - OLAP по проводкам: `DateTime.DateTyped` или `DateTime.Typed`

3. **Формат даты:** `yyyy-MM-dd'T'HH:mm:ss.SSS`

4. **buildSummary:** С версии 9.1.2 по умолчанию `false`. Для получения итогов передавайте `"buildSummary": true`.

---

## 8. Технологические карты (ТТК)

> Технологические карты (рецепты) в iiko строго привязаны к элементам номенклатуры (блюдам, модификаторам, заготовкам) и датам. На каждый учетный день элементу номенклатуры может быть сопоставлено не более одной технологической карты.

### Получение всех ТТК
```
GET https://host:port/resto/api/v2/assemblyCharts/getAll?dateFrom={dateFrom}&dateTo={dateTo}
```

**Параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `dateFrom` | yyyy-MM-dd | Начальная дата (обязательный) |
| `dateTo` | yyyy-MM-dd | Конечная дата (если не задан — все будущие) |
| `includeDeletedProducts` | Boolean | Включать удалённые блюда (по умолчанию true) |
| `includePreparedCharts` | Boolean | Разложить до конечных ингредиентов (по умолчанию false) |

**Пример:**
```
GET /resto/api/v2/assemblyCharts/getAll?dateFrom=2024-01-01&dateTo=2024-12-31
```

**Ответ (ChartResultDto):**
```json
{
    "knownRevision": 12345,
    "assemblyCharts": [...],
    "preparedCharts": [...],
    "deletedAssemblyChartIds": null,
    "deletedPreparedChartIds": null
}
```

### Получение обновлений ТТК
```
GET https://host:port/resto/api/v2/assemblyCharts/getAllUpdate?knownRevision={rev}&dateFrom={dateFrom}
```

Используйте `knownRevision` из предыдущего ответа для получения только изменений.

### Создание/обновление ТТК
```
POST https://host:port/resto/api/v2/assemblyCharts/save
Content-Type: application/json
```

**Тело запроса (AssemblyChartDto):**
```json
{
    "assembledProductId": "UUID блюда",
    "dateFrom": "2024-01-01",
    "dateTo": null,
    "assembledAmount": 2,
    "productWriteoffStrategy": "ASSEMBLE",
    "effectiveDirectWriteoffStoreSpecification": {
        "departments": [],
        "inverse": false
    },
    "productSizeAssemblyStrategy": "COMMON",
    "items": [
        {
            "sortWeight": 0,
            "productId": "UUID ингредиента",
            "amountIn": 0.4,
            "amountMiddle": 0.36,
            "amountOut": 0.36,
            "packageTypeId": null
        }
    ],
    "technologyDescription": "Технология приготовления",
    "description": "Описание",
    "appearance": "Требования к оформлению",
    "organoleptic": "Органолептические показатели",
    "outputComment": "Суммарный выход"
}
```

**Поля ингредиента (items):**
| Поле | Тип | Описание |
|------|-----|----------|
| `productId` | UUID | ID ингредиента |
| `amountIn` | BigDecimal | Количество брутто |
| `amountMiddle` | BigDecimal | Количество после холодной обработки |
| `amountOut` | BigDecimal | Количество нетто (выход) |
| `amountIn1-3` / `amountOut1-3` | BigDecimal | Акт проработки (3 измерения) |
| `packageTypeId` | UUID | UUID фасовки |

**Стратегии списания (productWriteoffStrategy):**
| Код | Описание |
|-----|----------|
| `ASSEMBLE` | Списывать по ингредиентам |
| `WRITEOFF` | Списывать готовое блюдо |

**Ответ:**
```json
{
    "result": "SUCCESS",
    "errors": null,
    "response": {
        "id": "UUID созданной ТТК",
        ...
    }
}
```

### Удаление ТТК
```
POST https://host:port/resto/api/v2/assemblyCharts/delete
Content-Type: application/json
```

**Тело:**
```json
{
    "id": "UUID технологической карты"
}
```

**Ответ:**
```json
{
    "result": "SUCCESS",
    "errors": null,
    "response": "UUID удалённой ТТК"
}
```

### StoreSpecification (подразделения)

Структура для указания подмножества подразделений:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `departments` | List<UUID> | Список ID подразделений |
| `inverse` | Boolean | false = только указанные; true = все КРОМЕ указанных |

**Примеры:**
```json
// Только в двух подразделениях
{"departments": ["uuid1", "uuid2"], "inverse": false}

// Во всех, кроме одного
{"departments": ["uuid1"], "inverse": true}

// Для всех подразделений
{"departments": [], "inverse": true}
```

---

## 9. Номенклатурные группы

### Получение списка групп
```
GET https://host:port/resto/api/v2/entities/products/group/list
```

**Параметры:**
| Параметр | Версия | Тип | Описание |
|----------|--------|-----|----------|
| `includeDeleted` | 6.2 | Boolean | Включать удалённые (по умолчанию false) |
| `ids` | 6.2 | List<UUID> | Фильтр по ID |
| `parentIds` | 6.2 | List<UUID> | Фильтр по родительской группе |
| `nums` | 6.2.3 | List<String> | Фильтр по артикулу |
| `codes` | 6.2.3 | List<String> | Фильтр по коду |
| `revisionFrom` | 6.4 | Integer | Фильтр по ревизии |

**Ответ (ProductGroupDto):**
```json
{
    "id": "UUID группы",
    "deleted": false,
    "name": "Название группы",
    "description": "Описание",
    "num": "00093",
    "code": "98",
    "parent": "UUID родительской группы или null",
    "modifiers": [],
    "taxCategory": "UUID налоговой категории",
    "category": "UUID пользовательской категории",
    "accountingCategory": "UUID бухгалтерской категории",
    "color": {"red": 119, "green": 119, "blue": 119},
    "fontColor": {"red": 0, "green": 0, "blue": 0},
    "frontImageId": "UUID изображения",
    "position": null,
    "visibilityFilter": {
        "departments": ["UUID подразделения"],
        "excluding": false
    }
}
```

### POST-версия (с телом запроса)
```
POST https://host:port/resto/api/v2/entities/products/group/list
Content-Type: application/json
```

**Тело:**
```json
{
    "includeDeleted": false,
    "revisionFrom": -1,
    "ids": ["uuid1", "uuid2"],
    "parentIds": ["parent-uuid"]
}
```

### Удаление группы
```
POST https://host:port/resto/api/v2/entities/products/group/delete
```

> ⚠️ Нельзя удалить группу, если в ней есть дочерние группы или продукты!

### Восстановление группы
```
POST https://host:port/resto/api/v2/entities/products/group/restore
```

---

## 10. API EDI (Электронный документооборот)

> EDI API для работы с заказами поставщикам через электронный документооборот.

### Список заказов EDI
```
GET https://host:port/resto/api/edi/{ediSystem}/orders/list?from={dateFrom}&to={dateTo}
```

**Параметры:**
| Параметр | Описание |
|----------|----------|
| `ediSystem` | GUID участника EDI (из iikoOffice → Обмен данными → Системы EDI) |
| `from` | Начальная дата (yyyy-MM-dd) |
| `to` | Конечная дата (yyyy-MM-dd) |
| `revisionFrom` | (с 6.4) Фильтр по ревизии |

**Ответ (XML):**
```xml
<orderDtoes>
    <order number="10004" date="2016-08-15" status="original" processingStatus="readyToSend">
        <seller>
            <gln>1111111111111</gln>
            <name>Поставщик02</name>
            <inn>2222222222222</inn>
        </seller>
        <buyer>
            <gln>2000000002460</gln>
            <guid>77ee6049-abb2-4459-a9b1-aaf413c9125e</guid>
            <name>Кухня1</name>
        </buyer>
        <lineItems>
            <lineItem>
                <lineNumber>1</lineNumber>
                <internalBuyerCode>0001</internalBuyerCode>
                <name>Апельсин</name>
                <requestedQuantity>
                    <measureUnit>KG</measureUnit>
                    <quantity>2.500000000</quantity>
                </requestedQuantity>
                <priceWithoutVat>55.08</priceWithoutVat>
                <sumWithVat>137.700000000</sumWithVat>
            </lineItem>
        </lineItems>
        <totalSumWithVat>24837.655000000</totalSumWithVat>
    </order>
</orderDtoes>
```

### Постановка заказа на отправку
```
PUT https://host:port/resto/api/edi/{ediSystem}/orders/send
```

**Тело запроса (XML):**
```xml
<documentIdentifierDtoes>
    <documentIdentifier number="10025" date="2016-08-24" />
</documentIdentifierDtoes>
```

### Распроведение заказа
```
PUT https://host:port/resto/api/edi/{ediSystem}/orders/unregister
```

Устанавливает статус "не проведен" для указанных заказов.

---

## 11. Пользовательские категории

> Пользовательские категории — это кастомные категории для классификации продуктов (например, "Завтраки", "Веганское", "Сезонное").

### Получение списка категорий
```
GET https://host:port/resto/api/v2/entities/products/category/list
```

**Параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `includeDeleted` | Boolean | Включать удалённые (по умолчанию false) |
| `ids` | List<UUID> | Фильтр по ID |
| `revisionFrom` | Integer | Фильтр по ревизии |

**Ответ:**
```json
[{
    "id": "7e29cd73-05da-7ac4-0165-0f11a132002b",
    "rootType": "ProductCategory",
    "deleted": false,
    "code": null,
    "name": "Категория 1"
}]
```

### Создание категории
```
POST https://host:port/resto/api/v2/entities/products/category/save
Content-Type: application/json
```

**Тело:**
```json
{
    "name": "Категория 1"
}
```

**Ответ:**
```json
{
    "result": "SUCCESS",
    "errors": null,
    "response": {
        "id": "7e29cd73-05da-7ac4-0165-0f11a132002b",
        "rootType": "ProductCategory",
        "deleted": false,
        "code": null,
        "name": "Категория 1"
    }
}
```

### Редактирование категории
```
POST https://host:port/resto/api/v2/entities/products/category/update
Content-Type: application/json
```

**Тело:**
```json
{
    "id": "70936cd4-474d-4b5f-b9bc-ac2799bfc137",
    "name": "Категория 2"
}
```

### Удаление категории
```
POST https://host:port/resto/api/v2/entities/products/category/delete
Content-Type: application/json
```

**Тело:**
```json
{
    "id": "70936cd4-474d-4b5f-b9bc-ac2799bfc137"
}
```

> ⚠️ Нельзя удалить уже удалённую категорию!

### Восстановление категории
```
POST https://host:port/resto/api/v2/entities/products/category/restore
Content-Type: application/json
```

**Тело:**
```json
{
    "id": "70936cd4-474d-4b5f-b9bc-ac2799bfc137"
}
```

> ⚠️ Нельзя восстановить НЕ удалённую категорию!

---

*Документация актуальна на декабрь 2025. Источник: https://ru.iiko.help/articles/#!api-documentations/iikoserver-api*

