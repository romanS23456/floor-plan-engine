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
   - Parse validation results (areas, errors, warnings, connectivity)
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

## What This Project Is NOT

- ❌ Not a visual editor
- ❌ Not a CAD application
- ❌ Not a drag-and-drop tool
- ❌ Not a 3D modeling software

## What This Project IS

- ✅ API-first backend for AI agents
- ✅ Structured geometry storage and validation
- ✅ Operations-first design (add room, remove wall, move door)
- ✅ Source of truth for floor plan data
- ✅ Connectivity analysis for spatial reasoning

## Adding New Features

When extending this project:
1. Keep API as the primary interface
2. Maintain structured JSON as data format
3. Don't break existing endpoints
4. Add validation rules before new features
5. Run `python -m pytest -q` after each change
