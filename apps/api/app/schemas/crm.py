from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

# --- Organization Schemas ---


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    website_url: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    website_url: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OrganizationResponse(OrganizationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Wrapped single organization
class OrganizationWrappedResponse(BaseModel):
    data: OrganizationResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


# Wrapped list of organizations
class OrganizationListResponse(BaseModel):
    data: List[OrganizationResponse]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


# --- Person Schemas ---


class PersonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    organization_id: Optional[UUID] = None
    role: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = None
    relationship_type: str = Field("contact")
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("relationship_type")
    def validate_relationship_type(cls, v):
        allowed = {"mentor", "investor", "peer", "collaborator", "lead", "client", "contact"}
        if v not in allowed:
            raise ValueError(f"relationship_type must be one of {allowed}")
        return v


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    organization_id: Optional[UUID] = None
    role: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = None
    relationship_type: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("relationship_type")
    def validate_relationship_type(cls, v):
        if v is None:
            return v
        allowed = {"mentor", "investor", "peer", "collaborator", "lead", "client", "contact"}
        if v not in allowed:
            raise ValueError(f"relationship_type must be one of {allowed}")
        return v


class PersonResponse(PersonBase):
    id: UUID
    user_id: UUID
    last_interaction_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Wrapped single person
class PersonWrappedResponse(BaseModel):
    data: PersonResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


# Wrapped list of people
class PeopleListResponse(BaseModel):
    data: List[PersonResponse]
    pagination: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


# --- Relationship Schemas ---
class RelationshipCreateRequest(BaseModel):
    source_person_id: UUID
    target_person_id: UUID
    relationship_nature: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None


class RelationshipResponse(BaseModel):
    id: UUID
    user_id: UUID
    source_person_id: UUID
    target_person_id: UUID
    relationship_nature: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
