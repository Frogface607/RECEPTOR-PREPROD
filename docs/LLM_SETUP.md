# LLM Setup

## Настройка OpenAI для техкарт v2

1) В `backend/.env` укажи:

```bash
OPENAI_API_KEY=sk-...
TECHCARDS_V2_MODEL=gpt-4o-mini
TECHCARDS_V2_USE_LLM=true
FEATURE_TECHCARDS_V2=true
```

2) Перезапусти backend (или весь контейнер):

```bash
sudo supervisorctl restart backend
```

3) Проверь статус:

```bash
curl http://localhost:8001/api/v1/techcards.v2/status
```

Должен вернуть:
```json
{
  "feature_enabled": true,
  "llm_enabled": true, 
  "model": "gpt-4o-mini"
}
```

4) Генерация с явным флагом на запрос:

```bash
curl -X POST "http://localhost:8001/api/v1/techcards.v2/generate?use_llm=true" \
  -H "Content-Type: application/json" \
  -d '{"name":"EDISON","cuisine":"мексиканская","equipment":["oven"],"budget":350.0,"dietary":[]}'
```

## Безопасный fallback

**Почему так:** мы используем **Structured Outputs** с `json_schema`, чтобы сразу получать валидный JSON под нашу схему, без лишнего пост-парсинга (см. OpenAI docs). Если ключа нет — пайплайн возвращается к локальным функциям и работает стабильно.

## Устранение проблем

- **401 Unauthorized**: Неверный `OPENAI_API_KEY`
- **429 Rate Limited**: Превышен лимит запросов, включены автоматические ретраи
- **408 Timeout**: Превышен таймаут `TECHCARDS_V2_REQUEST_TIMEOUT`
- **llm_enabled: false**: Проверь наличие ключа и флага `TECHCARDS_V2_USE_LLM=true`

При любых ошибках OpenAI система автоматически переключается на локальные заглушки.