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
| POST | `/plans/program-check` | Validate plan against RoomProgram (MVP 7) |

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

## RoomProgram v1 (MVP 7)

RoomProgram describes expected room composition and adjacency intent. It is **project intent, not geometry** — it does not generate rooms or modify the plan.

### Example RoomProgram

```json
{
  "name": "3BR Family House",
  "requirements": [
    {
      "id": "req-kitchen",
      "room_type": "kitchen",
      "required": true,
      "min_count": 1,
      "target_area_m2": 15.0,
      "min_area_m2": 10.0
    },
    {
      "id": "req-living",
      "room_type": "public",
      "required": true,
      "min_count": 1,
      "target_area_m2": 30.0
    },
    {
      "id": "req-bedrooms",
      "room_type": "private",
      "required": true,
      "min_count": 3,
      "max_count": 4,
      "min_area_m2": 12.0
    },
    {
      "id": "req-bathrooms",
      "room_type": "bathroom",
      "required": true,
      "min_count": 2
    }
  ],
  "adjacency_requirements": [
    {
      "id": "adj-kitchen-living",
      "from_room_type": "kitchen",
      "to_room_type": "public",
      "adjacency_type": "direct",
      "required": true
    },
    {
      "id": "sep-private-service",
      "from_room_type": "private",
      "to_room_type": "kitchen",
      "adjacency_type": "separated",
      "required": false
    }
  ]
}
```

### Adjacency Types

- `direct` — Rooms must directly connect via a door
- `separated` — Rooms must NOT directly connect
- `near` — Not yet distance-based in MVP 7; returns `PROGRAM_UNSUPPORTED_ADJACENCY_TYPE` info issue

### POST /plans/program-check

Validates a floor plan against a RoomProgram:

```bash
curl -X POST http://localhost:8000/plans/program-check \
  -H "Content-Type: application/json" \
  -d '{
    "plan": {...},
    "room_program": {...}
  }'
```

Response includes all standard validation fields plus:
- `program_summary.requirements_total` — total requirements checked
- `program_summary.requirements_checked` — successfully validated
- `program_summary.issues_count` — number of program issues found
- `program_summary.matched_room_types` — room types found in plan
- `program_summary.missing_room_types` — required room types not found
- `program_summary.unsupported_checks` — unsupported adjacency types (e.g., "near")
- `program_issues` — list of ValidationIssue objects for program mismatches

**Note:** RoomProgram is intent only — it does not infer missing rooms as geometry or generate rooms automatically. Distance-based "near" adjacency will be implemented in a future MVP.

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
- `RoomProgram` model describing expected room composition and adjacency intent
- `RoomRequirement` model for room type requirements:
  - required/optional rooms
  - min/max count
  - target/min/max area constraints
- `AdjacencyRequirement` model for adjacency intent:
  - `direct` — rooms must directly connect
  - `separated` — rooms must NOT directly connect
  - `near` — not yet distance-based (returns info issue)
- Program validation service in `app/program_validation.py`
- Issue taxonomy extended with 11 program-related issue codes:
  - `PROGRAM_REQUIRED_ROOM_TYPE_MISSING`
  - `PROGRAM_TOO_FEW_ROOMS_OF_TYPE`
  - `PROGRAM_TOO_MANY_ROOMS_OF_TYPE`
  - `PROGRAM_ROOM_AREA_BELOW_MINIMUM`
  - `PROGRAM_ROOM_AREA_ABOVE_MAXIMUM`
  - `PROGRAM_TARGET_AREA_MISMATCH`
  - `PROGRAM_REQUIRED_ADJACENCY_MISSING`
  - `PROGRAM_FORBIDDEN_ADJACENCY_EXISTS`
  - `PROGRAM_UNSUPPORTED_ADJACENCY_TYPE`
  - `PROGRAM_EMPTY`
  - `PROGRAM_INVALID_REQUIREMENT`
- New endpoint:
  - `POST /plans/program-check` — validate plan against RoomProgram
- Response includes:
  - `program_summary` — counts and summary info
  - `program_issues` — structured ValidationIssue objects
- RoomProgram is **intent**, not geometry — does not generate rooms
- Tests: 13 unit tests + 6 API tests

---

## Next: MVP 8 — SiteContext Lite

See ROADMAP.md for future development plans.