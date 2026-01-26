"""Inventory domain models.

Following ACME conventions:
- InventoryUpdate: What clients send to update stock levels
- InventoryOut: What we return to clients
- InventoryInDB: Internal representation with all fields
"""

from datetime import datetime
from pydantic import BaseModel, Field


class InventoryUpdate(BaseModel):
    """Input model for updating inventory stock levels.
    
    Use quantity_change for relative adjustments (add/remove stock).
    Use quantity_absolute for setting exact stock level.
    """
    
    quantity_change: int | None = Field(
        None,
        description="Amount to add (positive) or remove (negative) from current stock"
    )
    quantity_absolute: int | None = Field(
        None,
        ge=0,
        description="Set stock to this exact quantity"
    )
    reason: str | None = Field(
        None,
        max_length=500,
        description="Reason for the stock adjustment"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "quantity_change": -5,
                    "reason": "Sold 5 units"
                },
                {
                    "quantity_absolute": 100,
                    "reason": "Inventory recount"
                }
            ]
        }
    }


class InventoryOut(BaseModel):
    """Output model for inventory data.
    
    This is what clients see.
    """
    
    product_id: int
    product_name: str
    sku: str
    stock_quantity: int
    low_stock_threshold: int = 10
    is_low_stock: bool = False
    last_updated: datetime
    
    model_config = {
        "from_attributes": True,
    }


class InventoryInDB(BaseModel):
    """Internal inventory model with all fields.
    
    Used internally - includes audit fields.
    """
    
    product_id: int
    product_name: str
    sku: str
    stock_quantity: int
    low_stock_threshold: int = 10
    last_updated: datetime
    
    model_config = {
        "from_attributes": True,
    }
    
    @property
    def is_low_stock(self) -> bool:
        """Check if stock is below threshold."""
        return self.stock_quantity <= self.low_stock_threshold
