from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class InteractionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    person_id: Optional[UUID] = None
    venture_id: Optional[UUID] = None
    interaction_type: str = Field("meeting")
    summary: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    key_takeaways: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    markdown_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("interaction_type")
    def validate_interaction_type(cls, v):
        allowed = {"meeting", "call", "email", "chat", "event", "note"}
        if v not in allowed:
            raise ValueError(f"interaction_type must be one of {allowed}")
        return v


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    person_id: Optional[UUID] = None
    venture_id: Optional[UUID] = None
    interaction_type: Optional[str] = None
    summary: Optional[str] = None
    date: Optional[datetime] = None
    key_takeaways: Optional[List[str]] = None
    next_actions: Optional[List[str]] = None
    markdown_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("interaction_type")
    def validate_interaction_type(cls, v):
        if v is None:
            return v
        allowed = {"meeting", "call", "email", "chat", "event", "note"}
        if v not in allowed:
            raise ValueError(f"interaction_type must be one of {allowed}")
        return v


class InteractionResponse(InteractionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Wrapped single interaction
class InteractionWrappedResponse(BaseModel):
    data: InteractionResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


# Wrapped list of interactions
class InteractionListResponse(BaseModel):
    data: List[InteractionResponse]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)
