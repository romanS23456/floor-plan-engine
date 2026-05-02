from fastapi import FastAPI, HTTPException, Response
from app.models import Plan
from app.validation import validate_plan
from app.sample_data import get_valid_sample_plan
from app.svg_renderer import render_plan_svg
from app.constraints import PlanningConstraint
from typing import List, Optional
from pydantic import BaseModel

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
        from app.constraint_validation import validate_constraints
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
