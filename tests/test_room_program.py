"""Tests for Room Program validation."""

import pytest
from app.models import Plan, Room, Door
from app.room_program import RoomProgram, RoomRequirement, AdjacencyRequirement
from app.program_validation import validate_room_program


def make_plan(rooms_data):
    """Helper to create a plan with rooms."""
    rooms = []
    doors = []
    for r in rooms_data:
        rooms.append(Room(
            id=r["id"],
            name=r.get("name", ""),
            polygon_mm=r["polygon_mm"]
        ))
    return Plan(rooms=rooms, doors=doors, windows=[], furniture=[])


def test_empty_program():
    """Test that empty program returns PROGRAM_EMPTY info."""
    plan = make_plan([
        {"id": "room1", "name": "Living", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}
    ])
    program = RoomProgram(requirements=[])
    
    result = validate_room_program(plan, program)
    
    assert result["program_summary"]["requirements_total"] == 0
    assert len(result["program_issues"]) == 1
    assert result["program_issues"][0]["code"] == "PROGRAM_EMPTY"
    assert result["program_issues"][0]["severity"] == "info"


def test_missing_required_room_type():
    """Test missing required room type produces error."""
    plan = make_plan([
        {"id": "bedroom", "name": "Bedroom", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="kitchen", required=True, min_count=1)
    ])
    
    result = validate_room_program(plan, program)
    
    assert "kitchen" in result["program_summary"]["missing_room_types"]
    assert any(i["code"] == "PROGRAM_REQUIRED_ROOM_TYPE_MISSING" for i in result["program_issues"])
    errors = [i for i in result["program_issues"] if i["severity"] == "error"]
    assert len(errors) > 0


def test_too_few_rooms():
    """Test too few rooms of required type."""
    plan = make_plan([
        {"id": "bedroom1", "name": "Bedroom 1", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="private", required=True, min_count=2)
    ])
    
    result = validate_room_program(plan, program)
    
    assert any(i["code"] == "PROGRAM_TOO_FEW_ROOMS_OF_TYPE" for i in result["program_issues"])


def test_too_many_rooms():
    """Test too many rooms produces warning."""
    plan = make_plan([
        {"id": "bedroom1", "name": "Bedroom 1", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
        {"id": "bedroom2", "name": "Bedroom 2", "polygon_mm": [[3000, 0], [6000, 0], [6000, 3000], [3000, 3000]]},
        {"id": "bedroom3", "name": "Bedroom 3", "polygon_mm": [[6000, 0], [9000, 0], [9000, 3000], [6000, 3000]]},
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="private", required=True, max_count=2)
    ])
    
    result = validate_room_program(plan, program)
    
    assert any(i["code"] == "PROGRAM_TOO_MANY_ROOMS_OF_TYPE" for i in result["program_issues"])
    warnings = [i for i in result["program_issues"] if i["severity"] == "warning"]
    assert len(warnings) > 0


def test_area_below_minimum():
    """Test room area below minimum produces warning."""
    plan = make_plan([
        {"id": "small-room", "name": "Small", "polygon_mm": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]}  # 1 m²
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="unknown", min_area_m2=5.0)
    ])
    
    result = validate_room_program(plan, program)
    
    assert any(i["code"] == "PROGRAM_ROOM_AREA_BELOW_MINIMUM" for i in result["program_issues"])


def test_area_above_maximum():
    """Test room area above maximum produces warning."""
    plan = make_plan([
        {"id": "large-room", "name": "Large", "polygon_mm": [[0, 0], [10000, 0], [10000, 10000], [0, 10000]]}  # 100 m²
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="unknown", max_area_m2=50.0)
    ])
    
    result = validate_room_program(plan, program)
    
    assert any(i["code"] == "PROGRAM_ROOM_AREA_ABOVE_MAXIMUM" for i in result["program_issues"])


def test_target_area_mismatch():
    """Test target area mismatch produces info."""
    plan = make_plan([
        {"id": "room1", "name": "Room", "polygon_mm": [[0, 0], [10000, 0], [10000, 10000], [0, 10000]]}  # 100 m²
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="unknown", target_area_m2=20.0)
    ])
    
    result = validate_room_program(plan, program)
    
    assert any(i["code"] == "PROGRAM_TARGET_AREA_MISMATCH" for i in result["program_issues"])
    infos = [i for i in result["program_issues"] if i["severity"] == "info"]
    assert len(infos) > 0


def test_required_direct_adjacency_missing():
    """Test missing required direct adjacency produces warning."""
    plan = make_plan([
        {"id": "bedroom", "name": "Bedroom", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
        {"id": "bathroom", "name": "Bathroom", "polygon_mm": [[4000, 0], [7000, 0], [7000, 3000], [4000, 3000]]},
    ])
    # No doors connecting them
    program = RoomProgram(
        requirements=[
            RoomRequirement(id="req1", room_type="private"),
            RoomRequirement(id="req2", room_type="bathroom"),
        ],
        adjacency_requirements=[
            AdjacencyRequirement(id="adj1", from_room_type="private", to_room_type="bathroom", adjacency_type="direct", required=True)
        ]
    )
    
    result = validate_room_program(plan, program)
    
    assert any(i["code"] == "PROGRAM_REQUIRED_ADJACENCY_MISSING" for i in result["program_issues"])


def test_separated_adjacency_violation():
    """Test forbidden adjacency (separated) violation."""
    plan = make_plan([
        {"id": "bedroom", "name": "Bedroom", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
        {"id": "bathroom", "name": "Bathroom", "polygon_mm": [[3000, 0], [6000, 0], [6000, 3000], [3000, 3000]]},
    ])
    # Add door connecting them
    plan.doors = [Door(
        id="door1",
        from_room_id="bedroom",
        to_room_id="bathroom",
        position_mm=[3000, 1500],
        width_mm=900
    )]
    
    program = RoomProgram(
        requirements=[
            RoomRequirement(id="req1", room_type="private"),
            RoomRequirement(id="req2", room_type="bathroom"),
        ],
        adjacency_requirements=[
            AdjacencyRequirement(id="adj1", from_room_type="private", to_room_type="bathroom", adjacency_type="separated", required=True)
        ]
    )
    
    result = validate_room_program(plan, program)
    
    assert any(i["code"] == "PROGRAM_FORBIDDEN_ADJACENCY_EXISTS" for i in result["program_issues"])


def test_near_adjacency_unsupported():
    """Test near adjacency returns unsupported/info."""
    plan = make_plan([
        {"id": "bedroom", "name": "Bedroom", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
        {"id": "bathroom", "name": "Bathroom", "polygon_mm": [[4000, 0], [7000, 0], [7000, 3000], [4000, 3000]]},
    ])
    program = RoomProgram(
        requirements=[
            RoomRequirement(id="req1", room_type="private"),
            RoomRequirement(id="req2", room_type="bathroom"),
        ],
        adjacency_requirements=[
            AdjacencyRequirement(id="adj1", from_room_type="private", to_room_type="bathroom", adjacency_type="near", required=True)
        ]
    )
    
    result = validate_room_program(plan, program)
    
    assert any(i["code"] == "PROGRAM_UNSUPPORTED_ADJACENCY_TYPE" for i in result["program_issues"])
    assert "adjacency:near:private:bathroom" in result["program_summary"]["unsupported_checks"]


def test_invalid_requirement_does_not_crash():
    """Test invalid requirement does not crash."""
    plan = make_plan([
        {"id": "room1", "name": "Room", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="")  # Empty room_type
    ])
    
    # Should not crash
    result = validate_room_program(plan, program)
    assert isinstance(result, dict)
    assert "program_summary" in result
    assert "program_issues" in result


def test_program_summary_contains_counts():
    """Test program_summary contains correct counts."""
    plan = make_plan([
        {"id": "bedroom", "name": "Bedroom", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]},
        {"id": "kitchen", "name": "Kitchen", "polygon_mm": [[3000, 0], [6000, 0], [6000, 3000], [3000, 3000]]},
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="private"),
        RoomRequirement(id="req2", room_type="public"),
        RoomRequirement(id="req3", room_type="bathroom", required=True),
    ])
    
    result = validate_room_program(plan, program)
    
    summary = result["program_summary"]
    assert summary["requirements_total"] == 3
    assert summary["requirements_checked"] == 3
    assert "private" in summary["matched_room_types"]
    assert "public" in summary["matched_room_types"]
    assert "bathroom" in summary["missing_room_types"]


def test_program_issues_have_validation_issue_shape():
    """Test program issues have ValidationIssue shape."""
    plan = make_plan([
        {"id": "room1", "name": "Room", "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}
    ])
    program = RoomProgram(requirements=[
        RoomRequirement(id="req1", room_type="nonexistent", required=True)
    ])
    
    result = validate_room_program(plan, program)
    
    assert len(result["program_issues"]) > 0
    issue = result["program_issues"][0]
    assert "id" in issue
    assert "code" in issue
    assert "severity" in issue
    assert "category" in issue
    assert "entity_refs" in issue
    assert "message" in issue
