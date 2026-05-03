"""RoomProgram models for Floor Plan Engine.

MVP 7: RoomProgram v1.
RoomProgram describes expected room composition and relationships.
It does not generate rooms and does not parse natural language.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RoomRequirement(BaseModel):
    """A single room requirement inside a RoomProgram."""

    id: str = Field(description="Unique requirement id")
    room_type: str = Field(description="Required room type, for example bedroom, kitchen, bathroom")
    name: Optional[str] = Field(default=None, description="Human-readable requirement name")
    quantity: int = Field(default=1, ge=1, description="Required room count")
    required: bool = Field(default=True, description="Whether this room type is mandatory")

    target_area_m2: Optional[float] = Field(default=None, gt=0, description="Target area in square meters")
    min_area_m2: Optional[float] = Field(default=None, gt=0, description="Minimum acceptable area")
    max_area_m2: Optional[float] = Field(default=None, gt=0, description="Maximum acceptable area")

    required_adjacencies: List[str] = Field(
        default_factory=list,
        description="Room types that should be directly connected to this room type",
    )
    forbidden_adjacencies: List[str] = Field(
        default_factory=list,
        description="Room types that should not be directly connected to this room type",
    )

    meta: Dict[str, Any] = Field(default_factory=dict)


class RoomProgram(BaseModel):
    """Structured room program for validating a Plan."""

    id: str = Field(description="Unique room program id")
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    target_total_area_m2: Optional[float] = Field(default=None, gt=0)
    requirements: List[RoomRequirement] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


def infer_program_room_type(room_id: str, room_name: str, explicit_room_type: Optional[str] = None) -> str:
    """Infer a normalized room type.

    Explicit room_type from Plan.Room has priority.
    Fallback is a deterministic id/name heuristic.
    """

    if explicit_room_type:
        return explicit_room_type.strip().lower()

    text = f"{room_id} {room_name}".strip().lower()

    patterns = {
        "bedroom": ["bedroom", "master", "bed", "спальня"],
        "bathroom": ["bathroom", "bath", "toilet", "wc", "санузел", "ванная", "туалет"],
        "kitchen": ["kitchen", "cook", "кухня"],
        "living": ["living", "lounge", "гостиная"],
        "dining": ["dining", "столовая"],
        "entry": ["entry", "entrance", "foyer", "прихожая", "тамбур"],
        "corridor": ["corridor", "hallway", "passage", "коридор", "холл"],
        "office": ["office", "study", "кабинет"],
        "garage": ["garage", "гараж"],
        "storage": ["storage", "pantry", "closet", "кладовая", "гардероб"],
        "laundry": ["laundry", "постирочная"],
        "utility": ["utility", "boiler", "technical", "котельная", "техпомещение"],
        "terrace": ["terrace", "patio", "терраса"],
    }

    for room_type, aliases in patterns.items():
        if any(alias in text for alias in aliases):
            return room_type

    return "unknown"
