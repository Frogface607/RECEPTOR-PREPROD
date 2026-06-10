# Venue Intelligence Roadmap

Receptor is not a generic sales dashboard. The product goal is an owner-grade
business intelligence system for restaurants: iiko facts + venue context +
clear management actions.

## Core Promise

For each venue, Receptor should answer:

- What happened with the business?
- Where are we losing money or attention?
- Which menu, shift, staff, guest, or context signal explains it?
- What should the owner or manager do today?

Every answer should follow:

1. Fact
2. Interpretation
3. Action
4. Missing data, if the conclusion needs more context

## Venue Intelligence Profile

The profile is the memory of a specific venue. It should be filled from:

- Owner questionnaire
- iiko facts
- Deep Research across maps, reviews, website, social pages
- Manual corrections by the owner or manager

Fields:

- Format and positioning
- Audience
- Strengths
- Guest pains
- Owner goals
- Operating risks
- Decision rules
- Recommended analytical focus

## BI Pillars

### Money

- Revenue by period
- Average check
- Items sold
- Period comparison
- Day-of-week pattern
- Forecast to end of day/week

### Menu

- Top dishes by revenue
- Top dishes by amount
- Category mix
- Weak categories
- Menu engineering: stars, plowhorses, puzzles, dogs
- Food cost and margin when tech cards/purchase data are available

### Team

- Shifts
- Cashiers/employees from iiko
- Sales by employee if reliable
- Data quality warnings when checks are closed by another person
- Bonus logic should be explicit and fair, not blindly inferred

### Guests

- Reviews and ratings
- Repeated complaints
- Strengths guests mention
- Service risks
- Value perception: price, portion, quality, waiting time

### Operations

- Stop-list and availability signals
- Schedule/staffing fit against demand
- Delivery/pickup profitability when channel data exists
- Inventory and write-offs when data exists

## Copilot Behavior

Copilot must use the Venue Intelligence Profile in every answer.

Good answer:

> Выручка просела на 12%, но проблема не в общем трафике: коктейли упали
> сильнее остальных категорий. Для вашего формата барная выручка важна как
> маржинальный слой. Сегодня: проверь стоп-лист бара, поставь официантам фокус
> на 2 коктейля и сравни вечернюю смену с прошлой пятницей.

Bad answer:

> Выручка составила 100 000 ₽. Топ блюд: бургер, салат, суп.

## First Implementation Slice

Implemented:

- `VenueIntelligenceProfile` domain model
- Default pilot profile for sandbox
- Dashboard card: goals, risks, Copilot focus
- Copilot prompt receives profile context
- Mock Copilot uses profile warnings in revenue, menu and shift answers
- `get_owner_brief` tool combines revenue, menu, categories and shifts into
  risks/actions for owner-level questions
- SQL migration placeholder for `venues.intelligence_profile`

## Next Implementation Slice

1. Add owner questionnaire to onboarding/settings.
2. Add `/api/venue/research` using OpenAI/Perplexity-style web research.
3. Store `intelligence_profile` in Supabase `venues`.
4. Add model routing: cheap model for simple tool answers, premium model for
   Deep Research and strategic owner brief synthesis.
5. Add menu engineering view once margin/food-cost data exists.
6. Add review intelligence module from MyReply.
