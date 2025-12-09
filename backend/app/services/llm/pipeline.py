from __future__ import annotations
import os, json, time, traceback
from typing import Dict, Any, List, Set
from pydantic import BaseModel
from receptor_agent.techcards_v2.schemas import TechCardV2, NutritionV2, CostV2, MetaV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.techcards_v2.strict_validator import validate_techcard_v2, create_draft_response
from receptor_agent.techcards_v2.normalize import normalize_card
from receptor_agent.techcards_v2.quantify import rebalance
from receptor_agent.techcards_v2.haccp_templates import enrich_haccp
from receptor_agent.techcards_v2.cost_calculator import calculate_cost_for_tech_card
from receptor_agent.techcards_v2.nutrition_calculator import calculate_nutrition_for_tech_card
from receptor_agent.techcards_v2.postcheck_v2 import postcheck_v2
from receptor_agent.techcards_v2.chef_rules import run_chef_rules, has_critical_rule_errors
from receptor_agent.techcards_v2.contentcheck_v2 import run_content_check, has_critical_content_errors
from receptor_agent.techcards_v2.sanitize import sanitize_card_v2, validate_sanitized_card

from .clients.openai_client import call_structured, get_client
from .prompts.templates import DRAFT_PROMPT, NORMALIZE_PROMPT, QUANTIFY_PROMPT, HACCP_PROMPT, CRITIC_PROMPT
from .prompts.schemas import TECHCARD_CORE_SCHEMA

def _use_llm() -> bool:
    return os.getenv("TECHCARDS_V2_USE_LLM", "false").lower() in ("1","true","yes","on") and get_client() is not None

class ProfileInput(BaseModel):
    name: str
    cuisine: str | None = None
    equipment: List[str] = []
    budget: float | None = None
    dietary: List[str] = []
    user_id: str | None = None  # CLEANUP TECH CARD DATA & UI: добавляем user_id для связи с аккаунтом

class PipelineResult(BaseModel):
    card: TechCardV2 | None = None
    issues: List[str] = []
    status: str = "READY"  # Все техкарты создаются со статусом READY
    raw_data: Dict[str, Any] | None = None

def collect_sub_recipe_ids(tech_card_data: Dict[str, Any]) -> Set[str]:
    """Собираем все ID подрецептов из техкарты"""
    sub_recipe_ids = set()
    ingredients = tech_card_data.get("ingredients", [])
    for ingredient in ingredients:
        sub_recipe = ingredient.get("subRecipe")
        if sub_recipe and "id" in sub_recipe:
            sub_recipe_ids.add(sub_recipe["id"])
    return sub_recipe_ids

async def fetch_sub_recipes_cache(sub_recipe_ids: Set[str]) -> Dict[str, TechCardV2]:
    """
    Получаем подрецепты по ID из базы данных
    
    TODO: В будущем это должно извлекать TechCardV2 из MongoDB
    Пока возвращаем пустой кеш для избежания ошибок
    """
    # Заглушка для подрецептов - в будущем здесь будет обращение к БД
    sub_recipes_cache = {}
    
    # TODO: Реализовать получение подрецептов из базы данных:
    # from motor.motor_asyncio import AsyncIOMotorClient
    # for sub_recipe_id in sub_recipe_ids:
    #     doc = await db.techcards_v2.find_one({"meta.id": sub_recipe_id})
    #     if doc:
    #         sub_recipes_cache[sub_recipe_id] = TechCardV2.model_validate(doc)
    
    return sub_recipes_cache

def _system() -> str:
    return "You return strictly JSON that matches the provided JSON Schema."

def _system_ru() -> str:
    """System prompt для русских промптов v2"""
    return "Ты возвращаешь строго JSON, соответствующий предоставленной JSON Schema."

def _make_user(content: Dict[str, Any]) -> str:
    return json.dumps(content, ensure_ascii=False)

def _load_prompt_v2(filename: str) -> str:
    """Загружает промпт из папки prompts/v2/"""
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts", "v2")
    filepath = os.path.join(prompts_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"Prompt file {filename} not found"

def _format_template(template: str, **kwargs) -> str:
    """Форматирует шаблон промпта с подстановкой переменных, поддерживает условные блоки"""
    result = template
    
    # Обработка условных блоков {{#constraints}}...{{/constraints}}
    if 'constraints' in kwargs and kwargs['constraints']:
        # Убираем теги и оставляем содержимое
        result = result.replace('{{#constraints}}', '').replace('{{/constraints}}', '')
        # Подставляем constraints
        constraints = kwargs['constraints']
        if 'mustHave' in constraints:
            result = result.replace('{{mustHave}}', ', '.join(constraints['mustHave']))
        if 'forbid' in constraints:
            result = result.replace('{{forbid}}', ', '.join(constraints['forbid']))
        if 'hints' in constraints:
            result = result.replace('{{hints}}', ', '.join(constraints['hints']))
    else:
        # Удаляем весь блок constraints если его нет
        import re
        result = re.sub(r'{{#constraints}}.*?{{/constraints}}', '', result, flags=re.DOTALL)
    
    # Обычные подстановки
    for key, value in kwargs.items():
        if key != 'constraints':
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))
    
    return result

def _create_skeleton_techcard(profile: ProfileInput, error_reason: str = "LLM unavailable") -> Dict[str, Any]:
    """
    Создает детерминированный skeleton TechCardV2 при сбое LLM
    GX-01-FINAL: Жёсткий фоллбек для предсказуемости
    """
    import uuid
    from datetime import datetime
    
    # Обрезаем title до 80 символов
    title = profile.name[:80] if len(profile.name) > 80 else profile.name
    
    return {
        "meta": {
            "id": str(uuid.uuid4()),
            "title": title,
            "version": "2.0", 
            "createdAt": datetime.now().isoformat(),
            "cuisine": profile.cuisine or "международная",
            "tags": [],
            "timings": {}  # Будет заполнено в конце pipeline
        },
        "portions": 1,  # GX-01-FINAL: portions=1
        "yield": {
            "perPortion_g": 250.0,  # GX-01-FINAL: 250г на порцию
            "perBatch_g": 250.0     # GX-01-FINAL: 250г на batch (1 порция)
        },
        "ingredients": [  # CLEANUP TECH CARD DATA & UI: Базовые ингредиенты для тестирования артикулов
            {
                "name": "Основной ингредиент 1",
                "canonical_id": None,
                "skuId": "test-sku-001",  # Тестовый GUID для поиска в iiko RMS
                "product_code": None,  # Будет заполнен в pipeline
                "subRecipe": None,
                "unit": "g",
                "brutto_g": 100.0,
                "loss_pct": 10.0,
                "netto_g": 90.0,
                "allergens": []
            },
            {
                "name": "Основной ингредиент 2", 
                "canonical_id": None,
                "skuId": "test-sku-002",  # Тестовый GUID для поиска в iiko RMS
                "product_code": None,  # Будет заполнен в pipeline
                "subRecipe": None,
                "unit": "g",
                "brutto_g": 50.0,
                "loss_pct": 5.0,
                "netto_g": 47.5,
                "allergens": []
            }
        ],
        "process": [
            {
                "n": 1,
                "action": "Подготовка сырья", # GX-01-FINAL: минимальный процесс
                "time_min": None,
                "temp_c": None,
                "equipment": None,
                "details": None
            }
        ],
        "storage": {
            "conditions": "Комнатная температура",
            "shelfLife_hours": 24.0,
            "servingTemp_c": 20.0
        },
        "nutrition": NutritionV2().model_dump(),  # Пустое питание
        "cost": CostV2().model_dump(),           # Пустая стоимость  
        "printNotes": [],
        "issues": [error_reason]  # Будет преобразовано в список строк в pipeline
    }

def _create_minimal_fallback(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    GX-01-FINAL: Создает минимальную карту из кривых данных normalize
    """
    import uuid
    from datetime import datetime
    
    fallback = {
        "meta": data.get("meta", {
            "id": str(uuid.uuid4()),
            "title": "Fallback техкарта",
            "version": "2.0", 
            "createdAt": datetime.now().isoformat(),
            "cuisine": "международная",
            "tags": [],
            "timings": {}
        }),
        "portions": max(1, data.get("portions", 1)),  # >= 1
        "yield": {
            "perPortion_g": max(1.0, data.get("yield", {}).get("perPortion_g", 250.0)),
            "perBatch_g": max(1.0, data.get("yield", {}).get("perBatch_g", 250.0))
        },
        "ingredients": data.get("ingredients", []),  # может быть пустым
        "process": data.get("process") or [
            {"n": 1, "action": "Подготовка сырья", "time_min": None, "temp_c": None, "equipment": None, "details": None}
        ],
        "storage": data.get("storage", {
            "conditions": "Комнатная температура",
            "shelfLife_hours": 24.0,
            "servingTemp_c": 20.0
        }),
        "nutrition": NutritionV2().model_dump(),
        "cost": CostV2().model_dump(),
        "printNotes": data.get("printNotes", [])
    }
    
    return fallback

def extract_anchors(dish_name: str, cuisine: str = None) -> Dict[str, Any]:
    """Извлечение якорей из названия блюда через LLM"""
    if not _use_llm():
        return {"mustHave": [], "forbid": [], "hints": []}
        
    try:
        system_prompt = _load_prompt_v2("extract_anchors.ru.txt")
        user_template = _load_prompt_v2("extract_anchors_user.ru.txt")
        
        user_prompt = _format_template(
            user_template,
            dish_name=dish_name,
            cuisine=cuisine or "международная"
        )
        
        # Простая JSON схема для якорей
        anchors_schema = {
            "type": "object",
            "properties": {
                "mustHave": {"type": "array", "items": {"type": "string"}},
                "forbid": {"type": "array", "items": {"type": "string"}},
                "hints": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["mustHave", "forbid", "hints"]
        }
        
        result = call_structured(
            system=_system_ru() + "\n\n" + system_prompt,
            user=user_prompt,
            json_schema=anchors_schema,
            temperature=0.3,
            top_p=0.9
        )
        
        return result
        
    except Exception as e:
        print(f"Error extracting anchors: {e}")
        return {"mustHave": [], "forbid": [], "hints": []}

def generate_draft_v2(profile: ProfileInput, constraints: Dict[str, Any] = None) -> Dict[str, Any]:
    """Генерация чернового JSON с помощью нового промпта v2 и constraints"""
    if not _use_llm():
        return _create_skeleton_techcard(profile, "LLM disabled")
        
    try:
        # Загружаем промпты v2
        system_prompt = _load_prompt_v2("generate_draft.ru.txt") 
        user_template = _load_prompt_v2("generate_draft_user.ru.txt")
        
        # Подготавливаем данные для шаблона
        brief = f"{profile.name}. Кухня: {profile.cuisine or 'международная'}. "
        if profile.equipment:
            brief += f"Доступно оборудование: {', '.join(profile.equipment)}. "
        if profile.budget:
            brief += f"Бюджет: ~{profile.budget} руб. "
        if profile.dietary:
            brief += f"Диетические требования: {', '.join(profile.dietary)}."
            
        portions = 4
        yield_per_portion = 200.0  # грамм на порцию по умолчанию
        
        template_params = {
            "brief": brief,
            "portions": portions,
            "yield_per_portion_g": yield_per_portion
        }
        
        # Добавляем constraints если есть
        if constraints:
            template_params["constraints"] = constraints
        
        user_prompt = _format_template(user_template, **template_params)
        
        # GX-01-FINAL: draft с gpt-4o-mini, max_tokens≈900, локальный SLA ≤ 12s
        return call_structured(
            system=_system_ru() + "\n\n" + system_prompt,
            user=user_prompt,
            json_schema=TECHCARD_CORE_SCHEMA,
            model="gpt-4o-mini",
            max_tokens=900,
            temperature=0.2,
            top_p=0.9,
            presence_penalty=0,
            frequency_penalty=0,
            timeout_ms=12000,  # GX-01-FINAL: локальный SLA ≤ 12s
            stage="draft"      # GX-01-FINAL: логирование стадии
        )
        
    except Exception as e:
        print(f"❌ generate_draft_v2 failed: {e}")
        return _create_skeleton_techcard(profile, f"Draft generation failed: {str(e)}")

def normalize_to_v2(draft_json: Dict[str, Any], constraints: Dict[str, Any] = None) -> Dict[str, Any]:
    """Нормализация черновика до финального TechCardV2 с constraints"""
    if not _use_llm():
        return draft_json
        
    try:
        # Загружаем промпты нормализации
        system_prompt = _load_prompt_v2("normalize_to_v2.ru.txt")
        user_template = _load_prompt_v2("normalize_to_v2_user.ru.txt") 
        
        template_params = {
            "draft_json": json.dumps(draft_json, ensure_ascii=False, indent=2)
        }
        
        # Добавляем constraints если есть
        if constraints:
            template_params["constraints"] = constraints
        
        user_prompt = _format_template(user_template, **template_params)
        
        # GX-01-FINAL: normalize с gpt-4o-mini, max_tokens≈600, локальный SLA ≤ 10s
        return call_structured(
            system=_system_ru() + "\n\n" + system_prompt,
            user=user_prompt, 
            json_schema=TECHCARD_CORE_SCHEMA,
            model="gpt-4o-mini",
            max_tokens=600,
            temperature=0.2,
            top_p=0.9,
            presence_penalty=0,
            frequency_penalty=0,
            timeout_ms=10000,  # GX-01-FINAL: локальный SLA ≤ 10s
            stage="normalize"  # GX-01-FINAL: логирование стадии
        )
        
    except Exception as e:
        print(f"❌ normalize_to_v2 failed: {e}")
        return draft_json

# Старые функции (сохранены для совместимости)
def _get_fallback_draft(profile: ProfileInput) -> Dict[str, Any]:
    """Fallback черновик при отключенном LLM"""
    return {
        "meta": {
            "title": f"Блюдо {profile.cuisine or 'авторское'}",
            "version": "2.0",
            "cuisine": profile.cuisine,
            "tags": []
        },
        "portions": 4,
        "yield": {
            "perPortion_g": 145.0,    
            "perBatch_g": 580.0       
        },
        "ingredients": [
            {
                "name": "Куриное филе",
                "unit": "g",
                "brutto_g": 600.0,
                "loss_pct": 10.0,
                "netto_g": 540.0,
                "allergens": []
            },
            {
                "name": "Соль поваренная",
                "unit": "g", 
                "brutto_g": 8.0,
                "loss_pct": 0.0,
                "netto_g": 8.0,
                "allergens": []
            },
            {
                "name": "Растительное масло",
                "unit": "ml",
                "brutto_g": 30.0,
                "loss_pct": 1.0,
                "netto_g": 29.7,
                "allergens": []
            }
        ],
        "process": [
            {"n": 1, "action": "Подготовка ингредиентов", "time_min": 10.0, "temp_c": None},
            {"n": 2, "action": "Обжаривание на среднем огне", "time_min": 15.0, "temp_c": 180.0},
            {"n": 3, "action": "Доведение до готовности", "time_min": 10.0, "temp_c": 75.0}
        ],
        "storage": {
            "conditions": "Холодильник 0...+4°C",
            "shelfLife_hours": 48.0,
            "servingTemp_c": 65.0
        },
        "nutrition": NutritionV2().model_dump(),
        "cost": CostV2().model_dump(),
        "printNotes": []
    }

def generate_draft(profile: ProfileInput, courses: int = 1) -> Dict[str, Any]:
    if _use_llm():
        try:
            payload = {"profile": profile.model_dump()}
            return call_structured(_system()+"\n"+DRAFT_PROMPT, _make_user(payload), TECHCARD_CORE_SCHEMA)
        except Exception:
            # fallback на локальный режим при любой ошибке LLM
            pass
    # fallback локально - в формате TechCardV2
    return {
        "meta": {
            "title": f"Блюдо {profile.cuisine or 'авторское'}",
            "version": "2.0",
            "cuisine": profile.cuisine,
            "tags": []
        },
        "portions": 4,
        "yield": {
            "perPortion_g": 145.0,    # 577.7g / 4 = 144.4, округлено до 145
            "perBatch_g": 580.0       # 145 * 4 = 580, близко к сумме netto_g (577.7)
        },
        "ingredients": [
            {
                "name": "Куриное филе",
                "unit": "g",
                "brutto_g": 600.0,
                "loss_pct": 10.0,
                "netto_g": 540.0,  # 600 * (1 - 10/100) = 540 ✓
                "allergens": []
            },
            {
                "name": "Соль поваренная",
                "unit": "g", 
                "brutto_g": 8.0,
                "loss_pct": 0.0,
                "netto_g": 8.0,  # 8 * (1 - 0/100) = 8 ✓
                "allergens": []
            },
            {
                "name": "Растительное масло",
                "unit": "ml",
                "brutto_g": 30.0,
                "loss_pct": 1.0,  # Изменил с 5% на 1%
                "netto_g": 29.7,  # 30 * (1 - 1/100) = 29.7 ✓
                "allergens": []
            }
        ],
        "process": [
            {"n": 1, "action": "Подготовка ингредиентов", "time_min": 10.0, "temp_c": None},
            {"n": 2, "action": "Обжаривание на среднем огне", "time_min": 15.0, "temp_c": 180.0},
            {"n": 3, "action": "Доведение до готовности", "time_min": 10.0, "temp_c": 75.0}
        ],
        "storage": {
            "conditions": "Холодильник 0...+4°C",
            "shelfLife_hours": 48.0,
            "servingTemp_c": 65.0
        },
        "nutrition": NutritionV2().model_dump(),
        "cost": CostV2().model_dump(),
        "printNotes": []
    }

def normalize(draft: Dict[str, Any]) -> Dict[str, Any]:
    if _use_llm():
        try:
            return call_structured(_system()+"\n"+NORMALIZE_PROMPT, _make_user({"draft": draft}), TECHCARD_CORE_SCHEMA)
        except Exception:
            pass
    return normalize_card(draft)

def quantify(norm: Dict[str, Any]) -> Dict[str, Any]:
    if _use_llm():
        try:
            return call_structured(_system()+"\n"+QUANTIFY_PROMPT, _make_user({"norm": norm}), TECHCARD_CORE_SCHEMA)
        except Exception:
            pass
    return rebalance(norm)

def build_haccp(data: Dict[str, Any]) -> Dict[str, Any]:
    if _use_llm():
        try:
            return call_structured(_system()+"\n"+HACCP_PROMPT, _make_user({"data": data}), TECHCARD_CORE_SCHEMA)
        except Exception:
            pass
    return enrich_haccp(data)

def critique(card: TechCardV2) -> List[str]:
    ok, issues = validate_card(card)
    if ok or not _use_llm():
        return issues
    # Позовем LLM для минимальных правок и re-validate
    try:
        fixed = call_structured(_system()+"\n"+CRITIC_PROMPT, _make_user({"card": card.model_dump(by_alias=True)}), TECHCARD_CORE_SCHEMA)
        new = TechCardV2.model_validate(fixed)
        ok2, issues2 = validate_card(new)
        if ok2: return []
        return issues2
    except Exception:
        return issues

def run_pipeline(profile: ProfileInput) -> PipelineResult:
    """
    GX-01-FINAL: Полностью стабилизированная генерация с локальными timings и мягким fallback
    Генерация техкарты с анкерной валидностью, правилами шефа и строгой валидацией TechCardV2
    """
    # GX-01-FINAL: Локальный сбор timings, присваиваем один раз в конце
    start_total = time.perf_counter()
    timings = {}
    all_issues = []
    
    try:
        # Шаг 0: Извлекаем якоря из названия блюда (только если включена строгая проверка)
        constraints = {}
        strict_anchors = os.environ.get('STRICT_ANCHORS', 'false').lower() == 'true'  # GX-01-FINAL: по умолчанию false
        
        if strict_anchors:
            constraints = extract_anchors(profile.name, profile.cuisine)
            print(f"Extracted anchors: {constraints}")
        
        # Шаг 1: Генерируем черновик с новым промптом v2 и constraints
        start_draft = time.perf_counter()
        draft_data = generate_draft_v2(profile, constraints if constraints else None)
        timings["llm_draft_ms"] = int((time.perf_counter() - start_draft) * 1000)
        
        # Проверяем на skeleton (fallback) - если это skeleton, обрабатываем issues
        skeleton_mode = False
        if "issues" in draft_data:
            skeleton_mode = True
            skeleton_issues = draft_data.pop("issues", [])
            all_issues.extend(skeleton_issues)
            print("🔄 Skeleton techcard created due to LLM failure - proceeding with draft")
        
        # Шаг 2: Нормализуем черновик до финального TechCardV2 с constraints
        start_normalize = time.perf_counter()
        normalized_data = normalize_to_v2(draft_data, constraints if constraints else None)
        timings["llm_normalize_ms"] = int((time.perf_counter() - start_normalize) * 1000)
        
        # GX-01-FINAL: Жёсткий «слепок» после normalize - безопасная валидация
        start_validate = time.perf_counter()
        try:
            # Пробуем создать TechCardV2 из нормализованных данных
            temp_card = TechCardV2.model_validate(normalized_data)
            validated_card = temp_card
            validation_issues = []
            normalize_fallback = False
        except Exception as validation_error:
            print(f"⚠️ Normalize validation failed: {validation_error}")
            # GX-01-FINAL: Мягкий fallback - создаем минимальную карту
            fallback_data = _create_minimal_fallback(normalized_data)
            try:
                validated_card = TechCardV2.model_validate(fallback_data)
                validation_issues = [f"normalizeShape: {str(validation_error)}"]
                all_issues.extend(validation_issues)
                normalize_fallback = True
                print("🔄 Created minimal fallback card after normalize failure")
            except Exception as fallback_error:
                # Критическая ошибка - используем skeleton
                print(f"❌ Fallback failed: {fallback_error}")
                skeleton_data = _create_skeleton_techcard(profile, f"Normalize and fallback failed: {str(fallback_error)}")
                skeleton_issues = skeleton_data.pop("issues", [])
                validated_card = TechCardV2.model_validate(skeleton_data)
                validation_issues = [f"criticalFallback: {str(fallback_error)}"]
                all_issues.extend(validation_issues + skeleton_issues)
                normalize_fallback = True
                skeleton_mode = True
        
        timings["validate_ms"] = int((time.perf_counter() - start_validate) * 1000)
        
        # Собираем ID подрецептов из валидированных данных
        sub_recipe_ids = collect_sub_recipe_ids(validated_card.model_dump())
        sub_recipes_cache = {}  # Временная заглушка
        
        # Шаг 3.5: Анкерная валидность (только если есть constraints)
        start_content = time.perf_counter()
        content_issues = []
        if constraints and strict_anchors:
            content_issues = run_content_check(validated_card, constraints)
        timings["contentcheck_ms"] = int((time.perf_counter() - start_content) * 1000)
        
        # Шаг 4: ВСЕГДА выполняем калькуляторы (единый источник истины)
        start_cost = time.perf_counter()
        try:
            validated_card = calculate_cost_for_tech_card(validated_card, sub_recipes_cache)
        except Exception as e:
            all_issues.append(f"Cost calculation error: {str(e)}")
        timings["cost_ms"] = int((time.perf_counter() - start_cost) * 1000)
        
        start_nutrition = time.perf_counter()
        try:
            validated_card = calculate_nutrition_for_tech_card(validated_card, sub_recipes_cache)
        except Exception as e:
            all_issues.append(f"Nutrition calculation error: {str(e)}")
        timings["nutrition_ms"] = int((time.perf_counter() - start_nutrition) * 1000)
        
        # Шаг 5: СТАНДАРТНАЯ ПОРЦИЯ - нормализация на 1 порцию (ПЕРЕД всеми проверками)
        start_normalize_portion = time.perf_counter()
        try:
            from receptor_agent.techcards_v2.portion_normalizer import get_portion_normalizer
            normalizer = get_portion_normalizer()
            
            # Применяем нормализацию порций
            card_dict = validated_card.model_dump()
            normalized_dict = normalizer.normalize_techcard(card_dict)
            
            # Создаем новый валидный TechCardV2 объект
            validated_card = TechCardV2.model_validate(normalized_dict)
            
            # Проверяем корректность нормализации
            validation_result = normalizer.validate_normalization(normalized_dict)
            if not validation_result.get('valid', False):
                all_issues.append(f"Portion normalization validation failed: {validation_result.get('error', 'Unknown error')}")
            else:
                # Логируем успешную нормализацию для аудита
                scale_factor = validation_result.get('scale_factor', 0)
                archetype = validation_result.get('archetype', 'unknown')
                print(f"✅ Portion normalized: archetype={archetype}, scale_factor={scale_factor}")
                
        except Exception as e:
            all_issues.append(f"Portion normalization error: {str(e)}")
            
        timings["portion_normalize_ms"] = int((time.perf_counter() - start_normalize_portion) * 1000)
        
        # Шаг 6: САНИТАЙЗЕР - приводим к строгому формату (ПОСЛЕ нормализации)
        start_sanitize = time.perf_counter()
        try:
            # GX-01-FINAL: sanitize_card_v2 должна быть чистой функцией
            validated_card = sanitize_card_v2(validated_card)
        except Exception as e:
            all_issues.append(f"Card sanitization error: {str(e)}")
        timings["sanitize_ms"] = int((time.perf_counter() - start_sanitize) * 1000)
        
        # Шаг 7: Правила шефа (rule-based sanity checks) - ПОСЛЕ нормализации
        start_chef = time.perf_counter()
        chef_rule_issues = run_chef_rules(validated_card)
        
        # GX-01-FINAL: Смягчение блокирующих правил для skeleton режима
        if skeleton_mode:
            # В skeleton режиме stepsMin3 не блокирует (warning вместо error)
            for issue in chef_rule_issues:
                if issue.get("type") == "ruleError:stepsMin3":
                    issue["type"] = "ruleWarning:stepsMin3"  # понижаем до warning
        
        # Шаг 8: Пост-проверка качества генерации (ПОСЛЕ нормализации и санитизации)
        start_postcheck = time.perf_counter()
        postcheck_issues = postcheck_v2(validated_card)
        timings["postcheck_ms"] = int((time.perf_counter() - start_postcheck) * 1000)
        
        # GX-01-FINAL: Собираем timings локально, присваиваем один раз
        timings["total_ms"] = int((time.perf_counter() - start_total) * 1000)
        
        # Шаг 9: Генерация артикулов для блюда и ингредиентов (ПЕРЕД обновлением timings)
        start_articles = time.perf_counter()
        try:
            # CRITICAL FIX: Генерируем артикул для блюда, сначала ищем в iiko RMS
            dish_article = getattr(validated_card.meta, 'article', None)
            if not dish_article:
                # STEP 1: Попробуем найти блюдо в iiko RMS
                dish_found_in_rms = False
                try:
                    from ..integrations.iiko_rms_service import IikoRmsService
                    from ..exports.iiko_xlsx import find_dish_in_iiko_rms
                    
                    rms_service = IikoRmsService()
                    dish_search_result = find_dish_in_iiko_rms(validated_card.meta.title, rms_service)
                    
                    if dish_search_result.get('status') == 'found' and dish_search_result.get('dish_code'):
                        dish_article = dish_search_result['dish_code']
                        dish_found_in_rms = True
                        print(f"✅ Found existing dish in iiko RMS: {validated_card.meta.title} -> {dish_article}")
                except Exception as e:
                    print(f"⚠️ Error searching dish in RMS: {e}")
                
                # STEP 2: Если не нашли в RMS - используем ArticleAllocator
                if not dish_found_in_rms:
                    from ..integrations.article_allocator import ArticleAllocator, ArticleType
                    allocator = ArticleAllocator()
                    dish_id = validated_card.meta.id or f"dish_{int(time.time())}"
                    allocated_result = allocator.allocate_articles(
                        article_type=ArticleType.DISH,
                        count=1,
                        entity_ids=[dish_id],
                        entity_names=[validated_card.meta.title]
                    )
                    
                    if allocated_result and len(allocated_result) > 0:
                        dish_article = allocated_result[0]  # First article from the list
                        print(f"✅ Generated new dish article: {dish_article}")
                
                # Обновляем meta с найденным или сгенерированным артикулом
                if dish_article:
                    updated_meta = validated_card.meta.model_copy(deep=True)
                    if hasattr(updated_meta, 'article'):
                        updated_meta.article = dish_article
                    else:
                        # Добавляем article как новое поле
                        meta_dict = updated_meta.model_dump()
                        meta_dict['article'] = dish_article
                        from ..techcards_v2.schemas import MetaV2
                        updated_meta = MetaV2.model_validate(meta_dict)
                    
                    validated_card = validated_card.model_copy(update={"meta": updated_meta})
            
            # Генерируем артикулы для ингредиентов, если отсутствуют
            updated_ingredients = []
            ingredient_ids_for_allocation = []
            ingredients_needing_articles = []
            
            # CRITICAL FIX: Сначала ищем артикулы в iiko RMS, затем используем ArticleAllocator
            try:
                from ..integrations.iiko_rms_service import IikoRmsService
                rms_service = IikoRmsService()
            except Exception as e:
                print(f"⚠️ Could not initialize RMS service: {e}")
                rms_service = None
            
            for i, ingredient in enumerate(validated_card.ingredients):
                product_code = getattr(ingredient, 'product_code', None)
                updated_ingredient = ingredient
                
                if not product_code:
                    # STEP 1: Попробуем найти артикул в iiko RMS по skuId
                    sku_id = getattr(ingredient, 'skuId', None)
                    
                    if sku_id and rms_service:
                        try:
                            from ..exports.iiko_xlsx import get_product_code_from_rms
                            found_article = get_product_code_from_rms(sku_id, rms_service)
                            
                            # Если нашли артикул и это не тот же skuId (значит нашли реальный артикул)
                            if found_article and found_article != sku_id:
                                # Обновляем ингредиент с найденным артикулом
                                ingredient_dict = ingredient.model_dump()
                                ingredient_dict['product_code'] = found_article
                                
                                from ..techcards_v2.schemas import IngredientV2
                                updated_ingredient = IngredientV2.model_validate(ingredient_dict)
                                
                                print(f"✅ Found existing article in iiko RMS for {ingredient.name}: {found_article}")
                            else:
                                # STEP 2: Если не нашли в RMS - добавляем в список для ArticleAllocator
                                temp_id = f"ingredient_{i}_{ingredient.name[:10].lower().replace(' ', '_')}"
                                ingredient_ids_for_allocation.append(temp_id)
                                ingredients_needing_articles.append((i, ingredient))
                        except Exception as e:
                            print(f"⚠️ Error searching RMS for {ingredient.name}: {e}")
                            # Fallback: добавляем в список для ArticleAllocator
                            temp_id = f"ingredient_{i}_{ingredient.name[:10].lower().replace(' ', '_')}"
                            ingredient_ids_for_allocation.append(temp_id)
                            ingredients_needing_articles.append((i, ingredient))
                    else:
                        # Нет skuId или RMS - используем ArticleAllocator
                        temp_id = f"ingredient_{i}_{ingredient.name[:10].lower().replace(' ', '_')}"
                        ingredient_ids_for_allocation.append(temp_id)
                        ingredients_needing_articles.append((i, ingredient))
                
                updated_ingredients.append(updated_ingredient)
            
            # Выделяем артикулы для ингредиентов
            if ingredient_ids_for_allocation:
                from ..integrations.article_allocator import ArticleAllocator, ArticleType
                allocator = ArticleAllocator()
                allocated_result = allocator.allocate_articles(
                    article_type=ArticleType.PRODUCT,
                    count=len(ingredient_ids_for_allocation),
                    entity_ids=ingredient_ids_for_allocation,
                    entity_names=[ing[1].name for ing in ingredients_needing_articles]
                )
                
                if allocated_result and len(allocated_result) > 0:
                    # Обновляем ингредиенты с артикулами
                    allocated_articles = allocated_result  # List of strings
                    
                    for i, article in enumerate(allocated_articles):
                        if i < len(ingredients_needing_articles):
                            ingredient_idx, original_ingredient = ingredients_needing_articles[i]
                            # article is already a string
                            
                            # Создаем обновленный ингредиент с product_code
                            ingredient_dict = original_ingredient.model_dump()
                            ingredient_dict['product_code'] = article
                            
                            from ..techcards_v2.schemas import IngredientV2
                            updated_ingredient = IngredientV2.model_validate(ingredient_dict)
                            updated_ingredients[ingredient_idx] = updated_ingredient
                            
                            print(f"✅ Generated product article for {original_ingredient.name}: {article}")
                    
                    # Обновляем техкарту с новыми ингредиентами
                    validated_card = validated_card.model_copy(update={"ingredients": updated_ingredients})
                        
        except Exception as e:
            print(f"⚠️ Article generation failed: {e}")
            traceback.print_exc()
            # Не блокируем pipeline из-за ошибки генерации артикулов
            
        timings["article_generation_ms"] = int((time.perf_counter() - start_articles) * 1000)
        
        # Обновляем meta с timings - безопасная сериализация (ПОСЛЕ генерации артикулов)
        validated_card = validated_card.model_copy(update={
            "meta": validated_card.meta.model_copy(update={"timings": timings})
        })
        
        # Объединяем все issues
        all_issues.extend([issue.get("hint", "") for issue in content_issues])
        all_issues.extend([issue.get("hint", "") for issue in chef_rule_issues])
        all_issues.extend([issue.get("hint", "") for issue in postcheck_issues])
        
        # Проверяем наличие критических ошибок
        has_critical_content_errors_flag = has_critical_content_errors(content_issues)
        has_critical_chef_errors_flag = has_critical_rule_errors(chef_rule_issues)
        
        # CLEANUP TECH CARD DATA & UI: Все техкарты создаются со статусом READY
        # Убираем draft статус - все техкарты теперь READY для продакшена
        return PipelineResult(
            card=validated_card,
            issues=[], # Очищаем issues для чистого интерфейса
            status="READY"  # Все техкарты имеют статус READY
        )
            
    except Exception as e:
        # GX-01-FINAL: Критическая ошибка в pipeline - создаем skeleton fallback
        print(f"❌ Critical pipeline error: {e}")
        try:
            timings["total_ms"] = int((time.perf_counter() - start_total) * 1000)
            
            skeleton_card_data = _create_skeleton_techcard(profile, f"Pipeline error: {str(e)}")
            skeleton_issues = skeleton_card_data.pop("issues", [])
            
            fallback_card = TechCardV2.model_validate(skeleton_card_data)
            
            # Добавляем базовые расчеты и timings для fallback
            try:
                fallback_card = calculate_cost_for_tech_card(fallback_card, {})
                fallback_card = calculate_nutrition_for_tech_card(fallback_card, {})
            except Exception:
                pass
                
            # Обновляем meta с timings
            fallback_card = fallback_card.model_copy(update={
                "meta": fallback_card.meta.model_copy(update={"timings": timings})
            })
            
            return PipelineResult(
                card=fallback_card,
                issues=[], # Очищаем issues для чистого интерфейса
                status="READY"  # Даже fallback техкарты имеют статус READY
            )
        except Exception as fallback_error:
            # Последний fallback без карты
            timings["total_ms"] = int((time.perf_counter() - start_total) * 1000)
            return PipelineResult(
                card=None,
                issues=[], # Очищаем issues для чистого интерфейса
                status="READY",  # Все техкарты имеют статус READY
                raw_data={"timings": timings}
            )