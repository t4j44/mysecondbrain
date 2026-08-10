import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import PDFAnalysisError

logger = logging.getLogger("api.errors")


def build_error_response(
    code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    req_id = request_id or f"req_{uuid.uuid4().hex[:10]}"
    headers = {}
    if status_code == 429:
        headers["Retry-After"] = "60"

    payload = {
        "error": {"code": code, "message": message, "details": details or {}, "request_id": req_id}
    }
    return JSONResponse(status_code=status_code, content=payload, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PDFAnalysisError)
    async def pdf_analysis_exception_handler(request: Request, exc: PDFAnalysisError):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:10]}")
        return build_error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            request_id=req_id,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:10]}")
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "RESOURCE_NOT_FOUND",
            413: "FILE_TOO_LARGE",
            415: "UNSUPPORTED_MEDIA_TYPE",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        message = str(exc.detail) if exc.detail else "An HTTP error occurred."
        return build_error_response(
            code=code, message=message, status_code=exc.status_code, request_id=req_id
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:10]}")
        errors_summary = []
        for err in exc.errors():
            loc = " -> ".join([str(x) for x in err.get("loc", [])])
            errors_summary.append({"field": loc, "issue": err.get("msg")})
        return build_error_response(
            code="VALIDATION_ERROR",
            message="Request body payload validation failed.",
            status_code=422,
            details={"errors": errors_summary},
            request_id=req_id,
        )

    # Catch GoogleGenAI API Errors dynamically if imported
    try:
        from google.genai.errors import APIError as GenAIAPIError

        @app.exception_handler(GenAIAPIError)
        async def genai_api_exception_handler(request: Request, exc: GenAIAPIError):
            req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:10]}")
            status_code = getattr(exc, "code", 500)
            if status_code == 429:
                return build_error_response(
                    code="RATE_LIMIT_EXCEEDED",
                    message="GoogleGenAI API rate limit exceeded. Please try again shortly.",
                    status_code=429,
                    details={"provider": "GoogleGenAI", "raw_message": str(exc)},
                    request_id=req_id,
                )
            return build_error_response(
                code="AI_SERVICE_UNAVAILABLE",
                message=f"GoogleGenAI provider error: {exc}",
                status_code=503,
                details={"provider": "GoogleGenAI", "raw_message": str(exc)},
                request_id=req_id,
            )
    except ImportError:
        pass

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:10]}")
        logger.error(f"Unhandled exception [req_id={req_id}]: {exc}", exc_info=True)
        return build_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred during document processing.",
            status_code=500,
            details={"type": exc.__class__.__name__},
            request_id=req_id,
        )
