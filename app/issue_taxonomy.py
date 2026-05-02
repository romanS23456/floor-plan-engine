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
