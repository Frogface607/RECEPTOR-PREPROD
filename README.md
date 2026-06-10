# Receptor

Operational BI and AI copilot for restaurant owners.

Receptor connects to iiko, turns sales data into a dashboard, answers questions
through an AI copilot, and generates a Daily Brief for owner-level decisions.

## Stack

- Next.js 16 App Router, React 19, TypeScript
- Supabase Auth and Postgres
- iiko Cloud/RMS client facade
- OpenAI/Anthropic AI backends with deterministic fallback
- Vitest, ESLint, Vercel

## Core Surfaces

- `/onboarding` - connect iiko apiLogin and select organization
- `/dashboard/[venueId]` - BI, charts, shifts, Daily Brief, AI chat
- `/settings` - account and venue connection status
- `/api/brief` - JSON/text Daily Brief
- `/api/brief/send` - delivery hook for Daily Brief
- `/api/auth/dev` - protected developer sandbox login

## Environment

See `.env.local.example`.

Important production variables:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `ENCRYPTION_KEY`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`

Optional developer access:

- `RECEPTOR_DEV_MODE=true`
- `RECEPTOR_DEV_EMAIL=you@example.com`
- `RECEPTOR_DEV_ACCESS_KEY=<private key>`

Optional Telegram delivery:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Scripts

```bash
npm run dev
npm run build
npm run start
npm run lint
npm run typecheck
npm test
```

## Sandbox

When real iiko credentials are absent, `USE_MOCK_IIKO=true` uses deterministic
sandbox fixtures from `src/lib/mock`. The public UI points to
`/dashboard/dev-venue` for local/product testing.
