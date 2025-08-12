from __future__ import annotations
from typing import List, Optional, Literal, Dict, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
import uuid

UOM = Literal["g", "ml", "pcs"]

class MetaV2(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=2, max_length=200)
    version: str = Field(default="2.0")
    createdAt: datetime = Field(default_factory=datetime.now)
    cuisine: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)

class YieldV2(BaseModel):
    perPortion_g: float = Field(..., gt=0)
    perBatch_g: float = Field(..., gt=0)

class IngredientV2(BaseModel):
    name: str = Field(..., min_length=1)
    skuId: Optional[str] = None
    unit: UOM = "g"
    brutto_g: float = Field(..., ge=0)
    loss_pct: float = Field(..., ge=0, le=100)
    netto_g: float = Field(..., ge=0)
    allergens: Optional[List[str]] = Field(default_factory=list)
    
    @field_validator("netto_g")
    @classmethod
    def validate_netto(cls, v, info):
        if hasattr(info, 'data') and 'brutto_g' in info.data and 'loss_pct' in info.data:
            brutto = info.data['brutto_g']
            loss = info.data['loss_pct']
            expected_netto = brutto * (1 - loss / 100)
            if abs(v - expected_netto) > 1.0:  # допуск ±1 г
                raise ValueError(f"netto_g must equal brutto_g * (1 - loss_pct/100). Expected: {expected_netto:.1f}, got: {v}")
        return v

class ProcessStepV2(BaseModel):
    n: int = Field(..., ge=1)
    action: str = Field(..., min_length=1)
    time_min: Optional[float] = None
    temp_c: Optional[float] = None
    equipment: Optional[List[str]] = Field(default_factory=list)
    ccp: Optional[bool] = False
    note: Optional[str] = None
    
    @field_validator("temp_c", "time_min")
    @classmethod
    def validate_thermal_step(cls, v, info):
        # Для термообработки должен быть time_min ИЛИ temp_c
        if hasattr(info, 'data') and 'action' in info.data:
            action = info.data['action'].lower()
            is_thermal = any(word in action for word in ['жарить', 'варить', 'готовить', 'тушить', 'запекать', 'кипятить'])
            if is_thermal and info.field_name == 'time_min' and v is None and info.data.get('temp_c') is None:
                raise ValueError("Thermal process steps must have either time_min or temp_c")
        return v

class StorageV2(BaseModel):
    conditions: str = Field(..., min_length=1)
    shelfLife_hours: float = Field(..., gt=0)
    servingTemp_c: Optional[float] = None

class NutritionPer(BaseModel):
    kcal: float = Field(..., ge=0)
    proteins_g: float = Field(..., ge=0)
    fats_g: float = Field(..., ge=0)
    carbs_g: float = Field(..., ge=0)

class NutritionV2(BaseModel):
    per100g: Optional[NutritionPer] = None
    perPortion: Optional[NutritionPer] = None

class CostMetaV2(BaseModel):
    source: Literal["catalog", "csv", "llm", "none"] = "none"
    coveragePct: float = Field(..., ge=0, le=100)
    asOf: Optional[str] = None  # YYYY-MM-DD format

class CostV2(BaseModel):
    rawCost: Optional[float] = None
    costPerPortion: Optional[float] = None
    markup_pct: Optional[float] = None
    vat_pct: Optional[float] = None

class TechCardV2(BaseModel):
    meta: MetaV2
    portions: int = Field(..., ge=1)
    yield_: YieldV2 = Field(..., alias="yield")
    ingredients: List[IngredientV2] = Field(..., min_length=1)
    process: List[ProcessStepV2] = Field(..., min_length=3)
    storage: StorageV2
    nutrition: NutritionV2 = Field(default_factory=NutritionV2)
    cost: CostV2 = Field(default_factory=CostV2)
    costMeta: Optional[CostMetaV2] = None
    printNotes: Optional[List[str]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)
    
    @field_validator("process")
    @classmethod
    def validate_process_steps(cls, v):
        if len(v) < 3:
            raise ValueError("Process must have at least 3 steps")
        return v
    
    @field_validator("yield_")
    @classmethod
    def validate_yield_consistency(cls, v, info):
        if hasattr(info, 'data') and 'ingredients' in info.data and 'portions' in info.data:
            ingredients = info.data['ingredients']
            portions = info.data['portions']
            
            total_netto = sum(ing.get('netto_g', 0) for ing in ingredients if isinstance(ing, dict))
            expected_batch = v.perPortion_g * portions if hasattr(v, 'perPortion_g') else 0
            
            # Проверяем соответствие суммы netto ≈ perBatch_g (допуск ±5%)
            if expected_batch > 0 and abs(total_netto - expected_batch) > expected_batch * 0.05:
                raise ValueError(f"Sum of ingredients netto_g ({total_netto}g) must ≈ yield.perBatch_g ({expected_batch}g) within 5%")
        return v

# Обратная совместимость - старые классы для существующего кода
Meta = MetaV2
Yield = BaseModel  # Placeholder
Ingredient = BaseModel  # Placeholder
ProcessStep = BaseModel  # Placeholder
CCP = BaseModel  # Placeholder
HACCP = BaseModel  # Placeholder