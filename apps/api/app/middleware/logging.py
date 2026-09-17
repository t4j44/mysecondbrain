import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "N/A")

        path = request.url.path
        if '/public/portfolio/' in path:
            path = '/api/v1/public/portfolio/[redacted]'
        # We do not log full request body or authorization headers to protect user privacy and secrets
        logger.info(
            f"Incoming request: {request.method} {path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled server failure during {request.method} {path}: {type(exc).__name__}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "status_code": 500,
                },
            )
            raise exc

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            f"Completed {request.method} {path} with status {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "duration_ms": duration_ms,
                "status_code": response.status_code,
            },
        )
        return response
