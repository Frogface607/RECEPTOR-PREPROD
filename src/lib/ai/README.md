# lib/ai — Anthropic Claude tool-calling (Phase 4)

Replaces v1's 1656-line keyword intent-routing chat.py with proper tool-calls.

Planned (Phase 4, TDD):
- `system-prompt.ts` — short system prompt (from spec §AI Chat)
- `tools/` — 6 BI tool definitions:
  - `get_revenue.ts`
  - `get_dish_statistics.ts`
  - `get_shifts.ts`
  - `get_olap_report.ts`
  - `compare_periods.ts`
  - `get_nomenclature_search.ts`
- `client.ts` — Anthropic SDK wrapper with tool-call loop
- `streaming.ts` — Vercel AI SDK / SSE for chat UI streaming

Each tool dispatches to `lib/iiko/client.ts` so mock and real backends are
transparent to Claude.

Limits enforcement (per plan tier): Free 10 msg/day, Pro 200/day, Team unlimited.
