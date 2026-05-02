from typing import Optional, List
from pydantic import BaseModel


class Room(BaseModel):
    id: str
    name: str
    polygon_mm: List[List[float]]  # list of [x, y] coordinates in millimeters
    target_area_m2: Optional[float] = None
    room_type: Optional[str] = None
    privacy_level: Optional[str] = None


class Door(BaseModel):
    id: str
    from_room_id: str
    to_room_id: Optional[str] = None
    position_mm: List[float]  # [x, y] in millimeters
    width_mm: int
    swing: Optional[str] = None


class Window(BaseModel):
    id: str
    room_id: str
    position_mm: List[float]  # [x, y] in millimeters
    width_mm: int


class Furniture(BaseModel):
    id: str
    room_id: str
    type: str
    polygon_mm: List[List[float]]  # list of [x, y] coordinates in millimeters


class Plan(BaseModel):
    rooms: List[Room]
    doors: List[Door]
    windows: List[Window]
    furniture: List[Furniture]
