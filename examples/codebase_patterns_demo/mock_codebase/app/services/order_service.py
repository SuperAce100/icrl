"""Order service - business logic for order operations.

This service handles all order-related business logic:
- CRUD operations
- Business rule validation
- Database interactions

Routes should call these methods, not implement logic themselves.
"""

from datetime import datetime, timezone
from decimal import Decimal
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.core.logging import get_logger
from app.models.order import OrderCreate, OrderUpdate, OrderInDB

logger = get_logger(__name__)


# Mock database - in real app, this would be SQLAlchemy/async DB
_mock_orders_db: dict[int, OrderInDB] = {
    1: OrderInDB(
        id=1,
        customer_id=1,
        product_id=101,
        quantity=2,
        unit_price=Decimal("29.99"),
        total_amount=Decimal("59.98"),
        status="confirmed",
        notes="Express shipping requested",
        is_active=True,
        created_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
    ),
    2: OrderInDB(
        id=2,
        customer_id=2,
        product_id=102,
        quantity=1,
        unit_price=Decimal("149.99"),
        total_amount=Decimal("149.99"),
        status="pending",
        notes=None,
        is_active=True,
        created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
    ),
}
_next_id = 3


class OrderService:
    """Service for order operations.
    
    All methods follow these patterns:
    - Raise custom exceptions (NotFoundError, etc.) for error cases
    - Log operations with structured logging
    - Return internal models (OrderInDB) - routes convert to OrderOut
    """
    
    async def get_by_id(self, order_id: int) -> OrderInDB:
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
        active_only: bool = True,
    ) -> tuple[list[OrderInDB], int]:
        """List orders with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            active_only: If True, only return active orders
            
        Returns:
            Tuple of (orders, total_count)
        """
        logger.info("order_list_started", skip=skip, limit=limit, active_only=active_only)
        
        all_orders = list(_mock_orders_db.values())
        if active_only:
            all_orders = [o for o in all_orders if o.is_active]
        
        total = len(all_orders)
        orders = all_orders[skip : skip + limit]
        
        logger.info("order_list_completed", count=len(orders), total=total)
        return orders, total
    
    async def create(self, data: OrderCreate) -> OrderInDB:
        """Create a new order.
        
        Args:
            data: Order creation data
            
        Returns:
            The created order
        """
        global _next_id
        
        logger.info("order_create_started", customer_id=data.customer_id, product_id=data.product_id)
        
        # In real app: fetch product price from product service
        unit_price = Decimal("29.99")  # Mock price
        total_amount = unit_price * data.quantity
        
        # Create order
        now = datetime.now(timezone.utc)
        order = OrderInDB(
            id=_next_id,
            customer_id=data.customer_id,
            product_id=data.product_id,
            quantity=data.quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            status="pending",
            notes=data.notes,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        
        _mock_orders_db[_next_id] = order
        _next_id += 1
        
        logger.info("order_created", order_id=order.id, customer_id=order.customer_id)
        return order
    
    async def update(self, order_id: int, data: OrderUpdate) -> OrderInDB:
        """Update an existing order.
        
        Args:
            order_id: The order's ID
            data: Fields to update (only non-None fields are applied)
            
        Returns:
            The updated order
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        logger.info("order_update_started", order_id=order_id)
        
        order = await self.get_by_id(order_id)
        
        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        
        # Recalculate total if quantity changed
        if "quantity" in update_data:
            update_data["total_amount"] = order.unit_price * update_data["quantity"]
        
        updated_order = order.model_copy(update=update_data)
        updated_order = updated_order.model_copy(
            update={"updated_at": datetime.now(timezone.utc)}
        )
        
        _mock_orders_db[order_id] = updated_order
        
        logger.info("order_updated", order_id=order_id, fields=list(update_data.keys()))
        return updated_order
    
    async def delete(self, order_id: int) -> None:
        """Delete an order (soft delete - sets is_active=False).
        
        Args:
            order_id: The order's ID
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        logger.info("order_delete_started", order_id=order_id)
        
        order = await self.get_by_id(order_id)
        
        # Soft delete
        updated_order = order.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        _mock_orders_db[order_id] = updated_order
        
        logger.info("order_deleted", order_id=order_id)
