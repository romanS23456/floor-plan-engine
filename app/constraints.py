"""Planning constraints for Floor Plan Engine.

MVP 5: First version of declarative project requirements.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PlanningConstraint(BaseModel):
    """A planning constraint expressing a project requirement."""
    
    id: str
    constraint_type: str = Field(
        description="Type of constraint: min_area, max_area, required_connection, "
                    "forbidden_connection, required_room_type, required_access_from_entry"
    )
    priority: str = Field(default="should", description="Priority: must, should, nice_to_have")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    
    # Targeting fields
    room_id: Optional[str] = Field(default=None, description="Target specific room by ID")
    room_type: Optional[str] = Field(default=None, description="Target rooms by type")
    target_room_id: Optional[str] = Field(default=None, description="Target for connection constraints")
    target_room_type: Optional[str] = Field(default=None, description="Target type for connection constraints")
    
    # Value fields
    min_area_m2: Optional[float] = Field(default=None, description="Minimum area in m²")
    max_area_m2: Optional[float] = Field(default=None, description="Maximum area in m²")
    count: int = Field(default=1, description="Required count for room type constraints")
    
    # Additional metadata
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# Allowed constraint types
CONSTRAINT_TYPES = [
    "min_area",
    "max_area",
    "required_connection",
    "forbidden_connection",
    "required_room_type",
    "required_access_from_entry",
]

# Allowed priority values
PRIORITY_VALUES = ["must", "should", "nice_to_have"]

# Priority to severity mapping
PRIORITY_TO_SEVERITY = {
    "must": "error",
    "should": "warning",
    "nice_to_have": "info",
}


def priority_to_severity(priority: str) -> str:
    """Convert constraint priority to issue severity."""
    return PRIORITY_TO_SEVERITY.get(priority, "warning")


def is_valid_constraint_type(constraint_type: str) -> bool:
    """Check if constraint type is valid."""
    return constraint_type in CONSTRAINT_TYPES


def is_valid_priority(priority: str) -> bool:
    """Check if priority is valid."""
    return priority in PRIORITY_VALUES
