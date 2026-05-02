# ROADMAP.md - Floor Plan Engine Development Roadmap

## Current Status: MVP 2 ✅ COMPLETE

**MVP 2 — Connectivity Validation** has been implemented.

---

## MVP History

### MVP 1 — Core Plan JSON ✅ COMPLETE

**Features:**
- [x] Project structure with app/ and tests/ directories
- [x] Data models: Room, Door, Window, Furniture, Plan
- [x] Geometry calculations using Shapely (area in m² from mm coordinates)
- [x] Validation logic (polygon points, door references, connectivity warnings)
- [x] FastAPI endpoints: GET /health, POST /plans/validate
- [x] Sample data with 5 rooms (entry hall, kitchen-living, pantry, guest bathroom, bedroom)
- [x] Tests for geometry, validation, and API
- [x] Documentation: README.md, AGENTS.md, ROADMAP.md

### MVP 2 — Connectivity Validation ✅ COMPLETE

**Features:**
- [x] New module: `app/connectivity.py`
- [x] Room type inference (`infer_room_type`): entry, hall, bathroom, pantry, private, public, service, unknown
- [x] Room graph construction (`build_room_graph`) using NetworkX
- [x] Entry room detection (`get_entry_room_ids`): external doors or inferred type
- [x] Unreachable room detection (`find_unreachable_rooms`)
- [x] Pantry-through-bathroom detection (`detect_pantry_through_bathroom`)
- [x] Privacy warnings (`detect_privacy_warnings`):
  - Direct public-private connections
  - Bathroom connected to pantry
  - Pass-through private rooms
- [x] Updated `validate_plan` to include connectivity analysis
- [x] New `connectivity` block in response (backwards-compatible)
- [x] Optional fields in Room model: `room_type`, `privacy_level`
- [x] Tests for connectivity module and updated validation tests
- [x] Updated documentation (README.md, AGENTS.md, ROADMAP.md)

**New Validation Rules:**

Errors:
- `UNREACHABLE_ROOM`: room cannot be reached from any entry room

Warnings:
- `NO_ENTRY_ROOM`: no entry point detected
- `PANTRY_THROUGH_BATHROOM`: pantry only accessible through bathroom
- `PRIVACY_DIRECT_PUBLIC_PRIVATE`: private room directly connected to public room
- `PRIVACY_PASS_THROUGH_PRIVATE_ROOM`: private room is a pass-through
- `BATHROOM_CONNECTED_TO_PANTRY`: bathroom directly connected to pantry

**Backwards Compatibility:**
- Old JSON plans without `room_type` still work (auto-inferred)
- Old endpoints unchanged (`GET /health`, `POST /plans/validate`)
- New `connectivity` field is additive; old clients can ignore it
- All MVP 1 tests pass without modification

---

## Future MVPs (Not Yet Implemented)

The following MVPs should be added **one at a time**. Do NOT implement multiple MVPs in a single iteration.

### MVP 3 — SVG Debug Renderer (Next)
- GET /plans/{id}/export.svg endpoint
- 2D floor plan visualization for debugging
- Layer support (walls, furniture, dimensions)
- Simple SVG output, not a full UI

### MVP 4 — Walls & Boundaries
- Wall entities with thickness, material, start/end points
- Automatic wall generation from room polygons
- Wall intersection detection
- Door/window placement on walls

### MVP 5 — Operations API
- POST /operations/add-room
- POST /operations/remove-room
- POST /operations/move-wall
- POST /operations/add-door
- Transaction-style operations with rollback support

### MVP 6 — Diff & Snapshots
- Plan snapshotting (save/restore states)
- Diff between two plan versions
- Operation history tracking

### MVP 7 — Zoning & Rules
- Zone definitions (private, public, wet, dry)
- Building code validation rules
- Accessibility compliance checks
- Minimum dimension enforcement

### MVP 8 — 3D Export
- GET /plans/{id}/export.obj or .glb
- Basic 3D extrusion from 2D plans
- Wall heights, door openings, window cutouts

---

## Development Rules

1. **One MVP at a time** — Complete and test each MVP before starting the next.

2. **Never break existing endpoints** — Maintain backward compatibility. Add new endpoints; don't modify existing ones unless fixing bugs.

3. **Run tests after every change:**
   ```bash
   python -m pytest -q
   ```

4. **API-first design** — All features must be accessible via API. UI is secondary (debug only).

5. **Structured geometry is source of truth** — Never lose precision. Store coordinates in mm, calculate areas in m².

6. **Document changes** — Update README.md and this ROADMAP.md after each MVP.

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 0.1.0 (MVP 1) | Current | ✅ Complete |
| 0.2.0 (MVP 2) | Current | ✅ Complete |
| 0.3.0 (MVP 3) | Next | ⏳ Planned: SVG Debug Renderer |
