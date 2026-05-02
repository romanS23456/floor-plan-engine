"""Room Program model and validation for Floor Plan Engine.

MVP 7: RoomProgram v1
Describes expected room composition and compares actual Plan against it.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RoomRequirement(BaseModel):
    """A single room requirement in a program."""
    
    id: str = Field(description="Unique identifier for this requirement")
    room_type: str = Field(description="Required room type (e.g., 'bedroom', 'kitchen', 'bathroom')")
    name: Optional[str] = Field(default=None, description="Human-readable room name")
    quantity: int = Field(default=1, description="How many rooms of this type are required (1 or more)")
    required: bool = Field(default=True, description="True = must exist, False = optional")
    target_area_m2: Optional[float] = Field(default=None, description="Target area in m²")
    min_area_m2: Optional[float] = Field(default=None, description="Minimum acceptable area in m²")
    max_area_m2: Optional[float] = Field(default=None, description="Maximum acceptable area in m²")
    required_adjacencies: List[str] = Field(default_factory=list, description="List of room types that must be adjacent (e.g., ['kitchen', 'dining'])")
    forbidden_adjacencies: List[str] = Field(default_factory=list, description="List of room types that must NOT be adjacent")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RoomProgram(BaseModel):
    """A room program describing expected room composition and relationships."""
    
    id: str = Field(description="Unique identifier for this program")
    name: Optional[str] = Field(default=None, description="Human-readable program name")
    description: Optional[str] = Field(default=None, description="Narrative description of program intent")
    target_total_area_m2: Optional[float] = Field(default=None, description="Target total project area in m²")
    requirements: List[RoomRequirement] = Field(description="List of room requirements")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


def infer_room_type(room_id: str, room_name: str) -> str:
    """Infer room type from id and name (simple heuristic).
    
    Args:
        room_id: Room ID from plan
        room_name: Room name from plan
        
    Returns:
        Inferred room type string
    """
    combined = f"{room_id} {room_name}".lower()
    
    # Common patterns
    type_patterns = {
        "bedroom": ["bedroom", "master", "bed"],
        "bathroom": ["bathroom", "bath", "toilet", "wc"],
        "kitchen": ["kitchen", "kitchenette", "cook"],
        "living": ["living", "lounge", "sitting room"],
        "dining": ["dining", "diningroom", "dinner"],
        "entry": ["entry", "entrance", "foyer", "hall", "lobby"],
        "corridor": ["corridor", "hallway", "passage"],
        "office": ["office", "study", "workspace"],
        "garage": ["garage", "carport"],
        "storage": ["storage", "pantry", "closet", "utility"],
        "laundry": ["laundry", "washer"],
        "garden": ["garden", "patio", "terrace", "outdoor"],
    }
    
    for room_type, patterns in type_patterns.items():
        for pattern in patterns:
            if pattern in combined:
                return room_type
    
    return "unknown"
