"""Custom exception hierarchy for ACME API.

ALL error conditions should use these exceptions, NOT HTTPException directly.
The exception handlers in main.py convert these to proper HTTP responses.

Benefits:
- Consistent error response format
- Automatic logging of errors
- Type-safe error handling
- Easy to test

Usage:
    from app.core.exceptions import NotFoundError, ValidationError
    
    # Instead of: raise HTTPException(status_code=404, detail="User not found")
    # Do this:    raise NotFoundError("User", user_id)
    
    # Instead of: raise HTTPException(status_code=400, detail="Invalid email")
    # Do this:    raise ValidationError("email", "Invalid email format")
"""

from typing import Any


class ACMEBaseError(Exception):
    """Base exception for all ACME API errors.
    
    All custom exceptions inherit from this, allowing:
    - Catch-all handling: except ACMEBaseError
    - Consistent structure across error types
    """
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class NotFoundError(ACMEBaseError):
    """Resource not found (404).
    
    Usage:
        raise NotFoundError("User", user_id)
        raise NotFoundError("Order", order_id, details={"searched_in": "active_orders"})
    """
    
    status_code = 404
    error_code = "NOT_FOUND"
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        details: dict[str, Any] | None = None,
    ) -> None:
        message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(ACMEBaseError):
    """Validation error (400).
    
    Usage:
        raise ValidationError("email", "Invalid email format")
        raise ValidationError("age", "Must be at least 18", details={"provided": 16})
    """
    
    status_code = 400
    error_code = "VALIDATION_ERROR"
    
    def __init__(
        self,
        field: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        message = f"Validation failed for '{field}': {reason}"
        super().__init__(message, details)
        self.field = field
        self.reason = reason


class ConflictError(ACMEBaseError):
    """Resource conflict (409).
    
    Usage:
        raise ConflictError("User with email 'x@y.com' already exists")
        raise ConflictError("Order already processed", details={"order_id": 123})
    """
    
    status_code = 409
    error_code = "CONFLICT"


class ForbiddenError(ACMEBaseError):
    """Access forbidden (403).
    
    Usage:
        raise ForbiddenError("Cannot modify archived orders")
        raise ForbiddenError("Insufficient permissions", details={"required": "admin"})
    """
    
    status_code = 403
    error_code = "FORBIDDEN"


class RateLimitError(ACMEBaseError):
    """Rate limit exceeded (429).
    
    Usage:
        raise RateLimitError("Too many requests", details={"retry_after": 60})
    """
    
    status_code = 429
    error_code = "RATE_LIMITED"
