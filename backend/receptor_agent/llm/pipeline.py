from __future__ import annotations
import os, json
from typing import Dict, Any, List, Set
from pydantic import BaseModel
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.techcards_v2.validators import validate_card
from receptor_agent.techcards_v2.strict_validator import validate_techcard_v2, create_draft_response
from receptor_agent.techcards_v2.normalize import normalize_card
from receptor_agent.techcards_v2.quantify import rebalance
from receptor_agent.techcards_v2.haccp_templates import enrich_haccp
from receptor_agent.techcards_v2.cost_calculator import calculate_cost_for_tech_card
from receptor_agent.techcards_v2.nutrition_calculator import calculate_nutrition_for_tech_card
from receptor_agent.techcards_v2.postcheck_v2 import postcheck_v2
from receptor_agent.techcards_v2.chef_rules import run_chef_rules, has_critical_rule_errors

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

class PipelineResult(BaseModel):
    card: TechCardV2 | None = None
    issues: List[str] = []
    status: str = "success"  # "success", "draft", "failed"
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
    """Форматирует шаблон промпта с подстановкой переменных"""
    result = template
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))
    return result

def generate_draft_v2(profile: ProfileInput) -> Dict[str, Any]:
    """Генерация чернового JSON с помощью нового промпта v2"""
    if not _use_llm():
        return _get_fallback_draft(profile)
        
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
        
        user_prompt = _format_template(
            user_template,
            brief=brief,
            portions=portions,
            yield_per_portion_g=yield_per_portion
        )
        
        # Вызываем LLM с настройками для качественной генерации  
        return call_structured(
            system=_system_ru() + "\n\n" + system_prompt,
            user=user_prompt,
            json_schema=TECHCARD_CORE_SCHEMA,
            temperature=0.2,
            top_p=0.9,
            presence_penalty=0,
            frequency_penalty=0
        )
        
    except Exception as e:
        print(f"Error in generate_draft_v2: {e}")
        return _get_fallback_draft(profile)

def normalize_to_v2(draft_json: Dict[str, Any]) -> Dict[str, Any]:
    """Нормализация черновика до финального TechCardV2"""
    if not _use_llm():
        return draft_json
        
    try:
        # Загружаем промпты нормализации
        system_prompt = _load_prompt_v2("normalize_to_v2.ru.txt")
        user_template = _load_prompt_v2("normalize_to_v2_user.ru.txt") 
        
        user_prompt = _format_template(
            user_template,
            draft_json=json.dumps(draft_json, ensure_ascii=False, indent=2)
        )
        
        # Определяем модель: gpt-4o для сложных случаев
        use_4o = os.environ.get('USE_4O_FOR_NORMALIZE', 'false').lower() == 'true'
        model = "gpt-4o" if use_4o else "gpt-4o-mini"
        
        return call_structured(
            system=_system_ru() + "\n\n" + system_prompt,
            user=user_prompt, 
            json_schema=TECHCARD_CORE_SCHEMA,
            model=model,
            temperature=0.2,
            top_p=0.9,
            presence_penalty=0,
            frequency_penalty=0
        )
        
    except Exception as e:
        print(f"Error in normalize_to_v2: {e}")
        return draft_json

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
        "nutrition": {"per100g": None, "perPortion": None},
        "cost": {"rawCost": None, "costPerPortion": None},
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
        "nutrition": {"per100g": None, "perPortion": None},
        "cost": {"rawCost": None, "costPerPortion": None},
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

def run_pipeline(profile: ProfileInput) -> PipelineResult:
    """Генерация техкарты с строгой валидацией TechCardV2 и новой цепочкой промптов v2"""
    try:
        # Шаг 1: Генерируем черновик с новым промптом v2
        draft_data = generate_draft_v2(profile)
        
        # Шаг 2: Нормализуем черновик до финального TechCardV2
        normalized_data = normalize_to_v2(draft_data)
        
        # Собираем ID подрецептов из нормализованных данных
        sub_recipe_ids = collect_sub_recipe_ids(normalized_data)
        
        # Получаем подрецепты из кеша (пока заглушка)
        sub_recipes_cache = {}  # Временная заглушка
        
        # Шаг 3: СТРОГАЯ ВАЛИДАЦИЯ TechCardV2
        is_valid, validation_issues, validated_card = validate_techcard_v2(normalized_data)
        
        if is_valid and validated_card:
            # Шаг 4: Правила шефа (rule-based sanity checks)
            chef_rule_issues = run_chef_rules(validated_card)
            
            # Шаг 5: Пост-проверка качества генерации
            postcheck_issues = postcheck_v2(validated_card)
            
            # Объединяем все issues
            all_issues = validation_issues + chef_rule_issues + [issue.get("hint", "") for issue in postcheck_issues]
            
            # Проверяем наличие критических ошибок правил шефа
            has_critical_chef_errors = has_critical_rule_errors(chef_rule_issues)
            
            # Если есть критические ошибки постпроверки, пытаемся ещё раз нормализовать
            has_critical_postcheck_errors = any(
                issue.get("type", "").startswith("postcheck:") and 
                issue.get("type", "") in [
                    "postcheck:yieldConsistency", 
                    "postcheck:lossBounds", 
                    "postcheck:units"
                ]
                for issue in postcheck_issues
            )
            
            if has_critical_postcheck_errors and _use_llm():
                try:
                    # Дополнительный прогон нормализатора с описанием проблем
                    issues_description = "; ".join([issue.get("hint", "") for issue in postcheck_issues])
                    system_prompt = _load_prompt_v2("normalize_to_v2.ru.txt") + f"\n\nИСПРАВЬ ОШИБКИ: {issues_description}"
                    user_template = _load_prompt_v2("normalize_to_v2_user.ru.txt")
                    
                    user_prompt = _format_template(
                        user_template,
                        draft_json=json.dumps(normalized_data, ensure_ascii=False, indent=2)
                    )
                    
                    fixed_data = call_structured(
                        system=_system_ru() + "\n\n" + system_prompt,
                        user=user_prompt,
                        json_schema=TECHCARD_CORE_SCHEMA,
                        temperature=0.1,  # Более строгий режим
                        top_p=0.8
                    )
                    
                    # Повторная валидация исправленных данных
                    is_valid_fixed, _, validated_card_fixed = validate_techcard_v2(fixed_data)
                    if is_valid_fixed and validated_card_fixed:
                        validated_card = validated_card_fixed
                        # Обновляем постпроверку
                        postcheck_issues = postcheck_v2(validated_card)
                        
                except Exception:
                    pass  # Игнорируем ошибки дополнительной нормализации
            
            # Рассчитываем стоимость для валидной карты с подрецептами
            try:
                validated_card = calculate_cost_for_tech_card(validated_card, sub_recipes_cache)
            except Exception as e:
                validation_issues.append(f"Cost calculation error: {str(e)}")
            
            # Рассчитываем питательность для валидной карты с подрецептами
            try:
                validated_card = calculate_nutrition_for_tech_card(validated_card, sub_recipes_cache)
            except Exception as e:
                validation_issues.append(f"Nutrition calculation error: {str(e)}")
            
            # Определяем статус на основе постпроверки
            if postcheck_issues:
                all_issues = validation_issues + [issue.get("hint", "") for issue in postcheck_issues]
                return PipelineResult(
                    card=validated_card,
                    issues=all_issues,
                    status="draft"  # Есть проблемы постпроверки
                )
            else:
                # Успешная генерация без проблем
                return PipelineResult(
                    card=validated_card,
                    issues=[],
                    status="success"
                )
        else:
            # Ошибки валидации - попытаемся все же создать карту для draft режима
            draft_card = None
            try:
                # Попытаемся создать TechCardV2 из normalized данных, даже если есть validation issues
                draft_card = TechCardV2.model_validate(normalized_data)
                
                # Попытаемся добавить базовые расчеты для draft карты с подрецептами
                try:
                    draft_card = calculate_cost_for_tech_card(draft_card, sub_recipes_cache)
                except Exception:
                    pass  # Игнорируем ошибки расчета стоимости для draft
                
                try:
                    draft_card = calculate_nutrition_for_tech_card(draft_card, sub_recipes_cache)
                except Exception:
                    pass  # Игнорируем ошибки расчета питания для draft
                    
            except Exception as validation_error:
                validation_issues.append(f"Failed to create draft card: {str(validation_error)}")
            
            return PipelineResult(
                card=draft_card,  # Теперь возвращаем карту даже для draft
                issues=validation_issues,
                status="draft",
                raw_data=normalized_data
            )
            
    except Exception as e:
        # Критическая ошибка в pipeline
        return PipelineResult(
            card=None,
            issues=[f"Pipeline error: {str(e)}"],
            status="failed",
            raw_data=None
        )