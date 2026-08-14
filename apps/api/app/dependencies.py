from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import AuthenticationError
from app.dependencies.auth import decode_and_verify_token

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    """
    Decodes and verifies the Bearer JWT token from Supabase Auth via JWKS with symmetric migration fallback.
    Returns the authenticated user's UUID.
    """
    token = credentials.credentials
    payload = decode_and_verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token subject claim ('sub') is missing.")

    return UUID(user_id)
