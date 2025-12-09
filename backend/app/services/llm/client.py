
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional

class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4o",
        temperature: float = 0.7
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {e}")
            return "Извините, произошла ошибка при обращении к AI."

