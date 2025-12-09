"""
Nutrition Calculator для TechCardV2
Модуль для расчета БЖУ (белки, жиры, углеводы, калории) по ингредиентам
Поддерживает USDA FoodData Central как первичный источник данных
"""

import json
import os
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

from .schemas import TechCardV2, IngredientV2, NutritionV2, NutritionPer, NutritionMetaV2

class USDANutritionProvider:
    """Провайдер данных о питательности из USDA FoodData Central"""
    
    def __init__(self):
        self.usda_db_path = os.path.join(os.path.dirname(__file__), "../../data/usda/usda.sqlite")
        self.canonical_map_path = os.path.join(os.path.dirname(__file__), "../../data/usda/canonical_map.json")
        self.canonical_map = self._load_canonical_map()
        
    def _load_canonical_map(self) -> Dict[str, Any]:
        """Загрузка канонического маппинга ингредиентов к USDA FDC ID"""
        try:
            with open(self.canonical_map_path, 'r', encoding='utf-8') as f:
                mapping_list = json.load(f)
                
            # Создаем индекс для быстрого поиска
            mapping = {}
            for item in mapping_list:
                canonical_id = item['canonical_id']
                fdc_id = item['fdc_id']
                synonyms = item['synonyms']
                
                # Индексируем по canonical_id 
                mapping[canonical_id] = {'fdc_id': fdc_id, 'synonyms': synonyms}
                
                # Индексируем по каждому синониму
                for synonym in synonyms:
                    mapping[synonym.lower()] = {'fdc_id': fdc_id, 'canonical_id': canonical_id}
                    
            return mapping
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def find_nutrition_data(self, ingredient_name: str, canonical_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Поиск данных о питательности в USDA базе
        Порядок поиска: canonical_id → fuzzy по synonyms → нет данных
        """
        if not os.path.exists(self.usda_db_path):
            return None
            
        try:
            conn = sqlite3.connect(self.usda_db_path)
            cursor = conn.cursor()
            
            fdc_id = None
            source_info = None
            
            # 1. Прямой поиск по canonical_id
            if canonical_id and canonical_id in self.canonical_map:
                fdc_id = self.canonical_map[canonical_id]['fdc_id']
                source_info = "canonical_id_direct"
            
            # 2. Поиск по точному совпадению синонимов
            if not fdc_id:
                ingredient_lower = ingredient_name.lower().strip()
                if ingredient_lower in self.canonical_map:
                    fdc_id = self.canonical_map[ingredient_lower]['fdc_id']
                    source_info = "synonym_exact"
            
            # 3. Fuzzy поиск по синонимам (порог 0.85)
            if not fdc_id:
                best_ratio = 0.0
                best_fdc_id = None
                
                for synonym, data in self.canonical_map.items():
                    if 'fdc_id' in data:  # Это синоним, не canonical_id
                        ratio = SequenceMatcher(None, ingredient_name.lower(), synonym).ratio()
                        if ratio > best_ratio and ratio >= 0.85:
                            best_ratio = ratio
                            best_fdc_id = data['fdc_id']
                
                if best_fdc_id:
                    fdc_id = best_fdc_id
                    source_info = f"synonym_fuzzy_{best_ratio:.2f}"
            
            # Если FDC ID найден, получаем данные из SQLite
            if fdc_id:
                # Получаем базовую информацию о продукте
                cursor.execute("SELECT description FROM foods WHERE fdc_id = ?", (fdc_id,))
                food_info = cursor.fetchone()
                
                if not food_info:
                    conn.close()
                    return None
                    
                # Получаем данные о питательности (nutrient_id: 1008=kcal, 1003=protein, 1004=fat, 1005=carbs)
                cursor.execute("""
                    SELECT nutrient_id, amount 
                    FROM food_nutrient 
                    WHERE fdc_id = ? AND nutrient_id IN (1008, 1003, 1004, 1005)
                """, (fdc_id,))
                
                nutrients = dict(cursor.fetchall())
                
                # Проверяем наличие основных питательных веществ
                if 1008 not in nutrients:  # Нет калорий
                    conn.close()
                    return None
                
                # Получаем данные о порциях для pcs конверсии
                cursor.execute("""
                    SELECT portion_description, gram_weight
                    FROM food_portion
                    WHERE fdc_id = ?
                """, (fdc_id,))
                
                portions = dict(cursor.fetchall())
                
                conn.close()
                
                # Формируем результат в том же формате что и JSON каталоги
                result = {
                    "fdc_id": fdc_id,
                    "description": food_info[0],
                    "per100g": {
                        "kcal": float(nutrients.get(1008, 0)),
                        "proteins_g": float(nutrients.get(1003, 0)),
                        "fats_g": float(nutrients.get(1004, 0)),
                        "carbs_g": float(nutrients.get(1005, 0))
                    },
                    "source": f"usda_{source_info}"
                }
                
                # Добавляем информацию о порциях если есть
                if portions:
                    # Ищем подходящую порцию для pcs конверсии
                    for desc, weight in portions.items():
                        if any(word in desc.lower() for word in ['egg', 'яйцо', 'large', 'medium', 'piece']):
                            result["mass_per_piece_g"] = float(weight)
                            break
                
                return result
                
            conn.close()
            return None
            
        except Exception as e:
            print(f"USDA nutrition lookup error: {e}")
            return None


class NutritionCalculator:
    """Калькулятор БЖУ для техкарт с поддержкой USDA данных"""
    
    def __init__(self, catalog_path: str = None, use_bootstrap: bool = True, use_usda: bool = True):
        """Инициализация с каталогом питательных веществ и USDA"""
        if catalog_path is None:
            catalog_path = os.path.join(os.path.dirname(__file__), "../../data/nutrition_catalog.dev.json")
        
        self.catalog_path = catalog_path
        self.use_bootstrap = use_bootstrap
        self.use_usda = use_usda
        
        # Инициализируем провайдеры данных в порядке приоритета
        self.usda_provider = USDANutritionProvider() if use_usda else None
        self.catalog = self._load_catalog()
        self.nutrition_index = self._build_nutrition_index()
        self.densities = self.catalog.get("densities", {})
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Загрузка каталога питательных веществ из JSON"""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
                
            # Проверяем, есть ли данные в каталоге
            items_count = len(catalog.get("items", []))
            
            # Если каталог пустой и включена поддержка bootstrap
            if items_count < 10 and self.use_bootstrap:
                return self._load_bootstrap_catalog()
            
            return catalog
        except FileNotFoundError:
            if self.use_bootstrap:
                return self._load_bootstrap_catalog()
            return {"items": [], "densities": {}}
        except json.JSONDecodeError:
            if self.use_bootstrap:
                return self._load_bootstrap_catalog()
            return {"items": [], "densities": {}}
    
    def _load_bootstrap_catalog(self) -> Dict[str, Any]:
        """Загружает bootstrap каталог питания из JSON"""
        try:
            bootstrap_path = os.path.join(os.path.dirname(__file__), "../../data/bootstrap/nutrition_ru.demo.json")
            
            if not os.path.exists(bootstrap_path):
                return {"items": [], "densities": {}}
            
            with open(bootstrap_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading bootstrap nutrition catalog: {e}")
            return {"items": [], "densities": {}}
    
    def _build_nutrition_index(self) -> Dict[str, Dict[str, Any]]:
        """Создает индекс всех продуктов для быстрого поиска с улучшенным маппингом"""
        index = {}
        items = self.catalog.get("items", [])
        
        for item in items:
            name = item.get("name", "").lower()
            if name:
                # Основное название
                index[name] = item
                
                # Добавляем без лишних слов для лучшего поиска
                clean_name = self._clean_ingredient_name(name)
                if clean_name != name:
                    index[clean_name] = item
                
                # TECH CARD QUALITY BOOST: Добавляем улучшенное индексирование по ключевым словам
                # Разбиваем название на слова и индексируем каждое ключевое слово
                words = name.split()
                if len(words) > 1:
                    # Для составных названий добавляем каждое ключевое слово
                    for word in words:
                        if len(word) > 3:  # Индексируем только слова длиннее 3 символов
                            if word not in index:  # Не перезаписываем если уже есть точное совпадение
                                index[word] = item
                
            # Добавляем canonical_id для поиска
            canonical_id = item.get("canonical_id", "").lower()
            if canonical_id:
                index[canonical_id] = item
        
        print(f"🔧 TECH CARD QUALITY BOOST: Built nutrition index with {len(index)} entries")
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
    
    def find_nutrition_data(self, ingredient_name: str, canonical_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Поиск данных о питательности ингредиента
        TECH CARD QUALITY BOOST: Улучшенная логика поиска с использованием расширенного каталога
        Порядок источников: dev-каталог → USDA → bootstrap
        Возвращает: данные продукта или None
        """
        
        # TECH CARD QUALITY BOOST: Сначала пробуем расширенный локальный каталог (приоритет)
        clean_name = ingredient_name.lower().strip()
        
        # 1. Прямое совпадение по названию
        if clean_name in self.nutrition_index:
            result = self.nutrition_index[clean_name].copy()
            result["source"] = "catalog"
            return result
        
        # 2. Поиск по canonical_id
        if canonical_id and canonical_id.lower() in self.nutrition_index:
            result = self.nutrition_index[canonical_id.lower()].copy()
            result["source"] = "catalog_canonical"
            return result
        
        # 3. Поиск с очищенным названием
        clean_name_processed = self._clean_ingredient_name(ingredient_name)
        if clean_name_processed in self.nutrition_index:
            result = self.nutrition_index[clean_name_processed].copy()
            result["source"] = "catalog_clean"
            return result
        
        # 4. TECH CARD QUALITY BOOST: Поиск по ключевым словам
        words = clean_name.split()
        for word in words:
            if len(word) > 3 and word in self.nutrition_index:
                result = self.nutrition_index[word].copy()
                result["source"] = "catalog_keyword"
                return result
        
        # 5. Fuzzy matching для близких совпадений (80% порог для каталогов)
        best_match = None
        best_ratio = 0.0
        
        for indexed_name, item_data in self.nutrition_index.items():
            ratio = SequenceMatcher(None, clean_name, indexed_name).ratio()
            if ratio > best_ratio and ratio >= 0.8:  # 80% совпадение для питания
                best_ratio = ratio
                best_match = item_data.copy()
                best_match["source"] = f"catalog_fuzzy_{best_ratio:.2f}"
        
        if best_match:
            return best_match
        
        # 6. Только если в каталоге не найдено - пробуем USDA (если включен)
        if self.use_usda and self.usda_provider:
            usda_data = self.usda_provider.find_nutrition_data(ingredient_name, canonical_id)
            if usda_data:
                return usda_data
        
        return None
    
    def _convert_to_grams(self, amount: float, unit: str, ingredient_name: str = "", nutrition_data: Dict[str, Any] = None) -> Tuple[float, str]:
        """
        Конвертация количества в граммы с поддержкой USDA порций
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
            # Для штук сначала проверяем USDA данные, затем обычную логику
            mass_per_piece = None
            
            # 1. Проверяем USDA данные (приоритет)
            if nutrition_data and "mass_per_piece_g" in nutrition_data:
                mass_per_piece = nutrition_data["mass_per_piece_g"]
                source = "usda_portion"
            else:
                # 2. Проверяем обычный каталог
                nutrition_fallback = self.find_nutrition_data(ingredient_name)
                if nutrition_fallback and "mass_per_piece_g" in nutrition_fallback:
                    mass_per_piece = nutrition_fallback["mass_per_piece_g"]
                    source = "catalog_portion"
            
            if mass_per_piece:
                grams = amount * mass_per_piece
                return grams, f"pcs_to_g_{source}_{mass_per_piece}g"
            else:
                return 0.0, "no_mass_for_pcs"
        
        return amount, "unknown_unit"
    
    def calculate_ingredient_nutrition(self, ingredient: IngredientV2, sub_recipes_cache: Dict[str, TechCardV2] = None) -> Tuple[Optional[Dict[str, float]], str]:
        """
        Расчет питательности одного ингредиента или подрецепта с поддержкой USDA
        Возвращает: (питательность, статус)
        """
        # Если это подрецепт - рассчитываем через него
        if ingredient.subRecipe:
            return self._calculate_subrecipe_nutrition(ingredient, sub_recipes_cache or {})
        
        # Обычная логика для обычных ингредиентов
        # Ищем данные о питательности (USDA → dev-каталог → bootstrap)
        canonical_id = getattr(ingredient, 'canonical_id', None)
        nutrition_data = self.find_nutrition_data(ingredient.name, canonical_id)
        
        if not nutrition_data or "per100g" not in nutrition_data:
            return None, "no_nutrition_data"
        
        per100g = nutrition_data["per100g"]
        
        # Конвертируем в граммы (передаем nutrition_data для USDA порций)
        mass_grams, conversion_status = self._convert_to_grams(
            ingredient.netto_g, 
            ingredient.unit,
            ingredient.name,
            nutrition_data  # Передаем данные о продукте для поиска порций
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
        
        # Определяем статус с учетом источника данных
        source = nutrition_data.get("source", "catalog")
        status = f"calculated_{conversion_status}_{source}"
        
        return nutrition, status
    
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
        Расчет полной питательности техкарты с поддержкой USDA
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
        source_stats = {"usda": 0, "catalog": 0, "bootstrap": 0}
        
        # Рассчитываем питательность каждого ингредиента
        for ingredient in tech_card.ingredients:
            nutrition, status = self.calculate_ingredient_nutrition(ingredient, sub_recipes_cache)
            
            if nutrition:
                # Добавляем к общей питательности
                for key in total_nutrition:
                    total_nutrition[key] += nutrition[key]
                
                if "calculated" in status or "subrecipe_calculated" in status:
                    found_ingredients += 1
                    
                    # Подсчитываем источники для метаданных
                    if "usda" in status:
                        source_stats["usda"] += 1
                    elif "bootstrap" in status:
                        # Если нашли через bootstrap каталог
                        source_stats["bootstrap"] += 1  
                    else:
                        source_stats["catalog"] += 1
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
        
        # Определяем основной источник данных
        if source_stats["usda"] > source_stats["catalog"] and source_stats["usda"] > source_stats["bootstrap"]:
            primary_source = "usda"
        elif source_stats["bootstrap"] > source_stats["catalog"]:
            primary_source = "bootstrap"
        else:
            primary_source = "catalog"
        
        # FIX: Safely calculate batch_grams with fallback to sum of netto_g
        if tech_card.yield_ and tech_card.yield_.perBatch_g and tech_card.yield_.perBatch_g > 0:
            batch_grams = tech_card.yield_.perBatch_g
        else:
            # Fallback: calculate from sum of netto_g (more accurate than 1.0)
            total_netto = sum(float(ing.netto_g or 0) for ing in tech_card.ingredients)
            if total_netto > 0:
                batch_grams = total_netto
            else:
                # Last resort: use portions * default portion size
                portions = max(tech_card.portions, 1)
                batch_grams = portions * 200.0  # Default 200g per portion
        
        # FIX: Validate batch_grams is reasonable (not too small)
        if batch_grams < 10.0:
            # If batch_grams is too small, recalculate from ingredients
            total_netto = sum(float(ing.netto_g or 0) for ing in tech_card.ingredients)
            if total_netto > 0:
                batch_grams = total_netto
                print(f"⚠️ KBJU FIX: batch_grams was too small ({batch_grams}), recalculated from netto_g: {batch_grams}")
            else:
                # Use default
                portions = max(tech_card.portions, 1)
                batch_grams = portions * 200.0
                print(f"⚠️ KBJU FIX: batch_grams was too small, using default: {batch_grams}")
        
        # Создаем питательность на 100г
        per100g = NutritionPer(
            kcal=round(total_nutrition["kcal"] * 100 / batch_grams, 1) if batch_grams > 0 else 0.0,
            proteins_g=round(total_nutrition["proteins_g"] * 100 / batch_grams, 1) if batch_grams > 0 else 0.0,
            fats_g=round(total_nutrition["fats_g"] * 100 / batch_grams, 1) if batch_grams > 0 else 0.0,
            carbs_g=round(total_nutrition["carbs_g"] * 100 / batch_grams, 1) if batch_grams > 0 else 0.0
        )
        
        # FIX: Safely calculate portion_grams with validation
        if tech_card.yield_ and tech_card.yield_.perPortion_g and tech_card.yield_.perPortion_g > 0:
            portion_grams = tech_card.yield_.perPortion_g
        else:
            # Fallback: calculate from batch_grams and portions
            portions = max(tech_card.portions, 1)
            portion_grams = batch_grams / portions
        
        # FIX: Validate portion_grams is reasonable (not too small or too large)
        if portion_grams < 10.0 or portion_grams > 2000.0:
            # Recalculate from batch_grams and portions
            portions = max(tech_card.portions, 1)
            portion_grams = batch_grams / portions
            if portion_grams < 10.0:
                portion_grams = 200.0  # Default portion size
                print(f"⚠️ KBJU FIX: portion_grams was invalid, using default: {portion_grams}")
            elif portion_grams > 2000.0:
                portion_grams = 200.0  # Default portion size
                print(f"⚠️ KBJU FIX: portion_grams was too large, using default: {portion_grams}")
        
        # Создаем питательность на порцию
        per_portion = NutritionPer(
            kcal=round(per100g.kcal * portion_grams / 100, 1),
            proteins_g=round(per100g.proteins_g * portion_grams / 100, 1),
            fats_g=round(per100g.fats_g * portion_grams / 100, 1),
            carbs_g=round(per100g.carbs_g * portion_grams / 100, 1)
        )
        
        # FIX: Log calculation details for debugging
        print(f"🔍 KBJU Calculation: batch_grams={batch_grams}, portion_grams={portion_grams}, per100g.kcal={per100g.kcal}, per_portion.kcal={per_portion.kcal}")
        
        # Создаем метаданные
        nutrition_meta = NutritionMetaV2(
            source=primary_source,
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
    GX-01-FINAL: Возвращает обновленную техкарту с заполненными полями nutrition и nutritionMeta
    """
    calculator = NutritionCalculator()
    nutrition, nutrition_meta, nutrition_issues = calculator.calculate_tech_card_nutrition(tech_card, sub_recipes_cache)
    
    # GX-01-FINAL: Создаем новую техкарту с обновленной питательностью (чистая функция)
    updated_tech_card = tech_card.model_copy(update={
        "nutrition": nutrition,
        "nutritionMeta": nutrition_meta
    })
    
    # Issues обрабатываются в pipeline, не здесь
    return updated_tech_card