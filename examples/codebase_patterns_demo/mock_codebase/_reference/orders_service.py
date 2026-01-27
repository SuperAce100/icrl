"""REFERENCE: Expected order service after ICRL completes the task.

This file shows what ICRL should generate when asked to:
"Add a GET /orders endpoint that returns a list of orders"

Key patterns to observe:
1. Structured logging with get_logger(__name__)
2. Custom exceptions (NotFoundError, ValidationError)
3. Async methods returning internal models
4. Business logic contained in service, not routes
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from app.core.logging import get_logger
# from app.models.order import OrderCreate, OrderUpdate, OrderInDB, OrderStatus, OrderItemOut

logger = get_logger(__name__)


# Mock database
_mock_orders_db: dict = {}  # Would be dict[int, OrderInDB]
_next_id = 1


class OrderService:
    """Service for order operations.
    
    All methods follow these patterns:
    - Raise custom exceptions (NotFoundError, etc.) for error cases
    - Log operations with structured logging
    - Return internal models (OrderInDB) - routes convert to OrderOut
    """
    
    async def get_by_id(self, order_id: int):  # -> OrderInDB
        """Get an order by ID.
        
        Args:
            order_id: The order's ID
            
        Returns:
            The order if found
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        logger.info("order_fetch_started", order_id=order_id)
        
        order = _mock_orders_db.get(order_id)
        if not order:
            logger.warning("order_not_found", order_id=order_id)
            raise NotFoundError("Order", order_id)
        
        logger.info("order_fetch_completed", order_id=order_id)
        return order
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: int | None = None,
        status: str | None = None,
    ):  # -> tuple[list[OrderInDB], int]
        """List orders with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            user_id: Filter by user (optional)
            status: Filter by status (optional)
            
        Returns:
            Tuple of (orders, total_count)
        """
        logger.info(
            "order_list_started",
            skip=skip,
            limit=limit,
            user_id=user_id,
            status=status,
        )
        
        all_orders = list(_mock_orders_db.values())
        
        if user_id is not None:
            all_orders = [o for o in all_orders if o.user_id == user_id]
        
        if status is not None:
            all_orders = [o for o in all_orders if o.status == status]
        
        total = len(all_orders)
        orders = all_orders[skip : skip + limit]
        
        logger.info("order_list_completed", count=len(orders), total=total)
        return orders, total
    
    async def create(self, data):  # data: OrderCreate -> OrderInDB
        """Create a new order.
        
        Args:
            data: Order creation data
            
        Returns:
            The created order
            
        Raises:
            ValidationError: If order data is invalid
        """
        global _next_id
        
        logger.info("order_create_started", user_id=data.user_id, item_count=len(data.items))
        
        # Calculate total
        total = sum(
            item.quantity * item.unit_price
            for item in data.items
        )
        
        # Create order items
        items = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.quantity * item.unit_price,
            }
            for item in data.items
        ]
        
        now = datetime.now(timezone.utc)
        order = {
            "id": _next_id,
            "user_id": data.user_id,
            "items": items,
            "status": "pending",
            "total": total,
            "shipping_address": data.shipping_address,
            "notes": data.notes,
            "created_at": now,
            "updated_at": now,
        }
        
        _mock_orders_db[_next_id] = order
        _next_id += 1
        
        logger.info("order_created", order_id=order["id"], total=str(total))
        return order
    
    async def update_status(self, order_id: int, new_status: str):  # -> OrderInDB
        """Update order status.
        
        Args:
            order_id: The order's ID
            new_status: The new status
            
        Returns:
            The updated order
            
        Raises:
            NotFoundError: If order doesn't exist
            ForbiddenError: If status transition is not allowed
        """
        logger.info("order_status_update_started", order_id=order_id, new_status=new_status)
        
        order = await self.get_by_id(order_id)
        old_status = order["status"]
        
        # Validate status transition
        if old_status == "cancelled":
            raise ForbiddenError("Cannot update status of cancelled order")
        
        if old_status == "delivered" and new_status != "delivered":
            raise ForbiddenError("Cannot change status of delivered order")
        
        order["status"] = new_status
        order["updated_at"] = datetime.now(timezone.utc)
        
        logger.info(
            "order_status_updated",
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
        )
        return order
    
    async def cancel(self, order_id: int):  # -> OrderInDB
        """Cancel an order.
        
        Args:
            order_id: The order's ID
            
        Returns:
            The cancelled order
            
        Raises:
            NotFoundError: If order doesn't exist
            ForbiddenError: If order cannot be cancelled
        """
        logger.info("order_cancel_started", order_id=order_id)
        
        order = await self.get_by_id(order_id)
        
        if order["status"] in ("shipped", "delivered"):
            raise ForbiddenError(
                f"Cannot cancel order in '{order['status']}' status",
                details={"current_status": order["status"]},
            )
        
        order["status"] = "cancelled"
        order["updated_at"] = datetime.now(timezone.utc)
        
        logger.info("order_cancelled", order_id=order_id)
        return order
