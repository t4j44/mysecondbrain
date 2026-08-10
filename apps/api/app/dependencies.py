from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.errors import AuthenticationError

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    """
    Decodes the Bearer JWT token from Supabase Auth.
    Locally verifies signature against settings.SUPABASE_JWT_SECRET.
    Returns the authenticated user's UUID.
    """
    token = credentials.credentials
    try:
        # Supabase default alg is HS256, audience is "authenticated"
        payload = jwt.decode(
            token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Token subject claim ('sub') is missing.")

        return UUID(user_id)
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired. Re-authentication required.") from exc
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid authentication token: {str(e)}") from e
