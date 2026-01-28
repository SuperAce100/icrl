"""Standard API response wrapper for ACME API.

ALL endpoints must return APIResponse[T] for consistency.
This ensures:
- Consistent response structure across all endpoints
- Proper typing for OpenAPI schema generation
- Standard error format

Usage:
    @router.get("/items/{id}", response_model=APIResponse[ItemOut])
    async def get_item(id: int) -> APIResponse[ItemOut]:
        item = await item_service.get_by_id(id)
        return APIResponse.success(data=item, message="Item retrieved")

NEVER return raw dicts or Pydantic models directly!
"""

from datetime import datetime, timezone
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard response wrapper for all ACME API endpoints.
    
    Attributes:
        success: Whether the operation succeeded
        message: Human-readable message about the operation
        data: The actual response payload (generic type)
        timestamp: When the response was generated (UTC)
        request_id: Unique identifier for request tracing (set by middleware)
    """
    
    success: bool = True
    message: str = ""
    data: T | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str | None = None  # Set by RequestIDMiddleware
    
    @classmethod
    def success(
        cls,
        data: T,
        message: str = "Operation successful",
    ) -> "APIResponse[T]":
        """Create a successful response.
        
        Args:
            data: The response payload
            message: Human-readable success message
            
        Returns:
            APIResponse with success=True
        """
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error(
        cls,
        message: str,
        data: T | None = None,
    ) -> "APIResponse[T]":
        """Create an error response.
        
        Note: Prefer raising custom exceptions (NotFoundError, etc.)
        which are automatically converted to proper HTTP responses.
        
        Args:
            message: Human-readable error message
            data: Optional error details
            
        Returns:
            APIResponse with success=False
        """
        return cls(success=False, message=message, data=data)


class PaginatedData(BaseModel, Generic[T]):
    """Wrapper for paginated list responses.
    
    Usage:
        @router.get("/items", response_model=APIResponse[PaginatedData[ItemOut]])
        async def list_items(skip: int = 0, limit: int = 20):
            items, total = await item_service.list(skip=skip, limit=limit)
            return APIResponse.success(
                data=PaginatedData(items=items, total=total, skip=skip, limit=limit),
                message=f"Retrieved {len(items)} items"
            )
    """
    
    items: list[T]
    total: int
    skip: int = 0
    limit: int = 20
    
    @property
    def has_more(self) -> bool:
        """Check if there are more items beyond this page."""
        return self.skip + len(self.items) < self.total
