# 🚀 RECEPTOR PRO - План вывода на рынок

**Дата:** 2025-01-XX  
**Production URL:** https://receptorai.pro  
**Статус:** ✅ Работает, требует доработок

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### ✅ Что работает отлично:
- ✅ V2 генерация техкарт (29s, production quality)
- ✅ IIKO RMS интеграция (2,831 продуктов)
- ✅ Автомаппинг SKU (95-100% accuracy)
- ✅ Real-time пересчет КБЖУ и цен
- ✅ Google OAuth авторизация
- ✅ Экспорт в IIKO форматы (XLSX, ZIP)

### ⚠️ Что требует доработки:
- ⚠️ SKU mappings не сохраняются после автомаппинга
- ⚠️ Converted V2 теряется в UI после конвертации
- ⚠️ КБЖУ overcalculation (нужна проверка)
- ⚠️ TestSprite coverage 50% (2/4 passed)

---

## 🎯 ПЛАН ДЕЙСТВИЙ (Приоритеты)

### 🔴 PHASE 1: Критичные фиксы (1-2 дня)

#### 1.1 Фикс SKU Persistence
**Проблема:** Маппинги работают, но не сохраняются в MongoDB

**Решение:**
```python
# backend/receptor_agent/routes/techcards_v2.py
# После auto-mapping добавить:
await db.techcards_v2.update_one(
    {"meta.id": techcard_id},
    {"$set": {"ingredients": mapped_ingredients}}
)
```

**Файлы:**
- `backend/receptor_agent/routes/techcards_v2.py`

#### 1.2 Фикс V2 State After Conversion
**Проблема:** После конвертации V1→V2 техкарта теряется в UI

**Решение:**
```javascript
// frontend/src/App.js
// После успешной конвертации:
setTcV2(response.data.techcard);
setCurrentTechCardId(response.data.techcard.meta.id); // ADD THIS!
```

**Файлы:**
- `frontend/src/App.js` (найти handler конвертации)

#### 1.3 Проверка КБЖУ Calculation
**Проблема:** Overcalculation (4669 kcal вместо ~700)

**Действие:**
- Проверить `backend/receptor_agent/techcards_v2/nutrition_calculator.py`
- Проверить portion sizes и multipliers

---

### 🟡 PHASE 2: Подготовка к запуску (2-3 дня)

#### 2.1 Onboarding для новых пользователей
**Что:** 4-step onboarding flow

**Готовые модули:**
- ✅ `receptor-v3-ui-export/components/Onboarding/`
- ✅ `receptor-v3-ui-export/hooks/useOnboarding.ts`

**Интеграция:**
1. Скопировать компоненты в `frontend/src/components/`
2. Интегрировать в `App.js`
3. Добавить localStorage check для first-time users

**Ожидаемый эффект:** +40% retention новых пользователей

#### 2.2 Monetization Setup (YooKassa)
**Что:** Интеграция платежей для российского рынка

**Готовые модули:**
- ✅ `receptor-v3-ui-export/services/billingApi.ts`
- ✅ `receptor-v3-ui-export/components/PricingPage.tsx`

**Backend endpoints:**
```python
@api_router.post("/yookassa/checkout")
async def create_yookassa_checkout(package_id: str, user_id: str):
    # Create YooKassa payment
    # Return confirmation_url

@api_router.post("/yookassa/webhook")
async def yookassa_webhook(payment_data: dict):
    # Handle payment.succeeded
    # Activate PRO for user
```

**Цены:**
- PRO: 1990₽/месяц или 19900₽/год

#### 2.3 Bug Report System
**Что:** Gamified система отчетов об ошибках

**Готовые модули:**
- ✅ `receptor-v3-ui-export/components/BugReport/`
- ✅ Token rewards: 5-50 за отчет

**Интеграция:**
1. Добавить floating button "🐛 Сообщить о баге"
2. Backend endpoint для сохранения отчетов
3. Награждение токенами пользователей

---

### 🟢 PHASE 3: Полировка и оптимизация (3-5 дней)

#### 3.1 App.js Modularization
**Текущее:** 19,474 строк в одном файле

**Цель:** Разбить на модули:
- `components/TechCardGenerator/`
- `components/AIKitchen/`
- `components/Export/`
- `components/Layout/`

**Стратегия:** Постепенная миграция с feature flags

#### 3.2 Performance Optimization
**Текущее:**
- Tech card generation: 29s ✅
- Auto-mapping: 10s ✅
- IIKO search: 1-3s ✅

**Улучшения:**
- Redis caching для IIKO catalog
- Lazy load AI tools modals
- Code splitting для bundle size
- Service worker для offline mode

#### 3.3 Documentation
**Нужно:**
- User manual (PDF)
- Video tutorials
- FAQ page
- IIKO import guide

---

## 📋 CHECKLIST ДЛЯ ЗАПУСКА

### Pre-Launch (Must Have):
- [ ] Фикс SKU persistence
- [ ] Фикс V2 state после конвертации
- [ ] Проверка КБЖУ calculation
- [ ] Onboarding интегрирован
- [ ] YooKassa setup (test mode)
- [ ] Bug report button добавлен
- [ ] Error tracking (Sentry)
- [ ] Analytics configured
- [ ] Legal pages (Terms, Privacy)
- [ ] Support email setup

### Nice to Have:
- [ ] App.js refactored
- [ ] 100% test coverage
- [ ] Full documentation
- [ ] Mobile app (future)

---

## 🎯 МЕТРИКИ УСПЕХА

### Technical KPIs:
- ✅ ZIP export success rate >95%
- ✅ Auto-mapping coverage >90%
- ✅ Page load time <2s
- ✅ No critical errors in production

### Business KPIs:
- 🎯 Onboarding completion >70%
- 🎯 Free→PRO conversion >5%
- 🎯 User retention (weekly) >60%
- 🎯 Average revenue per user >1000₽/month

### User Experience:
- 🎯 NPS score >50
- 🎯 Support requests <2% of users
- 🎯 Time to first success <10 minutes

---

## 🚀 БЫСТРЫЙ СТАРТ (Сегодня-Завтра)

### Сегодня (2-3 часа):
1. ✅ Фикс SKU persistence в backend
2. ✅ Фикс V2 state в frontend
3. ✅ Проверка КБЖУ calculation
4. ✅ Commit & push changes

### Завтра (4-6 часов):
5. ✅ Интеграция Onboarding
6. ✅ YooKassa test mode setup
7. ✅ Bug report button
8. ✅ Deploy на production

### На неделе:
9. ✅ Тестирование с реальными пользователями
10. ✅ Сбор feedback
11. ✅ Итерации на основе feedback
12. ✅ Подготовка к публичному запуску

---

## 💰 БИЗНЕС-МОДЕЛЬ

### Pricing Tiers:
- **FREE:** 5 техкарт/месяц
- **PRO:** Unlimited техкарты + IIKO integration (1990₽/мес или 19900₽/год)
- **Enterprise:** Multi-user + API access (по запросу)

### Revenue Projections:
- Month 1: 50-100 users → 10-15 PRO (20k-30k₽)
- Month 3: 500 users → 100 PRO (200k₽/month)
- Month 6: IIKO partnership → 5,000 users → 1,000 PRO (2M₽/month)

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

**Что выбираем?**

**A. Быстрый Launch (MVP)**
- Фиксы критичных багов
- Базовый onboarding
- YooKassa setup
- Запуск для первых 10-20 пользователей

**B. Production-Ready**
- Все фиксы + рефакторинг
- Полная документация
- 100% test coverage
- Enterprise features

**C. Revenue-First**
- Monetization setup
- Marketing campaign
- Customer acquisition
- Scale что работает

**Рекомендация:** Гибридный подход (A + C) - быстрый запуск с monetization

---

**Готов помочь с любым из этих путей! 💪**



