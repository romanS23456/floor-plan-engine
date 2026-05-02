# AGENTS.md - Guidelines for AI Agents

## Project Philosophy

**This is a GPT-first / API-first project.**

- **Structured geometry is the source of truth.** All floor plan data is stored as precise JSON with coordinates in millimeters.
- **Human uses UI only as debug-viewer.** There is no mouse-first CAD interface. The primary interaction is through API calls from AI agents.
- **Do NOT build mouse-first CAD tools.** This backend is designed for programmatic access by LLMs and AI architects.

## How to Use This Project

1. **AI Agent Workflow:**
   - Receive natural language description from user
   - Generate/modify Plan JSON structure
   - POST to `/plans/validate` endpoint
   - Parse validation results (areas, errors, warnings, connectivity, issues, geometry)
   - Iterate until plan is valid

2. **Data Format:**
   - All coordinates are in millimeters (mm)
   - Areas are calculated and returned in square meters (m²)
   - Polygons are defined as lists of [x, y] points

3. **Validation Rules:**
   - Rooms must have polygons with at least 3 points
   - Door `from_room_id` must reference an existing room
   - Door `to_room_id` (if not null) must reference an existing room
   - Warning if a room has no connected doors
   - Connectivity validation (MVP 2): unreachable rooms, entry detection, privacy warnings

4. **Connectivity Graph:**
   - **Connectivity graph is part of structured geometry review.**
   - GPT-architect should use connectivity analysis before suggesting layout fixes.
   - Check `connectivity.entry_room_ids` to identify entry points.
   - Check `connectivity.unreachable_room_ids` for isolated rooms.
   - Review warnings for privacy issues and problematic connections.

5. **SVG Debug Renderer (MVP 3):**
   - Use `POST /plans/render-svg` to get visual representation for debugging.
   - SVG uses `data-id` and `data-entity-type` attributes for programmatic access.
   - All text content is HTML-escaped to prevent XSS.
   - External doors are styled differently from internal doors.
   - SVG is for human debug viewing only — structured JSON remains the source of truth.

6. **ValidationIssue Format (MVP 4):**
   - **ValidationIssue is the canonical issue format for future review, fixes and operations.**
   - All issues (geometric, connectivity, constraints) are returned as structured `ValidationIssue` objects.
   - Each issue has: `id`, `code`, `severity`, `category`, `entity_refs`, `message`, `consequence`, `confidence`, `fixability`, `source`.
   - Legacy `errors`/`warnings` arrays remain for backwards compatibility.
   - Use `issues` array for structured processing by AI agents.
   - Issue categories: `geometry`, `references`, `connectivity`, `privacy`, `area`, `furniture`, `openings`, `constraints`, `unknown`.

7. **PlanningConstraint (MVP 5):**
   - **PlanningConstraint is the first structured way to express project requirements.**
   - Constraints describe project intent, not legal code.
   - Use `/plans/validate-with-constraints` endpoint to validate plan against constraints.
   - Constraint types: `min_area`, `max_area`, `required_connection`, `forbidden_connection`, `required_room_type`, `required_access_from_entry`.
   - Priority levels: `must` (error), `should` (warning), `nice_to_have` (info).
   - Constraint violations are returned as `ValidationIssue` objects in `constraint_violations` array.
   - Normative requirements must remain `requires_check` unless verified.

8. **ProjectBrief Lite (MVP 6):**
   - **ProjectBrief captures project intent and household/lifestyle context.**
   - ProjectBrief does NOT replace Plan JSON — geometry remains the source of truth.
   - Use `/briefs/validate` to check brief completeness before plan review.
   - Use `/plans/validate-with-brief` for combined validation.
   - Brief conclusions MUST include limitations when data is missing:
     - Household missing → bedroom and privacy conclusions are limited
     - Lifestyle missing → scenario-based conclusions are limited
     - Priorities missing → tradeoff ranking is limited
     - RoomProgram not available → missing room checks are limited
     - SiteContext not available → garden/orientation/driveway checks are limited
   - Do NOT implement full questionnaire, CRM, or client onboarding yet.
   - Do NOT treat brief assumptions as facts.
   - Do NOT claim legal/normative compliance based only on ProjectBrief.
   - Brief issues use category `brief_mismatch` with severities: warning (missing context), info (lifestyle hints).

## What This Project Is NOT

- ❌ Not a visual editor
- ❌ Not a CAD application
- ❌ Not a drag-and-drop tool
- ❌ Not a 3D modeling software
- ❌ Not a wall model yet (before MVP 15)
- ❌ Not a door orientation system yet (before MVP 15/16)

## What This Project IS

- ✅ API-first backend for AI agents
- ✅ Structured geometry storage and validation
- ✅ Operations-first design (add room, remove wall, move door)
- ✅ Source of truth for floor plan data
- ✅ Connectivity analysis for spatial reasoning
- ✅ Canonical issue format for review and fixes
- ✅ Constraint-based requirement validation

## Adding New Features

When extending this project:
1. Keep API as the primary interface
2. Maintain structured JSON as data format
3. Don't break existing endpoints
4. Add validation rules before new features
5. Run `python -m pytest -q` after each change
6. Update README.md, AGENTS.md, ROADMAP.md
7. Do not implement wall model before WallLite MVP (MVP 15)
8. Do not implement door orientation before WallLite/openings (MVP 16)
9. Geometric validation is required before GPT-architect suggests layout changes
10. Connectivity graph is part of structured geometry review
11. RoomProgram describes expected room composition and adjacency intent (MVP 7)
12. RoomProgram does NOT replace Plan JSON or ProjectBrief — it is additional context
13. Program validation must produce ValidationIssue objects
14. Do not infer missing rooms as geometry in MVP 7
15. Do not generate rooms automatically in MVP 7
16. Do not implement distance-based near adjacency until later MVP
