"""Project Brief models for Floor Plan Engine.

Minimal structured project context so GPT-architect can understand:
- project type
- design stage
- household composition
- lifestyle requirements
- priorities
- missing brief data
- limitations of plan review
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class Household(BaseModel):
    """Household composition."""
    adults: Optional[int] = None
    children: Optional[int] = None
    elderly: Optional[int] = None
    guests_often: Optional[bool] = None


class Lifestyle(BaseModel):
    """Lifestyle requirements."""
    cooks_often: Optional[bool] = None
    works_from_home: Optional[bool] = None
    needs_guest_room: Optional[bool] = None
    pets: Optional[bool] = None
    permanent_living: Optional[bool] = None


class ProjectBrief(BaseModel):
    """Project brief capturing project intent and context."""
    id: Optional[str] = None
    project_name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    stage: Optional[str] = None
    architectural_style: Optional[str] = None
    budget_level: Optional[str] = None
    construction_method: Optional[str] = None
    target_total_area_m2: Optional[float] = None
    floors_count: Optional[int] = None
    household: Optional[Household] = None
    lifestyle: Optional[Lifestyle] = None
    priorities: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
