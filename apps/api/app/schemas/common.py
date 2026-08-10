from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None
    request_id: str = "N/A"


class ErrorResponse(BaseModel):
    error: ErrorDetail


class StatusMessage(BaseModel):
    status: str = "success"
    message: str
    details: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)
