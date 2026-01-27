"""Inventory service - business logic for inventory operations.

This service handles all inventory-related business logic:
- Listing inventory items
- Updating stock levels
- Low stock detection

Routes should call these methods, not implement logic themselves.
"""

from datetime import datetime, timezone

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.inventory import InventoryUpdate, InventoryInDB
from app.services.product_service import ProductService

logger = get_logger(__name__)


class InventoryService:
    """Service for inventory operations.
    
    All methods follow these patterns:
    - Raise custom exceptions (NotFoundError, etc.) for error cases
    - Log operations with structured logging
    - Return internal models (InventoryInDB) - routes convert to InventoryOut
    """
    
    def __init__(self) -> None:
        self._product_service = ProductService()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        low_stock_only: bool = False,
    ) -> tuple[list[InventoryInDB], int]:
        """List inventory items with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            low_stock_only: If True, only return items with low stock
            
        Returns:
            Tuple of (inventory_items, total_count)
        """
        logger.info(
            "inventory_list_started",
            skip=skip,
            limit=limit,
            low_stock_only=low_stock_only,
        )
        
        # Get all active products
        products, _ = await self._product_service.list(
            skip=0,
            limit=1000,  # Get all for filtering
            active_only=True,
        )
        
        # Convert to inventory items
        inventory_items = [
            InventoryInDB(
                product_id=p.id,
                product_name=p.name,
                sku=p.sku,
                stock_quantity=p.stock_quantity,
                low_stock_threshold=10,
                last_updated=p.updated_at,
            )
            for p in products
        ]
        
        # Filter low stock if requested
        if low_stock_only:
            inventory_items = [item for item in inventory_items if item.is_low_stock]
        
        total = len(inventory_items)
        paginated_items = inventory_items[skip : skip + limit]
        
        logger.info("inventory_list_completed", count=len(paginated_items), total=total)
        return paginated_items, total
    
    async def get_by_product_id(self, product_id: int) -> InventoryInDB:
        """Get inventory for a specific product.
        
        Args:
            product_id: The product's ID
            
        Returns:
            The inventory item if found
            
        Raises:
            NotFoundError: If product doesn't exist
        """
        logger.info("inventory_fetch_started", product_id=product_id)
        
        product = await self._product_service.get_by_id(product_id)
        
        inventory_item = InventoryInDB(
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            stock_quantity=product.stock_quantity,
            low_stock_threshold=10,
            last_updated=product.updated_at,
        )
        
        logger.info("inventory_fetch_completed", product_id=product_id)
        return inventory_item
    
    async def update_stock(
        self,
        product_id: int,
        data: InventoryUpdate,
    ) -> InventoryInDB:
        """Update stock level for a product.
        
        Args:
            product_id: The product's ID
            data: Stock update data (either quantity_change or quantity_absolute)
            
        Returns:
            The updated inventory item
            
        Raises:
            NotFoundError: If product doesn't exist
            ValidationError: If no update method specified or resulting stock would be negative
        """
        logger.info(
            "inventory_update_started",
            product_id=product_id,
            quantity_change=data.quantity_change,
            quantity_absolute=data.quantity_absolute,
            reason=data.reason,
        )
        
        # Validate that at least one update method is specified
        if data.quantity_change is None and data.quantity_absolute is None:
            raise ValidationError(
                "quantity",
                "Either quantity_change or quantity_absolute must be provided",
            )
        
        # Get current product
        product = await self._product_service.get_by_id(product_id)
        
        # Calculate new quantity
        if data.quantity_absolute is not None:
            new_quantity = data.quantity_absolute
            quantity_change = new_quantity - product.stock_quantity
        else:
            quantity_change = data.quantity_change
            new_quantity = product.stock_quantity + quantity_change
        
        # Validate new quantity
        if new_quantity < 0:
            raise ValidationError(
                "stock_quantity",
                f"Insufficient stock. Current: {product.stock_quantity}, requested change: {quantity_change}",
                details={"current_stock": product.stock_quantity, "requested_change": quantity_change},
            )
        
        # Update via product service
        updated_product = await self._product_service.update_stock(product_id, quantity_change)
        
        inventory_item = InventoryInDB(
            product_id=updated_product.id,
            product_name=updated_product.name,
            sku=updated_product.sku,
            stock_quantity=updated_product.stock_quantity,
            low_stock_threshold=10,
            last_updated=updated_product.updated_at,
        )
        
        logger.info(
            "inventory_updated",
            product_id=product_id,
            old_quantity=product.stock_quantity,
            new_quantity=updated_product.stock_quantity,
            reason=data.reason,
        )
        
        return inventory_item
