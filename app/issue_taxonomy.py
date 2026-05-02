"""Issue taxonomy for Floor Plan Engine.

Centralized definitions of issue codes, categories, severities, and defaults.
This is the canonical reference for all validation issues.
"""

from typing import Dict, Any, Optional

# Severity levels
ISSUE_SEVERITIES = ["error", "warning", "info"]

# Category values
ISSUE_CATEGORIES = [
    "geometry",
    "references",
    "connectivity",
    "privacy",
    "area",
    "furniture",
    "openings",
    "constraints",
    "brief_mismatch",
    "site",
    "zoning",
    "operations",
    "unknown",
]

# Confidence levels
CONFIDENCE_LEVELS = ["high", "medium", "low", "unknown"]

# Fixability levels
FIXABILITY_LEVELS = [
    "not_fixable",
    "manual_review_required",
    "operation_candidate_possible",
    "auto_fix_possible_later",
    "unknown",
]

# Issue code definitions
ISSUE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # MVP 1 - Basic validation
    "INVALID_ROOM_POLYGON": {
        "category": "geometry",
        "default_severity": "error",
        "default_message": "Room has invalid polygon (less than 3 points or invalid geometry)",
        "default_consequence": "Cannot calculate area or validate geometry",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "INVALID_DOOR_FROM_ROOM_REFERENCE": {
        "category": "references",
        "default_severity": "error",
        "default_message": "Door references non-existent from_room_id",
        "default_consequence": "Door connectivity cannot be established",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "INVALID_DOOR_TO_ROOM_REFERENCE": {
        "category": "references",
        "default_severity": "error",
        "default_message": "Door references non-existent to_room_id",
        "default_consequence": "Door connectivity cannot be established",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "ROOM_WITHOUT_DOOR": {
        "category": "connectivity",
        "default_severity": "warning",
        "default_message": "Room has no connected doors",
        "default_consequence": "Room may be inaccessible",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    
    # MVP 2 - Connectivity
    "NO_ENTRY_ROOM": {
        "category": "connectivity",
        "default_severity": "warning",
        "default_message": "No entry room detected in plan",
        "default_consequence": "Cannot determine accessibility from entrance",
        "default_confidence": "medium",
        "default_fixability": "manual_review_required",
    },
    "UNREACHABLE_ROOM": {
        "category": "connectivity",
        "default_severity": "error",
        "default_message": "Room is not reachable from any entry room",
        "default_consequence": "Room is isolated and inaccessible",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "PANTRY_THROUGH_BATHROOM": {
        "category": "privacy",
        "default_severity": "warning",
        "default_message": "Pantry is only accessible through bathroom",
        "default_consequence": "Poor layout: storage accessed through wet zone",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "PRIVACY_DIRECT_PUBLIC_PRIVATE": {
        "category": "privacy",
        "default_severity": "warning",
        "default_message": "Private room directly connected to public room",
        "default_consequence": "Reduced privacy for private spaces",
        "default_confidence": "medium",
        "default_fixability": "operation_candidate_possible",
    },
    "PRIVACY_PASS_THROUGH_PRIVATE_ROOM": {
        "category": "privacy",
        "default_severity": "warning",
        "default_message": "Private room is a pass-through room",
        "default_consequence": "Privacy compromised by traffic flow",
        "default_confidence": "medium",
        "default_fixability": "manual_review_required",
    },
    "BATHROOM_CONNECTED_TO_PANTRY": {
        "category": "privacy",
        "default_severity": "warning",
        "default_message": "Bathroom directly connected to pantry",
        "default_consequence": "Hygiene concern: wet zone adjacent to food storage",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    
    # MVP 4 - Geometric validation
    "ROOM_OVERLAP": {
        "category": "geometry",
        "default_severity": "error",
        "default_message": "Rooms overlap in space",
        "default_consequence": "Invalid geometry: rooms cannot occupy same space",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "FURNITURE_OUTSIDE_ROOM": {
        "category": "furniture",
        "default_severity": "error",
        "default_message": "Furniture is placed outside its assigned room",
        "default_consequence": "Invalid placement: furniture must be inside room",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "INVALID_FURNITURE_POLYGON": {
        "category": "furniture",
        "default_severity": "error",
        "default_message": "Furniture has invalid polygon (less than 3 points)",
        "default_consequence": "Cannot validate furniture geometry",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "UNKNOWN_WINDOW_ROOM_REFERENCE": {
        "category": "references",
        "default_severity": "error",
        "default_message": "Window references non-existent room_id",
        "default_consequence": "Window placement cannot be validated",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "UNKNOWN_FURNITURE_ROOM_REFERENCE": {
        "category": "references",
        "default_severity": "error",
        "default_message": "Furniture references non-existent room_id",
        "default_consequence": "Furniture placement cannot be validated",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "ROOM_AREA_BELOW_MINIMUM": {
        "category": "area",
        "default_severity": "warning",
        "default_message": "Room area is below minimum for its type",
        "default_consequence": "Room may be too small for intended use",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "ROUGH_DOOR_FURNITURE_CONFLICT": {
        "category": "furniture",
        "default_severity": "warning",
        "default_message": "Door position conflicts with furniture placement",
        "default_consequence": "Door swing or clearance may be blocked",
        "default_confidence": "low",
        "default_fixability": "operation_candidate_possible",
    },
    
    # MVP 5 - Constraint violations
    "CONSTRAINT_MIN_AREA_VIOLATION": {
        "category": "constraints",
        "default_severity": "error",
        "default_message": "Room violates minimum area constraint",
        "default_consequence": "Project requirement not met",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "CONSTRAINT_MAX_AREA_VIOLATION": {
        "category": "constraints",
        "default_severity": "error",
        "default_message": "Room violates maximum area constraint",
        "default_consequence": "Project requirement not met",
        "default_consequence": "Project requirement not met",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "CONSTRAINT_REQUIRED_CONNECTION_MISSING": {
        "category": "constraints",
        "default_severity": "error",
        "default_message": "Required connection between rooms is missing",
        "default_consequence": "Project requirement not met",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "CONSTRAINT_FORBIDDEN_CONNECTION_EXISTS": {
        "category": "constraints",
        "default_severity": "error",
        "default_message": "Forbidden connection between rooms exists",
        "default_consequence": "Project requirement violated",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "CONSTRAINT_REQUIRED_ROOM_TYPE_MISSING": {
        "category": "constraints",
        "default_severity": "error",
        "default_message": "Required room type is missing or insufficient count",
        "default_consequence": "Project requirement not met",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "CONSTRAINT_REQUIRED_ACCESS_FROM_ENTRY_MISSING": {
        "category": "constraints",
        "default_severity": "error",
        "default_message": "Required access from entry room is missing",
        "default_consequence": "Room is not accessible as required",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "CONSTRAINT_TARGET_NOT_FOUND": {
        "category": "constraints",
        "default_severity": "warning",
        "default_message": "Constraint targets non-existent room",
        "default_consequence": "Constraint cannot be validated",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "CONSTRAINT_INVALID_DEFINITION": {
        "category": "constraints",
        "default_severity": "warning",
        "default_message": "Constraint has invalid or incomplete definition",
        "default_consequence": "Constraint cannot be validated",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    
    # MVP 6 - Project Brief issues
    "BRIEF_MISSING_PROJECT_TYPE": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Project type is missing; project context is incomplete",
        "default_consequence": "Plan review conclusions may not match intended project type",
        "default_confidence": "medium",
        "default_fixability": "manual_review_required",
    },
    "BRIEF_UNSUPPORTED_PROJECT_TYPE": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Current engine is optimized for private house concept review",
        "default_consequence": "Some checks may not apply to this project type",
        "default_confidence": "high",
        "default_fixability": "not_fixable",
    },
    "BRIEF_MISSING_STAGE": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Design stage is missing; project context is incomplete",
        "default_consequence": "Review depth may not match design phase expectations",
        "default_confidence": "medium",
        "default_fixability": "manual_review_required",
    },
    "BRIEF_MISSING_HOUSEHOLD": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Household is missing; bedroom and privacy conclusions are limited",
        "default_consequence": "Cannot validate household-specific requirements",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "BRIEF_MISSING_LIFESTYLE": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Lifestyle is missing; scenario-based plan conclusions are limited",
        "default_consequence": "Cannot validate lifestyle-driven space requirements",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "BRIEF_MISSING_PRIORITIES": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Priorities are missing; tradeoff ranking is limited",
        "default_consequence": "Cannot prioritize recommendations based on client values",
        "default_confidence": "medium",
        "default_fixability": "manual_review_required",
    },
    "BRIEF_MISSING_BUDGET_LEVEL": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Budget level is missing; cost-related recommendations are limited",
        "default_consequence": "Cannot tailor suggestions to budget constraints",
        "default_confidence": "medium",
        "default_fixability": "manual_review_required",
    },
    "BRIEF_UNKNOWN_CONSTRUCTION_METHOD": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Construction method is unknown; construction-specific advice is limited",
        "default_consequence": "Cannot provide construction-method-specific guidance",
        "default_confidence": "medium",
        "default_fixability": "manual_review_required",
    },
    "BRIEF_LOW_COMPLETENESS": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Brief completeness is low; review confidence is reduced",
        "default_consequence": "Many conclusions may lack sufficient context",
        "default_confidence": "high",
        "default_fixability": "manual_review_required",
    },
    "BRIEF_PLAN_REVIEW_LIMITED": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Plan review is limited due to missing brief data",
        "default_consequence": "Review conclusions have reduced confidence",
        "default_confidence": "high",
        "default_fixability": "not_fixable",
    },
    "BRIEF_WORK_FROM_HOME_WITHOUT_WORKSPACE_HINT": {
        "category": "brief_mismatch",
        "default_severity": "info",
        "default_message": "Works from home is indicated but no workspace/office room detected",
        "default_consequence": "May need to add dedicated workspace",
        "default_confidence": "low",
        "default_fixability": "operation_candidate_possible",
    },
    "BRIEF_GUESTS_OFTEN_WITHOUT_GUEST_LOGIC_HINT": {
        "category": "brief_mismatch",
        "default_severity": "info",
        "default_message": "Guests often indicated but guest facilities may be insufficient",
        "default_consequence": "Guest accommodation may be inadequate",
        "default_confidence": "low",
        "default_fixability": "operation_candidate_possible",
    },
    "BRIEF_COOKS_OFTEN_WITHOUT_KITCHEN_HINT": {
        "category": "brief_mismatch",
        "default_severity": "warning",
        "default_message": "Cooks often indicated but no kitchen detected",
        "default_consequence": "Kitchen may be missing or not properly identified",
        "default_confidence": "medium",
        "default_fixability": "operation_candidate_possible",
    },
    
    # MVP 7 - Room Program issues
    "PROGRAM_MISSING_REQUIRED_ROOM": {
        "category": "area",
        "default_severity": "error",
        "default_message": "Room program requires room type that is missing from plan",
        "default_consequence": "Plan does not satisfy room program requirements",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "PROGRAM_AREA_BELOW_MINIMUM": {
        "category": "area",
        "default_severity": "warning",
        "default_message": "Room area is below program minimum",
        "default_consequence": "Room does not meet program area requirement",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "PROGRAM_AREA_ABOVE_MAXIMUM": {
        "category": "area",
        "default_severity": "warning",
        "default_message": "Room area exceeds program maximum",
        "default_consequence": "Room exceeds program area target",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "PROGRAM_REQUIRED_ADJACENCY_MISSING": {
        "category": "connectivity",
        "default_severity": "warning",
        "default_message": "Room program requires adjacency that is missing",
        "default_consequence": "Required room relationships not satisfied",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
    "PROGRAM_FORBIDDEN_ADJACENCY_PRESENT": {
        "category": "connectivity",
        "default_severity": "warning",
        "default_message": "Room program forbids adjacency that is present",
        "default_consequence": "Forbidden room relationships present in plan",
        "default_confidence": "high",
        "default_fixability": "operation_candidate_possible",
    },
}


def get_issue_definition(code: str) -> Dict[str, Any]:
    """Get full definition for an issue code."""
    if code in ISSUE_DEFINITIONS:
        return ISSUE_DEFINITIONS[code].copy()
    # Unknown code defaults
    return {
        "category": "unknown",
        "default_severity": "warning",
        "default_message": f"Unknown issue code: {code}",
        "default_consequence": "Unknown consequence",
        "default_confidence": "unknown",
        "default_fixability": "unknown",
    }


def get_issue_category(code: str) -> str:
    """Get category for an issue code."""
    definition = get_issue_definition(code)
    return definition.get("category", "unknown")


def get_default_severity(code: str) -> str:
    """Get default severity for an issue code."""
    definition = get_issue_definition(code)
    return definition.get("default_severity", "warning")


def is_known_issue_code(code: str) -> bool:
    """Check if an issue code is known."""
    return code in ISSUE_DEFINITIONS


def get_all_issue_codes() -> list:
    """Get list of all known issue codes."""
    return list(ISSUE_DEFINITIONS.keys())
