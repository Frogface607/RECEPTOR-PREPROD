# Receptor v2

AI-копайлот владельца ресторана. Подключение к iiko (Cloud + RMS) → BI dashboard + AI-чат с tool-calling над OLAP данными.

**Status:** Phase 0 (scaffold) → mock-first build. Live: [receptorai.pro](https://www.receptorai.pro).

## Stack

- **Next.js 16** (App Router, Turbopack) · React 19 · TypeScript 5 · Tailwind 4
- **shadcn/ui** (`base-nova` style, `@base-ui/react`) · Recharts 3 · lucide-react
- **Supabase** (Auth + Postgres) — keys arrive after 31 May 2026
- **Anthropic Claude** (tool-calling) + OpenRouter (fallback)
- **Vitest** + Testing Library (jsdom)
- **Vercel** deploy → `receptorai.pro`

## Repo layout

```
src/
├── app/                  Next.js App Router (routes + API routes)
├── components/
│   ├── ui/               shadcn primitives
│   ├── dashboard/        KPI cards, charts (Phase 2)
│   ├── chat/             AI chat drawer (Phase 4)
│   └── marketing/        Landing sections (Phase 2)
└── lib/
    ├── iiko/             iiko Cloud + RMS clients (Phase 1, port of v1 Python)
    ├── db/               Supabase client + queries (Phase 3)
    ├── mock/             Edison-shaped fixtures (Phase 1)
    ├── ai/               Claude tool-calling (Phase 4)
    ├── format.ts         RU number formatters (TDD ✓)
    └── utils.ts          shadcn cn() helper
docs/
├── brand-guide.md        Receptor brand v2.0
└── v1-iiko-reference/    Python clients to port → TypeScript
```

## Scripts

```bash
npm run dev         # next dev (Turbopack)
npm run build       # next build (production)
npm run start       # next start
npm run lint        # eslint
npm run typecheck   # tsc --noEmit
npm test            # vitest run
npm run test:watch  # vitest --watch
```

## Build phases

See `D:\PROJECTS\FROGFACE-VAULT\canonical\plans\2026-05-30-receptor-build-kickoff.md`.

| Phase | Scope | Mode |
|---|---|---|
| 0 | Scaffold, tooling, v1 archive | ✅ |
| 1 | Mock fixtures + iiko client port | TDD |
| 2 | Landing + BI Dashboard | frontend-design |
| 3 | Supabase Auth + onboarding + settings | frontend-design |
| 4 | AI Chat + Claude tools | TDD + frontend-design |
| 5 | Pricing + billing UI | frontend-design |
| 6 | Polish + Михно demo | — |

## Mock-first

Until iiko keys arrive, `USE_MOCK_IIKO=true` makes `lib/iiko/client.ts` read from `lib/mock/`. Flip to `false` to use real clients with same interface. See `.env.local.example`.

## v1 reference

Полный inventory of v1 codebase (что работает / что выкинуть):
`D:\PROJECTS\FROGFACE-VAULT\canonical\plans\2026-05-29-receptor-inventory-report.md`.

История v1 заморожена в ветке `legacy-v1`.
