"""Room Program models for Floor Plan Engine.

RoomProgram describes expected room composition and adjacency intent.
This is NOT geometry - it's a specification of what rooms should exist.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class RoomRequirement(BaseModel):
    """Requirement for a room type in the program."""
    id: str
    room_type: str
    name: Optional[str] = None
    required: bool = True
    min_count: int = 1
    max_count: Optional[int] = None
    target_area_m2: Optional[float] = None
    min_area_m2: Optional[float] = None
    max_area_m2: Optional[float] = None
    notes: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class AdjacencyRequirement(BaseModel):
    """Adjacency requirement between room types."""
    id: str
    from_room_type: str
    to_room_type: str
    adjacency_type: str = "direct"
    required: bool = True
    priority: str = "should"
    notes: Optional[str] = None


class RoomProgram(BaseModel):
    """Room program specifying expected rooms and adjacencies."""
    id: Optional[str] = None
    name: Optional[str] = None
    requirements: List[RoomRequirement] = Field(default_factory=list)
    adjacency_requirements: List[AdjacencyRequirement] = Field(default_factory=list)
    notes: Optional[str] = None
