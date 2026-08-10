from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class MemoryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=50)
    tags: List[str] = Field(default_factory=list)
    linked_venture_id: Optional[UUID] = None
    linked_person_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("category")
    def validate_category(cls, v):
        if v is None:
            return v
        allowed = {
            "reflection",
            "lesson",
            "win",
            "failure",
            "observation",
            "decision_context",
            "quote",
        }
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v


class MemoryCreate(MemoryBase):
    pass


class MemoryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    linked_venture_id: Optional[UUID] = None
    linked_person_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("category")
    def validate_category(cls, v):
        if v is None:
            return v
        allowed = {
            "reflection",
            "lesson",
            "win",
            "failure",
            "observation",
            "decision_context",
            "quote",
        }
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v


class MemoryResponse(MemoryBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Wrapped single memory
class MemoryWrappedResponse(BaseModel):
    data: MemoryResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


# Wrapped list of memories
class MemoryListResponse(BaseModel):
    data: List[MemoryResponse]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)
