"""Program validation logic for Floor Plan Engine.

MVP 7: RoomProgram v1 validation
Compares actual plan against room program requirements.
"""

from typing import List, Dict, Set, Tuple, Optional
from app.models import Plan, Room
from app.room_program import RoomProgram, RoomRequirement, infer_room_type
from app.issues import make_issue
from app.connectivity import build_room_graph
from app.geometry import calculate_polygon_area_m2


def extract_room_types_from_plan(plan: Plan) -> Dict[str, List[Room]]:
    """Extract rooms grouped by inferred type from plan.
    
    Returns a dict mapping room_type -> list of matching Room objects.
    """
    rooms_by_type: Dict[str, List[Room]] = {}
    
    for room in plan.rooms:
        inferred_type = infer_room_type(room.id, room.name)
        if inferred_type not in rooms_by_type:
            rooms_by_type[inferred_type] = []
        rooms_by_type[inferred_type].append(room)
    
    return rooms_by_type


def check_missing_required_rooms(
    program: RoomProgram,
    rooms_by_type: Dict[str, List[Room]]
) -> List[Dict]:
    """Check for missing required rooms.
    
    Returns list of issue dicts for missing required room types.
    """
    issues = []
    
    for req in program.requirements:
        if not req.required:
            continue
        
        available_count = len(rooms_by_type.get(req.room_type, []))
        required_count = req.quantity
        
        if available_count < required_count:
            missing_count = required_count - available_count
            issue = make_issue(
                code="PROGRAM_MISSING_REQUIRED_ROOM",
                message=f"Missing {missing_count} required room(s) of type '{req.room_type}' (required: {required_count}, found: {available_count})",
                severity="error",
                category="area",
                entity_refs=[{"type": "program_requirement", "id": req.id}],
                consequence=f"Program requires {required_count} {req.room_type}(s) but only {available_count} present",
                confidence="high",
                fixability="operation_candidate_possible",
            )
            issues.append(issue)
    
    return issues


def check_area_mismatches(
    program: RoomProgram,
    rooms_by_type: Dict[str, List[Room]]
) -> List[Dict]:
    """Check for room area mismatches against program requirements.
    
    Returns list of issue dicts for area violations.
    """
    issues = []
    
    for req in program.requirements:
        matching_rooms = rooms_by_type.get(req.room_type, [])
        
        for i, room in enumerate(matching_rooms):
            try:
                room_area = calculate_polygon_area_m2(room.polygon_mm)
            except Exception:
                continue
            
            # Check minimum area
            if req.min_area_m2 is not None and room_area < req.min_area_m2:
                issue = make_issue(
                    code="PROGRAM_AREA_BELOW_MINIMUM",
                    message=f"Room '{room.name}' ({room.id}) area {room_area:.1f} m² below minimum {req.min_area_m2} m²",
                    severity="warning",
                    category="area",
                    entity_refs=[
                        {"type": "room", "id": room.id},
                        {"type": "program_requirement", "id": req.id}
                    ],
                    consequence=f"Room does not meet program minimum area requirement",
                    confidence="high",
                    fixability="operation_candidate_possible",
                )
                issues.append(issue)
            
            # Check maximum area
            if req.max_area_m2 is not None and room_area > req.max_area_m2:
                issue = make_issue(
                    code="PROGRAM_AREA_ABOVE_MAXIMUM",
                    message=f"Room '{room.name}' ({room.id}) area {room_area:.1f} m² exceeds maximum {req.max_area_m2} m²",
                    severity="warning",
                    category="area",
                    entity_refs=[
                        {"type": "room", "id": room.id},
                        {"type": "program_requirement", "id": req.id}
                    ],
                    consequence=f"Room exceeds program maximum area requirement",
                    confidence="high",
                    fixability="operation_candidate_possible",
                )
                issues.append(issue)
    
    return issues


def check_adjacency_requirements(
    program: RoomProgram,
    plan: Plan,
    rooms_by_type: Dict[str, List[Room]]
) -> List[Dict]:
    """Check for required and forbidden adjacencies.
    
    Returns list of issue dicts for adjacency violations.
    """
    issues = []
    
    # Build connectivity for adjacency checking
    graph = build_room_graph(plan)
    room_id_to_obj = {room.id: room for room in plan.rooms}
    room_id_to_type = {room.id: infer_room_type(room.id, room.name) for room in plan.rooms}
    
    for req in program.requirements:
        matching_rooms = rooms_by_type.get(req.room_type, [])
        
        for room in matching_rooms:
            room_id = room.id
            adjacent_room_ids = set(graph.neighbors(room_id)) if room_id in graph else set()
            adjacent_types = set(
                room_id_to_type.get(adj_id, "unknown")
                for adj_id in adjacent_room_ids
            )
            
            # Check required adjacencies
            for required_type in req.required_adjacencies:
                if required_type not in adjacent_types:
                    issue = make_issue(
                        code="PROGRAM_REQUIRED_ADJACENCY_MISSING",
                        message=f"Room '{room.name}' ({room_id}) missing required adjacency to '{required_type}'",
                        severity="warning",
                        category="connectivity",
                        entity_refs=[
                            {"type": "room", "id": room_id},
                            {"type": "program_requirement", "id": req.id}
                        ],
                        consequence=f"Program requires {req.room_type} to be adjacent to {required_type}",
                        confidence="high",
                        fixability="operation_candidate_possible",
                    )
                    issues.append(issue)
            
            # Check forbidden adjacencies
            for forbidden_type in req.forbidden_adjacencies:
                if forbidden_type in adjacent_types:
                    issue = make_issue(
                        code="PROGRAM_FORBIDDEN_ADJACENCY_PRESENT",
                        message=f"Room '{room.name}' ({room_id}) has forbidden adjacency to '{forbidden_type}'",
                        severity="warning",
                        category="connectivity",
                        entity_refs=[
                            {"type": "room", "id": room_id},
                            {"type": "program_requirement", "id": req.id}
                        ],
                        consequence=f"Program forbids {req.room_type} adjacency to {forbidden_type}",
                        confidence="high",
                        fixability="operation_candidate_possible",
                    )
                    issues.append(issue)
    
    return issues


def validate_program_against_plan(program: RoomProgram, plan: Plan) -> Dict:
    """Validate a plan against a room program.
    
    Returns a dict with:
    - program: the input program
    - program_issues: list of issue dicts
    - matched_requirements: list of satisfied requirements
    - total_area_m2: calculated total area
    """
    rooms_by_type = extract_room_types_from_plan(plan)
    
    # Collect all issues
    all_issues = []
    all_issues.extend(check_missing_required_rooms(program, rooms_by_type))
    all_issues.extend(check_area_mismatches(program, rooms_by_type))
    all_issues.extend(check_adjacency_requirements(program, plan, rooms_by_type))
    
    # Calculate total area using proper polygon area calculation
    total_area_m2 = 0
    for room in plan.rooms:
        try:
            area_m2 = calculate_polygon_area_m2(room.polygon_mm)
            total_area_m2 += area_m2
        except Exception:
            pass
    
    # Count matched requirements
    matched = []
    for req in program.requirements:
        available = len(rooms_by_type.get(req.room_type, []))
        if available >= req.quantity:
            matched.append({
                "requirement_id": req.id,
                "room_type": req.room_type,
                "required": req.quantity,
                "available": available
            })
    
    return {
        "program": program.model_dump(),
        "program_issues": all_issues,
        "matched_requirements": matched,
        "total_area_m2": round(total_area_m2, 2),
    }
