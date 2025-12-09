from __future__ import annotations
import json
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import logging

logger = logging.getLogger(__name__)

class PriceProvider:
    """
    IK-03: Unified price provider with enhanced strategy sources: 
    iiko (RMS) → dev-catalog → bootstrap → llm-fallback
    """
    
    def __init__(self):
        self.iiko_prices = {}  # IK-03: iiko RMS prices (highest priority)
        self.user_prices = {}  # MongoDB user prices (if available)
        self.catalog_prices = {}  # price_catalog.dev.json
        self.bootstrap_prices = {}  # prices_ru.demo.csv
        self.knowledge_base_prices = {}  # Prices extracted from knowledge base
        self.loaded = False
        
    def _load_sources(self):
        """Load price data from all sources with IK-03 iiko RMS support"""
        if self.loaded:
            return
            
        current_dir = Path(__file__).parent.parent.parent
        
        # IK-03: 1. Load iiko RMS prices (highest priority)
        self._load_iiko_prices()
        
        # 2. Load user prices from MongoDB (graceful fallback if unavailable)
        self._load_user_prices()
        
        # 3. Load catalog prices
        catalog_path = current_dir / "data" / "price_catalog.dev.json"
        if catalog_path.exists():
            try:
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    catalog_data = json.load(f)
                    self._process_catalog_data(catalog_data)
            except Exception as e:
                logger.warning(f"Failed to load catalog prices: {e}")
        
        # 4. Load bootstrap prices  
        bootstrap_path = current_dir / "data" / "bootstrap" / "prices_ru.demo.csv"
        if bootstrap_path.exists():
            try:
                with open(bootstrap_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self._process_bootstrap_row(row)
            except Exception as e:
                logger.warning(f"Failed to load bootstrap prices: {e}")
        
        # 5. Load prices from knowledge base (lowest priority, but comprehensive)
        self._load_knowledge_base_prices()
                
        self.loaded = True
        logger.info(f"Price provider loaded: iiko={len(self.iiko_prices)}, user={len(self.user_prices)}, catalog={len(self.catalog_prices)}, bootstrap={len(self.bootstrap_prices)}, knowledge_base={len(self.knowledge_base_prices)}")
    
    def _load_iiko_prices(self):
        """IK-03: Load prices from iiko RMS integration"""
        try:
            from ..integrations.iiko_rms_service import get_iiko_rms_service
            
            # Get iiko RMS service
            rms_service = get_iiko_rms_service()
            
            # Fetch prices from cache (organization_id could be made configurable)
            prices = rms_service.get_prices(organization_id="default", active_only=True)
            
            for price in prices:
                # Normalize name for matching
                name_normalized = self._normalize_name(price["name"])
                
                # Create price entry with IK-03 fields
                price_entry = {
                    "price_per_g": price["price_per_unit"],  # Already normalized to g/ml
                    "unit": price["unit"],  # g, ml, or pcs
                    "currency": price.get("currency", "RUB"),
                    "vat_pct": price.get("vat_pct", 0.0),  # IK-03: VAT support
                    "source": "iiko",
                    "sku_id": price["skuId"],
                    "article": price.get("article"),
                    "as_of": price["as_of"],
                    "active": price.get("active", True)
                }
                
                self.iiko_prices[name_normalized] = price_entry
            
            logger.info(f"Loaded {len(self.iiko_prices)} prices from iiko RMS")
            
        except Exception as e:
            logger.warning(f"Failed to load iiko RMS prices (graceful fallback): {e}")
            # Graceful degradation - continue without iiko prices

    def _normalize_name(self, name: str) -> str:
        """Normalize ingredient name for consistent matching"""
        return name.strip().lower()
    
    def _load_knowledge_base_prices(self):
        """Load prices from knowledge base markdown files"""
        try:
            from ..rag.extract_catalog_data import extract_prices_from_knowledge_base
            
            # Extract prices from knowledge base
            kb_prices = extract_prices_from_knowledge_base()
            
            for name_normalized, price_data in kb_prices.items():
                price = price_data.get("price", 0)
                unit = price_data.get("unit", "kg")
                
                if price > 0:
                    # Convert to price per gram
                    price_per_g = self._normalize_price_to_gram(price, unit)
                    
                    sku_id = f"KB_{name_normalized.replace(' ', '_').upper()}"
                    
                    self.knowledge_base_prices[name_normalized] = {
                        "name": price_data.get("name", name_normalized),
                        "price_per_g": price_per_g,
                        "source": "knowledge_base",
                        "asOf": price_data.get("extracted_date", datetime.now().isoformat()),
                        "skuId": sku_id,
                        "unit": unit,
                        "original_price": price,
                        "category": price_data.get("category", "general")
                    }
            
            logger.info(f"Loaded {len(self.knowledge_base_prices)} prices from knowledge base")
            
        except Exception as e:
            logger.warning(f"Failed to load knowledge base prices (graceful fallback): {e}")
            self.knowledge_base_prices = {}

    def _load_user_prices(self):
        """Load user prices from MongoDB (graceful fallback if unavailable)"""
        try:
            # Try to connect to MongoDB for user_prices collection
            # If MongoDB is unavailable, gracefully continue with empty user_prices
            self.user_prices = {}  # Placeholder - implement MongoDB integration later
        except Exception as e:
            logger.info(f"MongoDB unavailable for user prices, continuing: {e}")
            self.user_prices = {}

    def _process_catalog_data(self, catalog_data: dict):
        """Process price_catalog.dev.json structure"""
        ingredients = catalog_data.get("ingredients", {})
        asOf = catalog_data.get("asOf", "2025-01-17")
        
        for category, items in ingredients.items():
            for name, details in items.items():
                price = details.get("price")
                unit = details.get("unit", "kg")
                canonical_id = details.get("canonical_id")
                
                if price and isinstance(price, (int, float)):
                    # Convert to price per gram
                    price_per_g = self._normalize_price_to_gram(price, unit)
                    
                    sku_id = f"CAT_{name.replace(' ', '_').upper()}"
                    
                    self.catalog_prices[name.lower()] = {
                        "name": name,
                        "price_per_g": price_per_g,
                        "source": "catalog", 
                        "asOf": asOf,
                        "skuId": sku_id,
                        "canonical_id": canonical_id,
                        "unit": unit,
                        "original_price": price
                    }

    def _process_bootstrap_row(self, row: dict):
        """Process prices_ru.demo.csv row"""
        try:
            name = row.get("name", "").strip()
            price = float(row.get("price", 0))
            unit = row.get("unit", "kg").strip()
            category = row.get("category", "").strip()
            
            if name and price > 0:
                price_per_g = self._normalize_price_to_gram(price, unit)
                
                sku_id = f"BOOT_{name.replace(' ', '_').upper()}"
                asOf = "2025-01-17"  # Bootstrap data date
                
                self.bootstrap_prices[name.lower()] = {
                    "name": name,
                    "price_per_g": price_per_g, 
                    "source": "bootstrap",
                    "asOf": asOf,
                    "skuId": sku_id,
                    "unit": unit,
                    "original_price": price,
                    "category": category
                }
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid bootstrap price row: {row}, error: {e}")

    def _normalize_price_to_gram(self, price: float, unit: str) -> float:
        """Convert price to RUB per gram"""
        unit = unit.lower().strip()
        
        if unit in ("g", "г", "gram", "грамм"):
            return price  # Already per gram
        elif unit in ("kg", "кг", "kilogram", "килограмм"):
            return price / 1000  # Convert kg to grams
        elif unit in ("l", "л", "liter", "литр"):
            return price / 1000  # Assume 1L = 1kg for liquids
        elif unit in ("ml", "мл", "milliliter", "миллилитр"):
            return price  # 1ml ≈ 1g for liquids
        elif unit in ("pcs", "шт", "piece", "штука"):
            # For pieces, assume standard weights
            # This should ideally use food_portion data like USDA
            standard_weights = {
                "яйцо": 50,  # 50g per egg
                "лук": 150,  # 150g per onion
                "морковь": 100,  # 100g per carrot
            }
            # Try to guess weight, fallback to 100g
            estimated_weight = 100  # Default 100g per piece
            return price / estimated_weight
        else:
            logger.warning(f"Unknown unit for price normalization: {unit}, assuming per gram")
            return price

    def resolve(self, ingredient) -> Optional[Dict]:
        """
        IK-03: Resolve price for ingredient using enhanced priority: 
        skuId → canonical_id → fuzzy name with iiko RMS as top priority
        
        Returns:
            {
                "price_per_g": float,   # RUB per gram (normalized)
                "source": "iiko"|"user"|"catalog"|"bootstrap"|"llm", 
                "asOf": "YYYY-MM-DD",
                "skuId": Optional[str],
                "vat_pct": Optional[float]  # IK-03: VAT rate if available
            } | None
        """
        self._load_sources()
        
        ingredient_name = getattr(ingredient, 'name', str(ingredient)).strip().lower()
        ingredient_sku_id = getattr(ingredient, 'skuId', None)
        ingredient_canonical_id = getattr(ingredient, 'canonical_id', None)
        
        # 1. Try by skuId first (highest priority)
        if ingredient_sku_id:
            result = self._find_by_sku_id(ingredient_sku_id)
            if result:
                return result
        
        # 2. Try by canonical_id 
        if ingredient_canonical_id:
            result = self._find_by_canonical_id(ingredient_canonical_id)
            if result:
                return result
        
        # 3. Try fuzzy matching by name (threshold 0.85)
        result = self._find_by_fuzzy_name(ingredient_name)
        if result:
            return result
        
        # 4. LLM fallback (if enabled)
        if os.getenv("PRICE_VIA_LLM", "false").lower() in ("1", "true"):
            result = self._llm_fallback_pricing(ingredient_name)
            if result:
                return result
        
        return None

    def _find_by_sku_id(self, sku_id: str) -> Optional[Dict]:
        """Find price by SKU ID in all sources"""
        # Search in iiko prices first (highest priority)
        for price_data in self.iiko_prices.values():
            if price_data.get("sku_id") == sku_id:
                return price_data
        
        # Search in user prices
        for price_data in self.user_prices.values():
            if price_data.get("skuId") == sku_id:
                return price_data
        
        # Search in catalog
        for price_data in self.catalog_prices.values():
            if price_data.get("skuId") == sku_id:
                return price_data
        
        # Search in bootstrap  
        for price_data in self.bootstrap_prices.values():
            if price_data.get("skuId") == sku_id:
                return price_data
        
        return None

    def _find_by_canonical_id(self, canonical_id: str) -> Optional[Dict]:
        """Find price by canonical_id in all sources"""
        # Search in iiko prices first (highest priority)
        for price_data in self.iiko_prices.values():
            if price_data.get("canonical_id") == canonical_id:
                return price_data
        
        # Search in user prices
        for price_data in self.user_prices.values():
            if price_data.get("canonical_id") == canonical_id:
                return price_data
        
        # Search in catalog
        for price_data in self.catalog_prices.values():
            if price_data.get("canonical_id") == canonical_id:
                return price_data
                
        # Bootstrap prices don't have canonical_id mapping yet
        return None

    def _find_by_fuzzy_name(self, ingredient_name: str) -> Optional[Dict]:
        """Find price by fuzzy name matching (threshold 0.85)"""
        best_match = None
        best_score = 0
        threshold = 85  # 85% similarity
        
        # Search all sources in priority order
        all_sources = [
            (self.iiko_prices, "iiko"),
            (self.user_prices, "user"),
            (self.catalog_prices, "catalog"), 
            (self.bootstrap_prices, "bootstrap"),
            (self.knowledge_base_prices, "knowledge_base")
        ]
        
        for source_dict, source_name in all_sources:
            for key, price_data in source_dict.items():
                # Try both the key and the original name
                names_to_try = [key, price_data.get("name", "").lower()]
                
                for name_variant in names_to_try:
                    if not name_variant:
                        continue
                        
                    score = fuzz.ratio(ingredient_name, name_variant)
                    if score >= threshold and score > best_score:
                        best_score = score
                        best_match = price_data
                        
                    # Also try partial matching
                    partial_score = fuzz.partial_ratio(ingredient_name, name_variant)
                    if partial_score >= threshold and partial_score > best_score:
                        best_score = partial_score
                        best_match = price_data
        
        return best_match

    def _llm_fallback_pricing(self, ingredient_name: str) -> Optional[Dict]:
        """LLM-based fallback pricing (placeholder)"""
        # This is the existing fallback logic from cost_calculator
        # Could be enhanced with actual LLM calls in the future
        fallback_prices = {
            "мясо": 500,    # 500 RUB/kg
            "рыба": 400,    # 400 RUB/kg  
            "овощи": 100,   # 100 RUB/kg
            "специи": 1000, # 1000 RUB/kg
        }
        
        # Simple category detection
        category = "other"
        if any(word in ingredient_name for word in ["говядина", "свинина", "курица", "мясо"]):
            category = "мясо"
        elif any(word in ingredient_name for word in ["рыба", "треска", "лосось", "судак"]):
            category = "рыба"
        elif any(word in ingredient_name for word in ["лук", "морковь", "картофель", "капуста"]):
            category = "овощи"
        elif any(word in ingredient_name for word in ["соль", "перец", "специи", "приправа"]):
            category = "специи"
        
        price_per_kg = fallback_prices.get(category, 150)  # Default 150 RUB/kg
        price_per_g = price_per_kg / 1000
        
        return {
            "price_per_g": price_per_g,
            "source": "llm",
            "asOf": datetime.now().strftime("%Y-%m-%d"),
            "skuId": f"LLM_{ingredient_name.replace(' ', '_').upper()}"
        }

    def search_for_mapping(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search prices for mapping interface
        Returns candidates in format: {source, name, skuId, unit, price_per_unit, currency, asOf}
        """
        self._load_sources()
        
        results = []
        query_lower = query.lower().strip()
        
        if not query_lower:
            return results
        
        # Search all sources
        all_sources = [
            (self.iiko_prices, "iiko"),
            (self.user_prices, "user"),
            (self.catalog_prices, "catalog"),
            (self.bootstrap_prices, "bootstrap"),
            (self.knowledge_base_prices, "knowledge_base")
        ]
        
        for source_dict, source_name in all_sources:
            for key, price_data in source_dict.items():
                # Check if query matches
                name = price_data.get("name", "")
                if (query_lower in key or 
                    query_lower in name.lower() or
                    any(query_lower in word for word in name.lower().split())):
                    
                    # Convert back to original unit price for display
                    price_per_g = price_data.get("price_per_g", 0)
                    unit = price_data.get("unit", "kg")
                    
                    if unit.lower() in ("kg", "кг"):
                        price_per_unit = price_per_g * 1000
                    elif unit.lower() in ("l", "л"):
                        price_per_unit = price_per_g * 1000  
                    else:
                        price_per_unit = price_per_g
                    
                    results.append({
                        "source": source_name,
                        "name": name,
                        "skuId": price_data.get("sku_id") or price_data.get("skuId"),
                        "unit": unit,
                        "price_per_unit": round(price_per_unit, 2),
                        "currency": price_data.get("currency", "RUB"),
                        "asOf": price_data.get("as_of") or price_data.get("asOf"),
                        "canonical_id": price_data.get("canonical_id")
                    })
        
        # Sort by priority: iiko > user > catalog > bootstrap > knowledge_base, then by name similarity
        def sort_key(item):
            source_priority = {"iiko": 0, "user": 1, "catalog": 2, "bootstrap": 3, "knowledge_base": 4}.get(item["source"], 5)
            name_similarity = 100 - fuzz.ratio(query_lower, item["name"].lower())
            return (source_priority, name_similarity)
        
        results.sort(key=sort_key)
        return results[:limit]

    def is_stale_price(self, asOf: str, days_threshold: int = 30) -> bool:
        """Check if price data is stale (older than threshold days)"""
        try:
            price_date = datetime.strptime(asOf, "%Y-%m-%d")
            threshold_date = datetime.now() - timedelta(days=days_threshold)
            return price_date < threshold_date
        except (ValueError, TypeError):
            return True  # Assume stale if can't parse date