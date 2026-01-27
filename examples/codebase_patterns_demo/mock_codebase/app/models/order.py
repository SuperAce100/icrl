"""Order domain models.

Following ACME conventions:
- OrderCreate: What clients send to create an order
- OrderUpdate: What clients send to update (all optional)
- OrderOut: What we return to clients (no sensitive data)
- OrderInDB: Internal representation with all fields
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    """Input model for creating a new order.
    
    Validated fields only - no id, timestamps, or computed fields.
    """
    
    customer_id: int = Field(..., description="ID of the customer placing the order")
    product_id: int = Field(..., description="ID of the product being ordered")
    quantity: int = Field(..., ge=1, description="Quantity of items ordered")
    notes: str | None = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_id": 1,
                    "product_id": 101,
                    "quantity": 2,
                    "notes": "Please gift wrap",
                }
            ]
        }
    }


class OrderUpdate(BaseModel):
    """Input model for updating an order.
    
    All fields optional - only provided fields are updated.
    """
    
    quantity: int | None = Field(None, ge=1)
    notes: str | None = None
    status: str | None = Field(None, pattern="^(pending|confirmed|shipped|delivered|cancelled)$")


class OrderOut(BaseModel):
    """Output model for order data.
    
    This is what clients see - no internal fields.
    """
    
    id: int
    customer_id: int
    product_id: int
    quantity: int
    total_amount: Decimal
    status: str
    notes: str | None = None
    is_active: bool = True
    created_at: datetime
    
    model_config = {
        "from_attributes": True,  # Allow creating from ORM objects
    }


class OrderInDB(BaseModel):
    """Internal order model with all fields.
    
    Used internally - never returned directly to clients.
    """
    
    id: int
    customer_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    status: str
    notes: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
    }
