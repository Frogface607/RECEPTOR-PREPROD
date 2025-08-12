"""
Cost Calculator для TechCardV2
Модуль для расчета себестоимости блюд на основе каталога цен
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
import re

from .schemas import TechCardV2, IngredientV2, CostV2

class CostCalculator:
    """Калькулятор себестоимости для техкарт"""
    
    def __init__(self, catalog_path: str = None):
        """Инициализация с каталогом цен"""
        if catalog_path is None:
            catalog_path = os.path.join(os.path.dirname(__file__), "../../data/price_catalog.dev.json")
        
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
        self.ingredient_index = self._build_ingredient_index()
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Загрузка каталога цен из JSON"""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_empty_catalog()
        except json.JSONDecodeError:
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
    
    def calculate_ingredient_cost(self, ingredient: IngredientV2) -> Tuple[float, str]:
        """
        Расчет стоимости одного ингредиента
        Возвращает: (стоимость, статус)
        """
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
            # Используем fallback цену
            fallback_price = self._get_fallback_price(ingredient.name)
            # Для fallback используем граммы как есть
            amount_kg = ingredient.brutto_g / 1000.0 if ingredient.unit == "g" else ingredient.brutto_g
            cost = amount_kg * fallback_price
            return cost, "fallback_price_used"
    
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
    
    def calculate_tech_card_cost(self, tech_card: TechCardV2) -> CostV2:
        """
        Расчет полной стоимости техкарты
        """
        total_cost = 0.0
        ingredient_costs = []
        
        # Рассчитываем стоимость каждого ингредиента
        for ingredient in tech_card.ingredients:
            cost, status = self.calculate_ingredient_cost(ingredient)
            total_cost += cost
            ingredient_costs.append({
                "name": ingredient.name,
                "cost": cost,
                "status": status
            })
        
        # Рассчитываем стоимость на порцию
        cost_per_portion = total_cost / tech_card.portions if tech_card.portions > 0 else total_cost
        
        # Получаем настройки наценки
        markup_settings = self.catalog.get("markup_settings", {})
        default_markup = markup_settings.get("default_markup_pct", 300)
        default_vat = markup_settings.get("default_vat_pct", 20)
        
        # Создаем и возвращаем объект стоимости
        return CostV2(
            rawCost=round(total_cost, 2),
            costPerPortion=round(cost_per_portion, 2),
            markup_pct=default_markup,
            vat_pct=default_vat
        )

def calculate_cost_for_tech_card(tech_card: TechCardV2) -> TechCardV2:
    """
    Функция-обертка для расчета стоимости техкарты
    Возвращает обновленную техкарту с заполненными полями cost
    """
    calculator = CostCalculator()
    cost = calculator.calculate_tech_card_cost(tech_card)
    
    # Обновляем техкарту с рассчитанной стоимостью
    tech_card.cost = cost
    return tech_card