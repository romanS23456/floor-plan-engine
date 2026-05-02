import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that /health endpoint works"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_validate_plan_endpoint():
    """Test that /plans/validate endpoint works"""
    plan_data = {
        "rooms": [
            {
                "id": "room-1",
                "name": "Room 1",
                "polygon_mm": [[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            }
        ],
        "doors": [
            {
                "id": "door-1",
                "from_room_id": "room-1",
                "to_room_id": None,
                "position_mm": [1500, 0],
                "width_mm": 900
            }
        ],
        "windows": [],
        "furniture": []
    }
    
    response = client.post("/plans/validate", json=plan_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "areas" in data
    assert "errors" in data
    assert "warnings" in data
    assert "issues" in data
    assert "geometry" in data
    assert "room-1" in data["areas"]


def test_render_svg_endpoint():
    """Test that /plans/render-svg endpoint works"""
    plan_data = {
        "rooms": [
            {
                "id": "room-1",
                "name": "Room 1",
                "polygon_mm": [[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            }
        ],
        "doors": [
            {
                "id": "door-1",
                "from_room_id": "room-1",
                "to_room_id": None,
                "position_mm": [1500, 0],
                "width_mm": 900
            }
        ],
        "windows": [],
        "furniture": []
    }
    
    response = client.post("/plans/render-svg", json=plan_data)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    
    svg_content = response.text
    assert svg_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert '<svg' in svg_content
    assert 'data-id="room-1"' in svg_content
    assert 'data-entity-type="room"' in svg_content


def test_render_svg_endpoint_custom_size():
    """Test that /plans/render-svg endpoint accepts custom dimensions"""
    plan_data = {
        "rooms": [
            {
                "id": "room-1",
                "name": "Room 1",
                "polygon_mm": [[0, 0], [3000, 0], [3000, 4000], [0, 4000]]
            }
        ],
        "doors": [],
        "windows": [],
        "furniture": []
    }
    
    response = client.post("/plans/render-svg?width=1024&height=768", json=plan_data)
    assert response.status_code == 200
    
    svg_content = response.text
    assert 'width="1024"' in svg_content
    assert 'height="768"' in svg_content


def test_validate_with_constraints_endpoint_works():
    """Test that POST /plans/validate-with-constraints works"""
    plan_data = {
        "rooms": [
            {
                "id": "bedroom",
                "name": "Bedroom",
                "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]
            }
        ],
        "doors": [
            {
                "id": "door-1",
                "from_room_id": "bedroom",
                "to_room_id": None,
                "position_mm": [1500, 0],
                "width_mm": 900
            }
        ],
        "windows": [],
        "furniture": []
    }
    
    constraints = [
        {
            "id": "min_bedroom_area",
            "constraint_type": "min_area",
            "priority": "must",
            "room_id": "bedroom",
            "min_area_m2": 5.0
        }
    ]
    
    request_data = {
        "plan": plan_data,
        "constraints": constraints
    }
    
    response = client.post("/plans/validate-with-constraints", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "areas" in data
    assert "errors" in data
    assert "warnings" in data
    assert "issues" in data
    assert "constraint_violations" in data
    assert "constraints_summary" in data


def test_validate_with_constraints_returns_violations():
    """Test that validate-with-constraints returns constraint_violations"""
    plan_data = {
        "rooms": [
            {
                "id": "small-room",
                "name": "Small Room",
                "polygon_mm": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]  # 1 m²
            }
        ],
        "doors": [],
        "windows": [],
        "furniture": []
    }
    
    constraints = [
        {
            "id": "min_area_constraint",
            "constraint_type": "min_area",
            "priority": "must",
            "room_id": "small-room",
            "min_area_m2": 10.0
        }
    ]
    
    request_data = {
        "plan": plan_data,
        "constraints": constraints
    }
    
    response = client.post("/plans/validate-with-constraints", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["constraint_violations"]) > 0
    violation = data["constraint_violations"][0]
    assert violation["code"] == "CONSTRAINT_MIN_AREA_VIOLATION"


def test_validate_with_constraints_appends_to_issues():
    """Test that violations are appended to issues list"""
    plan_data = {
        "rooms": [
            {
                "id": "tiny-room",
                "name": "Tiny Room",
                "polygon_mm": [[0, 0], [500, 0], [500, 500], [0, 500]]  # 0.25 m²
            }
        ],
        "doors": [],
        "windows": [],
        "furniture": []
    }
    
    constraints = [
        {
            "id": "area_check",
            "constraint_type": "min_area",
            "priority": "must",
            "room_id": "tiny-room",
            "min_area_m2": 5.0
        }
    ]
    
    request_data = {
        "plan": plan_data,
        "constraints": constraints
    }
    
    response = client.post("/plans/validate-with-constraints", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    # Violations should be in both constraint_violations and issues
    assert len(data["constraint_violations"]) > 0
    assert len(data["issues"]) >= len(data["constraint_violations"])


def test_validate_with_constraints_keeps_all_fields():
    """Test that validate-with-constraints keeps all standard fields"""
    plan_data = {
        "rooms": [
            {
                "id": "room1",
                "name": "Room 1",
                "polygon_mm": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]
            }
        ],
        "doors": [
            {
                "id": "door-ext",
                "from_room_id": "room1",
                "to_room_id": None,
                "position_mm": [1500, 0],
                "width_mm": 900
            }
        ],
        "windows": [],
        "furniture": []
    }
    
    constraints = []
    
    request_data = {
        "plan": plan_data,
        "constraints": constraints
    }
    
    response = client.post("/plans/validate-with-constraints", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    # All standard fields must be present
    assert "areas" in data
    assert "errors" in data
    assert "warnings" in data
    assert "connectivity" in data
    assert "geometry" in data
    assert "issues" in data
    assert "constraints" in data
    assert "constraint_violations" in data
    assert "constraints_summary" in data
