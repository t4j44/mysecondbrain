from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --- INTEGRATION & GOOGLE SCHEMAS (Tasks 29, 30, 31) ---
class IntegrationResponse(BaseModel):
    id: str
    user_id: str
    provider_name: str
    account_identifier: Optional[str] = None
    scopes: List[str] = []
    is_connected: bool
    created_at: datetime
    updated_at: datetime
    # Notice: encrypted_tokens is intentionally EXCLUDED to ensure secrets never leave backend!
    model_config = ConfigDict(from_attributes=True)


class GoogleCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1)
    state: Optional[str] = None
    scope: Optional[str] = None


class GoogleCallbackResponse(BaseModel):
    status: str = "connected"
    provider: str = "google"
    account_identifier: str
    scopes_granted: List[str] = []
    message: str = "Google integration connected and credentials encrypted successfully."


class SyncDriveRequest(BaseModel):
    folder_id: Optional[str] = None
    sync_mode: str = "one_way"  # one_way or two_way


class SyncCalendarRequest(BaseModel):
    calendar_id: Optional[str] = "primary"
    time_min: Optional[datetime] = None
    time_max: Optional[datetime] = None


class JobResponse(BaseModel):
    id: str
    user_id: str
    job_type: str
    status: str
    retry_count: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    result_payload: Dict[str, Any] = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- EXPORT SCHEMAS (Task 32) ---
class ExportRequest(BaseModel):
    export_type: str = Field(default="full", pattern="^(record|module|full)$")
    target_module: Optional[str] = None
    record_id: Optional[str] = None
    include_attachments: bool = True


class ExportResponse(BaseModel):
    id: str
    user_id: str
    export_type: str
    status: str
    file_path: Optional[str] = None
    signed_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- AUDIT LOG SCHEMAS ---
class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    event_type: str
    target_entity: Optional[str] = None
    target_id: Optional[str] = None
    details: Dict[str, Any] = {}
    timestamp: datetime
    request_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
