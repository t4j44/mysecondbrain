import hashlib
import mimetypes
from typing import Optional, Tuple

from app.core.constants import ALLOWED_MIME_TYPES, MAX_UPLOAD_SIZE_BYTES
from app.core.errors import ErrorCode, StorageError
from app.utils.sanitization import sanitize_filename


def calculate_checksum(content: bytes) -> str:
    """Generate SHA256 checksum of file bytes for deduplication and file verifiability."""
    return hashlib.sha256(content).hexdigest()


def validate_upload_file(
    filename: str, content: bytes, content_type: Optional[str] = None
) -> Tuple[str, str, str, int]:
    """
    Validate file extension, size, MIME type, and return sanitized_filename, ext, mime_type, size.
    Raises StorageError on violation.
    """
    size = len(content)
    if size > MAX_UPLOAD_SIZE_BYTES:
        raise StorageError(
            message=f"File exceeds limit of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB.",
            code=ErrorCode.FILE_TOO_LARGE,
            details={"size_bytes": size},
        )

    clean_name = sanitize_filename(filename)
    ext = clean_name.split(".")[-1].lower() if "." in clean_name else ""

    # If browser supplied content_type is missing or untrusted, guess via mimetypes
    guessed_mime, _ = mimetypes.guess_type(clean_name)
    final_mime = (content_type or guessed_mime or "application/octet-stream").lower()

    # Check if format is supported
    valid_exts = set(ALLOWED_MIME_TYPES.values()) | {"jpeg"}
    if ext not in valid_exts or (final_mime != "application/octet-stream" and ALLOWED_MIME_TYPES.get(final_mime) != ext and not (ext == "jpeg" and final_mime == "image/jpeg") and not (ext in {"md", "csv", "json"} and final_mime == "text/plain")):
        raise StorageError(
            message=f"File format '{final_mime}' or extension '.{ext}' is not supported.",
            code=ErrorCode.FILE_TYPE_NOT_SUPPORTED,
            details={"allowed_extensions": list(valid_exts)},
        )

    return clean_name, ext, final_mime, size
