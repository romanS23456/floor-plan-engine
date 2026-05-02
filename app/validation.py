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
from app.geometric_validation import (
    detect_room_overlaps,
    detect_furniture_outside_room,
    detect_unknown_references,
    detect_min_area_issues,
    detect_rough_door_furniture_conflicts,
)
from app.issues import make_issue


def validate_plan(plan: Plan) -> Dict[str, Any]:
    """
    Validate a floor plan and return validation results.
    
    Returns:
        dict with keys:
            - areas: dict mapping room_id to area in m²
            - errors: list of error messages
            - warnings: list of warning messages
            - connectivity: dict with connectivity analysis
            - issues: list of structured ValidationIssue dicts
            - geometry: dict with geometric validation details
    """
    result = {
        "areas": {},
        "errors": [],
        "warnings": [],
        "issues": [],
        "geometry": {
            "room_overlaps": [],
            "furniture_outside_room": [],
            "unknown_references": [],
            "min_area_issues": [],
            "door_furniture_conflicts": [],
        }
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
            error_msg = f"Room '{room.id}' ({room.name}): polygon must have at least 3 points, got {len(room.polygon_mm)}"
            result["errors"].append(error_msg)
            result["issues"].append(make_issue(
                code="INVALID_ROOM_POLYGON",
                severity="error",
                entity_refs=[{"type": "room", "id": room.id}],
                message=error_msg,
            ))
        else:
            # Calculate area
            try:
                area = calculate_polygon_area_m2(room.polygon_mm)
                result["areas"][room.id] = round(area, 4)
            except ValueError as e:
                error_msg = f"Room '{room.id}' ({room.name}): invalid polygon - {str(e)}"
                result["errors"].append(error_msg)
                result["issues"].append(make_issue(
                    code="INVALID_ROOM_POLYGON",
                    severity="error",
                    entity_refs=[{"type": "room", "id": room.id}],
                    message=error_msg,
                ))
    
    # Validate doors
    for door in plan.doors:
        # Check from_room_id exists
        if door.from_room_id not in room_ids:
            error_msg = f"Door '{door.id}': from_room_id '{door.from_room_id}' does not exist"
            result["errors"].append(error_msg)
            result["issues"].append(make_issue(
                code="INVALID_DOOR_FROM_ROOM_REFERENCE",
                severity="error",
                entity_refs=[
                    {"type": "door", "id": door.id},
                    {"type": "room", "id": door.from_room_id},
                ],
                message=error_msg,
            ))
        else:
            rooms_with_doors.add(door.from_room_id)
        
        # Check to_room_id exists if not null
        if door.to_room_id is not None and door.to_room_id not in room_ids:
            error_msg = f"Door '{door.id}': to_room_id '{door.to_room_id}' does not exist"
            result["errors"].append(error_msg)
            result["issues"].append(make_issue(
                code="INVALID_DOOR_TO_ROOM_REFERENCE",
                severity="error",
                entity_refs=[
                    {"type": "door", "id": door.id},
                    {"type": "room", "id": door.to_room_id},
                ],
                message=error_msg,
            ))
        elif door.to_room_id is not None:
            rooms_with_doors.add(door.to_room_id)
    
    # Check for rooms without doors (warning)
    for room in plan.rooms:
        if room.id not in rooms_with_doors:
            warning_msg = f"Room '{room.id}' ({room.name}): no door connected"
            result["warnings"].append(warning_msg)
            result["issues"].append(make_issue(
                code="ROOM_WITHOUT_DOOR",
                severity="warning",
                entity_refs=[{"type": "room", "id": room.id}],
                message=warning_msg,
            ))
    
    # Connectivity validation (MVP 2)
    entry_room_ids = get_entry_room_ids(plan)
    unreachable_rooms = find_unreachable_rooms(plan)
    pantry_through_bathroom = detect_pantry_through_bathroom(plan)
    privacy_warnings = detect_privacy_warnings(plan)
    
    # Add connectivity errors
    for room_id in unreachable_rooms:
        error_msg = f"UNREACHABLE_ROOM: room_id={room_id}"
        result["errors"].append(error_msg)
        result["issues"].append(make_issue(
            code="UNREACHABLE_ROOM",
            severity="error",
            entity_refs=[{"type": "room", "id": room_id}],
            message=f"Room '{room_id}' is not reachable from any entry room",
        ))
    
    # Add connectivity warnings
    if not entry_room_ids:
        result["warnings"].append("NO_ENTRY_ROOM")
        result["issues"].append(make_issue(
            code="NO_ENTRY_ROOM",
            severity="warning",
            entity_refs=[],
            message="No entry room detected in plan",
        ))
    
    for room_id in pantry_through_bathroom:
        warning_msg = f"PANTRY_THROUGH_BATHROOM: room_id={room_id}"
        result["warnings"].append(warning_msg)
        result["issues"].append(make_issue(
            code="PANTRY_THROUGH_BATHROOM",
            severity="warning",
            entity_refs=[{"type": "room", "id": room_id}],
            message=f"Pantry '{room_id}' is only accessible through bathroom",
        ))
    
    for pw in privacy_warnings:
        if pw["type"] == "PRIVACY_DIRECT_PUBLIC_PRIVATE":
            warning_msg = f"PRIVACY_DIRECT_PUBLIC_PRIVATE: room_id={pw['room_id']}"
            result["warnings"].append(warning_msg)
            result["issues"].append(make_issue(
                code="PRIVACY_DIRECT_PUBLIC_PRIVATE",
                severity="warning",
                entity_refs=[{"type": "room", "id": pw["room_id"]}],
                message=f"Private room '{pw['room_id']}' directly connected to public room",
            ))
        elif pw["type"] == "PRIVACY_PASS_THROUGH_PRIVATE_ROOM":
            warning_msg = f"PRIVACY_PASS_THROUGH_PRIVATE_ROOM: room_id={pw['room_id']}"
            result["warnings"].append(warning_msg)
            result["issues"].append(make_issue(
                code="PRIVACY_PASS_THROUGH_PRIVATE_ROOM",
                severity="warning",
                entity_refs=[{"type": "room", "id": pw["room_id"]}],
                message=f"Private room '{pw['room_id']}' is a pass-through room",
            ))
        elif pw["type"] == "BATHROOM_CONNECTED_TO_PANTRY":
            warning_msg = f"BATHROOM_CONNECTED_TO_PANTRY: room_id={pw['room_id']}"
            result["warnings"].append(warning_msg)
            result["issues"].append(make_issue(
                code="BATHROOM_CONNECTED_TO_PANTRY",
                severity="warning",
                entity_refs=[{"type": "room", "id": pw["room_id"]}],
                message=f"Bathroom '{pw['room_id']}' directly connected to pantry",
            ))
    
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
    
    # Geometric validation (MVP 4)
    room_overlaps = detect_room_overlaps(plan)
    furniture_outside = detect_furniture_outside_room(plan)
    unknown_refs = detect_unknown_references(plan)
    min_area_issues = detect_min_area_issues(plan)
    door_furniture_conflicts = detect_rough_door_furniture_conflicts(plan)
    
    # Process room overlaps
    for overlap in room_overlaps:
        result["geometry"]["room_overlaps"].append(overlap)
        error_msg = f"ROOM_OVERLAP: {overlap.get('message', 'Rooms overlap')}"
        result["errors"].append(error_msg)
        result["issues"].append(make_issue(
            code="ROOM_OVERLAP",
            severity="error",
            entity_refs=[{"type": "room", "id": rid} for rid in overlap.get("room_ids", [])],
            message=overlap.get("message", "Rooms overlap"),
        ))
    
    # Process furniture outside room
    for issue in furniture_outside:
        result["geometry"]["furniture_outside_room"].append(issue)
        error_msg = f"{issue.get('code', 'FURNITURE_OUTSIDE_ROOM')}: {issue.get('message', '')}"
        result["errors"].append(error_msg)
        result["issues"].append(make_issue(
            code=issue.get("code", "FURNITURE_OUTSIDE_ROOM"),
            severity="error",
            entity_refs=[{"type": "furniture", "id": issue.get("furniture_id")}],
            message=issue.get("message", ""),
        ))
    
    # Process unknown references
    for issue in unknown_refs:
        result["geometry"]["unknown_references"].append(issue)
        error_msg = f"{issue.get('code', 'UNKNOWN_REFERENCE')}: {issue.get('message', '')}"
        result["errors"].append(error_msg)
        result["issues"].append(make_issue(
            code=issue.get("code", "UNKNOWN_REFERENCE"),
            severity="error",
            entity_refs=issue.get("entity_refs", []),
            message=issue.get("message", ""),
        ))
    
    # Process min area issues
    for issue in min_area_issues:
        result["geometry"]["min_area_issues"].append(issue)
        warning_msg = f"{issue.get('code', 'ROOM_AREA_BELOW_MINIMUM')}: {issue.get('message', '')}"
        result["warnings"].append(warning_msg)
        result["issues"].append(make_issue(
            code=issue.get("code", "ROOM_AREA_BELOW_MINIMUM"),
            severity="warning",
            entity_refs=[{"type": "room", "id": issue.get("room_id")}],
            message=issue.get("message", ""),
        ))
    
    # Process door-furniture conflicts
    for issue in door_furniture_conflicts:
        result["geometry"]["door_furniture_conflicts"].append(issue)
        warning_msg = f"{issue.get('code', 'ROUGH_DOOR_FURNITURE_CONFLICT')}: {issue.get('message', '')}"
        result["warnings"].append(warning_msg)
        result["issues"].append(make_issue(
            code=issue.get("code", "ROUGH_DOOR_FURNITURE_CONFLICT"),
            severity="warning",
            entity_refs=[
                {"type": "door", "id": issue.get("door_id")},
                {"type": "furniture", "id": issue.get("furniture_id")},
            ],
            message=issue.get("message", ""),
        ))
    
    return result
