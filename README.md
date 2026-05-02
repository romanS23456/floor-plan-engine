# Floor Plan Engine

API-first / operations-first backend for GPT / AI-architect. **Structured geometry is the source of truth.**

This is NOT a CAD or visual editor. It's a backend engine that provides structured floor plan data and validation for AI agents.

## What This Project Does

- Defines floor plan data models (rooms, doors, windows, furniture) with precise geometry in millimeters
- Validates floor plans (polygon validity, door connections, area calculations, geometric checks)
- Provides REST API for plan validation with constraint support
- Uses Shapely for geometric operations
- Structured `ValidationIssue` format for all issues
- `PlanningConstraint` model for project requirements

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

Response includes areas, errors, warnings, connectivity, issues, and geometry:
```json
{
  "areas": {"room-1": 20.0},
  "errors": [],
  "warnings": [],
  "connectivity": {...},
  "issues": [...],
  "geometry": {...}
}
```

### Render SVG (Debug Visualization)
```bash
curl -X POST http://localhost:8000/plans/render-svg \
  -H "Content-Type: application/json" \
  -d '{"rooms": [...], "doors": [...], "windows": [], "furniture": []}'
```

Returns SVG with `Content-Type: image/svg+xml`.

### Validate with Constraints (MVP 5)
```bash
curl -X POST http://localhost:8000/plans/validate-with-constraints \
  -H "Content-Type: application/json" \
  -d '{
    "plan": {
      "rooms": [{"id": "bedroom", "name": "Bedroom", "polygon_mm": [[0,0],[3000,0],[3000,3000],[0,3000]]}],
      "doors": [],
      "windows": [],
      "furniture": []
    },
    "constraints": [
      {
        "id": "min_bedroom_area",
        "constraint_type": "min_area",
        "priority": "must",
        "room_id": "bedroom",
        "min_area_m2": 10.0
      }
    ]
  }'
```

Returns standard validation fields plus:
- `constraints`: list of provided constraints
- `constraint_violations`: structured ValidationIssue objects for violations
- `constraints_summary`: counts by priority

## Architecture

- `app/models.py` - Pydantic data models for rooms, doors, windows, furniture, and plans
- `app/geometry.py` - Geometric calculations using Shapely
- `app/validation.py` - Plan validation logic (MVP 1 + MVP 2 connectivity + MVP 4 geometric)
- `app/connectivity.py` - Room connectivity analysis (MVP 2)
- `app/geometric_validation.py` - Geometric validation rules (MVP 4)
- `app/issues.py` - Structured ValidationIssue format (MVP 4)
- `app/issue_taxonomy.py` - Centralized issue definitions (MVP 5)
- `app/constraints.py` - PlanningConstraint model (MVP 5)
- `app/constraint_validation.py` - Constraint validation service (MVP 5)
- `app/room_program.py` - RoomProgram and RoomRequirement models (MVP 7)
- `app/program_validation.py` - Program validation logic (MVP 7)
- `app/main.py` - FastAPI application with endpoints
- `app/sample_data.py` - Sample floor plan data for testing
- `app/svg_renderer.py` - SVG rendering logic (MVP 3)

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/plans/validate` | Validate a floor plan |
| POST | `/plans/render-svg` | Render floor plan as SVG (debug only) |
| POST | `/plans/validate-with-constraints` | Validate plan with custom constraints (MVP 5) |
| POST | `/briefs/validate` | Validate project brief completeness (MVP 6) |
| POST | `/plans/validate-with-brief` | Validate plan with project brief context (MVP 6) |
| POST | `/plans/program-check` | Validate plan against room program (MVP 7) |

## ProjectBrief Lite (MVP 6)

ProjectBrief captures project intent and household/lifestyle context. It does NOT replace Plan JSON — geometry remains the source of truth.

### Example ProjectBrief

```json
{
  "project_type": "private_house",
  "stage": "concept_design",
  "household": {
    "adults": 2,
    "children": 1,
    "guests_often": true
  },
  "lifestyle": {
    "cooks_often": true,
    "works_from_home": false,
    "needs_guest_room": true
  },
  "priorities": ["natural_light", "cost_efficiency"],
  "budget_level": "medium",
  "construction_method": "traditional",
  "target_total_area_m2": 120.0,
  "floors_count": 1
}
```

### POST /briefs/validate

Validates a project brief and returns completeness assessment:

```bash
curl -X POST http://localhost:8000/briefs/validate \
  -H "Content-Type: application/json" \
  -d '{"project_brief": {...}}'
```

Response includes:
- `brief_completeness.score` — 0 to 100
- `brief_completeness.missing_fields` — list of missing fields
- `brief_completeness.unknown_fields` — fields with "unknown" values
- `brief_completeness.is_ready_for_plan_review` — true if score >= 60
- `brief_completeness.limitations` — review limitations due to missing data
- `brief_issues` — list of ValidationIssue objects

### POST /plans/validate-with-brief

Combines plan validation with brief context:

```bash
curl -X POST http://localhost:8000/plans/validate-with-brief \
  -H "Content-Type: application/json" \
  -d '{
    "plan": {...},
    "project_brief": {...},
    "constraints": [...]
  }'
```

Response includes all standard validation fields plus:
- `brief_completeness` — brief scoring and limitations
- `brief_issues` — issues from brief validation
- `brief_plan_issues` — heuristic mismatches between plan and brief
- `constraint_violations` — if constraints provided
- `constraints_summary` — if constraints provided

**Note:** Missing brief data limits review confidence. Brief conclusions should always include limitations when data is missing. Do not treat brief assumptions as facts.

## ValidationIssue Format (MVP 4+)

All validation issues use structured format:

```json
{
  "id": "issue_code_entity_ids",
  "code": "ROOM_OVERLAP",
  "severity": "error",
  "category": "geometry",
  "entity_refs": [{"type": "room", "id": "room1"}, {"type": "room", "id": "room2"}],
  "message": "Rooms overlap by 5.0 m²",
  "consequence": "Invalid geometry: rooms cannot occupy same space",
  "confidence": "high",
  "fixability": "manual_review_required",
  "source": "validation"
}
```

## PlanningConstraint Format (MVP 5)

Constraints express project requirements:

```json
{
  "id": "unique_constraint_id",
  "constraint_type": "min_area",
  "priority": "must",
  "description": "Bedroom must be at least 10 m²",
  "room_id": "bedroom",
  "min_area_m2": 10.0
}
```

**Constraint types:**
- `min_area` — Minimum room area
- `max_area` — Maximum room area
- `required_connection` — Rooms must be connected
- `forbidden_connection` — Rooms must NOT be connected
- `required_room_type` — Required count of room type
- `required_access_from_entry` — Room must be accessible from entry

**Priority levels:**
- `must` → severity: error
- `should` → severity: warning
- `nice_to_have` → severity: info

---

## RoomProgram Lite (MVP 7)

RoomProgram describes the expected room composition and spatial relationships for a project.

### Example RoomProgram

```json
{
  "id": "program_001",
  "name": "3BR Family House",
  "description": "Program for a 3-bedroom family home",
  "target_total_area_m2": 120.0,
  "requirements": [
    {
      "id": "req_master_bed",
      "room_type": "bedroom",
      "name": "Master Bedroom",
      "quantity": 1,
      "required": true,
      "min_area_m2": 20.0,
      "max_area_m2": 30.0,
      "required_adjacencies": ["bathroom"],
      "forbidden_adjacencies": ["kitchen", "garage"]
    },
    {
      "id": "req_guest_bed",
      "room_type": "bedroom",
      "name": "Guest Bedroom",
      "quantity": 2,
      "required": true,
      "min_area_m2": 12.0,
      "required_adjacencies": ["bathroom"]
    },
    {
      "id": "req_kitchen",
      "room_type": "kitchen",
      "quantity": 1,
      "required": true,
      "min_area_m2": 12.0,
      "required_adjacencies": ["dining", "entry"],
      "forbidden_adjacencies": ["bedroom"]
    }
  ]
}
```

### POST /plans/program-check

Validates a plan against a room program:

```bash
curl -X POST http://localhost:8000/plans/program-check \
  -H "Content-Type: application/json" \
  -d '{
    "plan": {...},
    "program": {...}
  }'
```

Response includes:
- `program` — the input program
- `program_issues` — list of ValidationIssue objects for violations
- `matched_requirements` — list of satisfied requirements
- `total_area_m2` — calculated total project area

Example response:

```json
{
  "program": {...},
  "program_issues": [
    {
      "id": "PROGRAM_MISSING_REQUIRED_ROOM_req_garage",
      "code": "PROGRAM_MISSING_REQUIRED_ROOM",
      "severity": "error",
      "category": "area",
      "entity_refs": [{"type": "program_requirement", "id": "req_garage"}],
      "message": "Missing 1 required room(s) of type 'garage' (required: 1, found: 0)",
      "consequence": "Program requires 1 garage(s) but only 0 present",
      "confidence": "high",
      "fixability": "operation_candidate_possible",
      "source": "validation"
    },
    {
      "id": "PROGRAM_AREA_BELOW_MINIMUM_bedroom1_req_master_bed",
      "code": "PROGRAM_AREA_BELOW_MINIMUM",
      "severity": "warning",
      "category": "area",
      "entity_refs": [
        {"type": "room", "id": "bedroom1"},
        {"type": "program_requirement", "id": "req_master_bed"}
      ],
      "message": "Room 'Master Bedroom' (bedroom1) area 18.5 m² below minimum 20.0 m²",
      "consequence": "Room does not meet program minimum area requirement",
      "confidence": "high",
      "fixability": "operation_candidate_possible",
      "source": "validation"
    }
  ],
  "matched_requirements": [
    {
      "requirement_id": "req_guest_bed",
      "room_type": "bedroom",
      "required": 2,
      "available": 2
    },
    {
      "requirement_id": "req_kitchen",
      "room_type": "kitchen",
      "required": 1,
      "available": 1
    }
  ],
  "total_area_m2": 125.5
}
```

**Note:** RoomProgram v1 focuses on:
- Room type matching and quantity validation
- Area range validation
- Adjacency requirements (required and forbidden connections)
- Room type inference from room id/name

Room type inference uses simple heuristics:
- `bedroom` — matches "bed", "master"
- `bathroom` — matches "bath", "wc", "toilet"
- `kitchen` — matches "kitchen", "cook"
- `living` — matches "living", "lounge", "sitting"
- `dining` — matches "dining", "diningroom"
- And more — see `infer_room_type()` for full list

---

## MVP History

### MVP 1 ✅ Core Plan JSON
- Core Plan JSON structure
- Area calculation (mm² → m²)
- Basic validation (polygon points, door references)
- `/health` endpoint
- `/plans/validate` endpoint

### MVP 2 ✅ Connectivity Validation
- Room type inference from id/name
- Room graph construction using NetworkX
- Entry room detection
- Unreachable room detection
- Privacy warnings (pantry-through-bathroom, direct public-private, etc.)

### MVP 3 ✅ SVG Debug Renderer
- `POST /plans/render-svg` endpoint
- Renders rooms, doors, windows, furniture with labels
- Uses `data-id` and `data-entity-type` attributes
- HTML escapes all text content to prevent XSS

### MVP 4 ✅ Geometric Validation + ValidationIssue v1
- Structured `ValidationIssue` format via `make_issue()`
- Geometric validation rules:
  - `ROOM_OVERLAP` — detect overlapping rooms
  - `FURNITURE_OUTSIDE_ROOM` — furniture outside assigned room
  - `INVALID_FURNITURE_POLYGON` — invalid furniture geometry
  - `UNKNOWN_WINDOW_ROOM_REFERENCE` — window references non-existent room
  - `UNKNOWN_FURNITURE_ROOM_REFERENCE` — furniture references non-existent room
  - `ROOM_AREA_BELOW_MINIMUM` — room area below minimum for type
  - `ROUGH_DOOR_FURNITURE_CONFLICT` — door position conflicts with furniture
- Response includes `issues` and `geometry` blocks

### MVP 5 ✅ Issue Taxonomy + PlanningConstraint v1
- Centralized issue taxonomy with 25+ issue codes
- Categories: geometry, references, connectivity, privacy, area, furniture, constraints
- `PlanningConstraint` model for declarative requirements
- Priority levels: must, should, nice_to_have
- New endpoint: `POST /plans/validate-with-constraints`
- Constraint violations returned as structured ValidationIssue objects

### MVP 6 ✅ ProjectBrief Lite
- `ProjectBrief` model capturing project intent and context
- `Household` and `Lifestyle` sub-models
- Brief completeness scoring (0–100)
- Limitations tracking when data is missing
- Plan-against-brief heuristic checks:
  - Unsupported project type warning
  - Work-from-home without workspace hint
  - Guests often without guest facilities hint
  - Cooks often without kitchen hint
- New endpoints:
   - `POST /briefs/validate` — validate brief completeness
   - `POST /plans/validate-with-brief` — combined plan + brief validation
- Issue taxonomy extended with 13 brief-related issue codes

### MVP 7 ✅ RoomProgram v1

Implemented:
- `app/room_program.py` — RoomProgram, RoomRequirement models
- `app/program_validation.py` — program validation logic
- Room type inference from room id/name
- Room quantity validation against program requirements
- Room area range validation (min/max)
- Required and forbidden adjacency validation
- `POST /plans/program-check` endpoint
- tests/test_room_program.py — 18 tests
- Issue taxonomy extended with 5 room program issue codes
- README.md updated with MVP 7 documentation
- All 89 tests passing

---

## Next: MVP 8 — SiteContext Lite

See ROADMAP.md for future development plans.