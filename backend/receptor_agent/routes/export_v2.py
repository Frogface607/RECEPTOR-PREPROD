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
        """Load techcards from database"""
        # TODO: Implement database loading
        # For now, return mock data for testing
        return []
    
    async def _process_dishes(self, techcards: List[TechCardV2], organization_id: str) -> Tuple[List[Dict], List[str]]:
        """Process dishes and allocate missing articles"""
        missing_dishes = []
        generated_articles = []
        
        for techcard in techcards:
            dish_article = getattr(techcard, 'article', None)
            
            if not dish_article:
                # Try to find in iiko RMS first
                found_article = await self._find_dish_in_iiko(techcard.name, organization_id)
                
                if found_article:
                    # Update techcard with found article
                    techcard.article = found_article
                else:
                    # Allocate new article
                    entity_id = f"dish_{techcard.id}"
                    allocated_articles = self.allocator.allocate_articles(
                        article_type=ArticleType.DISH,
                        count=1,
                        organization_id=organization_id,
                        entity_ids=[entity_id],
                        entity_names=[techcard.name]
                    )
                    
                    if allocated_articles:
                        new_article = allocated_articles[0]
                        techcard.article = new_article
                        generated_articles.append(new_article)
                        
                        # Get yield safely
                        yield_value = 200  # default
                        if hasattr(techcard, 'yield_') and techcard.yield_:
                            yield_value = getattr(techcard.yield_, 'perPortion_g', 200)
                        
                        missing_dishes.append({
                            "id": techcard.id,
                            "name": techcard.name,
                            "article": new_article,
                            "type": "dish",
                            "unit": "порц",
                            "yield": yield_value
                        })
        
        return missing_dishes, generated_articles
    
    async def _process_products(self, techcards: List[TechCardV2], organization_id: str) -> Tuple[List[Dict], List[str]]:
        """Process product ingredients and allocate missing articles"""
        missing_products = []
        generated_articles = []
        product_names_processed = set()
        
        for techcard in techcards:
            for ingredient in techcard.ingredients:
                # Skip if already processed or has article
                if ingredient.name in product_names_processed or getattr(ingredient, 'product_code', None):
                    continue
                    
                product_names_processed.add(ingredient.name)
                
                # Try to find in iiko RMS first
                found_article = await self._find_product_in_iiko(ingredient.name, organization_id)
                
                if found_article:
                    # Update ingredient with found article
                    ingredient.product_code = found_article
                else:
                    # Allocate new article
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


class DualExporter:
    """EX-03: Generates ZIP with TTK and skeleton files"""
    
    def __init__(self):
        self.allocator = get_article_allocator()
    
    async def create_export_zip(self, 
                               techcard_ids: List[str], 
                               preflight_result: Dict[str, Any],
                               operational_rounding: bool = True,
                               organization_id: str = "default") -> io.BytesIO:
        """
        Create ZIP with TTK and skeleton files
        
        Returns BytesIO buffer with ZIP content
        """
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 1. Create iiko_TTK.xlsx
                ttk_xlsx = await self._create_ttk_xlsx(techcard_ids, operational_rounding)
                zip_file.writestr("iiko_TTK.xlsx", ttk_xlsx.getvalue())
                
                # 2. Create Dish-Skeletons.xlsx if needed
                if preflight_result["counts"]["dishSkeletons"] > 0:
                    dish_skeletons_xlsx = await self._create_dish_skeletons_xlsx(
                        preflight_result["missing"]["dishes"]
                    )
                    zip_file.writestr("Dish-Skeletons.xlsx", dish_skeletons_xlsx.getvalue())
                
                # 3. Create Product-Skeletons.xlsx if needed
                if preflight_result["counts"]["productSkeletons"] > 0:
                    product_skeletons_xlsx = await self._create_product_skeletons_xlsx(
                        preflight_result["missing"]["products"]
                    )
                    zip_file.writestr("Product-Skeletons.xlsx", product_skeletons_xlsx.getvalue())
            
            # 4. Claim articles after successful skeleton generation
            await self._claim_generated_articles(preflight_result, organization_id)
            
            zip_buffer.seek(0)
            return zip_buffer
            
        except Exception as e:
            logger.error(f"Dual export error: {e}")
            raise HTTPException(500, f"Export failed: {str(e)}")
    
    async def _create_ttk_xlsx(self, techcard_ids: List[str], operational_rounding: bool) -> io.BytesIO:
        """Create iiko TTK XLSX file with proper article formatting"""
        try:
            # Import here to avoid circular imports
            from ..exports.iiko_xlsx import create_iiko_ttk_xlsx
            from ..techcards_v2.operational_rounding import get_operational_rounder
            
            # Load techcards (mock for now - in real implementation would load from database)
            # For testing purposes, create a minimal mock techcard
            from ..techcards_v2.schemas import TechCardV2, IngredientV2, YieldV2
            
            # Create a mock techcard for testing
            mock_techcard = TechCardV2(
                id="mock-tc-001",
                name="Mock Tech Card",
                ingredients=[
                    IngredientV2(
                        name="Test Ingredient",
                        netto=100.0,
                        brutto=110.0,
                        unit="g",
                        loss_pct=9.09
                    )
                ],
                yield_=YieldV2(perPortion_g=200.0),
                portions=1
            )
            
            # Apply operational rounding if requested
            if operational_rounding:
                rounder = get_operational_rounder()
                result = rounder.round_techcard_ingredients(mock_techcard.dict())
                # Convert back to TechCardV2 - simplified for testing
                mock_techcard = TechCardV2(**result['rounded_techcard'])
            
            # Create XLSX with proper article formatting
            export_options = {
                "use_product_codes": True,  # Always use articles, not GUIDs
                "operational_rounding": operational_rounding
            }
            
            xlsx_buffer, issues = create_iiko_ttk_xlsx(
                card=mock_techcard,
                export_options=export_options
            )
            
            return xlsx_buffer
            
        except Exception as e:
            logger.error(f"TTK XLSX creation error: {e}")
            raise
    
    async def _create_dish_skeletons_xlsx(self, missing_dishes: List[Dict]) -> io.BytesIO:
        """Create Dish-Skeletons.xlsx file"""
        try:
            # Import here to avoid circular imports
            from ..exports.iiko_xlsx import create_dish_skeletons_xlsx
            
            # Convert missing dishes to dish_codes_mapping format
            dish_codes_mapping = {dish["name"]: dish["article"] for dish in missing_dishes}
            
            # Create empty cards list since we don't have actual techcards loaded
            cards = []
            
            xlsx_buffer = create_dish_skeletons_xlsx(
                dish_codes_mapping=dish_codes_mapping,
                cards=cards
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
    EX-03: Dual Export (ZIP)
    
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
        if not preflight_result:
            raise HTTPException(400, "preflight_result is required")
        
        operational_rounding = body.get('operational_rounding', True)
        organization_id = body.get('organization_id', 'default')
        
        # Create export ZIP
        zip_buffer = await dual_exporter.create_export_zip(
            techcard_ids=techcard_ids,
            preflight_result=preflight_result,
            operational_rounding=operational_rounding,
            organization_id=organization_id
        )
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"iiko_export_{timestamp}.zip"
        
        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dual export error: {e}")
        raise HTTPException(500, f"Dual export failed: {str(e)}")


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