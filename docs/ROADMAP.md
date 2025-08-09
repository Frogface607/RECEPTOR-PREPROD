# Roadmap AI Menu Designer 2025

## Track A: TechCards for IIKo

### Sprint 1-2: Enhanced TechCards Structure (2 недели)
**Цель**: Расширить техкарты до полного соответствия IIKo стандартам

**Features:**
- **Брутто/Нетто расчёты**
  - Добавить автоматический расчёт потерь при обработке продуктов
  - Учёт усушки/упрения для разных типов продуктов
  - Калькулятор waste percentages по категориям ингредиентов

- **Аллергены и диетические ограничения**
  - База данных аллергенов для всех ингредиентов
  - Автоматическое определение аллергенов в блюдах
  - Маркировка веганских, глютен-фри, лактозо-фри блюд
  - Интеграция с профилем заведения для фильтрации

- **HACCP compliance**
  - Температурные режимы хранения и приготовления
  - Critical Control Points для каждого этапа приготовления
  - Автоматические чек-листы для контроля качества
  - Сроки годности промежуточных заготовок

**Мильстоун**: Техкарты содержат всю информацию, необходимую для restaurant compliance

### Sprint 3-4: Export & Import System (2 недели)
**Цель**: Создать universal систему экспорта для разных IIKo установок

**Features:**
- **Multi-format Export**
  - PDF техкарты с HACCP данными
  - CSV для bulk import в IIKo
  - Excel шаблоны для ручного ввода
  - JSON API format для программной интеграции

- **Template система**
  - Customizable PDF templates под разные типы заведений
  - Брендинг техкарт (логотипы, цвета, шрифты)
  - Локализация шаблонов (разные языки)
  - A4/Letter format support

- **Batch operations**
  - Массовый экспорт всех техкарт проекта
  - Zip архивы с организованной структурой папок
  - Email delivery больших экспортов
  - Progress tracking для длительных операций

**Мильстоун**: Техкарты можно экспортировать в любом формате для любой IIKo установки

### Sprint 5-6: Write-back Adapter Development (2 недели)
**Цель**: Подготовить адаптер для прямой записи в IIKo (пока отключён)

**Features:**
- **Universal API Connector**
  - Поддержка IIKo Cloud API и IIKo Office API
  - Auto-detection типа IIKo установки
  - Fallback mechanisms при недоступности endpoints
  - Retry logic с exponential backoff

- **Data Mapping Engine**
  - Mapping AI техкарт на IIKo data structures
  - Validation совместимости данных
  - Conflict resolution strategies
  - Preview changes before writing

- **Permission System**
  - Role-based access для IIKo операций
  - Audit logs всех write операций
  - Rollback capabilities для критических изменений
  - Safe mode для тестирования

**Мильстоун**: Готов write-back адаптер (отключён в production до получения разрешения от IIKo)

## Track B: BI/Analytics Dashboard

### Sprint 7-8: IIKo Cloud API Integration (2 недели)
**Цель**: Подключить real-time данные из IIKo для аналитики

**Features:**
- **Sales Data Pipeline**
  - Подключение к IIKo Cloud API для продаж
  - Синхронизация данных по сменам
  - Real-time уведомления о новых продажах
  - Historical data import (последние 12 месяцев)

- **Employee & Operations Data**
  - Данные о сотрудниках и их production efficiency
  - Время приготовления блюд vs плановое время
  - Equipment utilization tracking
  - Shift performance metrics

- **Inventory & Costs**
  - Подключение к складской системе IIKo
  - Real-time остатки ингредиентов
  - Автоматический расчёт себестоимости блюд
  - Cost variance analysis

**Мильстоун**: Real-time pipeline данных из IIKo Cloud API работает стабильно

### Sprint 9-10: Data Warehouse & Metrics (2 недели)
**Цель**: Создать хранилище метрик и базовые dashboard'ы

**Features:**
- **Time-series Database**
  - Оптимизированное хранение временных рядов
  - Efficient queries для large datasets
  - Data retention policies
  - Compression для historical data

- **KPI Calculation Engine**
  - 20+ ключевых метрик ресторана
  - Food cost percentage, Labor cost %, Revenue per seat
  - Menu item profitability analysis
  - Customer satisfaction proxy metrics

- **Basic Dashboards**
  - Real-time sales monitor
  - Daily/Weekly/Monthly performance reports
  - Top/Bottom performing dishes
  - Cost analysis по категориям

**Мильстоун**: Базовые dashboard'ы показывают актуальные данные ресторана

### Sprint 11-12: AI Recommendations Engine (2 недели)
**Цель**: Intelligent рекомендации на основе данных

**Features:**
- **Menu Optimization AI**
  - Анализ продаж для определения неэффективных блюд
  - Seasonal demand forecasting
  - Price optimization рекомендации
  - New dish suggestions на основе trends

- **Operational Intelligence**
  - Inventory optimization recommendations
  - Staff scheduling optimization
  - Equipment maintenance predictions
  - Energy cost optimization tips

- **Predictive Analytics**
  - Forecast продаж на следующие 30 дней
  - Demand prediction для inventory planning
  - Customer churn risk analysis
  - Revenue optimization opportunities

**Мильстоун**: AI выдаёт actionable рекомендации для улучшения бизнес-метрик

## Integrated Features (Cross-track)

### Sprint 13-14: Advanced Menu Intelligence (2 недели)
**Features:**
- **Smart Menu Engineering**
  - AI анализирует продажи и рекомендует menu changes
  - A/B testing для новых блюд
  - Seasonal menu rotation planning
  - Competitor analysis integration

- **Dynamic Pricing Engine**
  - Real-time price adjustments на основе demand
  - Competitor pricing monitoring
  - Cost inflation auto-adjustments
  - Revenue optimization algorithms

### Sprint 15-16: Customer Experience Analytics (2 недели)
**Features:**
- **Customer Journey Mapping**
  - Анализ ordering patterns через IIKo POS данные
  - Customer lifetime value calculations
  - Loyalty program effectiveness analysis
  - Personalized menu recommendations

- **Experience Optimization**
  - Wait time optimization через kitchen analytics
  - Menu readability и psychology-based improvements
  - Cross-selling opportunities identification
  - Customer satisfaction correlation analysis

## Major Milestones

### Q1 2025: Professional TechCards
- ✅ Полные техкарты с HACCP compliance
- ✅ Multi-format export в любую IIKo систему
- ✅ Готовность к официальной интеграции с IIKo

### Q2 2025: Business Intelligence Platform  
- ✅ Real-time analytics dashboard
- ✅ AI-powered business recommendations
- ✅ Predictive analytics для планирования

### Q3 2025: Complete Restaurant OS
- ✅ Integrated menu management + analytics
- ✅ Automated business optimization
- ✅ Multi-location management capabilities

## Success Metrics

### TechCards Track (Track A)
- **Adoption**: 500+ ресторанов используют export features
- **Quality**: 95%+ совместимость с IIKo форматами
- **Efficiency**: 10x сокращение времени на создание техкарт

### Analytics Track (Track B)
- **Data Coverage**: 100% IIKo integrations working
- **User Engagement**: 80%+ пользователей заходят в analytics еженедельно  
- **Business Impact**: 15%+ улучшение profit margins у клиентов

### Combined Platform
- **Market Position**: #1 AI-powered restaurant management platform в России
- **Revenue**: 100M₽+ ARR
- **Scale**: 2000+ активных ресторанов

## Technical Architecture Evolution

### Microservices Transition
- Разделение монолитного server.py на специализированные сервисы
- TechCards Service, Analytics Service, IIKo Integration Service
- Message queue (Redis/RabbitMQ) для межсервисного взаимодействия

### Scalability Improvements
- Kubernetes horizontal autoscaling
- Database sharding для больших объёмов данных
- CDN для static assets (PDF техкарты, images)

### Advanced Integrations
- Multiple POS systems support (не только IIKo)
- Accounting systems integration (1C, SAP)
- Suppliers integration для real-time pricing
- Payment systems integration для transaction data