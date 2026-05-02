"""Constraint validation service for Floor Plan Engine.

MVP 5: Validates PlanningConstraints against a Plan.
"""

from typing import List, Dict, Any, Optional
from app.models import Plan, Room
from app.constraints import PlanningConstraint, priority_to_severity, is_valid_constraint_type
from app.connectivity import build_room_graph, get_entry_room_ids, infer_room_type
from app.geometry import calculate_polygon_area_m2
from app.issues import make_issue


def validate_constraints(plan: Plan, constraints: List[PlanningConstraint]) -> Dict[str, Any]:
    """Validate a list of constraints against a plan.
    
    Returns:
        {
            "constraint_violations": [...],
            "constraints_summary": {
                "total": int,
                "violated": int,
                "by_priority": {"must": int, "should": int, "nice_to_have": int}
            }
        }
    """
    violations = []
    summary = {
        "total": len(constraints),
        "violated": 0,
        "by_priority": {"must": 0, "should": 0, "nice_to_have": 0},
    }
    
    # Build room graph once
    room_graph = build_room_graph(plan)
    entry_room_ids = get_entry_room_ids(plan)
    
    # Build room lookup
    room_by_id = {room.id: room for room in plan.rooms}
    
    for constraint in constraints:
        # Check for invalid definition first
        if not is_valid_constraint_type(constraint.constraint_type):
            issue = make_issue(
                code="CONSTRAINT_INVALID_DEFINITION",
                severity="warning",
                entity_refs=[{"type": "constraint", "id": constraint.id}],
                message=f"Invalid constraint type: {constraint.constraint_type}",
            )
            violations.append(issue)
            continue
        
        # Validate based on constraint type
        constraint_violations = _validate_single_constraint(
            constraint, plan, room_by_id, room_graph, entry_room_ids
        )
        
        for violation in constraint_violations:
            violations.append(violation)
            # Count by priority
            priority = constraint.priority
            if priority in summary["by_priority"]:
                summary["by_priority"][priority] += 1
        
        summary["violated"] = len([v for v in violations if v.get("code", "").startswith("CONSTRAINT_")])
    
    return {
        "constraint_violations": violations,
        "constraints_summary": summary,
    }


def _validate_single_constraint(
    constraint: PlanningConstraint,
    plan: Plan,
    room_by_id: Dict[str, Room],
    room_graph,
    entry_room_ids: List[str],
) -> List[Dict[str, Any]]:
    """Validate a single constraint and return list of violation issues."""
    violations = []
    
    if constraint.constraint_type == "min_area":
        violations.extend(_validate_min_area(constraint, plan, room_by_id))
    
    elif constraint.constraint_type == "max_area":
        violations.extend(_validate_max_area(constraint, plan, room_by_id))
    
    elif constraint.constraint_type == "required_connection":
        violations.extend(_validate_required_connection(constraint, plan, room_by_id, room_graph))
    
    elif constraint.constraint_type == "forbidden_connection":
        violations.extend(_validate_forbidden_connection(constraint, plan, room_by_id, room_graph))
    
    elif constraint.constraint_type == "required_room_type":
        violations.extend(_validate_required_room_type(constraint, plan, room_by_id))
    
    elif constraint.constraint_type == "required_access_from_entry":
        violations.extend(_validate_required_access_from_entry(constraint, plan, room_by_id, room_graph, entry_room_ids))
    
    return violations


def _validate_min_area(
    constraint: PlanningConstraint,
    plan: Plan,
    room_by_id: Dict[str, Room],
) -> List[Dict[str, Any]]:
    """Validate min_area constraint."""
    violations = []
    severity = priority_to_severity(constraint.priority)
    
    target_rooms = _get_target_rooms(constraint, room_by_id)
    
    for room in target_rooms:
        try:
            area = calculate_polygon_area_m2(room.polygon_mm)
        except (ValueError, Exception):
            continue  # Invalid polygon handled elsewhere
        
        if constraint.min_area_m2 is not None and area < constraint.min_area_m2:
            issue = make_issue(
                code="CONSTRAINT_MIN_AREA_VIOLATION",
                severity=severity,
                entity_refs=[
                    {"type": "room", "id": room.id},
                    {"type": "constraint", "id": constraint.id},
                ],
                message=f"Room '{room.id}' area ({area:.2f} m²) is below minimum ({constraint.min_area_m2} m²)",
                consequence="Project requirement not met",
            )
            issue["meta"] = {
                "area_m2": round(area, 2),
                "min_area_m2": constraint.min_area_m2,
                "constraint_id": constraint.id,
            }
            violations.append(issue)
    
    return violations


def _validate_max_area(
    constraint: PlanningConstraint,
    plan: Plan,
    room_by_id: Dict[str, Room],
) -> List[Dict[str, Any]]:
    """Validate max_area constraint."""
    violations = []
    severity = priority_to_severity(constraint.priority)
    
    target_rooms = _get_target_rooms(constraint, room_by_id)
    
    for room in target_rooms:
        try:
            area = calculate_polygon_area_m2(room.polygon_mm)
        except (ValueError, Exception):
            continue
        
        if constraint.max_area_m2 is not None and area > constraint.max_area_m2:
            issue = make_issue(
                code="CONSTRAINT_MAX_AREA_VIOLATION",
                severity=severity,
                entity_refs=[
                    {"type": "room", "id": room.id},
                    {"type": "constraint", "id": constraint.id},
                ],
                message=f"Room '{room.id}' area ({area:.2f} m²) exceeds maximum ({constraint.max_area_m2} m²)",
                consequence="Project requirement not met",
            )
            issue["meta"] = {
                "area_m2": round(area, 2),
                "max_area_m2": constraint.max_area_m2,
                "constraint_id": constraint.id,
            }
            violations.append(issue)
    
    return violations


def _validate_required_connection(
    constraint: PlanningConstraint,
    plan: Plan,
    room_by_id: Dict[str, Room],
    room_graph,
) -> List[Dict[str, Any]]:
    """Validate required_connection constraint."""
    violations = []
    severity = priority_to_severity(constraint.priority)
    
    # Check if targets exist
    if constraint.room_id and constraint.room_id not in room_by_id:
        issue = make_issue(
            code="CONSTRAINT_TARGET_NOT_FOUND",
            severity="warning",
            entity_refs=[{"type": "constraint", "id": constraint.id}],
            message=f"Constraint targets non-existent room: {constraint.room_id}",
        )
        return [issue]
    
    if constraint.target_room_id and constraint.target_room_id not in room_by_id:
        issue = make_issue(
            code="CONSTRAINT_TARGET_NOT_FOUND",
            severity="warning",
            entity_refs=[{"type": "constraint", "id": constraint.id}],
            message=f"Constraint targets non-existent room: {constraint.target_room_id}",
        )
        return [issue]
    
    # Specific room-to-room connection
    if constraint.room_id and constraint.target_room_id:
        has_connection = room_graph.has_edge(constraint.room_id, constraint.target_room_id)
        if not has_connection:
            issue = make_issue(
                code="CONSTRAINT_REQUIRED_CONNECTION_MISSING",
                severity=severity,
                entity_refs=[
                    {"type": "room", "id": constraint.room_id},
                    {"type": "room", "id": constraint.target_room_id},
                    {"type": "constraint", "id": constraint.id},
                ],
                message=f"Required connection missing between '{constraint.room_id}' and '{constraint.target_room_id}'",
                consequence="Project requirement not met",
            )
            violations.append(issue)
    
    # Type-to-type connection
    elif constraint.room_type and constraint.target_room_type:
        found = False
        for room in plan.rooms:
            if infer_room_type(room) == constraint.room_type:
                for neighbor in room_graph.neighbors(room.id):
                    neighbor_room = room_by_id.get(neighbor)
                    if neighbor_room and infer_room_type(neighbor_room) == constraint.target_room_type:
                        found = True
                        break
            if found:
                break
        
        if not found:
            issue = make_issue(
                code="CONSTRAINT_REQUIRED_CONNECTION_MISSING",
                severity=severity,
                entity_refs=[{"type": "constraint", "id": constraint.id}],
                message=f"Required connection missing between {constraint.room_type} and {constraint.target_room_type} rooms",
                consequence="Project requirement not met",
            )
            violations.append(issue)
    
    return violations


def _validate_forbidden_connection(
    constraint: PlanningConstraint,
    plan: Plan,
    room_by_id: Dict[str, Room],
    room_graph,
) -> List[Dict[str, Any]]:
    """Validate forbidden_connection constraint."""
    violations = []
    severity = priority_to_severity(constraint.priority)
    
    # Check if targets exist
    if constraint.room_id and constraint.room_id not in room_by_id:
        issue = make_issue(
            code="CONSTRAINT_TARGET_NOT_FOUND",
            severity="warning",
            entity_refs=[{"type": "constraint", "id": constraint.id}],
            message=f"Constraint targets non-existent room: {constraint.room_id}",
        )
        return [issue]
    
    if constraint.target_room_id and constraint.target_room_id not in room_by_id:
        issue = make_issue(
            code="CONSTRAINT_TARGET_NOT_FOUND",
            severity="warning",
            entity_refs=[{"type": "constraint", "id": constraint.id}],
            message=f"Constraint targets non-existent room: {constraint.target_room_id}",
        )
        return [issue]
    
    # Specific room-to-room connection
    if constraint.room_id and constraint.target_room_id:
        has_connection = room_graph.has_edge(constraint.room_id, constraint.target_room_id)
        if has_connection:
            issue = make_issue(
                code="CONSTRAINT_FORBIDDEN_CONNECTION_EXISTS",
                severity=severity,
                entity_refs=[
                    {"type": "room", "id": constraint.room_id},
                    {"type": "room", "id": constraint.target_room_id},
                    {"type": "constraint", "id": constraint.id},
                ],
                message=f"Forbidden connection exists between '{constraint.room_id}' and '{constraint.target_room_id}'",
                consequence="Project requirement violated",
            )
            violations.append(issue)
    
    # Type-to-type connection
    elif constraint.room_type and constraint.target_room_type:
        for room in plan.rooms:
            if infer_room_type(room) == constraint.room_type:
                for neighbor in room_graph.neighbors(room.id):
                    neighbor_room = room_by_id.get(neighbor)
                    if neighbor_room and infer_room_type(neighbor_room) == constraint.target_room_type:
                        issue = make_issue(
                            code="CONSTRAINT_FORBIDDEN_CONNECTION_EXISTS",
                            severity=severity,
                            entity_refs=[
                                {"type": "room", "id": room.id},
                                {"type": "room", "id": neighbor},
                                {"type": "constraint", "id": constraint.id},
                            ],
                            message=f"Forbidden connection exists between {constraint.room_type} and {constraint.target_room_type} rooms",
                            consequence="Project requirement violated",
                        )
                        violations.append(issue)
                        break
    
    return violations


def _validate_required_room_type(
    constraint: PlanningConstraint,
    plan: Plan,
    room_by_id: Dict[str, Room],
) -> List[Dict[str, Any]]:
    """Validate required_room_type constraint."""
    violations = []
    severity = priority_to_severity(constraint.priority)
    
    if not constraint.room_type:
        issue = make_issue(
            code="CONSTRAINT_INVALID_DEFINITION",
            severity="warning",
            entity_refs=[{"type": "constraint", "id": constraint.id}],
            message="required_room_type constraint requires room_type field",
        )
        return [issue]
    
    # Count rooms of the required type
    matching_rooms = [room for room in plan.rooms if infer_room_type(room) == constraint.room_type]
    
    if len(matching_rooms) < constraint.count:
        issue = make_issue(
            code="CONSTRAINT_REQUIRED_ROOM_TYPE_MISSING",
            severity=severity,
            entity_refs=[{"type": "constraint", "id": constraint.id}],
            message=f"Required {constraint.count} room(s) of type '{constraint.room_type}', found {len(matching_rooms)}",
            consequence="Project requirement not met",
        )
        violations.append(issue)
    
    return violations


def _validate_required_access_from_entry(
    constraint: PlanningConstraint,
    plan: Plan,
    room_by_id: Dict[str, Room],
    room_graph,
    entry_room_ids: List[str],
) -> List[Dict[str, Any]]:
    """Validate required_access_from_entry constraint."""
    violations = []
    severity = priority_to_severity(constraint.priority)
    
    # No entry rooms
    if not entry_room_ids:
        issue = make_issue(
            code="CONSTRAINT_REQUIRED_ACCESS_FROM_ENTRY_MISSING",
            severity=severity,
            entity_refs=[{"type": "constraint", "id": constraint.id}],
            message="No entry room available to check access from",
            consequence="Cannot validate access requirement",
        )
        return [issue]
    
    target_rooms = _get_target_rooms(constraint, room_by_id)
    
    for room in target_rooms:
        # Check if reachable from any entry room
        is_reachable = False
        for entry_id in entry_room_ids:
            try:
                if entry_id in room_graph and room.id in room_graph:
                    if entry_id == room.id or room_graph.has_path(entry_id, room.id):
                        is_reachable = True
                        break
            except Exception:
                continue
        
        if not is_reachable:
            issue = make_issue(
                code="CONSTRAINT_REQUIRED_ACCESS_FROM_ENTRY_MISSING",
                severity=severity,
                entity_refs=[
                    {"type": "room", "id": room.id},
                    {"type": "constraint", "id": constraint.id},
                ],
                message=f"Room '{room.id}' is not accessible from any entry room",
                consequence="Room is not accessible as required",
            )
            violations.append(issue)
    
    return violations


def _get_target_rooms(constraint: PlanningConstraint, room_by_id: Dict[str, Room]) -> List[Room]:
    """Get list of rooms targeted by a constraint."""
    target_rooms = []
    
    if constraint.room_id:
        if constraint.room_id in room_by_id:
            target_rooms = [room_by_id[constraint.room_id]]
    elif constraint.room_type:
        target_rooms = [room for room in room_by_id.values() if infer_room_type(room) == constraint.room_type]
    
    return target_rooms
