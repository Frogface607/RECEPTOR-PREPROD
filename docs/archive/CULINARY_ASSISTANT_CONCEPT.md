# 🤖 КУЛИНАРНЫЙ АССИСТЕНТ RECEPTOR

## 💡 КОНЦЕПЦИЯ

AI-ассистент на главной странице, заточенный под ресторанного шефа и управляющего. Помогает с консультациями, советами, расчетами и принятием решений в ресторанном бизнесе.

---

## 🎯 ЦЕЛЕВАЯ АУДИТОРИЯ

1. **Шеф-повара** - консультации по рецептам, техникам, меню
2. **Управляющие** - бизнес-вопросы, аналитика, оптимизация
3. **Владельцы** - стратегия, финансы, масштабирование
4. **Начинающие** - обучение, базовые знания

---

## 🧠 СПЕЦИАЛИЗАЦИИ АССИСТЕНТА

### 1. **Шеф-консультант** (Culinary Expert)
```
Фокус: Рецепты, техники, кулинарные вопросы
Примеры вопросов:
- "Как правильно приготовить утку конфи?"
- "Какие специи подходят к баранине?"
- "Как оптимизировать рецепт для снижения себестоимости?"
- "Какая температура для су-вид говядины?"
```

### 2. **Бизнес-консультант** (Restaurant Manager)
```
Фокус: Управление, финансы, операционные вопросы
Примеры вопросов:
- "Как рассчитать наценку на блюдо?"
- "Сколько персонала нужно на кухню на 50 посадочных мест?"
- "Как оптимизировать меню для увеличения прибыли?"
- "Какие метрики важны для ресторана?"
```

### 3. **Меню-аналитик** (Menu Analyst)
```
Фокус: Анализ меню, рекомендации, оптимизация
Примеры вопросов:
- "Какие блюда убрать из меню?"
- "Как сбалансировать меню по категориям?"
- "Какие блюда добавить для увеличения среднего чека?"
```

### 4. **Финансовый аналитик** (Financial Advisor)
```
Фокус: Расчеты, себестоимость, маржа, ROI
Примеры вопросов:
- "Как рассчитать себестоимость блюда?"
- "Какая должна быть наценка на пасту?"
- "Сколько стоит открыть ресторан на 100 мест?"
```

---

## 🎨 UI/UX КОНЦЕПЦИЯ

### Вариант 1: **Встроенный чат в сайдбаре** (Рекомендую)
```
┌─────────────────────────────────────┐
│  RECEPTOR                    [👤]   │
├──────────┬──────────────────────────┤
│          │                          │
│  Главная │  🤖 Кулинарный          │
│  Техкарты│  Ассистент              │
│  Меню    │                          │
│  История │  ┌────────────────────┐ │
│  Кабинет │  │ Привет! Я твой     │ │
│          │  │ кулинарный         │ │
│          │  │ ассистент. Чем     │ │
│          │  │ могу помочь?       │ │
│          │  └────────────────────┘ │
│          │                          │
│          │  [Как рассчитать        │
│          │   себестоимость?]       │
│          │                          │
│          │  ┌────────────────────┐ │
│          │  │ Себестоимость =    │ │
│          │  │ (Стоимость         │ │
│          │  │  ингредиентов +    │ │
│          │  │  трудозатраты +    │ │
│          │  │  накладные) /      │ │
│          │  │  количество порций  │ │
│          │  └────────────────────┘ │
│          │                          │
│          │  [Введите вопрос...]    │
│          │  [Отправить]            │
│          └──────────────────────────┤
```

### Вариант 2: **Модальное окно** (По клику на кнопку)
```
Главная страница → Кнопка "💬 Спросить ассистента" → Модальное окно с чатом
```

### Вариант 3: **Вкладка на главной** (Как отдельная секция)
```
Главная страница:
- Создание техкарты (основное)
- Кулинарный ассистент (вкладка рядом)
```

---

## 💬 ПРИМЕРЫ ДИАЛОГОВ

### Пример 1: Кулинарный вопрос
```
👤 Пользователь: "Как правильно приготовить утку конфи?"

🤖 Ассистент: 
"Утка конфи - классическая французская техника. Вот пошаговый рецепт:

1. **Подготовка**: Утку разделить на части (грудка, ножки, крылья)
2. **Засолка**: Посолить и оставить на 2-4 часа в холодильнике
3. **Томление**: Положить в утиный жир, томить при 80-90°C 2-3 часа
4. **Хранение**: Можно хранить в жире до 3 месяцев

**Совет**: Ножки получаются особенно нежными. Хотите, создам полную техкарту?"

[Создать техкарту] [Больше советов]
```

### Пример 2: Бизнес-вопрос
```
👤 Пользователь: "Как рассчитать наценку на блюдо?"

🤖 Ассистент:
"Наценка рассчитывается так:

**Формула**: Наценка = (Цена продажи - Себестоимость) / Себестоимость × 100%

**Пример**:
- Себестоимость: 200₽
- Цена продажи: 800₽
- Наценка: (800 - 200) / 200 × 100% = 300%

**Рекомендации по наценке**:
- Закуски: 300-400%
- Основные блюда: 250-350%
- Десерты: 400-500%
- Напитки: 500-700%

Хотите, рассчитаю наценку для вашего блюда?"

[Рассчитать] [Больше о финансах]
```

### Пример 3: Оптимизация меню
```
👤 Пользователь: "Какие блюда убрать из меню?"

🤖 Ассистент:
"Чтобы определить, какие блюда убрать, нужно проанализировать:

1. **Маржинальность** - блюда с низкой маржой (< 200%)
2. **Популярность** - редко заказываемые блюда
3. **Трудозатраты** - сложные в приготовлении, но не прибыльные
4. **Сезонность** - несезонные ингредиенты

**Красные флаги**:
- Маржа < 150%
- Заказов < 5 в неделю
- Время приготовления > 30 минут
- Сложные ингредиенты с коротким сроком хранения

Загрузите ваше меню, и я проанализирую его автоматически!"

[Загрузить меню] [Пример анализа]
```

---

## 🔧 ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ

### Backend: Новый эндпоинт
```python
@api_router.post("/api/assistant/chat")
async def chat_with_assistant(request: AssistantChatRequest):
    """
    Чат с кулинарным ассистентом
    
    Request:
    {
        "user_id": "uuid",
        "message": "Как рассчитать наценку?",
        "context": "restaurant_manager",  # или "chef", "owner"
        "conversation_id": "uuid"  # для продолжения диалога
    }
    
    Response:
    {
        "response": "Наценка рассчитывается...",
        "conversation_id": "uuid",
        "suggestions": [
            "Создать техкарту",
            "Рассчитать себестоимость",
            "Проанализировать меню"
        ],
        "tokens_used": 150,
        "credits_spent": 5
    }
    """
    
    # Проверка кредитов (5 токенов за сообщение)
    await check_credits_required(request.user_id, "assistant_chat", 5)
    
    # Системный промпт в зависимости от контекста
    system_prompt = get_system_prompt(request.context)
    
    # Вызов LLM
    response = await call_assistant_llm(
        system_prompt=system_prompt,
        user_message=request.message,
        conversation_history=get_conversation_history(request.conversation_id)
    )
    
    # Списание кредитов
    await deduct_credits(request.user_id, 5, "assistant_chat", {
        "message_length": len(request.message),
        "response_length": len(response)
    })
    
    return {
        "response": response,
        "conversation_id": request.conversation_id or str(uuid.uuid4()),
        "suggestions": generate_suggestions(response),
        "tokens_used": response.tokens_used,
        "credits_spent": 5
    }
```

### Системные промпты

#### Шеф-консультант
```python
CHEF_SYSTEM_PROMPT = """
Ты опытный шеф-повар с 20-летним стажем работы в мишленовских ресторанах.
Твоя специализация:
- Рецепты и техники приготовления
- Кулинарные советы и рекомендации
- Оптимизация рецептов
- Подбор ингредиентов и специй
- Технические вопросы кухни

Всегда отвечай профессионально, но доступно. Давай конкретные советы с примерами.
Если пользователь спрашивает о рецепте, предлагай создать техкарту в RECEPTOR.
"""
```

#### Бизнес-консультант
```python
MANAGER_SYSTEM_PROMPT = """
Ты опытный управляющий рестораном с 15-летним стажем.
Твоя специализация:
- Финансовые расчеты (себестоимость, наценка, маржа)
- Оптимизация меню
- Управление персоналом
- Операционные вопросы
- Метрики и аналитика

Всегда давай конкретные цифры и формулы. Предлагай практические решения.
Если нужно, предлагай использовать функции RECEPTOR для расчетов.
"""
```

### Frontend: React компонент
```jsx
// CulinaryAssistant.jsx
import { useState, useRef, useEffect } from 'react';

const CulinaryAssistant = ({ userId }) => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Привет! Я твой кулинарный ассистент RECEPTOR. Чем могу помочь?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState('chef'); // chef, manager, owner
  const messagesEndRef = useRef(null);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post('/api/assistant/chat', {
        user_id: userId,
        message: input,
        context: context
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.response,
        suggestions: response.data.suggestions,
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error('Assistant error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Заголовок */}
      <div className="p-4 border-b bg-purple-600 text-white rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🤖</span>
            <div>
              <h3 className="font-semibold">Кулинарный ассистент</h3>
              <select 
                value={context}
                onChange={(e) => setContext(e.target.value)}
                className="text-xs bg-purple-700 rounded px-2 py-1 mt-1"
              >
                <option value="chef">Шеф-консультант</option>
                <option value="manager">Бизнес-консультант</option>
                <option value="owner">Владелец</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Сообщения */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.suggestions && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {msg.suggestions.map((suggestion, i) => (
                    <button
                      key={i}
                      className="text-xs bg-white bg-opacity-20 rounded px-2 py-1 hover:bg-opacity-30"
                      onClick={() => setInput(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Ввод */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Задайте вопрос..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Отправить
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          💡 Каждое сообщение стоит 5 токенов
        </p>
      </div>
    </div>
  );
};
```

---

## 💰 МОНЕТИЗАЦИЯ

### Стоимость в токенах
- **Базовый чат**: 5 токенов за сообщение
- **Расширенный анализ**: 10 токенов (если требуется анализ данных)
- **Генерация контента**: 15 токенов (если создается техкарта/меню)

### Лимиты по подпискам
- **FREE**: 10 сообщений/день (50 токенов)
- **STARTER**: 50 сообщений/день (250 токенов)
- **PRO**: Безлимит
- **BUSINESS**: Безлимит + приоритетная обработка

---

## 🚀 ПЛАН ВНЕДРЕНИЯ

### Фаза 1: MVP (1-2 недели)
1. ✅ Базовый чат на главной странице
2. ✅ Один системный промпт (универсальный)
3. ✅ Простой UI (встроенный в сайдбар или модальное окно)
4. ✅ Интеграция с системой токенов

### Фаза 2: Специализации (1 неделя)
1. ✅ Выбор контекста (шеф/менеджер/владелец)
2. ✅ Разные системные промпты
3. ✅ Предложения действий (создать техкарту, рассчитать и т.д.)

### Фаза 3: Продвинутые функции (2 недели)
1. ✅ История диалогов (сохранение в БД)
2. ✅ Контекстные предложения на основе диалога
3. ✅ Интеграция с техкартами (создание из чата)
4. ✅ Голосовой ввод (опционально)

---

## 💡 ДОПОЛНИТЕЛЬНЫЕ ИДЕИ

### Быстрые вопросы (Quick Actions)
```
Кнопки на главной:
- "Как рассчитать себестоимость?"
- "Какая наценка оптимальна?"
- "Как оптимизировать меню?"
- "Какие блюда добавить?"
```

### Шаблоны вопросов
```
Категории:
- 💰 Финансы
- 🍽️ Рецепты
- 📊 Меню
- 👥 Персонал
- 📈 Аналитика
```

### Интеграция с техкартами
```
В чате:
"Создай техкарту для тако с уткой"
→ Ассистент создает техкарту через API
→ Показывает результат в чате
→ Предлагает сохранить
```

---

## 🎯 ПРЕИМУЩЕСТВА

1. **Увеличение engagement** - пользователи будут чаще заходить
2. **Образовательная ценность** - помогает новичкам
3. **Дифференциация** - уникальная фича на рынке
4. **Монетизация** - дополнительный источник дохода через токены
5. **Retention** - пользователи возвращаются за советами

---

**Создано с ❤️ для RECEPTOR** 🚀

