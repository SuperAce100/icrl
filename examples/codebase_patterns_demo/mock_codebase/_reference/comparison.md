# Pattern Comparison: Vanilla LLM vs ICRL

This document shows the concrete differences between what a vanilla LLM generates vs what ICRL generates after learning your patterns.

## Scenario: "Add a GET /orders/{order_id} endpoint"

### ❌ Vanilla LLM Output (Without ICRL)

```python
# app/routes/orders.py - What vanilla Claude/GPT might generate

from fastapi import APIRouter, HTTPException

router = APIRouter()

# In-memory storage (bad: no service layer)
orders_db = {
    1: {"id": 1, "user_id": 1, "total": 99.99, "status": "pending"}
}

@router.get("/orders/{order_id}")
async def get_order(order_id: int):
    """Get an order by ID."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")  # Wrong!
    
    order = orders_db[order_id]
    print(f"Retrieved order {order_id}")  # Wrong logging!
    return order  # Raw dict, no wrapper!
```

**Problems:**
- ❌ Uses `HTTPException` instead of `NotFoundError`
- ❌ Returns raw dict instead of `APIResponse`
- ❌ Uses `print()` instead of structured logging
- ❌ Business logic in route (no service layer)
- ❌ No type hints on return value
- ❌ No response_model declaration

---

### ✅ ICRL Output (After Learning Patterns)

```python
# app/routes/orders.py - What ICRL generates after learning

from fastapi import APIRouter

from app.core.response import APIResponse
from app.core.logging import get_logger
from app.models.order import OrderOut
from app.services import order_service

logger = get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=APIResponse[OrderOut])
async def get_order(order_id: int) -> APIResponse[OrderOut]:
    """Get an order by ID.
    
    Raises NotFoundError if order doesn't exist.
    """
    logger.info("get_order_request", order_id=order_id)
    
    # Service raises NotFoundError if not found
    order = await order_service.get_by_id(order_id)
    
    return APIResponse.success(
        data=OrderOut.model_validate(order),
        message="Order retrieved successfully",
    )
```

**Correct patterns:**
- ✅ Uses `NotFoundError` (raised by service)
- ✅ Returns `APIResponse[OrderOut]`
- ✅ Structured logging with `logger.info("event", key=value)`
- ✅ Delegates to `order_service` (service layer)
- ✅ Proper type hints
- ✅ `response_model` declaration for OpenAPI

---

## Side-by-Side: List Endpoint

### ❌ Vanilla

```python
@router.get("/orders")
def list_orders(skip: int = 0, limit: int = 10):
    orders = list(orders_db.values())[skip:skip+limit]
    return {"orders": orders, "count": len(orders)}
```

### ✅ ICRL

```python
@router.get("", response_model=APIResponse[PaginatedData[OrderOut]])
async def list_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    user_id: int | None = Query(None, description="Filter by user ID"),
) -> APIResponse[PaginatedData[OrderOut]]:
    """List all orders with pagination."""
    logger.info("list_orders_request", skip=skip, limit=limit, user_id=user_id)
    
    orders, total = await order_service.list(skip=skip, limit=limit, user_id=user_id)
    order_outs = [OrderOut.model_validate(o) for o in orders]
    
    return APIResponse.success(
        data=PaginatedData(items=order_outs, total=total, skip=skip, limit=limit),
        message=f"Retrieved {len(order_outs)} orders",
    )
```

---

## Side-by-Side: Create Endpoint

### ❌ Vanilla

```python
@router.post("/orders")
def create_order(user_id: int, items: list):
    order_id = max(orders_db.keys()) + 1
    order = {"id": order_id, "user_id": user_id, "items": items}
    orders_db[order_id] = order
    return order
```

### ✅ ICRL

```python
@router.post("", response_model=APIResponse[OrderOut], status_code=201)
async def create_order(order_data: OrderCreate) -> APIResponse[OrderOut]:
    """Create a new order.
    
    Validates products and calculates total.
    """
    logger.info("create_order_request", user_id=order_data.user_id)
    
    order = await order_service.create(order_data)
    
    return APIResponse.success(
        data=OrderOut.model_validate(order),
        message="Order created successfully",
    )
```

---

## Why This Matters

| Aspect | Vanilla LLM | ICRL |
|--------|-------------|------|
| **Consistency** | Every endpoint different | All endpoints follow same pattern |
| **Error handling** | Generic HTTPException | Custom exceptions with proper codes |
| **Response format** | Varies (dict, list, model) | Always `APIResponse[T]` |
| **Logging** | print() or nothing | Structured, searchable logs |
| **Architecture** | Logic in routes | Clean service layer separation |
| **Type safety** | Often missing | Full type hints |
| **Documentation** | Basic | OpenAPI-ready with examples |

**The compound effect**: After 10 endpoints, a vanilla LLM codebase is a mess of inconsistent patterns. An ICRL codebase looks like it was written by one person following strict guidelines.
