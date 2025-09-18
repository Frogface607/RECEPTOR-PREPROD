# 📋 Детальное описание компонентов

## 🎨 Layout System

### Header.tsx
**Назначение:** Современный хедер с навигацией и пользовательским меню

**Фичи:**
- Адаптивная навигация
- Индикатор PRO статуса
- Быстрый доступ к багрепорту
- Выпадающее меню профиля

**Пропсы:**
```tsx
interface HeaderProps {
  user?: User
  onLogout?: () => void
  showBugReport?: boolean
}
```

**Интеграция в legacy:**
```jsx
import { Header } from './receptor-v3-ui-export/components/Layout/Header'

<Header 
  user={currentUser} 
  onLogout={handleLogout}
  showBugReport={true} 
/>
```

---

### Sidebar.tsx  
**Назначение:** Боковая навигация с иконками и активными состояниями

**Фичи:**
- Коллапсирующаяся навигация
- Активные состояния для текущей страницы
- PRO-gating для премиум разделов
- Быстрые действия (создать техкарту)

**Использование:**
```jsx
import { Sidebar } from './receptor-v3-ui-export/components/Layout/Sidebar'

<Sidebar 
  currentPath="/techcards"
  userPlan="free" // or "pro"
  onNavigate={handleNavigate}
/>
```

---

## 🚀 Onboarding Flow

### OnboardingModal.tsx
**Назначение:** Главный компонент 4-шагового онбординга

**Шаги:**
1. Welcome - выбор роли
2. Setup - настройка профиля  
3. FirstSuccess - первая генерация (demo)
4. Explore - обзор возможностей

**Интеграция:**
```jsx
import { OnboardingModal } from './receptor-v3-ui-export/components/Onboarding'
import { useOnboarding } from './receptor-v3-ui-export/hooks'

const { isVisible, currentStep, completeOnboarding } = useOnboarding()

{isVisible && (
  <OnboardingModal 
    currentStep={currentStep}
    onComplete={completeOnboarding}
  />
)}
```

### WelcomeStep.tsx
**Назначение:** Приветственный экран с выбором роли

**Роли:**
- Шеф-повар (фокус на создании техкарт)
- Менеджер (фокус на планировании меню)
- Владелец (фокус на аналитике и прибыли)

### SetupStep.tsx
**Назначение:** Настройка профиля пользователя

**Поля:**
- Название заведения
- Тип кухни
- Размер команды
- Опыт работы

### FirstSuccessStep.tsx
**Назначение:** Демонстрация создания первой техкарты

**Особенности:**
- Интерактивная демо-генерация
- Объяснение каждого этапа
- Мотивация к дальнейшему использованию

### ExploreStep.tsx  
**Назначение:** Обзор ключевых возможностей системы

**Разделы:**
- Генерация техкарт с ИИ
- Библиотека и организация
- Экспорт и интеграции
- PRO возможности

---

## 💳 PRO Upgrade & Billing

### PricingPage.tsx
**Назначение:** Страница тарифных планов с YooKassa интеграцией

**Планы:**
- **Free:** базовая генерация, 10 техкарт
- **PRO:** безлимит, экспорт, интеграции, приоритет

**Фичи:**
- YooKassa Hosted Checkout
- Обработка success/cancel статусов
- Отображение текущего плана
- Upgrade/downgrade функционал

**YooKassa интеграция:**
```jsx
const handleUpgrade = async () => {
  const checkoutUrl = await billingApi.createCheckout({
    plan: 'pro',
    amount: 990,
    userId: user.id
  })
  window.location.href = checkoutUrl
}
```

### UpgradeModal.tsx (TODO)
**Назначение:** Быстрый upgrade modal внутри приложения

---

## 🍽️ TechCard Generation

### TechCardView.tsx
**Назначение:** Отображение готовой техкарты со всеми данными

**Секции:**
- Заголовок и основная информация
- Таблица ингредиентов  
- Шаги приготовления
- Пищевая ценность
- Калькуляция стоимости
- Кнопки действий (сохранить, экспорт)

**Пропсы:**
```tsx
interface TechCardViewProps {
  techCard: TechCardV2
  onSave?: (card: TechCardV2) => void
  onExport?: (format: string) => void
  showActions?: boolean
}
```

### TechCardGeneration.tsx (TODO)
**Назначение:** Форма создания новой техкарты

### IngredientsTable.tsx
**Назначение:** Интерактивная таблица ингредиентов

**Фичи:**
- Inline редактирование количества
- Автоматический пересчет стоимости
- Добавление/удаление ингредиентов
- Валидация данных

### ProcessSteps.tsx
**Назначение:** Отображение и редактирование шагов приготовления

**Фичи:**
- Нумерованные шаги
- Время приготовления каждого шага
- Температурные режимы
- Необходимое оборудование

### NutritionCard.tsx
**Назначение:** Карточка пищевой ценности

**Показатели:**
- Калории (на 100г и на порцию)
- Белки, жиры, углеводы
- Клетчатка
- Визуальные индикаторы

### SaveButton.tsx
**Назначение:** Кнопка сохранения с состояниями

**Состояния:**
- Default - готов к сохранению
- Loading - процесс сохранения  
- Success - успешно сохранено
- Error - ошибка сохранения

---

## 🛠️ Utility Components

### ErrorBoundary.tsx
**Назначение:** Глобальная обработка ошибок React компонентов

**Фичи:**
- Fallback UI при краше компонентов
- Автоматический retry механизм
- Отправка ошибок в аналитику
- Dev/prod различные отображения

**Использование:**
```jsx
import { ErrorBoundary } from './receptor-v3-ui-export/components'

<ErrorBoundary fallback={<ErrorFallback />}>
  <App />
</ErrorBoundary>
```

### BugReportModal.tsx
**Назначение:** Геймифицированная система сбора багов

**Фичи:**
- Токены за баг-репорты (5-50 токенов)
- Приоритизация по важности
- Автоматический сбор контекста (URL, user agent, etc)
- Скриншоты и описания

**Типы багов:**
- UI проблемы (5 токенов)
- Функциональные ошибки (15 токенов)  
- Критические баги (50 токенов)

### TokensDisplay.tsx
**Назначение:** Отображение токенов пользователя

**Фичи:**
- Текущий баланс токенов
- История заработка
- Обменный курс (токены → скидки)

### ExportMaster.tsx
**Назначение:** Мастер экспорта техкарт

**Форматы:**
- PDF (базовый для всех)
- Excel (PRO)
- iiko RMS (PRO)
- ZIP архив (PRO)

**Настройки:**
- Выбор техкарт для экспорта
- Кастомизация шаблонов  
- Пакетный экспорт

---

## 🔗 Зависимости компонентов

### Обязательные для работы:
- React 18+
- TypeScript
- Tailwind CSS или аналогичная CSS система
- Axios для API запросов

### Необязательные улучшения:
- Framer Motion для анимаций
- React Query для кеширования API
- React Hook Form для форм
- Date-fns для работы с датами

---

## 🎯 Рекомендации по интеграции

### Пошаговая интеграция:

1. **Этап 1: Layout**
   - Header + Sidebar
   - Базовые стили
   - Навигация

2. **Этап 2: Onboarding**  
   - OnboardingModal для новых пользователей
   - Hooks для управления состоянием

3. **Этап 3: TechCard UI**
   - TechCardView вместо старого отображения
   - IngredientsTable для редактирования

4. **Этап 4: PRO Features**
   - PricingPage
   - Billing интеграция
   - Feature gating

5. **Этап 5: Utilities**
   - ErrorBoundary
   - BugReport система
   - ExportMaster

### Feature Flags для контроля:
```js
const flags = {
  new_header: true,
  new_sidebar: false, 
  onboarding_v3: true,
  pro_billing: false,
  bug_report_system: true
}
```

Каждый компонент можно включать постепенно и тестировать изолированно!