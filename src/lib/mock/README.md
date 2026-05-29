# lib/mock — Edison-shaped fixtures (Phase 1)

Realistic mock data that matches iiko OLAP response shapes so we can build the
full UI and `lib/ai/` tool-calls before iiko keys arrive.

Planned (Phase 1, TDD):
- `edison-fixtures.ts` — venue, organizations, nomenclature
- `edison-revenue.ts` — daily revenue, average check, periods
- `edison-dishes.ts` — top dishes, categories
- `edison-shifts.ts` — cashier shifts (зал/мангал/бар)
- `index.ts` — public `getMockX(period)` API mirroring real clients

Numbers are anchored on Edison reality:
- Daily revenue ₽150-300k (weekday/weekend swing)
- Top dishes: бургеры из «Нечто», крафт-пиво, авторские коктейли
- Categories: бургеры / пиво / коктейли / закуски / десерты
