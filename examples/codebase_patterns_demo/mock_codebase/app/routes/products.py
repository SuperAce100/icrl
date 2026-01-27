"""Product routes - CRUD operations for products.

This module follows the ACME API patterns:
1. All endpoints return APIResponse[T]
2. Business logic is in ProductService, not here
3. Custom exceptions are raised, not HTTPException
4. Structured logging for observability
"""

from fastapi import APIRouter, Query

from app.core.response import APIResponse, PaginatedData
from app.core.logging import get_logger
from app.models.product import ProductCreate, ProductUpdate, ProductOut
from app.services import product_service

logger = get_logger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=APIResponse[PaginatedData[ProductOut]])
async def list_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    active_only: bool = Query(True, description="Only return active products"),
    category: str | None = Query(None, description="Filter by category"),
) -> APIResponse[PaginatedData[ProductOut]]:
    """List all products with pagination and filtering.
    
    Returns a paginated list of products. By default, only active products are returned.
    Optionally filter by category.
    """
    logger.info(
        "list_products_request",
        skip=skip,
        limit=limit,
        active_only=active_only,
        category=category,
    )
    
    products, total = await product_service.list(
        skip=skip,
        limit=limit,
        active_only=active_only,
        category=category,
    )
    
    # Convert internal models to output models
    product_outs = [ProductOut.model_validate(p) for p in products]
    
    return APIResponse.success(
        data=PaginatedData(items=product_outs, total=total, skip=skip, limit=limit),
        message=f"Retrieved {len(product_outs)} products",
    )


@router.get("/{product_id}", response_model=APIResponse[ProductOut])
async def get_product(product_id: int) -> APIResponse[ProductOut]:
    """Get a product by ID.
    
    Raises NotFoundError if product doesn't exist.
    """
    logger.info("get_product_request", product_id=product_id)
    
    # Service raises NotFoundError if not found - exception handler converts to 404
    product = await product_service.get_by_id(product_id)
    
    return APIResponse.success(
        data=ProductOut.model_validate(product),
        message="Product retrieved successfully",
    )


@router.post("", response_model=APIResponse[ProductOut], status_code=201)
async def create_product(product_data: ProductCreate) -> APIResponse[ProductOut]:
    """Create a new product.
    
    Raises ConflictError if SKU already exists.
    """
    logger.info("create_product_request", sku=product_data.sku, name=product_data.name)
    
    # Service handles validation and raises ConflictError if SKU exists
    product = await product_service.create(product_data)
    
    return APIResponse.success(
        data=ProductOut.model_validate(product),
        message="Product created successfully",
    )


@router.patch("/{product_id}", response_model=APIResponse[ProductOut])
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
) -> APIResponse[ProductOut]:
    """Update an existing product.
    
    Only provided fields are updated. Raises NotFoundError if product doesn't exist.
    """
    logger.info("update_product_request", product_id=product_id)
    
    product = await product_service.update(product_id, product_data)
    
    return APIResponse.success(
        data=ProductOut.model_validate(product),
        message="Product updated successfully",
    )


@router.delete("/{product_id}", response_model=APIResponse[None])
async def delete_product(product_id: int) -> APIResponse[None]:
    """Delete a product (soft delete).
    
    Sets the product's is_active flag to False. Raises NotFoundError if product doesn't exist.
    """
    logger.info("delete_product_request", product_id=product_id)
    
    await product_service.delete(product_id)
    
    return APIResponse.success(
        data=None,
        message="Product deleted successfully",
    )


@router.post("/{product_id}/stock", response_model=APIResponse[ProductOut])
async def update_stock(
    product_id: int,
    quantity_change: int = Query(..., description="Amount to add (positive) or remove (negative)"),
) -> APIResponse[ProductOut]:
    """Update product stock quantity.
    
    Use positive values to add stock, negative to remove.
    Raises ValidationError if resulting stock would be negative.
    """
    logger.info(
        "update_stock_request",
        product_id=product_id,
        quantity_change=quantity_change,
    )
    
    product = await product_service.update_stock(product_id, quantity_change)
    
    return APIResponse.success(
        data=ProductOut.model_validate(product),
        message=f"Stock updated. New quantity: {product.stock_quantity}",
    )
