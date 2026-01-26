"""Product service - business logic for product operations.

This service handles all product-related business logic:
- CRUD operations
- Inventory management
- Business rule validation

Routes should call these methods, not implement logic themselves.
"""

from datetime import datetime, timezone
from decimal import Decimal
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.core.logging import get_logger
from app.models.product import ProductCreate, ProductUpdate, ProductInDB

logger = get_logger(__name__)


# Mock database - in real app, this would be SQLAlchemy/async DB
_mock_products_db: dict[int, ProductInDB] = {
    1: ProductInDB(
        id=1,
        name="Widget Standard",
        description="Our classic widget for everyday use",
        sku="WGT-STD-001",
        price=Decimal("19.99"),
        category="Widgets",
        stock_quantity=250,
        is_active=True,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    ),
    2: ProductInDB(
        id=2,
        name="Gadget Deluxe",
        description="Premium gadget with advanced features",
        sku="GDG-DLX-001",
        price=Decimal("49.99"),
        category="Gadgets",
        stock_quantity=75,
        is_active=True,
        created_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
    ),
    3: ProductInDB(
        id=3,
        name="Thingamajig Basic",
        description="Entry-level thingamajig",
        sku="THG-BSC-001",
        price=Decimal("9.99"),
        category="Thingamajigs",
        stock_quantity=500,
        is_active=True,
        created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
    ),
}
_next_id = 4


class ProductService:
    """Service for product operations.
    
    All methods follow these patterns:
    - Raise custom exceptions (NotFoundError, etc.) for error cases
    - Log operations with structured logging
    - Return internal models (ProductInDB) - routes convert to ProductOut
    """
    
    async def get_by_id(self, product_id: int) -> ProductInDB:
        """Get a product by ID.
        
        Args:
            product_id: The product's ID
            
        Returns:
            The product if found
            
        Raises:
            NotFoundError: If product doesn't exist
        """
        logger.info("product_fetch_started", product_id=product_id)
        
        product = _mock_products_db.get(product_id)
        if not product:
            logger.warning("product_not_found", product_id=product_id)
            raise NotFoundError("Product", product_id)
        
        logger.info("product_fetch_completed", product_id=product_id)
        return product
    
    async def get_by_sku(self, sku: str) -> ProductInDB | None:
        """Get a product by SKU.
        
        Args:
            sku: The product's SKU
            
        Returns:
            The product if found, None otherwise
        """
        for product in _mock_products_db.values():
            if product.sku == sku:
                return product
        return None
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        active_only: bool = True,
        category: str | None = None,
    ) -> tuple[list[ProductInDB], int]:
        """List products with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            active_only: If True, only return active products
            category: Filter by category (optional)
            
        Returns:
            Tuple of (products, total_count)
        """
        logger.info(
            "product_list_started",
            skip=skip,
            limit=limit,
            active_only=active_only,
            category=category,
        )
        
        all_products = list(_mock_products_db.values())
        
        if active_only:
            all_products = [p for p in all_products if p.is_active]
        
        if category:
            all_products = [p for p in all_products if p.category == category]
        
        total = len(all_products)
        products = all_products[skip : skip + limit]
        
        logger.info("product_list_completed", count=len(products), total=total)
        return products, total
    
    async def create(self, data: ProductCreate) -> ProductInDB:
        """Create a new product.
        
        Args:
            data: Product creation data
            
        Returns:
            The created product
            
        Raises:
            ConflictError: If SKU already exists
        """
        global _next_id
        
        logger.info("product_create_started", sku=data.sku, name=data.name)
        
        # Check for duplicate SKU
        existing = await self.get_by_sku(data.sku)
        if existing:
            logger.warning("product_create_conflict", sku=data.sku)
            raise ConflictError(f"Product with SKU '{data.sku}' already exists")
        
        # Create product
        now = datetime.now(timezone.utc)
        product = ProductInDB(
            id=_next_id,
            name=data.name,
            description=data.description,
            sku=data.sku,
            price=data.price,
            category=data.category,
            stock_quantity=data.stock_quantity,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        
        _mock_products_db[_next_id] = product
        _next_id += 1
        
        logger.info("product_created", product_id=product.id, sku=product.sku)
        return product
    
    async def update(self, product_id: int, data: ProductUpdate) -> ProductInDB:
        """Update an existing product.
        
        Args:
            product_id: The product's ID
            data: Fields to update (only non-None fields are applied)
            
        Returns:
            The updated product
            
        Raises:
            NotFoundError: If product doesn't exist
        """
        logger.info("product_update_started", product_id=product_id)
        
        product = await self.get_by_id(product_id)
        
        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        updated_product = product.model_copy(update=update_data)
        updated_product = updated_product.model_copy(
            update={"updated_at": datetime.now(timezone.utc)}
        )
        
        _mock_products_db[product_id] = updated_product
        
        logger.info("product_updated", product_id=product_id, fields=list(update_data.keys()))
        return updated_product
    
    async def delete(self, product_id: int) -> None:
        """Delete a product (soft delete - sets is_active=False).
        
        Args:
            product_id: The product's ID
            
        Raises:
            NotFoundError: If product doesn't exist
        """
        logger.info("product_delete_started", product_id=product_id)
        
        product = await self.get_by_id(product_id)
        
        # Soft delete
        updated_product = product.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        _mock_products_db[product_id] = updated_product
        
        logger.info("product_deleted", product_id=product_id)
    
    async def update_stock(self, product_id: int, quantity_change: int) -> ProductInDB:
        """Update product stock quantity.
        
        Args:
            product_id: The product's ID
            quantity_change: Amount to add (positive) or remove (negative)
            
        Returns:
            The updated product
            
        Raises:
            NotFoundError: If product doesn't exist
            ValidationError: If resulting stock would be negative
        """
        logger.info(
            "product_stock_update_started",
            product_id=product_id,
            quantity_change=quantity_change,
        )
        
        product = await self.get_by_id(product_id)
        
        new_quantity = product.stock_quantity + quantity_change
        if new_quantity < 0:
            raise ValidationError(
                "stock_quantity",
                f"Insufficient stock. Current: {product.stock_quantity}, requested change: {quantity_change}",
                details={"current_stock": product.stock_quantity, "requested_change": quantity_change},
            )
        
        updated_product = product.model_copy(
            update={
                "stock_quantity": new_quantity,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        _mock_products_db[product_id] = updated_product
        
        logger.info(
            "product_stock_updated",
            product_id=product_id,
            old_quantity=product.stock_quantity,
            new_quantity=new_quantity,
        )
        return updated_product
