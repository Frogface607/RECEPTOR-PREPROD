# 🔧 Руководство по интеграции в Legacy

## 📋 Подготовка

### 1. Копирование файлов
```bash
# Скопировать всю папку в legacy проект
cp -r /path/to/receptor-v3-ui-export ./src/v3-components

# Или разместить в отдельной папке
mkdir src/components-v3
cp -r /path/to/receptor-v3-ui-export/* ./src/components-v3/
```

### 2. Установка зависимостей
```bash
# Если используете новые пакеты
npm install @types/react @types/react-dom
# или yarn add @types/react @types/react-dom
```

### 3. Настройка путей (опционально)
```js
// В tsconfig.json или jsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@v3/*": ["./src/components-v3/*"]
    }
  }
}
```

---

## 🚀 Интеграция по этапам

### Этап 1: Layout System

#### 1.1 Замена Header
```jsx
// В вашем App.js/App.tsx
import { Header } from './v3-components/components/Layout/Header'
import { useFeatureFlags } from './v3-components/utils/featureFlags'

function App() {
  const { isEnabled } = useFeatureFlags()
  
  return (
    <div className="app">
      {isEnabled('new_header') ? 
        <Header 
          user={currentUser}
          onLogout={handleLogout}
          showBugReport={true}
        /> : 
        <OldHeader />
      }
      {/* rest of app */}
    </div>
  )
}
```

#### 1.2 Добавление Sidebar
```jsx
import { Sidebar } from './v3-components/components/Layout/Sidebar'

function Layout({ children }) {
  const { isEnabled } = useFeatureFlags()
  
  return (
    <div className="flex">
      {isEnabled('new_sidebar') && (
        <Sidebar 
          currentPath={location.pathname}
          userPlan={user.plan}
          onNavigate={navigate}
        />
      )}
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}
```

#### 1.3 Глобальные стили
```jsx
// В корневом файле (App.js, index.js)
import './v3-components/styles/globals.css'
import './v3-components/styles/colors.css'
import './v3-components/styles/typography.css'
```

---

### Этап 2: User Plan Context

#### 2.1 Обертка приложения в UserPlanProvider
```jsx
import { UserPlanProvider } from './v3-components/contexts/UserPlanContext'

function App() {
  return (
    <UserPlanProvider>
      {/* ваше приложение */}
    </UserPlanProvider>
  )
}
```

#### 2.2 Использование в компонентах
```jsx
import { useUserPlan } from './v3-components/contexts/UserPlanContext'

function SomeComponent() {
  const { isPro, canUse, upgradeUser } = useUserPlan()
  
  return (
    <div>
      {isPro ? (
        <ProFeature />
      ) : (
        <button onClick={upgradeUser}>
          Upgrade to PRO
        </button>
      )}
    </div>
  )
}
```

---

### Этап 3: Onboarding для новых пользователей

#### 3.1 Добавление OnboardingModal
```jsx
import { OnboardingModal } from './v3-components/components/Onboarding/OnboardingModal'
import { useOnboarding } from './v3-components/hooks/useOnboarding'

function App() {
  const { 
    isVisible, 
    currentStep, 
    completeOnboarding, 
    nextStep, 
    prevStep 
  } = useOnboarding()
  
  return (
    <>
      {/* основное приложение */}
      <MainApp />
      
      {/* онбординг модал */}
      {isVisible && (
        <OnboardingModal
          currentStep={currentStep}
          onNext={nextStep}
          onPrev={prevStep}
          onComplete={completeOnboarding}
        />
      )}
    </>
  )
}
```

#### 3.2 Настройка условий показа
```jsx
// В useOnboarding хуке можно настроить логику:
const shouldShowOnboarding = () => {
  // Показывать только новым пользователям
  return !user.hasCompletedOnboarding && isFirstVisit
}
```

---

### Этап 4: PRO Upgrade Flow

#### 4.1 Страница тарифов
```jsx
import { PricingPage } from './v3-components/components/PricingPage'

// В роутинге
<Route path="/pricing" component={PricingPage} />

// Или как отдельная страница
function PricingPageWrapper() {
  return (
    <Layout>
      <PricingPage 
        currentPlan={user.plan}
        onUpgrade={handleUpgrade}
      />
    </Layout>
  )
}
```

#### 4.2 Billing API интеграция
```jsx
import { billingApi } from './v3-components/services/billingApi'

const handleUpgrade = async () => {
  try {
    const checkout = await billingApi.createCheckout({
      plan: 'pro',
      userId: user.id,
      amount: 990
    })
    
    // Redirect to YooKassa
    window.location.href = checkout.confirmation.confirmation_url
  } catch (error) {
    console.error('Upgrade failed:', error)
  }
}
```

#### 4.3 Обработка успешной оплаты
```jsx
// В компоненте обработки success redirect
import { useEffect } from 'react'
import { billingApi } from './v3-components/services/billingApi'

function PaymentSuccess() {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.get('status') === 'success') {
      // Обновить статус пользователя
      billingApi.confirmPayment(urlParams.get('payment_id'))
        .then(() => {
          // Redirect to dashboard with PRO features
          navigate('/dashboard?upgraded=true')
        })
    }
  }, [])
  
  return <div>Обрабатываем платеж...</div>
}
```

---

### Этап 5: TechCard Components

#### 5.1 Замена отображения техкарт
```jsx
import { TechCardView } from './v3-components/components/TechCard/TechCardView'

function TechCardPage({ techCardId }) {
  const [techCard, setTechCard] = useState(null)
  
  // Загрузка данных...
  
  return (
    <TechCardView
      techCard={techCard}
      onSave={handleSave}
      onExport={handleExport}
      showActions={true}
    />
  )
}
```

#### 5.2 Использование IngredientsTable
```jsx
import { IngredientsTable } from './v3-components/components/TechCard/IngredientsTable'

function EditTechCard({ techCard, onChange }) {
  const handleIngredientsChange = (newIngredients) => {
    onChange({
      ...techCard,
      ingredients: newIngredients
    })
  }
  
  return (
    <div>
      <h2>Ингредиенты</h2>
      <IngredientsTable
        ingredients={techCard.ingredients}
        onChange={handleIngredientsChange}
        editable={true}
      />
    </div>
  )
}
```

---

### Этап 6: Utility Components

#### 6.1 ErrorBoundary
```jsx
import { ErrorBoundary } from './v3-components/components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary fallback={<ErrorFallback />}>
      <MainApp />
    </ErrorBoundary>
  )
}

function ErrorFallback() {
  return (
    <div className="error-fallback">
      <h2>Что-то пошло не так</h2>
      <button onClick={() => window.location.reload()}>
        Перезагрузить страницу
      </button>
    </div>
  )
}
```

#### 6.2 Bug Report System
```jsx
import { BugReportModal } from './v3-components/components/BugReport/BugReportModal'
import { useState } from 'react'

function App() {
  const [showBugReport, setShowBugReport] = useState(false)
  
  return (
    <>
      <MainApp />
      
      {/* Кнопка для вызова багрепорта */}
      <button 
        className="fixed bottom-4 right-4 bg-red-500 text-white p-3 rounded-full"
        onClick={() => setShowBugReport(true)}
      >
        🐛 Сообщить о баге
      </button>
      
      {/* Модал багрепорта */}
      {showBugReport && (
        <BugReportModal
          onClose={() => setShowBugReport(false)}
          onSubmit={handleBugReport}
        />
      )}
    </>
  )
}
```

---

## 🎛️ Feature Flags

### Настройка feature flags
```jsx
// В v3-components/utils/featureFlags.js
export const DEFAULT_FLAGS = {
  new_header: true,
  new_sidebar: false,
  onboarding_v3: true,
  pro_billing: true,
  bug_report_system: true,
  techcard_v3_view: false,
  export_master: false
}

// Использование в компонентах
import { useFeatureFlags } from './v3-components/utils/featureFlags'

function SomeComponent() {
  const { isEnabled } = useFeatureFlags()
  
  return (
    <>
      {isEnabled('techcard_v3_view') ? (
        <TechCardViewV3 />
      ) : (
        <TechCardViewLegacy />
      )}
    </>
  )
}
```

---

## 🧪 A/B тестирование

### Постепенный rollout
```jsx
// Канареечное развертывание
export const getCanaryFlag = (flagName, percentage) => {
  const userId = getCurrentUserId()
  const hash = hashString(userId + flagName)
  return (hash % 100) < percentage
}

// В featureFlags.js
export const DEFAULT_FLAGS = {
  new_header: getCanaryFlag('new_header', 50), // 50% пользователей
  new_sidebar: getCanaryFlag('new_sidebar', 25), // 25% пользователей
  // ...
}
```

---

## 🚀 Production Checklist

### Перед выкладкой в прод:

- [ ] Все новые компоненты протестированы изолированно
- [ ] Feature flags настроены для постепенного rollout
- [ ] CSS стили не конфликтуют с legacy стилями  
- [ ] API endpoints совместимы с legacy backend
- [ ] Error boundaries установлены вокруг новых компонентов
- [ ] Fallback'и настроены на случай ошибок
- [ ] Аналитика настроена для трекинга использования новых фич
- [ ] Performance проверен (bundle size, loading time)

### Мониторинг после выкладки:

- [ ] Error rate в новых компонентах
- [ ] User engagement с новыми фичами
- [ ] Conversion rate в PRO upgrade flow
- [ ] Performance metrics (FCP, LCP, CLS)
- [ ] Обратная связь пользователей через bug report систему

---

## 🆘 Troubleshooting

### Частые проблемы:

**1. Конфликт CSS стилей**
```css
/* Изолируйте V3 стили */
.v3-component {
  /* V3 styles here */
}
```

**2. TypeScript ошибки**
```tsx
// Добавьте type definitions
declare module './v3-components/*'
```

**3. API совместимость**  
```jsx
// Используйте адаптеры
const adaptLegacyTechCard = (legacyCard) => ({
  ...legacyCard,
  // конвертация в V3 формат
})
```

**4. Bundle size**
```jsx
// Ленивая загрузка компонентов
const OnboardingModal = lazy(() => 
  import('./v3-components/components/Onboarding/OnboardingModal')
)
```

Этот гайд поможет интегрировать V3 компоненты безопасно и постепенно!