from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Attach strict security posture headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Private CRM, memory, meeting, OAuth and MCP responses must never be
        # shared across users by a browser/CDN/proxy cache.
        path = request.url.path
        if path.startswith(("/api/v1/", "/oauth/", "/mcp/")) or path == "/mcp":
            response.headers.setdefault("Cache-Control", "private, no-store")

        # Preserve the streaming contract, even for authenticated MCP/SSE.
        if response.headers.get("content-type", "").startswith("text/event-stream"):
            response.headers["Cache-Control"] = "no-cache, no-transform"
            response.headers["Connection"] = "keep-alive"
            response.headers["X-Accel-Buffering"] = "no"

        return response
