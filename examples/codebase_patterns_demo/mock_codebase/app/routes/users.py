"""User routes - CRUD operations for users.

This module demonstrates the ACME API patterns:
1. All endpoints return APIResponse[T]
2. Business logic is in UserService, not here
3. Custom exceptions are raised, not HTTPException
4. Structured logging for observability

Copy this pattern when creating new route modules!
"""

from fastapi import APIRouter, Query

from app.core.response import APIResponse, PaginatedData
from app.core.logging import get_logger
from app.models.user import UserCreate, UserUpdate, UserOut
from app.services import user_service

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=APIResponse[PaginatedData[UserOut]])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    active_only: bool = Query(True, description="Only return active users"),
) -> APIResponse[PaginatedData[UserOut]]:
    """List all users with pagination.
    
    Returns a paginated list of users. By default, only active users are returned.
    """
    logger.info("list_users_request", skip=skip, limit=limit, active_only=active_only)
    
    users, total = await user_service.list(skip=skip, limit=limit, active_only=active_only)
    
    # Convert internal models to output models
    user_outs = [UserOut.model_validate(u) for u in users]
    
    return APIResponse.success(
        data=PaginatedData(items=user_outs, total=total, skip=skip, limit=limit),
        message=f"Retrieved {len(user_outs)} users",
    )


@router.get("/{user_id}", response_model=APIResponse[UserOut])
async def get_user(user_id: int) -> APIResponse[UserOut]:
    """Get a user by ID.
    
    Raises NotFoundError if user doesn't exist.
    """
    logger.info("get_user_request", user_id=user_id)
    
    # Service raises NotFoundError if not found - exception handler converts to 404
    user = await user_service.get_by_id(user_id)
    
    return APIResponse.success(
        data=UserOut.model_validate(user),
        message="User retrieved successfully",
    )


@router.post("", response_model=APIResponse[UserOut], status_code=201)
async def create_user(user_data: UserCreate) -> APIResponse[UserOut]:
    """Create a new user.
    
    Raises ConflictError if email already exists.
    """
    logger.info("create_user_request", email=user_data.email)
    
    # Service handles validation and raises ConflictError if email exists
    user = await user_service.create(user_data)
    
    return APIResponse.success(
        data=UserOut.model_validate(user),
        message="User created successfully",
    )


@router.patch("/{user_id}", response_model=APIResponse[UserOut])
async def update_user(user_id: int, user_data: UserUpdate) -> APIResponse[UserOut]:
    """Update an existing user.
    
    Only provided fields are updated. Raises NotFoundError if user doesn't exist.
    """
    logger.info("update_user_request", user_id=user_id)
    
    user = await user_service.update(user_id, user_data)
    
    return APIResponse.success(
        data=UserOut.model_validate(user),
        message="User updated successfully",
    )


@router.delete("/{user_id}", response_model=APIResponse[None])
async def delete_user(user_id: int) -> APIResponse[None]:
    """Delete a user (soft delete).
    
    Sets the user's is_active flag to False. Raises NotFoundError if user doesn't exist.
    """
    logger.info("delete_user_request", user_id=user_id)
    
    await user_service.delete(user_id)
    
    return APIResponse.success(
        data=None,
        message="User deleted successfully",
    )
