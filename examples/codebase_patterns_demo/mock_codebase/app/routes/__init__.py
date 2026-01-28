"""API routes for ACME API.

Each route module should:
1. Create a router with appropriate prefix and tags
2. Use APIResponse for all responses
3. Delegate business logic to services
4. Use custom exceptions for errors

Example structure:
    router = APIRouter(prefix="/users", tags=["users"])
    
    @router.get("/{user_id}", response_model=APIResponse[UserOut])
    async def get_user(user_id: int) -> APIResponse[UserOut]:
        user = await user_service.get_by_id(user_id)
        return APIResponse.success(data=UserOut.model_validate(user))
"""

from app.routes.users import router as users_router
from app.routes.products import router as products_router
from app.routes.orders import router as orders_router
from app.routes.categories import router as categories_router
from app.routes.inventory import router as inventory_router

__all__ = [
    "categories_router",
    "inventory_router",
    "orders_router",
    "products_router",
    "users_router",
]
