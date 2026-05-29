# lib/iiko — iiko Cloud + RMS clients (Phase 1)

TypeScript port of v1 Python clients from `docs/v1-iiko-reference/`.

Planned files (Phase 1, TDD):
- `models.ts` — Zod schemas (replaces `iiko_models.py` + `iiko_rms_models.py`)
- `cloud-client.ts` — Cloud API (`api-ru.iiko.services`)
- `rms-client.ts` — RMS Server (`/resto/api/...`)
- `client.ts` — unified facade with mock/real switch via `USE_MOCK_IIKO` env
