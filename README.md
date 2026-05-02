# Floor Plan Engine

API-first / operations-first backend for GPT / AI-architect. **Structured geometry is the source of truth.**

This is NOT a CAD or visual editor. It's a backend engine that provides structured floor plan data and validation for AI agents.

## What This Project Does

- Defines floor plan data models (rooms, doors, windows, furniture) with precise geometry in millimeters
- Validates floor plans (polygon validity, door connections, area calculations)
- Provides REST API for plan validation
- Uses Shapely for geometric operations

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
```

## Run Server

```bash
# Start the FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or run directly:
```bash
python -m app.main
```

## Run Tests

```bash
python -m pytest -q
```

## Example curl

### Health Check
```bash
curl http://localhost:8000/health
```

### Validate a Plan
```bash
curl -X POST http://localhost:8000/plans/validate \
  -H "Content-Type: application/json" \
  -d '{
    "rooms": [
      {
        "id": "room-1",
        "name": "Living Room",
        "polygon_mm": [[0, 0], [5000, 0], [5000, 4000], [0, 4000]]
      }
    ],
    "doors": [
      {
        "id": "door-1",
        "from_room_id": "room-1",
        "to_room_id": null,
        "position_mm": [2500, 0],
        "width_mm": 900
      }
    ],
    "windows": [],
    "furniture": []
  }'
```

Response:
```json
{
  "areas": {
    "room-1": 20.0
  },
  "errors": [],
  "warnings": [],
  "connectivity": {
    "entry_room_ids": ["room-1"],
    "unreachable_room_ids": [],
    "room_graph": {
      "nodes": ["room-1"],
      "edges": []
    }
  }
}
```

## Architecture

- `app/models.py` - Pydantic data models for rooms, doors, windows, furniture, and plans
- `app/geometry.py` - Geometric calculations using Shapely
- `app/validation.py` - Plan validation logic (MVP 1 + MVP 2 connectivity)
- `app/connectivity.py` - Room connectivity analysis (MVP 2)
- `app/main.py` - FastAPI application with endpoints
- `app/sample_data.py` - Sample floor plan data for testing

## MVP 1 Features ✅

- Core Plan JSON structure
- Area calculation (mm² → m²)
- Basic validation (polygon points, door references, room connectivity warnings)
- `/health` endpoint
- `/plans/validate` endpoint

## MVP 2 Features ✅

### Connectivity Validation
- Room type inference from id/name (entry, hall, bathroom, pantry, private, public, service, unknown)
- Room graph construction using NetworkX
- Entry room detection (external doors or inferred type)
- Unreachable room detection

### New Validation Rules

**Errors:**
- `UNREACHABLE_ROOM`: room cannot be reached from any entry room

**Warnings:**
- `NO_ENTRY_ROOM`: no entry point detected in the plan
- `PANTRY_THROUGH_BATHROOM`: pantry only accessible through bathroom
- `PRIVACY_DIRECT_PUBLIC_PRIVATE`: private room directly connected to public room
- `PRIVACY_PASS_THROUGH_PRIVATE_ROOM`: private room is a pass-through (degree > 1)
- `BATHROOM_CONNECTED_TO_PANTRY`: bathroom directly connected to pantry

### Response Format Update
The `/plans/validate` endpoint now includes an additional `connectivity` block:

```json
{
  "areas": {...},
  "errors": [...],
  "warnings": [...],
  "connectivity": {
    "entry_room_ids": ["entry-hall"],
    "unreachable_room_ids": [],
    "room_graph": {
      "nodes": ["entry-hall", "kitchen-living"],
      "edges": [["entry-hall", "kitchen-living"]]
    }
  }
}
```

This is backwards-compatible — old clients can ignore the new `connectivity` field.

## MVP 3 Features ✅

### SVG Debug Renderer
- `POST /plans/render-svg` endpoint returns SVG visualization for debug viewing
- Renders rooms, doors, windows, furniture with labels and areas
- Uses `data-id` and `data-entity-type` attributes for programmatic access
- HTML escapes all text content to prevent XSS
- External doors styled differently from internal doors
- Customizable dimensions via query parameters (`?width=1024&height=768`)

### New Endpoint
```bash
curl -X POST http://localhost:8000/plans/render-svg \
  -H "Content-Type: application/json" \
  -d '{
    "rooms": [
      {
        "id": "room-1",
        "name": "Living Room",
        "polygon_mm": [[0, 0], [5000, 0], [5000, 4000], [0, 4000]]
      }
    ],
    "doors": [],
    "windows": [],
    "furniture": []
  }'
```

Returns SVG with `Content-Type: image/svg+xml`.

### Architecture Update
- `app/svg_renderer.py` - SVG rendering logic (MVP 3)

---

## Next: MVP 4 — Operations API

See ROADMAP.md for future development plans.