"""ACME API - Main FastAPI application.

This is the entry point for the ACME API. It configures:
- Exception handlers for custom exceptions
- Middleware for request context
- Route registration
- Logging setup

Run with: uvicorn app.main:app --reload
"""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ACMEBaseError
from app.core.logging import configure_logging, bind_request_context, get_logger
from app.core.response import APIResponse
from app.routes import users_router, products_router, orders_router, categories_router, inventory_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    configure_logging(json_format=False)  # Pretty logs for dev
    logger.info("application_started", version="1.0.0")
    
    yield
    
    # Shutdown
    logger.info("application_stopped")


app = FastAPI(
    title="ACME API",
    description="Internal API for ACME Corp services",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------
# These convert our custom exceptions to proper HTTP responses with consistent format

@app.exception_handler(ACMEBaseError)
async def acme_exception_handler(request: Request, exc: ACMEBaseError) -> JSONResponse:
    """Handle all ACME custom exceptions.
    
    Converts exceptions to consistent JSON response format.
    """
    logger.error(
        "request_failed",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
    )
    
    response = APIResponse.error(message=exc.message, data=exc.to_dict())
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
    )


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Add request context for logging and tracing."""
    request_id = str(uuid.uuid4())
    
    # Bind context for structured logging
    bind_request_context(request_id=request_id)
    
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
    )
    
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(users_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health", response_model=APIResponse[dict])
async def health_check() -> APIResponse[dict]:
    """Health check endpoint for load balancers."""
    return APIResponse.success(
        data={"status": "healthy", "version": "1.0.0"},
        message="Service is healthy",
    )
