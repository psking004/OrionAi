from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

VALID_STATUSES = {"active", "paused", "completed", "archived"}


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    status: str = "active"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty")
        if len(v) > 200:
            raise ValueError("Project name too long (max 200 chars)")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        return v


class ProjectResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    tech_stack: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
