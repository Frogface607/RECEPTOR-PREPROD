"""
Nutrition Calculator для TechCardV2
Модуль для расчета БЖУ (белки, жиры, углеводы, калории) по ингредиентам
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

from .schemas import TechCardV2, IngredientV2, NutritionV2, NutritionPer, NutritionMetaV2

class NutritionCalculator:
    """Калькулятор БЖУ для техкарт"""
    
    def __init__(self, catalog_path: str = None):
        """Инициализация с каталогом питательных веществ"""
        if catalog_path is None:
            catalog_path = os.path.join(os.path.dirname(__file__), "../../data/nutrition_catalog.dev.json")
        
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
        self.nutrition_index = self._build_nutrition_index()
        self.densities = self.catalog.get("densities", {})
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Загрузка каталога питательных веществ из JSON"""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"items": [], "densities": {}}
        except json.JSONDecodeError:
            return {"items": [], "densities": {}}
    
    def _build_nutrition_index(self) -> Dict[str, Dict[str, Any]]:
        """Создает индекс всех продуктов для быстрого поиска"""
        index = {}
        items = self.catalog.get("items", [])
        
        for item in items:
            name = item.get("name", "").lower()
            if name:
                index[name] = item
                
                # Добавляем без лишних слов для лучшего поиска
                clean_name = self._clean_ingredient_name(name)
                if clean_name != name:
                    index[clean_name] = item
        
        return index
    
    def _clean_ingredient_name(self, name: str) -> str:
        """Очистка названия ингредиента для лучшего сопоставления"""
        name = name.lower().strip()
        
        # Удаляем часто встречающиеся уточнения
        remove_words = [
            'свежий', 'свежая', 'свежее',
            'замороженный', 'замороженная', 'замороженное',
            'молотый', 'молотая', 'молотое',
            'сушеный', 'сушеная', 'сушеное'
        ]
        
        for word in remove_words:
            name = name.replace(word, '').strip()
        
        # Убираем лишние пробелы
        return ' '.join(name.split())
    
    def find_nutrition_data(self, ingredient_name: str) -> Optional[Dict[str, Any]]:
        """
        Поиск данных о питательности ингредиента
        Возвращает: данные продукта или None
        """
        clean_name = ingredient_name.lower().strip()
        
        # Прямое совпадение
        if clean_name in self.nutrition_index:
            return self.nutrition_index[clean_name]
        
        # Поиск с очищенным названием
        clean_name_processed = self._clean_ingredient_name(ingredient_name)
        if clean_name_processed in self.nutrition_index:
            return self.nutrition_index[clean_name_processed]
        
        # Fuzzy matching для близких совпадений
        best_match = None
        best_ratio = 0.0
        
        for indexed_name, item_data in self.nutrition_index.items():
            ratio = SequenceMatcher(None, clean_name, indexed_name).ratio()
            if ratio > best_ratio and ratio >= 0.8:  # 80% совпадение для питания
                best_ratio = ratio
                best_match = item_data
        
        return best_match
    
    def _convert_to_grams(self, amount: float, unit: str, ingredient_name: str = "") -> Tuple[float, str]:
        """
        Конвертация количества в граммы
        Возвращает: (масса_в_граммах, статус)
        """
        if unit == "g":
            return amount, "direct_grams"
        
        elif unit == "ml":
            # Ищем плотность для конвертации ml → g
            name_lower = ingredient_name.lower()
            density = 1.0  # По умолчанию как вода
            
            # Определяем плотность по названию
            if any(word in name_lower for word in ['масло растительное', 'растительное масло', 'масло подсолнечное']):
                density = self.densities.get("veg_oil", 0.91)
            elif 'масло оливковое' in name_lower:
                density = self.densities.get("olive_oil", 0.91)
            elif 'молоко' in name_lower:
                density = self.densities.get("milk", 1.03)
            elif 'сливки' in name_lower:
                density = self.densities.get("cream", 1.02)
            elif 'соус соевый' in name_lower:
                density = self.densities.get("soy_sauce", 1.20)
            elif 'уксус' in name_lower:
                density = self.densities.get("vinegar", 1.01)
            else:
                density = self.densities.get("water", 1.0)
            
            grams = amount * density
            return grams, f"ml_to_g_density_{density}"
        
        elif unit == "pcs":
            # Для штук нужна масса одной штуки
            nutrition_data = self.find_nutrition_data(ingredient_name)
            if nutrition_data and "mass_per_piece_g" in nutrition_data:
                mass_per_piece = nutrition_data["mass_per_piece_g"]
                grams = amount * mass_per_piece
                return grams, f"pcs_to_g_mass_{mass_per_piece}g"
            else:
                return 0.0, "no_mass_for_pcs"
        
        return amount, "unknown_unit"
    
    def calculate_ingredient_nutrition(self, ingredient: IngredientV2, sub_recipes_cache: Dict[str, TechCardV2] = None) -> Tuple[Optional[Dict[str, float]], str]:
        """
        Расчет питательности одного ингредиента или подрецепта
        Возвращает: (питательность, статус)
        """
        # Если это подрецепт - рассчитываем через него
        if ingredient.subRecipe:
            return self._calculate_subrecipe_nutrition(ingredient, sub_recipes_cache or {})
        
        # Обычная логика для обычных ингредиентов
        # Ищем данные о питательности
        nutrition_data = self.find_nutrition_data(ingredient.name)
        
        if not nutrition_data or "per100g" not in nutrition_data:
            return None, "no_nutrition_data"
        
        per100g = nutrition_data["per100g"]
        
        # Конвертируем в граммы
        mass_grams, conversion_status = self._convert_to_grams(
            ingredient.netto_g, 
            ingredient.unit,
            ingredient.name
        )
        
        if "no_mass_for_pcs" in conversion_status:
            return None, "no_mass_for_pcs"
        
        # Рассчитываем питательность для данной массы
        nutrition = {
            "kcal": per100g["kcal"] * (mass_grams / 100.0),
            "proteins_g": per100g["proteins_g"] * (mass_grams / 100.0),
            "fats_g": per100g["fats_g"] * (mass_grams / 100.0),
            "carbs_g": per100g["carbs_g"] * (mass_grams / 100.0)
        }
        
        return nutrition, f"calculated_{conversion_status}"
    
    def _calculate_subrecipe_nutrition(self, ingredient: IngredientV2, sub_recipes_cache: Dict[str, TechCardV2]) -> Tuple[Optional[Dict[str, float]], str]:
        """
        Расчет питательности подрецепта
        Возвращает: (питательность_за_netto_g, статус)
        """
        subrecipe_id = ingredient.subRecipe.id
        subrecipe_title = ingredient.subRecipe.title
        
        # Ищем подрецепт в кеше
        if subrecipe_id not in sub_recipes_cache:
            return None, f"subrecipe_not_found_{subrecipe_title}"
        
        sub_tech_card = sub_recipes_cache[subrecipe_id]
        
        # Проверяем наличие nutrition данных в подрецепте
        if not sub_tech_card.nutrition or not sub_tech_card.nutrition.per100g:
            return None, f"subrecipe_no_nutrition_{subrecipe_title}"
        
        # Получаем питательность на 100г готового подрецепта
        per100g = sub_tech_card.nutrition.per100g
        
        # Рассчитываем питательность для требуемого количества (netto_g граммов готового подрецепта)
        nutrition = {
            "kcal": per100g.kcal * (ingredient.netto_g / 100.0),
            "proteins_g": per100g.proteins_g * (ingredient.netto_g / 100.0),
            "fats_g": per100g.fats_g * (ingredient.netto_g / 100.0),
            "carbs_g": per100g.carbs_g * (ingredient.netto_g / 100.0)
        }
        
        return nutrition, f"subrecipe_calculated_{subrecipe_title}"
    
    def calculate_tech_card_nutrition(self, tech_card: TechCardV2, sub_recipes_cache: Dict[str, TechCardV2] = None) -> tuple[NutritionV2, NutritionMetaV2, list]:
        """
        Расчет полной питательности техкарты
        Возвращает: (nutrition, nutrition_meta, issues)
        """
        total_nutrition = {
            "kcal": 0.0,
            "proteins_g": 0.0,
            "fats_g": 0.0,
            "carbs_g": 0.0
        }
        
        found_ingredients = 0
        issues = []
        
        # Рассчитываем питательность каждого ингредиента
        for ingredient in tech_card.ingredients:
            nutrition, status = self.calculate_ingredient_nutrition(ingredient, sub_recipes_cache)
            
            if nutrition:
                # Добавляем к общей питательности
                for key in total_nutrition:
                    total_nutrition[key] += nutrition[key]
                
                if "calculated" in status or "subrecipe_calculated" in status:
                    found_ingredients += 1
            else:
                # Добавляем issue для отсутствующих данных
                if "subrecipe_not_found" in status or "subrecipe_no_nutrition" in status:
                    # Issues для проблем с подрецептами
                    subrecipe_title = status.split('_', 3)[-1] if '_' in status else "unknown"
                    missing = []
                    if "not_found" in status:
                        missing.append("recipe")
                    if "no_nutrition" in status:
                        missing.append("nutrition")
                    
                    issues.append({
                        "type": "subRecipeNotReady",
                        "name": subrecipe_title,
                        "missing": missing
                    })
                elif "no_mass_for_pcs" in status:
                    issues.append({
                        "type": "noMassForPcs",
                        "name": ingredient.name
                    })
                else:
                    issues.append({
                        "type": "noNutrition",
                        "name": ingredient.name,
                        "hint": "add to nutrition catalog / map canonical_id"
                    })
        
        # Рассчитываем покрытие
        total_ingredients = len(tech_card.ingredients)
        coverage_pct = (found_ingredients / total_ingredients * 100) if total_ingredients > 0 else 0
        
        # Создаем питательность на 100г
        batch_grams = tech_card.yield_.perBatch_g if tech_card.yield_ else 1.0
        per100g = NutritionPer(
            kcal=round(total_nutrition["kcal"] * 100 / batch_grams, 1),
            proteins_g=round(total_nutrition["proteins_g"] * 100 / batch_grams, 1),
            fats_g=round(total_nutrition["fats_g"] * 100 / batch_grams, 1),
            carbs_g=round(total_nutrition["carbs_g"] * 100 / batch_grams, 1)
        )
        
        # Создаем питательность на порцию
        portion_grams = tech_card.yield_.perPortion_g if tech_card.yield_ else batch_grams / max(tech_card.portions, 1)
        per_portion = NutritionPer(
            kcal=round(per100g.kcal * portion_grams / 100, 1),
            proteins_g=round(per100g.proteins_g * portion_grams / 100, 1),
            fats_g=round(per100g.fats_g * portion_grams / 100, 1),
            carbs_g=round(per100g.carbs_g * portion_grams / 100, 1)
        )
        
        # Создаем метаданные
        nutrition_meta = NutritionMetaV2(
            source="catalog",
            coveragePct=round(coverage_pct, 1)
        )
        
        # Создаем результат
        nutrition = NutritionV2(
            per100g=per100g,
            perPortion=per_portion
        )
        
        return nutrition, nutrition_meta, issues

def calculate_nutrition_for_tech_card(tech_card: TechCardV2, sub_recipes_cache: Dict[str, TechCardV2] = None) -> TechCardV2:
    """
    Функция-обертка для расчета питательности техкарты
    Возвращает обновленную техкарту с заполненными полями nutrition и nutritionMeta
    """
    calculator = NutritionCalculator()
    nutrition, nutrition_meta, nutrition_issues = calculator.calculate_tech_card_nutrition(tech_card, sub_recipes_cache)
    
    # Обновляем техкарту с рассчитанной питательностью и метаданными
    tech_card.nutrition = nutrition
    tech_card.nutritionMeta = nutrition_meta
    
    return tech_card