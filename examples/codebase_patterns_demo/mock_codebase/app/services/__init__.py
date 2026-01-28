"""Service layer for ACME API.

Services contain business logic and are the ONLY place that should:
- Access the database
- Implement business rules
- Coordinate between multiple operations

Routes should NEVER contain business logic - they only:
- Parse/validate input
- Call service methods
- Format responses

Pattern:
    # In routes/users.py
    user = await user_service.create(user_data)
    return APIResponse.success(data=UserOut.model_validate(user))
    
    # In services/user_service.py
    class UserService:
        async def create(self, data: UserCreate) -> UserInDB:
            # Validation, business rules, DB operations here
            ...
"""

from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.services.category_service import CategoryService
from app.services.inventory_service import InventoryService

# Singleton instances - import these in routes
user_service = UserService()
product_service = ProductService()
order_service = OrderService()
category_service = CategoryService()
inventory_service = InventoryService()

__all__ = [
    "CategoryService",
    "InventoryService",
    "OrderService",
    "ProductService",
    "UserService",
    "category_service",
    "inventory_service",
    "order_service",
    "product_service",
    "user_service",
]
