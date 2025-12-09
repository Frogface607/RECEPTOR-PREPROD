from __future__ import annotations
from typing import List
from pydantic import BaseModel
from receptor_agent.techcards_v2.schemas import TechCardV2

class MenuV2(BaseModel):
    menuId: str
    items: List[TechCardV2]