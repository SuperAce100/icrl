"""REFERENCE: Expected order models after ICRL completes the task.

This file shows what ICRL should generate when asked to:
"Add a GET /orders endpoint that returns a list of orders"

This is NOT imported by the app - it's just for reference/comparison.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status values."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItemCreate(BaseModel):
    """Input model for order line items."""
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class OrderItemOut(BaseModel):
    """Output model for order line items."""
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    
    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    """Input model for creating a new order."""
    user_id: int
    items: list[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: str
    notes: str | None = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "items": [
                        {"product_id": 1, "quantity": 2, "unit_price": "19.99"}
                    ],
                    "shipping_address": "123 Main St, Anytown, USA",
                }
            ]
        }
    }


class OrderUpdate(BaseModel):
    """Input model for updating an order."""
    status: OrderStatus | None = None
    shipping_address: str | None = None
    notes: str | None = None


class OrderOut(BaseModel):
    """Output model for order data."""
    id: int
    user_id: int
    items: list[OrderItemOut]
    status: OrderStatus
    total: Decimal
    shipping_address: str
    notes: str | None = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class OrderInDB(BaseModel):
    """Internal order model with all fields."""
    id: int
    user_id: int
    items: list[OrderItemOut]
    status: OrderStatus = OrderStatus.PENDING
    total: Decimal
    shipping_address: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
