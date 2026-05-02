from fastapi import FastAPI, HTTPException, Response
from app.models import Plan
from app.validation import validate_plan
from app.sample_data import get_valid_sample_plan
from app.svg_renderer import render_plan_svg
from app.constraints import PlanningConstraint
from typing import List, Optional
from pydantic import BaseModel

from app.request_models import ProjectBriefValidationRequest, PlanBriefValidationRequest, PlanProgramValidationRequest
from app.brief_validation import validate_project_brief, validate_plan_against_brief
from app.constraint_validation import validate_constraints
from app.program_validation import validate_room_program

app = FastAPI(
    title="Floor Plan Engine",
    description="API-first backend for GPT/AI architect - structured geometry is the source of truth",
    version="0.4.0"
)


class PlanConstraintValidationRequest(BaseModel):
    """Request model for validate-with-constraints endpoint."""
    plan: Plan
    constraints: List[PlanningConstraint] = []


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/plans/validate")
def validate_plan_endpoint(plan: Plan):
    """
    Validate a floor plan and return validation results.
    
    Returns areas, errors, warnings, connectivity info, issues, and geometry checks.
    """
    try:
        result = validate_plan(plan)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/plans/render-svg")
def render_svg_endpoint(plan: Plan, width: int = 800, height: int = 600):
    """
    Render a floor plan as SVG for debug visualization.
    
    Returns SVG with rooms, labels, areas, doors, windows, and furniture.
    Uses data-id and data-entity-type attributes for programmatic access.
    """
    try:
        svg_content = render_plan_svg(plan, width=width, height=height)
        return Response(content=svg_content, media_type="image/svg+xml")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/plans/validate-with-constraints")
def validate_with_constraints_endpoint(request: PlanConstraintValidationRequest):
    """
    Validate a floor plan with custom planning constraints.
    
    MVP 5: Validates plan against both built-in rules and user-provided constraints.
    Returns all standard validation fields plus constraint_violations and constraints_summary.
    """
    try:
        # Run standard validation
        result = validate_plan(request.plan)
        
        # Run constraint validation
        constraint_result = validate_constraints(request.plan, request.constraints)
        
        # Add constraint results to response
        result["constraints"] = [c.model_dump() for c in request.constraints]
        result["constraint_violations"] = constraint_result["constraint_violations"]
        result["constraints_summary"] = constraint_result["constraints_summary"]
        
        # Append constraint violations to issues list
        result["issues"].extend(constraint_result["constraint_violations"])
        
        # Mirror constraint violations into legacy errors/warnings based on severity
        for violation in constraint_result["constraint_violations"]:
            severity = violation.get("severity", "warning")
            message = f"{violation.get('code', 'UNKNOWN')}: {violation.get('message', '')}"
            if severity == "error":
                result["errors"].append(message)
            else:  # warning or info
                result["warnings"].append(message)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/briefs/validate")
def validate_brief_endpoint(request: ProjectBriefValidationRequest):
    """
    Validate a project brief and return completeness assessment.
    
    MVP 6: Returns brief_completeness score and brief_issues.
    Does not require a plan - validates only the brief context.
    """
    try:
        result = validate_project_brief(request.project_brief)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/plans/validate-with-brief")
def validate_plan_with_brief_endpoint(request: PlanBriefValidationRequest):
    """
    Validate a floor plan with project brief context.
    
    MVP 6: Combines plan validation, brief validation, and plan-against-brief checks.
    Optionally includes constraint validation if constraints are provided.
    
    Returns:
        - All standard validation fields (areas, errors, warnings, issues, connectivity, geometry)
        - brief_completeness
        - brief_issues
        - brief_plan_issues
        - constraints_summary (if constraints provided)
        - constraint_violations (if constraints provided)
    """
    try:
        # Run standard plan validation
        result = validate_plan(request.plan)
        
        # Run brief validation
        brief_result = validate_project_brief(request.project_brief)
        
        # Run plan-against-brief validation
        plan_brief_result = validate_plan_against_brief(request.plan, request.project_brief)
        
        # Add brief results to response
        result["brief_completeness"] = brief_result["brief_completeness"]
        result["brief_issues"] = brief_result["brief_issues"]
        result["brief_plan_issues"] = plan_brief_result["brief_plan_issues"]
        
        # Append brief issues and plan-brief issues to main issues list
        result["issues"].extend(brief_result["brief_issues"])
        result["issues"].extend(plan_brief_result["brief_plan_issues"])
        
        # Handle constraints if provided
        if request.constraints:
            constraint_result = validate_constraints(request.plan, request.constraints)
            
            result["constraints"] = [c.model_dump() for c in request.constraints]
            result["constraint_violations"] = constraint_result["constraint_violations"]
            result["constraints_summary"] = constraint_result["constraints_summary"]
            
            # Append constraint violations to issues list
            result["issues"].extend(constraint_result["constraint_violations"])
            
            # Mirror constraint violations into legacy errors/warnings
            for violation in constraint_result["constraint_violations"]:
                severity = violation.get("severity", "warning")
                message = f"{violation.get('code', 'UNKNOWN')}: {violation.get('message', '')}"
                if severity == "error":
                    result["errors"].append(message)
                else:
                    result["warnings"].append(message)
        
        # Mirror brief issues severity to legacy errors/warnings
        for issue in brief_result["brief_issues"] + plan_brief_result["brief_plan_issues"]:
            severity = issue.get("severity", "warning")
            message = f"{issue.get('code', 'UNKNOWN')}: {issue.get('message', '')}"
            if severity == "error":
                result["errors"].append(message)
            else:
                result["warnings"].append(message)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/plans/program-check")
def program_check_endpoint(request: PlanProgramValidationRequest):
    """
    Validate a floor plan against a RoomProgram.
    
    MVP 7: Validates plan against room program requirements including:
    - Required room types and counts
    - Min/max/target area requirements
    - Direct adjacency requirements
    - Separated adjacency requirements
    
    Optionally includes:
    - Constraint validation if constraints provided
    - Brief validation if project_brief provided
    
    Returns:
        - All standard validation fields (areas, errors, warnings, issues, connectivity, geometry)
        - program_summary
        - program_issues
        - constraints_summary (if constraints provided)
        - constraint_violations (if constraints provided)
        - brief_completeness (if project_brief provided)
        - brief_issues (if project_brief provided)
        - brief_plan_issues (if project_brief provided)
    """
    try:
        # Run standard plan validation
        result = validate_plan(request.plan)
        
        # Run room program validation
        program_result = validate_room_program(request.plan, request.room_program)
        
        # Add program results to response
        result["program_summary"] = program_result["program_summary"]
        result["program_issues"] = program_result["program_issues"]
        
        # Append program issues to main issues list
        result["issues"].extend(program_result["program_issues"])
        
        # Mirror program issues severity to legacy errors/warnings
        for issue in program_result["program_issues"]:
            severity = issue.get("severity", "warning")
            message = f"{issue.get('code', 'UNKNOWN')}: {issue.get('message', '')}"
            if severity == "error":
                result["errors"].append(message)
            else:
                result["warnings"].append(message)
        
        # Handle constraints if provided
        if request.constraints:
            constraint_result = validate_constraints(request.plan, request.constraints)
            
            result["constraints"] = [c.model_dump() for c in request.constraints]
            result["constraint_violations"] = constraint_result["constraint_violations"]
            result["constraints_summary"] = constraint_result["constraints_summary"]
            
            # Append constraint violations to issues list
            result["issues"].extend(constraint_result["constraint_violations"])
            
            # Mirror constraint violations into legacy errors/warnings
            for violation in constraint_result["constraint_violations"]:
                severity = violation.get("severity", "warning")
                message = f"{violation.get('code', 'UNKNOWN')}: {violation.get('message', '')}"
                if severity == "error":
                    result["errors"].append(message)
                else:
                    result["warnings"].append(message)
        
        # Handle project brief if provided
        if request.project_brief:
            brief_result = validate_project_brief(request.project_brief)
            plan_brief_result = validate_plan_against_brief(request.plan, request.project_brief)
            
            result["brief_completeness"] = brief_result["brief_completeness"]
            result["brief_issues"] = brief_result["brief_issues"]
            result["brief_plan_issues"] = plan_brief_result["brief_plan_issues"]
            
            # Append brief issues to main issues list
            result["issues"].extend(brief_result["brief_issues"])
            result["issues"].extend(plan_brief_result["brief_plan_issues"])
            
            # Mirror brief issues severity to legacy errors/warnings
            for issue in brief_result["brief_issues"] + plan_brief_result["brief_plan_issues"]:
                severity = issue.get("severity", "warning")
                message = f"{issue.get('code', 'UNKNOWN')}: {issue.get('message', '')}"
                if severity == "error":
                    result["errors"].append(message)
                else:
                    result["warnings"].append(message)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
