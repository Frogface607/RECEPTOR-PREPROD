"""
P0.3: Enhanced Mapping Service with Performance Optimizations ≤3s
Optimized for batch-50 ingredients with caching, indexing, and profiling
"""

import os
import json
import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from fuzzywuzzy import fuzz, process
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

from .iiko_rms_service import get_iiko_rms_service
from .iiko_rms_models import IikoRmsMapping

logger = logging.getLogger(__name__)


class EnhancedMappingService:
    """P0.3: Performance-optimized mapping service ≤3s for batch-50"""
    
    def __init__(self):
        self.rms_service = get_iiko_rms_service()
        self.ru_synonyms = self._load_ru_synonyms()
        
        # P0.3: Performance optimizations
        self.max_workers = 8  # Ограниченный пул потоков
        self._product_index = {}  # Предрассчитанный индекс
        self._cache = {}  # LRU кэш 500 ключей
        self._cache_max_size = 500
        self._cache_ttl = 24 * 60 * 60  # 24 часа TTL
        
        # Scoring thresholds
        self.auto_accept_threshold = 0.90  
        self.review_threshold = 0.70       
    
    def _load_ru_synonyms(self) -> Dict[str, List[str]]:
        """Load Russian synonyms dictionary (30 базовых позиций)"""
        synonyms = {
            # Молочные продукты
            "яйца": [
                "яйцо куриное", "яйцо С1", "яйцо С0", "яйца куриные столовые",
                "яйцо столовое", "egg", "eggs", "куриное яйцо"
            ],
            "молоко": [
                "молоко 3.2%", "молоко коровье", "молоко цельное", "молоко питьевое",
                "молоко пастеризованное", "milk", "молоко свежее"
            ],
            "сливки": [
                "сливки 33%", "сливки 35%", "сливки жирные", "сливки для взбивания",
                "сливки кулинарные", "cream", "heavy cream"
            ],
            "сметана": [
                "сметана 20%", "сметана 15%", "сметана домашняя", "sour cream", "сметана густая"
            ],
            "творог": [
                "творог 9%", "творог жирный", "творог домашний", "cottage cheese", "творог зернистый"
            ],
            "сыр": [
                "сыр твердый", "сыр российский", "сыр голландский", "cheese", "сыр полутвердый"
            ],
            "масло сливочное": [
                "масло", "сливочное масло", "butter", "масло 82.5%", "масло крестьянское"
            ],
            
            # Мясо и птица  
            "говядина": [
                "мясо говяжье", "говядина свежая", "beef", "телятина", "говядина мраморная",
                "вырезка говяжья", "грудинка говяжья"
            ],
            "свинина": [
                "мясо свиное", "свинина свежая", "pork", "корейка свиная", "окорок свиной"
            ],
            "курица": [
                "куриное мясо", "птица", "chicken", "курица домашняя", "бройлер",
                "филе куриное", "грудка куриная"
            ],
            "баранина": [
                "мясо баранье", "баранина свежая", "lamb", "ягненок", "каре ягненка"
            ],
            
            # Овощи
            "лук": [
                "лук репчатый", "лук желтый", "onion", "лук свежий", "лук крупный",
                "лук белый", "лук красный"
            ],
            "морковь": [
                "морковка", "carrot", "морковь свежая", "морковь столовая", "морковь оранжевая"
            ],
            "картофель": [
                "картошка", "potato", "картофель свежий", "картофель столовый", "клубни картофеля"
            ],
            "помидоры": [
                "томаты", "tomato", "помидор", "томат свежий", "помидоры красные",
                "томаты черри", "помидоры грунтовые"
            ],
            "огурцы": [
                "огурец", "cucumber", "огурцы свежие", "огурцы соленые", "огурцы грунтовые"
            ],
            "капуста": [
                "капуста белокочанная", "cabbage", "капуста свежая", "капуста молодая"
            ],
            "перец болгарский": [
                "перец сладкий", "bell pepper", "перец красный", "перец желтый", "перец зеленый"
            ],
            "чеснок": [
                "garlic", "чеснок свежий", "зубчики чеснока", "головка чеснока"
            ],
            
            # Зелень и приправы
            "петрушка": [
                "зелень петрушки", "parsley", "петрушка свежая", "листья петрушки"
            ],
            "укроп": [
                "зелень укропа", "dill", "укроп свежий", "веточки укропа"
            ],
            "базилик": [
                "зелень базилика", "basil", "базилик свежий", "листья базилика"
            ],
            "кинза": [
                "кориандр", "cilantro", "кинза свежая", "зелень кинзы"
            ],
            
            # Крупы и мука
            "рис": [
                "rice", "рис круглозерный", "рис длиннозерный", "рис белый", "крупа рисовая"
            ],
            "гречка": [
                "гречневая крупа", "buckwheat", "гречка ядрица", "гречиха"
            ],
            "мука": [
                "мука пшеничная", "flour", "мука высшего сорта", "мука белая", "мука хлебопекарная"
            ],
            "овсянка": [
                "овсяные хлопья", "oats", "геркулес", "овес", "хлопья овсяные"
            ],
            
            # Жиры и масла
            "масло растительное": [
                "масло подсолнечное", "vegetable oil", "масло рафинированное", 
                "масло дезодорированное", "подсолнечное масло"
            ],
            "оливковое масло": [
                "масло оливковое", "olive oil", "масло extra virgin", "олива"
            ],
            
            # Специи и приправы  
            "соль": [
                "соль поваренная", "salt", "соль пищевая", "соль морская", "соль каменная"
            ],
            "сахар": [
                "сахар-песок", "sugar", "сахар белый", "сахар свекловичный"
            ],
            "перец черный": [
                "перец молотый", "black pepper", "перец горошком", "специи"
            ],
            
            # Консервы и заготовки
            "томатная паста": [
                "паста томатная", "tomato paste", "концентрат томатный", "томат-паста"
            ]
        }
        
        # Load custom synonyms if available
        try:
            custom_synonyms_path = "/app/backend/data/ru_synonyms_extended.json"
            if os.path.exists(custom_synonyms_path):
                with open(custom_synonyms_path, 'r', encoding='utf-8') as f:
                    custom_synonyms = json.load(f)
                    synonyms.update(custom_synonyms)
                    logger.info(f"Loaded {len(custom_synonyms)} custom synonyms")
        except Exception as e:
            logger.warning(f"Failed to load custom synonyms: {e}")
        
        logger.info(f"Loaded {len(synonyms)} synonym groups with RU support")
        return synonyms
    
    def _build_product_index(self, rms_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """P0.3: Предрассчитать индекс продуктов для быстрого поиска"""
        start_time = time.time()
        
        index = {
            "by_normalized_name": {},  # normName -> [products]
            "by_tokens": {},          # token -> [products] 
            "by_synonyms": {},        # synonym -> [products]
            "products_slim": {}       # product_id -> slim_product (payload diet)
        }
        
        for product in rms_products:
            product_id = str(product["_id"])
            product_name = product["name"]
            
            # P0.3: Payload diet - только нужные поля
            slim_product = {
                "_id": product_id,
                "name": product_name,
                "unit": product.get("unit", "г"),
                "price_per_unit": product.get("price_per_unit", 0.0),
                "group_name": product.get("group_name", ""),
                "article": product.get("article", "")
            }
            index["products_slim"][product_id] = slim_product
            
            # Нормализованное имя
            norm_name = self._normalize_for_matching(product_name.lower())
            if norm_name not in index["by_normalized_name"]:
                index["by_normalized_name"][norm_name] = []
            index["by_normalized_name"][norm_name].append(product_id)
            
            # Токены для частичного поиска
            tokens = norm_name.split()
            for token in tokens:
                if len(token) > 2:  # Игнорировать короткие токены
                    if token not in index["by_tokens"]:
                        index["by_tokens"][token] = []
                    index["by_tokens"][token].append(product_id)
            
            # Синонимы
            product_lower = product_name.lower()
            for canonical, synonyms in self.ru_synonyms.items():
                for synonym in synonyms:
                    if synonym.lower() in product_lower:
                        if canonical not in index["by_synonyms"]:
                            index["by_synonyms"][canonical] = []
                        index["by_synonyms"][canonical].append(product_id)
        
        build_time = (time.time() - start_time) * 1000
        logger.info(f"P0.3: Product index built in {build_time:.1f}ms for {len(rms_products)} products")
        
        return index
    
    def _get_cache_key(self, ingredient_name: str, organization_id: str) -> str:
        """P0.3: Генерация ключа кэша"""
        normalized = self._normalize_for_matching(ingredient_name.lower())
        return hashlib.md5(f"{normalized}:{organization_id}".encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """P0.3: Получение результата из кэша с проверкой TTL"""
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if time.time() - entry["timestamp"] < self._cache_ttl:
                return entry["result"]
            else:
                # Expired entry
                del self._cache[cache_key]
        return None
    
    def _set_cached_result(self, cache_key: str, result: Dict[str, Any]):
        """P0.3: Сохранение результата в LRU кэш"""
        # LRU eviction if cache is full
        if len(self._cache) >= self._cache_max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]
        
        self._cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
    
    def _find_fast_matches(self, ingredient_name: str, index: Dict[str, Any]) -> List[Dict[str, Any]]:
        """P0.3: Быстрый поиск совпадений через индекс (вместо полного сканирования)"""
        matches = []
        ingredient_lower = ingredient_name.lower().strip()
        norm_ingredient = self._normalize_for_matching(ingredient_lower)
        
        # Strategy 1: Exact normalized match (fastest)
        if norm_ingredient in index["by_normalized_name"]:
            for product_id in index["by_normalized_name"][norm_ingredient]:
                product = index["products_slim"][product_id]
                matches.append({
                    "product": product,
                    "confidence": 0.95,
                    "match_type": "exact_normalized",
                    "match_reason": "Точное нормализованное совпадение"
                })
        
        # Strategy 2: Synonym matching
        canonical_form = self._find_canonical_form(ingredient_lower)
        if canonical_form and canonical_form in index["by_synonyms"]:
            for product_id in index["by_synonyms"][canonical_form]:
                if product_id not in [m["product"]["_id"] for m in matches]:
                    product = index["products_slim"][product_id]
                    matches.append({
                        "product": product,
                        "confidence": 0.90,
                        "match_type": "synonym",
                        "match_reason": f"Синоним: {canonical_form}"
                    })
        
        # Strategy 3: Token-based partial matching (только если мало точных совпадений)
        if len(matches) < 3:
            tokens = norm_ingredient.split()
            candidate_products = set()
            
            for token in tokens:
                if len(token) > 2 and token in index["by_tokens"]:
                    candidate_products.update(index["by_tokens"][token])
            
            # P0.3: Top-K резка ПЕРЕД скорингом (не после)
            candidate_products = list(candidate_products)[:20]  # Топ-20 кандидатов для скоринга
            
            for product_id in candidate_products:
                if product_id not in [m["product"]["_id"] for m in matches]:
                    product = index["products_slim"][product_id] 
                    
                    # Быстрый fuzzy только для кандидатов
                    score = fuzz.partial_ratio(ingredient_lower, product["name"].lower()) / 100.0
                    
                    if score >= 0.70:  # Минимальный порог
                        matches.append({
                            "product": product,
                            "confidence": score,
                            "match_type": "partial_fuzzy",
                            "match_reason": f"Частичное совпадение: {score:.2f}"
                        })
        
        # Сортировка по confidence и возврат топ-5
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:5]  # P0.3: Top-5 резка
    
    def enhanced_auto_mapping(self, ingredients: List[Dict[str, Any]], 
                            organization_id: str) -> Dict[str, Any]:
        """
        P0.3: Performance-optimized auto-mapping ≤3s for batch-50
        Enhanced auto-mapping with Russian synonyms and confidence scoring
        GX-02: ≥0.90 автопринятие; 0.70–0.89 на проверку
        """
        try:
            start_time = time.time()
            logger.info(f"P0.3: Starting optimized auto-mapping for {len(ingredients)} ingredients")
            
            # Get RMS products for organization
            rms_products = list(self.rms_service.products.find({
                "organization_id": organization_id,
                "active": True
            }))
            
            if not rms_products:
                return {
                    "status": "no_products",
                    "message": "Номенклатура iiko не найдена. Выполните синхронизацию.",
                    "results": [],
                    "stats": {"total": 0, "auto_accept": 0, "review": 0, "no_match": 0}
                }
            
            # P0.3: Build product index for fast search (one-time cost)
            index_start = time.time()
            self._product_index = self._build_product_index(rms_products)
            index_time = (time.time() - index_start) * 1000
            logger.info(f"P0.3: Product index built in {index_time:.1f}ms")
            
            mapping_results = []
            stats = {"total": len(ingredients), "auto_accept": 0, "review": 0, "no_match": 0}
            
            # P0.3: Batch processing with parallel execution
            batch_start = time.time()
            processed_ingredients = [ing for ing in ingredients 
                                   if ing.get("name", "").strip() and not ing.get("skuId")]
            
            # Process ingredients in batches with threading
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all ingredient processing tasks
                future_to_ingredient = {
                    executor.submit(self._process_ingredient_fast, ingredient, organization_id): ingredient
                    for ingredient in processed_ingredients
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_ingredient):
                    ingredient = future_to_ingredient[future]
                    try:
                        result = future.result()
                        if result:
                            mapping_results.append(result)
                            # Update stats
                            if result["status"] == "auto_accept":
                                stats["auto_accept"] += 1
                            elif result["status"] == "review":
                                stats["review"] += 1
                    except Exception as exc:
                        logger.error(f"P0.3: Ingredient {ingredient.get('name')} processing error: {exc}")
                        stats["no_match"] += 1
            
            # Count no matches
            stats["no_match"] = stats["total"] - len(mapping_results)
            
            batch_time = (time.time() - batch_start) * 1000
            logger.info(f"P0.3: Batch processing completed in {batch_time:.1f}ms")
            
            # Sort results by confidence (highest first)
            mapping_results.sort(key=lambda x: x["confidence"], reverse=True)
            
            coverage_info = self._calculate_coverage(ingredients, mapping_results)
            
            total_time = (time.time() - start_time) * 1000
            logger.info(f"P0.3: Total enhanced auto-mapping completed in {total_time:.1f}ms")
            
            return {
                "status": "success",
                "results": mapping_results,
                "stats": stats,
                "coverage": coverage_info,
                "products_scanned": len(rms_products),
                "performance": {
                    "total_time_ms": round(total_time, 1),
                    "index_time_ms": round(index_time, 1),
                    "batch_time_ms": round(batch_time, 1),
                    "ingredients_processed": len(processed_ingredients),
                    "target_met": total_time <= 3000
                },
                "message": f"Найдено {len(mapping_results)} совпадений. " +
                          f"Автопринятие: {stats['auto_accept']}, На проверку: {stats['review']}"
            }
            
        except Exception as e:
            logger.error(f"Enhanced auto-mapping error: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка автомаппинга: {str(e)}",
                "results": [],
                "stats": {"total": 0, "auto_accept": 0, "review": 0, "no_match": 0}
            }
    
    def _process_ingredient_fast(self, ingredient: Dict[str, Any], organization_id: str) -> Optional[Dict[str, Any]]:
        """P0.3: Fast ingredient processing with caching and optimized search"""
        ingredient_name = ingredient.get("name", "").strip()
        if not ingredient_name:
            return None
            
        # P0.3: Check cache first
        cache_key = self._get_cache_key(ingredient_name, organization_id)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            # Update ingredient data in cached result
            cached_result["ingredient_name"] = ingredient_name
            cached_result["original_unit"] = ingredient.get("unit", "g")
            return cached_result
        
        # P0.3: Use fast indexed search instead of full scan
        matches = self._find_fast_matches(ingredient_name, self._product_index)
        
        if matches:
            best_match = matches[0]  # Highest scored match
            
            # Determine mapping status based on confidence
            if best_match["confidence"] >= self.auto_accept_threshold:
                status = "auto_accept"
            elif best_match["confidence"] >= self.review_threshold:
                status = "review"  
            else:
                return None  # Skip low confidence matches
            
            # Create mapping result with slim product data
            mapping_result = {
                "ingredient_name": ingredient_name,
                "original_unit": ingredient.get("unit", "g"),
                "status": status,
                "confidence": best_match["confidence"],
                "match_type": best_match["match_type"],
                "suggestion": {
                    "sku_id": best_match["product"]["_id"],
                    "name": best_match["product"]["name"],
                    "article": best_match["product"].get("article", ""),
                    "unit": best_match["product"]["unit"],
                    "price_per_unit": best_match["product"].get("price_per_unit", 0.0),
                    "currency": "RUB",
                    "group_name": best_match["product"].get("group_name"),
                    "source": "rms_enhanced"
                },
                "alternatives": matches[1:3] if len(matches) > 1 else []  # Top 2 alternatives (payload diet)
            }
            
            # P0.3: Cache the result for future use
            self._set_cached_result(cache_key, mapping_result.copy())
            
            return mapping_result
        
        return None
    
    def _find_enhanced_matches(self, ingredient_name: str, 
                              rms_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find enhanced matches using multiple scoring strategies"""
        matches = []
        ingredient_lower = ingredient_name.lower().strip()
        
        # Strategy 1: Exact synonym matching (highest confidence)
        canonical_ingredient = self._find_canonical_form(ingredient_lower)
        if canonical_ingredient:
            # Search for canonical form in products
            for product in rms_products:
                product_name_lower = product["name"].lower()
                
                # Check if product matches canonical ingredient or its synonyms
                if canonical_ingredient in self.ru_synonyms:
                    for synonym in self.ru_synonyms[canonical_ingredient]:
                        if synonym.lower() in product_name_lower or product_name_lower in synonym.lower():
                            confidence = 0.95  # High confidence for synonym matches
                            matches.append({
                                "product": product,
                                "confidence": confidence,
                                "match_type": "synonym",
                                "match_reason": f"Синоним '{synonym}' → '{product['name']}'"
                            })
                            break
        
        # Strategy 2: Direct fuzzy matching
        for product in rms_products:
            product_name = product["name"]
            
            # Fuzzy matching scores
            ratio = fuzz.ratio(ingredient_lower, product_name.lower()) / 100.0
            partial_ratio = fuzz.partial_ratio(ingredient_lower, product_name.lower()) / 100.0
            token_sort_ratio = fuzz.token_sort_ratio(ingredient_lower, product_name.lower()) / 100.0
            
            # Combined score with weights
            combined_score = (ratio * 0.4 + partial_ratio * 0.3 + token_sort_ratio * 0.3)
            
            # Boost score for exact matches
            if ingredient_lower == product_name.lower():
                combined_score = 1.0
            elif ingredient_lower in product_name.lower() or product_name.lower() in ingredient_lower:
                combined_score = max(combined_score, 0.85)
            
            # Only include matches above minimum threshold
            if combined_score >= 0.60:
                matches.append({
                    "product": product,
                    "confidence": combined_score,
                    "match_type": "fuzzy",
                    "match_reason": f"Fuzzy match: {combined_score:.2f}"
                })
        
        # Strategy 3: Normalized matching (remove special chars, units)
        normalized_ingredient = self._normalize_for_matching(ingredient_lower)
        for product in rms_products:
            normalized_product = self._normalize_for_matching(product["name"].lower())
            
            if normalized_ingredient == normalized_product:
                # Check if not already matched with higher score
                existing_match = next((m for m in matches if m["product"]["_id"] == product["_id"]), None)
                if not existing_match or existing_match["confidence"] < 0.90:
                    if existing_match:
                        matches.remove(existing_match)
                    
                    matches.append({
                        "product": product,
                        "confidence": 0.90,
                        "match_type": "normalized",
                        "match_reason": f"Normalized match: '{normalized_ingredient}'"
                    })
        
        # Remove duplicates and sort by confidence
        seen_product_ids = set()
        unique_matches = []
        for match in sorted(matches, key=lambda x: x["confidence"], reverse=True):
            product_id = match["product"]["_id"]
            if product_id not in seen_product_ids:
                seen_product_ids.add(product_id)
                unique_matches.append(match)
        
        return unique_matches[:10]  # Return top 10 matches
    
    def _find_canonical_form(self, ingredient_name: str) -> Optional[str]:
        """Find canonical form of ingredient name using synonyms"""
        for canonical, synonyms in self.ru_synonyms.items():
            # Check exact match
            if ingredient_name == canonical:
                return canonical
            
            # Check synonyms
            for synonym in synonyms:
                if ingredient_name == synonym.lower() or synonym.lower() in ingredient_name:
                    return canonical
        
        return None
    
    def _normalize_for_matching(self, text: str) -> str:
        """Normalize text for better matching (remove units, special chars)"""
        # Remove common units
        units_pattern = r'\b(г|кг|мл|л|шт|штук|граммов?|килограммов?|литров?|миллилитров?)\b'
        text = re.sub(units_pattern, '', text, flags=re.IGNORECASE)
        
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _calculate_coverage(self, ingredients: List[Dict[str, Any]], 
                          mapping_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate mapping coverage statistics"""
        total_ingredients = len([ing for ing in ingredients if ing.get("name", "").strip()])
        ingredients_with_sku = len([ing for ing in ingredients if ing.get("skuId")])
        
        auto_accept_count = len([r for r in mapping_results if r["status"] == "auto_accept"])
        review_count = len([r for r in mapping_results if r["status"] == "review"])
        
        potential_coverage = ingredients_with_sku + auto_accept_count + review_count
        potential_coverage_pct = (potential_coverage / total_ingredients * 100) if total_ingredients > 0 else 0
        
        return {
            "total_ingredients": total_ingredients,
            "current_with_sku": ingredients_with_sku,
            "auto_accept_available": auto_accept_count,
            "review_available": review_count,
            "potential_coverage": potential_coverage,
            "potential_coverage_pct": round(potential_coverage_pct, 1),
            "current_coverage_pct": round((ingredients_with_sku / total_ingredients * 100) if total_ingredients > 0 else 0, 1)
        }
    
    def apply_auto_accepted_mappings(self, techcard: Dict[str, Any], 
                                   mapping_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply auto-accepted mappings (≥0.90 confidence) to TechCard"""
        try:
            updated_card = techcard.copy()
            ingredients = updated_card.get("ingredients", [])
            
            # Create mapping lookup
            auto_accept_mappings = {
                result["ingredient_name"]: result["suggestion"] 
                for result in mapping_results 
                if result["status"] == "auto_accept"
            }
            
            applied_count = 0
            for ingredient in ingredients:
                ingredient_name = ingredient.get("name", "").strip()
                
                if ingredient_name in auto_accept_mappings and not ingredient.get("skuId"):
                    suggestion = auto_accept_mappings[ingredient_name]
                    
                    # Apply mapping
                    ingredient["skuId"] = suggestion["sku_id"]
                    # Optionally update unit if different
                    if suggestion["unit"] != ingredient.get("unit"):
                        ingredient["mapped_unit"] = suggestion["unit"]
                    
                    applied_count += 1
            
            logger.info(f"Applied {applied_count} auto-accepted mappings")
            return updated_card
            
        except Exception as e:
            logger.error(f"Error applying auto-accepted mappings: {str(e)}")
            return techcard
    
    def save_mapping_decisions(self, organization_id: str, 
                             mapping_results: List[Dict[str, Any]],
                             user_decisions: Dict[str, str]) -> Dict[str, Any]:
        """Save user mapping decisions to database for future use"""
        try:
            saved_count = 0
            
            for result in mapping_results:
                ingredient_name = result["ingredient_name"]
                user_decision = user_decisions.get(ingredient_name, "")
                
                if user_decision in ["accepted", "rejected"]:
                    # Create or update mapping record
                    mapping = IikoRmsMapping(
                        ingredient_name=ingredient_name,
                        ingredient_name_normalized=ingredient_name.lower(),
                        rms_product_id=result["suggestion"]["sku_id"],
                        rms_product_name=result["suggestion"]["name"],
                        rms_article=result["suggestion"].get("article"),
                        mapping_type="user_decision",
                        match_score=result["confidence"],
                        approved=(user_decision == "accepted"),
                        organization_id=organization_id
                    )
                    
                    # Upsert mapping
                    self.rms_service.mappings.update_one(
                        {
                            "ingredient_name": ingredient_name,
                            "rms_product_id": result["suggestion"]["sku_id"]
                        },
                        {"$set": mapping.model_dump(by_alias=True, exclude={"id"})},
                        upsert=True
                    )
                    
                    saved_count += 1
            
            logger.info(f"Saved {saved_count} user mapping decisions")
            
            return {
                "status": "success",
                "saved_count": saved_count,
                "message": f"Сохранено {saved_count} решений пользователя"
            }
            
        except Exception as e:
            logger.error(f"Error saving mapping decisions: {str(e)}")
            return {
                "status": "error", 
                "message": f"Ошибка сохранения решений: {str(e)}"
            }


# Global enhanced mapping service instance
_enhanced_mapping_service: Optional[EnhancedMappingService] = None

def get_enhanced_mapping_service() -> EnhancedMappingService:
    """Get or create global EnhancedMappingService instance"""
    global _enhanced_mapping_service
    
    if _enhanced_mapping_service is None:
        _enhanced_mapping_service = EnhancedMappingService()
    
    return _enhanced_mapping_service