from typing import Dict, Any, List
from app.models import Plan
from app.geometry import calculate_polygon_area_m2
from app.connectivity import (
    build_room_graph,
    get_entry_room_ids,
    find_unreachable_rooms,
    detect_pantry_through_bathroom,
    detect_privacy_warnings,
)


def validate_plan(plan: Plan) -> Dict[str, Any]:
    """
    Validate a floor plan and return validation results.
    
    Returns:
        dict with keys:
            - areas: dict mapping room_id to area in m²
            - errors: list of error messages
            - warnings: list of warning messages
            - connectivity: dict with connectivity analysis (optional)
    """
    result = {
        "areas": {},
        "errors": [],
        "warnings": []
    }
    
    # Build set of room IDs for reference checking
    room_ids = set()
    
    # Track which rooms have doors connected
    rooms_with_doors = set()
    
    # Validate rooms
    for room in plan.rooms:
        room_ids.add(room.id)
        
        # Check polygon has minimum 3 points
        if len(room.polygon_mm) < 3:
            result["errors"].append(
                f"Room '{room.id}' ({room.name}): polygon must have at least 3 points, got {len(room.polygon_mm)}"
            )
        else:
            # Calculate area
            try:
                area = calculate_polygon_area_m2(room.polygon_mm)
                result["areas"][room.id] = round(area, 4)
            except ValueError as e:
                result["errors"].append(
                    f"Room '{room.id}' ({room.name}): invalid polygon - {str(e)}"
                )
    
    # Validate doors
    for door in plan.doors:
        # Check from_room_id exists
        if door.from_room_id not in room_ids:
            result["errors"].append(
                f"Door '{door.id}': from_room_id '{door.from_room_id}' does not exist"
            )
        else:
            rooms_with_doors.add(door.from_room_id)
        
        # Check to_room_id exists if not null
        if door.to_room_id is not None and door.to_room_id not in room_ids:
            result["errors"].append(
                f"Door '{door.id}': to_room_id '{door.to_room_id}' does not exist"
            )
        elif door.to_room_id is not None:
            rooms_with_doors.add(door.to_room_id)
    
    # Check for rooms without doors (warning)
    for room in plan.rooms:
        if room.id not in rooms_with_doors:
            result["warnings"].append(
                f"Room '{room.id}' ({room.name}): no door connected"
            )
    
    # Connectivity validation (MVP 2)
    entry_room_ids = get_entry_room_ids(plan)
    unreachable_rooms = find_unreachable_rooms(plan)
    pantry_through_bathroom = detect_pantry_through_bathroom(plan)
    privacy_warnings = detect_privacy_warnings(plan)
    
    # Add connectivity errors
    for room_id in unreachable_rooms:
        result["errors"].append(f"UNREACHABLE_ROOM: room_id={room_id}")
    
    # Add connectivity warnings
    if not entry_room_ids:
        result["warnings"].append("NO_ENTRY_ROOM")
    
    for room_id in pantry_through_bathroom:
        result["warnings"].append(f"PANTRY_THROUGH_BATHROOM: room_id={room_id}")
    
    for pw in privacy_warnings:
        if pw["type"] == "PRIVACY_DIRECT_PUBLIC_PRIVATE":
            result["warnings"].append(f"PRIVACY_DIRECT_PUBLIC_PRIVATE: room_id={pw['room_id']}")
        elif pw["type"] == "PRIVACY_PASS_THROUGH_PRIVATE_ROOM":
            result["warnings"].append(f"PRIVACY_PASS_THROUGH_PRIVATE_ROOM: room_id={pw['room_id']}")
        elif pw["type"] == "BATHROOM_CONNECTED_TO_PANTRY":
            result["warnings"].append(f"BATHROOM_CONNECTED_TO_PANTRY: room_id={pw['room_id']}")
    
    # Add connectivity info to result
    graph = build_room_graph(plan)
    result["connectivity"] = {
        "entry_room_ids": entry_room_ids,
        "unreachable_room_ids": unreachable_rooms,
        "room_graph": {
            "nodes": list(graph.nodes()),
            "edges": [[u, v] for u, v in graph.edges()]
        }
    }
    
    return result
