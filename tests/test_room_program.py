"""Tests for RoomProgram validation (MVP 7)."""

import pytest
from app.models import Plan, Room, Door, Window, Furniture
from app.room_program import RoomProgram, RoomRequirement, AdjacencyRequirement
from app.program_validation import validate_room_program


def _make_simple_plan():
    """Create a simple test plan with rooms and doors."""
    return Plan(
        rooms=[
            Room(
                id="kitchen-1",
                name="Kitchen",
                polygon_mm=[[0, 0], [4000, 0], [4000, 3000], [0, 3000]]
            ),
            Room(
                id="living-1",
                name="Living Room",
                polygon_mm=[[4000, 0], [8000, 0], [8000, 5000], [4000, 5000]]
            ),
            Room(
                id="bedroom-1",
                name="Bedroom",
                polygon_mm=[[0, 3000], [4000, 3000], [4000, 6000], [0, 6000]]
            ),
            Room(
                id="bathroom-1",
                name="Bathroom",
                polygon_mm=[[4000, 5000], [6000, 5000], [6000, 6000], [4000, 6000]]
            ),
        ],
        doors=[
            Door(
                id="door-1",
                from_room_id="kitchen-1",
                to_room_id="living-1",
                position_mm=[4000, 1500],
                width_mm=900
            ),
            Door(
                id="door-2",
                from_room_id="kitchen-1",
                to_room_id="bedroom-1",
                position_mm=[2000, 3000],
                width_mm=800
            ),
            Door(
                id="door-3",
                from_room_id="living-1",
                to_room_id="bathroom-1",
                position_mm=[5000, 5000],
                width_mm=700
            ),
            Door(
                id="door-4",
                from_room_id="kitchen-1",
                to_room_id=None,
                position_mm=[0, 1500],
                width_mm=900
            ),
        ],
        windows=[],
        furniture=[]
    )


class TestEmptyProgram:
    def test_empty_program_returns_info_issue(self):
        """Empty program should return PROGRAM_EMPTY info issue."""
        plan = _make_simple_plan()
        program = RoomProgram(requirements=[], adjacency_requirements=[])
        
        result = validate_room_program(plan, program)
        
        assert result["program_summary"]["issues_count"] == 1
        assert len(result["program_issues"]) == 1
        issue = result["program_issues"][0]
        assert issue["code"] == "PROGRAM_EMPTY"
        assert issue["severity"] == "info"


class TestRoomCountValidation:
    def test_missing_required_room_type_returns_issue(self):
        """Missing required room type should return issue."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(
                    id="req-dining",
                    room_type="dining",
                    required=True,
                    min_count=1
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_REQUIRED_ROOM_TYPE_MISSING"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"
    
    def test_too_few_rooms_of_type_returns_issue(self):
        """Too few rooms of required type should return issue."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(
                    id="req-bedroom-2",
                    room_type="private",
                    required=True,
                    min_count=2
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_TOO_FEW_ROOMS_OF_TYPE"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"
    
    def test_too_many_rooms_of_type_returns_issue(self):
        """Too many rooms of a type should return info issue."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(
                    id="req-bathroom-max",
                    room_type="bathroom",
                    required=True,
                    min_count=1,
                    max_count=1
                )
            ]
        )
        
        # Add another bathroom to the plan
        plan.rooms.append(Room(
            id="bathroom-2",
            name="WC",
            polygon_mm=[[6000, 5000], [8000, 5000], [8000, 6000], [6000, 6000]]
        ))
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_TOO_MANY_ROOMS_OF_TYPE"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "info"


class TestAreaValidation:
    def test_room_area_below_minimum_returns_issue(self):
        """Room below minimum area should return warning."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(
                    id="req-bedroom-min",
                    room_type="private",
                    required=True,
                    min_count=1,
                    min_area_m2=20.0  # bedroom is only 12 m²
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_ROOM_AREA_BELOW_MINIMUM"]
        assert len(issues) >= 1
        assert issues[0]["severity"] == "warning"
    
    def test_room_area_above_maximum_returns_issue(self):
        """Room above maximum area should return info."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(
                    id="req-living-max",
                    room_type="public",
                    required=True,
                    min_count=1,
                    max_area_m2=10.0  # living is 20 m²
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_ROOM_AREA_ABOVE_MAXIMUM"]
        assert len(issues) >= 1
        assert issues[0]["severity"] == "info"
    
    def test_target_area_mismatch_returns_info(self):
        """Room significantly different from target should return info."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(
                    id="req-kitchen-target",
                    room_type="kitchen",
                    required=True,
                    min_count=1,
                    target_area_m2=50.0  # kitchen is only 12 m² - more than 20% diff
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_TARGET_AREA_MISMATCH"]
        assert len(issues) >= 1
        assert issues[0]["severity"] == "info"


class TestAdjacencyValidation:
    def test_required_direct_adjacency_missing_returns_issue(self):
        """Missing required direct adjacency should return warning."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[],
            adjacency_requirements=[
                AdjacencyRequirement(
                    id="adj-bedroom-bathroom",
                    from_room_type="private",
                    to_room_type="bathroom",
                    adjacency_type="direct",
                    required=True
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_REQUIRED_ADJACENCY_MISSING"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"
    
    def test_separated_adjacency_violation_returns_issue(self):
        """Forbidden adjacency that exists should return warning."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[],
            adjacency_requirements=[
                AdjacencyRequirement(
                    id="sep-kitchen-bedroom",
                    from_room_type="kitchen",
                    to_room_type="private",
                    adjacency_type="separated",
                    required=True
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_FORBIDDEN_ADJACENCY_EXISTS"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "warning"
    
    def test_near_adjacency_returns_unsupported_info(self):
        """'near' adjacency type should return unsupported info issue."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[],
            adjacency_requirements=[
                AdjacencyRequirement(
                    id="near-kitchen-living",
                    from_room_type="kitchen",
                    to_room_type="public",
                    adjacency_type="near",
                    required=True
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_UNSUPPORTED_ADJACENCY_TYPE"]
        assert len(issues) == 1
        assert issues[0]["severity"] == "info"
        assert "near" in result["program_summary"]["unsupported_checks"][0]


class TestInvalidRequirement:
    def test_invalid_requirement_does_not_crash(self):
        """Invalid requirement should not crash, should return warning."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(
                    id="req-invalid",
                    room_type="",  # Empty room_type is invalid
                    required=True,
                    min_count=-1  # Negative count is invalid
                )
            ]
        )
        
        result = validate_room_program(plan, program)
        
        issues = [i for i in result["program_issues"] if i["code"] == "PROGRAM_INVALID_REQUIREMENT"]
        assert len(issues) >= 1
        assert issues[0]["severity"] == "warning"


class TestProgramSummary:
    def test_program_summary_contains_counts(self):
        """Program summary should contain correct counts."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(id="req-1", room_type="kitchen", min_count=1),
                RoomRequirement(id="req-2", room_type="bathroom", min_count=1),
            ],
            adjacency_requirements=[
                AdjacencyRequirement(id="adj-1", from_room_type="kitchen", to_room_type="public")
            ]
        )
        
        result = validate_room_program(plan, program)
        
        summary = result["program_summary"]
        assert summary["requirements_total"] == 3
        assert summary["requirements_checked"] == 3
        assert "matched_room_types" in summary
        assert "missing_room_types" in summary
        assert "unsupported_checks" in summary


class TestIssueShape:
    def test_program_issues_have_validation_issue_shape(self):
        """Program issues should have ValidationIssue structure."""
        plan = _make_simple_plan()
        program = RoomProgram(
            requirements=[
                RoomRequirement(id="req-missing", room_type="dining", required=True, min_count=1)
            ]
        )
        
        result = validate_room_program(plan, program)
        
        assert len(result["program_issues"]) > 0
        issue = result["program_issues"][0]
        
        # Check required fields
        assert "id" in issue
        assert "code" in issue
        assert "severity" in issue
        assert "category" in issue
        assert "entity_refs" in issue
        assert "message" in issue
        assert "consequence" in issue
        assert "confidence" in issue
        assert "fixability" in issue
        assert "source" in issue
