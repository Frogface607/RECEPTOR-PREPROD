"""
Deep Research Agent - автоматическое исследование заведения
Собирает информацию из интернета и создаёт досье для персонализации
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def conduct_deep_research(
    venue_name: str,
    city: str,
    web_search_func,
    llm_client
) -> Dict[str, Any]:
    """
    Проводит глубокое исследование заведения
    
    Returns:
        Структурированное досье с информацией о заведении
    """
    logger.info(f"🔬 Starting deep research for: {venue_name}, {city}")
    
    # Фаза 1: Сбор информации
    research_data = await gather_information(venue_name, city, web_search_func)
    
    # Фаза 2: Анализ (reasoning model)
    analysis = await analyze_research(venue_name, city, research_data, llm_client)
    
    # Фаза 3: Структурирование досье
    dossier = create_dossier(venue_name, city, research_data, analysis)
    
    logger.info(f"✅ Deep research completed for {venue_name}")
    return dossier


async def gather_information(
    venue_name: str,
    city: str,
    web_search_func
) -> Dict[str, Any]:
    """
    Собирает информацию через web search
    """
    searches = {}
    
    # 1. Общая информация + отзывы
    try:
        logger.info(f"🔍 Searching reviews for {venue_name} {city}...")
        result = await web_search_func(
            f"{venue_name} {city} отзывы меню",
            max_results=5
        )
        logger.info(f"✅ Reviews search: {len(result.get('results', []))} results")
        searches["reviews"] = result
    except Exception as e:
        logger.error(f"❌ Reviews search failed: {e}", exc_info=True)
        searches["reviews"] = {"results": [], "error": str(e)}
    
    # 2. Соцсети
    try:
        logger.info(f"🔍 Searching social media...")
        result = await web_search_func(
            f"{venue_name} {city} Instagram VK Telegram",
            max_results=3
        )
        logger.info(f"✅ Social search: {len(result.get('results', []))} results")
        searches["social"] = result
    except Exception as e:
        logger.error(f"❌ Social search failed: {e}", exc_info=True)
        searches["social"] = {"results": [], "error": str(e)}
    
    # 3. Конкуренты
    try:
        logger.info(f"🔍 Searching competitors...")
        result = await web_search_func(
            f"рестораны бары {city} похожие на {venue_name}",
            max_results=5
        )
        logger.info(f"✅ Competitors search: {len(result.get('results', []))} results")
        searches["competitors"] = result
    except Exception as e:
        logger.error(f"❌ Competitors search failed: {e}", exc_info=True)
        searches["competitors"] = {"results": [], "error": str(e)}
    
    return searches


async def analyze_research(
    venue_name: str,
    city: str,
    research_data: Dict[str, Any],
    llm_client
) -> Dict[str, Any]:
    """
    Анализирует собранную информацию через reasoning model
    """
    logger.info(f"🧠 Starting AI analysis with o3-mini...")
    
    # Подготавливаем промпт для анализа
    prompt = f"""Проанализируй информацию о заведении "{venue_name}" в городе {city}.

СОБРАННЫЕ ДАННЫЕ:

## Отзывы и общая информация:
{format_search_results(research_data.get("reviews", {}))}

## Социальные сети:
{format_search_results(research_data.get("social", {}))}

## Конкуренты:
{format_search_results(research_data.get("competitors", {}))}

---

ЗАДАЧА: Создай структурированное досье в формате JSON:

{{
  "summary": "Краткое описание заведения (2-3 предложения)",
  "positioning": "Позиционирование (какой сегмент, концепция)",
  "strengths": ["сильная сторона 1", "сильная сторона 2", ...],
  "weaknesses": ["слабое место 1", "слабое место 2", ...],
  "popular_items": ["популярная позиция 1", ...],
  "price_segment": "эконом/средний/средний+/премиум",
  "avg_check_estimate": "диапазон среднего чека",
  "rating_estimate": "примерный рейтинг если нашёл",
  "competitors": [
    {{"name": "название", "positioning": "чем отличается", "price": "примерная цена"}}
  ],
  "opportunities": ["возможность для улучшения 1", ...],
  "threats": ["угроза/риск 1", ...]
}}

Отвечай ТОЛЬКО JSON, без дополнительного текста."""

    try:
        # Используем reasoning model для глубокого анализа
        logger.info(f"🧠 Calling o3-mini for reasoning analysis...")
        
        # Пробуем o3-mini, если не получается - fallback на gpt-4o
        try:
            response, usage = await llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "Ты бизнес-аналитик ресторанного рынка. Анализируешь данные и создаёшь структурированные досье."},
                    {"role": "user", "content": prompt}
                ],
                model="o3-mini",  # Reasoning для глубокого анализа
                auto_route=False
            )
        except Exception as model_error:
            logger.warning(f"⚠️ o3-mini unavailable, using gpt-4o: {model_error}")
            response, usage = await llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "Ты бизнес-аналитик ресторанного рынка. Анализируешь данные и создаёшь структурированные досье."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o",
                auto_route=False
            )
        
        logger.info(f"✅ AI analysis completed. Model: {usage.get('model')}, Cost: ${usage.get('cost_usd', 0):.4f}")
        
        # Парсим JSON из ответа
        import json
        import re
        
        # Ищем JSON в ответе
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
            logger.info(f"✅ Parsed analysis: {len(analysis.get('strengths', []))} strengths, {len(analysis.get('weaknesses', []))} weaknesses")
        else:
            logger.error(f"❌ Failed to parse JSON from response")
            analysis = {"error": "Failed to parse JSON", "raw_response": response[:500]}
        
        return analysis
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return {"error": str(e)}


def format_search_results(search_data: Dict[str, Any]) -> str:
    """Форматирует результаты поиска для промпта"""
    if not search_data.get("results"):
        return "Информация не найдена"
    
    formatted = []
    for r in search_data["results"][:5]:
        formatted.append(f"- {r.get('title', 'N/A')}\n  {r.get('content', '')[:300]}")
    
    return "\n\n".join(formatted)


def create_dossier(
    venue_name: str,
    city: str,
    research_data: Dict[str, Any],
    analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Создаёт финальное досье для сохранения в БД
    """
    return {
        "venue_name": venue_name,
        "city": city,
        "research_date": datetime.utcnow().isoformat(),
        
        # Анализ от AI
        "summary": analysis.get("summary", ""),
        "positioning": analysis.get("positioning", ""),
        "strengths": analysis.get("strengths", []),
        "weaknesses": analysis.get("weaknesses", []),
        "popular_items": analysis.get("popular_items", []),
        "opportunities": analysis.get("opportunities", []),
        "threats": analysis.get("threats", []),
        
        # Метрики
        "price_segment": analysis.get("price_segment", "unknown"),
        "avg_check_estimate": analysis.get("avg_check_estimate", "unknown"),
        "rating_estimate": analysis.get("rating_estimate", "unknown"),
        
        # Конкуренты
        "competitors": analysis.get("competitors", []),
        
        # Сырые данные (для отладки)
        "raw_sources": {
            "reviews_count": len(research_data.get("reviews", {}).get("results", [])),
            "social_count": len(research_data.get("social", {}).get("results", [])),
            "competitors_count": len(research_data.get("competitors", {}).get("results", []))
        }
    }


def format_dossier_for_context(dossier: Dict[str, Any]) -> str:
    """
    Форматирует досье для добавления в контекст чата
    """
    if not dossier:
        return ""
    
    context = f"""
### 🏢 ИССЛЕДОВАНИЕ ЗАВЕДЕНИЯ: {dossier.get('venue_name', 'N/A')}

**Город:** {dossier.get('city', 'N/A')}  
**Дата исследования:** {dossier.get('research_date', 'N/A')[:10]}

**Описание:** {dossier.get('summary', 'N/A')}

**Позиционирование:** {dossier.get('positioning', 'N/A')}

**Ценовой сегмент:** {dossier.get('price_segment', 'N/A')}  
**Средний чек:** {dossier.get('avg_check_estimate', 'N/A')}

**✅ Сильные стороны:**
{format_list(dossier.get('strengths', []))}

**⚠️ Слабые места (из отзывов):**
{format_list(dossier.get('weaknesses', []))}

**🔥 Популярные позиции:**
{format_list(dossier.get('popular_items', []))}

**💡 Возможности для роста:**
{format_list(dossier.get('opportunities', []))}

**🏪 Основные конкуренты:**
{format_competitors(dossier.get('competitors', []))}
"""
    
    return context


def format_list(items: List[str]) -> str:
    """Форматирует список для вывода"""
    if not items:
        return "- Нет данных"
    return "\n".join([f"- {item}" for item in items])


def format_competitors(competitors: List[Dict[str, Any]]) -> str:
    """Форматирует список конкурентов"""
    if not competitors:
        return "- Нет данных"
    
    formatted = []
    for c in competitors[:5]:
        name = c.get("name", "N/A")
        pos = c.get("positioning", "")
        price = c.get("price", "")
        formatted.append(f"- **{name}** — {pos} ({price})")
    
    return "\n".join(formatted)

