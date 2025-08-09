from __future__ import annotations
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator

UOM = Literal["g", "ml", "pcs"]

class Meta(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    category: Optional[str] = None
    cuisine: Optional[str] = None
    description: Optional[str] = None

class Yield(BaseModel):
    portions: int = Field(..., gt=0, le=500)
    per_portion_g: int = Field(..., gt=1, le=5000)
    total_net_g: int = Field(..., gt=1, le=1000000)

    @field_validator("total_net_g")
    @classmethod
    def _positive(cls, v):
        if v <= 0:
            raise ValueError("total_net_g must be > 0")
        return v

class Ingredient(BaseModel):
    name: str
    uom: UOM = "g"
    gross_g: float = Field(..., ge=0)
    net_g: float = Field(..., ge=0)
    loss_pct: float = Field(0, ge=0, le=95)
    notes: Optional[str] = None
    # нормализованное имя из словаря
    canonical: Optional[str] = None
    needs_review: bool = False

class ProcessStep(BaseModel):
    step: int
    desc: str
    temp_c: Optional[int] = None
    time_min: Optional[int] = None

class CCP(BaseModel):
    name: str
    limit: str
    monitoring: str
    corrective: str

class HACCP(BaseModel):
    hazards: List[str] = Field(default_factory=list)
    ccp: List[CCP] = Field(default_factory=list)
    storage: Optional[str] = None  # условия/сроки

class TechCardV2(BaseModel):
    meta: Meta
    yield_: Yield = Field(..., alias="yield")
    ingredients: List[Ingredient]
    process: List[ProcessStep] = Field(default_factory=list)
    haccp: HACCP = Field(default_factory=HACCP)
    allergens: List[str] = Field(default_factory=list)
    pricing: Optional[Dict[str, float]] = None  # опционально: себестоимость/наценка

    class Config:
        populate_by_name = True