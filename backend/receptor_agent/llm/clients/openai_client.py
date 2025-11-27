from __future__ import annotations
import os, json, time
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError

def _enabled() -> bool:
    return os.getenv("TECHCARDS_V2_USE_LLM", "false").lower() in ("1","true","yes","on") and bool(os.getenv("OPENAI_API_KEY"))

_client: Optional[OpenAI] = None

def get_client() -> Optional[OpenAI]:
    global _client
    if not _enabled():
        return None
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client

@retry(
    reraise=True,
    stop=stop_after_attempt(2),  # retries=1 означает 1 retry = 2 попытки всего
    wait=wait_exponential(multiplier=1, min=0.5, max=1.5),  # 500→1500 мс
    retry=retry_if_exception_type((APITimeoutError, RateLimitError))
)
def call_structured(system: str, user: str, json_schema: Dict[str, Any], 
                   model: Optional[str] = None, timeout_ms: Optional[int] = None,
                   max_tokens: Optional[int] = None,
                   temperature: Optional[float] = None, top_p: Optional[float] = None,
                   presence_penalty: Optional[float] = None, frequency_penalty: Optional[float] = None,
                   stage: str = "llm_call") -> Dict[str, Any]:
    """
    Вызов LLM с инструментированием времени выполнения
    
    Args:
        stage: Название стадии для логирования ("draft", "normalize", etc.)
        timeout_ms: Таймаут в миллисекундах (default: 20000)
        max_tokens: Максимум токенов для ответа
    """
    cli = get_client()
    if cli is None:
        raise RuntimeError("LLM_DISABLED")

    start_time = time.time()
    
    try:
        mdl = model or os.getenv("TECHCARDS_V2_MODEL", "gpt-5-mini")
        # GX-01-FINAL: timeout_ms=20000 по умолчанию
        timeout_seconds = (timeout_ms or 20000) / 1000.0
        
        print(f"🔄 {stage}: Starting LLM call (model={mdl}) with timeout {timeout_seconds}s")

        # Chat Completions API + response_format json_schema (Structured Outputs)
        params = {
            "model": mdl,
            "timeout": timeout_seconds,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "techcard_schema",
                    "schema": json_schema,
                    "strict": False
                }
            }
        }
        
        # GX-01-FINAL: добавляем max_tokens если указано
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        # Добавляем дополнительные параметры если они указаны
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p  
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
            
        resp = cli.chat.completions.create(**params)
        
        # Логирование времени выполнения
        elapsed_ms = int((time.time() - start_time) * 1000)
        print(f"✅ {stage}: Completed in {elapsed_ms}ms")
        
        # Извлекаем JSON из response
        try:
            content = resp.choices[0].message.content
            if not content:
                raise APIError("Empty response content")
            return json.loads(content)
        except (json.JSONDecodeError, IndexError) as e:
            raise APIError(f"Failed to parse structured output: {e}")
            
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        print(f"❌ {stage}: Failed after {elapsed_ms}ms - {error_msg}")
        
        # Если модель не найдена, пробуем fallback на gpt-4o-mini
        if "model" in error_msg.lower() and ("not found" in error_msg.lower() or "invalid" in error_msg.lower() or "does not exist" in error_msg.lower()):
            print(f"⚠️ Model {mdl} not available, trying fallback to gpt-4o-mini...")
            try:
                params["model"] = "gpt-4o-mini"
                resp = cli.chat.completions.create(**params)
                elapsed_ms = int((time.time() - start_time) * 1000)
                print(f"✅ {stage}: Completed with fallback model in {elapsed_ms}ms")
                content = resp.choices[0].message.content
                if not content:
                    raise APIError("Empty response content")
                return json.loads(content)
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {str(fallback_error)}")
                raise e  # Raise original error
        
        raise