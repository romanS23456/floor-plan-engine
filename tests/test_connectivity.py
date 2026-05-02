"""Tests for connectivity module."""

import pytest
from app.models import Plan, Room, Door, Window, Furniture
from app.connectivity import (
    infer_room_type,
    build_room_graph,
    get_entry_room_ids,
    find_unreachable_rooms,
    detect_pantry_through_bathroom,
    detect_privacy_warnings,
)


def test_build_room_graph_creates_nodes_and_edges():
    """Test that build_room_graph creates nodes and edges from doors."""
    rooms = [
        Room(id="room-a", name="Room A", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
        Room(id="room-b", name="Room B", polygon_mm=[[1000, 0], [2000, 0], [2000, 1000], [1000, 1000]]),
        Room(id="room-c", name="Room C", polygon_mm=[[2000, 0], [3000, 0], [3000, 1000], [2000, 1000]]),
    ]
    
    doors = [
        Door(id="door-1", from_room_id="room-a", to_room_id="room-b", position_mm=[1000, 500], width_mm=900),
        Door(id="door-2", from_room_id="room-b", to_room_id="room-c", position_mm=[2000, 500], width_mm=900),
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    graph = build_room_graph(plan)
    
    # Check nodes
    assert set(graph.nodes()) == {"room-a", "room-b", "room-c"}
    
    # Check edges
    assert graph.has_edge("room-a", "room-b")
    assert graph.has_edge("room-b", "room-c")
    assert not graph.has_edge("room-a", "room-c")


def test_get_entry_room_ids_finds_external_door():
    """Test that get_entry_room_ids finds room with external door (to_room_id=None)."""
    rooms = [
        Room(id="entry-hall", name="Entry Hall", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
        Room(id="living", name="Living Room", polygon_mm=[[1000, 0], [2000, 0], [2000, 1000], [1000, 1000]]),
    ]
    
    doors = [
        Door(id="door-ext", from_room_id="entry-hall", to_room_id=None, position_mm=[500, 0], width_mm=900),
        Door(id="door-int", from_room_id="entry-hall", to_room_id="living", position_mm=[1000, 500], width_mm=900),
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    entry_rooms = get_entry_room_ids(plan)
    
    assert "entry-hall" in entry_rooms
    assert "living" not in entry_rooms


def test_get_entry_room_ids_finds_by_name():
    """Test that get_entry_room_ids finds room by inferred type 'entry'."""
    rooms = [
        Room(id="main-entrance", name="Main Entrance", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
    ]
    
    # No external door, but name contains "entrance"
    doors = []
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    entry_rooms = get_entry_room_ids(plan)
    
    assert "main-entrance" in entry_rooms


def test_unreachable_room_returns_error():
    """Test that unreachable room is detected."""
    rooms = [
        Room(id="entry", name="Entry", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
        Room(id="isolated", name="Isolated Room", polygon_mm=[[2000, 0], [3000, 0], [3000, 1000], [2000, 1000]]),
    ]
    
    doors = [
        Door(id="door-ext", from_room_id="entry", to_room_id=None, position_mm=[500, 0], width_mm=900),
        # No door connecting to isolated room
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    unreachable = find_unreachable_rooms(plan)
    
    assert "isolated" in unreachable
    assert "entry" not in unreachable


def test_no_entry_room_returns_empty_list():
    """Test that find_unreachable_rooms returns empty list when no entry room exists."""
    rooms = [
        Room(id="room-a", name="Room A", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
        Room(id="room-b", name="Room B", polygon_mm=[[1000, 0], [2000, 0], [2000, 1000], [1000, 1000]]),
    ]
    
    doors = [
        Door(id="door-1", from_room_id="room-a", to_room_id="room-b", position_mm=[1000, 500], width_mm=900),
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    unreachable = find_unreachable_rooms(plan)
    
    # No entry room means we can't determine reachability
    assert unreachable == []


def test_pantry_through_bathroom_single_connection():
    """Test detection of pantry connected only to bathroom."""
    rooms = [
        Room(id="entry", name="Entry", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]]),
        Room(id="bathroom", name="Bathroom", polygon_mm=[[1000, 0], [2000, 0], [2000, 1000], [1000, 1000]]),
        Room(id="pantry", name="Pantry", polygon_mm=[[2000, 0], [3000, 0], [3000, 1000], [2000, 1000]]),
    ]
    
    doors = [
        Door(id="door-ext", from_room_id="entry", to_room_id=None, position_mm=[500, 0], width_mm=900),
        Door(id="door-1", from_room_id="entry", to_room_id="bathroom", position_mm=[1000, 500], width_mm=900),
        Door(id="door-2", from_room_id="bathroom", to_room_id="pantry", position_mm=[2000, 500], width_mm=700),
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    problematic = detect_pantry_through_bathroom(plan)
    
    assert "pantry" in problematic


def test_direct_public_private_connection():
    """Test detection of direct connection between public and private rooms."""
    rooms = [
        Room(id="kitchen-living", name="Kitchen-Living", polygon_mm=[[0, 0], [2000, 0], [2000, 1000], [0, 1000]]),
        Room(id="bedroom", name="Bedroom", polygon_mm=[[2000, 0], [3000, 0], [3000, 1000], [2000, 1000]]),
    ]
    
    doors = [
        Door(id="door-1", from_room_id="kitchen-living", to_room_id="bedroom", position_mm=[2000, 500], width_mm=900),
    ]
    
    plan = Plan(rooms=rooms, doors=doors, windows=[], furniture=[])
    warnings = detect_privacy_warnings(plan)
    
    privacy_warnings = [w for w in warnings if w["type"] == "PRIVACY_DIRECT_PUBLIC_PRIVATE"]
    assert len(privacy_warnings) > 0
    assert any(w["room_id"] == "bedroom" for w in privacy_warnings)


def test_infer_room_type_entry():
    """Test room type inference for entry rooms."""
    assert infer_room_type(Room(id="entry-hall", name="Entry Hall", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "entry"
    assert infer_room_type(Room(id="main-entrance", name="Main Entrance", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "entry"
    assert infer_room_type(Room(id="hall", name="Hall", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "hall"


def test_infer_room_type_bathroom():
    """Test room type inference for bathrooms."""
    assert infer_room_type(Room(id="bath", name="Bathroom", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "bathroom"
    assert infer_room_type(Room(id="wc", name="WC", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "bathroom"
    assert infer_room_type(Room(id="toilet", name="Toilet", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "bathroom"


def test_infer_room_type_pantry():
    """Test room type inference for pantry."""
    assert infer_room_type(Room(id="pantry", name="Pantry", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "pantry"
    assert infer_room_type(Room(id="storage", name="Storage", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "pantry"


def test_infer_room_type_private():
    """Test room type inference for private rooms."""
    assert infer_room_type(Room(id="bedroom", name="Bedroom", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "private"
    assert infer_room_type(Room(id="master", name="Master Suite", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "private"
    assert infer_room_type(Room(id="child-room", name="Child Room", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "private"


def test_infer_room_type_public():
    """Test room type inference for public rooms."""
    assert infer_room_type(Room(id="kitchen", name="Kitchen", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "public"
    assert infer_room_type(Room(id="living", name="Living Room", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "public"
    assert infer_room_type(Room(id="dining", name="Dining Room", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "public"


def test_infer_room_type_unknown():
    """Test room type inference for unknown rooms."""
    assert infer_room_type(Room(id="mystery", name="Mystery Room", polygon_mm=[[0, 0], [1000, 0], [1000, 1000], [0, 1000]])) == "unknown"
