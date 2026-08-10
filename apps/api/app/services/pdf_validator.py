import base64
import binascii
from typing import Tuple

from app.config import settings
from app.core.errors import (
    FileSizeExceededError,
    InvalidPayloadError,
    UnsupportedMediaTypeError,
)

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
]

MAGIC_BYTES_MAP = {
    b"%PDF": "application/pdf",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}


class PDFValidator:
    """Validator for PDF and image document payloads."""

    @staticmethod
    def clean_base64(file_data: str) -> str:
        """Removes data URI header if present (e.g. 'data:application/pdf;base64,...')."""
        if not file_data or not isinstance(file_data, str):
            raise InvalidPayloadError("Base64 file data must be a non-empty string")
        if "," in file_data:
            file_data = file_data.split(",", 1)[1]
        return file_data.strip()

    @staticmethod
    def decode_and_validate(
        file_data_b64: str,
        declared_mime_type: str = "application/pdf",
        max_size_mb: int = settings.MAX_FILE_SIZE_MB,
    ) -> Tuple[bytes, str]:
        """
        Decodes base64 document, checks byte size limits, and verifies magic byte MIME types.

        Returns:
            Tuple[bytes, str]: (raw_bytes, detected_or_verified_mime_type)
        """
        cleaned_b64 = PDFValidator.clean_base64(file_data_b64)

        try:
            raw_bytes = base64.b64decode(cleaned_b64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise InvalidPayloadError(f"Corrupt or invalid base64 encoding: {exc}") from exc

        byte_length = len(raw_bytes)

        if byte_length == 0:
            raise InvalidPayloadError("Document payload is empty (0 bytes)")

        max_bytes = max_size_mb * 1024 * 1024
        if byte_length > max_bytes:
            raise FileSizeExceededError(max_mb=max_size_mb, actual_bytes=byte_length)

        # Verify declared MIME type against allowed list
        normalized_mime = declared_mime_type.lower().strip()
        if normalized_mime not in ALLOWED_MIME_TYPES:
            raise UnsupportedMediaTypeError(
                mime_type=declared_mime_type, allowed_types=ALLOWED_MIME_TYPES
            )

        # Magic byte verification
        detected_mime = PDFValidator.detect_mime_type(raw_bytes)
        final_mime = detected_mime or normalized_mime

        if final_mime not in ALLOWED_MIME_TYPES:
            raise UnsupportedMediaTypeError(mime_type=final_mime, allowed_types=ALLOWED_MIME_TYPES)

        return raw_bytes, final_mime

    @staticmethod
    def detect_mime_type(raw_bytes: bytes) -> str | None:
        """Detect MIME type from initial magic bytes."""
        for magic, mime in MAGIC_BYTES_MAP.items():
            if raw_bytes.startswith(magic):
                return mime
        if len(raw_bytes) >= 12 and raw_bytes.startswith(b"RIFF") and raw_bytes[8:12] == b"WEBP":
            return "image/webp"
        return None
