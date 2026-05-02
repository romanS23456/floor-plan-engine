"""Program validation for Floor Plan Engine.

Validates a Plan against a RoomProgram specification.
"""

from typing import Any, Dict, List, Set
from app.models import Plan
from app.room_program import RoomProgram, RoomRequirement, AdjacencyRequirement
from app.connectivity import infer_room_type, build_room_graph
from app.geometry import calculate_polygon_area_m2
from app.issues import make_issue


def validate_room_program(plan: Plan, room_program: RoomProgram) -> Dict[str, Any]:
    """
    Validate a floor plan against a room program.
    
    Returns:
        dict with keys:
            - program_summary: dict with counts and matched/missing room types
            - program_issues: list of ValidationIssue dicts
    """
    result = {
        "program_summary": {
            "requirements_total": 0,
            "requirements_checked": 0,
            "issues_count": 0,
            "matched_room_types": [],
            "missing_room_types": [],
            "unsupported_checks": []
        },
        "program_issues": []
    }
    
    # Handle empty program
    if not room_program.requirements:
        result["program_summary"]["requirements_total"] = 0
        result["program_issues"].append(make_issue(
            code="PROGRAM_EMPTY",
            severity="info",
            entity_refs=[],
            message="Room program has no requirements; nothing to validate",
        ))
        return result
    
    # Build room type mapping from plan
    room_id_to_type: Dict[str, str] = {}
    room_type_to_ids: Dict[str, List[str]] = {}
    room_areas: Dict[str, float] = {}
    
    for room in plan.rooms:
        room_type = infer_room_type(room)
        room_id_to_type[room.id] = room_type
        
        if room_type not in room_type_to_ids:
            room_type_to_ids[room_type] = []
        room_type_to_ids[room_type].append(room.id)
        
        # Calculate area
        try:
            area = calculate_polygon_area_m2(room.polygon_mm)
            room_areas[room.id] = area
        except (ValueError, TypeError):
            room_areas[room.id] = 0.0
    
    result["program_summary"]["requirements_total"] = len(room_program.requirements)
    
    # Track which room types are required
    required_room_types: Set[str] = set()
    
    # Check each room requirement
    for req in room_program.requirements:
        # Skip invalid requirements gracefully
        if not req.room_type:
            continue
        
        result["program_summary"]["requirements_checked"] += 1
        
        if req.required:
            required_room_types.add(req.room_type)
        
        # Count rooms matching this type
        matching_room_ids = room_type_to_ids.get(req.room_type, [])
        count = len(matching_room_ids)
        
        # Check minimum count
        min_count = req.min_count if req.min_count is not None else 1
        if count < min_count:
            if req.required:
                result["program_summary"]["missing_room_types"].append(req.room_type)
                result["program_issues"].append(make_issue(
                    code="PROGRAM_REQUIRED_ROOM_TYPE_MISSING" if count == 0 else "PROGRAM_TOO_FEW_ROOMS_OF_TYPE",
                    severity="error",
                    entity_refs=[{"type": "room_requirement", "id": req.id}],
                    message=f"Required room type '{req.room_type}': expected at least {min_count}, found {count}",
                ))
                result["program_summary"]["issues_count"] += 1
            else:
                result["program_issues"].append(make_issue(
                    code="PROGRAM_TOO_FEW_ROOMS_OF_TYPE",
                    severity="warning",
                    entity_refs=[{"type": "room_requirement", "id": req.id}],
                    message=f"Room type '{req.room_type}': expected at least {min_count}, found {count}",
                ))
                result["program_summary"]["issues_count"] += 1
        else:
            # Room type is present
            if req.room_type not in result["program_summary"]["matched_room_types"]:
                result["program_summary"]["matched_room_types"].append(req.room_type)
        
        # Check maximum count
        if req.max_count is not None and count > req.max_count:
            result["program_issues"].append(make_issue(
                code="PROGRAM_TOO_MANY_ROOMS_OF_TYPE",
                severity="warning",
                entity_refs=[{"type": "room_requirement", "id": req.id}],
                message=f"Room type '{req.room_type}': expected at most {req.max_count}, found {count}",
            ))
            result["program_summary"]["issues_count"] += 1
        
        # Check area constraints for matching rooms
        for room_id in matching_room_ids:
            area = room_areas.get(room_id, 0.0)
            
            # Min area check
            if req.min_area_m2 is not None and area < req.min_area_m2:
                result["program_issues"].append(make_issue(
                    code="PROGRAM_ROOM_AREA_BELOW_MINIMUM",
                    severity="warning",
                    entity_refs=[{"type": "room", "id": room_id}],
                    message=f"Room '{room_id}' ({req.room_type}): area {area:.2f} m² is below minimum {req.min_area_m2} m²",
                ))
                result["program_summary"]["issues_count"] += 1
            
            # Max area check
            if req.max_area_m2 is not None and area > req.max_area_m2:
                result["program_issues"].append(make_issue(
                    code="PROGRAM_ROOM_AREA_ABOVE_MAXIMUM",
                    severity="warning",
                    entity_refs=[{"type": "room", "id": room_id}],
                    message=f"Room '{room_id}' ({req.room_type}): area {area:.2f} m² is above maximum {req.max_area_m2} m²",
                ))
                result["program_summary"]["issues_count"] += 1
            
            # Target area check (tolerance of 20%)
            if req.target_area_m2 is not None:
                tolerance = req.target_area_m2 * 0.2
                if abs(area - req.target_area_m2) > tolerance:
                    result["program_issues"].append(make_issue(
                        code="PROGRAM_TARGET_AREA_MISMATCH",
                        severity="info",
                        entity_refs=[{"type": "room", "id": room_id}],
                        message=f"Room '{room_id}' ({req.room_type}): area {area:.2f} m² differs from target {req.target_area_m2} m² by more than 20%",
                    ))
                    result["program_summary"]["issues_count"] += 1
    
    # Check adjacency requirements
    graph = build_room_graph(plan)
    
    for adj_req in room_program.adjacency_requirements:
        from_type = adj_req.from_room_type
        to_type = adj_req.to_room_type
        adj_type = adj_req.adjacency_type
        
        # Find rooms of these types
        from_room_ids = room_type_to_ids.get(from_type, [])
        to_room_ids = room_type_to_ids.get(to_type, [])
        
        if not from_room_ids or not to_room_ids:
            # Can't check adjacency if rooms don't exist
            continue
        
        if adj_type == "direct":
            # Check if any from_room is directly connected to any to_room
            has_connection = False
            for from_id in from_room_ids:
                if from_id in graph.nodes():
                    neighbors = set(graph.neighbors(from_id))
                    if any(to_id in neighbors for to_id in to_room_ids):
                        has_connection = True
                        break
            
            if not has_connection and adj_req.required:
                result["program_issues"].append(make_issue(
                    code="PROGRAM_REQUIRED_ADJACENCY_MISSING",
                    severity="warning",
                    entity_refs=[
                        {"type": "adjacency_requirement", "id": adj_req.id},
                    ],
                    message=f"Required direct adjacency missing: '{from_type}' should be adjacent to '{to_type}'",
                ))
                result["program_summary"]["issues_count"] += 1
        
        elif adj_type == "separated":
            # Check that no from_room is directly connected to any to_room
            has_forbidden_connection = False
            for from_id in from_room_ids:
                if from_id in graph.nodes():
                    neighbors = set(graph.neighbors(from_id))
                    if any(to_id in neighbors for to_id in to_room_ids):
                        has_forbidden_connection = True
                        break
            
            if has_forbidden_connection and adj_req.required:
                result["program_issues"].append(make_issue(
                    code="PROGRAM_FORBIDDEN_ADJACENCY_EXISTS",
                    severity="warning",
                    entity_refs=[
                        {"type": "adjacency_requirement", "id": adj_req.id},
                    ],
                    message=f"Forbidden adjacency exists: '{from_type}' should NOT be adjacent to '{to_type}'",
                ))
                result["program_summary"]["issues_count"] += 1
        
        elif adj_type == "near":
            # Near adjacency requires distance calculation - unsupported in MVP 7
            result["program_summary"]["unsupported_checks"].append(f"adjacency:near:{from_type}:{to_type}")
            result["program_issues"].append(make_issue(
                code="PROGRAM_UNSUPPORTED_ADJACENCY_TYPE",
                severity="info",
                entity_refs=[{"type": "adjacency_requirement", "id": adj_req.id}],
                message=f"Adjacency type 'near' is not supported in MVP 7: '{from_type}' to '{to_type}'",
            ))
    
    return result
