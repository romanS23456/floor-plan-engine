"""Request models for Floor Plan Engine."""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.models import Plan
from app.constraints import PlanningConstraint
from app.project_brief import ProjectBrief
from app.room_program import RoomProgram


class ProjectBriefValidationRequest(BaseModel):
    """Request model for brief validation endpoint."""
    project_brief: ProjectBrief


class PlanBriefValidationRequest(BaseModel):
    """Request model for plan validation with brief endpoint."""
    plan: Plan
    project_brief: ProjectBrief
    constraints: List[PlanningConstraint] = Field(default_factory=list)


class PlanProgramCheckRequest(BaseModel):
    """Request model for program validation endpoint."""
    plan: Plan
    program: RoomProgram
