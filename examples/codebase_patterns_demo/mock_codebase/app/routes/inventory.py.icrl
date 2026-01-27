"""Inventory routes - operations for tracking product inventory.

This module follows the ACME API patterns:
1. All endpoints return APIResponse[T]
2. Business logic is in InventoryService, not here
3. Custom exceptions are raised, not HTTPException
4. Structured logging for observability
"""

from fastapi import APIRouter, Query

from app.core.response import APIResponse, PaginatedData
from app.core.logging import get_logger
from app.models.inventory import InventoryUpdate, InventoryOut
from app.services import inventory_service

logger = get_logger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=APIResponse[PaginatedData[InventoryOut]])
async def list_inventory(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    low_stock_only: bool = Query(False, description="Only return items with low stock"),
) -> APIResponse[PaginatedData[InventoryOut]]:
    """List all inventory items with pagination and filtering.
    
    Returns a paginated list of inventory items. Optionally filter to show
    only items with low stock levels.
    """
    logger.info(
        "list_inventory_request",
        skip=skip,
        limit=limit,
        low_stock_only=low_stock_only,
    )
    
    items, total = await inventory_service.list(
        skip=skip,
        limit=limit,
        low_stock_only=low_stock_only,
    )
    
    # Convert internal models to output models
    inventory_outs = [
        InventoryOut(
            product_id=item.product_id,
            product_name=item.product_name,
            sku=item.sku,
            stock_quantity=item.stock_quantity,
            low_stock_threshold=item.low_stock_threshold,
            is_low_stock=item.is_low_stock,
            last_updated=item.last_updated,
        )
        for item in items
    ]
    
    return APIResponse.success(
        data=PaginatedData(items=inventory_outs, total=total, skip=skip, limit=limit),
        message=f"Retrieved {len(inventory_outs)} inventory items",
    )


@router.get("/{product_id}", response_model=APIResponse[InventoryOut])
async def get_inventory(product_id: int) -> APIResponse[InventoryOut]:
    """Get inventory for a specific product.
    
    Raises NotFoundError if product doesn't exist.
    """
    logger.info("get_inventory_request", product_id=product_id)
    
    item = await inventory_service.get_by_product_id(product_id)
    
    inventory_out = InventoryOut(
        product_id=item.product_id,
        product_name=item.product_name,
        sku=item.sku,
        stock_quantity=item.stock_quantity,
        low_stock_threshold=item.low_stock_threshold,
        is_low_stock=item.is_low_stock,
        last_updated=item.last_updated,
    )
    
    return APIResponse.success(
        data=inventory_out,
        message="Inventory retrieved successfully",
    )


@router.patch("/{product_id}", response_model=APIResponse[InventoryOut])
async def update_stock(
    product_id: int,
    update_data: InventoryUpdate,
) -> APIResponse[InventoryOut]:
    """Update stock level for a product.
    
    Use quantity_change for relative adjustments (positive to add, negative to remove).
    Use quantity_absolute to set an exact stock level.
    
    Raises NotFoundError if product doesn't exist.
    Raises ValidationError if resulting stock would be negative.
    """
    logger.info(
        "update_stock_request",
        product_id=product_id,
        quantity_change=update_data.quantity_change,
        quantity_absolute=update_data.quantity_absolute,
    )
    
    item = await inventory_service.update_stock(product_id, update_data)
    
    inventory_out = InventoryOut(
        product_id=item.product_id,
        product_name=item.product_name,
        sku=item.sku,
        stock_quantity=item.stock_quantity,
        low_stock_threshold=item.low_stock_threshold,
        is_low_stock=item.is_low_stock,
        last_updated=item.last_updated,
    )
    
    return APIResponse.success(
        data=inventory_out,
        message=f"Stock updated. New quantity: {item.stock_quantity}",
    )
