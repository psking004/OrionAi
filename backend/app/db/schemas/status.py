from datetime import datetime
from typing import List
from pydantic import BaseModel


class ProjectStatusResponse(BaseModel):
    id: int
    project_id: int
    progress: str
    problems: List[str]
    stuck_points: List[str]
    next_steps: List[str]
    missing_features: List[str]
    health_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class NextStepsResponse(BaseModel):
    project_id: int
    roadmap: List[str]
    steps: List[str]
