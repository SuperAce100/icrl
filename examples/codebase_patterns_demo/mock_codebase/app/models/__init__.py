"""Pydantic models for ACME API.

Models are organized by domain:
- user.py: User-related models
- product.py: Product-related models
- (add more as needed)

Naming conventions:
- {Entity}Create: Input for creating new entities
- {Entity}Update: Input for updating entities (all fields optional)
- {Entity}Out: Output model (what we return to clients)
- {Entity}InDB: Internal model with DB-specific fields (id, timestamps)
"""

from app.models.user import (
    UserCreate,
    UserUpdate,
    UserOut,
    UserInDB,
)
from app.models.product import (
    ProductCreate,
    ProductUpdate,
    ProductOut,
    ProductInDB,
)
from app.models.order import (
    OrderCreate,
    OrderUpdate,
    OrderOut,
    OrderInDB,
)
from app.models.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryOut,
    CategoryInDB,
)
from app.models.inventory import (
    InventoryUpdate,
    InventoryOut,
    InventoryInDB,
)

__all__ = [
    # User models
    "UserCreate",
    "UserUpdate", 
    "UserOut",
    "UserInDB",
    # Product models
    "ProductCreate",
    "ProductUpdate",
    "ProductOut",
    "ProductInDB",
    # Order models
    "OrderCreate",
    "OrderUpdate",
    "OrderOut",
    "OrderInDB",
    # Category models
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryOut",
    "CategoryInDB",
    # Inventory models
    "InventoryUpdate",
    "InventoryOut",
    "InventoryInDB",
]
