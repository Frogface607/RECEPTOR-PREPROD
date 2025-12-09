"""
Санитайзер для TechCardV2 - приведение nutrition и cost к строгому формату
Решает проблемы с null-значениями, строками вместо чисел, неправильными типами
"""
import re
from typing import Dict, Any, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from receptor_agent.techcards_v2.schemas import TechCardV2


def sanitize_card_v2(card: 'TechCardV2') -> 'TechCardV2':
    """
    GX-01-FINAL: Чистая функция - принудительная нормализация карточки TechCardV2
    Принимает TechCardV2, возвращает новый объект TechCardV2 без in-place модификаций
    
    Args:
        card: Экземпляр TechCardV2
        
    Returns:
        TechCardV2: Санитизированная техкарта с правильными типами
    """
    from receptor_agent.techcards_v2.schemas import TechCardV2
    
    # GX-01-FINAL: Используем by_alias=False чтобы получить внутренние имена полей (yield_ вместо yield)
    card_dict = card.model_dump(by_alias=False)
    
    # 1. Нормализация nutrition
    card_dict["nutrition"] = sanitize_nutrition(card_dict.get("nutrition"))
    
    # 2. Нормализация cost  
    card_dict["cost"] = sanitize_cost(card_dict.get("cost"))
    
    # 3. Нормализация meta полей
    if "nutritionMeta" in card_dict:
        card_dict["nutritionMeta"] = sanitize_meta(card_dict["nutritionMeta"])
    
    if "costMeta" in card_dict:
        card_dict["costMeta"] = sanitize_meta(card_dict["costMeta"])
    
    # 4. Удаление лишних полей - используем внутренние имена полей
    card_dict = remove_unknown_fields_internal(card_dict)
    
    # 5. GX-01-FINAL: Создаем новый объект TechCardV2
    return TechCardV2.model_validate(card_dict)


def sanitize_nutrition(nutrition: Any) -> Dict[str, Any]:
    """Санитизация поля nutrition"""
    if nutrition is None or not isinstance(nutrition, dict):
        nutrition = {}
    
    # Гарантируем наличие per100g и perPortion
    per100g = nutrition.get("per100g", {})
    per_portion = nutrition.get("perPortion", {})
    
    if not isinstance(per100g, dict):
        per100g = {}
    if not isinstance(per_portion, dict):
        per_portion = {}
    
    # Санитизируем per100g
    sanitized_per100g = {
        "kcal": safe_float(per100g.get("kcal", 0), precision=1),
        "proteins_g": safe_float(per100g.get("proteins_g", 0), precision=1),
        "fats_g": safe_float(per100g.get("fats_g", 0), precision=1),
        "carbs_g": safe_float(per100g.get("carbs_g", 0), precision=1)
    }
    
    # Санитизируем perPortion
    sanitized_per_portion = {
        "kcal": safe_float(per_portion.get("kcal", 0), precision=1),
        "proteins_g": safe_float(per_portion.get("proteins_g", 0), precision=1),
        "fats_g": safe_float(per_portion.get("fats_g", 0), precision=1),
        "carbs_g": safe_float(per_portion.get("carbs_g", 0), precision=1)
    }
    
    return {
        "per100g": sanitized_per100g,
        "perPortion": sanitized_per_portion
    }


def sanitize_cost(cost: Any) -> Dict[str, Any]:
    """Санитизация поля cost"""
    if cost is None or not isinstance(cost, dict):
        cost = {}
    
    return {
        "rawCost": safe_float(cost.get("rawCost", 0), precision=2, min_value=0),
        "costPerPortion": safe_float(cost.get("costPerPortion", 0), precision=2, min_value=0),
        "markup_pct": safe_float(cost.get("markup_pct", 300), precision=1, min_value=0),
        "vat_pct": safe_float(cost.get("vat_pct", 20), precision=1, min_value=0),
        "currency": str(cost.get("currency", "RUB"))
    }


def sanitize_meta(meta: Any) -> Dict[str, Any]:
    """Санитизация мета-полей (nutritionMeta, costMeta)"""
    if meta is None or not isinstance(meta, dict):
        return {}
    
    sanitized_meta = {}
    
    # source - строка
    if "source" in meta:
        sanitized_meta["source"] = str(meta["source"])
    
    # coveragePct - число от 0 до 100
    if "coveragePct" in meta:
        coverage = safe_float(meta["coveragePct"], precision=1, min_value=0, max_value=100)
        sanitized_meta["coveragePct"] = coverage
    
    # asOf - строка (дата)
    if "asOf" in meta:
        sanitized_meta["asOf"] = str(meta["asOf"])
    
    return sanitized_meta


def safe_float(value: Any, precision: int = 2, min_value: float = None, max_value: float = None) -> float:
    """
    Безопасное преобразование в float с округлением
    
    Args:
        value: Значение для преобразования
        precision: Количество знаков после запятой
        min_value: Минимальное значение
        max_value: Максимальное значение
        
    Returns:
        float: Нормализованное число
    """
    # Если уже число
    if isinstance(value, (int, float)):
        result = float(value)
    else:
        # Попытка парсинга строки
        if value is None or value == "":
            result = 0.0
        else:
            try:
                # Обработка строк с запятыми (европейский формат)
                str_value = str(value).replace(",", ".")
                # Удаление лишних символов (кроме цифр, точки и знака минус)
                cleaned_value = re.sub(r'[^\d\.\-]', '', str_value)
                if not cleaned_value:
                    result = 0.0
                else:
                    result = float(cleaned_value)
            except (ValueError, TypeError):
                result = 0.0
    
    # Применяем ограничения
    if min_value is not None:
        result = max(result, min_value)
    if max_value is not None:
        result = min(result, max_value)
    
    # Округляем до нужной точности
    return round(result, precision)


def remove_unknown_fields(card_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Удаляет неизвестные поля, оставляя только те, что есть в схеме TechCardV2
    """
    # Известные поля верхнего уровня TechCardV2
    known_fields = {
        "meta", "portions", "yield", "ingredients", "process", "storage", 
        "allergens", "notes", "nutrition", "cost", "nutritionMeta", "costMeta", "issues"
    }
    
    # Фильтруем только известные поля
    filtered = {}
    for key, value in card_dict.items():
        if key in known_fields:
            filtered[key] = value
        # Можно добавить логгирование удаленных полей для отладки
        # else:
        #     print(f"Removing unknown field: {key}")
    
    return filtered


def remove_unknown_fields_internal(card_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Удаляет неизвестные поля, используя внутренние имена полей (yield_ вместо yield)
    """
    # Известные поля верхнего уровня TechCardV2 с внутренними именами
    known_fields = {
        "meta", "portions", "yield_", "ingredients", "process", "storage", 
        "allergens", "notes", "nutrition", "cost", "nutritionMeta", "costMeta", "issues"
    }
    
    # Фильтруем только известные поля
    filtered = {}
    for key, value in card_dict.items():
        if key in known_fields:
            filtered[key] = value
    
    return filtered


def validate_sanitized_card(card_dict: Dict[str, Any]) -> bool:
    """
    Проверка что карточка корректно санитизирована
    
    Returns:
        bool: True если все обязательные поля присутствуют и правильного типа
    """
    try:
        # Проверяем nutrition
        nutrition = card_dict.get("nutrition", {})
        if not isinstance(nutrition, dict):
            return False
        
        per100g = nutrition.get("per100g", {})
        per_portion = nutrition.get("perPortion", {})
        
        if not isinstance(per100g, dict) or not isinstance(per_portion, dict):
            return False
        
        # Проверяем обязательные БЖУ поля
        required_nutrition_fields = ["kcal", "proteins_g", "fats_g", "carbs_g"]
        for field in required_nutrition_fields:
            if field not in per100g or not isinstance(per100g[field], (int, float)):
                return False
            if field not in per_portion or not isinstance(per_portion[field], (int, float)):
                return False
        
        # Проверяем cost
        cost = card_dict.get("cost", {})
        if not isinstance(cost, dict):
            return False
        
        required_cost_fields = ["rawCost", "costPerPortion", "markup_pct", "vat_pct", "currency"]
        for field in required_cost_fields:
            if field not in cost:
                return False
            if field == "currency":
                if not isinstance(cost[field], str):
                    return False
            else:
                if not isinstance(cost[field], (int, float)):
                    return False
        
        return True
        
    except Exception:
        return False