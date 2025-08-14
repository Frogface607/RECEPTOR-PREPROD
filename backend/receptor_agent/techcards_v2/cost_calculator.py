"""
Cost Calculator для TechCardV2
Модуль для расчета себестоимости блюд на основе каталога цен
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
import re

from .schemas import TechCardV2, IngredientV2, CostV2, CostMetaV2

class CostCalculator:
    """Калькулятор себестоимости для техкарт"""
    
    def __init__(self, catalog_path: str = None, use_bootstrap: bool = True):
        """Инициализация с каталогом цен"""
        if catalog_path is None:
            catalog_path = os.path.join(os.path.dirname(__file__), "../../data/price_catalog.dev.json")
        
        self.catalog_path = catalog_path
        self.use_bootstrap = use_bootstrap
        self.catalog = self._load_catalog()
        self.ingredient_index = self._build_ingredient_index()
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Загрузка каталога цен из JSON"""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
                
            # Проверяем, есть ли данные в каталоге
            ingredients_count = sum(len(category) for category in catalog.get("ingredients", {}).values())
            
            # Если каталог пустой и включена поддержка bootstrap
            if ingredients_count < 10 and self.use_bootstrap:
                return self._load_bootstrap_catalog()
            
            return catalog
        except FileNotFoundError:
            if self.use_bootstrap:
                return self._load_bootstrap_catalog()
            return self._get_empty_catalog()
        except json.JSONDecodeError:
            if self.use_bootstrap:
                return self._load_bootstrap_catalog()
            return self._get_empty_catalog()
    
    def _load_bootstrap_catalog(self) -> Dict[str, Any]:
        """Загружает bootstrap каталог из CSV"""
        try:
            import pandas as pd
            bootstrap_path = os.path.join(os.path.dirname(__file__), "../../data/bootstrap/prices_ru.demo.csv")
            
            if not os.path.exists(bootstrap_path):
                return self._get_empty_catalog()
            
            # Читаем CSV файл
            df = pd.read_csv(bootstrap_path, encoding='utf-8')
            
            # Конвертируем в формат каталога
            catalog = {
                "catalog_version": "1.0",
                "last_updated": "2025-01-18",
                "currency": "RUB",
                "price_unit": "per_kg_or_liter",
                "source": "bootstrap_demo",
                "ingredients": {},
                "fallback_prices": {
                    "default_meat": 500,
                    "default_fish": 600, 
                    "default_dairy": 200,
                    "default_vegetable": 100,
                    "default_spice": 1000,
                    "default_grain": 100,
                    "default_oil": 200,
                    "default_other": 150
                },
                "markup_settings": {
                    "default_markup_pct": 300,
                    "default_vat_pct": 20
                }
            }
            
            # Группируем по категориям
            for _, row in df.iterrows():
                name = row['Название продукта'].lower()
                price = float(row['Цена за кг/л (руб)'])
                category = row['Категория']
                
                if category not in catalog["ingredients"]:
                    catalog["ingredients"][category] = {}
                
                # Определяем единицу измерения
                unit = "kg"
                if "масло" in name and "сливочное" not in name:
                    unit = "liter"
                elif name in ["молоко 3.2%", "сливки 20%", "сливки 35%", "кефир", "ряженка", "соевый соус", "уксус столовый 9%"]:
                    unit = "liter"
                
                catalog["ingredients"][category][name] = {
                    "price": price,
                    "unit": unit,
                    "category": category
                }
                
                # Специальная обработка для яиц
                if "яйца" in name:
                    if "куриные" in name:
                        catalog["ingredients"][category][name]["pieces_per_kg"] = 18
                    elif "перепелиные" in name:
                        catalog["ingredients"][category][name]["pieces_per_kg"] = 80
                        
            return catalog
            
        except Exception as e:
            print(f"Error loading bootstrap catalog: {e}")
            return self._get_empty_catalog()
    
    def _get_empty_catalog(self) -> Dict[str, Any]:
        """Возвращает пустой каталог с базовыми настройками"""
        return {
            "catalog_version": "1.0",
            "currency": "RUB", 
            "ingredients": {},
            "fallback_prices": {"default_other": 150},
            "markup_settings": {"default_markup_pct": 300, "default_vat_pct": 20}
        }
    
    def _build_ingredient_index(self) -> Dict[str, Tuple[str, str]]:
        """Создает индекс всех ингредиентов для быстрого поиска"""
        index = {}
        ingredients = self.catalog.get("ingredients", {})
        
        for category, items in ingredients.items():
            for ingredient_name, data in items.items():
                # Добавляем в индекс как есть
                index[ingredient_name.lower()] = (category, ingredient_name)
                
                # Добавляем без лишних слов для лучшего поиска
                clean_name = self._clean_ingredient_name(ingredient_name)
                if clean_name != ingredient_name.lower():
                    index[clean_name] = (category, ingredient_name)
        
        return index
    
    def _clean_ingredient_name(self, name: str) -> str:
        """Очистка названия ингредиента для лучшего сопоставления"""
        # Убираем лишние слова и приводим к нижнему регистру
        name = name.lower().strip()
        
        # Удаляем часто встречающиеся уточнения
        remove_words = [
            'свежий', 'свежая', 'свежее',
            'замороженный', 'замороженная', 'замороженное',
            'молотый', 'молотая', 'молотое',
            'сушеный', 'сушеная', 'сушеное',
            'филе', 'мякоть', 'без костей'
        ]
        
        for word in remove_words:
            name = name.replace(word, '').strip()
        
        # Убираем лишние пробелы
        name = re.sub(r'\s+', ' ', name)
        
        return name
    
    def find_ingredient_price(self, ingredient_name: str) -> Optional[Tuple[float, str, str]]:
        """
        Поиск цены ингредиента в каталоге
        Возвращает: (цена, единица_измерения, категория) или None
        """
        clean_name = ingredient_name.lower().strip()
        
        # Прямое совпадение
        if clean_name in self.ingredient_index:
            category, original_name = self.ingredient_index[clean_name]
            ingredient_data = self.catalog["ingredients"][category][original_name]
            return ingredient_data["price"], ingredient_data["unit"], ingredient_data["category"]
        
        # Поиск с очищенным названием
        clean_name_processed = self._clean_ingredient_name(ingredient_name)
        if clean_name_processed in self.ingredient_index:
            category, original_name = self.ingredient_index[clean_name_processed]
            ingredient_data = self.catalog["ingredients"][category][original_name]
            return ingredient_data["price"], ingredient_data["unit"], ingredient_data["category"]
        
        # Fuzzy matching для близких совпадений
        best_match = None
        best_ratio = 0.0
        
        for indexed_name, (category, original_name) in self.ingredient_index.items():
            ratio = SequenceMatcher(None, clean_name, indexed_name).ratio()
            if ratio > best_ratio and ratio >= 0.7:  # 70% совпадение
                best_ratio = ratio
                best_match = (category, original_name)
        
        if best_match:
            category, original_name = best_match
            ingredient_data = self.catalog["ingredients"][category][original_name]
            return ingredient_data["price"], ingredient_data["unit"], ingredient_data["category"]
        
        return None
    
    def _convert_to_base_unit(self, amount: float, unit: str, ingredient_unit: str, 
                            ingredient_name: str = "") -> float:
        """
        Конвертация количества в базовую единицу каталога
        amount: количество в техкарте
        unit: единица в техкарте (g, ml, pcs)
        ingredient_unit: единица в каталоге (kg, liter)
        """
        # Конвертация граммов в килограммы
        if unit == "g" and ingredient_unit == "kg":
            return amount / 1000.0
        
        # Конвертация миллилитров в литры
        if unit == "ml" and ingredient_unit == "liter":
            return amount / 1000.0
        
        # Обработка штук для яиц
        if unit == "pcs":
            if "яйц" in ingredient_name.lower():
                # Конвертируем штуки яиц в кг через pieces_per_kg
                pieces_per_kg = 18  # стандартно
                return amount / pieces_per_kg
            else:
                # Для других штучных товаров используем стандартный вес
                return amount * 0.1  # 100г за штуку как базовое значение
        
        # Если единицы уже совпадают
        if unit == ingredient_unit:
            return amount
        
        # По умолчанию возвращаем как есть
        return amount
    
    def calculate_ingredient_cost(self, ingredient: IngredientV2, use_llm_fallback: bool = True, sub_recipes_cache: Dict[str, 'TechCardV2'] = None) -> Tuple[float, str]:
        """
        Расчет стоимости одного ингредиента или подрецепта
        Возвращает: (стоимость, статус)
        """
        # Если это подрецепт - рассчитываем через него
        if ingredient.subRecipe:
            return self._calculate_subrecipe_cost(ingredient, sub_recipes_cache or {})
        
        # Обычная логика для обычных ингредиентов
        # Ищем ингредиент в каталоге
        price_data = self.find_ingredient_price(ingredient.name)
        
        if price_data:
            price_per_unit, catalog_unit, category = price_data
            
            # Конвертируем количество в единицы каталога
            converted_amount = self._convert_to_base_unit(
                ingredient.brutto_g, 
                ingredient.unit,
                catalog_unit, 
                ingredient.name
            )
            
            # Рассчитываем стоимость
            cost = converted_amount * price_per_unit
            return cost, f"found_in_catalog_{category}"
        else:
            # Используем fallback только если разрешено
            if use_llm_fallback:
                fallback_price = self._get_fallback_price(ingredient.name)
                # Для fallback используем граммы как есть
                amount_kg = ingredient.brutto_g / 1000.0 if ingredient.unit == "g" else ingredient.brutto_g
                cost = amount_kg * fallback_price
                return cost, "fallback_price_used"
            else:
                return 0.0, "no_price_found"
    
    def _calculate_subrecipe_cost(self, ingredient: IngredientV2, sub_recipes_cache: Dict[str, 'TechCardV2']) -> Tuple[float, str]:
        """
        Расчет стоимости подрецепта
        Возвращает: (стоимость_за_netto_g, статус)
        """
        subrecipe_id = ingredient.subRecipe.id
        subrecipe_title = ingredient.subRecipe.title
        
        # Ищем подрецепт в кеше
        if subrecipe_id not in sub_recipes_cache:
            return 0.0, f"subrecipe_not_found_{subrecipe_title}"
        
        sub_tech_card = sub_recipes_cache[subrecipe_id]
        
        # Проверяем наличие cost данных в подрецепте
        if not sub_tech_card.cost or not sub_tech_card.cost.rawCost:
            return 0.0, f"subrecipe_no_cost_{subrecipe_title}"
        
        # Проверяем наличие yield данных
        if not sub_tech_card.yield_ or not sub_tech_card.yield_.perBatch_g:
            return 0.0, f"subrecipe_no_yield_{subrecipe_title}"
        
        # Рассчитываем стоимость за грамм готового подрецепта
        cost_per_g = sub_tech_card.cost.rawCost / sub_tech_card.yield_.perBatch_g
        
        # Стоимость за требуемое количество (netto_g граммов готового подрецепта)
        total_cost = ingredient.netto_g * cost_per_g
        
        return total_cost, f"subrecipe_calculated_{subrecipe_title}"
    
    def _get_fallback_price(self, ingredient_name: str) -> float:
        """Получение резервной цены на основе названия ингредиента"""
        name_lower = ingredient_name.lower()
        fallback_prices = self.catalog.get("fallback_prices", {})
        
        # Пытаемся угадать категорию по ключевым словам
        meat_words = ['мясо', 'говядин', 'свинин', 'курин', 'индейк', 'утк', 'бекон', 'ветчин']
        fish_words = ['рыб', 'лосос', 'семг', 'треск', 'скумбр', 'креветк', 'кальмар']
        dairy_words = ['молоко', 'сливк', 'сметан', 'творог', 'сыр', 'масло сливочн']
        vegetable_words = ['овощ', 'картофел', 'морков', 'лук', 'помидор', 'огурц', 'капуст']
        spice_words = ['соль', 'перец', 'специ', 'пряност', 'лавров', 'базилик', 'укроп']
        grain_words = ['крупа', 'рис', 'гречк', 'овсянк', 'макарон', 'спагетт', 'мука']
        oil_words = ['масло', 'жир']
        
        if any(word in name_lower for word in meat_words):
            return fallback_prices.get("default_meat", 500)
        elif any(word in name_lower for word in fish_words):
            return fallback_prices.get("default_fish", 600)
        elif any(word in name_lower for word in dairy_words):
            return fallback_prices.get("default_dairy", 200)
        elif any(word in name_lower for word in vegetable_words):
            return fallback_prices.get("default_vegetable", 100)
        elif any(word in name_lower for word in spice_words):
            return fallback_prices.get("default_spice", 1000)
        elif any(word in name_lower for word in grain_words):
            return fallback_prices.get("default_grain", 100)
        elif any(word in name_lower for word in oil_words):
            return fallback_prices.get("default_oil", 200)
        else:
            return fallback_prices.get("default_other", 150)
    
    def calculate_tech_card_cost(self, tech_card: TechCardV2, sub_recipes_cache: Dict[str, 'TechCardV2'] = None) -> tuple[CostV2, CostMetaV2, list]:
        """
        Расчет полной стоимости техкарты
        Возвращает: (cost, cost_meta, issues)
        """
        # Проверяем флаг LLM для цен (по умолчанию false)
        use_llm_for_prices = os.getenv("PRICE_VIA_LLM", "false").lower() in ("true", "1", "yes", "on")
        
        total_cost = 0.0
        ingredient_costs = []
        found_ingredients = 0
        issues = []
        
        # Рассчитываем стоимость каждого ингредиента
        for ingredient in tech_card.ingredients:
            cost, status = self.calculate_ingredient_cost(
                ingredient, 
                use_llm_fallback=use_llm_for_prices,
                sub_recipes_cache=sub_recipes_cache or {}
            )
            
            if "found_in_catalog" in status or "subrecipe_calculated" in status:
                found_ingredients += 1
            elif "subrecipe_not_found" in status or "subrecipe_no_cost" in status or "subrecipe_no_yield" in status:
                # Issues для проблем с подрецептами
                subrecipe_title = status.split('_', 3)[-1] if '_' in status else "unknown"
                missing = []
                if "not_found" in status:
                    missing.append("recipe")
                if "no_cost" in status:
                    missing.append("cost")
                if "no_yield" in status:
                    missing.append("yield")
                    
                issues.append({
                    "type": "subRecipeNotReady",
                    "name": subrecipe_title,
                    "missing": missing
                })
            elif status in ["fallback_price_used", "no_price_found"]:
                # Добавляем issue для отсутствующих цен
                issues.append({
                    "type": "noPrice",
                    "name": ingredient.name,
                    "hint": "upload price list / map SKU"
                })
            
            total_cost += cost
            ingredient_costs.append({
                "name": ingredient.name,
                "cost": cost,
                "status": status
            })
        
        # Рассчитываем метаданные
        coverage_pct = (found_ingredients / len(tech_card.ingredients)) * 100 if tech_card.ingredients else 0
        
        # Определяем источник
        if found_ingredients > 0:
            source = "catalog"  # У нас пока только каталог, но готово для CSV
        elif coverage_pct == 0:
            source = "none"
        else:
            source = "catalog"  # Смешанный случай
        
        # Дата каталога из метаданных
        catalog_date = self.catalog.get("last_updated")
        
        # Создаем метаданные
        cost_meta = CostMetaV2(
            source=source,
            coveragePct=round(coverage_pct, 1),
            asOf=catalog_date
        )
        
        # Если покрытие 0% и LLM выключен, возвращаем пустую стоимость
        if coverage_pct == 0 and not use_llm_for_prices:
            return CostV2(), cost_meta, issues
        
        # Рассчитываем стоимость на порцию
        cost_per_portion = total_cost / tech_card.portions if tech_card.portions > 0 and total_cost > 0 else 0
        
        # Получаем настройки наценки
        markup_settings = self.catalog.get("markup_settings", {})
        default_markup = markup_settings.get("default_markup_pct", 300)
        default_vat = markup_settings.get("default_vat_pct", 20)
        
        # Создаем объект стоимости
        cost = CostV2(
            rawCost=round(total_cost, 2) if total_cost > 0 else None,
            costPerPortion=round(cost_per_portion, 2) if cost_per_portion > 0 else None,
            markup_pct=default_markup,
            vat_pct=default_vat
        )
        
        return cost, cost_meta, issues

def calculate_cost_for_tech_card(tech_card: TechCardV2, sub_recipes_cache: Dict[str, TechCardV2] = None) -> TechCardV2:
    """
    Функция-обертка для расчета стоимости техкарты
    Возвращает обновленную техкарту с заполненными полями cost и costMeta
    """
    calculator = CostCalculator()
    cost, cost_meta, cost_issues = calculator.calculate_tech_card_cost(tech_card, sub_recipes_cache)
    
    # Обновляем техкарту с рассчитанной стоимостью и метаданными
    tech_card.cost = cost
    tech_card.costMeta = cost_meta
    
    return tech_card