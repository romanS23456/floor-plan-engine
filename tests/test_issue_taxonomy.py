"""Tests for issue taxonomy in Floor Plan Engine."""

import pytest
from app.issue_taxonomy import (
    get_issue_definition,
    get_issue_category,
    get_default_severity,
    is_known_issue_code,
    ISSUE_CATEGORIES,
    ISSUE_SEVERITIES,
)
from app.issues import make_issue


def test_known_issue_code_returns_definition():
    """Known issue codes return full definition."""
    code = "ROOM_OVERLAP"
    definition = get_issue_definition(code)
    
    assert definition["category"] == "geometry"
    assert definition["default_severity"] == "error"
    assert "overlap" in definition["default_message"].lower()
    assert definition["default_confidence"] == "high"


def test_unknown_issue_code_returns_unknown_defaults():
    """Unknown issue codes return unknown category with warning severity."""
    code = "UNKNOWN_FAKE_CODE_12345"
    definition = get_issue_definition(code)
    
    assert definition["category"] == "unknown"
    assert definition["default_severity"] == "warning"
    assert not is_known_issue_code(code)


def test_get_issue_category_for_room_overlap():
    """ROOM_OVERLAP has geometry category."""
    category = get_issue_category("ROOM_OVERLAP")
    assert category == "geometry"


def test_make_issue_uses_taxonomy_defaults():
    """make_issue uses taxonomy defaults when not provided."""
    issue = make_issue(
        code="ROOM_OVERLAP",
        entity_refs=[{"type": "room", "id": "room1"}, {"type": "room", "id": "room2"}],
    )
    
    # Should use taxonomy defaults
    assert issue["category"] == "geometry"
    assert issue["severity"] == "error"
    assert issue["confidence"] == "high"
    assert issue["fixability"] == "manual_review_required"
    assert "room_overlap" in issue["id"]


def test_all_severities_are_valid():
    """All defined severities are in allowed list."""
    for code in ["ROOM_OVERLAP", "NO_ENTRY_ROOM", "PRIVACY_DIRECT_PUBLIC_PRIVATE"]:
        severity = get_default_severity(code)
        assert severity in ISSUE_SEVERITIES


def test_all_categories_are_valid():
    """All defined categories are in allowed list."""
    codes = [
        "ROOM_OVERLAP",  # geometry
        "INVALID_DOOR_FROM_ROOM_REFERENCE",  # references
        "UNREACHABLE_ROOM",  # connectivity
        "PANTRY_THROUGH_BATHROOM",  # privacy
        "ROOM_AREA_BELOW_MINIMUM",  # area
        "FURNITURE_OUTSIDE_ROOM",  # furniture
        "CONSTRAINT_MIN_AREA_VIOLATION",  # constraints
    ]
    
    for code in codes:
        category = get_issue_category(code)
        assert category in ISSUE_CATEGORIES, f"Category {category} for {code} not in allowed list"


def test_constraint_codes_exist():
    """All constraint violation codes are defined."""
    constraint_codes = [
        "CONSTRAINT_MIN_AREA_VIOLATION",
        "CONSTRAINT_MAX_AREA_VIOLATION",
        "CONSTRAINT_REQUIRED_CONNECTION_MISSING",
        "CONSTRAINT_FORBIDDEN_CONNECTION_EXISTS",
        "CONSTRAINT_REQUIRED_ROOM_TYPE_MISSING",
        "CONSTRAINT_REQUIRED_ACCESS_FROM_ENTRY_MISSING",
        "CONSTRAINT_TARGET_NOT_FOUND",
        "CONSTRAINT_INVALID_DEFINITION",
    ]
    
    for code in constraint_codes:
        assert is_known_issue_code(code), f"Code {code} should be known"
        definition = get_issue_definition(code)
        assert definition["category"] == "constraints"
