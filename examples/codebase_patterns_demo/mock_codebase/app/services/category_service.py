"""Category service - business logic for category operations.

This service handles all category-related business logic:
- CRUD operations
- Business rule validation

Routes should call these methods, not implement logic themselves.
"""

from datetime import datetime, timezone
from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import get_logger
from app.models.category import CategoryCreate, CategoryUpdate, CategoryInDB

logger = get_logger(__name__)


# Mock database - in real app, this would be SQLAlchemy/async DB
_mock_categories_db: dict[int, CategoryInDB] = {
    1: CategoryInDB(
        id=1,
        name="Widgets",
        description="Various types of widgets",
        parent_id=None,
        is_active=True,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    ),
    2: CategoryInDB(
        id=2,
        name="Gadgets",
        description="Electronic gadgets and devices",
        parent_id=None,
        is_active=True,
        created_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
    ),
    3: CategoryInDB(
        id=3,
        name="Thingamajigs",
        description="Miscellaneous thingamajigs",
        parent_id=None,
        is_active=True,
        created_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 10, tzinfo=timezone.utc),
    ),
}
_next_id = 4


class CategoryService:
    """Service for category operations.
    
    All methods follow these patterns:
    - Raise custom exceptions (NotFoundError, etc.) for error cases
    - Log operations with structured logging
    - Return internal models (CategoryInDB) - routes convert to CategoryOut
    """
    
    async def get_by_id(self, category_id: int) -> CategoryInDB:
        """Get a category by ID.
        
        Args:
            category_id: The category's ID
            
        Returns:
            The category if found
            
        Raises:
            NotFoundError: If category doesn't exist
        """
        logger.info("category_fetch_started", category_id=category_id)
        
        category = _mock_categories_db.get(category_id)
        if not category:
            logger.warning("category_not_found", category_id=category_id)
            raise NotFoundError("Category", category_id)
        
        logger.info("category_fetch_completed", category_id=category_id)
        return category
    
    async def get_by_name(self, name: str) -> CategoryInDB | None:
        """Get a category by name.
        
        Args:
            name: The category's name
            
        Returns:
            The category if found, None otherwise
        """
        for category in _mock_categories_db.values():
            if category.name.lower() == name.lower():
                return category
        return None
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        active_only: bool = True,
        parent_id: int | None = None,
    ) -> tuple[list[CategoryInDB], int]:
        """List categories with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            active_only: If True, only return active categories
            parent_id: Filter by parent category ID (optional)
            
        Returns:
            Tuple of (categories, total_count)
        """
        logger.info(
            "category_list_started",
            skip=skip,
            limit=limit,
            active_only=active_only,
            parent_id=parent_id,
        )
        
        all_categories = list(_mock_categories_db.values())
        
        if active_only:
            all_categories = [c for c in all_categories if c.is_active]
        
        if parent_id is not None:
            all_categories = [c for c in all_categories if c.parent_id == parent_id]
        
        total = len(all_categories)
        categories = all_categories[skip : skip + limit]
        
        logger.info("category_list_completed", count=len(categories), total=total)
        return categories, total
    
    async def create(self, data: CategoryCreate) -> CategoryInDB:
        """Create a new category.
        
        Args:
            data: Category creation data
            
        Returns:
            The created category
            
        Raises:
            ConflictError: If category name already exists
            NotFoundError: If parent_id is specified but doesn't exist
        """
        global _next_id
        
        logger.info("category_create_started", name=data.name)
        
        # Check for duplicate name
        existing = await self.get_by_name(data.name)
        if existing:
            logger.warning("category_create_conflict", name=data.name)
            raise ConflictError(f"Category with name '{data.name}' already exists")
        
        # Validate parent_id if provided
        if data.parent_id is not None:
            await self.get_by_id(data.parent_id)
        
        # Create category
        now = datetime.now(timezone.utc)
        category = CategoryInDB(
            id=_next_id,
            name=data.name,
            description=data.description,
            parent_id=data.parent_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        
        _mock_categories_db[_next_id] = category
        _next_id += 1
        
        logger.info("category_created", category_id=category.id, name=category.name)
        return category
    
    async def update(self, category_id: int, data: CategoryUpdate) -> CategoryInDB:
        """Update an existing category.
        
        Args:
            category_id: The category's ID
            data: Fields to update (only non-None fields are applied)
            
        Returns:
            The updated category
            
        Raises:
            NotFoundError: If category doesn't exist
            ConflictError: If new name already exists
        """
        logger.info("category_update_started", category_id=category_id)
        
        category = await self.get_by_id(category_id)
        
        # Check for duplicate name if name is being updated
        if data.name is not None and data.name.lower() != category.name.lower():
            existing = await self.get_by_name(data.name)
            if existing:
                logger.warning("category_update_conflict", name=data.name)
                raise ConflictError(f"Category with name '{data.name}' already exists")
        
        # Validate parent_id if provided
        if data.parent_id is not None:
            await self.get_by_id(data.parent_id)
        
        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        updated_category = category.model_copy(update=update_data)
        updated_category = updated_category.model_copy(
            update={"updated_at": datetime.now(timezone.utc)}
        )
        
        _mock_categories_db[category_id] = updated_category
        
        logger.info("category_updated", category_id=category_id, fields=list(update_data.keys()))
        return updated_category
    
    async def delete(self, category_id: int) -> None:
        """Delete a category (soft delete - sets is_active=False).
        
        Args:
            category_id: The category's ID
            
        Raises:
            NotFoundError: If category doesn't exist
        """
        logger.info("category_delete_started", category_id=category_id)
        
        category = await self.get_by_id(category_id)
        
        # Soft delete
        updated_category = category.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        _mock_categories_db[category_id] = updated_category
        
        logger.info("category_deleted", category_id=category_id)
