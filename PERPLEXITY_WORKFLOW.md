# 🔍 Workflow: Сбор базы знаний через Perplexity

## Проблема с OpenRouter API
Модели Perplexity через OpenRouter API недоступны (404/400 ошибки). Используем ручной сбор через веб-интерфейс + автоматическую обработку.

## Workflow

### Шаг 1: Deep Research в Perplexity
1. Открой https://www.perplexity.ai/
2. Выбери режим "Deep Research" (если доступен) или обычный поиск
3. Используй промпты из `backend/scripts/collect_knowledge_base.py` (раздел `PERPLEXITY_PROMPTS`)

### Шаг 2: Копирование результатов
1. Скопируй весь текст ответа от Perplexity
2. Сохрани ссылки на источники (если есть)

### Шаг 3: Отправка через API
Используй эндпоинт `POST /api/knowledge-base/process-research`:

```bash
curl -X POST http://localhost:8002/api/knowledge-base/process-research \
  -H "Content-Type: application/json" \
  -d '{
    "category": "haccp",
    "content": "ТЕКСТ ОТ PERPLEXITY...",
    "metadata": {
      "region": "Москва",
      "sources": ["url1", "url2"],
      "date": "2025-12-07"
    }
  }'
```

Или через Python:
```python
import requests

response = requests.post(
    "http://localhost:8002/api/knowledge-base/process-research",
    json={
        "category": "haccp",
        "content": "ТЕКСТ ОТ PERPLEXITY...",
        "metadata": {
            "region": "Москва",
            "sources": ["url1", "url2"]
        }
    }
)
print(response.json())
```

### Шаг 4: Автоматическая обработка
- Контент форматируется в Markdown
- Сохраняется в `backend/data/knowledge_base/`
- Можно запустить индексацию для RAG

## Категории для сбора

1. **haccp** - HACCP и СанПиН нормативы
2. **ingredients_prices** - Цены на ингредиенты
3. **techcards** - Техкарты и рецепты
4. **hr** - HR и управление персоналом
5. **finance** - Финансы и ценообразование
6. **marketing** - Маркетинг и продвижение
7. **iiko** - iiko и автоматизация
8. **regional** - Региональные особенности
9. **trends** - Тренды и инновации

## Промпты для Perplexity

Смотри `backend/scripts/collect_knowledge_base.py` - там все промпты в `PERPLEXITY_PROMPTS`.

## Альтернатива: Прямой API Perplexity

Если у тебя есть прямой API ключ Perplexity (не через OpenRouter), можно использовать:
- `https://api.perplexity.ai/chat/completions`
- Модель: `llama-3.1-sonar-large-128k-online`

Но для начала проще использовать веб-интерфейс + API обработки.

