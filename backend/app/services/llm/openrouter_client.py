"""
OpenRouter Client - доступ к лучшим моделям через единый API
https://openrouter.ai - агрегатор моделей (Claude, GPT, Gemini, и др.)
"""
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Конфигурация моделей через OpenRouter (лучшие для каждой задачи)
OPENROUTER_MODELS = {
    "simple": {
        "model": "openai/gpt-4o-mini",  # Дешёвый и быстрый
        "description": "Простые запросы, поиск, короткие ответы",
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
    },
    "standard": {
        "model": "openai/gpt-4o",  # Баланс цена/качество
        "description": "Рецепты, советы, средняя сложность",
        "cost_per_1k_input": 0.0025,
        "cost_per_1k_output": 0.01,
    },
    "advanced": {
        "model": "anthropic/claude-3.5-sonnet",  # Лучший для генерации контента
        "description": "Техкарты, детальная генерация, анализ",
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
    },
    "reasoning": {
        "model": "openai/o3-mini",  # Лучший reasoning
        "description": "Глубокий анализ, стратегия, бизнес-модели",
        "cost_per_1k_input": 0.01,
        "cost_per_1k_output": 0.04,
    },
    "expert": {
        "model": "anthropic/claude-3.5-sonnet",  # Флагман для сложных задач
        "description": "Максимум интеллекта, сложные цепочки",
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
    }
}


class OpenRouterClient:
    """
    Клиент для OpenRouter API - доступ к лучшим моделям
    """
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://receptor.ai",  # Для аналитики
                "X-Title": "RECEPTOR Copilot"
            }
        )
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
        auto_route: bool = True,
        complexity: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Генерация ответа через OpenRouter с умным роутингом
        
        Args:
            messages: История сообщений
            model: Конкретная модель (если None — автороутинг)
            temperature: Температура (игнорируется для reasoning)
            auto_route: Автоматически выбирать модель
            complexity: Уровень сложности ('simple', 'standard', 'advanced', 'reasoning', 'expert')
        
        Returns:
            Tuple[response_text, usage_info]
        """
        try:
            # Определяем модель
            if model is None:
                if complexity:
                    model = OPENROUTER_MODELS[complexity]["model"]
                    logger.info(f"🎯 Using explicit complexity: {complexity} → {model}")
                elif auto_route:
                    from .client import classify_query_complexity
                    last_user_msg = next(
                        (m["content"] for m in reversed(messages) if m["role"] == "user"),
                        ""
                    )
                    # Очищаем от контекста для классификации
                    clean_msg = last_user_msg.split("═══════════════════════════════════════════════════════════════")[0].strip()
                    clean_msg = clean_msg.split("📚 КОНТЕКСТ")[0].strip()
                    
                    complexity = classify_query_complexity(clean_msg)
                    model = OPENROUTER_MODELS[complexity]["model"]
                    logger.info(f"🎯 Auto-routed: query='{clean_msg[:50]}...' → complexity={complexity} → model={model}")
                else:
                    model = OPENROUTER_MODELS["standard"]["model"]
                    logger.info(f"🎯 Using default: {model}")
            
            # Определяем параметры запроса
            reasoning_models = ["o3-mini", "o1-mini", "o1-pro", "o1", "o3"]
            request_params = {
                "model": model,
                "messages": messages
            }
            
            # Добавляем temperature только для не-reasoning моделей
            if not any(r in model.lower() for r in reasoning_models):
                request_params["temperature"] = temperature
            
            # Выполняем запрос
            response = await self.client.chat.completions.create(**request_params)
            
            # Собираем статистику
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            
            # Считаем стоимость (используем конфиг или реальную из ответа)
            model_costs = next(
                (cfg for cfg in OPENROUTER_MODELS.values() if cfg["model"] == model),
                OPENROUTER_MODELS["standard"]
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
                "complexity": complexity or "standard",
                "provider": "openrouter"
            }
            
            return response.choices[0].message.content, usage_info
            
        except Exception as e:
            logger.error(f"OpenRouter error: {e}", exc_info=True)
            raise

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

