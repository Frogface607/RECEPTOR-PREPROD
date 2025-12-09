"""
LLM Client с умным роутингом моделей для RECEPTOR
"""
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional, Tuple
import re


# Конфигурация моделей (от дешёвой к дорогой)
MODEL_CONFIG = {
    "simple": {
        "model": "gpt-4o-mini",
        "description": "Простые запросы, поиск, короткие ответы",
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
    },
    "standard": {
        "model": "gpt-4o",
        "description": "Рецепты, советы, средняя сложность",
        "cost_per_1k_input": 0.0025,
        "cost_per_1k_output": 0.01,
    },
    "advanced": {
        "model": "gpt-5.1-mini",
        "description": "Техкарты, анализ, генерация контента",
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.012,
    },
    "reasoning": {
        "model": "o3-mini",
        "description": "Глубокий анализ, стратегия, бизнес-модели",
        "cost_per_1k_input": 0.01,
        "cost_per_1k_output": 0.04,
    },
    "expert": {
        "model": "gpt-5.1",
        "description": "Максимум интеллекта, сложные цепочки",
        "cost_per_1k_input": 0.015,
        "cost_per_1k_output": 0.06,
    }
}


def classify_query_complexity(query: str, context_length: int = 0) -> str:
    """
    Классифицирует сложность запроса для выбора модели.
    
    Returns: 'simple', 'standard', 'advanced', 'reasoning', 'expert'
    """
    query_lower = query.lower()
    
    # REASONING: глубокий анализ, требует рассуждений
    reasoning_patterns = [
        r'стратеги[яю]', r'бизнес.?план', r'финансов.*модел', 
        r'анализ.*рынк', r'конкурент.*анализ', r'глубок.*анализ',
        r'проанализируй', r'разбери.*детально', r'найди.*слаб.*мест',
        r'оптимизац.*бизнес', r'точка.*безубыточ', r'roi.*расчет',
        r'проблем.*реш', r'причин.*анализ', r'что.*не.*так',
        r'открыт.*заведен', r'запуск.*бизнес', r'концепц.*разработ',
        r'масштабирован', r'инвестиц.*обоснован', r'unit.?экономик'
    ]
    if any(re.search(p, query_lower) for p in reasoning_patterns):
        return "reasoning"
    
    # ADVANCED: техкарты, детальная генерация (без глубокого анализа)
    advanced_patterns = [
        r'техкарт[ау|у]', r'технологическ.*карт', r'калькуляц', r'себестоимость',
        r'рецепт.*подробн', r'пошагов.*инструкц', r'меню.*разработ',
        r'haccp.*план', r'санпин.*требован', r'аудит', r'чек.?лист'
    ]
    if any(re.search(p, query_lower) for p in advanced_patterns):
        return "advanced"
    
    # SIMPLE: короткие/простые запросы
    simple_patterns = [
        r'^привет', r'^здравствуй', r'^спасибо', r'^пока',
        r'найди', r'поиск', r'покажи', r'где\s', r'что такое',
        r'сколько стоит', r'цена', r'есть ли'
    ]
    if any(re.search(p, query_lower) for p in simple_patterns):
        return "simple"
    
    # Короткие запросы (< 50 символов) = simple
    if len(query) < 50:
        return "simple"
    
    # По умолчанию — standard
    return "standard"


class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.usage_stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
            "requests_by_model": {}
        }

    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        auto_route: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Генерация ответа с умным роутингом моделей.
        
        Args:
            messages: История сообщений
            model: Конкретная модель (если None — автороутинг)
            temperature: Температура генерации (игнорируется для reasoning моделей)
            auto_route: Автоматически выбирать модель по сложности
        
        Returns:
            Tuple[response_text, usage_info]
        """
        try:
            # Определяем модель
            if model is None and auto_route:
                last_user_msg = next(
                    (m["content"] for m in reversed(messages) if m["role"] == "user"), 
                    ""
                )
                complexity = classify_query_complexity(last_user_msg)
                model = MODEL_CONFIG[complexity]["model"]
            elif model is None:
                model = MODEL_CONFIG["standard"]["model"]
            
            # Определяем параметры запроса (reasoning модели не поддерживают temperature)
            reasoning_models = ["o3-mini", "o1-mini", "o1-pro", "o1", "o3"]
            request_params = {
                "model": model,
                "messages": messages
            }
            
            # Добавляем temperature только для не-reasoning моделей
            if model not in reasoning_models:
                request_params["temperature"] = temperature
            
            # Пробуем выбранную модель, с fallback на gpt-4o
            try:
                response = await self.client.chat.completions.create(**request_params)
            except Exception as model_error:
                # Fallback если модель недоступна
                print(f"⚠️ Model {model} unavailable, falling back to gpt-4o: {model_error}")
                model = "gpt-4o"
                fallback_params = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
                response = await self.client.chat.completions.create(**fallback_params)
            
            # Собираем статистику
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            
            # Считаем стоимость
            model_costs = next(
                (cfg for cfg in MODEL_CONFIG.values() if cfg["model"] == model),
                MODEL_CONFIG["standard"]
            )
            cost = (
                (input_tokens / 1000) * model_costs["cost_per_1k_input"] +
                (output_tokens / 1000) * model_costs["cost_per_1k_output"]
            )
            
            # Обновляем статистику
            self._update_stats(model, input_tokens, output_tokens, cost)
            
            usage_info = {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost, 6),
                "complexity": classify_query_complexity(
                    next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
                )
            }
            
            return response.choices[0].message.content, usage_info
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return "Извините, произошла ошибка при обращении к AI.", {"error": str(e)}
    
    def _update_stats(self, model: str, input_tokens: int, output_tokens: int, cost: float):
        """Обновляет статистику использования"""
        self.usage_stats["total_input_tokens"] += input_tokens
        self.usage_stats["total_output_tokens"] += output_tokens
        self.usage_stats["total_cost_usd"] += cost
        
        if model not in self.usage_stats["requests_by_model"]:
            self.usage_stats["requests_by_model"][model] = 0
        self.usage_stats["requests_by_model"][model] += 1
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования"""
        return self.usage_stats


# Для обратной совместимости — простой вызов без usage info
async def simple_chat_completion(
    client: OpenAIClient,
    messages: List[Dict[str, str]],
    model: str = "gpt-4o"
) -> str:
    """Простой вызов для обратной совместимости"""
    response, _ = await client.chat_completion(messages, model=model, auto_route=False)
    return response
