from fastapi import FastAPI, HTTPException
from app.models import Plan
from app.validation import validate_plan
from app.sample_data import get_valid_sample_plan

app = FastAPI(
    title="Floor Plan Engine",
    description="API-first backend for GPT/AI architect - structured geometry is the source of truth",
    version="0.1.0"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
