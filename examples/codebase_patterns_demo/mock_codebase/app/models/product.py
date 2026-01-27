"""Product domain models.

Following ACME conventions:
- ProductCreate: What clients send to create a product
- ProductUpdate: What clients send to update (all optional)
- ProductOut: What we return to clients
- ProductInDB: Internal representation with all fields
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Input model for creating a new product.
    
    Validated fields only - no id, timestamps, or computed fields.
    """
    
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    sku: str = Field(..., min_length=1, max_length=50, description="Stock Keeping Unit")
    price: Decimal = Field(..., gt=0, description="Price in USD")
    category: str | None = None
    stock_quantity: int = Field(default=0, ge=0)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Widget Pro",
                    "description": "Professional-grade widget",
                    "sku": "WGT-PRO-001",
                    "price": "29.99",
                    "category": "Widgets",
                    "stock_quantity": 100,
                }
            ]
        }
    }


class ProductUpdate(BaseModel):
    """Input model for updating a product.
    
    All fields optional - only provided fields are updated.
    """
    
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(None, gt=0)
    category: str | None = None
    stock_quantity: int | None = Field(None, ge=0)
    is_active: bool | None = None


class ProductOut(BaseModel):
    """Output model for product data.
    
    This is what clients see.
    """
    
    id: int
    name: str
    description: str | None = None
    sku: str
    price: Decimal
    category: str | None = None
    stock_quantity: int
    is_active: bool = True
    created_at: datetime
    
    model_config = {
        "from_attributes": True,
    }


class ProductInDB(BaseModel):
    """Internal product model with all fields.
    
    Used internally - includes audit fields.
    """
    
    id: int
    name: str
    description: str | None = None
    sku: str
    price: Decimal
    category: str | None = None
    stock_quantity: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
    }
