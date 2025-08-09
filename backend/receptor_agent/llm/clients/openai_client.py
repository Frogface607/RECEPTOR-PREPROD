from __future__ import annotations
import os, json
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
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=0.5, max=4),
    retry=retry_if_exception_type((APITimeoutError, RateLimitError))
)
def call_structured(system: str, user: str, json_schema: Dict[str, Any], model: Optional[str] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
    cli = get_client()
    if cli is None:
        raise RuntimeError("LLM_DISABLED")

    mdl = model or os.getenv("TECHCARDS_V2_MODEL", "gpt-4o-mini")
    tmo = float(os.getenv("TECHCARDS_V2_REQUEST_TIMEOUT", str(timeout or 25)))

    # Chat Completions API + response_format json_schema (Structured Outputs)
    # https://platform.openai.com/docs/guides/structured-outputs
    resp = cli.chat.completions.create(
        model=mdl,
        timeout=tmo,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "techcard_schema",
                "schema": json_schema,
                "strict": False  # Убираем strict mode для совместимости
            }
        }
    )
    
    # Извлекаем JSON из response
    try:
        content = resp.choices[0].message.content
        if not content:
            raise APIError("Empty response content")
        return json.loads(content)
    except (json.JSONDecodeError, IndexError) as e:
        raise APIError(f"Failed to parse structured output: {e}")