import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Valid regex for safe incoming request IDs
REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9\-_]{4,64}$")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        header_id = request.headers.get("X-Request-ID")
        if header_id and REQUEST_ID_REGEX.match(header_id):
            request_id = header_id
        else:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
