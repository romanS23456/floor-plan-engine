"""RoomProgram validation service for Floor Plan Engine.

Validates a Plan against a RoomProgram to check if the plan meets
the expected room composition and adjacency requirements.
"""

from typing import List, Dict, Any, Optional, Set
from app.models import Plan, Room
from app.room_program import RoomProgram, RoomRequirement, AdjacencyRequirement
from app.connectivity import infer_room_type, build_room_graph
from app.geometry import calculate_polygon_area_m2
from app.issues import make_issue


def _match_room_to_requirement(room: Room, requirement: RoomRequirement) -> bool:
    """Check if a room matches a room requirement.
    
    Matches by:
    1. Exact room_type match
    2. Loose matching by room id/name keywords
    """
    # Direct room_type match
    if room.room_type and room.room_type == requirement.room_type:
        return True
    
    # Loose matching by id/name
    identifier = f"{room.id} {room.name}".lower()
    room_type_lower = requirement.room_type.lower()
    
    # Kitchen mapping
    if room_type_lower in ["kitchen", "public"]:
        if any(kw in identifier for kw in ["kitchen"]):
            return True
    
    # Living/public mapping
    if room_type_lower in ["living", "public"]:
        if any(kw in identifier for kw in ["living", "dining"]):
            return True
    
    # Private/bedroom mapping
    if room_type_lower in ["private", "bedroom"]:
        if any(kw in identifier for kw in ["bedroom", "master", "guest", "child"]):
            return True
    
    # Bathroom mapping
    if room_type_lower in ["bathroom"]:
        if any(kw in identifier for kw in ["bathroom", "wc", "toilet"]):
            return True
    
    # Pantry/storage mapping
    if room_type_lower in ["pantry", "storage"]:
        if any(kw in identifier for kw in ["pantry", "storage"]):
            return True
    
    # Hall/entry mapping
    if room_type_lower in ["hall", "entry"]:
        if any(kw in identifier for kw in ["hall", "corridor", "entry", "entrance"]):
            return True
    
    return False


def _count_rooms_for_requirement(plan: Plan, requirement: RoomRequirement) -> List[Room]:
    """Count rooms that match a requirement."""
    matching_rooms = []
    for room in plan.rooms:
        if _match_room_to_requirement(room, requirement):
            matching_rooms.append(room)
    return matching_rooms


def _rooms_have_direct_adjacency(
    plan: Plan, 
    from_room_type: str, 
    to_room_type: str
) -> bool:
    """Check if any room of from_room_type directly connects to any room of to_room_type."""
    graph = build_room_graph(plan)
    
    # Get rooms of each type
    from_rooms: Set[str] = set()
    to_rooms: Set[str] = set()
    
    for room in plan.rooms:
        inferred_type = infer_room_type(room)
        # Match by exact type or loose matching
        if room.room_type == from_room_type or inferred_type == from_room_type:
            from_rooms.add(room.id)
        if room.room_type == to_room_type or inferred_type == to_room_type:
            to_rooms.add(room.id)
        
        # Also try loose matching for common types
        if from_room_type.lower() in ["public", "kitchen"]:
            if "kitchen" in f"{room.id} {room.name}".lower():
                from_rooms.add(room.id)
        if to_room_type.lower() in ["public", "kitchen"]:
            if "kitchen" in f"{room.id} {room.name}".lower():
                to_rooms.add(room.id)
                
        if from_room_type.lower() in ["public", "living"]:
            if "living" in f"{room.id} {room.name}".lower() or "dining" in f"{room.id} {room.name}".lower():
                from_rooms.add(room.id)
        if to_room_type.lower() in ["public", "living"]:
            if "living" in f"{room.id} {room.name}".lower() or "dining" in f"{room.id} {room.name}".lower():
                to_rooms.add(room.id)
    
    # Check if any from_room is connected to any to_room
    for from_room_id in from_rooms:
        if from_room_id not in graph.nodes():
            continue
        for neighbor in graph.neighbors(from_room_id):
            if neighbor in to_rooms:
                return True
    
    return False


def validate_room_program(plan: Plan, room_program: RoomProgram) -> Dict[str, Any]:
    """Validate a Plan against a RoomProgram.
    
    Returns:
        dict with:
        - program_summary: counts and summary info
        - program_issues: list of ValidationIssue dicts
    """
    issues: List[Dict[str, Any]] = []
    matched_room_types: List[str] = []
    missing_room_types: List[str] = []
    unsupported_checks: List[str] = []
    requirements_checked = 0
    
    # 1. Empty program check
    if not room_program.requirements and not room_program.adjacency_requirements:
        issues.append(make_issue(
            code="PROGRAM_EMPTY",
            severity="info",
            entity_refs=[],
            message="Room program is empty (no requirements defined)",
            consequence="No program validation can be performed"
        ))
        return {
            "program_summary": {
                "requirements_total": 0,
                "requirements_checked": 0,
                "issues_count": len(issues),
                "matched_room_types": [],
                "missing_room_types": [],
                "unsupported_checks": []
            },
            "program_issues": issues
        }
    
    requirements_total = len(room_program.requirements) + len(room_program.adjacency_requirements)
    
    # 2. Required room type count validation
    for req in room_program.requirements:
        # Check for invalid requirement
        if not req.room_type or req.min_count < 0:
            issues.append(make_issue(
                code="PROGRAM_INVALID_REQUIREMENT",
                severity="warning",
                entity_refs=[],
                message=f"Invalid requirement: {req.id}",
                consequence="Requirement cannot be validated"
            ))
            continue
        
        requirements_checked += 1
        matching_rooms = _count_rooms_for_requirement(plan, req)
        count = len(matching_rooms)
        
        # Track matched types
        if count > 0:
            matched_room_types.append(req.room_type)
        
        # Check minimum count
        if req.required and count < req.min_count:
            if count == 0:
                issues.append(make_issue(
                    code="PROGRAM_REQUIRED_ROOM_TYPE_MISSING",
                    severity="warning",
                    entity_refs=[{"type": "room_requirement", "id": req.id}],
                    message=f"Required room type '{req.room_type}' is missing",
                    consequence="Plan does not meet program requirements"
                ))
                missing_room_types.append(req.room_type)
            else:
                issues.append(make_issue(
                    code="PROGRAM_TOO_FEW_ROOMS_OF_TYPE",
                    severity="warning",
                    entity_refs=[{"type": "room_requirement", "id": req.id}],
                    message=f"Only {count} room(s) of type '{req.room_type}' found, minimum required is {req.min_count}",
                    consequence="Plan does not meet program quantity requirements"
                ))
        
        # Check maximum count
        if req.max_count is not None and count > req.max_count:
            issues.append(make_issue(
                code="PROGRAM_TOO_MANY_ROOMS_OF_TYPE",
                severity="info",
                entity_refs=[{"type": "room_requirement", "id": req.id}],
                message=f"{count} room(s) of type '{req.room_type}' found, maximum allowed is {req.max_count}",
                consequence="Plan exceeds program quantity limits"
            ))
        
        # 3. Area checks for matching rooms
        for room in matching_rooms:
            area = calculate_polygon_area_m2(room.polygon_mm)
            
            # Min area check
            if req.min_area_m2 is not None and area < req.min_area_m2:
                issues.append(make_issue(
                    code="PROGRAM_ROOM_AREA_BELOW_MINIMUM",
                    severity="warning",
                    entity_refs=[{"type": "room", "id": room.id}],
                    message=f"Room '{room.name}' ({room.id}) has area {area:.1f} m², below minimum {req.min_area_m2} m²",
                    consequence="Room does not meet program size requirements"
                ))
            
            # Max area check
            if req.max_area_m2 is not None and area > req.max_area_m2:
                issues.append(make_issue(
                    code="PROGRAM_ROOM_AREA_ABOVE_MAXIMUM",
                    severity="info",
                    entity_refs=[{"type": "room", "id": room.id}],
                    message=f"Room '{room.name}' ({room.id}) has area {area:.1f} m², above maximum {req.max_area_m2} m²",
                    consequence="Room exceeds program size limits"
                ))
            
            # Target area check (20% tolerance)
            if req.target_area_m2 is not None:
                diff_ratio = abs(area - req.target_area_m2) / req.target_area_m2
                if diff_ratio > 0.20:
                    issues.append(make_issue(
                        code="PROGRAM_TARGET_AREA_MISMATCH",
                        severity="info",
                        entity_refs=[{"type": "room", "id": room.id}],
                        message=f"Room '{room.name}' ({room.id}) has area {area:.1f} m², differs from target {req.target_area_m2} m² by {diff_ratio*100:.0f}%",
                        consequence="Room size may not match program intent"
                    ))
    
    # 4. Adjacency validation
    for adj_req in room_program.adjacency_requirements:
        # Check for invalid requirement
        if not adj_req.from_room_type or not adj_req.to_room_type:
            issues.append(make_issue(
                code="PROGRAM_INVALID_REQUIREMENT",
                severity="warning",
                entity_refs=[],
                message=f"Invalid adjacency requirement: {adj_req.id}",
                consequence="Requirement cannot be validated"
            ))
            continue
        
        requirements_checked += 1
        
        # Handle different adjacency types
        if adj_req.adjacency_type == "near":
            # Near is not supported yet
            unsupported_checks.append(f"near adjacency: {adj_req.from_room_type} to {adj_req.to_room_type}")
            issues.append(make_issue(
                code="PROGRAM_UNSUPPORTED_ADJACENCY_TYPE",
                severity="info",
                entity_refs=[{"type": "adjacency_requirement", "id": adj_req.id}],
                message=f"'near' adjacency type not yet supported for {adj_req.from_room_type} to {adj_req.to_room_type}",
                consequence="Adjacency requirement cannot be validated"
            ))
        
        elif adj_req.adjacency_type == "direct":
            has_adjacency = _rooms_have_direct_adjacency(
                plan, adj_req.from_room_type, adj_req.to_room_type
            )
            
            if adj_req.required and not has_adjacency:
                issues.append(make_issue(
                    code="PROGRAM_REQUIRED_ADJACENCY_MISSING",
                    severity="warning",
                    entity_refs=[{"type": "adjacency_requirement", "id": adj_req.id}],
                    message=f"Required direct adjacency missing: {adj_req.from_room_type} should connect to {adj_req.to_room_type}",
                    consequence="Plan does not meet program adjacency requirements"
                ))
        
        elif adj_req.adjacency_type == "separated":
            has_adjacency = _rooms_have_direct_adjacency(
                plan, adj_req.from_room_type, adj_req.to_room_type
            )
            
            if has_adjacency:
                issues.append(make_issue(
                    code="PROGRAM_FORBIDDEN_ADJACENCY_EXISTS",
                    severity="warning",
                    entity_refs=[{"type": "adjacency_requirement", "id": adj_req.id}],
                    message=f"Forbidden adjacency exists: {adj_req.from_room_type} should be separated from {adj_req.to_room_type}",
                    consequence="Plan violates program separation requirements"
                ))
    
    return {
        "program_summary": {
            "requirements_total": requirements_total,
            "requirements_checked": requirements_checked,
            "issues_count": len(issues),
            "matched_room_types": matched_room_types,
            "missing_room_types": missing_room_types,
            "unsupported_checks": unsupported_checks
        },
        "program_issues": issues
    }
