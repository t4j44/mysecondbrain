from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ErrorCode
from app.core.logging import logger


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "N/A")
        logger.warning(
            f"AppError generated: [{exc.code}] {exc.message}",
            extra={"request_id": request_id, "error_code": exc.code},
        )
        resp_headers = {"X-Request-ID": request_id}
        exc_headers = getattr(exc, "headers", None)
        if exc_headers and isinstance(exc_headers, dict):
            resp_headers.update(exc_headers)
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(request_id=request_id),
            headers=resp_headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "N/A")
        # Extract safe field-level details without leaking sensitive values
        details = []
        for error in exc.errors():
            loc = " -> ".join([str(loc_part) for loc_part in error.get("loc", [])])
            details.append({"field": loc, "error": error.get("msg", "Invalid value")})

        logger.warning(
            f"Input schema validation failed on {request.method} {request.url.path}",
            extra={"request_id": request_id, "error_code": ErrorCode.VALIDATION_FAILED.value},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": ErrorCode.VALIDATION_FAILED.value,
                    "message": "Input schema validation failed.",
                    "details": details,
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "N/A")
        logger.error(
            f"Database integrity constraint violated during request: {type(exc.orig).__name__}",
            extra={"request_id": request_id, "error_code": ErrorCode.CONFLICT.value},
        )
        # Never leak raw SQL or database internal identifiers
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": ErrorCode.CONFLICT.value,
                    "message": "Resource state conflict or duplicate detected in database.",
                    "details": None,
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "N/A")
        logger.error(
            f"Unhandled system failure: {type(exc).__name__}",
            extra={"request_id": request_id, "error_code": ErrorCode.INTERNAL_ERROR.value},
        )
        # Prevent stack trace exposure in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "An internal server error occurred.",
                    "details": None,
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id},
        )
