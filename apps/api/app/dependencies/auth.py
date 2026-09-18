from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWKClientError
from jwt.jwks_client import PyJWKClient
from pydantic import BaseModel

from app.core.config import settings
from app.core.constants import ErrorCode
from app.core.errors import AuthenticationError
from app.core.logging import logger

security_bearer = HTTPBearer(auto_error=False)

_jwks_clients: Dict[str, PyJWKClient] = {}


def get_jwks_client(jwks_url: str) -> PyJWKClient:
    """Returns a cached PyJWKClient instance for the JWKS endpoint."""
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(
            jwks_url,
            cache_jwk_set=True,
            lifespan=3600,
            cache_keys=True,
            max_cached_keys=16,
            timeout=10.0,
        )
    return _jwks_clients[jwks_url]


class AuthenticatedUser(BaseModel):
    id: str  # User UUID derived strictly from token sub claim
    email: str
    role: str = "authenticated"
    app_metadata: Dict[str, Any] = {}
    user_metadata: Dict[str, Any] = {}

    def is_founder(self) -> bool:
        """Verify if user possesses primary founder administrative role or ownership."""
        return self.role in {"authenticated", "founder", "admin"}


def decode_and_verify_token(token: str) -> Dict[str, Any]:
    """
    Decodes and verifies a Supabase user access token.

    1. Rejects opaque tokens / server secrets (sb_secret_...) as user JWTs.
    2. Enforces cryptographic signature verification using Supabase JWKS (asymmetric ES256/RS256).
    3. Allows temporary HS256 migration fallback when SUPABASE_JWT_SECRET or JWT_SECRET is present.
    4. In production, fails closed if verification against JWKS (or explicit migration secret) fails.
    """
    # 1. Inspect unverified token header
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise AuthenticationError(
            message="Invalid access token provided.",
            code=ErrorCode.INVALID_ACCESS_TOKEN,
        ) from exc

    alg = header.get("alg", "")
    if not alg or alg.lower() == "none":
        raise AuthenticationError(
            message="Invalid access token provided.",
            code=ErrorCode.INVALID_ACCESS_TOKEN,
        )

    jwks_url = settings.supabase_jwks_url

    # 2. Primary: Verify via Supabase JWKS (asymmetric keys or kid-bearing tokens)
    if jwks_url and (alg.startswith(("RS", "ES", "Ed")) or "kid" in header):
        try:
            jwks_client = get_jwks_client(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256", "RS384", "RS512", "ES384", "ES512", "EdDSA"],
                audience="authenticated",
                issuer=settings.SUPABASE_URL.rstrip("/") + "/auth/v1" if settings.SUPABASE_URL else None,
                options={"verify_exp": True, "verify_sub": True, "require": ["sub", "exp", "aud"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError(
                message="Access token has expired. Please refresh your credentials.",
                code=ErrorCode.ACCESS_TOKEN_EXPIRED,
            ) from exc
        except (jwt.InvalidTokenError, PyJWKClientError) as exc:
            if settings.is_production() or not alg.startswith("HS"):
                raise AuthenticationError(
                    message="Invalid access token provided.",
                    code=ErrorCode.INVALID_ACCESS_TOKEN,
                ) from exc

    # 3. Temporary migration / test fallback for symmetric HS256 tokens
    symmetric_secret = settings.SUPABASE_JWT_SECRET or (
        settings.JWT_SECRET if not settings.is_production() else ""
    )
    if alg.startswith("HS") and symmetric_secret:
        try:
            return jwt.decode(
                token,
                symmetric_secret,
                algorithms=["HS256", "HS384", "HS512"],
                audience="authenticated",
                issuer=settings.SUPABASE_URL.rstrip("/") + "/auth/v1" if settings.SUPABASE_URL else None,
                options={"verify_exp": True, "verify_sub": True, "require": ["sub", "exp", "aud"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError(
                message="Access token has expired. Please refresh your credentials.",
                code=ErrorCode.ACCESS_TOKEN_EXPIRED,
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError(
                message="Invalid access token provided.",
                code=ErrorCode.INVALID_ACCESS_TOKEN,
            ) from exc

    # 4. Fail closed if no validation path succeeded
    raise AuthenticationError(
        message="Invalid access token provided.",
        code=ErrorCode.INVALID_ACCESS_TOKEN,
    )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> AuthenticatedUser:
    """
    Verify Supabase JWT locally without network latency (ADR-003) or via cached JWKS.
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
        payload = decode_and_verify_token(token)
    except AuthenticationError as auth_err:
        if auth_err.code == ErrorCode.ACCESS_TOKEN_EXPIRED:
            logger.warning(
                "Expired authentication token provided in request.",
                extra={"request_id": request_id, "error_code": ErrorCode.ACCESS_TOKEN_EXPIRED.value},
            )
        else:
            logger.warning(
                f"Invalid JWT validation attempt: {auth_err.message}",
                extra={"request_id": request_id, "error_code": ErrorCode.INVALID_ACCESS_TOKEN.value},
            )
        raise

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError(
            message="Token payload is missing required subject claim.",
            code=ErrorCode.INVALID_ACCESS_TOKEN,
        )

    if request.url.path not in {"/api/v1/account/deletion-status", "/api/v1/account/delete"}:
        from app.dependencies.database import admin_db_session
        from app.models.entities import AccountClosure
        async with admin_db_session(reason="account_active_check") as db:
            if await db.get(AccountClosure, str(user_id)):
                raise AuthenticationError("Account deletion is in progress.")

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
