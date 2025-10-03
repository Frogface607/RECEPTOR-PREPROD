"""
Cost Calculator для TechCardV2 с использованием PriceProvider
Модуль для расчета себестоимости блюд на основе единого провайдера цен
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import Counter

from .schemas import TechCardV2, IngredientV2, CostV2, CostMetaV2
from .price_provider import PriceProvider

def calculate_cost_for_tech_card(tech_card: TechCardV2, sub_recipes_cache: Dict[str, TechCardV2] = None) -> TechCardV2:
    """
    Функция-обертка для расчета стоимости техкарты с использованием PriceProvider
    GX-01-FINAL: Возвращает обновленную техкарту с заполненными полями cost и costMeta
    """
    calculator = CostCalculator()
    cost, cost_meta, cost_issues = calculator.calculate_tech_card_cost(tech_card, sub_recipes_cache)
    
    # GX-01-FINAL: Создаем новую техкарту с обновленной стоимостью (чистая функция)
    updated_tech_card = tech_card.model_copy(update={
        "cost": cost,
        "costMeta": cost_meta
    })
    
    # Issues обрабатываются в pipeline, не здесь
    return updated_tech_card

class CostCalculator:
    """Калькулятор себестоимости для техкарт с использованием PriceProvider"""
    
    def __init__(self):
        """Инициализация с PriceProvider"""
        self.price_provider = PriceProvider()
    
    def calculate_tech_card_cost(self, tech_card: TechCardV2, sub_recipes_cache: Dict[str, TechCardV2] = None) -> Tuple[CostV2, CostMetaV2, List[Dict]]:
        """
        Расчет полной стоимости техкарты с использованием PriceProvider
        Возвращает: (cost, cost_meta, issues)
        """
        total_cost = 0.0
        ingredient_costs = []
        found_ingredients = 0
        issues = []
        sources_used = []  # Для отслеживания использованных источников
        as_of_dates = []   # Для определения минимальной даты
        
        # Рассчитываем стоимость каждого ингредиента
        for ingredient in tech_card.ingredients:
            cost, price_data, status = self._calculate_ingredient_cost(ingredient, sub_recipes_cache or {})
            
            if price_data and status == "found":
                found_ingredients += 1
                sources_used.append(price_data["source"])
                if price_data.get("asOf"):
                    as_of_dates.append(price_data["asOf"])
                    
                    # Проверяем на stale price (>30 дней)
                    if self.price_provider.is_stale_price(price_data["asOf"]):
                        issues.append({
                            "type": "stalePrice",
                            "name": ingredient.name,
                            "asOf": price_data["asOf"],
                            "hint": "price data older than 30 days"
                        })
            elif status == "subrecipe_issue":
                # Issues для проблем с подрецептами
                issues.append({
                    "type": "subRecipeNotReady",
                    "name": ingredient.name,
                    "hint": "sub-recipe missing cost or yield data"
                })
            else:
                # Issue для отсутствующей цены
                issues.append({
                    "type": "noPrice",
                    "name": ingredient.name,
                    "hint": "upload price list / map SKU"
                })
            
            total_cost += cost
            ingredient_costs.append({
                "name": ingredient.name,
                "cost": cost,
                "status": status,
                "source": price_data.get("source") if price_data else None
            })
        
        # Рассчитываем метаданные
        coverage_pct = (found_ingredients / len(tech_card.ingredients)) * 100 if tech_card.ingredients else 0
        
        # Определяем источник
        source_counts = Counter(sources_used)
        if not sources_used:
            source = "none"
        elif len(source_counts) == 1:
            # Один источник
            source = list(source_counts.keys())[0]
        else:
            # Смешанные источники
            source = "mixed"
        
        # Минимальная дата среди использованных
        min_as_of = min(as_of_dates) if as_of_dates else datetime.now().strftime("%Y-%m-%d")
        
        # Создаем метаданные
        cost_meta = CostMetaV2(
            source=source,
            coveragePct=round(coverage_pct, 1),
            asOf=min_as_of
        )
        
        # Если покрытие 0%, возвращаем пустую стоимость
        if coverage_pct == 0:
            return CostV2(), cost_meta, issues
        
        # Рассчитываем стоимость на порцию
        cost_per_portion = total_cost / tech_card.portions if tech_card.portions > 0 and total_cost > 0 else 0
        
        # Логирование для отладки
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"💰 Cost calculation: total_cost={total_cost}₽, portions={tech_card.portions}, cost_per_portion={cost_per_portion}₽")
        logger.info(f"📊 Coverage: {coverage_pct}%, found_ingredients={found_ingredients}/{len(tech_card.ingredients)}")
        
        # Проверка на реалистичность
        if cost_per_portion > 0 and cost_per_portion < 10:
            logger.warning(f"⚠️ Suspicious cost_per_portion={cost_per_portion}₽ - too low!")
            logger.warning(f"   Ingredients: {[ing.name for ing in tech_card.ingredients[:5]]}")
            logger.warning(f"   Ingredient costs: {ingredient_costs[:5]}")
        
        # Создаем объект стоимости
        cost = CostV2(
            rawCost=round(total_cost, 2) if total_cost > 0 else None,
            costPerPortion=round(cost_per_portion, 2) if cost_per_portion > 0 else None,
            markup_pct=300,  # Default markup
            vat_pct=20       # Default VAT
        )
        
        return cost, cost_meta, issues

    def _calculate_ingredient_cost(self, ingredient: IngredientV2, sub_recipes_cache: Dict[str, TechCardV2]) -> Tuple[float, Optional[Dict], str]:
        """
        Расчет стоимости одного ингредиента
        Возвращает: (стоимость, price_data, статус)
        """
        # Если это подрецепт
        if ingredient.subRecipe:
            return self._calculate_subrecipe_cost(ingredient, sub_recipes_cache)
        
        # Ищем цену через PriceProvider
        price_data = self.price_provider.resolve(ingredient)
        
        if price_data:
            # Рассчитываем стоимость: netto_g * price_per_g
            cost = ingredient.netto_g * price_data["price_per_g"]
            return cost, price_data, "found"
        else:
            return 0.0, None, "not_found"

    def _calculate_subrecipe_cost(self, ingredient: IngredientV2, sub_recipes_cache: Dict[str, TechCardV2]) -> Tuple[float, Optional[Dict], str]:
        """
        Расчет стоимости подрецепта
        Возвращает: (стоимость, price_data, статус)
        """
        if not ingredient.subRecipe:
            return 0.0, None, "no_subrecipe"
            
        subrecipe_id = ingredient.subRecipe.id
        
        # Ищем подрецепт в кеше
        if subrecipe_id not in sub_recipes_cache:
            return 0.0, None, "subrecipe_issue"
        
        sub_tech_card = sub_recipes_cache[subrecipe_id]
        
        # Проверяем наличие cost и yield данных в подрецепте
        if not sub_tech_card.cost or not sub_tech_card.cost.rawCost or not sub_tech_card.yield_ or not sub_tech_card.yield_.perBatch_g:
            return 0.0, None, "subrecipe_issue"
        
        # Рассчитываем стоимость за грамм готового подрецепта
        cost_per_g = sub_tech_card.cost.rawCost / sub_tech_card.yield_.perBatch_g
        
        # Стоимость за требуемое количество (netto_g граммов готового подрецепта)
        total_cost = ingredient.netto_g * cost_per_g
        
        # Создаем price_data для подрецепта
        price_data = {
            "price_per_g": cost_per_g,
            "source": "subrecipe",
            "asOf": sub_tech_card.costMeta.asOf if sub_tech_card.costMeta else datetime.now().strftime("%Y-%m-%d"),
            "skuId": f"SUB_{subrecipe_id}"
        }
        
        return total_cost, price_data, "found"