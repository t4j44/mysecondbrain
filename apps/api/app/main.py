from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.dependencies.database import admin_db_session, verify_database_ready
from app.mcp.router import router as mcp_http_router
from app.mcp.server import mcp_asgi_app, mcp_server
from app.middleware import (
    RateLimitingMiddleware,
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    setup_exception_handlers,
)

# Initialize JSON structured logging with redaction
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Taj's Second Brain FastAPI Backend Architecture...")
    async with mcp_server.session_manager.run():
        await verify_database_ready()
        yield
    logger.info("Shutting down FastAPI Backend Gracefully...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready FastAPI backend and domain service layer for Taj's Second Brain, enforcing strict multi-tenant Row Level Security (RLS) and ownership-first portability.",
    version=settings.APP_VERSION,
    docs_url="/api/docs" if not settings.is_production() else None,
    redoc_url="/api/redoc" if not settings.is_production() else None,
    openapi_url="/api/openapi.json" if not settings.is_production() else None,
    lifespan=lifespan,
)

# Register Custom Exception Handlers
setup_exception_handlers(app)

# Register Custom Middleware Layers (Order of execution: bottom-to-top for inbound requests)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# Configure CORS for Next.js Frontend & MCP integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)

# Register API v1 Domain Module Routers
app.include_router(api_router, prefix="/api/v1")

# Mount MCP Streamable HTTP Application at /mcp (ADR-013)
app.include_router(mcp_http_router, prefix="/mcp")

# --- SYSTEM HEALTH & PROBE ENDPOINTS (Task 1 & Task 9) ---
@app.get("/health", tags=["System Health"], summary="Standard application operational check")
@app.get("/api/v1/health", tags=["System Health"], summary="API v1 standard health check")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/live", tags=["System Health"], summary="Kubernetes liveness probe")
async def liveness_probe():
    return {"status": "alive"}


@app.get(
    "/health/ready",
    tags=["System Health"],
    summary="Readiness probe validating underlying database reachability",
)
async def readiness_probe():
    try:
        async with admin_db_session(reason="readiness_probe") as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
        http_code = status.HTTP_200_OK
    except Exception as exc:
        logger.error(f"Database readiness health check failed: {str(exc)}")
        db_status = "unreachable"
        http_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_code,
        content={
            "status": "ready" if db_status == "connected" else "not_ready",
            "database": db_status,
        },
    )


# Official MCP Streamable HTTP transport. This catch-all mount must remain the
# final route so REST, health, docs, and the compatibility GET manifest win.
app.mount("", mcp_asgi_app)
