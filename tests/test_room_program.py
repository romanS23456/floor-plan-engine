"""Tests for RoomProgram v1.

MVP 7:
- RoomProgram / RoomRequirement models
- room type extraction
- required room checks
- area checks
- adjacency checks
- /plans/program-check API endpoint
"""

from fastapi.testclient import TestClient

from app.main import app
from app.models import Door, Plan, Room
from app.program_validation import (
    check_adjacency_requirements,
    check_area_mismatches,
    check_missing_required_rooms,
    extract_room_types_from_plan,
    validate_program_against_plan,
)
from app.room_program import RoomProgram, RoomRequirement, infer_program_room_type


client = TestClient(app)


def make_program_test_plan() -> Plan:
    """Create a small deterministic plan for RoomProgram tests."""

    return Plan(
        rooms=[
            Room(
                id="bedroom-1",
                name="Bedroom",
                room_type="bedroom",
                polygon_mm=[[0, 0], [4000, 0], [4000, 3000], [0, 3000]],
            ),
            Room(
                id="bathroom-1",
                name="Bathroom",
                room_type="bathroom",
                polygon_mm=[[4000, 0], [6000, 0], [6000, 3000], [4000, 3000]],
            ),
            Room(
                id="kitchen-1",
                name="Kitchen",
                room_type="kitchen",
                polygon_mm=[[0, 3000], [3000, 3000], [3000, 6000], [0, 6000]],
            ),
            Room(
                id="living-1",
                name="Living Room",
                room_type="living",
                polygon_mm=[[3000, 3000], [7000, 3000], [7000, 6000], [3000, 6000]],
            ),
        ],
        doors=[
            Door(
                id="door-bedroom-bathroom",
                from_room_id="bedroom-1",
                to_room_id="bathroom-1",
                position_mm=[4000, 1500],
                width_mm=900,
            ),
            Door(
                id="door-kitchen-living",
                from_room_id="kitchen-1",
                to_room_id="living-1",
                position_mm=[3000, 4500],
                width_mm=900,
            ),
            Door(
                id="door-living-exterior",
                from_room_id="living-1",
                to_room_id=None,
                position_mm=[7000, 4500],
                width_mm=900,
            ),
        ],
        windows=[],
        furniture=[],
    )


def test_room_type_inference_prefers_explicit_room_type():
    assert infer_program_room_type(
        room_id="random-id",
        room_name="Some Room",
        explicit_room_type="Bedroom",
    ) == "bedroom"


def test_room_type_inference_uses_id_and_name_fallback():
    assert infer_program_room_type("room-1", "Kitchen") == "kitchen"
    assert infer_program_room_type("bathroom-1", "Room") == "bathroom"
    assert infer_program_room_type("unknown-1", "Unknown Room") == "unknown"


def test_extract_room_types_from_plan_groups_rooms_by_type():
    plan = make_program_test_plan()

    rooms_by_type = extract_room_types_from_plan(plan)

    assert set(rooms_by_type.keys()) == {"bedroom", "bathroom", "kitchen", "living"}
    assert [room.id for room in rooms_by_type["bedroom"]] == ["bedroom-1"]


def test_missing_required_room_creates_program_issue():
    plan = make_program_test_plan()
    rooms_by_type = extract_room_types_from_plan(plan)
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-garage",
                room_type="garage",
                quantity=1,
                required=True,
            )
        ],
    )

    issues = check_missing_required_rooms(program, rooms_by_type)

    assert len(issues) == 1
    assert issues[0]["code"] == "PROGRAM_MISSING_REQUIRED_ROOM"
    assert issues[0]["severity"] == "error"
    assert issues[0]["source"] == "program_validation"


def test_optional_missing_room_does_not_create_issue():
    plan = make_program_test_plan()
    rooms_by_type = extract_room_types_from_plan(plan)
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-garage",
                room_type="garage",
                quantity=1,
                required=False,
            )
        ],
    )

    issues = check_missing_required_rooms(program, rooms_by_type)

    assert issues == []


def test_min_area_violation_creates_program_issue():
    plan = make_program_test_plan()
    rooms_by_type = extract_room_types_from_plan(plan)
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-bedroom",
                room_type="bedroom",
                min_area_m2=15.0,
            )
        ],
    )

    issues = check_area_mismatches(program, rooms_by_type)

    assert len(issues) == 1
    assert issues[0]["code"] == "PROGRAM_AREA_BELOW_MINIMUM"
    assert issues[0]["severity"] == "warning"


def test_max_area_violation_creates_program_issue():
    plan = make_program_test_plan()
    rooms_by_type = extract_room_types_from_plan(plan)
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-bedroom",
                room_type="bedroom",
                max_area_m2=10.0,
            )
        ],
    )

    issues = check_area_mismatches(program, rooms_by_type)

    assert len(issues) == 1
    assert issues[0]["code"] == "PROGRAM_AREA_ABOVE_MAXIMUM"
    assert issues[0]["severity"] == "warning"


def test_required_adjacency_present_has_no_issue():
    plan = make_program_test_plan()
    rooms_by_type = extract_room_types_from_plan(plan)
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-kitchen",
                room_type="kitchen",
                required_adjacencies=["living"],
            )
        ],
    )

    issues = check_adjacency_requirements(program, plan, rooms_by_type)

    assert issues == []


def test_required_adjacency_missing_creates_program_issue():
    plan = make_program_test_plan()
    rooms_by_type = extract_room_types_from_plan(plan)
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-bedroom",
                room_type="bedroom",
                required_adjacencies=["kitchen"],
            )
        ],
    )

    issues = check_adjacency_requirements(program, plan, rooms_by_type)

    assert len(issues) == 1
    assert issues[0]["code"] == "PROGRAM_REQUIRED_ADJACENCY_MISSING"
    assert issues[0]["category"] == "connectivity"


def test_forbidden_adjacency_present_creates_program_issue():
    plan = make_program_test_plan()
    rooms_by_type = extract_room_types_from_plan(plan)
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-bedroom",
                room_type="bedroom",
                forbidden_adjacencies=["bathroom"],
            )
        ],
    )

    issues = check_adjacency_requirements(program, plan, rooms_by_type)

    assert len(issues) == 1
    assert issues[0]["code"] == "PROGRAM_FORBIDDEN_ADJACENCY_PRESENT"
    assert issues[0]["category"] == "connectivity"


def test_validate_program_against_plan_returns_expected_blocks():
    plan = make_program_test_plan()
    program = RoomProgram(
        id="program-1",
        name="Simple house program",
        requirements=[
            RoomRequirement(id="req-bedroom", room_type="bedroom", quantity=1),
            RoomRequirement(id="req-bathroom", room_type="bathroom", quantity=1),
            RoomRequirement(id="req-kitchen", room_type="kitchen", quantity=1),
            RoomRequirement(id="req-living", room_type="living", quantity=1),
        ],
    )

    result = validate_program_against_plan(program, plan)

    assert result["program"]["id"] == "program-1"
    assert result["program_issues"] == []
    assert len(result["matched_requirements"]) == 4
    assert result["room_types"]["bedroom"] == ["bedroom-1"]
    assert result["total_area_m2"] == 39.0


def test_validate_program_against_plan_returns_combined_issues():
    plan = make_program_test_plan()
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-bedrooms",
                room_type="bedroom",
                quantity=2,
                min_area_m2=15.0,
                required=True,
            ),
            RoomRequirement(
                id="req-garage",
                room_type="garage",
                quantity=1,
                required=True,
            ),
        ],
    )

    result = validate_program_against_plan(program, plan)
    issue_codes = [issue["code"] for issue in result["program_issues"]]

    assert "PROGRAM_MISSING_REQUIRED_ROOM" in issue_codes
    assert "PROGRAM_AREA_BELOW_MINIMUM" in issue_codes


def test_program_check_endpoint_works():
    plan = make_program_test_plan()
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(id="req-bedroom", room_type="bedroom", quantity=1),
            RoomRequirement(id="req-bathroom", room_type="bathroom", quantity=1),
        ],
    )

    response = client.post(
        "/plans/program-check",
        json={
            "plan": plan.model_dump(),
            "program": program.model_dump(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["program"]["id"] == "program-1"
    assert "program_issues" in data
    assert "matched_requirements" in data
    assert "room_types" in data
    assert "total_area_m2" in data


def test_program_check_endpoint_returns_program_issues():
    plan = make_program_test_plan()
    program = RoomProgram(
        id="program-1",
        requirements=[
            RoomRequirement(
                id="req-garage",
                room_type="garage",
                quantity=1,
                required=True,
            )
        ],
    )

    response = client.post(
        "/plans/program-check",
        json={
            "plan": plan.model_dump(),
            "program": program.model_dump(),
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["program_issues"]) == 1
    assert data["program_issues"][0]["code"] == "PROGRAM_MISSING_REQUIRED_ROOM"
