from __future__ import annotations
from typing import List, Optional, Literal, Dict, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
import uuid

UOM = Literal["g", "ml", "pcs"]

class SubRecipeRefV2(BaseModel):
    """Ссылка на подрецепт/полуфабрикат"""
    id: str = Field(..., description="UUID другой техкарты")
    title: str = Field(..., min_length=1, description="Название подрецепта для отображения")

class MetaV2(BaseModel):
    model_config = ConfigDict(extra="forbid")  # GX-01-FINAL: запрещаем лишние ключи
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=2, max_length=200)
    version: str = Field(default="2.0")
    createdAt: datetime = Field(default_factory=datetime.now)
    cuisine: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    # GX-01-FINAL: безопасная сериализация timings
    timings: Dict[str, float] = Field(default_factory=dict, description="Метрики времени выполнения pipeline (ms)")
    
    # Standard Portion by Default: поля для нормализации порций
    scale_factor: Optional[float] = Field(default=None, description="Коэффициент масштабирования для нормализации порций")
    archetype: Optional[str] = Field(default=None, description="Архетип блюда для нормализации порций")
    original_sum_netto: Optional[float] = Field(default=None, description="Исходная сумма нетто до нормализации")
    
    # Article field for iiko integration
    article: Optional[str] = Field(default=None, description="5-digit article code for iiko integration")
    normalized: Optional[bool] = Field(default=None, description="Флаг что техкарта была нормализована")

class YieldV2(BaseModel):
    perPortion_g: float = Field(..., gt=0)
    perBatch_g: float = Field(..., gt=0)

class IngredientV2(BaseModel):
    name: str = Field(..., min_length=1)
    canonical_id: Optional[str] = None  # Для маппинга к каталогу питания
    skuId: Optional[str] = None  # Для маппинга к каталогу цен/SKU (GUID)
    product_code: Optional[str] = None  # A. Hotfix & Migration: числовой код продукта iiko (article)
    subRecipe: Optional[SubRecipeRefV2] = None  # Ссылка на подрецепт/полуфабрикат
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
            # Увеличиваем допуск до ±3г для совместимости с операционным округлением
            if abs(v - expected_netto) > 3.0:  # допуск ±3 г
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

class NutritionMetaV2(BaseModel):
    source: Literal["catalog", "csv", "none", "usda", "bootstrap"] = "none"
    coveragePct: float = Field(..., ge=0, le=100)

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
    nutritionMeta: Optional[NutritionMetaV2] = None
    cost: CostV2 = Field(default_factory=CostV2)
    costMeta: Optional[CostMetaV2] = None
    printNotes: Optional[List[str]] = Field(default_factory=list)
    article: Optional[str] = None  # Phase 3.5: Dish article for iiko compatibility

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

def get_techcard_v2_schema() -> dict:
    """
    Возвращает JSON схему для TechCardV2 для использования в OpenAI structured outputs
    """
    return TechCardV2.model_json_schema()


def get_techcard_v2_example() -> dict:
    """
    Возвращает пример валидной TechCardV2 для промптов
    """
    return {
        "meta": {
            "id": "example-123",
            "title": "Салат Цезарь",
            "version": "2.0",
            "createdAt": "2025-01-20T10:00:00Z",
            "cuisine": "Европейская",
            "tags": ["салат", "классический"]
        },
        "portions": 4,
        "yield": {
            "perPortion_g": 150,
            "perBatch_g": 600
        },
        "ingredients": [
            {
                "name": "Салат Романо",
                "unit": "g",
                "brutto_g": 200,
                "loss_pct": 15,
                "netto_g": 170
            },
            {
                "name": "Куриное филе",
                "unit": "g", 
                "brutto_g": 300,
                "loss_pct": 5,
                "netto_g": 285
            }
        ],
        "process": [
            {
                "n": 1,
                "action": "Промыть и нарезать салат",
                "time_min": 5
            },
            {
                "n": 2,
                "action": "Обжарить куриное филе",
                "time_min": 10,
                "temp_c": 180
            },
            {
                "n": 3,
                "action": "Смешать ингредиенты и заправить",
                "time_min": 3
            }
        ],
        "storage": {
            "conditions": "Хранить в холодильнике",
            "shelfLife_hours": 24,
            "servingTemp_c": 5
        },
        "nutrition": {
            "per100g": {
                "kcal": 180,
                "proteins_g": 12,
                "fats_g": 8,
                "carbs_g": 6
            }
        },
        "cost": {
            "rawCost": 250,
            "costPerPortion": 62.5
        }
    }