"""User domain models.

Following ACME conventions:
- UserCreate: What clients send to create a user
- UserUpdate: What clients send to update (all optional)
- UserOut: What we return to clients (no sensitive data)
- UserInDB: Internal representation with all fields
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Input model for creating a new user.
    
    Validated fields only - no id, timestamps, or computed fields.
    """
    
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    department: str | None = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "alice@acme.com",
                    "name": "Alice Smith",
                    "department": "Engineering",
                }
            ]
        }
    }


class UserUpdate(BaseModel):
    """Input model for updating a user.
    
    All fields optional - only provided fields are updated.
    """
    
    email: EmailStr | None = None
    name: str | None = Field(None, min_length=1, max_length=100)
    department: str | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    """Output model for user data.
    
    This is what clients see - no internal fields like password_hash.
    """
    
    id: int
    email: EmailStr
    name: str
    department: str | None = None
    is_active: bool = True
    created_at: datetime
    
    model_config = {
        "from_attributes": True,  # Allow creating from ORM objects
    }


class UserInDB(BaseModel):
    """Internal user model with all fields.
    
    Used internally - never returned directly to clients.
    """
    
    id: int
    email: str
    name: str
    department: str | None = None
    is_active: bool = True
    password_hash: str  # Never expose this!
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
    }
