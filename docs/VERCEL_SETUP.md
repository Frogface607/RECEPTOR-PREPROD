# Vercel — Setup TODO для Босса

Phase 0 закоммичен и пушнут в `main` (`726bbb9d`).

Прод сейчас всё ещё показывает **старую CRA** (`title: "RECEPTOR — AI-копилот для ресторанного бизнеса"`). Это значит у Vercel project либо ещё не приехал автодеплой, либо **Build Settings прибиты к v1**.

## Что нужно проверить в Vercel Dashboard

Project: `receptor-preprod-final-nqu9nzl11` → Settings:

1. **Framework Preset:** должен быть **Next.js** (был «Other» или «Create React App»)
2. **Root Directory:** должен быть **`/`** (был, скорее всего, `frontend/` или `frontend`)
3. **Build Command:** `next build` (или leave empty — Next.js detect)
4. **Output Directory:** оставить пустым (Next.js handles)
5. **Install Command:** `npm install` (default)
6. **Node.js Version:** `22.x` (мы используем Node 22.16)

## Env Vars to remove

Старые v1 переменные больше не нужны:
- `REACT_APP_BACKEND_URL`
- `REACT_APP_API_URL`
- `MONGODB_URI`
- `JWT_SECRET_KEY`
- `OPENAI_API_KEY` (заменяется на ANTHROPIC_API_KEY в Phase 4)
- `ENVIRONMENT`
- `DB_NAME`
- `CORS_ORIGINS`
- `ADMIN_SECRET`
- `TAVILY_API_KEY`
- `YOOKASSA_SHOP_ID` / `YOOKASSA_SECRET_KEY` (вернутся в Phase 5)

## Env Vars to add (когда придут ключи после 31 мая)

```
USE_MOCK_IIKO=true                        # Phase 0–4 dev
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=                       # optional fallback
ENCRYPTION_KEY=                           # node -e 'console.log(require("crypto").randomBytes(32).toString("hex"))'
```

## Smoke check после фикса

```
curl -sL https://www.receptorai.pro | grep -E '_next/static|__next_f' | head -1
```
должен вернуть совпадение → значит Next.js задеплоен.
