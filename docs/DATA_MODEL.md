# Модель данных AI Menu Designer

## Обзор базы данных
- **Database**: MongoDB
- **Connection**: `mongodb://localhost:27017/receptor_pro`
- **Driver**: motor (async MongoDB driver для Python)

## Основные сущности

### 1. Users Collection

**Назначение**: Профили пользователей с данными подписки и настройками

```typescript
interface User {
  _id: ObjectId,                    // MongoDB ID
  id: string,                       // UUID для внешних ссылок
  name: string,                     // ФИО пользователя
  email: string,                    // Email для связи
  city: string,                     // Город для ценообразования
  created_at: string,               // ISO timestamp
  
  // Профиль заведения  
  venue_profile: {
    venue_type: string,             // Тип заведения (fine_dining, cafe, etc)
    cuisine_type: string,           // Кухня (european, asian, etc)  
    target_audience: string,        // Аудитория (families, business, etc)
    budget_level: string,           // Бюджет (budget, mid, premium)
    equipment?: string[],           // ID кухонного оборудования
    special_dietary_needs?: string[] // Диетические потребности
  },
  
  // Подписка и лимиты
  subscription_plan: string,        // free, starter, pro, business
  subscription_status: string,      // active, expired, suspended
  monthly_tech_cards_used: number, // Использовано техкарт в месяце
  monthly_limit: number,           // Лимит техкарт в месяце
  subscription_expires_at?: string, // Дата окончания подписки
  
  // Метаданные
  last_login_at?: string,
  preferences?: {
    language: string,              // ru, en
    notifications: boolean,
    theme: string                  // light, dark
  }
}
```

### 2. Menu_Projects Collection

**Назначение**: Сохранённые проекты меню пользователей

```typescript
interface MenuProject {
  _id: ObjectId,
  id: string,                      // UUID
  user_id: string,                 // Ссылка на User.id
  project_name: string,            // Название проекта
  created_at: string,
  updated_at: string,
  
  // Профиль заведения на момент создания
  venue_profile: VenueProfile,
  
  // Блюда в проекте
  menu_items: Array<{
    id: string,                    // UUID техкарты
    dish_name: string,             // Название блюда
    content: string,               // Полная техкарта (markdown)
    created_at: string,
    city: string,                  // Город генерации (для ценообразования)
    category?: string,             // Категория блюда
    estimated_price?: number,      // Расчётная цена
    estimated_cost?: number        // Себестоимость
  }>,
  
  // Статистика проекта
  total_dishes: number,
  total_estimated_revenue?: number,
  notes?: string                   // Заметки пользователя
}
```

### 3. User_History Collection

**Назначение**: История генераций техкарт для аналитики использования

```typescript
interface UserHistory {
  _id: ObjectId,
  id: string,
  user_id: string,                 // Ссылка на User.id
  created_at: string,
  
  // Тип операции
  action_type: string,             // "generate_menu", "generate_tech_card", "improve_dish"
  
  // Детали генерации
  request_data: {
    dish_name?: string,
    dishes_count?: number,
    venue_profile: VenueProfile,
    expectations?: string,
    city: string
  },
  
  // Результат
  response_data: {
    success: boolean,
    dishes_generated?: number,
    content?: string,              // Для одиночной техкарты
    menu?: TechCard[],            // Для массовой генерации
    error?: string
  },
  
  // Метрики производительности
  processing_time_ms: number,     // Время выполнения
  ai_model_used: string,         // gpt-4o-mini, gpt-4o, etc
  tokens_used?: number,          // Потрачено токенов OpenAI
  
  // Использование подписки
  subscription_plan: string,      // План на момент запроса
  monthly_usage_before: number,  // Использование до запроса
  monthly_usage_after: number    // Использование после запроса
}
```

### 4. IIKo_Sync_Records Collection

**Назначение**: Логи синхронизации с IIKo для отслеживания интеграции

```typescript
interface IIKoSyncRecord {
  _id: ObjectId,
  id: string,                     // UUID
  user_id: string,                // Кто инициировал
  created_at: string,
  
  // IIKo данные
  organization_id: string,        // ID организации в IIKo
  organization_name?: string,     // Название организации
  
  // Детали техкарты/блюда
  tech_card_name: string,         // Название блюда
  sync_type: string,             // "assembly_chart_only", "complete_dish_creation", etc
  sync_status: string,           // "created_as_assembly_chart", "complete_success", etc
  
  // Результаты создания
  assembly_chart_id?: string,    // ID техкарты в IIKo
  dish_product_id?: string,      // ID продукта в IIKo  
  category_id?: string,          // ID категории в IIKo
  
  // Метаданные
  ai_generated: boolean,         // Создано ли AI
  upload_success: boolean,       // Успешность операции
  steps_completed?: string[],    // Завершённые этапы
  errors?: string[],            // Возникшие ошибки
  
  // Дополнительные данные
  prepared_data?: any,          // Подготовленные данные для ручной загрузки
  sync_notes?: string
}
```

### 5. Cities Collection

**Назначение**: Справочник городов для ценообразования

```typescript
interface City {
  _id: ObjectId,
  code: string,                   // moscow, spb, novosibirsk
  name: string,                   // Москва, Санкт-Петербург
  region?: string,                // Московская область
  
  // Коэффициенты ценообразования
  price_coefficients: {
    food_cost_multiplier: number,  // 1.0 для Москвы, 0.8 для регионов
    rent_coefficient: number,      // Влияние аренды на цены
    labor_cost_coefficient: number, // Стоимость рабочей силы
    logistics_coefficient: number   // Логистические расходы
  },
  
  // Метаданные
  active: boolean,
  population?: number,
  timezone: string               // Europe/Moscow, Asia/Novosibirsk
}
```

## Связи между сущностями

### 1:N Relationships

```typescript
User (1) → MenuProject (N)
  - user_id связывает проекты с пользователями

User (1) → UserHistory (N)  
  - user_id для истории активности пользователя

User (1) → IIKoSyncRecord (N)
  - user_id для логов синхронизации с IIKo

MenuProject (1) → TechCard (N)
  - project содержит массив menu_items

City (1) → User (N)
  - city (string) связывает пользователей с городами
```

### M:N Relationships

```typescript
User (M) ↔ KitchenEquipment (N)
  - через массив equipment[] в venue_profile
  - позволяет пользователям иметь множество единиц оборудования
  - единица оборудования может быть у многих пользователей
```

## Индексы MongoDB

**Критические индексы для производительности:**

```javascript
// Users Collection
db.users.createIndex({ "id": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "city": 1 })

// MenuProjects Collection  
db.menu_projects.createIndex({ "user_id": 1 })
db.menu_projects.createIndex({ "created_at": -1 })
db.menu_projects.createIndex({ "user_id": 1, "created_at": -1 })

// UserHistory Collection
db.user_history.createIndex({ "user_id": 1 })
db.user_history.createIndex({ "created_at": -1 })
db.user_history.createIndex({ "action_type": 1 })
db.user_history.createIndex({ "user_id": 1, "created_at": -1 })

// IIKoSyncRecords Collection
db.iiko_sync_records.createIndex({ "user_id": 1 })
db.iiko_sync_records.createIndex({ "organization_id": 1 })
db.iiko_sync_records.createIndex({ "sync_status": 1 })
db.iiko_sync_records.createIndex({ "created_at": -1 })

// Cities Collection
db.cities.createIndex({ "code": 1 }, { unique: true })
db.cities.createIndex({ "active": 1 })
```

## Хранение идентификаторов IIKo

**Где хранятся ID из IIKo:**

1. **Организации**: Получаются динамически через API, не сохраняются
2. **Продукты/Номенклатура**: Кэшируются во время работы, не persistent storage  
3. **Assembly Charts**: `assembly_chart_id` в IIKoSyncRecord
4. **DISH Products**: `dish_product_id` в IIKoSyncRecord
5. **Categories**: `category_id` в IIKoSyncRecord

**Стратегия ID менеджмента:**
- UUID используются для всех внутренних ID
- IIKo ID сохраняются только для tracking созданных сущностей
- Кэширование IIKo данных в памяти с TTL
- Нет дублирования IIKo базы данных в MongoDB

## Миграции данных

**Планы по schema evolution:**

1. **v1 → v2**: Добавление venue_profile в User
2. **v2 → v3**: Расширение IIKoSyncRecord для DISH products
3. **v3 → v4**: Добавление analytics данных в UserHistory

**Стратегия миграций:**
- Backward compatibility для существующих документов
- Default values для новых полей
- Пошаговое обновление без downtime