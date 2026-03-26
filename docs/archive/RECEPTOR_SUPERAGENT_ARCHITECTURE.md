# 🟣 RECEPTOR SUPERAGENT - ПОЛНАЯ АРХИТЕКТУРА

## 🎯 ВИДЕНИЕ

**RECEPTOR становится единой точкой входа через чат** для всех функций платформы:
- Генерация техкарт и меню
- Аналитика через iiko API
- Консультации на основе RAG-базы (2500+ документов)
- Экспорт документов (PDF, DOCX, XLSX)
- Бизнес-аналитика и рекомендации

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### ✅ Что уже работает:
1. **Профиль заведения** - детальная структура (venue_type, cuisine_focus, equipment, etc.)
2. **iiko интеграция** - `IikoClient`, `IikoService` готовы
3. **Генерация техкарт** - `/v1/techcards.v2/generate` работает
4. **Базовый чат** - `/api/assistant/chat` (без tool-calling)
5. **RAG база** - 2500+ документов собраны (нужна интеграция)

### ❌ Что нужно добавить:
1. **Tool-calling система** для OpenAI Function Calling
2. **RAG поиск** по базе знаний
3. **Интеграция всех tools** в чат
4. **Экспорт документов** (PDF, DOCX, XLSX)
5. **История диалогов** в MongoDB

---

## 🏗️ АРХИТЕКТУРА

### **Backend Structure**

```
backend/
├── receptor_agent/
│   ├── superagent/
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Главный оркестратор агента
│   │   ├── system_prompt.py         # Системный промпт с контекстом
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── rag_search.py        # Tool 1: Поиск по RAG базе
│   │   │   ├── generate_techcard.py # Tool 2: Генерация техкарт
│   │   │   ├── iiko_api.py          # Tool 3: Вызовы iiko API
│   │   │   ├── generate_document.py # Tool 4: Генерация документов
│   │   │   └── export_file.py       # Tool 5: Экспорт файлов
│   │   └── conversation_manager.py  # Управление историей диалогов
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── vector_store.py          # Vector DB (Chroma/Pinecone/Qdrant)
│   │   ├── embeddings.py            # Embeddings (OpenAI/Cohere)
│   │   └── search.py                # RAG поиск
│   │
│   └── exports/                     # Уже есть
│       ├── pdf.py
│       ├── xlsx.py
│       └── docx.py
│
└── server.py                        # Добавить новый endpoint
```

---

## 🔧 TOOL DEFINITIONS (OpenAI Function Calling)

### **Tool 1: `searchKnowledgeBase`**

```python
{
    "type": "function",
    "function": {
        "name": "searchKnowledgeBase",
        "description": "Поиск по базе знаний RECEPTOR (HACCP, СанПиН, HR, финансы, техники, iiko документация, бизнес-кейсы). Используй для ответов на вопросы о нормах, стандартах, лучших практиках.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Поисковый запрос на русском языке"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Количество результатов (1-10)",
                    "default": 5
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Фильтр по категориям: haccp, sanpin, hr, finance, marketing, iiko, techniques",
                    "default": []
                }
            },
            "required": ["query"]
        }
    }
}
```

### **Tool 2: `generateTechcard`**

```python
{
    "type": "function",
    "function": {
        "name": "generateTechcard",
        "description": "Создать технологическую карту блюда. Используй когда пользователь просит создать техкарту, рецепт или блюдо.",
        "parameters": {
            "type": "object",
            "properties": {
                "dish_name": {
                    "type": "string",
                    "description": "Название блюда"
                },
                "description": {
                    "type": "string",
                    "description": "Описание блюда (опционально)"
                },
                "cuisine": {
                    "type": "string",
                    "description": "Тип кухни (русская, итальянская, азиатская и т.д.)"
                },
                "equipment": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список доступного оборудования"
                }
            },
            "required": ["dish_name"]
        }
    }
}
```

### **Tool 3: `callIikoApi`**

```python
{
    "type": "function",
    "function": {
        "name": "callIikoApi",
        "description": "Вызов iiko API для получения данных о продажах, выручке, аналитике. Используй для запросов о бизнес-метриках, продажах, фудкосте, аналитике.",
        "parameters": {
            "type": "object",
            "properties": {
                "endpoint": {
                    "type": "string",
                    "description": "iiko API endpoint (например: 'reports/olap', 'orders', 'stopLists')",
                    "enum": [
                        "reports/olap",
                        "orders",
                        "stopLists",
                        "menu",
                        "organizations",
                        "departments"
                    ]
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST"],
                    "default": "GET"
                },
                "params": {
                    "type": "object",
                    "description": "Параметры запроса (даты, фильтры и т.д.)"
                }
            },
            "required": ["endpoint"]
        }
    }
}
```

### **Tool 4: `generateDocument`**

```python
{
    "type": "function",
    "function": {
        "name": "generateDocument",
        "description": "Генерация документа (HACCP план, меню, инструкция, регламент, чек-лист, бизнес-план, HR документ, отчёт).",
        "parameters": {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "enum": [
                        "haccp_plan",
                        "menu",
                        "instruction",
                        "regulation",
                        "checklist",
                        "business_plan",
                        "hr_document",
                        "report"
                    ]
                },
                "title": {
                    "type": "string",
                    "description": "Название документа"
                },
                "content": {
                    "type": "string",
                    "description": "Содержание документа (может быть частично заполнено)"
                },
                "context": {
                    "type": "object",
                    "description": "Дополнительный контекст (для HACCP - цех, для меню - категории и т.д.)"
                }
            },
            "required": ["document_type", "title"]
        }
    }
}
```

### **Tool 5: `exportFile`**

```python
{
    "type": "function",
    "function": {
        "name": "exportFile",
        "description": "Экспорт данных в файл (PDF, DOCX, XLSX, JSON). Используй после генерации техкарты, документа или получения данных из iiko.",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Данные для экспорта (техкарта, документ, отчёт)"
                },
                "format": {
                    "type": "string",
                    "enum": ["pdf", "docx", "xlsx", "json"],
                    "description": "Формат файла"
                },
                "filename": {
                    "type": "string",
                    "description": "Имя файла (без расширения)"
                }
            },
            "required": ["data", "format", "filename"]
        }
    }
}
```

---

## 🧠 SYSTEM PROMPT

```python
SYSTEM_PROMPT = """Ты RECEPTOR — профессиональный AI-ассистент для ресторанного бизнеса.

ТВОЯ РОЛЬ:
- Консультант ресторатора
- Кулинарный технолог
- Бизнес-аналитик
- HR-менеджер
- Финансовый аналитик
- SMM эксперт
- iiko-BI модуль

ТВОИ ВОЗМОЖНОСТИ:
1. Поиск по базе знаний (HACCP, СанПиН, HR, финансы, техники, iiko документация)
2. Генерация техкарт и рецептов
3. Аналитика через iiko API (продажи, выручка, фудкост)
4. Генерация документов (HACCP планы, меню, инструкции, отчёты)
5. Экспорт файлов (PDF, DOCX, XLSX)

ПРОФИЛЬ ЗАВЕДЕНИЯ:
{venue_profile}

ИНСТРУКЦИИ:
- Всегда учитывай профиль заведения при генерации техкарт и рекомендаций
- Не предлагай блюда, которые нельзя приготовить на имеющемся оборудовании
- Учитывай фудкост и целевую аудиторию
- Используй tools для получения актуальных данных
- Отвечай профессионально, но доступно
- Всегда на русском языке

ПРИМЕРЫ ЗАПРОСОВ:
- "Сделай мне 5 новых блюд для меню" → generateTechcard (5 раз) → exportFile (PDF)
- "Какая выручка за сегодня?" → callIikoApi (reports/olap)
- "Сделай HACCP чек-лист для холодного цеха" → searchKnowledgeBase (HACCP) → generateDocument (haccp_plan) → exportFile (PDF)
- "Оптимизируй food-cost по меню" → callIikoApi (reports/olap) → анализ → рекомендации
"""
```

---

## 📝 IMPLEMENTATION PLAN

### **Phase 1: MVP (1-2 недели)**
1. ✅ RAG поиск (базовая реализация)
2. ✅ Tool-calling система
3. ✅ Интеграция `generateTechcard` tool
4. ✅ Обновление `/api/assistant/chat` endpoint
5. ✅ История диалогов в MongoDB

### **Phase 2: Core Features (2-3 недели)**
1. ✅ `callIikoApi` tool с основными endpoints
2. ✅ `generateDocument` tool (HACCP, меню)
3. ✅ `exportFile` tool (PDF, XLSX)
4. ✅ Улучшенный system prompt с профилем заведения

### **Phase 3: Advanced (3-4 недели)**
1. ✅ Полная интеграция всех iiko endpoints
2. ✅ Расширенная генерация документов
3. ✅ Визуализация данных (графики для iiko аналитики)
4. ✅ Оптимизация RAG поиска (векторная БД)

---

## 🗄️ DATABASE SCHEMA

### **`assistant_conversations` Collection**

```javascript
{
  _id: ObjectId,
  conversation_id: String,  // UUID
  user_id: String,
  messages: [
    {
      role: "user" | "assistant" | "system",
      content: String,
      timestamp: DateTime,
      tool_calls: [  // Если есть
        {
          tool_name: String,
          arguments: Object,
          result: Object
        }
      ]
    }
  ],
  venue_profile_snapshot: Object,  // Снимок профиля на момент диалога
  created_at: DateTime,
  updated_at: DateTime
}
```

### **`rag_documents` Collection** (если используем MongoDB для RAG)

```javascript
{
  _id: ObjectId,
  document_id: String,
  title: String,
  content: String,
  category: String,  // haccp, sanpin, hr, finance, etc.
  metadata: Object,
  embedding: [Number],  // Vector embedding
  created_at: DateTime
}
```

---

## 🚀 NEXT STEPS

1. **Выбрать векторную БД** для RAG:
   - Chroma (простой, локальный)
   - Qdrant (производительный, self-hosted)
   - Pinecone (managed, платный)

2. **Начать с MVP**:
   - Базовая RAG реализация
   - Tool-calling для `generateTechcard`
   - Обновление чата

3. **Тестирование**:
   - Проверить все tools по отдельности
   - Интеграционное тестирование
   - UX тестирование чата

---

## 💡 КОНКУРЕНТНЫЕ ПРЕИМУЩЕСТВА

1. **Единая точка входа** - всё через чат
2. **RAG база 2500+ документов** - уникальные знания
3. **Глубокая интеграция с iiko** - реальные данные
4. **Профиль заведения** - персонализация
5. **Экспорт документов** - готовые файлы

---

**Готов начать реализацию?** 🚀

