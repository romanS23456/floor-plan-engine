import pytest
from app.models import Plan, Room, Door, Window, Furniture
from app.validation import validate_plan


def test_invalid_door_reference_returns_error():
    """Test that a door with non-existent from_room_id returns an error"""
    rooms = [
        Room(
            id="room-1",
            name="Room 1",
            polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
        )
    ]
    
    doors = [
        Door(
            id="door-1",
            from_room_id="non-existent-room",
            to_room_id="room-1",
            position_mm=[1500, 0],
            width_mm=900
        )
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    result = validate_plan(plan)
    
    assert len(result["errors"]) > 0
    assert any("non-existent-room" in err for err in result["errors"])


def test_room_without_door_returns_warning():
    """Test that a room without any connected door returns a warning"""
    rooms = [
        Room(
            id="isolated-room",
            name="Isolated Room",
            polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
        ),
        Room(
            id="connected-room",
            name="Connected Room",
            polygon_mm=[[3000, 0], [6000, 0], [6000, 4000], [3000, 4000]]
        )
    ]
    
    # Door only connects to connected-room
    doors = [
        Door(
            id="door-1",
            from_room_id="connected-room",
            to_room_id=None,
            position_mm=[4500, 0],
            width_mm=900
        )
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    result = validate_plan(plan)
    
    assert len(result["warnings"]) > 0
    assert any("isolated-room" in warn for warn in result["warnings"])


def test_valid_plan_returns_areas():
    """Test that a valid plan returns calculated areas"""
    rooms = [
        Room(
            id="room-1",
            name="Room 1",
            polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
        )
    ]
    
    doors = [
        Door(
            id="door-1",
            from_room_id="room-1",
            to_room_id=None,
            position_mm=[1500, 0],
            width_mm=900
        )
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    result = validate_plan(plan)
    
    assert "room-1" in result["areas"]
    assert result["areas"]["room-1"] == 12.0
    assert len(result["errors"]) == 0


def test_unreachable_room_error_in_validate():
    """Test that unreachable room returns UNREACHABLE_ROOM error in validate_plan."""
    rooms = [
        Room(id="entry", name="Entry", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
        Room(id="isolated", name="Isolated Room", polygon_mm=[[2000, 0], [3000, 0], [3000, 1000], [2000, 1000]]),
    ]
    
    doors = [
        Door(id="door-ext", from_room_id="entry", to_room_id=None, position_mm=[500, 0], width_mm=900),
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    result = validate_plan(plan)
    
    assert any("UNREACHABLE_ROOM" in err for err in result["errors"])
    assert any("isolated" in err for err in result["errors"])


def test_no_entry_room_warning_in_validate():
    """Test that no entry room returns NO_ENTRY_ROOM warning in validate_plan."""
    rooms = [
        Room(id="room-a", name="Room A", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
        Room(id="room-b", name="Room B", polygon_mm=[[1000, 0], [2000, 0], [2000, 1000], [1000, 1000]]),
    ]
    
    doors = [
        Door(id="door-1", from_room_id="room-a", to_room_id="room-b", position_mm=[1000, 500], width_mm=900),
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    result = validate_plan(plan)
    
    assert "NO_ENTRY_ROOM" in result["warnings"]


def test_connectivity_info_in_result():
    """Test that connectivity info is included in validate_plan result."""
    rooms = [
        Room(id="entry", name="Entry", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
        Room(id="living", name="Living", polygon_mm=[[1000, 0], [2000, 0], [2000, 1000], [1000, 1000]]),
    ]
    
    doors = [
        Door(id="door-ext", from_room_id="entry", to_room_id=None, position_mm=[500, 0], width_mm=900),
        Door(id="door-1", from_room_id="entry", to_room_id="living", position_mm=[1000, 500], width_mm=900),
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    result = validate_plan(plan)
    
    assert "connectivity" in result
    assert "entry_room_ids" in result["connectivity"]
    assert "unreachable_room_ids" in result["connectivity"]
    assert "room_graph" in result["connectivity"]
    assert "entry" in result["connectivity"]["entry_room_ids"]
    assert set(result["connectivity"]["room_graph"]["nodes"]) == {"entry", "living"}
