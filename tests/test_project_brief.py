"""Tests for Project Brief functionality (MVP 6)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.project_brief import ProjectBrief, Household, Lifestyle
from app.models import Plan, Room, Door, Window, Furniture
from app.brief_validation import validate_project_brief, validate_plan_against_brief

client = TestClient(app)


def make_sample_plan():
    """Create a minimal sample plan for testing."""
    return Plan(
        rooms=[
            Room(
                id="room1",
                name="Living Room",
                polygon_mm=[[0, 0], [4000, 0], [4000, 3000], [0, 3000]],
                room_type="public"
            ),
            Room(
                id="room2",
                name="Bedroom",
                polygon_mm=[[4000, 0], [7000, 0], [7000, 3000], [4000, 3000]],
                room_type="private"
            ),
            Room(
                id="room3",
                name="Kitchen",
                polygon_mm=[[0, 3000], [4000, 3000], [4000, 5000], [0, 5000]],
                room_type="public"
            ),
            Room(
                id="room4",
                name="Bathroom",
                polygon_mm=[[4000, 3000], [7000, 3000], [7000, 5000], [4000, 5000]],
                room_type="private"
            ),
        ],
        doors=[
            Door(
                id="door1",
                from_room_id="room1",
                to_room_id="room2",
                position_mm=[4000, 1500],
                width_mm=900
            ),
            Door(
                id="door2",
                from_room_id="room1",
                to_room_id="room3",
                position_mm=[2000, 3000],
                width_mm=900
            ),
            Door(
                id="door3",
                from_room_id="room3",
                to_room_id="room4",
                position_mm=[4000, 4000],
                width_mm=800
            ),
        ],
        windows=[
            Window(
                id="window1",
                room_id="room1",
                position_mm=[2000, 0],
                width_mm=1200
            ),
        ],
        furniture=[]
    )


def test_complete_brief_high_score():
    """Complete brief returns score >= 60 and is_ready_for_plan_review true."""
    brief = ProjectBrief(
        project_type="private_house",
        stage="concept_design",
        household=Household(adults=2, children=1),
        lifestyle=Lifestyle(cooks_often=True, works_from_home=False),
        priorities=["cost_efficiency", "natural_light"],
        budget_level="medium",
        construction_method="traditional",
        target_total_area_m2=120.0,
        floors_count=1
    )
    
    result = validate_project_brief(brief)
    
    assert result["brief_completeness"]["score"] >= 60
    assert result["brief_completeness"]["is_ready_for_plan_review"] is True
    assert len(result["brief_completeness"]["missing_fields"]) == 0


def test_missing_household_returns_issue():
    """Missing household creates BRIEF_MISSING_HOUSEHOLD."""
    brief = ProjectBrief(
        project_type="private_house",
        stage="concept_design",
        household=None,
        lifestyle=Lifestyle(),
        priorities=["cost_efficiency"],
        budget_level="medium",
        construction_method="traditional",
        target_total_area_m2=120.0,
        floors_count=1
    )
    
    result = validate_project_brief(brief)
    
    issue_codes = [issue["code"] for issue in result["brief_issues"]]
    assert "BRIEF_MISSING_HOUSEHOLD" in issue_codes
    assert "household" in result["brief_completeness"]["missing_fields"]


def test_missing_priorities_returns_issue():
    """Empty priorities creates BRIEF_MISSING_PRIORITIES."""
    brief = ProjectBrief(
        project_type="private_house",
        stage="concept_design",
        household=Household(adults=2),
        lifestyle=Lifestyle(),
        priorities=[],
        budget_level="medium",
        construction_method="traditional",
        target_total_area_m2=120.0,
        floors_count=1
    )
    
    result = validate_project_brief(brief)
    
    issue_codes = [issue["code"] for issue in result["brief_issues"]]
    assert "BRIEF_MISSING_PRIORITIES" in issue_codes
    assert "priorities" in result["brief_completeness"]["missing_fields"]


def test_unknown_construction_method_tracked():
    """construction_method='unknown' appears in unknown_fields or creates BRIEF_UNKNOWN_CONSTRUCTION_METHOD."""
    brief = ProjectBrief(
        project_type="private_house",
        stage="concept_design",
        household=Household(adults=2),
        lifestyle=Lifestyle(),
        priorities=["cost_efficiency"],
        budget_level="medium",
        construction_method="unknown",
        target_total_area_m2=120.0,
        floors_count=1
    )
    
    result = validate_project_brief(brief)
    
    # Either in unknown_fields or as an issue
    has_unknown = "construction_method" in result["brief_completeness"]["unknown_fields"]
    issue_codes = [issue["code"] for issue in result["brief_issues"]]
    has_issue = "BRIEF_UNKNOWN_CONSTRUCTION_METHOD" in issue_codes
    
    assert has_unknown or has_issue


def test_low_completeness_returns_warning():
    """Mostly empty brief creates BRIEF_LOW_COMPLETENESS."""
    brief = ProjectBrief()
    
    result = validate_project_brief(brief)
    
    issue_codes = [issue["code"] for issue in result["brief_issues"]]
    assert "BRIEF_LOW_COMPLETENESS" in issue_codes
    assert result["brief_completeness"]["score"] < 60
    assert result["brief_completeness"]["is_ready_for_plan_review"] is False


def test_unsupported_project_type_returns_plan_brief_issue():
    """project_type='apartment' creates BRIEF_UNSUPPORTED_PROJECT_TYPE."""
    plan = make_sample_plan()
    brief = ProjectBrief(
        project_type="apartment",
        stage="concept_design",
        household=Household(adults=2),
        lifestyle=Lifestyle(),
        priorities=["cost_efficiency"],
        budget_level="medium",
        construction_method="traditional",
        target_total_area_m2=80.0,
        floors_count=1
    )
    
    result = validate_plan_against_brief(plan, brief)
    
    issue_codes = [issue["code"] for issue in result["brief_plan_issues"]]
    assert "BRIEF_UNSUPPORTED_PROJECT_TYPE" in issue_codes


def test_works_from_home_without_workspace_returns_hint():
    """lifestyle.works_from_home true and no office room returns BRIEF_WORK_FROM_HOME_WITHOUT_WORKSPACE_HINT."""
    plan = make_sample_plan()
    brief = ProjectBrief(
        project_type="private_house",
        stage="concept_design",
        household=Household(adults=2),
        lifestyle=Lifestyle(works_from_home=True),
        priorities=["cost_efficiency"],
        budget_level="medium",
        construction_method="traditional",
        target_total_area_m2=120.0,
        floors_count=1
    )
    
    result = validate_plan_against_brief(plan, brief)
    
    issue_codes = [issue["code"] for issue in result["brief_plan_issues"]]
    assert "BRIEF_WORK_FROM_HOME_WITHOUT_WORKSPACE_HINT" in issue_codes


def test_cooks_often_without_kitchen_returns_hint():
    """lifestyle.cooks_often true and no kitchen/public room returns BRIEF_COOKS_OFTEN_WITHOUT_KITCHEN_HINT."""
    # Create a plan without kitchen or public rooms
    plan = Plan(
        rooms=[
            Room(
                id="room1",
                name="Bedroom 1",
                polygon_mm=[[0, 0], [4000, 0], [4000, 3000], [0, 3000]],
                room_type="private"
            ),
            Room(
                id="room2",
                name="Bedroom 2",
                polygon_mm=[[4000, 0], [7000, 0], [7000, 3000], [4000, 3000]],
                room_type="private"
            ),
        ],
        doors=[
            Door(
                id="door1",
                from_room_id="room1",
                to_room_id="room2",
                position_mm=[4000, 1500],
                width_mm=900
            ),
        ],
        windows=[],
        furniture=[]
    )
    
    brief = ProjectBrief(
        project_type="private_house",
        stage="concept_design",
        household=Household(adults=2),
        lifestyle=Lifestyle(cooks_often=True),
        priorities=["cost_efficiency"],
        budget_level="medium",
        construction_method="traditional",
        target_total_area_m2=120.0,
        floors_count=1
    )
    
    result = validate_plan_against_brief(plan, brief)
    
    issue_codes = [issue["code"] for issue in result["brief_plan_issues"]]
    assert "BRIEF_COOKS_OFTEN_WITHOUT_KITCHEN_HINT" in issue_codes


def test_validate_with_brief_shape_contains_existing_blocks():
    """Response contains areas, errors, warnings, issues, connectivity, geometry."""
    plan = make_sample_plan()
    brief = ProjectBrief(
        project_type="private_house",
        stage="concept_design",
        household=Household(adults=2),
        lifestyle=Lifestyle(),
        priorities=["cost_efficiency"],
        budget_level="medium",
        construction_method="traditional",
        target_total_area_m2=120.0,
        floors_count=1
    )
    
    response = client.post("/plans/validate-with-brief", json={
        "plan": plan.model_dump(),
        "project_brief": brief.model_dump()
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Check standard validation blocks exist
    assert "areas" in data
    assert "errors" in data
    assert "warnings" in data
    assert "issues" in data
    assert "connectivity" in data
    assert "geometry" in data
    
    # Check MVP 6 blocks exist
    assert "brief_completeness" in data
    assert "brief_issues" in data
    assert "brief_plan_issues" in data
