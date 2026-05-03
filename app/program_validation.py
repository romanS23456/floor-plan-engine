"""RoomProgram validation logic for Floor Plan Engine.

MVP 7: compare actual Plan rooms against structured RoomProgram requirements.
"""

from typing import Dict, List, Set

from app.connectivity import build_room_graph
from app.geometry import calculate_polygon_area_m2
from app.issues import make_issue
from app.models import Plan, Room
from app.room_program import RoomProgram, RoomRequirement, infer_program_room_type


def extract_room_types_from_plan(plan: Plan) -> Dict[str, List[Room]]:
    """Group plan rooms by normalized room type."""

    rooms_by_type: Dict[str, List[Room]] = {}

    for room in plan.rooms:
        room_type = infer_program_room_type(
            room_id=room.id,
            room_name=room.name,
            explicit_room_type=room.room_type,
        )
        rooms_by_type.setdefault(room_type, []).append(room)

    return rooms_by_type


def check_missing_required_rooms(
    program: RoomProgram,
    rooms_by_type: Dict[str, List[Room]],
) -> List[Dict]:
    """Detect missing required room types or insufficient required quantity."""

    issues: List[Dict] = []

    for requirement in program.requirements:
        if not requirement.required:
            continue

        available_count = len(rooms_by_type.get(requirement.room_type, []))

        if available_count < requirement.quantity:
            missing_count = requirement.quantity - available_count
            issues.append(
                make_issue(
                    code="PROGRAM_MISSING_REQUIRED_ROOM",
                    severity="error",
                    category="area",
                    entity_refs=[{"type": "program_requirement", "id": requirement.id}],
                    message=(
                        f"Room program requires {requirement.quantity} room(s) of type "
                        f"'{requirement.room_type}', but plan has {available_count}. "
                        f"Missing: {missing_count}."
                    ),
                    consequence="Plan does not satisfy required room composition.",
                    confidence="high",
                    fixability="operation_candidate_possible",
                    source="program_validation",
                )
            )

    return issues


def _room_area_m2(room: Room) -> float:
    """Calculate room area in square meters from polygon_mm."""

    return calculate_polygon_area_m2(room.polygon_mm)


def check_area_mismatches(
    program: RoomProgram,
    rooms_by_type: Dict[str, List[Room]],
) -> List[Dict]:
    """Detect room area violations against min/max program requirements."""

    issues: List[Dict] = []

    for requirement in program.requirements:
        matching_rooms = rooms_by_type.get(requirement.room_type, [])

        for room in matching_rooms:
            room_area = _room_area_m2(room)

            if requirement.min_area_m2 is not None and room_area < requirement.min_area_m2:
                issues.append(
                    make_issue(
                        code="PROGRAM_AREA_BELOW_MINIMUM",
                        severity="warning",
                        category="area",
                        entity_refs=[
                            {"type": "room", "id": room.id},
                            {"type": "program_requirement", "id": requirement.id},
                        ],
                        message=(
                            f"Room '{room.name}' area is {room_area:.2f} m², "
                            f"below program minimum {requirement.min_area_m2:.2f} m²."
                        ),
                        consequence="Room may be too small for the intended program.",
                        confidence="high",
                        fixability="operation_candidate_possible",
                        source="program_validation",
                    )
                )

            if requirement.max_area_m2 is not None and room_area > requirement.max_area_m2:
                issues.append(
                    make_issue(
                        code="PROGRAM_AREA_ABOVE_MAXIMUM",
                        severity="warning",
                        category="area",
                        entity_refs=[
                            {"type": "room", "id": room.id},
                            {"type": "program_requirement", "id": requirement.id},
                        ],
                        message=(
                            f"Room '{room.name}' area is {room_area:.2f} m², "
                            f"above program maximum {requirement.max_area_m2:.2f} m²."
                        ),
                        consequence="Room may exceed the intended program area.",
                        confidence="high",
                        fixability="operation_candidate_possible",
                        source="program_validation",
                    )
                )

    return issues


def _adjacent_room_types_for_room(plan: Plan, room: Room) -> Set[str]:
    """Return normalized room types adjacent to a room through doors."""

    graph = build_room_graph(plan)
    adjacent_room_types: Set[str] = []

    if room.id not in graph:
        return set()

    rooms_by_id = {candidate.id: candidate for candidate in plan.rooms}

    result: Set[str] = set()
    for adjacent_room_id in graph.neighbors(room.id):
        adjacent_room = rooms_by_id.get(adjacent_room_id)
        if adjacent_room is None:
            continue

        result.add(
            infer_program_room_type(
                room_id=adjacent_room.id,
                room_name=adjacent_room.name,
                explicit_room_type=adjacent_room.room_type,
            )
        )

    return result


def check_adjacency_requirements(
    program: RoomProgram,
    plan: Plan,
    rooms_by_type: Dict[str, List[Room]],
) -> List[Dict]:
    """Detect required and forbidden adjacency violations."""

    issues: List[Dict] = []

    for requirement in program.requirements:
        matching_rooms = rooms_by_type.get(requirement.room_type, [])

        for room in matching_rooms:
            adjacent_types = _adjacent_room_types_for_room(plan, room)

            for required_type in requirement.required_adjacencies:
                if required_type not in adjacent_types:
                    issues.append(
                        make_issue(
                            code="PROGRAM_REQUIRED_ADJACENCY_MISSING",
                            severity="warning",
                            category="connectivity",
                            entity_refs=[
                                {"type": "room", "id": room.id},
                                {"type": "program_requirement", "id": requirement.id},
                            ],
                            message=(
                                f"Room '{room.name}' must be adjacent to "
                                f"'{required_type}' by room program, but it is not."
                            ),
                            consequence="Required room relationship is missing.",
                            confidence="high",
                            fixability="operation_candidate_possible",
                            source="program_validation",
                        )
                    )

            for forbidden_type in requirement.forbidden_adjacencies:
                if forbidden_type in adjacent_types:
                    issues.append(
                        make_issue(
                            code="PROGRAM_FORBIDDEN_ADJACENCY_PRESENT",
                            severity="warning",
                            category="connectivity",
                            entity_refs=[
                                {"type": "room", "id": room.id},
                                {"type": "program_requirement", "id": requirement.id},
                            ],
                            message=(
                                f"Room '{room.name}' is adjacent to forbidden room type "
                                f"'{forbidden_type}' by room program."
                            ),
                            consequence="Forbidden room relationship is present.",
                            confidence="high",
                            fixability="operation_candidate_possible",
                            source="program_validation",
                        )
                    )

    return issues


def build_matched_requirements(
    program: RoomProgram,
    rooms_by_type: Dict[str, List[Room]],
) -> List[Dict]:
    """Return requirement match summary for the program."""

    matched_requirements: List[Dict] = []

    for requirement in program.requirements:
        available_count = len(rooms_by_type.get(requirement.room_type, []))
        matched_requirements.append(
            {
                "requirement_id": requirement.id,
                "room_type": requirement.room_type,
                "required": requirement.required,
                "required_quantity": requirement.quantity,
                "available_quantity": available_count,
                "is_satisfied": (not requirement.required) or available_count >= requirement.quantity,
            }
        )

    return matched_requirements


def validate_program_against_plan(program: RoomProgram, plan: Plan) -> Dict:
    """Validate a Plan against a RoomProgram."""

    rooms_by_type = extract_room_types_from_plan(plan)

    program_issues: List[Dict] = []
    program_issues.extend(check_missing_required_rooms(program, rooms_by_type))
    program_issues.extend(check_area_mismatches(program, rooms_by_type))
    program_issues.extend(check_adjacency_requirements(program, plan, rooms_by_type))

    total_area_m2 = sum(_room_area_m2(room) for room in plan.rooms)

    return {
        "program": program.model_dump(),
        "program_issues": program_issues,
        "matched_requirements": build_matched_requirements(program, rooms_by_type),
        "room_types": {
            room_type: [room.id for room in rooms]
            for room_type, rooms in rooms_by_type.items()
        },
        "total_area_m2": round(total_area_m2, 2),
    }
