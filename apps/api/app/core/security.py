import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.errors import ErrorCode, IntegrationError


def _get_fernet() -> Fernet:
    """Derive a valid 32-byte url-safe base64 Fernet key from settings.TOKEN_ENCRYPTION_KEY."""
    try:
        key = settings.TOKEN_ENCRYPTION_KEY
        if not key or len(key.strip()) < 8:
            raise ValueError("Invalid encryption key configuration.")

        # Ensure it is 32 bytes url-safe base64
        try:
            # Try decoding to see if it is already a valid fernet key
            decoded = base64.urlsafe_b64decode(key.encode("utf-8"))
            if len(decoded) == 32:
                return Fernet(key.encode("utf-8"))
        except Exception:
            pass

        # If not 32 bytes url-safe base64, hash with SHA256 and base64-encode to derive a valid key
        derived_key = base64.urlsafe_b64encode(hashlib.sha256(key.encode("utf-8")).digest())
        return Fernet(derived_key)
    except Exception as e:
        raise IntegrationError(
            message="Token encryption service is unavailable or misconfigured.",
            code=ErrorCode.INTERNAL_ERROR,
            details={"raw_error": str(e)},
        ) from e


def encrypt_token(plain_token: str) -> str:
    """Encrypt OAuth refresh tokens or secrets before saving to canonical persistence."""
    if not plain_token:
        return ""
    try:
        f = _get_fernet()
        return f.encrypt(plain_token.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise IntegrationError(
            message="Failed to encrypt sensitive integration credentials.",
            code=ErrorCode.INTERNAL_ERROR,
            details={"raw_error": str(e)},
        ) from e


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt stored OAuth tokens in real-time server memory during provider calls."""
    if not encrypted_token:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise IntegrationError(
            message="Integration token is invalid or corrupted. Re-authentication required.",
            code=ErrorCode.INTEGRATION_TOKEN_INVALID,
        ) from exc
    except Exception as e:
        raise IntegrationError(
            message="Failed to decrypt integration credentials.",
            code=ErrorCode.INTERNAL_ERROR,
            details={"raw_error": str(e)},
        ) from e
