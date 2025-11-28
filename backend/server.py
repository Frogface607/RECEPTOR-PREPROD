# Добавляем endpoint для deep research после endpoint /assistant/conversations/{conversation_id}

@api_router.post("/venue/deep-research")
async def deep_research_venue(request: dict):
    """
    Глубокое исследование заведения через web search
    
    Request:
    {
        "user_id": "uuid",
        "venue_name": "Ресторан 'Уют'",
        "city": "Москва",
        "description": "Опциональное описание заведения"
    }
    
    Response:
    {
        "success": true,
        "research_data": {
            "competitor_analysis": "...",
            "customer_reviews_summary": "...",
            "market_position": "...",
            "recommendations": "..."
        },
        "tokens_used": 500,
        "credits_spent": 50
    }
    """
    user_id = request.get("user_id")
    venue_name = request.get("venue_name", "").strip()
    city = request.get("city", "").strip()
    description = request.get("description", "").strip()
    
    if not user_id or not venue_name or not city:
        raise HTTPException(status_code=400, detail="user_id, venue_name и city обязательны")
    
    try:
        # TODO: Реализовать web search через доступные инструменты
        # Пока возвращаем заглушку
        
        # Формируем поисковые запросы
        search_queries = [
            f"{venue_name} {city} отзывы",
            f"{venue_name} {city} ресторан",
            f"рестораны {city} похожие на {venue_name}",
            f"{venue_name} {city} меню цены"
        ]
        
        # Здесь будет web search
        # Пока используем LLM для анализа на основе описания
        research_prompt = f"""Проведи глубокий анализ ресторана для персонализации AI-ассистента.

Название: {venue_name}
Город: {city}
Описание: {description if description else 'Не указано'}

Проанализируй и предоставь:
1. Анализ конкурентов в городе {city}
2. Рекомендации по позиционированию
3. Советы по улучшению на основе лучших практик
4. Персонализированные рекомендации для этого заведения

Будь конкретным и практичным. Отвечай на русском языке."""

        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI client not initialized")
        
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по ресторанному бизнесу. Проводишь глубокий анализ заведений для персонализации AI-ассистента."},
                {"role": "user", "content": research_prompt}
            ],
            temperature=0.7,
            max_completion_tokens=2000
        )
        
        research_text = response.choices[0].message.content
        
        # Сохраняем результаты исследования
        research_data = {
            "user_id": user_id,
            "venue_name": venue_name,
            "city": city,
            "research_data": {
                "competitor_analysis": research_text[:500] + "...",
                "customer_reviews_summary": "Анализ отзывов будет доступен после интеграции web search",
                "market_position": research_text[500:1000] + "...",
                "recommendations": research_text[1000:] if len(research_text) > 1000 else research_text
            },
            "created_at": datetime.now().isoformat(),
            "tokens_used": response.usage.total_tokens
        }
        
        await db.venue_research.update_one(
            {"user_id": user_id},
            {"$set": research_data},
            upsert=True
        )
        
        return {
            "success": True,
            "research_data": research_data["research_data"],
            "tokens_used": response.usage.total_tokens,
            "credits_spent": 50
        }
        
    except Exception as e:
        logger.error(f"Deep research error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка исследования: {str(e)}")
