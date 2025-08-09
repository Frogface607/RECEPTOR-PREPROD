# API Endpoints Documentation

## Базовая информация
- **Base URL**: `${REACT_APP_BACKEND_URL}/api`
- **Authentication**: Session-based (user_id в request body)
- **Content-Type**: `application/json`
- **All endpoints**: Префикс `/api` обязателен

## Menu Generation & Tech Cards

### `POST /api/generate-menu`
Генерация меню с множественными техкартами

**Request Body:**
```typescript
{
  dishes_count: number,           // Количество блюд (3-15)
  venue_profile: {
    venue_type: string,           // Тип заведения
    cuisine_type: string,         // Тип кухни  
    target_audience: string,      // Целевая аудитория
    budget_level: string,         // Бюджетный уровень
    city: string                  // Город для ценообразования
  },
  expectations: string,           // Свободное описание ожиданий
  user_id: string                // ID пользователя
}
```

**Response:**
```typescript
{
  success: boolean,
  menu: Array<{
    dish_name: string,
    content: string,              // Полная техкарта в markdown
    id: string,
    created_at: string,
    city: string
  }>,
  user_id: string,
  dishes_generated: number,
  city: string
}
```

### `POST /api/generate-tech-card`
Генерация одной техкарты

**Request Body:**
```typescript
{
  dish_name: string,
  venue_profile: VenueProfile,
  user_id: string,
  city?: string
}
```

**Response:**
```typescript
{
  success: boolean,
  content: string,                // Техкарта в markdown формате
  dish_name: string,
  user_id: string,
  id: string,
  city: string
}
```

### `POST /api/improve-dish`
Улучшение существующей техкарты

**Request Body:**
```typescript
{
  current_tech_card: string,      // Текущая техкарта
  improvement_request: string,    // Запрос на улучшение
  user_id: string
}
```

## IIKo Integration

### Health & Status

### `GET /api/iiko/health`
Проверка состояния интеграции с IIKo

**Response:**
```typescript
{
  status: "healthy" | "error",
  iiko_connection: "active" | "failed",
  auth_status: string,
  last_check: string,
  organizations_count?: number
}
```

### Organizations

### `GET /api/iiko/organizations`
Получение списка организаций из IIKo

**Response:**
```typescript
{
  success: boolean,
  organizations: Array<{
    id: string,
    name: string,
    address: string,
    active: boolean
  }>
}
```

### Menu & Products

### `GET /api/iiko/menu/{organization_id}`
Получение номенклатуры организации

**Path Parameters:**
- `organization_id`: string

**Response:**
```typescript
{
  success: boolean,
  menu: {
    categories: Array<{
      id: string,
      name: string,
      description: string,
      active: boolean
    }>,
    items: Array<{
      id: string,
      name: string,
      description: string,
      category_id: string,
      price: number,
      weight: number,
      active: boolean
    }>
  }
}
```

### Categories Management

### `GET /api/iiko/categories/{organization_id}`
Получение всех категорий

**Response:**
```typescript
{
  success: boolean,
  categories: Array<{
    id: string,
    name: string,
    parent_id?: string,
    description: string,
    active: boolean
  }>,
  total_count: number
}
```

### `POST /api/iiko/categories/create`
Создание новой категории

**Request Body:**
```typescript
{
  name: string,                   // Название категории
  organization_id: string,
  parent_id?: string,            // Родительская категория
  description?: string
}
```

### `POST /api/iiko/categories/check`
Проверка существования категории

**Request Body:**
```typescript
{
  category_name: string,
  organization_id: string
}
```

**Response:**
```typescript
{
  success: boolean,
  exists: boolean,
  category?: {
    id: string,
    name: string,
    items_count: number
  }
}
```

### Tech Cards (Assembly Charts)

### `POST /api/iiko/assembly-charts/create`
Создание техкарты в IIKo

**Request Body:**
```typescript
{
  name: string,
  description: string,
  ingredients: Array<{
    name: string,
    quantity: number,
    unit: string,
    price?: number
  }>,
  preparation_steps: string[],
  organization_id: string,
  weight?: number,
  price?: number,
  category_id?: string
}
```

### `GET /api/iiko/assembly-charts/all/{organization_id}`
Получение всех техкарт организации

### `POST /api/iiko/tech-cards/upload`
Загрузка AI техкарты в IIKo (Enhanced)

**Request Body:** TechCardUpload (см. выше)

**Response:**
```typescript
{
  success: boolean,
  sync_id: string,
  status: "complete_success" | "assembly_only" | "dish_only",
  message: string,
  details: {
    assembly_chart: {
      created: boolean,
      id?: string
    },
    dish_product: {
      created: boolean,
      id?: string,
      name?: string
    }
  },
  will_appear_in_menu: boolean
}
```

### Products (DISH Creation)

### `POST /api/iiko/products/create-complete-dish`
Создание полноценного блюда (Assembly Chart + DISH Product)

**Request Body:** TechCardUpload

**Response:**
```typescript
{
  success: boolean,
  sync_id: string,
  status: "complete_success" | "partial_success" | "complete_failure",
  message: string,
  details: {
    assembly_chart: { created: boolean, id?: string },
    dish_product: { created: boolean, id?: string, name?: string },
    category: { id?: string }
  },
  summary: {
    dish_name: string,
    assembly_chart_created: boolean,
    dish_product_created: boolean,
    category_used?: string,
    steps_completed: number,
    errors_count: number
  }
}
```

### Analytics & Reports

### `GET /api/iiko/sales-report/{organization_id}`
Базовый отчет по продажам

**Query Parameters:**
- `date_from`: string (YYYY-MM-DD)
- `date_to`: string (YYYY-MM-DD)

### `GET /api/iiko/analytics/{organization_id}`
Аналитическая сводка (OLAP)

## User Management

### `POST /api/create-user`
Создание нового пользователя

**Request Body:**
```typescript
{
  name: string,
  email: string,
  city: string
}
```

### `POST /api/update-user`
Обновление профиля пользователя

**Request Body:**
```typescript
{
  user_id: string,
  name?: string,
  email?: string,
  city?: string,
  venue_profile?: VenueProfile
}
```

### `POST /api/update-venue-profile`
Обновление профиля заведения

**Request Body:**
```typescript
{
  user_id: string,
  venue_profile: {
    venue_type: string,
    cuisine_type: string,
    target_audience: string,
    budget_level: string,
    equipment?: string[],
    special_dietary_needs?: string[]
  }
}
```

## Projects Management

### `POST /api/save-project`
Сохранение проекта меню

**Request Body:**
```typescript
{
  user_id: string,
  project_name: string,
  menu_items: Array<{
    dish_name: string,
    content: string
  }>,
  venue_profile: VenueProfile
}
```

### `GET /api/user-projects/{user_id}`
Получение проектов пользователя

## Reference Data

### `GET /api/cities`
Справочник городов

**Response:**
```typescript
Array<{
  code: string,
  name: string,
  region?: string
}>
```

### `GET /api/venue-types`
Типы заведений

**Response:**
```typescript
{
  [key: string]: {
    name: string,
    description: string,
    complexity_level: "low" | "medium" | "high",
    price_multiplier: number
  }
}
```

### `GET /api/cuisine-types`
Типы кухонь

### `GET /api/subscription-plans`
Тарифные планы

### `GET /api/kitchen-equipment`
Кухонное оборудование

## Subscription & Billing

### `POST /api/update-subscription`
Обновление подписки пользователя

### `GET /api/user-subscription/{user_id}`
Текущая подписка пользователя

## Error Handling

Все endpoints возвращают стандартизированные HTTP статус коды:

- **200**: Success
- **400**: Bad Request (валидация не прошла)
- **404**: Not Found (ресурс не найден)
- **500**: Internal Server Error

**Формат ошибки:**
```typescript
{
  detail: string,                 // Описание ошибки
  error_code?: string,            // Код ошибки для программной обработки
  field_errors?: Array<{          // Ошибки валидации полей
    field: string,
    message: string
  }>
}
```