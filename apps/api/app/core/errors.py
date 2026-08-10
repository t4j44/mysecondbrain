from typing import Any, Dict, Optional

from fastapi.responses import JSONResponse

from app.core.constants import ErrorCode


class AppError(Exception):
    """Base hierarchy class for structured domain errors across Taj's Second Brain."""

    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code.value if isinstance(code, ErrorCode) else str(code)
        self.status_code = status_code
        self.details = details
        self.headers = headers

    def to_dict(self, request_id: str = "N/A") -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "request_id": request_id,
            }
        }

    def to_json_response(self, request_id: str = "N/A") -> JSONResponse:
        resp_headers = {"X-Request-ID": request_id}
        if self.headers:
            resp_headers.update(self.headers)
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict(request_id=request_id),
            headers=resp_headers,
        )


class AuthenticationError(AppError):
    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.AUTHENTICATION_REQUIRED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=401, details=details)


class AuthorizationError(AppError):
    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.PERMISSION_DENIED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=403, details=details)


class NotFoundError(AppError):
    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.RESOURCE_NOT_FOUND,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=404, details=details)


class ConflictError(AppError):
    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.DUPLICATE_RESOURCE,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=409, details=details)


class ValidationError(AppError):
    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.VALIDATION_FAILED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=400, details=details)


class AIProviderError(AppError):
    def __init__(
        self,
        message: Optional[str] = None,
        provider_message: Optional[str] = None,
        provider: Optional[str] = None,
        code: Any = "AI_SERVICE_UNAVAILABLE",
        details: Optional[Dict[str, Any]] = None,
    ):
        msg = message or provider_message or f"AI Provider ({provider}) encountered an error."
        err_details = details or {}
        if provider:
            err_details["provider"] = provider
        if provider_message and not message:
            err_details["provider_message"] = provider_message
        super().__init__(message=msg, code=code, status_code=503, details=err_details)


class IntegrationError(AppError):
    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.INTEGRATION_NOT_CONNECTED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=400, details=details)


class StorageError(AppError):
    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.FILE_UPLOAD_FAILED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, code=code, status_code=500, details=details)


class PDFAnalysisError(AppError):
    """Base exception for PDF & image analysis operations."""

    def __init__(
        self,
        message: str,
        code: Any = ErrorCode.DOCUMENT_PROCESSING_FAILED,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            message=message, code=code, status_code=status_code, details=details, headers=headers
        )


class FileSizeExceededError(PDFAnalysisError):
    """Raised when an uploaded document or image exceeds the maximum permitted file size."""

    def __init__(
        self,
        message: Optional[str] = None,
        max_bytes: Optional[int] = None,
        max_mb: Optional[float] = None,
        actual_bytes: Optional[int] = None,
    ):
        msg = message or "Uploaded file size exceeds maximum allowed limit."
        details: Dict[str, Any] = {}
        if max_bytes is not None:
            details["max_size_bytes"] = max_bytes
        if max_mb is not None:
            details["max_size_mb"] = max_mb
        if actual_bytes is not None:
            details["actual_size_bytes"] = actual_bytes
        super().__init__(
            message=msg,
            code=ErrorCode.FILE_TOO_LARGE,
            status_code=413,
            details=details or None,
        )


class UnsupportedMediaTypeError(PDFAnalysisError):
    """Raised when the submitted document or image MIME type is unsupported."""

    def __init__(
        self,
        message: Optional[str] = None,
        mime_type: Optional[str] = None,
        allowed_types: Optional[list[str]] = None,
    ):
        msg = message or "The submitted media type is not supported for document analysis."
        details: Dict[str, Any] = {}
        if mime_type is not None:
            details["submitted_mime_type"] = mime_type
        if allowed_types is not None:
            details["allowed_mime_types"] = allowed_types
        super().__init__(
            message=msg,
            code="UNSUPPORTED_MEDIA_TYPE",
            status_code=415,
            details=details or None,
        )


class InvalidPayloadError(PDFAnalysisError):
    """Raised when an inline payload is malformed or improperly encoded."""

    def __init__(self, message: str = "Corrupt or invalid base64 payload."):
        super().__init__(
            message=message,
            code="INVALID_BASE64",
            status_code=400,
        )


class RateLimitExceededError(PDFAnalysisError):
    """Raised when downstream provider rate limits are exceeded."""

    def __init__(
        self,
        message: str = "Downstream analysis rate limits exceeded. Please retry later.",
        retry_after_seconds: Optional[int] = None,
    ):
        details = {"retry_after_seconds": retry_after_seconds} if retry_after_seconds else None
        headers = {"Retry-After": str(retry_after_seconds)} if retry_after_seconds else None
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
            headers=headers,
        )
