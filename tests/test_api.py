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
    assert "room-1" in data["areas"]
