import time
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.constants import ErrorCode

# In-memory sliding window rate limiter per user/ip
# Routes with strict throttling requirements
STRICT_RATE_PATHS = {
    "/api/v1/documents",
    "/api/v1/ai/",
    "/api/v1/exports",
    "/api/v1/integrations",
}

# Max requests per window (60 seconds)
DEFAULT_RATE_LIMIT = 300
STRICT_RATE_LIMIT = 30


class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Map key -> (count, window_start_time)
        self.tracker: Dict[str, Tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next):
        # Health check endpoints bypass rate limits
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Determine client identifier (IP or Authorization header hash if available)
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        is_strict = any(path.startswith(prefix) for prefix in STRICT_RATE_PATHS)
        limit = STRICT_RATE_LIMIT if is_strict else DEFAULT_RATE_LIMIT
        window_seconds = 60.0

        bucket_key = f"{client_ip}:{'strict' if is_strict else 'normal'}"
        now = time.time()

        count, window_start = self.tracker.get(bucket_key, (0, now))
        if now - window_start > window_seconds:
            # Reset window
            count = 1
            window_start = now
        else:
            count += 1

        self.tracker[bucket_key] = (count, window_start)

        if count > limit:
            request_id = getattr(request.state, "request_id", "N/A")
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": ErrorCode.RATE_LIMITED.value,
                        "message": f"Rate limit exceeded. Maximum {limit} requests per minute allowed for this operation.",
                        "details": {"limit": limit, "window_seconds": 60},
                        "request_id": request_id,
                    }
                },
                headers={
                    "X-Request-ID": request_id,
                    "Retry-After": str(int(window_seconds - (now - window_start))),
                },
            )

        return await call_next(request)
