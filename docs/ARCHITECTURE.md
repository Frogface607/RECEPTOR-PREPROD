# Архитектура AI Menu Designer (Receptor PRO)

## Обзор системы

AI Menu Designer построен как full-stack SaaS приложение с современной микросервисной архитектурой:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│    Backend      │────│   Database      │
│   (React)       │    │   (FastAPI)     │    │   (MongoDB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                       ┌─────────────────┐
                       │  External APIs  │
                       │  - OpenAI       │
                       │  - IIKo Office  │
                       └─────────────────┘
```

## FastAPI Backend Architecture

### Модульная структура
```
server.py
├── Entry Point & Configuration
│   ├── CORS setup
│   ├── Environment variables
│   └── MongoDB connection
│
├── Service Layer
│   ├── IikoServerAuthManager
│   ├── IikoServerIntegrationService
│   └── OpenAI Integration
│
├── API Router Layer
│   ├── /api/generate-menu
│   ├── /api/iiko/*
│   ├── /api/subscription/*
│   └── /api/analytics/*
│
└── Data Models (Pydantic)
    ├── TechCardUpload
    ├── VenueProfileUpdate
    └── MenuGenerationRequest
```

### Ключевые компоненты

#### 1. Entry Point (server.py:32-45)
- **FastAPI app initialization**
- **CORS middleware** для cross-origin requests
- **MongoDB connection** через motor.motor_asyncio
- **Environment configuration** через dotenv

#### 2. Service Layer

##### IikoServerAuthManager (server.py:47-118)
```python
class IikoServerAuthManager:
    - SHA1 authentication для IIKo Office
    - Session management с auto-refresh
    - Token expiration handling (15-min buffer)
    - Error recovery механизмы
```

##### IikoServerIntegrationService (server.py:120-740)
```python
class IikoServerIntegrationService:
    - get_organizations() - получение списка организаций
    - get_menu_items() - загрузка номенклатуры IIKo
    - create_dish_product() - создание DISH продуктов
    - create_complete_dish_in_iiko() - полное создание блюда
    - get_sales_report() - отчеты по продажам
    - get_sales_olap_report() - OLAP аналитика
```

#### 3. API Router Layer
- **Префикс**: `/api` (обязательно для Kubernetes ingress)
- **Authentication**: Session-based через user_id
- **Error Handling**: Structured HTTP exceptions
- **Response Format**: Стандартизированный JSON

#### 4. Data Models (Pydantic)
- **Type Safety**: Валидация входящих данных
- **Auto Documentation**: OpenAPI schema generation
- **Error Messages**: Детализированные ошибки валидации

## Интеграции

### OpenAI Integration
```python
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
- Model: gpt-4o-mini (cost-optimized)
- GOLDEN_PROMPT: специализированный промпт для HoReCa
- Structured output parsing
```

### IIKo Office Integration
```python
Base URL: https://iikoffice1.api.rms.ru
Authentication: SHA1 hash + session tokens
Endpoints:
  - /resto/api/auth - аутентификация
  - /resto/api/v2/entities/products/list - номенклатура
  - /resto/api/v2/assemblyCharts - техкарты
  - /resto/api/reports/olap - аналитические отчеты
```

### MongoDB Database
```javascript
Collections:
  - users: пользователи и подписки
  - user_history: история генераций техкарт
  - menu_projects: проекты меню
  - iiko_sync_records: логи синхронизации с IIKo
  - cities: справочник городов для ценообразования
```

## Deployment Architecture

### Kubernetes + Supervisor
```yaml
Services:
  - frontend: React dev server (port 3000)
  - backend: FastAPI (port 8001) 
  - mongodb: Local instance
  - supervisor: Process management

Ingress Rules:
  - /api/* → backend:8001
  - /* → frontend:3000
```

### Environment Configuration
```bash
# Backend (.env)
MONGO_URL=mongodb://localhost:27017/
DB_NAME=receptor_pro
OPENAI_API_KEY=sk-...
IIKO_LOGIN=...
IIKO_PASSWORD=...
IIKO_SERVER_URL=https://iikoffice1.api.rms.ru

# Frontend (.env) 
REACT_APP_BACKEND_URL=https://ai-menu-wizard.preview.emergentagent.com
```

## Очереди задач
**Статус**: Not implemented
**Планы**: 
- Background jobs для массовой генерации техкарт
- Email notifications для завершенных операций
- Scheduled tasks для синхронизации с IIKo

## Настройки и конфигурация

### Критические настройки
- **MONGO_URL**: НЕ ИЗМЕНЯТЬ (настроен для локального доступа)  
- **REACT_APP_BACKEND_URL**: НЕ ИЗМЕНЯТЬ (настроен для внешнего доступа)
- **API Prefix**: Все backend routes ДОЛЖНЫ начинаться с `/api`

### Масштабирование
- **Horizontal**: Ready для Docker containerization
- **Vertical**: MongoDB indexes для performance
- **Cache**: В планах Redis для session storage