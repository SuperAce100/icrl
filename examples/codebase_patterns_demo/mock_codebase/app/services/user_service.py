"""User service - business logic for user operations.

This service handles all user-related business logic:
- CRUD operations
- Business rule validation
- Database interactions

Routes should call these methods, not implement logic themselves.
"""

from datetime import datetime, timezone
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.core.logging import get_logger
from app.models.user import UserCreate, UserUpdate, UserInDB

logger = get_logger(__name__)


# Mock database - in real app, this would be SQLAlchemy/async DB
_mock_users_db: dict[int, UserInDB] = {
    1: UserInDB(
        id=1,
        email="alice@acme.com",
        name="Alice Smith",
        department="Engineering",
        is_active=True,
        password_hash="hashed_password_here",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    ),
    2: UserInDB(
        id=2,
        email="bob@acme.com", 
        name="Bob Jones",
        department="Sales",
        is_active=True,
        password_hash="hashed_password_here",
        created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
    ),
}
_next_id = 3


class UserService:
    """Service for user operations.
    
    All methods follow these patterns:
    - Raise custom exceptions (NotFoundError, etc.) for error cases
    - Log operations with structured logging
    - Return internal models (UserInDB) - routes convert to UserOut
    """
    
    async def get_by_id(self, user_id: int) -> UserInDB:
        """Get a user by ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            The user if found
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        logger.info("user_fetch_started", user_id=user_id)
        
        user = _mock_users_db.get(user_id)
        if not user:
            logger.warning("user_not_found", user_id=user_id)
            raise NotFoundError("User", user_id)
        
        logger.info("user_fetch_completed", user_id=user_id)
        return user
    
    async def get_by_email(self, email: str) -> UserInDB | None:
        """Get a user by email.
        
        Args:
            email: The user's email
            
        Returns:
            The user if found, None otherwise
        """
        for user in _mock_users_db.values():
            if user.email == email:
                return user
        return None
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 20,
        active_only: bool = True,
    ) -> tuple[list[UserInDB], int]:
        """List users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            active_only: If True, only return active users
            
        Returns:
            Tuple of (users, total_count)
        """
        logger.info("user_list_started", skip=skip, limit=limit, active_only=active_only)
        
        all_users = list(_mock_users_db.values())
        if active_only:
            all_users = [u for u in all_users if u.is_active]
        
        total = len(all_users)
        users = all_users[skip : skip + limit]
        
        logger.info("user_list_completed", count=len(users), total=total)
        return users, total
    
    async def create(self, data: UserCreate) -> UserInDB:
        """Create a new user.
        
        Args:
            data: User creation data
            
        Returns:
            The created user
            
        Raises:
            ConflictError: If email already exists
        """
        global _next_id
        
        logger.info("user_create_started", email=data.email)
        
        # Check for duplicate email
        existing = await self.get_by_email(data.email)
        if existing:
            logger.warning("user_create_conflict", email=data.email)
            raise ConflictError(f"User with email '{data.email}' already exists")
        
        # Create user
        now = datetime.now(timezone.utc)
        user = UserInDB(
            id=_next_id,
            email=data.email,
            name=data.name,
            department=data.department,
            is_active=True,
            password_hash="temporary_hash",  # In real app: hash password
            created_at=now,
            updated_at=now,
        )
        
        _mock_users_db[_next_id] = user
        _next_id += 1
        
        logger.info("user_created", user_id=user.id, email=user.email)
        return user
    
    async def update(self, user_id: int, data: UserUpdate) -> UserInDB:
        """Update an existing user.
        
        Args:
            user_id: The user's ID
            data: Fields to update (only non-None fields are applied)
            
        Returns:
            The updated user
            
        Raises:
            NotFoundError: If user doesn't exist
            ConflictError: If new email already exists
        """
        logger.info("user_update_started", user_id=user_id)
        
        user = await self.get_by_id(user_id)
        
        # Check email uniqueness if changing email
        if data.email and data.email != user.email:
            existing = await self.get_by_email(data.email)
            if existing:
                raise ConflictError(f"User with email '{data.email}' already exists")
        
        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        updated_user = user.model_copy(update=update_data)
        updated_user = updated_user.model_copy(
            update={"updated_at": datetime.now(timezone.utc)}
        )
        
        _mock_users_db[user_id] = updated_user
        
        logger.info("user_updated", user_id=user_id, fields=list(update_data.keys()))
        return updated_user
    
    async def delete(self, user_id: int) -> None:
        """Delete a user (soft delete - sets is_active=False).
        
        Args:
            user_id: The user's ID
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        logger.info("user_delete_started", user_id=user_id)
        
        user = await self.get_by_id(user_id)
        
        # Soft delete
        updated_user = user.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        _mock_users_db[user_id] = updated_user
        
        logger.info("user_deleted", user_id=user_id)
