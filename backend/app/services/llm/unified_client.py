"""
Unified LLM Client - использует OpenRouter (лучшие модели) или OpenAI (fallback)
"""
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class UnifiedLLMClient:
    """
    Универсальный клиент: OpenRouter (приоритет) → OpenAI (fallback)
    """
    def __init__(self, openrouter_key: Optional[str] = None, openai_key: Optional[str] = None):
        self.openrouter_client = None
        self.openai_client = None
        self.primary_provider = None
        
        # Пробуем OpenRouter сначала
        if openrouter_key:
            try:
                from .openrouter_client import OpenRouterClient
                self.openrouter_client = OpenRouterClient(api_key=openrouter_key)
                self.primary_provider = "openrouter"
                logger.info("✅ Using OpenRouter as primary LLM provider")
            except Exception as e:
                logger.warning(f"⚠️ OpenRouter init failed: {e}")
        
        # Fallback на OpenAI
        if openai_key:
            try:
                from .client import OpenAIClient
                self.openai_client = OpenAIClient(api_key=openai_key)
                if not self.primary_provider:
                    self.primary_provider = "openai"
                    logger.info("✅ Using OpenAI as LLM provider")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI init failed: {e}")
        
        if not self.primary_provider:
            raise ValueError("No LLM provider available! Need OPENROUTER_API_KEY or OPENAI_API_KEY")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        auto_route: bool = True,
        complexity: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Генерация ответа через лучший доступный провайдер
        """
        # Пробуем OpenRouter сначала
        if self.openrouter_client:
            try:
                response, usage = await self.openrouter_client.chat_completion(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    auto_route=auto_route,
                    complexity=complexity
                )
                return response, usage
            except Exception as e:
                logger.warning(f"⚠️ OpenRouter failed, falling back to OpenAI: {e}")
        
        # Fallback на OpenAI
        if self.openai_client:
            response, usage = await self.openai_client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                auto_route=auto_route
            )
            return response, usage
        
        raise RuntimeError("No LLM provider available!")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования"""
        stats = {
            "primary_provider": self.primary_provider,
            "openrouter": None,
            "openai": None
        }
        
        if self.openrouter_client:
            stats["openrouter"] = self.openrouter_client.get_usage_stats()
        if self.openai_client:
            stats["openai"] = self.openai_client.get_usage_stats()
        
        return stats

