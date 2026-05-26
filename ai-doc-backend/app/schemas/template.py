from datetime import datetime
from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=128)
    analyze_type: str = Field(..., pattern="^(policy|bidding)$")


class TemplateResponse(BaseModel):
    id: int
    user_id: int
    template_name: str
    analyze_type: str
    minio_key: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True
