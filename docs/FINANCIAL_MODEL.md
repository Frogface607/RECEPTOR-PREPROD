# RECEPTOR Tools — Financial Model

**Version:** 1.0 | **Date:** 2026-03-29 | **Currency:** RUB (USD rate assumed: 1 USD = 90 RUB)

---

## 1. Unit Economics Per User

### 1.1 LLM API Cost Per Tool Use

| Parameter | Value |
|-----------|-------|
| Average input tokens per call | 500 |
| Average output tokens per call | 1,500 |
| Input token cost (gpt-4o-mini via OpenRouter) | $0.00015 / 1K tokens |
| Output token cost (gpt-4o-mini via OpenRouter) | $0.0006 / 1K tokens |
| Input token cost (claude-3.5-sonnet via OpenRouter) | $0.003 / 1K tokens |
| Output token cost (claude-3.5-sonnet via OpenRouter) | $0.015 / 1K tokens |

**Cost per single tool use:**

| Model | Input Cost | Output Cost | Total (USD) | Total (RUB) |
|-------|-----------|-------------|-------------|-------------|
| gpt-4o-mini | $0.000075 | $0.0009 | **$0.000975** | **0.088 ₽** |
| claude-3.5-sonnet | $0.0015 | $0.0225 | **$0.024** | **2.16 ₽** |

**Blended cost assumption:** 80% gpt-4o-mini + 20% claude-3.5-sonnet (heavy tasks only)

| Blended metric | Value |
|----------------|-------|
| Blended cost per use (USD) | $0.000975 * 0.8 + $0.024 * 0.2 = **$0.00558** |
| Blended cost per use (RUB) | **0.50 ₽** |

### 1.2 Monthly Cost Per User (30 uses/month)

| Item | Calculation | RUB |
|------|-------------|-----|
| LLM API cost (30 uses) | 30 * 0.50 ₽ | **15.00 ₽** |
| Server cost allocation (at 1,000 users) | ~5,000 ₽ / 1,000 | **5.00 ₽** |
| **Total variable cost per user** | | **20.00 ₽** |

### 1.3 Margin at 500 ₽/month Subscription

| Metric | Value |
|--------|-------|
| Revenue per user | 500 ₽ |
| Variable cost per user | 20 ₽ |
| **Gross margin per user** | **480 ₽ (96%)** |
| Gross margin if user does 100 uses/month | 500 - 50 - 5 = **445 ₽ (89%)** |
| Gross margin if user does 300 uses/month (power user) | 500 - 150 - 5 = **345 ₽ (69%)** |

**Key insight:** Even heavy users (300 uses/month) remain profitable. LLM costs are well-controlled when routing 80%+ of calls through gpt-4o-mini.

---

## 2. Revenue Projections (3 Scenarios)

### Subscription: 500 ₽/month

**User growth trajectory (paid subscribers):**

| Month | Conservative | Moderate | Optimistic |
|-------|-------------|----------|-----------|
| 1 | 100 | 300 | 1,000 |
| 2 | 150 | 500 | 1,800 |
| 3 | 200 | 750 | 2,800 |
| 4 | 270 | 950 | 3,800 |
| 5 | 370 | 1,200 | 4,800 |
| 6 | 500 | 1,500 | 5,000 |
| 7 | 570 | 1,900 | 7,000 |
| 8 | 650 | 2,400 | 9,000 |
| 9 | 730 | 3,000 | 12,000 |
| 10 | 820 | 3,600 | 15,000 |
| 11 | 910 | 4,300 | 17,500 |
| 12 | 1,000 | 5,000 | 20,000 |

### Monthly Revenue (₽):

| Month | Conservative | Moderate | Optimistic |
|-------|-------------|----------|-----------|
| 1 | 50,000 | 150,000 | 500,000 |
| 3 | 100,000 | 375,000 | 1,400,000 |
| 6 | 250,000 | 750,000 | 2,500,000 |
| 9 | 365,000 | 1,500,000 | 6,000,000 |
| 12 | 500,000 | 2,500,000 | 10,000,000 |

### Cumulative Revenue — Year 1 (₽):

| Scenario | Total Year 1 Revenue | Avg Monthly Revenue |
|----------|---------------------|-------------------|
| Conservative | ~3,000,000 ₽ | 250,000 ₽ |
| Moderate | ~12,000,000 ₽ | 1,000,000 ₽ |
| Optimistic | ~50,000,000 ₽ | 4,170,000 ₽ |

### Annual Recurring Revenue (ARR) at Month 12:

| Scenario | MRR (Month 12) | ARR |
|----------|----------------|-----|
| Conservative | 500,000 ₽ | 6,000,000 ₽ |
| Moderate | 2,500,000 ₽ | 30,000,000 ₽ |
| Optimistic | 10,000,000 ₽ | 120,000,000 ₽ |

---

## 3. Cost Structure

### 3.1 Fixed Costs (Monthly)

| Item | Free Tier | Growth (500 users) | Scale (5,000 users) |
|------|-----------|-------------------|---------------------|
| **Hosting — Frontend** | | | |
| Vercel (Hobby → Pro → Enterprise) | 0 ₽ | 1,800 ₽ ($20) | 9,000 ₽ ($100) |
| **Hosting — Backend** | | | |
| Render (Free → Starter → Standard) | 0 ₽ | 630 ₽ ($7) | 2,250 ₽ ($25) |
| Additional Render workers | 0 ₽ | 0 ₽ | 4,500 ₽ ($50) |
| **Database** | | | |
| MongoDB Atlas (Free → M10 → M30) | 0 ₽ | 5,130 ₽ ($57) | 18,000 ₽ ($200) |
| **Domain & DNS** | | | |
| Domain (.ru or .com) | 125 ₽/mo amort. | 125 ₽ | 125 ₽ |
| Cloudflare CDN/DNS | 0 ₽ | 0 ₽ | 1,800 ₽ ($20 Pro) |
| **Monitoring** | | | |
| Sentry (free → team) | 0 ₽ | 0 ₽ | 2,340 ₽ ($26) |
| **Payment Processing** | | | |
| YooKassa commission (3.5% of revenue) | variable | variable | variable |
| **Total Fixed Infrastructure** | **~125 ₽** | **~7,685 ₽** | **~38,015 ₽** |

### 3.2 Variable Costs Per User (Monthly)

| Item | 30 uses/mo | 50 uses/mo | 100 uses/mo |
|------|-----------|-----------|------------|
| LLM API (blended) | 15 ₽ | 25 ₽ | 50 ₽ |
| Tavily search calls (est. 5/mo) | 2 ₽ | 3 ₽ | 5 ₽ |
| Server marginal cost | 5 ₽ | 5 ₽ | 5 ₽ |
| YooKassa fee (3.5% of 500₽) | 17.5 ₽ | 17.5 ₽ | 17.5 ₽ |
| **Total variable per user** | **39.5 ₽** | **50.5 ₽** | **77.5 ₽** |

### 3.3 Marketing Costs

| Channel | CPC / Unit Cost | CAC Estimate | Notes |
|---------|----------------|-------------|-------|
| Yandex.Direct (restaurant keywords) | 30-80 ₽ CPC | 1,500-4,000 ₽ | "автоматизация ресторана", "управление меню" |
| Telegram channels (HoReCa) | 5,000-15,000 ₽/post | 500-1,500 ₽ | Targeted communities |
| Content marketing (SEO) | 0 ₽ (time only) | 200-500 ₽ | Long-tail, 3-6 month payoff |
| Referral program (give 1 mo free) | 500 ₽ | 500 ₽ | Best channel long term |
| Industry events / RestoForum | 50,000 ₽/event | 2,000-5,000 ₽ | Brand awareness |

**Recommended starting budget:** 50,000-100,000 ₽/month

**Target blended CAC:** 1,500 ₽ (3 months to payback at 500 ₽/mo)

---

## 4. Break-Even Analysis

### 4.1 Cost Summary

| Cost Category | Amount (Monthly) |
|---------------|-----------------|
| Fixed infrastructure (Growth tier) | 7,685 ₽ |
| Marketing budget | 75,000 ₽ |
| Founder salary equivalent | 0 ₽ (bootstrapped) |
| **Total fixed costs** | **82,685 ₽** |

| Per-User Variable | Amount |
|-------------------|--------|
| LLM + API costs | 17 ₽ |
| Payment processing (3.5%) | 17.5 ₽ |
| Server marginal | 5 ₽ |
| **Total variable per user** | **39.5 ₽** |

### 4.2 Contribution Margin

| Metric | Value |
|--------|-------|
| Revenue per user | 500 ₽ |
| Variable cost per user | 39.5 ₽ |
| **Contribution margin** | **460.5 ₽ (92.1%)** |

### 4.3 Break-Even Point

```
Break-even users = Fixed Costs / Contribution Margin
                 = 82,685 / 460.5
                 = 180 paid users
```

| Scenario | Fixed Costs | Break-Even Users | When Reached? |
|----------|-------------|-----------------|---------------|
| Bootstrap (no marketing) | 7,685 ₽ | **17 users** | Month 1 |
| With 50K marketing | 57,685 ₽ | **126 users** | Month 1-2 |
| With 100K marketing | 107,685 ₽ | **234 users** | Month 2-3 |
| With salary (150K) + marketing | 232,685 ₽ | **506 users** | Month 3-6 |

### 4.4 Profitability Timeline

| Scenario | Month to Profitability | Monthly Profit at Month 12 |
|----------|----------------------|---------------------------|
| Conservative | Month 3-4 | 500*460.5 - 82,685 = **147,565 ₽** |
| Moderate | Month 1-2 | 5,000*460.5 - 107,685 = **2,194,815 ₽** |
| Optimistic | Month 1 | 20,000*460.5 - 157,685 = **9,052,315 ₽** |

---

## 5. Pricing Strategy Analysis

### Option A: Flat 500 ₽/month Unlimited

| Metric | Value |
|--------|-------|
| Simplicity | Excellent — easy to communicate |
| Revenue per user | 500 ₽ guaranteed |
| Risk | Power users (300+ uses) cut margins to ~69% |
| Support overhead | Low — no usage tracking disputes |
| Conversion from free | Moderate — price feels fair |

**Projected revenue (1,000 users):** 500,000 ₽/month

### Option B: 300 ₽/month + 50 uses + 10 ₽/extra

| Metric | Value |
|--------|-------|
| Base revenue per user | 300 ₽ |
| Avg user (30 uses) | 300 ₽ (stays within limit) |
| Power user (100 uses) | 300 + 50*10 = 800 ₽ |
| Heavy user (300 uses) | 300 + 250*10 = 2,800 ₽ |
| Support overhead | **High** — billing disputes, "why am I charged extra?" |
| Conversion from free | Higher — lower entry point |
| Complexity | Needs usage tracking UI, notifications, overage billing |

**Projected revenue (1,000 users, mixed):**
- 700 light users * 300 = 210,000
- 200 moderate users * 500 = 100,000
- 100 power users * 1,000 = 100,000
- **Total: 410,000 ₽/month** (less than Option A, more complexity)

### Option C: Freemium — 5 free/day then 500 ₽ Unlimited

| Metric | Value |
|--------|-------|
| Free tier cost (5 uses/day * 0.50₽ * 30 days) | 75 ₽/user/month |
| Conversion rate (industry avg) | 2-5% |
| Funnel: 10,000 free -> 300 paid | 150,000 ₽/month revenue |
| Free tier server cost (10K users) | ~75,000 ₽ LLM + hosting |
| Support overhead | Low on paid, zero on free |
| Viral potential | **Highest** — no barrier to try |

**Projected revenue (10K free, 500 paid):** 250,000 ₽ - 75,000 ₽ free tier cost = **175,000 ₽ net**

### Recommendation Matrix

| Criteria | Option A (500₽ flat) | Option B (300₽ + overage) | Option C (Freemium) |
|----------|---------------------|--------------------------|-------------------|
| Revenue per 1K users | 500,000 ₽ | 410,000 ₽ | 250,000 ₽* |
| Support overhead | Low | High | Low |
| Engineering complexity | Low | High | Medium |
| Conversion clarity | Clear | Confusing | Clear |
| Margin safety | Good | Best (power users pay more) | Risky |
| Growth potential | Moderate | Low | Highest |

*at 5% conversion; increases significantly with scale

### RECOMMENDED STRATEGY: Hybrid A+C

**Launch with:**
1. **Free tier:** 5 uses/day, no registration required (for viral spread)
2. **PRO tier:** 500 ₽/month unlimited (clear upgrade path)
3. **Phase 2 (Month 6+):** Add annual plan at 4,990 ₽/year (save 2 months)

**Why this maximizes revenue with minimal support:**
- Free tier creates product-led growth loop (restaurant workers share tools with colleagues)
- No overage billing = zero billing support tickets
- 500 ₽/month is below decision threshold for most restaurant managers (~$5.50/month)
- Annual plan improves retention and cash flow

---

## 6. Financial Summary — Year 1 (Moderate Scenario)

| Quarter | Paid Users | MRR | LLM Costs | Infra | Marketing | Net Profit |
|---------|-----------|-----|-----------|-------|-----------|-----------|
| Q1 | 300→750 | 250,000 | 10,500 | 7,685 | 75,000 | **156,815** |
| Q2 | 750→1,500 | 562,500 | 21,000 | 7,685 | 100,000 | **433,815** |
| Q3 | 1,500→3,000 | 1,125,000 | 42,000 | 15,000 | 125,000 | **943,000** |
| Q4 | 3,000→5,000 | 2,000,000 | 70,000 | 25,000 | 150,000 | **1,755,000** |
| **Year 1** | | **~12M ₽** | **~430K ₽** | **~165K ₽** | **~1.35M ₽** | **~3.3M ₽** |

Note: MRR shown is average for the quarter. Net profit excludes founder compensation and taxes.

---

## 7. Key Metrics to Track

| Metric | Target |
|--------|--------|
| CAC (Customer Acquisition Cost) | < 1,500 ₽ |
| LTV (Lifetime Value, 8-month avg retention) | 4,000 ₽ |
| LTV:CAC ratio | > 3:1 |
| Monthly churn rate | < 8% |
| Free-to-paid conversion | > 3% |
| Avg uses per user/month | 25-40 |
| LLM cost as % of revenue | < 5% |
| Gross margin | > 90% |
| Payback period | < 3 months |

---

## 8. Sensitivity Analysis

### What if average uses/month is higher than expected?

| Avg Uses/Month | LLM Cost/User | Margin | Break-Even (w/ 100K marketing) |
|---------------|--------------|--------|-------------------------------|
| 30 (baseline) | 15 ₽ | 92% | 234 users |
| 50 | 25 ₽ | 90% | 241 users |
| 100 | 50 ₽ | 84% | 259 users |
| 200 | 100 ₽ | 72% | 295 users |
| 500 (abuse) | 250 ₽ | 48% | 430 users |

**Mitigation:** Implement soft rate limit at 200 uses/day. Block automated/bot traffic. Monitor per-user cost weekly.

### What if model prices change?

| Scenario | Blended Cost/Use | Impact on Margins |
|----------|-----------------|------------------|
| Prices drop 50% (likely by 2027) | 0.25 ₽ | Margin improves to 95%+ |
| Prices increase 2x | 1.00 ₽ | Margin still 88% at 30 uses |
| Forced to use claude-3.5-sonnet only | 2.16 ₽ | Margin drops to 73% at 30 uses |

**Conclusion:** Business model is robust even under adverse LLM pricing scenarios.

---

## 9. Existing Pricing Context (from codebase)

The current RECEPTOR billing setup (in `billingApi.ts`) shows:
- **PRO Monthly RU:** 1,990 ₽ — positioned as full copilot platform
- **PRO Annual RU:** 19,900 ₽ — 2 months free
- **PRO Monthly USD:** $29 — international tier
- **PRO Annual USD:** $290 — international tier

**Recommendation for RECEPTOR Tools (micro-tools product):**
Position at **500 ₽/month** as a separate, lighter product distinct from the full 1,990 ₽ RECEPTOR PRO copilot. This creates a natural upgrade funnel:

```
Free (5 uses/day) → Tools PRO (500 ₽/mo) → RECEPTOR PRO (1,990 ₽/mo)
```

This three-tier approach captures the entire market from individual cooks to restaurant chain operators.
