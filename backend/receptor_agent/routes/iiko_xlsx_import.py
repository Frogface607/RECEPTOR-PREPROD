"""
IK-04/01: iiko XLSX Import API endpoints
Provides functionality to import iiko XLSX tech card templates and convert to TechCardV2
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from ..integrations.iiko_xlsx_parser import IikoXlsxParser, IikoXlsxParseError
from ..techcards_v2.schemas import TechCardV2, NutritionV2, CostV2

logger = logging.getLogger(__name__)

# Router for iiko XLSX import
router = APIRouter(prefix="/api/v1/iiko", tags=["iiko XLSX Import"])

# Response models
class IikoXlsxImportIssue(BaseModel):
    code: str = Field(description="Issue code")
    level: str = Field(description="Issue level: warning, error, info") 
    msg: str = Field(description="Issue message")

class IikoXlsxImportMeta(BaseModel):
    source: str = Field(default="iiko-xlsx", description="Import source")
    parsed_rows: int = Field(description="Number of rows parsed")
    filename: str = Field(default="import.xlsx", description="Original filename")

class IikoXlsxImportResponse(BaseModel):
    status: str = Field(description="Import status: success, draft")
    techcard: Dict[str, Any] = Field(description="Parsed TechCardV2 structure")
    issues: List[IikoXlsxImportIssue] = Field(default_factory=list, description="Parsing issues")
    meta: IikoXlsxImportMeta = Field(description="Import metadata")

@router.post("/import/ttk.xlsx", response_model=IikoXlsxImportResponse)
async def import_iiko_xlsx(
    file: UploadFile = File(..., description="iiko XLSX tech card template")
):
    """
    IK-04/01: Import iiko XLSX tech card template and convert to TechCardV2
    
    Supports both RU/EN headers with flexible column ordering.
    Normalizes units, calculates yield/portions, and preserves SKU codes.
    """
    try:
        logger.info(f"Starting XLSX import for file: {file.filename}")
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="File must be an XLSX format"
            )
        
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Parse XLSX to TechCardV2
        parser = IikoXlsxParser()
        parse_result = parser.parse_xlsx_to_techcard(file_content, file.filename)
        
        techcard_data = parse_result["techcard"]
        issues = parse_result["issues"]
        meta = parse_result["meta"]
        
        # Validate parsed TechCardV2 structure
        try:
            techcard = TechCardV2.model_validate(techcard_data)
        except Exception as validation_error:
            logger.error(f"TechCardV2 validation failed: {validation_error}")
            
            # Add validation issue
            issues.append({
                "code": "validationFailed",
                "level": "error",
                "msg": f"Структура техкарты не прошла валидацию: {str(validation_error)}"
            })
            
            # Return draft status with issues
            return IikoXlsxImportResponse(
                status="draft",
                techcard=techcard_data,
                issues=[IikoXlsxImportIssue(**issue) for issue in issues],
                meta=IikoXlsxImportMeta(**meta)
            )
        
        # Apply cost and nutrition calculations (recalc)
        try:
            from ..techcards_v2.cost_calculator import calculate_cost_for_tech_card
            from ..techcards_v2.nutrition_calculator import calculate_nutrition_for_tech_card
            
            # Calculate costs and nutrition (preserving skuId values)
            techcard = calculate_cost_for_tech_card(techcard, {})  # Empty sub_recipes_cache
            techcard = calculate_nutrition_for_tech_card(techcard, {})
            
            logger.info(f"✅ Recalculation completed for imported tech card")
            
        except Exception as calc_error:
            logger.warning(f"Recalculation failed: {calc_error}")
            issues.append({
                "code": "recalcFailed",
                "level": "warning", 
                "msg": f"Пересчёт стоимости/питания неуспешен: {str(calc_error)}"
            })
        
        # Determine final status
        has_critical_issues = any(issue.get("level") == "error" for issue in issues)
        final_status = "draft" if has_critical_issues else "success"
        
        logger.info(f"✅ XLSX import completed: {final_status}, {len(issues)} issues, {meta['parsed_rows']} rows")
        
        return IikoXlsxImportResponse(
            status=final_status,
            techcard=techcard.model_dump(by_alias=True),
            issues=[IikoXlsxImportIssue(**issue) for issue in issues],
            meta=IikoXlsxImportMeta(**meta)
        )
        
    except IikoXlsxParseError as e:
        logger.error(f"XLSX parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"XLSX parsing failed: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error during XLSX import: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")