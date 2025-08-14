"""
Анкерная валидность (Content Check) для TechCardV2
Проверяет соответствие техкарты брифу через обязательные/запрещенные ингредиенты
"""
import os
import json
from typing import List, Dict, Any, Set
from receptor_agent.techcards_v2.schemas import TechCardV2


def load_anchors_mapping() -> Dict[str, Any]:
    """Загружает словарь мэппинга якорей RU → EN canonical_id"""
    try:
        anchors_path = os.path.join(os.path.dirname(__file__), "../../data/anchors_map.json")
        with open(anchors_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"mappings": {}}


def normalize_ingredient_name(ingredient_name: str) -> str:
    """Нормализует название ингредиента для поиска"""
    return ingredient_name.lower().strip()


def find_ingredient_canonicals(ingredient_name: str, mapping: Dict[str, Any]) -> List[str]:
    """Находит канонические ID для ингредиента"""
    normalized_name = normalize_ingredient_name(ingredient_name)
    canonicals = []
    
    # Проверяем синонимы
    synonyms = mapping.get("mappings", {}).get("синонимы", {})
    if normalized_name in synonyms:
        canonicals.extend(synonyms[normalized_name])
    
    # Проверяем по категориям
    for category, items in mapping.get("mappings", {}).items():
        if category == "синонимы":
            continue
        if isinstance(items, dict):
            for ru_name, canonical_ids in items.items():
                if normalized_name == normalize_ingredient_name(ru_name):
                    canonicals.extend(canonical_ids if isinstance(canonical_ids, list) else [canonical_ids])
                # Также проверяем частичное совпадение
                elif normalized_name in normalize_ingredient_name(ru_name) or normalize_ingredient_name(ru_name) in normalized_name:
                    canonicals.extend(canonical_ids if isinstance(canonical_ids, list) else [canonical_ids])
    
    return list(set(canonicals))  # Убираем дубликаты


def check_ingredient_presence(tech_card: TechCardV2, anchor: str, mapping: Dict[str, Any]) -> bool:
    """Проверяет наличие якоря среди ингредиентов техкарты"""
    anchor_canonicals = find_ingredient_canonicals(anchor, mapping)
    anchor_normalized = normalize_ingredient_name(anchor)
    
    for ingredient in tech_card.ingredients:
        ingredient_name = normalize_ingredient_name(ingredient.name)
        ingredient_canonicals = find_ingredient_canonicals(ingredient.name, mapping)
        
        # Прямое совпадение названий
        if anchor_normalized == ingredient_name:
            return True
        
        # Частичное совпадение названий
        if anchor_normalized in ingredient_name or ingredient_name in anchor_normalized:
            return True
        
        # Совпадение через canonical_id
        if ingredient.canonical_id:
            ingredient_canonical = normalize_ingredient_name(ingredient.canonical_id)
            if ingredient_canonical in [normalize_ingredient_name(c) for c in anchor_canonicals]:
                return True
        
        # Совпадение через найденные канонические ID
        for anchor_canonical in anchor_canonicals:
            if normalize_ingredient_name(anchor_canonical) in [normalize_ingredient_name(c) for c in ingredient_canonicals]:
                return True
        
        # Проверка подрецептов
        if ingredient.subRecipe:
            subrecipe_name = normalize_ingredient_name(ingredient.subRecipe.title)
            if anchor_normalized in subrecipe_name:
                return True
    
    return False


def run_content_check(tech_card: TechCardV2, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Запуск анкерной валидации техкарты
    
    Args:
        tech_card: Валидированная техкарта TechCardV2
        constraints: Словарь с mustHave, forbid, hints
        
    Returns:
        List[Dict]: Список issues с типами contentError/contentWarning
    """
    issues = []
    mapping = load_anchors_mapping()
    
    # 1. missingAnchor (error) - проверка обязательных якорей
    must_have = constraints.get("mustHave", [])
    missing_anchors = []
    
    for anchor in must_have:
        if not check_ingredient_presence(tech_card, anchor, mapping):
            missing_anchors.append(anchor)
    
    if missing_anchors:
        issues.append({
            "type": "contentError:missingAnchor",
            "hint": f"Отсутствуют обязательные ингредиенты: {', '.join(missing_anchors)}",
            "meta": {
                "missing_anchors": missing_anchors,
                "must_have": must_have
            }
        })
    
    # 2. forbiddenIngredient (error) - проверка запрещенных ингредиентов
    forbidden = constraints.get("forbid", [])
    found_forbidden = []
    
    for forbidden_item in forbidden:
        if check_ingredient_presence(tech_card, forbidden_item, mapping):
            found_forbidden.append(forbidden_item)
    
    if found_forbidden:
        issues.append({
            "type": "contentError:forbiddenIngredient", 
            "hint": f"Обнаружены запрещённые ингредиенты: {', '.join(found_forbidden)}",
            "meta": {
                "forbidden_found": found_forbidden,
                "forbidden_list": forbidden
            }
        })
    
    # 3. proteinMismatch (warning) - несоответствие главного белка
    protein_issues = check_protein_mismatch(tech_card, constraints, mapping)
    issues.extend(protein_issues)
    
    # 4. subRecipeNotReady (warning) - специальная обработка соусов
    subrecipe_issues = check_special_subrecipes(tech_card, constraints)
    issues.extend(subrecipe_issues)
    
    return issues


def check_protein_mismatch(tech_card: TechCardV2, constraints: Dict[str, Any], mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Проверка соответствия главного белка категории блюда"""
    issues = []
    
    # Определяем ожидаемую категорию белка из названия
    title = tech_card.meta.title.lower()
    expected_protein_category = None
    
    if any(fish in title for fish in ["треска", "лосось", "семга", "судак", "рыба"]):
        expected_protein_category = "рыба"
    elif any(meat in title for meat in ["говядина", "стейк", "бефстроганов"]):
        expected_protein_category = "говядина" 
    elif any(chicken in title for chicken in ["курица", "куриный", "цыпленок"]):
        expected_protein_category = "курица"
    elif any(pork in title for pork in ["свинина", "свиной"]):
        expected_protein_category = "свинина"
    
    if expected_protein_category:
        # Ищем основной белок в ингредиентах
        main_proteins = []
        for ingredient in tech_card.ingredients:
            ingredient_name = normalize_ingredient_name(ingredient.name)
            # Определяем категорию найденного белка
            if any(fish in ingredient_name for fish in ["треска", "лосось", "семга", "судак", "рыба"]):
                main_proteins.append("рыба")
            elif any(meat in ingredient_name for meat in ["говядина", "говяжий"]):
                main_proteins.append("говядина")
            elif any(chicken in ingredient_name for chicken in ["курица", "куриный", "курин"]):
                main_proteins.append("курица")
            elif any(pork in ingredient_name for pork in ["свинина", "свиной"]):
                main_proteins.append("свинина")
        
        # Проверяем несоответствие
        if main_proteins and expected_protein_category not in main_proteins:
            issues.append({
                "type": "contentWarning:proteinMismatch",
                "hint": f"Несоответствие белка: ожидается {expected_protein_category}, найдено {', '.join(set(main_proteins))}",
                "meta": {
                    "expected_protein": expected_protein_category,
                    "found_proteins": main_proteins
                }
            })
    
    return issues


def check_special_subrecipes(tech_card: TechCardV2, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Проверка специальных подрецептов (соусы и полуфабрикаты)"""
    issues = []
    
    must_have = constraints.get("mustHave", [])
    special_items = []
    
    # Находим специальные якоря (соусы, полуфабрикаты)
    for anchor in must_have:
        if any(sauce_word in anchor.lower() for sauce_word in ["соус", "биск", "бешамель", "песто"]):
            special_items.append(anchor)
    
    for special_item in special_items:
        # Проверяем наличие как обычного ингредиента или подрецепта
        found_as_ingredient = False
        found_as_subrecipe = False
        
        for ingredient in tech_card.ingredients:
            ingredient_name = normalize_ingredient_name(ingredient.name)
            special_normalized = normalize_ingredient_name(special_item)
            
            if special_normalized in ingredient_name:
                found_as_ingredient = True
                break
            
            if ingredient.subRecipe:
                subrecipe_name = normalize_ingredient_name(ingredient.subRecipe.title)
                if special_normalized in subrecipe_name:
                    found_as_subrecipe = True
                    break
        
        # Если не найден ни как ингредиент, ни как подрецепт
        if not found_as_ingredient and not found_as_subrecipe:
            issues.append({
                "type": "contentWarning:subRecipeNotReady",
                "hint": f"Рекомендуется подрецепт для {special_item}",
                "meta": {
                    "special_item": special_item,
                    "suggestion": f"Создайте отдельную техкарту для '{special_item}' и используйте как подрецепт"
                }
            })
    
    return issues


def has_critical_content_errors(issues: List[Dict[str, Any]]) -> bool:
    """Проверяет наличие критических ошибок контента (contentError)"""
    return any(
        issue.get("type", "").startswith("contentError:")
        for issue in issues
    )