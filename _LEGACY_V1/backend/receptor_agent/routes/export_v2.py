"""
Phase 2: Preflight + Dual Export (ZIP) Routes
PF-02: Preflight Orchestrator
EX-03: Dual Export (ZIP)
"""

import io
import json
import os
import logging
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from receptor_agent.techcards_v2.schemas import TechCardV2
from receptor_agent.integrations.article_allocator import get_article_allocator, ArticleType

router = APIRouter()
logger = logging.getLogger(__name__)


class PreflightOrchestrator:
    """PF-02: Orchestrates article allocation and TTK date resolution"""
    
    def __init__(self):
        self.allocator = get_article_allocator()
        
    async def run_preflight(self, techcard_ids: List[str], organization_id: str = "default") -> Dict[str, Any]:
        """
        Run comprehensive preflight check and article allocation
        
        Returns:
        {
            "ttkDate": "YYYY-MM-DD",
            "missing": {"dishes": [...], "products": [...]},
            "generated": {"dishArticles": [...], "productArticles": [...]},
            "counts": {"dishSkeletons": 1, "productSkeletons": 2}
        }
        """
        try:
            # Load techcards from database
            techcards = await self._load_techcards(techcard_ids)
            
            # Check and allocate missing dish articles
            missing_dishes, generated_dish_articles = await self._process_dishes(techcards, organization_id)
            
            # Check and allocate missing product articles
            missing_products, generated_product_articles = await self._process_products(techcards, organization_id)
            
            # Resolve TTK date conflicts
            ttk_date = await self._resolve_ttk_date(organization_id)
            
            return {
                "ttkDate": ttk_date,
                "missing": {
                    "dishes": missing_dishes,
                    "products": missing_products
                },
                "generated": {
                    "dishArticles": generated_dish_articles,
                    "productArticles": generated_product_articles
                },
                "counts": {
                    "dishSkeletons": len(missing_dishes),
                    "productSkeletons": len(missing_products)
                }
            }
            
        except Exception as e:
            logger.error(f"Preflight orchestration error: {e}")
            raise HTTPException(500, f"Preflight failed: {str(e)}")
    
    async def _load_techcards(self, techcard_ids: List[str]) -> List[TechCardV2]:
        """
        Phase 3.5: Load techcards from database
        
        For frontend integration, if techcard_ids contains 'current',
        this indicates we should use the current techcard in session.
        Otherwise, load specific techcards by ID.
        """
        try:
            # Import here to avoid circular imports
            import os
            from motor.motor_asyncio import AsyncIOMotorClient
            
            # Get MongoDB connection (same pattern as server.py)
            mongo_url = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
            db_name = os.environ.get('DB_NAME', 'receptor_pro')
            
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name.strip('"')]
            techcards_collection = db.user_history  # Техkарты сохраняются в user_history
            
            techcards = []
            
            # Load specific techcards by ID
            for techcard_id in techcard_ids:
                    try:
                        # Search in user_history format (id field)
                        doc = await techcards_collection.find_one({"id": techcard_id})
                        
                        if doc:
                            # Load from user_history format
                            if 'techcard_v2_data' in doc and doc['techcard_v2_data']:
                                # New format with V2 data
                                techcard = TechCardV2(**doc['techcard_v2_data'])
                            elif 'content' in doc and doc['content']:
                                # Old format - try to parse JSON
                                try:
                                    import json
                                    content_data = json.loads(doc['content'])
                                    techcard = TechCardV2(**content_data)
                                except:
                                    logger.warning(f"Cannot parse techcard content for {techcard_id}")
                                    continue
                            else:
                                logger.warning(f"No valid techcard data for {techcard_id}")
                                continue
                                
                            techcards.append(techcard)
                            logger.info(f"Loaded techcard from user_history: {techcard_id}")
                        else:
                            logger.warning(f"Techcard not found: {techcard_id}")
                            # Don't create mock data - return empty list instead
                    except Exception as e:
                        logger.error(f"Error loading techcard {techcard_id}: {e}")
                        # Don't create mock data - continue to next techcard
            
            client.close()
            return techcards
            
        except Exception as e:
            logger.error(f"Error loading techcards: {e}")
            # Return empty list instead of mock data
            return []
    
    
    async def _process_dishes(self, techcards: List[TechCardV2], organization_id: str) -> Tuple[List[Dict], List[str]]:
        """
        Phase 3.5: Process dishes with RMS existence check
        
        Logic:
        1. For each techcard: if dish.article is empty OR doesn't exist in RMS
        2. Try to find in iiko RMS first (by name)
        3. If not found, allocate new article via AA-01
        4. Add to Dish-Skeletons for export
        """
        missing_dishes = []
        generated_articles = []
        
        for techcard in techcards:
            # V2 techcards store article in meta.article, not techcard.article
            dish_article = getattr(techcard.meta, 'article', None)
            needs_skeleton = False
            
            logger.info(f"🔍 Processing dish: '{techcard.meta.title}', article: '{dish_article}'")
            
            if not dish_article:
                # Case 1: No article at all
                needs_skeleton = True
                logger.info(f"✅ Dish '{techcard.meta.title}' has no article - needs skeleton")
            else:
                # Case 2: Has article but check if it exists in RMS
                logger.info(f"🔍 Checking if article '{dish_article}' exists in RMS...")
                article_exists = await self._check_dish_article_in_rms(dish_article, organization_id)
                logger.info(f"🔍 Article '{dish_article}' exists in RMS: {article_exists}")
                if not article_exists:
                    needs_skeleton = True
                    logger.info(f"✅ Dish '{techcard.meta.title}' article '{dish_article}' not found in RMS - needs skeleton")
                else:
                    logger.info(f"ℹ️ Dish '{techcard.meta.title}' article '{dish_article}' found in RMS - no skeleton needed")
            
            if needs_skeleton:
                # Try to find by name in iiko RMS first
                found_article = await self._find_dish_in_iiko(techcard.meta.title, organization_id)
                
                if found_article:
                    # Update techcard with found article
                    techcard.meta.article = found_article
                    logger.info(f"Found existing dish '{techcard.meta.title}' in RMS with article '{found_article}'")
                else:
                    # Allocate new article via AA-01
                    entity_id = f"dish_{getattr(techcard, 'id', techcard.meta.title.replace(' ', '_'))}"
                    allocated_articles = self.allocator.allocate_articles(
                        article_type=ArticleType.DISH,
                        count=1,
                        organization_id=organization_id,
                        entity_ids=[entity_id],
                        entity_names=[techcard.meta.title]
                    )
                    
                    if allocated_articles:
                        new_article = allocated_articles[0]
                        techcard.meta.article = new_article
                        generated_articles.append(new_article)
                        
                        # Get yield safely
                        yield_value = 200  # default
                        if hasattr(techcard, 'yield_') and techcard.yield_:
                            yield_value = getattr(techcard.yield_, 'perPortion_g', 200)
                        
                        missing_dishes.append({
                            "id": getattr(techcard, 'id', entity_id),
                            "name": techcard.meta.title,
                            "article": new_article,
                            "type": "dish",
                            "unit": "порц",
                            "yield": yield_value
                        })
                        
                        logger.info(f"Generated new article '{new_article}' for dish '{techcard.meta.title}'")
        
        return missing_dishes, generated_articles
    
    async def _process_products(self, techcards: List[TechCardV2], organization_id: str) -> Tuple[List[Dict], List[str]]:
        """Process product ingredients and allocate missing articles"""
        missing_products = []
        generated_articles = []
        product_names_processed = set()
        
        for techcard in techcards:
            for ingredient in techcard.ingredients:
                # Skip if already processed
                if ingredient.name in product_names_processed:
                    continue
                    
                product_names_processed.add(ingredient.name)
                
                existing_code = getattr(ingredient, 'product_code', None)
                needs_mapping = True
                
                # If has existing code, check if it's generated (not real iiko code)
                if existing_code:
                    if self._is_generated_article(existing_code):
                        # Has generated code, try to find real iiko code
                        logger.info(f"Ingredient '{ingredient.name}' has generated code '{existing_code}', trying to find real iiko code")
                    else:
                        # Has real iiko code, skip
                        logger.info(f"Ingredient '{ingredient.name}' already has real iiko code '{existing_code}'")
                        needs_mapping = False
                
                if needs_mapping:
                    # Try to find in iiko RMS first
                    found_article = await self._find_product_in_iiko(ingredient.name, organization_id)
                    
                    if found_article:
                        # Update ingredient with found real article
                        ingredient.product_code = found_article
                        logger.info(f"Found real iiko article for '{ingredient.name}': {found_article}")
                    else:
                        # No real article found, generate new or keep existing generated
                        if not existing_code or not self._is_generated_article(existing_code):
                            # Allocate new generated article
                            entity_id = f"product_{ingredient.name.replace(' ', '_')}"
                            allocated_articles = self.allocator.allocate_articles(
                                article_type=ArticleType.PRODUCT,
                                count=1,
                                organization_id=organization_id,
                                entity_ids=[entity_id],
                                entity_names=[ingredient.name]
                            )
                            
                            if allocated_articles:
                                new_article = allocated_articles[0]
                                ingredient.product_code = new_article
                                generated_articles.append(new_article)
                                
                                missing_products.append({
                                    "id": entity_id,
                                    "name": ingredient.name,
                                    "article": new_article,
                                    "type": "product",
                                    "unit": ingredient.unit,
                                    "group": self._categorize_ingredient(ingredient.name)
                                })
                        else:
                            # Keep existing generated article and add to missing
                            generated_articles.append(existing_code)
                            entity_id = f"product_{ingredient.name.replace(' ', '_')}"
                            missing_products.append({
                                "id": entity_id,
                                "name": ingredient.name,
                                "article": existing_code,
                                "type": "product",
                                "unit": ingredient.unit,
                                "group": self._categorize_ingredient(ingredient.name)
                            })
                            logger.info(f"Ingredient '{ingredient.name}' keeps generated article '{existing_code}' -> missing products")
        
        return missing_products, generated_articles
    
    async def _find_dish_in_iiko(self, dish_name: str, organization_id: str) -> Optional[str]:
        """Try to find dish article in iiko RMS"""
        try:
            # Import here to avoid circular imports
            from ..exports.iiko_xlsx import find_dish_in_iiko_rms
            from ..integrations.iiko_rms_service import get_iiko_rms_service
            
            rms_service = get_iiko_rms_service()
            result = find_dish_in_iiko_rms(dish_name, rms_service)
            
            if result and len(result) > 0:
                # Return the first match's article
                return result[0].get('article')
            
        except Exception as e:
            logger.warning(f"Error finding dish in iiko: {e}")
        
        return None
    
    async def _check_dish_article_in_rms(self, article: str, organization_id: str) -> bool:
        """
        Phase 3.5: Check if dish article exists in iiko RMS
        
        Returns True if article exists, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from ..integrations.iiko_rms_service import get_iiko_rms_service
            
            rms_service = get_iiko_rms_service()
            
            # Search for dish by article (exact match on num field)
            dish = rms_service.products.find_one({
                "organization_id": organization_id,
                "num": article,  # Use num field (true article) not code
                "product_type": {"$in": ["DISH", "dish"]}  # Only dishes
            })
            
            exists = dish is not None
            logger.info(f"Article '{article}' exists in RMS: {exists}")
            return exists
            
        except Exception as e:
            logger.warning(f"Error checking dish article in RMS: {e}")
            # If we can't check, assume it doesn't exist (safer)
            return False
    
    async def _find_product_in_iiko(self, product_name: str, organization_id: str) -> Optional[str]:
        """Try to find product article in iiko RMS"""
        try:
            # Import here to avoid circular imports  
            from ..exports.iiko_xlsx import get_product_code_from_rms
            from ..integrations.iiko_rms_service import get_iiko_rms_service
            
            rms_service = get_iiko_rms_service()
            
            # Search by name in products collection
            product = rms_service.products.find_one({
                "organization_id": organization_id,
                "name": {"$regex": product_name, "$options": "i"}
            })
            
            if product:
                article = get_product_code_from_rms(product.get('_id'), rms_service)
                return article
            
        except Exception as e:
            logger.warning(f"Error finding product in iiko: {e}")
        
        return None
    
    async def _resolve_ttk_date(self, organization_id: str) -> str:
        """Resolve TTK date conflicts by shifting +1 to +7 days if needed"""
        try:
            # Import here to avoid circular imports
            from ..exports.iiko_xlsx import resolve_ttk_date_conflict
            
            base_date = datetime.now().date()
            resolved_date = resolve_ttk_date_conflict(base_date, organization_id)
            
            return resolved_date.isoformat()
            
        except Exception as e:
            logger.warning(f"Error resolving TTK date: {e}")
            # Fallback to today
            return datetime.now().date().isoformat()
    
    def _categorize_ingredient(self, ingredient_name: str) -> str:
        """Categorize ingredient for proper iiko group assignment"""
        name_lower = ingredient_name.lower()
        
        # Meat and fish
        if any(word in name_lower for word in ['мясо', 'говядина', 'свинина', 'курица', 'рыба', 'филе', 'фарш']):
            return 'Мясо и рыба'
        
        # Dairy
        if any(word in name_lower for word in ['молоко', 'сметана', 'творог', 'сыр', 'масло', 'йогурт']):
            return 'Молочные продукты'
        
        # Vegetables
        if any(word in name_lower for word in ['картофель', 'морковь', 'лук', 'помидор', 'огурец', 'капуста', 'свекла']):
            return 'Овощи'
        
        # Grocery
        if any(word in name_lower for word in ['мука', 'сахар', 'соль', 'перец', 'специи', 'крупа', 'рис']):
            return 'Бакалея'
        
        # Oils and sauces
        if any(word in name_lower for word in ['масло', 'соус', 'уксус', 'майонез']):
            return 'Масла и соусы'
        
        # Default
        return 'Сырьё'
    
    def _is_generated_article(self, article_code: str) -> bool:
        """
        Check if article code is generated by our ArticleAllocator (not real iiko code)
        
        Generated articles have patterns:
        - Numeric strings (e.g., "10000", "10001", "100015") 
        - Start with '1' followed by zeros, then increment
        - Width typically 5-6 digits
        
        Real iiko codes can be:
        - Non-numeric (e.g., "BEEF-001", "VEG_TOMATO")
        - Mixed alphanumeric
        """
        if not article_code or not isinstance(article_code, str):
            return False
        
        try:
            # Check if it's purely numeric
            article_int = int(article_code)
            
            # Generated articles typically start from 10000 (width=5) or 100000 (width=6)
            # and are sequential integers
            if 10000 <= article_int <= 999999:  # Covers width 5 and 6
                return True
            elif 1000 <= article_int <= 9999:  # Also width 4 just in case
                return True
            elif 1 <= article_int <= 999:  # And smaller widths
                return True
                
        except (ValueError, TypeError):
            # Non-numeric codes are real iiko codes
            pass
        
        return False


class DualExporter:
    """EX-03: Generates ZIP with TTK and skeleton files"""
    
    def __init__(self):
        self.allocator = get_article_allocator()
    
    async def _load_techcards(self, techcard_ids: List[str]) -> List[TechCardV2]:
        """
        Load techcards from database
        
        For frontend integration, if techcard_ids contains 'current',
        this indicates we should use the current techcard in session.
        Otherwise, load specific techcards by ID.
        """
        try:
            # Import here to avoid circular imports
            import os
            from pymongo import MongoClient
            
            # Get MongoDB connection (same pattern as iiko_rms_service)
            mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
            db_name = os.getenv('DB_NAME', 'receptor_pro')
            
            client = MongoClient(mongo_url)
            db = client[db_name.strip('"')]
            techcards_collection = db.user_history  # Техkарты сохраняются в user_history
            
            techcards = []
            
            # Load specific techcards by ID
            for techcard_id in techcard_ids:
                    try:
                        # Search in user_history format (id field)
                        doc = await techcards_collection.find_one({"id": techcard_id})
                        
                        if doc:
                            # Load from user_history format
                            if 'techcard_v2_data' in doc and doc['techcard_v2_data']:
                                # New format with V2 data
                                techcard = TechCardV2(**doc['techcard_v2_data'])
                            elif 'content' in doc and doc['content']:
                                # Old format - try to parse JSON
                                try:
                                    import json
                                    content_data = json.loads(doc['content'])
                                    techcard = TechCardV2(**content_data)
                                except:
                                    logger.warning(f"Cannot parse techcard content for {techcard_id}")
                                    continue
                            else:
                                logger.warning(f"No valid techcard data for {techcard_id}")
                                continue
                                
                            techcards.append(techcard)
                            logger.info(f"Loaded techcard from user_history: {techcard_id}")
                        else:
                            logger.warning(f"Techcard not found: {techcard_id}")
                            # Don't create mock data - return empty list instead
                    except Exception as e:
                        logger.error(f"Error loading techcard {techcard_id}: {e}")
                        # Don't create mock data - continue to next techcard
            
            client.close()
            return techcards
            
        except Exception as e:
            logger.error(f"Error loading techcards: {e}")
            # Return empty list instead of mock data
            return []
    

    async def create_export_zip(self, 
                               techcard_ids: List[str], 
                               preflight_result: Dict[str, Any],
                               operational_rounding: bool = True,
                               organization_id: str = "default") -> io.BytesIO:
        """
        REMOVE INVALID TECH CARD FROM ZIP: Create ZIP with ONLY skeleton files
        
        According to requirements, ZIP should contain ONLY:
        - Dish-Skeletons.xlsx (if dishes missing)
        - Product-Skeletons.xlsx (if products missing)
        
        NO invalid/empty tech cards (iiko_TTK.xlsx removed)
        
        Returns BytesIO buffer with ZIP content
        """
        try:
            zip_buffer = io.BytesIO()
            
            # FIX: Safely extract preflight data with fallback
            missing_dishes = preflight_result.get("missing", {}).get("dishes", []) or preflight_result.get("missing_dishes", [])
            missing_products = preflight_result.get("missing", {}).get("products", []) or preflight_result.get("missing_products", [])
            
            dish_skeletons_count = preflight_result.get("counts", {}).get("dishSkeletons", 0) or len(missing_dishes)
            product_skeletons_count = preflight_result.get("counts", {}).get("productSkeletons", 0) or len(missing_products)
            
            logger.info(f"🔍 Export ZIP - Dishes: {dish_skeletons_count}, Products: {product_skeletons_count}")
            logger.info(f"🔍 Export ZIP - Missing dishes: {len(missing_dishes)}, Missing products: {len(missing_products)}")
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # REMOVED: iiko_TTK.xlsx (invalid/empty tech card)
                # OLD: ttk_xlsx = await self._create_ttk_xlsx(techcard_ids, operational_rounding, preflight_result)
                # OLD: zip_file.writestr("iiko_TTK.xlsx", ttk_xlsx.getvalue())
                
                # 1. Create Dish-Skeletons.xlsx ONLY if dishes missing
                if dish_skeletons_count > 0 and missing_dishes:
                    try:
                        dish_skeletons_xlsx = await self._create_dish_skeletons_xlsx(missing_dishes)
                        
                        # Create dynamic filename with dish names
                        dish_names = [dish.get("name", dish.get("dish_name", "Unknown")) for dish in missing_dishes]
                        safe_dish_names = [name.replace(" ", "_").replace("/", "_") for name in dish_names if name]
                        dish_filename = f"Dish-Skeletons_{'_'.join(safe_dish_names[:2])}.xlsx"  # Max 2 names
                        if len(safe_dish_names) > 2:
                            dish_filename = f"Dish-Skeletons_{len(dish_names)}_dishes.xlsx"
                        
                        zip_file.writestr(dish_filename, dish_skeletons_xlsx.getvalue())
                        logger.info(f"✅ Added {dish_filename} with {dish_skeletons_count} dishes")
                    except Exception as e:
                        logger.error(f"❌ Failed to create dish skeletons: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                
                # 2. Create Product-Skeletons.xlsx ONLY if products missing
                if product_skeletons_count > 0 and missing_products:
                    try:
                        product_skeletons_xlsx = await self._create_product_skeletons_xlsx(missing_products)
                        
                        # Create dynamic filename with product count
                        product_filename = f"Product-Skeletons_{product_skeletons_count}_products.xlsx"
                        
                        zip_file.writestr(product_filename, product_skeletons_xlsx.getvalue())
                        logger.info(f"✅ Added {product_filename} with {product_skeletons_count} products")
                    except Exception as e:
                        logger.error(f"❌ Failed to create product skeletons: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                
                # 3. Verify ZIP contains only valid skeleton files
                files_in_zip = list(zip_file.namelist())
                valid_files = [f for f in files_in_zip if f.startswith("Dish-Skeletons_") or f.startswith("Product-Skeletons_")]
                
                logger.info(f"📦 ZIP export complete: {len(valid_files)} valid skeleton files created")
                logger.info(f"📦 Files in ZIP: {files_in_zip}")
                
                # 4. Ensure ZIP is not empty (at least one skeleton file should be present)
                if not files_in_zip:
                    logger.warning("⚠️ ZIP export created empty archive - no skeleton files needed")
                    # FIX: If ZIP is empty but we have dishes, create at least dish skeletons
                    if missing_dishes:
                        logger.warning("⚠️ Creating dish skeletons even though preflight said none needed")
                        try:
                            dish_skeletons_xlsx = await self._create_dish_skeletons_xlsx(missing_dishes)
                            dish_filename = f"Dish-Skeletons_{len(missing_dishes)}_dishes.xlsx"
                            zip_file.writestr(dish_filename, dish_skeletons_xlsx.getvalue())
                            logger.info(f"✅ Created fallback {dish_filename}")
                        except Exception as e:
                            logger.error(f"❌ Failed to create fallback dish skeletons: {e}")
            
            # 5. Claim articles after successful skeleton generation
            await self._claim_generated_articles(preflight_result, organization_id)
            
            zip_buffer.seek(0)
            return zip_buffer
            
        except Exception as e:
            logger.error(f"Dual export error: {e}")
            raise HTTPException(500, f"Export failed: {str(e)}")
    
    async def _create_ttk_xlsx(self, techcard_ids: List[str], operational_rounding: bool, preflight_result: Dict[str, Any] = None) -> io.BytesIO:
        """Create iiko TTK XLSX file with proper article formatting using preflight articles"""
        try:
            # Import here to avoid circular imports
            from ..exports.iiko_xlsx import create_iiko_ttk_xlsx
            from ..techcards_v2.operational_rounding import get_operational_rounder
            
            # Load real techcards from database
            techcards = await self._load_techcards(techcard_ids)
            
            if not techcards:
                raise HTTPException(status_code=404, detail="No techcards found for the provided IDs")
            
            # Use the first techcard for TTK-only export
            techcard = techcards[0]
            
            # Apply operational rounding if requested
            if operational_rounding:
                rounder = get_operational_rounder()
                result = rounder.round_techcard_ingredients(techcard.dict())
                # Convert back to TechCardV2
                techcard = TechCardV2(**result['rounded_techcard'])
            
            # Create export options with preflight article mapping
            export_options = {
                "use_product_codes": True,
                "operational_rounding": operational_rounding
            }
            
            # Pass preflight data to XLSX generator if available
            if preflight_result:
                export_options["preflight_result"] = preflight_result
            
            xlsx_buffer, issues = create_iiko_ttk_xlsx(
                card=techcard,
                export_options=export_options
            )
            
            return xlsx_buffer
            
        except Exception as e:
            logger.error(f"TTK XLSX creation error: {e}")
            raise
    
    async def _create_dish_skeletons_xlsx(self, missing_dishes: List[Dict]) -> io.BytesIO:
        """Create Dish-Skeletons.xlsx file with actual dish data"""
        try:
            # Import here to avoid circular imports
            from ..exports.iiko_xlsx import create_dish_skeletons_xlsx
            
            # Convert missing dishes to dish_codes_mapping format
            dish_codes_mapping = {dish["name"]: dish["article"] for dish in missing_dishes}
            
            # Create dish data directly from missing_dishes instead of requiring techcards
            dishes_data = []
            for dish in missing_dishes:
                dish_data = {
                    "name": dish["name"],
                    "article": dish["article"], 
                    "type": dish.get("type", "блюдо"),
                    "unit": dish.get("unit", "порц."),
                    "yield_g": dish.get("yield", 200.0)
                }
                dishes_data.append(dish_data)
            
            xlsx_buffer = create_dish_skeletons_xlsx(
                dish_codes_mapping=dish_codes_mapping,
                dishes_data=dishes_data  # Pass dish data instead of empty cards
            )
            
            return xlsx_buffer
            
        except Exception as e:
            logger.error(f"Dish skeletons XLSX creation error: {e}")
            raise
    
    async def _create_product_skeletons_xlsx(self, missing_products: List[Dict]) -> io.BytesIO:
        """Create Product-Skeletons.xlsx file"""
        try:
            # Import here to avoid circular imports
            from ..exports.iiko_xlsx import create_product_skeletons_xlsx
            
            xlsx_buffer = create_product_skeletons_xlsx(
                missing_ingredients=missing_products,
                generated_codes={p["name"]: p["article"] for p in missing_products}
            )
            
            return xlsx_buffer
            
        except Exception as e:
            logger.error(f"Product skeletons XLSX creation error: {e}")
            raise
    
    async def _claim_generated_articles(self, preflight_result: Dict[str, Any], organization_id: str):
        """Claim all generated articles to make them permanent"""
        try:
            all_articles = (
                preflight_result["generated"]["dishArticles"] + 
                preflight_result["generated"]["productArticles"]
            )
            
            if all_articles:
                claim_results = self.allocator.claim_articles(all_articles, organization_id)
                
                claimed_count = sum(1 for success in claim_results.values() if success)
                logger.info(f"Claimed {claimed_count}/{len(all_articles)} articles after skeleton generation")
                
        except Exception as e:
            logger.warning(f"Error claiming articles: {e}")


# Initialize services
preflight_orchestrator = PreflightOrchestrator()
dual_exporter = DualExporter()


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/export/preflight")
async def run_preflight_check(request: Request):
    """
    PF-02: Preflight Orchestrator
    
    Body:
    {
        "techcardIds": ["tc-1", "tc-2"],
        "organization_id": "org-123"  // Optional
    }
    
    Returns:
    {
        "ttkDate": "2024-01-15",
        "missing": {
            "dishes": [{"id": "...", "name": "...", "article": "10001"}],
            "products": [{"id": "...", "name": "...", "article": "20001"}]
        },
        "generated": {
            "dishArticles": ["10001"],
            "productArticles": ["20001", "20002"]
        },
        "counts": {
            "dishSkeletons": 1,
            "productSkeletons": 2
        }
    }
    """
    try:
        body = await request.json()
        
        techcard_ids = body.get('techcardIds', [])
        if not techcard_ids:
            raise HTTPException(400, "techcardIds list is required")
        
        organization_id = body.get('organization_id', 'default')
        
        # Run preflight orchestration
        result = await preflight_orchestrator.run_preflight(techcard_ids, organization_id)
        
        return {
            "status": "success",
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preflight check error: {e}")
        raise HTTPException(500, f"Preflight check failed: {str(e)}")


@router.post("/export/zip")
async def create_dual_export_zip(request: Request):
    """
    EX-03: Dual Export (ZIP) with Guard — dish-first rule
    
    Body:
    {
        "techcardIds": ["tc-1", "tc-2"],
        "operational_rounding": true,
        "organization_id": "org-123",  // Optional
        "preflight_result": {...}      // Result from preflight endpoint
    }
    
    Returns:
        ZIP file containing:
        - iiko_TTK.xlsx (always)
        - Dish-Skeletons.xlsx (if dishes missing)
        - Product-Skeletons.xlsx (if products missing)
    """
    try:
        body = await request.json()
        
        techcard_ids = body.get('techcardIds', [])
        if not techcard_ids:
            raise HTTPException(400, "techcardIds list is required")
        
        preflight_result = body.get('preflight_result')
        organization_id = body.get('organization_id', 'default')
        
        # DEBUG: Log received data
        logger.info(f"🔍 ZIP Export - Received techcard_ids: {techcard_ids}")
        logger.info(f"🔍 ZIP Export - Preflight result present: {bool(preflight_result)}")
        if preflight_result:
            # FIX: Safely extract missing dishes/products with fallback
            missing_dishes = preflight_result.get("missing", {}).get("dishes", []) or preflight_result.get("missing_dishes", [])
            missing_products = preflight_result.get("missing", {}).get("products", []) or preflight_result.get("missing_products", [])
            dish_count = preflight_result.get("counts", {}).get("dishSkeletons", 0) or len(missing_dishes)
            product_count = preflight_result.get("counts", {}).get("productSkeletons", 0) or len(missing_products)
            
            logger.info(f"🔍 ZIP Export - Missing dishes: {len(missing_dishes)} (count: {dish_count})")
            logger.info(f"🔍 ZIP Export - Missing products: {len(missing_products)} (count: {product_count})")
        
        # Guard — dish-first rule: Check if preflight was bypassed with missing dishes
        if not preflight_result:
            # No preflight provided - run our own check for guard validation
            logger.warning("ZIP export called without preflight_result - running guard check")
            guard_result = await preflight_orchestrator.run_preflight(techcard_ids, organization_id)
            
            if guard_result["counts"]["dishSkeletons"] > 0:
                # Guard triggered: dishes missing from RMS, cannot export TTK without skeletons
                missing_dishes = guard_result["missing"]["dishes"]
                raise HTTPException(400, {
                    "error": "PRE_FLIGHT_REQUIRED",
                    "message": "Нельзя экспортировать ТК без создания блюд в iiko. Сначала импортируйте скелеты блюд.",
                    "missing_dishes": missing_dishes,
                    "dish_count": len(missing_dishes),
                    "required_action": "import_dish_skeletons_first",
                    "preflight_result": guard_result
                })
            else:
                # No dishes missing, use guard result as preflight
                preflight_result = guard_result
        
        # Additional guard: Validate preflight result has dish skeleton info
        if preflight_result["counts"]["dishSkeletons"] > 0:
            logger.info(f"ZIP export proceeding with {preflight_result['counts']['dishSkeletons']} dish skeletons")
        
        operational_rounding = body.get('operational_rounding', True)
        
        # Create export ZIP
        zip_buffer = await dual_exporter.create_export_zip(
            techcard_ids=techcard_ids,
            preflight_result=preflight_result,
            operational_rounding=operational_rounding,
            organization_id=organization_id
        )
        
        # ALT Export Cleanup: Автоматическая очистка архива
        from ..exports.alt_export_cleanup import get_alt_export_validator
        
        validator = get_alt_export_validator()
        clean_zip_buffer, cleanup_stats = validator.cleanup_archive(
            zip_buffer, 
            context=f"zip_export_{len(techcard_ids)}_cards"
        )
        
        if cleanup_stats["cleaned"]:
            logger.info(f"ALT Cleanup applied: {cleanup_stats}")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"iiko_export_{timestamp}.zip"
        
        return StreamingResponse(
            iter([clean_zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dual export error: {e}")
        raise HTTPException(500, f"Dual export failed: {str(e)}")


@router.post("/export/ttk-only") 
async def create_ttk_only_export(request: Request):
    """
    Guard — dish-first rule: TTK-only export with strict dish validation
    
    This endpoint enforces the dish-first rule by blocking TTK-only exports
    when dishes don't exist in iiko RMS nomenclature.
    
    Body:
    {
        "techcardIds": ["tc-1", "tc-2"],
        "operational_rounding": true,
        "organization_id": "org-123"
    }
    
    Returns:
        - iiko_TTK.xlsx file if all dishes exist in RMS
        - PRE_FLIGHT_REQUIRED error if dishes missing
    """
    try:
        body = await request.json()
        
        techcard_ids = body.get('techcardIds', [])
        if not techcard_ids:
            raise HTTPException(400, "techcardIds list is required")
        
        organization_id = body.get('organization_id', 'default')
        operational_rounding = body.get('operational_rounding', True)
        
        # Guard — dish-first rule: Always run preflight check for TTK-only exports
        logger.info("TTK-only export requested - running dish guard validation")
        preflight_result = await preflight_orchestrator.run_preflight(techcard_ids, organization_id)
        
        # Strict guard: Block TTK-only export if any dishes missing
        if preflight_result["counts"]["dishSkeletons"] > 0:
            missing_dishes = preflight_result["missing"]["dishes"]
            
            logger.warning(f"TTK-only export blocked: {len(missing_dishes)} dishes missing from RMS")
            
            raise HTTPException(403, {
                "error": "PRE_FLIGHT_REQUIRED",
                "message": "Нельзя экспортировать только ТК - отсутствуют блюда в номенклатуре iiko",
                "details": "iiko отвергает ТК, если 'Артикул блюда' не существует в номенклатуре",
                "missing_dishes": missing_dishes,
                "dish_count": len(missing_dishes),
                "required_action": "import_dish_skeletons_first",
                "solution": "Используйте ZIP экспорт для получения скелетов блюд",
                "preflight_result": preflight_result
            })
        
        # Guard passed: All dishes exist, create TTK-only file
        logger.info("Dish guard passed - creating TTK-only export")
        
        ttk_xlsx = await dual_exporter._create_ttk_xlsx(techcard_ids, operational_rounding)
        
        # ALT Export Cleanup: Валидация TTK файла
        from ..exports.alt_export_cleanup import get_alt_export_validator
        
        validator = get_alt_export_validator()
        ttk_content = ttk_xlsx.getvalue()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"iiko_TTK_{timestamp}.xlsx"
        
        validation_result = validator.validate_single_ttk(
            ttk_content,
            filename=filename
        )
        
        if not validation_result["valid"]:
            logger.warning(f"TTK-only export validation issues: {validation_result['issues']}")
            # Логируем, но не блокируем (может быть legacy данные)
        else:
            logger.info(f"TTK-only export validation passed: {validation_result['metadata']}")
        
        return StreamingResponse(
            iter([ttk_xlsx.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTK-only export error: {e}")
        raise HTTPException(500, f"TTK-only export failed: {str(e)}")


# ALT Export Cleanup: Admin endpoints для мониторинга и управления

@router.get("/export/cleanup/stats")
def get_cleanup_statistics():
    """
    Получить статистику ALT Export Cleanup
    
    Возвращает:
    - Количество обработанных архивов
    - Количество удаленных дублей, невалидных файлов, superfluous files
    - Общую статистику очистки
    """
    try:
        from ..exports.alt_export_cleanup import get_alt_export_validator
        
        validator = get_alt_export_validator()
        stats = validator.get_cleanup_statistics()
        
        return {
            "status": "success",
            "cleanup_statistics": stats,
            "message": "ALT Export Cleanup statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get cleanup statistics: {e}")
        raise HTTPException(500, f"Statistics retrieval failed: {str(e)}")


@router.post("/export/cleanup/audit")
async def admin_audit_archives():
    """
    Admin: Полный аудит архивов ALT Export
    
    Выполняет комплексную проверку и возвращает детальный отчет:
    - Найденные проблемы
    - Рекомендации по очистке
    - Статистика по типам проблем
    """
    try:
        from ..exports.alt_export_cleanup import get_alt_export_validator
        
        validator = get_alt_export_validator()
        audit_result = validator.admin_audit_archives()
        
        logger.info(f"ALT Export audit completed: {audit_result}")
        
        return {
            "status": "success",
            "audit_result": audit_result,
            "message": "Archive audit completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Archive audit failed: {e}")
        raise HTTPException(500, f"Audit failed: {str(e)}")


@router.post("/export/cleanup/reset-stats")
def reset_cleanup_statistics():
    """
    Admin: Сброс статистики ALT Export Cleanup
    """
    try:
        from ..exports.alt_export_cleanup import get_alt_export_validator
        
        validator = get_alt_export_validator()
        old_stats = validator.get_cleanup_statistics()
        validator.reset_statistics()
        
        logger.info("ALT Export cleanup statistics reset")
        
        return {
            "status": "success",
            "message": "Cleanup statistics reset successfully",
            "previous_stats": old_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to reset cleanup statistics: {e}")
        raise HTTPException(500, f"Statistics reset failed: {str(e)}")


@router.get("/export/status")
async def get_export_status():
    """Get export system status"""
    try:
        # Check ArticleAllocator availability
        allocator_status = "available"
        try:
            allocator = get_article_allocator()
            test_stats = allocator.get_allocation_stats("test")
            allocator_status = "operational"
        except Exception as e:
            allocator_status = f"error: {str(e)}"
        
        return {
            "status": "success",
            "systems": {
                "preflight_orchestrator": "operational",
                "dual_exporter": "operational", 
                "article_allocator": allocator_status
            },
            "features": {
                "article_allocation": True,
                "ttk_date_resolution": True,
                "skeleton_generation": True,
                "zip_export": True,
                "article_claiming": True
            }
        }
        
    except Exception as e:
        logger.error(f"Export status error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }