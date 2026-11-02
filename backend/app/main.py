"""FastAPI application entry point.
Exposes OpenAPI specifications, registers domain routers, and sets up middleware.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.core.errors import SanadException, sanad_exception_handler
from backend.app.modules.auth.router import router as auth_router
from backend.app.modules.institutions.router import router as institutions_router
from backend.app.modules.admin.router import router as admin_router

# Setup structured logging
setup_logging(is_dev=(settings.ENV.value == "development"))

app = FastAPI(
    title="Sanad - Authenticity Validator for Academia",
    description="Dual-path academic credential verification platform (SIH25029).",
    version="0.1.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Register RFC 9457 exception handler
app.add_exception_handler(SanadException, sanad_exception_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_and_timing(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.perf_counter()

    response: Response = await call_next(request)

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

    logger.info(
        "http_request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
        request_id=request_id,
    )
    return response


# Register Phase 1 Domain Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(institutions_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)


@app.get("/healthz", tags=["Operations"])
async def healthz():
    """Liveness probe."""
    return {"status": "ok", "timestamp": time.time()}


@app.get("/readyz", tags=["Operations"])
async def readyz():
    """Readiness probe checking environment and operational readiness."""
    return {"status": "ready", "env": settings.ENV.value}


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Sanad Authenticity Validator",
        "version": "0.1.0",
        "api_v1": settings.API_V1_PREFIX,
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }
