from datetime import datetime
from typing import Literal
from pydantic import BaseModel, field_validator


class MessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message content cannot be empty")
        if len(v) > 32_000:
            raise ValueError("Message content too long (max 32,000 chars)")
        return v


class MessageResponse(BaseModel):
    id: int
    project_id: int
    role: str
    content: str
    timestamp: datetime

    model_config = {"from_attributes": True}
