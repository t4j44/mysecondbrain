from enum import Enum


class ErrorCode(str, Enum):
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_ACCESS_TOKEN = "INVALID_ACCESS_TOKEN"
    ACCESS_TOKEN_EXPIRED = "ACCESS_TOKEN_EXPIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    CONFLICT = "CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    RELATED_RESOURCE_NOT_FOUND = "RELATED_RESOURCE_NOT_FOUND"
    RELATED_RESOURCE_FORBIDDEN = "RELATED_RESOURCE_FORBIDDEN"
    FILE_TYPE_NOT_SUPPORTED = "FILE_TYPE_NOT_SUPPORTED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    DOCUMENT_PROCESSING_FAILED = "DOCUMENT_PROCESSING_FAILED"
    INTEGRATION_NOT_CONNECTED = "INTEGRATION_NOT_CONNECTED"
    INTEGRATION_TOKEN_INVALID = "INTEGRATION_TOKEN_INVALID"
    INTEGRATION_REAUTH_REQUIRED = "INTEGRATION_REAUTH_REQUIRED"
    SYNC_JOB_FAILED = "SYNC_JOB_FAILED"
    EXPORT_JOB_FAILED = "EXPORT_JOB_FAILED"
    AI_PROVIDER_NOT_CONFIGURED = "AI_PROVIDER_NOT_CONFIGURED"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File Upload rules
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit
ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "text/markdown": "md",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

# Task status transition rules
VALID_TASK_STATUSES = {"todo", "in_progress", "done", "cancelled"}
VALID_TASK_PRIORITIES = {"low", "medium", "high", "urgent"}

# Venture statuses
VALID_VENTURE_STATUSES = {"active", "paused", "archived", "exited"}

# Protected fields that clients cannot modify directly
PROTECTED_FIELDS = {
    "user_id",
    "created_at",
    "updated_at",
    "deleted_at",
    "archived_at",
    "embedding_status",
    "processing_status",
    "provider_usage_metadata",
    "audit_metadata",
    "encrypted_tokens",
    "refresh_token",
}
