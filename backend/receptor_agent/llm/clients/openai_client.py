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

        # Chat Completions API + response_format
        # GPT-5-mini may not support json_schema, use json format instead
        params = {
            "model": mdl,
            "timeout": timeout_seconds,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        }
        
        # Use json_schema for older models, json_object for gpt-5-mini
        # Note: gpt-5-mini may have issues with reasoning tokens and empty content
        if mdl == "gpt-5-mini" or "gpt-5" in mdl:
            # Try json_schema first - it might work better than json_object
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "techcard_schema",
                    "schema": json_schema,
                    "strict": False
                }
            }
            print(f"🔧 {stage}: Using json_schema format for {mdl}")
        else:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "techcard_schema",
                    "schema": json_schema,
                    "strict": False
                }
            }
        
        # GPT-5-mini requires max_completion_tokens instead of max_tokens
        if max_tokens:
            if mdl == "gpt-5-mini" or "gpt-5" in mdl:
                params["max_completion_tokens"] = max_tokens
                print(f"🔧 Using max_completion_tokens={max_tokens} for {mdl}")
            else:
                params["max_tokens"] = max_tokens
                print(f"🔧 Using max_tokens={max_tokens} for {mdl}")
        
        # GPT-5-mini only supports default temperature (1), no custom parameters
        # Добавляем дополнительные параметры только для старых моделей
        if mdl != "gpt-5-mini" and "gpt-5" not in mdl:
            if temperature is not None:
                params["temperature"] = temperature
            if top_p is not None:
                params["top_p"] = top_p  
            if presence_penalty is not None:
                params["presence_penalty"] = presence_penalty
            if frequency_penalty is not None:
                params["frequency_penalty"] = frequency_penalty
        else:
            print(f"🔧 Skipping custom parameters (temperature, top_p, etc.) for {mdl} - using defaults")
            
        resp = cli.chat.completions.create(**params)
        
        # Логирование времени выполнения
        elapsed_ms = int((time.time() - start_time) * 1000)
        print(f"✅ {stage}: Completed in {elapsed_ms}ms")
        
        # Извлекаем JSON из response
        try:
            if not resp.choices or len(resp.choices) == 0:
                raise ValueError("No choices in response")
            
            message = resp.choices[0].message
            
            # Получаем content напрямую
            content = message.content if hasattr(message, 'content') else None
            print(f"🔍 {stage}: Content check - exists: {content is not None}, type: {type(content)}, length: {len(content) if content else 0}, value preview: {repr(content)[:100] if content else 'None'}")
            
            # Проверяем, что content не пустой
            if not content or (isinstance(content, str) and len(content.strip()) == 0):
                print(f"⚠️ {stage}: Content is empty, checking response details...")
                print(f"🔍 {stage}: Full message dict keys: {list(message.model_dump().keys()) if hasattr(message, 'model_dump') else 'N/A'}")
                
                # Проверяем другие возможные места для ответа
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print(f"🔍 {stage}: Found tool_calls: {message.tool_calls}")
                if hasattr(message, 'refusal') and message.refusal:
                    print(f"🔍 {stage}: Found refusal: {message.refusal}")
                if hasattr(resp, 'model'):
                    print(f"🔍 {stage}: Model used: {resp.model}")
                if hasattr(resp, 'usage'):
                    usage = resp.usage
                    print(f"🔍 {stage}: Usage - completion_tokens: {usage.completion_tokens if hasattr(usage, 'completion_tokens') else 'N/A'}")
                    if hasattr(usage, 'completion_tokens_details') and hasattr(usage.completion_tokens_details, 'reasoning_tokens'):
                        reasoning = usage.completion_tokens_details.reasoning_tokens
                        print(f"🔍 {stage}: Reasoning tokens: {reasoning}")
                        if reasoning > 0:
                            print(f"⚠️ {stage}: Model used {reasoning} reasoning tokens - gpt-5-mini may require different approach for reasoning models")
                
                # Попробуем получить content через model_dump если доступно
                if hasattr(message, 'model_dump'):
                    msg_dict = message.model_dump()
                    print(f"🔍 {stage}: Message dict content field: {repr(msg_dict.get('content', 'NOT_FOUND'))[:200]}")
                    if 'content' in msg_dict and msg_dict['content']:
                        content = msg_dict['content']
                        print(f"✅ {stage}: Found content in model_dump!")
                
                if not content:
                    raise ValueError("Empty response content - gpt-5-mini may not support json_object format or requires different approach")
            
            parsed = json.loads(content)
            print(f"✅ {stage}: Successfully parsed JSON response")
            return parsed
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            error_detail = f"Failed to parse structured output: {e}"
            print(f"❌ {stage}: {error_detail}")
            if hasattr(resp, 'choices') and resp.choices and hasattr(resp.choices[0].message, 'content'):
                content_preview = str(resp.choices[0].message.content)[:200] if resp.choices[0].message.content else "None"
                print(f"🔍 Response content preview: {content_preview}")
            raise ValueError(error_detail)
            
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        # Безопасное получение сообщения об ошибке
        try:
            error_msg = str(e)
            error_type = type(e).__name__
        except Exception:
            error_msg = "Unknown error"
            error_type = "Unknown"
        print(f"❌ {stage}: Failed after {elapsed_ms}ms - {error_type}: {error_msg}")
        
        # Если модель не найдена или неправильный параметр, пробуем fallback на gpt-4o-mini
        if ("model" in error_msg.lower() and ("not found" in error_msg.lower() or "invalid" in error_msg.lower() or "does not exist" in error_msg.lower())) or \
           ("unsupported parameter" in error_msg.lower() and "max_tokens" in error_msg.lower()):
            print(f"⚠️ Model {mdl} issue detected, trying fallback to gpt-4o-mini...")
            try:
                # Исправляем параметры для fallback модели
                fallback_params = params.copy()
                fallback_params["model"] = "gpt-4o-mini"
                # Убираем max_completion_tokens и используем max_tokens для gpt-4o-mini
                if "max_completion_tokens" in fallback_params:
                    if "max_tokens" not in fallback_params and max_tokens:
                        fallback_params["max_tokens"] = max_tokens
                    del fallback_params["max_completion_tokens"]
                resp = cli.chat.completions.create(**fallback_params)
                elapsed_ms = int((time.time() - start_time) * 1000)
                print(f"✅ {stage}: Completed with fallback model in {elapsed_ms}ms")
                content = resp.choices[0].message.content
                if not content:
                    raise ValueError("Empty response content")
                return json.loads(content)
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {str(fallback_error)}")
                raise e  # Raise original error
        
        raise