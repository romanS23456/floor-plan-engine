"""RoomProgram models for Floor Plan Engine.

RoomProgram describes expected room composition and adjacency intent.
It is project intent, not geometry.
"""

from typing import Optional, List
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
    metadata: dict = Field(default_factory=dict)


class AdjacencyRequirement(BaseModel):
    """Requirement for adjacency between room types."""
    
    id: str
    from_room_type: str
    to_room_type: str
    adjacency_type: str = "direct"  # direct, near, separated
    required: bool = True
    priority: str = "should"
    notes: Optional[str] = None


class RoomProgram(BaseModel):
    """RoomProgram describing expected room composition and adjacencies."""
    
    id: Optional[str] = None
    name: Optional[str] = None
    requirements: List[RoomRequirement] = Field(default_factory=list)
    adjacency_requirements: List[AdjacencyRequirement] = Field(default_factory=list)
    notes: Optional[str] = None
