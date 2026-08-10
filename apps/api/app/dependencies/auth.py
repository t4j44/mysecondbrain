from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings
from app.core.constants import ErrorCode
from app.core.errors import AuthenticationError
from app.core.logging import logger

security_bearer = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    id: str  # User UUID derived strictly from token sub claim
    email: str
    role: str = "authenticated"
    app_metadata: Dict[str, Any] = {}
    user_metadata: Dict[str, Any] = {}

    def is_founder(self) -> bool:
        """Verify if user possesses primary founder administrative role or ownership."""
        return self.role in {"authenticated", "founder", "admin"}


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> AuthenticatedUser:
    """
    Verify Supabase JWT locally without network latency (ADR-003).
    Strictly forbids client-provided user_id in headers or bodies from supplanting token claims.
    """
    if not credentials:
        raise AuthenticationError(
            message="Missing authentication Bearer token.",
            code=ErrorCode.AUTHENTICATION_REQUIRED,
        )

    token = credentials.credentials
    request_id = getattr(request.state, "request_id", "N/A")

    try:
        # Verify JWT using symmetric HS256 project secret or test override secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": True, "verify_sub": True},
        )
    except jwt.ExpiredSignatureError as exc:
        logger.warning(
            "Expired authentication token provided in request.",
            extra={"request_id": request_id, "error_code": ErrorCode.ACCESS_TOKEN_EXPIRED.value},
        )
        raise AuthenticationError(
            message="Access token has expired. Please refresh your credentials.",
            code=ErrorCode.ACCESS_TOKEN_EXPIRED,
        ) from exc
    except jwt.InvalidTokenError as exc:
        logger.warning(
            f"Invalid JWT validation attempt: {str(exc)}",
            extra={"request_id": request_id, "error_code": ErrorCode.INVALID_ACCESS_TOKEN.value},
        )
        raise AuthenticationError(
            message="Invalid access token provided.",
            code=ErrorCode.INVALID_ACCESS_TOKEN,
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError(
            message="Token payload is missing required subject claim.",
            code=ErrorCode.INVALID_ACCESS_TOKEN,
        )

    return AuthenticatedUser(
        id=str(user_id),
        email=str(payload.get("email", "unknown@founder.local")),
        role=str(payload.get("role", "authenticated")),
        app_metadata=payload.get("app_metadata", {}),
        user_metadata=payload.get("user_metadata", {}),
    )


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[AuthenticatedUser]:
    if not credentials:
        return None
    try:
        return await get_current_user(request, credentials)
    except AuthenticationError:
        return None
