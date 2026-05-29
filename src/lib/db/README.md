# lib/db — Supabase client & queries

Planned (when keys arrive after 31 May):
- `client.ts` — server Supabase client (service role, RSC-safe)
- `browser.ts` — browser Supabase client (anon)
- `encryption.ts` — AES-GCM for iiko credentials (port of `v1-iiko-reference/encryption.py`)
- `queries/` — typed query helpers per table (venues, iiko_credentials, conversations…)
- `migrations/` — SQL migrations (run manually in Supabase SQL editor)
