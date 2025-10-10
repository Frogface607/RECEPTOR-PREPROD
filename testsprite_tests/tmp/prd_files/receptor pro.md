# RECEPTOR PRO - Техническая документация

## 🏗️ Архитектура проекта

**Stack:** React (Frontend) + FastAPI (Backend) + MongoDB (Database)

```
RECEPTOR PRO - AI Menu Designer
├── Frontend (React) - Монолитное SPA приложение
├── Backend (FastAPI) - RESTful API сервер  
├── MongoDB - База данных пользователей и техкарт
└── Внешние интеграции (OpenAI, IIKO RMS)
```

## 📁 Структура проекта

```
/app/
├── backend/                          # FastAPI Backend
│   ├── server.py                     # Основной сервер, все endpoints
│   ├── receptor_agent/               # Основная бизнес-логика
│   │   ├── routes/                   # Маршруты API
│   │   │   ├── techcards_v2.py      # V2 техкарты (структурированные)
│   │   │   ├── export_v2.py         # Экспорт в IIKO (ZIP, XLSX)
│   │   │   └── iiko_xlsx_import.py  # Импорт из IIKO
│   │   ├── integrations/             # Внешние интеграции
│   │   │   ├── enhanced_mapping_service.py  # Автомаппинг ингредиентов
│   │   │   ├── article_allocator.py  # Генерация артикулов
│   │   │   └── iiko_rms_service.py  # Интеграция с IIKO RMS
│   │   ├── techcards_v2/            # Логика V2 техкарт
│   │   │   ├── schemas.py           # Pydantic модели
│   │   │   ├── cost_calculator.py   # Расчет себестоимости
│   │   │   └── operational_rounding.py # Округление ингредиентов
│   │   └── exports/                 # Экспорт файлов
│   │       ├── iiko_xlsx.py         # Создание XLSX для IIKO
│   │       └── zipper.py            # ZIP архивы
│   ├── requirements.txt             # Python зависимости
│   └── .env                        # Переменные окружения Backend
│
├── frontend/                        # React Frontend
│   ├── src/
│   │   ├── App.js                   # Главный компонент (монолит ~12k строк)
│   │   └── config/
│   │       └── featureFlags.js     # Флаги функций
│   ├── package.json                # Node.js зависимости
│   └── .env                        # Переменные окружения Frontend
│
├── test_result.md                   # Протокол тестирования
├── ULTIMATE_LAUNCH_PLAN.md         # План запуска продукта
└── AI_KITCHEN_ENHANCEMENT_PLAN.md  # План развития AI-кухни
```

## 🔑 Ключевые концепции

### V1 vs V2 Техкарты
- **V1 Рецепты** - творческие рецепты от AI (свободный формат)
- **V2 Техкарты** - структурированные техкарты для IIKO (строгий формат)
- **Конвертация V1→V2** - преобразование рецептов в техкарты

### Пользовательские роли
- **demo_user** - демо пользователь с ограничениями
- **Авторизованные** - полный доступ ко всем функциям
- **Изоляция данных** - строгое разделение по `user_id`

## 🎯 Основные компоненты

### 1. Frontend (App.js) - Монолитная архитектура

**Основные состояния:**
```javascript
// Пользователь и аутентификация
const [currentUser, setCurrentUser] = useState(null);
const [userEquipment, setUserEquipment] = useState([]);
const [venueProfile, setVenueProfile] = useState({});

// Техкарты и рецепты
const [techCard, setTechCard] = useState(null);        // V1 рецепт
const [tcV2, setTcV2] = useState(null);               // V2 техкарта
const [aiKitchenRecipe, setAiKitchenRecipe] = useState(null); // AI-кухня

// UI состояния
const [currentView, setCurrentView] = useState('main'); // main, history, ai-kitchen
const [isGenerating, setIsGenerating] = useState(false);
```

**Ключевые функции:**
- `generateTechCard()` - Создание V2 техкарты напрямую
- `generateV1Recipe()` - Создание V1 рецепта в AI-кухне
- `convertV1ToV2()` - Конвертация V1→V2
- `executeZipExport()` - Экспорт в IIKO
- AI функции: `generateInspiration()`, `generateFoodPairing()`, etc.

### 2. Backend API Endpoints

**Основные группы:**
```python
# Техкарты V2
POST /api/v1/techcards.v2/generate      # Создание техкарты
POST /api/v1/techcards.v2/enhanced-auto-mapping  # Автомаппинг
GET  /api/v1/techcards.v2/catalog-search # Поиск в каталоге

# Экспорт
POST /api/v1/export/preflight          # Проверка перед экспортом
POST /api/v1/export/zip               # ZIP экспорт с скелетонами
POST /api/v1/techcards.v2/export/iiko.xlsx # XLSX для IIKO

# AI Функции
POST /api/generate-inspiration         # Вдохновение
POST /api/generate-food-pairing       # Фудпейринг
POST /api/generate-sales-script       # Скрипт продаж
POST /api/analyze-finances            # Финансовый анализ

# V1 Рецепты
POST /api/v1/generate-recipe          # Генерация V1
POST /api/v1/convert-v1-to-v2        # Конвертация

# Пользователи
GET  /api/user-history/{user_id}      # История пользователя
POST /api/v1/user/save-recipe        # Сохранение V1
```

### 3. База данных (MongoDB)

**Коллекции:**
```javascript
// Пользователи
users: {
  _id: "user_uuid",
  email: "user@example.com",
  subscription_plan: "pro",
  demo_mode: false
}

// История (все техкарты и рецепты)  
user_history: {
  _id: ObjectId,
  id: "uuid",           // Уникальный ID записи
  user_id: "user_uuid", // Владелец
  type: "v2_techcard" | "v1_recipe",
  dish_name: "Название блюда",
  data: {...},          // Полные данные техкарты/рецепта
  created_at: Date
}

// Кэш каталога продуктов
product_catalog: {
  name: "Говядина",
  article: "BEEF001", 
  price: 850.0,
  user_id: "user_uuid"
}
```

## 🔄 Ключевые процессы

### 1. Создание V2 техкарты (основной flow)

```mermaid
User Input → AI Generation → Article Allocation → Auto Mapping → Final Techcard
```

1. **Пользователь** описывает блюдо
2. **AI (GPT-4o)** генерирует подробную техкарту
3. **Article Allocator** присваивает артикулы (100001, 100002...)
4. **Enhanced Mapping** ищет реальные артикулы в IIKO
5. **Сохранение** в user_history

### 2. Экспорт в IIKO (сложный процесс)

```mermaid
Preflight Check → Generate Skeletons → Create ZIP → Download
```

1. **Preflight** - проверка несопоставленных ингредиентов
2. **Skeleton Generation** - создание Product-Skeletons.xlsx, Dish-Skeletons.xlsx
3. **ZIP Creation** - упаковка всех файлов
4. **Download** - отдача пользователю

### 3. AI-кухня (экспериментальные функции)

```mermaid
V1 Recipe → AI Enhancement → Save/Convert → V2 Techcard
```

## 🔧 Сложности и подводные камни

### 1. **Артикулы и маппинг (КРИТИЧНО!)**
```python
# Проблема: различие между сгенерированными и реальными артикулами
generated_articles = "100001", "100002"  # Наши
real_iiko_articles = "BEEF001", "VEG_TOM"  # Из IIKO

# Решение: функция _is_generated_article()
def _is_generated_article(code):
    return code.isdigit() and 1000 <= int(code) <= 999999
```

### 2. **Изоляция данных пользователей**
```python
# ОБЯЗАТЕЛЬНО везде фильтровать по user_id
user_data = db.user_history.find({"user_id": current_user_id})

# ОПАСНО - может показать чужие данные
all_data = db.user_history.find()  # ❌ НЕ ДЕЛАТЬ
```

### 3. **Frontend монолит App.js (~12k строк)**
- Все состояние в одном компоненте
- Сложная навигация между view (main, history, ai-kitchen)
- Множественные useEffect для синхронизации

### 4. **Асинхронность и состояния**
```javascript
// Проблема: race conditions при генерации
const [isGenerating, setIsGenerating] = useState(false);

// Решение: всегда проверять состояние
if (isGenerating) return; // Предотвращаем множественные запросы
```

### 5. **Интеграция с IIKO RMS**
```python
# Проблема: может быть недоступна
rms_service = get_iiko_rms_service()
if not rms_service:
    logger.warning("IIKO RMS не подключено")
    # Fallback на каталог или AI
```

## 🚀 Инструкции по запуску

### Переменные окружения

**Backend (.env):**
```bash
MONGO_URL=mongodb://localhost:27017/receptor_pro
DB_NAME=receptor_pro
OPENAI_API_KEY=sk-...
EMERGENT_LLM_KEY=emg-...
IIKO_API_LOGIN=your_login
IIKO_API_PASSWORD=your_password
```

**Frontend (.env):**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001  # Внимание: порт 8001!
```

### Команды запуска
```bash
# Backend
cd /app/backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001

# Frontend  
cd /app/frontend
yarn install
yarn start  # Порт 3000

# MongoDB
mongod --dbpath /data/db
```

## 🎨 UI/UX Особенности

### Адаптивность
- Responsive design для мобильных
- `sm:`, `md:` префиксы TailwindCSS
- Минимальная высота кнопок 44px для мобильных

### Состояния загрузки
```javascript
// Кнопки показывают процесс
{isGenerating ? 'СОЗДАНИЕ...' : 'СОЗДАТЬ ТЕХКАРТУ'}

// Прогресс-бары для долгих операций
setGenerationProgress(60); // 0-100
```

### Модальные окна
- Результаты AI функций в модалах
- Форматирование markdown через `formatProAIContent()`
- Кнопки "Сохранить как V1" для интеграции

## 🔍 Отладка и логирование

### Backend логи
```python
# Уровни логирования
logger.info("Информация")
logger.warning("Предупреждение") 
logger.error("Ошибка")

# Важные места для логов
- Генерация техкарт
- Экспорт процессы
- Интеграции с IIKO
```

### Frontend отладка
```javascript
// Console.log для критичных мест
console.log('🔍 Preflight result:', preflight);
console.log('🎯 Testing with aiKitchenRecipe:', aiKitchenRecipe?.name);

// React DevTools для состояний
```

## 📊 Метрики и аналитика

### Тайминги генерации
```python
timings = {
    'llm_draft_ms': 8564.0,
    'llm_normalize_ms': 4976.0, 
    'article_generation_ms': 250.0,
    'total_ms': 13592.0
}
```

### Пользовательская активность
- Сохранение в user_history с timestamp
- Подсчет созданных техкарт
- Отслеживание использования AI функций

## 🎯 Точки расширения

### 1. Новые AI функции
```python
# Добавить в server.py
@app.post("/api/new-ai-function")
async def new_function():
    # LLM запрос
    # Сохранение результата
    # Возврат данных
```

### 2. Интеграции
```python
# Новые сервисы в integrations/
class NewIntegrationService:
    def __init__(self):
        self.api_key = os.getenv('NEW_SERVICE_KEY')
```

### 3. UI компоненты
```javascript
// Выделение из App.js в отдельные компоненты
const TechCardGenerator = () => { ... }
const AIKitchen = () => { ... }
const ExportManager = () => { ... }
```

## ⚡ Производительность

### Критичные места
1. **AI генерация** - 10-30 секунд
2. **Автомаппинг** - зависит от размера каталога
3. **Экспорт ZIP** - создание множественных XLSX файлов
4. **MongoDB запросы** - индексы по user_id обязательны

### Оптимизации
- Кэширование каталога продуктов
- Пагинация в истории
- Оптимизация размеров изображений
- Минификация bundle'а

Этот техдок должен дать полную картину проекта для быстрого погружения в разработку! 🚀