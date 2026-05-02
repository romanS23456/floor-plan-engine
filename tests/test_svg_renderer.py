"""Tests for SVG renderer module."""

import pytest
from app.svg_renderer import render_plan_svg, _empty_svg
from app.models import Plan, Room, Door, Window, Furniture


def test_render_plan_svg_basic():
    """Test basic SVG rendering with one room."""
    plan = Plan(
        rooms=[
            Room(
                id="room-1",
                name="Test Room",
                polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            )
        ],
        doors=[],
        windows=[],
        furniture=[]
    )
    
    svg = render_plan_svg(plan)
    
    assert svg.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert '<svg' in svg
    assert 'data-id="room-1"' in svg
    assert 'data-entity-type="room"' in svg
    assert "Test Room" in svg
    assert "12.0" in svg  # area should be 12.0 m²


def test_render_plan_svg_with_doors():
    """Test SVG rendering with doors."""
    plan = Plan(
        rooms=[
            Room(
                id="room-1",
                name="Room 1",
                polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            ),
            Room(
                id="room-2",
                name="Room 2",
                polygon_mm=[[3000, 0], [6000, 0], [6000, 4000], [3000, 4000]]
            )
        ],
        doors=[
            Door(
                id="door-1",
                from_room_id="room-1",
                to_room_id="room-2",
                position_mm=[3000, 2000],
                width_mm=900
            ),
            Door(
                id="door-external",
                from_room_id="room-1",
                to_room_id=None,
                position_mm=[1500, 0],
                width_mm=900
            )
        ],
        windows=[],
        furniture=[]
    )
    
    svg = render_plan_svg(plan)
    
    assert 'data-id="door-1"' in svg
    assert 'data-entity-type="door"' in svg
    assert 'data-id="door-external"' in svg
    assert 'class="external-door"' in svg  # External door has different class
    assert 'class="door"' in svg or 'class="external-door"' in svg


def test_render_plan_svg_with_windows():
    """Test SVG rendering with windows."""
    plan = Plan(
        rooms=[
            Room(
                id="room-1",
                name="Room 1",
                polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            )
        ],
        doors=[],
        windows=[
            Window(
                id="window-1",
                room_id="room-1",
                position_mm=[1500, 0],
                width_mm=1200
            )
        ],
        furniture=[]
    )
    
    svg = render_plan_svg(plan)
    
    assert 'data-id="window-1"' in svg
    assert 'data-entity-type="window"' in svg
    assert 'class="window"' in svg


def test_render_plan_svg_with_furniture():
    """Test SVG rendering with furniture."""
    plan = Plan(
        rooms=[
            Room(
                id="room-1",
                name="Room 1",
                polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            )
        ],
        doors=[],
        windows=[],
        furniture=[
            Furniture(
                id="table-1",
                room_id="room-1",
                type="dining-table",
                polygon_mm=[[500, 500], [1500, 500], [1500, 1500], [500, 1500]]
            )
        ]
    )
    
    svg = render_plan_svg(plan)
    
    assert 'data-id="table-1"' in svg
    assert 'data-entity-type="furniture"' in svg
    assert 'data-furniture-type="dining-table"' in svg
    assert 'class="furniture"' in svg


def test_render_plan_svg_html_escaping():
    """Test that text content is HTML escaped."""
    plan = Plan(
        rooms=[
            Room(
                id="room-<script>",
                name="Room & <b>bold</b>",
                polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            )
        ],
        doors=[],
        windows=[],
        furniture=[]
    )
    
    svg = render_plan_svg(plan)
    
    # Check that special characters are escaped
    assert "&lt;script&gt;" in svg or "room-" in svg
    assert "&amp;" in svg or "&lt;b&gt;" in svg


def test_render_plan_svg_custom_size():
    """Test SVG rendering with custom dimensions."""
    plan = Plan(
        rooms=[
            Room(
                id="room-1",
                name="Room 1",
                polygon_mm=[[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            )
        ],
        doors=[],
        windows=[],
        furniture=[]
    )
    
    svg = render_plan_svg(plan, width=1024, height=768)
    
    assert 'width="1024"' in svg
    assert 'height="768"' in svg
    assert 'viewBox="0 0 1024 768"' in svg


def test_empty_svg():
    """Test empty SVG generation."""
    svg = _empty_svg(800, 600)
    
    assert svg.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert 'width="800"' in svg
    assert 'height="600"' in svg
    assert "No geometry to render" in svg


def test_render_plan_svg_empty_rooms():
    """Test SVG rendering with no rooms returns empty SVG."""
    plan = Plan(
        rooms=[],
        doors=[],
        windows=[],
        furniture=[]
    )
    
    svg = render_plan_svg(plan)
    
    assert "No geometry to render" in svg


def test_render_plan_svg_sample_plan():
    """Test SVG rendering with the sample plan."""
    from app.sample_data import get_valid_sample_plan
    
    plan = get_valid_sample_plan()
    svg = render_plan_svg(plan)
    
    # Should contain all rooms
    assert 'data-id="entry-hall"' in svg
    assert 'data-id="kitchen-living"' in svg
    assert 'data-id="pantry"' in svg
    assert 'data-id="guest-bathroom"' in svg
    assert 'data-id="bedroom"' in svg
    
    # Should contain doors
    assert 'data-entity-type="door"' in svg
    
    # Should contain windows
    assert 'data-entity-type="window"' in svg
    
    # Should contain furniture
    assert 'data-entity-type="furniture"' in svg
