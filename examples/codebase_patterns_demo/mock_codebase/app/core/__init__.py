"""Core utilities and patterns for ACME API.

This module contains the foundational patterns that ALL endpoints must follow:
- APIResponse: Standard response wrapper
- Custom exceptions: NotFoundError, ValidationError, etc.
- Structured logging: get_logger with context binding

IMPORTANT: All new endpoints MUST use these patterns for consistency.
"""

from app.core.exceptions import (
    ACMEBaseError,
    NotFoundError,
    ValidationError,
    ConflictError,
    ForbiddenError,
    RateLimitError,
)
from app.core.response import APIResponse, PaginatedData
from app.core.logging import get_logger, configure_logging, bind_request_context

__all__ = [
    # Response utilities
    "APIResponse",
    "PaginatedData",
    # Exceptions
    "ACMEBaseError",
    "NotFoundError", 
    "ValidationError",
    "ConflictError",
    "ForbiddenError",
    "RateLimitError",
    # Logging
    "get_logger",
    "configure_logging",
    "bind_request_context",
]
