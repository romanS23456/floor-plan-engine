from fastapi import FastAPI, HTTPException, Response
from app.models import Plan
from app.validation import validate_plan
from app.sample_data import get_valid_sample_plan
from app.svg_renderer import render_plan_svg

app = FastAPI(
    title="Floor Plan Engine",
    description="API-first backend for GPT/AI architect - structured geometry is the source of truth",
    version="0.2.0"
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/plans/validate")
def validate_plan_endpoint(plan: Plan):
    """
    Validate a floor plan and return validation results.
    
    Returns areas, errors, and warnings for the given plan.
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
