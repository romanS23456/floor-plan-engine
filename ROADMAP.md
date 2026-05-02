# Floor Plan Engine Roadmap

## Product Direction

Floor Plan Engine is an API-first / operations-first engine for GPT / AI architect.

This is not a mouse-first CAD editor.
Structured Plan JSON is the source of truth.
SVG, PDF, UI and renders are only representations of structured geometry.

Every MVP must:
- be small;
- include tests;
- preserve backward compatibility;
- keep existing endpoints working;
- update README.md;
- update AGENTS.md;
- run `python -m pytest -q`;
- end with an implementation report.

---

## Completed

### MVP 1 — Core Plan JSON ✅

Implemented:
- Plan, Room, Door, Window, Furniture models
- polygon geometry in millimeters
- area calculation
- basic validation
- FastAPI app
- GET /health
- POST /plans/validate
- tests

### MVP 2 — Connectivity Validation ✅

Implemented:
- room graph
- entry room detection
- unreachable room detection
- pantry through bathroom warning
- simple privacy warnings
- connectivity block in validation response
- tests

### MVP 3 — SVG Debug Renderer ✅

Implemented:
- app/svg_renderer.py
- POST /plans/render-svg
- rooms
- labels
- calculated areas
- doors
- windows
- furniture
- data-id and data-entity-type attributes
- SVG as debug visualization only
- tests

### MVP 4 — Geometric Validation + ValidationIssue v1 ✅

Implemented:
- app/issues.py
- ValidationIssue canonical issue format
- app/geometric_validation.py
- room overlap detection
- furniture outside room detection
- unknown references for windows/furniture
- minimum room area warnings
- rough door/furniture conflict warnings
- geometry block in validation response
- issues array in validation response
- tests

### MVP 5 — Issue Taxonomy + PlanningConstraint v1 ✅

Implemented:
- app/issue_taxonomy.py
- centralized issue definitions
- app/constraints.py
- PlanningConstraint model
- app/constraint_validation.py
- min_area constraint
- max_area constraint
- required_connection constraint
- forbidden_connection constraint
- required_room_type constraint
- required_access_from_entry constraint
- POST /plans/validate-with-constraints
- tests

### MVP 6 — ProjectBrief Lite ✅

Implemented:
- app/project_brief.py — ProjectBrief, Household, Lifestyle models
- app/brief_validation.py — validate_project_brief(), validate_plan_against_brief()
- app/request_models.py — request models for brief endpoints
- POST /briefs/validate — brief completeness validation
- POST /plans/validate-with-brief — combined plan + brief validation
- brief_completeness scoring (0–100) with limitations tracking
- 13 new brief-related issue codes in issue_taxonomy.py
- tests/test_project_brief.py — 9 tests
- tests/test_api.py — 5 new brief endpoint tests
- README.md updated with MVP 6 documentation
- AGENTS.md updated with ProjectBrief guidelines
- All 70 tests passing

---

## Current / Next

### MVP 7 — RoomProgram v1

Goal:
Add minimal structured project context so GPT-architect can understand:
- project type;
- design stage;
- household composition;
- lifestyle requirements;
- priorities;
- missing brief data;
- limitations of plan review.

Implement:
- app/project_brief.py
- ProjectBrief model
- Household model
- Lifestyle model
- app/brief_validation.py
- validate_project_brief()
- validate_plan_against_brief()
- POST /briefs/validate
- POST /plans/validate-with-brief
- brief_completeness block
- brief_issues
- brief_plan_issues
- tests

Do NOT implement in MVP 6:
- natural language brief parsing
- automatic constraint generation
- full questionnaire
- CRM/client onboarding
- SiteContext
- RoomProgram
- Review endpoint

---

## Planned

### MVP 7 — RoomProgram v1

Goal:
Describe expected room composition and compare plan against it.

Implement:
- RoomProgram model
- required rooms
- optional rooms
- target/min/max areas
- required adjacency
- forbidden adjacency
- program match validation
- missing room issues
- POST /plans/program-check

### MVP 8 — SiteContext Lite

Goal:
Add minimal site context for private house review.

Implement:
- north vector
- entry side
- driveway side
- garden side
- views
- neighbor/privacy risks
- slope optional
- utilities unknown flags
- POST /plans/site-check

### MVP 9 — Zoning Tags v1

Goal:
Add semantic zoning layer.

Implement:
- public/private/service/wet/dirty/clean tags
- zoning inference from room types
- zoning validation
- POST /plans/infer-zoning

### MVP 10 — Review Endpoint v1

Goal:
Create the main reasoning endpoint for GPT-architect.

Implement:
- POST /plans/review
- summary
- input_quality
- critical_issues
- warnings
- architectural_risks
- missing_data
- markdown_report
- client_friendly_summary

### MVP 11 — Operation Schema + Dry Run

Goal:
Define structured plan operations and preview their effects without mutating the plan.

Implement:
- Operation model
- OperationCandidate model
- dry-run endpoint
- affected entities
- predicted validation delta
- precondition failures
- POST /plans/operations/dry-run

### MVP 12 — Suggested Fixes as Operation Candidates

Goal:
Connect issues to structured fix suggestions.

Implement:
- suggested_fixes
- expected benefits
- tradeoffs
- confidence
- operation_candidate_ids
- POST /plans/suggest-fixes

### MVP 13 — Snapshots + Diff

Goal:
Compare plan states safely.

Implement:
- stateless snapshots
- before/after diff
- added/deleted/updated entities
- issue delta
- area delta
- POST /plans/snapshots
- POST /plans/diff

### MVP 14 — Safe Apply Operations

Goal:
Apply only safe structured operations.

Implement:
- POST /plans/operations/apply
- validation after apply
- new plan version/snapshot
- no destructive mutation without explicit apply

### MVP 15 — WallLite / Opening Model

Goal:
Introduce minimal wall/opening layer without becoming CAD.

Implement:
- WallLite
- Opening
- is_exterior
- adjacent_room_ids
- thickness_mm optional
- structural_role unknown/load_bearing/partition/exterior
- POST /plans/derive-walls
- POST /plans/validate-walls

### MVP 16 — Door Orientation + Clearance v1

Goal:
Validate door swing and clearance after WallLite exists.

Implement:
- opens_into_room_id
- hinge_side
- swing_direction
- approximate swing clearance
- door/furniture conflicts with better geometry

---

## Later

- Dimensions v1
- Corridor and circulation analysis
- Variant manager
- Zoning comparison
- Schematic plan generator
- Pattern library
- Constructability scoring
- Site/roof/facade helpers
- Reports
- PDF export
- DXF export
- 3D scene foundation
- Render prompt builder

---

## Explicitly Not Now

Do not implement yet:
- drag-and-drop CAD editor
- BIM/Revit clone
- automatic full house generator
- beautiful render pipeline
- 3D visualization
- VR
- mobile app
- real-time collaboration
- final cost estimation
- legal/normative approval engine
- door orientation before WallLite
- wall model before MVP 15
