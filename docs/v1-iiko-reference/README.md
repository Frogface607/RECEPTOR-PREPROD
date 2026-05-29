# v1 iiko Reference (archive)

> Архивная копия рабочих Python-клиентов из Receptor v1, сохранённая для **порта на TypeScript** в Receptor v2 (Next.js 16 + Supabase).
>
> Полная история v1 — в ветке `legacy-v1`. Эта папка — только важная часть, которую переписываем построчно.

## Что лежит

| Файл | Назначение | LOC | Что портируем |
|---|---|---|---|
| `iiko_client.py` | iiko Cloud API клиент (api-ru.iiko.services) | 1161 | → `lib/iiko/cloud-client.ts` |
| `iiko_rms_client.py` | iiko RMS Server клиент (/resto/api/...) | 1094 | → `lib/iiko/rms-client.ts` |
| `iiko_models.py` | Pydantic-модели Cloud | 135 | → `lib/iiko/models.ts` (Zod) |
| `iiko_rms_models.py` | Pydantic-модели RMS | 213 | → `lib/iiko/models.ts` (Zod) |
| `iiko_service.py` | Сервисный слой Cloud (connect/select/sync/search) | 463 | → `lib/iiko/cloud-service.ts` |
| `iiko_rms_service.py` | Сервисный слой RMS + OLAP-методы | 1529 | → `lib/iiko/rms-service.ts` (BI engine) |
| `iiko_api_routes.py` | FastAPI router, 27 endpoints | 1497 | → Next.js App Router `app/api/iiko/*` |
| `encryption.py` | Шифрование iiko credentials (Fernet/AES-GCM) | — | → `lib/db/encryption.ts` (Node crypto) |

## Что НЕ портируем

- MongoDB-зависимости (`pymongo`, `motor`) — заменяем на Supabase Postgres
- `pyiikocloudapi` (нишевая библиотека) — пишем прямой `fetch` + Zod
- Сложный fuzzy-search с lemmatized RU — упрощаем до базового similarity или Postgres `pg_trgm`
- HACCP/техкарты pipeline — не в скоупе v2

## Контекст портирования

См. `D:\PROJECTS\FROGFACE-VAULT\canonical\plans\2026-05-29-receptor-inventory-report.md` —
полная инвентаризация v1 с разбором endpoints, fallback-логики, и решением что переиспользуем.

См. `D:\PROJECTS\FROGFACE-VAULT\canonical\plans\2026-05-30-receptor-v2-spec.md` —
архитектура v2 и план порта.
