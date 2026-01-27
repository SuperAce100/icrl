"""Structured logging for ACME API.

ALL logging should use get_logger() and structured key-value pairs.
Never use print() or logging.info("message with {interpolation}").

Benefits:
- JSON-formatted logs for log aggregation (Datadog, etc.)
- Consistent context across log entries
- Easy to search and filter
- Automatic request context binding

Usage:
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    
    # Good: Structured logging with key-value pairs
    logger.info("user_created", user_id=user.id, email=user.email)
    logger.warning("rate_limit_approaching", user_id=user.id, current=95, limit=100)
    logger.error("payment_failed", order_id=order.id, reason=str(e))
    
    # Bad: String interpolation (don't do this!)
    # logger.info(f"Created user {user.id}")  # NO!
"""

import structlog
from typing import Any


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger for the given module.
    
    Args:
        name: Usually __name__ of the calling module
        
    Returns:
        Configured structlog logger with ACME defaults
        
    Example:
        logger = get_logger(__name__)
        logger.info("operation_completed", duration_ms=150, items_processed=42)
    """
    return structlog.get_logger(name)


def configure_logging(json_format: bool = True, log_level: str = "INFO") -> None:
    """Configure structlog with ACME defaults.
    
    Called once at application startup in main.py.
    
    Args:
        json_format: If True, output JSON logs (production). If False, pretty print (dev).
        log_level: Minimum log level to output.
    """
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def bind_request_context(request_id: str, user_id: int | None = None) -> None:
    """Bind request context to all subsequent log entries.
    
    Called by RequestContextMiddleware for each request.
    
    Args:
        request_id: Unique request identifier
        user_id: Authenticated user ID (if available)
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        user_id=user_id,
    )
