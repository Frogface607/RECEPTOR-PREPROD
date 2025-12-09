"""
Web Search через Tavily API для актуальной информации
https://tavily.com - $5/мес за 1000 запросов
"""
import os
import httpx
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_BASE_URL = "https://api.tavily.com"


async def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",  # "basic" или "advanced"
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None
) -> Dict:
    """
    Поиск в интернете через Tavily API.
    
    Args:
        query: Поисковый запрос
        max_results: Максимум результатов (1-10)
        search_depth: "basic" (быстрый) или "advanced" (глубокий)
        include_domains: Искать только на этих доменах
        exclude_domains: Исключить эти домены
    
    Returns:
        {
            "query": str,
            "results": [{"title": str, "url": str, "content": str, "score": float}],
            "answer": str (краткий ответ от Tavily AI)
        }
    """
    if not TAVILY_API_KEY:
        logger.warning("⚠️ TAVILY_API_KEY not set, web search disabled")
        return {
            "query": query,
            "results": [],
            "answer": None,
            "error": "Web search not configured"
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": True,  # Получаем AI-саммари
            }
            
            if include_domains:
                payload["include_domains"] = include_domains
            if exclude_domains:
                payload["exclude_domains"] = exclude_domains
            
            response = await client.post(
                f"{TAVILY_BASE_URL}/search",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "query": query,
                "results": [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:500],  # Ограничиваем
                        "score": r.get("score", 0)
                    }
                    for r in data.get("results", [])
                ],
                "answer": data.get("answer"),  # AI-generated answer
                "error": None
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Tavily API error: {e.response.status_code} - {e.response.text}")
        return {"query": query, "results": [], "answer": None, "error": str(e)}
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {"query": query, "results": [], "answer": None, "error": str(e)}


def format_search_results_for_context(search_result: Dict) -> str:
    """Форматирует результаты поиска для добавления в контекст LLM"""
    if not search_result.get("results") and not search_result.get("answer"):
        return ""
    
    context = "\n\n### 🌐 АКТУАЛЬНАЯ ИНФОРМАЦИЯ ИЗ ИНТЕРНЕТА ###\n"
    
    # AI-ответ от Tavily (если есть)
    if search_result.get("answer"):
        context += f"\n📝 Краткий ответ: {search_result['answer']}\n"
    
    # Детальные результаты
    if search_result.get("results"):
        context += "\n📰 Источники:\n"
        for i, r in enumerate(search_result["results"][:3], 1):  # Топ-3
            context += f"{i}. **{r['title']}**\n"
            context += f"   {r['content'][:300]}...\n"
            context += f"   🔗 {r['url']}\n\n"
    
    return context


def should_use_web_search(query: str) -> bool:
    """Определяет, нужен ли веб-поиск для данного запроса"""
    query_lower = query.lower()
    
    # Триггеры для веб-поиска
    web_triggers = [
        "тренд", "новост", "актуальн", "сейчас", "2025", "2024",
        "последн", "свежий", "новый", "современн",
        "тикток", "tiktok", "инстаграм", "instagram", "вирусн",
        "популярн", "хайп", "что модно", "что в тренде",
        "цена", "стоимост", "курс", "рынок", "прогноз",
        "конкурент", "новинк", "открыл", "закрыл"
    ]
    
    return any(trigger in query_lower for trigger in web_triggers)

