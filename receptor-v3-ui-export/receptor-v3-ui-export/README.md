# Receptor V3 UI Export 🎨

## 📋 Обзор
Экспорт всех ключевых UI компонентов, хуков, сервисов и стилей из V3-preview для безопасной интеграции в legacy продакшн версию.

## 🎯 Цель
- Сохранить современный минималистичный UI из V3
- Обеспечить плавную интеграцию в стабильную legacy бизнес-логику  
- Избежать риска поломки рабочих потоков
- Ускорить rollout новых фич

---

## 📁 Структура экспорта

### `/components/` - UI Компоненты

#### **Layout System**
- `Header.tsx` - Современный хедер с навигацией и пользовательским меню
- `Sidebar.tsx` - Боковая навигация с иконками и активными состояниями  
- `Layout.tsx` - Основной layout wrapper

#### **Onboarding Flow** 🚀
- `OnboardingModal.tsx` - Основной модальный компонент онбординга
- `WelcomeStep.tsx` - Приветственный экран с выбором роли
- `SetupStep.tsx` - Настройка профиля пользователя
- `FirstSuccessStep.tsx` - Первая генерация техкарты (demo)
- `ExploreStep.tsx` - Обзор возможностей системы

#### **PRO Upgrade & Billing** 💳
- `UpgradeModal.tsx` - Модалка апгрейда до PRO
- `PricingPage.tsx` - Страница тарифов с YooKassa интеграцией
- `PaymentSuccess.tsx` - Обработка успешной оплаты

#### **TechCard Generation** 🍽️
- `TechCardView.tsx` - Отображение готовой техкарты
- `TechCardGeneration.tsx` - Форма создания новой техкарты
- `IngredientsTable.tsx` - Таблица ингредиентов с редактированием
- `ProcessSteps.tsx` - Шаги приготовления
- `NutritionCard.tsx` - Пищевая ценность
- `SaveButton.tsx` - Кнопка сохранения с состояниями

#### **Utility Components**
- `ErrorBoundary.tsx` - Глобальная обработка ошибок React
- `BugReportModal.tsx` - Система сбора багов с токенами
- `TokensDisplay.tsx` - Отображение токенов/очков
- `ExportMaster.tsx` - Мастер экспорта (PDF, Excel, iiko)

### `/services/` - API Сервисы
- `techCardApi.ts` - API для работы с техкартами (с умным demo fallback)
- `billingApi.ts` - YooKassa интеграция и управление подписками
- `userProfileApi.ts` - Управление профилем пользователя
- `integrationsApi.ts` - iiko и другие интеграции
- `bugReportApi.ts` - API багрепортов

### `/hooks/` - React Хуки
- `useOnboarding.ts` - Управление состоянием онбординга
- `useTokens.ts` - Система токенов и достижений
- `useAnalytics.ts` - Трекинг пользовательских событий
- `useFeatureAccess.ts` - PRO-gating и управление доступом
- `useApiHealth.ts` - Мониторинг состояния API

### `/contexts/` - React Контексты  
- `UserPlanContext.tsx` - Глобальное состояние тарифного плана
- `OnboardingContext.tsx` - Состояние процесса онбординга

### `/utils/` - Утилиты
- `featureFlags.ts` - Система feature flags с канареечным rollout
- `demoData.ts` - Умная генерация demo данных на основе названия блюда

### `/styles/` - Стили
- `globals.css` - Глобальные стили и CSS переменные
- `colors.css` - Цветовая палитра V3
- `typography.css` - Типографика и шрифты

---

## 🎨 Ключевые UI Flow

### 1. **Onboarding Experience** 
*4-шаговый процесс адаптации новых пользователей*

**Шаги:**
1. **Welcome** - Выбор роли (Шеф-повар/Менеджер/Владелец)
2. **Setup** - Настройка профиля и предпочтений  
3. **First Success** - Генерация первой техкарты (demo)
4. **Explore** - Обзор возможностей системы

**Интеграция в Legacy:**
```jsx
import { OnboardingModal } from './receptor-v3-ui-export/components/OnboardingModal'
import { useOnboarding } from './receptor-v3-ui-export/hooks/useOnboarding'

// В App.jsx
const { isVisible, currentStep, completeOnboarding } = useOnboarding()
```

### 2. **PRO Upgrade Flow**
*Плавный переход от Free к PRO с YooKassa*

**Компоненты:**
- Pricing page с тарифными планами
- UpgradeModal для quick upgrade
- YooKassa Hosted Checkout интеграция
- Обработка webhooks payment.succeeded

**Интеграция в Legacy:**
```jsx
import { PricingPage, UpgradeModal } from './receptor-v3-ui-export/components'
import { useBilling } from './receptor-v3-ui-export/hooks'
```

### 3. **Tech Card Generation**
*Современный интерфейс создания техкарт*

**Фичи:**
- Умный demo fallback при недоступности AI
- Реалтайм генерация с прогресс индикаторами  
- Inline редактирование ингредиентов
- Автосохранение в библиотеку

### 4. **Bug Report System**
*Геймифицированная система сбора фидбека*

**Особенности:**
- Токены за баг-репорты
- Приоритизация по серьезности
- Автоматический сбор контекста

---

## 🔧 Интеграция в Legacy

### Пошаговый план:

1. **Копировать папку** `receptor-v3-ui-export/` в legacy проект
2. **Установить зависимости** (если нужны новые)
3. **Интегрировать по компонентам:**
   - Начать с `Layout` компонентов (Header, Sidebar)
   - Добавить `OnboardingModal` для новых пользователей
   - Внедрить `PRO upgrade` flow
   - Постепенно заменять старые компоненты на новые

### Пример интеграции:

```jsx
// В legacy App.js
import { Header, Sidebar, Layout } from './receptor-v3-ui-export/components'
import { UserPlanProvider } from './receptor-v3-ui-export/contexts'
import { useFeatureFlags } from './receptor-v3-ui-export/utils'

function App() {
  const { isEnabled } = useFeatureFlags()
  
  return (
    <UserPlanProvider>
      <Layout>
        {isEnabled('new_header') ? <Header /> : <OldHeader />}
        {isEnabled('new_sidebar') ? <Sidebar /> : <OldSidebar />}
        {/* ... rest of app */}
      </Layout>
    </UserPlanProvider>
  )
}
```

---

## 🚀 Преимущества этого подхода

- ✅ **Безопасность** - не ломаем legacy функционал
- ✅ **Гибкость** - интегрируем по частям через feature flags
- ✅ **Скорость** - быстрый rollout новых фич  
- ✅ **Качество** - сохраняем проверенный UX из V3
- ✅ **Maintainability** - четкое разделение old vs new

---

## 📸 Screenshots

*TODO: Добавить скриншоты ключевых flow*

- `onboarding-flow.png` - 4-шаговый онбординг
- `pricing-page.png` - Тарифы с YooKassa
- `techcard-generation.png` - Создание техкарты  
- `pro-upgrade-modal.png` - PRO апгрейд модалка

---

## 💡 Следующие шаги

1. ✅ **Экспорт завершен** - все компоненты извлечены из V3
2. 🔄 **Legacy интеграция** - постепенное внедрение в прод
3. 🧪 **A/B тестирование** - сравнение old vs new компонентов
4. 🚀 **Full rollout** - полный переход на новый UI

---

*Этот экспорт создан для ускорения перехода на современный UI без риска поломки стабильной бизнес-логики.*