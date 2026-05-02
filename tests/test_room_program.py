"""Tests for Room Program functionality (MVP 7)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.room_program import RoomProgram, RoomRequirement, infer_room_type
from app.program_validation import (
    validate_program_against_plan,
    extract_room_types_from_plan,
    check_missing_required_rooms,
    check_area_mismatches,
    check_adjacency_requirements,
)
from app.models import Plan, Room, Door

client = TestClient(app)


def make_basic_plan():
    """Create a minimal 4-room plan for testing."""
    return Plan(
        rooms=[
            Room(
                id="bedroom1",
                name="Master Bedroom",
                polygon_mm=[[0, 0], [4000, 0], [4000, 3000], [0, 3000]],
            ),
            Room(
                id="bathroom1",
                name="Bathroom",
                polygon_mm=[[4000, 0], [6000, 0], [6000, 3000], [4000, 3000]],
            ),
            Room(
                id="kitchen1",
                name="Kitchen",
                polygon_mm=[[0, 3000], [4000, 3000], [4000, 5000], [0, 5000]],
            ),
            Room(
                id="living1",
                name="Living Room",
                polygon_mm=[[4000, 3000], [8000, 3000], [8000, 5000], [4000, 5000]],
            ),
        ],
        doors=[
            Door(id="d1", from_room_id="bedroom1", to_room_id="bathroom1", position_mm=[4000, 1500], width_mm=900),
            Door(id="d2", from_room_id="bathroom1", to_room_id="living1", position_mm=[6000, 4000], width_mm=900),
            Door(id="d3", from_room_id="kitchen1", to_room_id="living1", position_mm=[4000, 4000], width_mm=900),
            Door(id="d4", from_room_id="living1", to_room_id=None, position_mm=[8000, 4000], width_mm=900),
        ],
        windows=[],
        furniture=[],
    )


class TestRoomTypeInference:
    """Test room type inference from id and name."""
    
    def test_infer_bedroom(self):
        assert infer_room_type("bed1", "Bedroom") == "bedroom"
        assert infer_room_type("master", "Master Bedroom") == "bedroom"
        assert infer_room_type("room1", "Bed Room") == "bedroom"
    
    def test_infer_bathroom(self):
        assert infer_room_type("bath1", "Bathroom") == "bathroom"
        assert infer_room_type("wc", "Toilet") == "bathroom"
    
    def test_infer_kitchen(self):
        assert infer_room_type("k1", "Kitchen") == "kitchen"
    
    def test_infer_living(self):
        assert infer_room_type("living1", "Living Room") == "living"
    
    def test_infer_unknown(self):
        assert infer_room_type("room_a", "Mystery Room") == "unknown"


class TestExtractRoomTypes:
    """Test extraction of rooms grouped by type."""
    
    def test_extract_from_basic_plan(self):
        plan = make_basic_plan()
        rooms_by_type = extract_room_types_from_plan(plan)
        
        assert "bedroom" in rooms_by_type
        assert "bathroom" in rooms_by_type
        assert "kitchen" in rooms_by_type
        assert "living" in rooms_by_type
        
        assert len(rooms_by_type["bedroom"]) == 1
        assert len(rooms_by_type["kitchen"]) == 1


class TestMissingRequiredRooms:
    """Test detection of missing required rooms."""
    
    def test_all_required_rooms_present(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            name="Simple 4-room",
            requirements=[
                RoomRequirement(id="r1", room_type="bedroom", quantity=1, required=True),
                RoomRequirement(id="r2", room_type="bathroom", quantity=1, required=True),
                RoomRequirement(id="r3", room_type="kitchen", quantity=1, required=True),
                RoomRequirement(id="r4", room_type="living", quantity=1, required=True),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_missing_required_rooms(program, rooms_by_type)
        
        assert len(issues) == 0
    
    def test_missing_required_room(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(id="r1", room_type="garage", quantity=1, required=True),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_missing_required_rooms(program, rooms_by_type)
        
        assert len(issues) == 1
        assert issues[0]["code"] == "PROGRAM_MISSING_REQUIRED_ROOM"
        assert "garage" in issues[0]["message"]
    
    def test_missing_multiple_bedrooms(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(id="r1", room_type="bedroom", quantity=3, required=True),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_missing_required_rooms(program, rooms_by_type)
        
        assert len(issues) == 1
        assert "2" in issues[0]["message"] and "required" in issues[0]["message"]
    
    def test_optional_rooms_not_required(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(id="r1", room_type="garage", quantity=1, required=False),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_missing_required_rooms(program, rooms_by_type)
        
        assert len(issues) == 0


class TestAreaMismatches:
    """Test detection of room area mismatches."""
    
    def test_minimum_area_violation(self):
        """Bedroom is 12 m², but program requires 15 m² minimum."""
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(
                    id="r1",
                    room_type="bedroom",
                    min_area_m2=15.0,
                ),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_area_mismatches(program, rooms_by_type)
        
        assert len(issues) > 0
        assert any(i["code"] == "PROGRAM_AREA_BELOW_MINIMUM" for i in issues)
    
    def test_maximum_area_violation(self):
        """Bedroom is 12 m², and program forbids over 10 m²."""
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(
                    id="r1",
                    room_type="bedroom",
                    max_area_m2=10.0,
                ),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_area_mismatches(program, rooms_by_type)
        
        assert len(issues) > 0
        assert any(i["code"] == "PROGRAM_AREA_ABOVE_MAXIMUM" for i in issues)
    
    def test_area_requirements_satisfied(self):
        """Bedroom is 12 m², program requires 10-15 m²."""
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(
                    id="r1",
                    room_type="bedroom",
                    min_area_m2=10.0,
                    max_area_m2=15.0,
                ),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_area_mismatches(program, rooms_by_type)
        
        assert len(issues) == 0


class TestAdjacencyRequirements:
    """Test detection of adjacency requirement violations."""
    
    def test_required_adjacency_present(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(
                    id="r1",
                    room_type="bedroom",
                    required_adjacencies=["bathroom"],
                ),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_adjacency_requirements(program, plan, rooms_by_type)
        
        # Bedroom and bathroom are connected
        assert len([i for i in issues if i["code"] == "PROGRAM_REQUIRED_ADJACENCY_MISSING"]) == 0
    
    def test_required_adjacency_missing(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(
                    id="r1",
                    room_type="bedroom",
                    required_adjacencies=["kitchen"],
                ),
            ],
        )
        rooms_by_type = extract_room_types_from_plan(plan)
        issues = check_adjacency_requirements(program, plan, rooms_by_type)
        
        # Bedroom and kitchen are not connected
        assert any(i["code"] == "PROGRAM_REQUIRED_ADJACENCY_MISSING" for i in issues)


class TestValidateProgramAgainstPlan:
    """Test full program validation."""
    
    def test_basic_validation(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            name="Basic House",
            requirements=[
                RoomRequirement(id="r1", room_type="bedroom", quantity=1, required=True),
                RoomRequirement(id="r2", room_type="bathroom", quantity=1, required=True),
                RoomRequirement(id="r3", room_type="kitchen", quantity=1, required=True),
                RoomRequirement(id="r4", room_type="living", quantity=1, required=True),
            ],
        )
        
        result = validate_program_against_plan(program, plan)
        
        assert result["program"]["id"] == "prog1"
        assert len(result["program_issues"]) == 0
        assert len(result["matched_requirements"]) == 4
        assert result["total_area_m2"] > 0
    
    def test_complex_validation_with_issues(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(
                    id="r1",
                    room_type="bedroom",
                    quantity=2,
                    required=True,
                    min_area_m2=15.0,
                ),
                RoomRequirement(
                    id="r2",
                    room_type="garage",
                    quantity=1,
                    required=True,
                ),
            ],
        )
        
        result = validate_program_against_plan(program, plan)
        
        # Should have issues: missing garage, missing 1 bedroom, bedroom too small
        assert len(result["program_issues"]) > 0
        assert any(i["code"] == "PROGRAM_MISSING_REQUIRED_ROOM" for i in result["program_issues"])


class TestProgramCheckEndpoint:
    """Test the /plans/program-check endpoint."""
    
    def test_endpoint_basic_validation(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            name="Basic House",
            requirements=[
                RoomRequirement(id="r1", room_type="bedroom", quantity=1, required=True),
                RoomRequirement(id="r2", room_type="bathroom", quantity=1, required=True),
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
        assert "program" in data
        assert "program_issues" in data
        assert "matched_requirements" in data
        assert "total_area_m2" in data
    
    def test_endpoint_with_issues(self):
        plan = make_basic_plan()
        program = RoomProgram(
            id="prog1",
            requirements=[
                RoomRequirement(id="r1", room_type="garage", quantity=1, required=True),
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
        assert len(data["program_issues"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
