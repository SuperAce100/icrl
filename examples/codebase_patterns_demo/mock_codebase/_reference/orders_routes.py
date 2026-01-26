"""REFERENCE: Expected order routes after ICRL completes the task.

This file shows what ICRL should generate when asked to:
"Add a GET /orders endpoint that returns a list of orders"

Key patterns to observe:
1. All endpoints return APIResponse[T]
2. Business logic delegated to OrderService
3. Custom exceptions (not HTTPException)
4. Structured logging for observability
5. Proper response_model declarations
"""

from fastapi import APIRouter, Query

from app.core.response import APIResponse, PaginatedData
from app.core.logging import get_logger
# from app.models.order import OrderCreate, OrderUpdate, OrderOut, OrderStatus
# from app.services import order_service

logger = get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


# @router.get("", response_model=APIResponse[PaginatedData[OrderOut]])
async def list_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    status: str | None = Query(None, description="Filter by status"),
):  # -> APIResponse[PaginatedData[OrderOut]]
    """List all orders with pagination and filtering.
    
    Returns a paginated list of orders. Optionally filter by user or status.
    """
    logger.info(
        "list_orders_request",
        skip=skip,
        limit=limit,
        user_id=user_id,
        status=status,
    )
    
    # orders, total = await order_service.list(
    #     skip=skip,
    #     limit=limit,
    #     user_id=user_id,
    #     status=status,
    # )
    
    # Convert internal models to output models
    # order_outs = [OrderOut.model_validate(o) for o in orders]
    
    # return APIResponse.success(
    #     data=PaginatedData(items=order_outs, total=total, skip=skip, limit=limit),
    #     message=f"Retrieved {len(order_outs)} orders",
    # )
    pass


# @router.get("/{order_id}", response_model=APIResponse[OrderOut])
async def get_order(order_id: int):  # -> APIResponse[OrderOut]
    """Get an order by ID.
    
    Raises NotFoundError if order doesn't exist.
    """
    logger.info("get_order_request", order_id=order_id)
    
    # Service raises NotFoundError if not found - exception handler converts to 404
    # order = await order_service.get_by_id(order_id)
    
    # return APIResponse.success(
    #     data=OrderOut.model_validate(order),
    #     message="Order retrieved successfully",
    # )
    pass


# @router.post("", response_model=APIResponse[OrderOut], status_code=201)
async def create_order(order_data):  # order_data: OrderCreate -> APIResponse[OrderOut]
    """Create a new order.
    
    Validates that all products exist and have sufficient stock.
    """
    logger.info("create_order_request", user_id=order_data.user_id)
    
    # order = await order_service.create(order_data)
    
    # return APIResponse.success(
    #     data=OrderOut.model_validate(order),
    #     message="Order created successfully",
    # )
    pass


# @router.patch("/{order_id}/status", response_model=APIResponse[OrderOut])
async def update_order_status(
    order_id: int,
    status: str,  # Would be OrderStatus enum
):  # -> APIResponse[OrderOut]
    """Update order status.
    
    Validates that the status transition is allowed.
    """
    logger.info("update_order_status_request", order_id=order_id, new_status=status)
    
    # order = await order_service.update_status(order_id, status)
    
    # return APIResponse.success(
    #     data=OrderOut.model_validate(order),
    #     message=f"Order status updated to {status}",
    # )
    pass


# @router.post("/{order_id}/cancel", response_model=APIResponse[OrderOut])
async def cancel_order(order_id: int):  # -> APIResponse[OrderOut]
    """Cancel an order.
    
    Only pending and confirmed orders can be cancelled.
    Raises ForbiddenError if order cannot be cancelled.
    """
    logger.info("cancel_order_request", order_id=order_id)
    
    # order = await order_service.cancel(order_id)
    
    # return APIResponse.success(
    #     data=OrderOut.model_validate(order),
    #     message="Order cancelled successfully",
    # )
    pass
