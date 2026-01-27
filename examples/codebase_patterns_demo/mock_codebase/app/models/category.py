"""Category domain models.

Following ACME conventions:
- CategoryCreate: What clients send to create a category
- CategoryUpdate: What clients send to update (all optional)
- CategoryOut: What we return to clients
- CategoryInDB: Internal representation with all fields
"""

from datetime import datetime
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Input model for creating a new category.
    
    Validated fields only - no id, timestamps, or computed fields.
    """
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    parent_id: int | None = Field(None, description="Parent category ID for nested categories")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Electronics",
                    "description": "Electronic devices and accessories",
                    "parent_id": None,
                }
            ]
        }
    }


class CategoryUpdate(BaseModel):
    """Input model for updating a category.
    
    All fields optional - only provided fields are updated.
    """
    
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    parent_id: int | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    """Output model for category data.
    
    This is what clients see.
    """
    
    id: int
    name: str
    description: str | None = None
    parent_id: int | None = None
    is_active: bool = True
    created_at: datetime
    
    model_config = {
        "from_attributes": True,
    }


class CategoryInDB(BaseModel):
    """Internal category model with all fields.
    
    Used internally - includes audit fields.
    """
    
    id: int
    name: str
    description: str | None = None
    parent_id: int | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
    }
