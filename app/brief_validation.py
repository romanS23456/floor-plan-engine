"""Brief validation service for Floor Plan Engine.

Validates ProjectBrief completeness and checks plan against brief hints.
"""

from typing import Dict, Any, List, Optional
from app.project_brief import ProjectBrief, Household, Lifestyle
from app.models import Plan, Room
from app.issues import make_issue


def validate_project_brief(brief: ProjectBrief) -> Dict[str, Any]:
    """Validate project brief completeness.
    
    Returns:
        {
            "brief_completeness": {
                "score": int,
                "missing_fields": [],
                "unknown_fields": [],
                "is_ready_for_plan_review": bool,
                "limitations": []
            },
            "brief_issues": [...]
        }
    """
    score = 0
    missing_fields: List[str] = []
    unknown_fields: List[str] = []
    limitations: List[str] = []
    brief_issues: List[Dict[str, Any]] = []
    
    # Check project_type (15 points)
    if brief.project_type:
        score += 15
    else:
        missing_fields.append("project_type")
        brief_issues.append(make_issue(
            code="BRIEF_MISSING_PROJECT_TYPE",
            severity="warning"
        ))
    
    # Check stage (10 points)
    if brief.stage:
        score += 10
    else:
        missing_fields.append("stage")
        brief_issues.append(make_issue(
            code="BRIEF_MISSING_STAGE",
            severity="warning"
        ))
    
    # Check household (20 points)
    if brief.household and (brief.household.adults is not None or brief.household.children is not None):
        score += 20
    elif brief.household is None:
        missing_fields.append("household")
        limitations.append("Household is missing; bedroom and privacy conclusions are limited.")
        brief_issues.append(make_issue(
            code="BRIEF_MISSING_HOUSEHOLD",
            severity="warning"
        ))
    else:
        # Household exists but no adults/children specified
        missing_fields.append("household.adults_or_children")
        brief_issues.append(make_issue(
            code="BRIEF_MISSING_HOUSEHOLD",
            severity="warning"
        ))
    
    # Check lifestyle (15 points)
    if brief.lifestyle:
        score += 15
    else:
        missing_fields.append("lifestyle")
        limitations.append("Lifestyle is missing; scenario-based plan conclusions are limited.")
        brief_issues.append(make_issue(
            code="BRIEF_MISSING_LIFESTYLE",
            severity="warning"
        ))
    
    # Check priorities (15 points)
    if brief.priorities and len(brief.priorities) > 0:
        score += 15
    else:
        missing_fields.append("priorities")
        limitations.append("Priorities are missing; tradeoff ranking is limited.")
        brief_issues.append(make_issue(
            code="BRIEF_MISSING_PRIORITIES",
            severity="warning"
        ))
    
    # Check budget_level (10 points)
    if brief.budget_level and brief.budget_level.lower() != "unknown":
        score += 10
    elif brief.budget_level is None:
        missing_fields.append("budget_level")
        brief_issues.append(make_issue(
            code="BRIEF_MISSING_BUDGET_LEVEL",
            severity="warning"
        ))
    elif brief.budget_level.lower() == "unknown":
        unknown_fields.append("budget_level")
    
    # Check construction_method (5 points)
    if brief.construction_method and brief.construction_method.lower() != "unknown":
        score += 5
    elif brief.construction_method is None:
        missing_fields.append("construction_method")
    elif brief.construction_method.lower() == "unknown":
        unknown_fields.append("construction_method")
        brief_issues.append(make_issue(
            code="BRIEF_UNKNOWN_CONSTRUCTION_METHOD",
            severity="warning"
        ))
    
    # Check target_total_area_m2 (5 points)
    if brief.target_total_area_m2 is not None:
        score += 5
    else:
        missing_fields.append("target_total_area_m2")
    
    # Check floors_count (5 points)
    if brief.floors_count is not None:
        score += 5
    else:
        missing_fields.append("floors_count")
    
    # Add RoomProgram limitation
    limitations.append("RoomProgram is not provided yet; missing room checks are limited.")
    
    # Add SiteContext limitation
    limitations.append("SiteContext is not provided yet; garden, orientation and driveway checks are limited.")
    
    # Determine readiness
    is_ready_for_plan_review = score >= 60
    
    # Add low completeness issue if score is low
    if score < 60:
        brief_issues.append(make_issue(
            code="BRIEF_LOW_COMPLETENESS",
            severity="warning",
            message=f"Brief completeness score is {score}/100; review confidence is reduced"
        ))
    
    if not is_ready_for_plan_review:
        brief_issues.append(make_issue(
            code="BRIEF_PLAN_REVIEW_LIMITED",
            severity="warning"
        ))
    
    return {
        "brief_completeness": {
            "score": score,
            "missing_fields": missing_fields,
            "unknown_fields": unknown_fields,
            "is_ready_for_plan_review": is_ready_for_plan_review,
            "limitations": limitations
        },
        "brief_issues": brief_issues
    }


def _has_room_type_hint(rooms: List[Room], hints: List[str]) -> bool:
    """Check if any room has a type hint in id, name, or room_type."""
    for room in rooms:
        check_str = f"{room.id} {room.name} {room.room_type or ''}".lower()
        for hint in hints:
            if hint.lower() in check_str:
                return True
    return False


def _infer_room_type(room: Room) -> Optional[str]:
    """Infer room type from id, name, or room_type field."""
    check_str = f"{room.id} {room.name} {room.room_type or ''}".lower()
    
    # Public spaces
    public_hints = ["living", "dining", "kitchen", "hall", "entry", "foyer", "public"]
    for hint in public_hints:
        if hint in check_str:
            return "public"
    
    # Private spaces
    private_hints = ["bedroom", "bathroom", "wc", "toilet", "study", "office"]
    for hint in private_hints:
        if hint in check_str:
            return "private"
    
    return None


def validate_plan_against_brief(plan: Plan, brief: ProjectBrief) -> Dict[str, Any]:
    """Validate plan against brief hints.
    
    Returns lightweight heuristic checks, not hard errors.
    
    Returns:
        {
            "brief_plan_issues": [...]
        }
    """
    brief_plan_issues: List[Dict[str, Any]] = []
    rooms = plan.rooms
    
    # Check 1: Unsupported project type
    if brief.project_type and brief.project_type.lower() != "private_house":
        brief_plan_issues.append(make_issue(
            code="BRIEF_UNSUPPORTED_PROJECT_TYPE",
            severity="warning",
            message=f"Project type '{brief.project_type}': current engine is optimized for private house concept review"
        ))
    
    # Check 2: Works from home without workspace
    if brief.lifestyle and brief.lifestyle.works_from_home:
        workspace_hints = ["office", "study", "cabinet", "workspace", "home_office"]
        if not _has_room_type_hint(rooms, workspace_hints):
            brief_plan_issues.append(make_issue(
                code="BRIEF_WORK_FROM_HOME_WITHOUT_WORKSPACE_HINT",
                severity="info",
                confidence="low"
            ))
    
    # Check 3: Guests often without guest logic
    guests_often = False
    if brief.household and brief.household.guests_often:
        guests_often = True
    
    if guests_often:
        bathroom_hints = ["bathroom", "wc", "toilet"]
        public_hints = ["kitchen", "living", "dining", "public"]
        
        has_bathroom = _has_room_type_hint(rooms, bathroom_hints)
        has_public = _has_room_type_hint(rooms, public_hints)
        
        if not has_bathroom or not has_public:
            brief_plan_issues.append(make_issue(
                code="BRIEF_GUESTS_OFTEN_WITHOUT_GUEST_LOGIC_HINT",
                severity="info",
                confidence="low"
            ))
    
    # Check 4: Cooks often without kitchen
    if brief.lifestyle and brief.lifestyle.cooks_often:
        kitchen_hints = ["kitchen"]
        has_kitchen = _has_room_type_hint(rooms, kitchen_hints)
        
        # Also check inferred room types
        if not has_kitchen:
            for room in rooms:
                if _infer_room_type(room) == "public":
                    has_kitchen = True
                    break
        
        if not has_kitchen:
            brief_plan_issues.append(make_issue(
                code="BRIEF_COOKS_OFTEN_WITHOUT_KITCHEN_HINT",
                severity="warning",
                confidence="medium"
            ))
    
    return {
        "brief_plan_issues": brief_plan_issues
    }
