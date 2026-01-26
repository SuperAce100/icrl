# ACME API Patterns Guide

This document describes the coding patterns that ALL new endpoints must follow.

## Quick Reference

| Pattern | Do This | Not This |
|---------|---------|----------|
| Response | `APIResponse.success(data=...)` | `return {...}` |
| Errors | `raise NotFoundError("User", id)` | `raise HTTPException(404, ...)` |
| Logging | `logger.info("event", key=value)` | `print(f"...")` |
| Logic | `await user_service.create(data)` | Business logic in route |

---

## 1. Response Wrapper

**Always** return `APIResponse[T]`:

```python
from app.core.response import APIResponse, PaginatedData

@router.get("/{id}", response_model=APIResponse[ItemOut])
async def get_item(id: int) -> APIResponse[ItemOut]:
    item = await item_service.get_by_id(id)
    return APIResponse.success(
        data=ItemOut.model_validate(item),
        message="Item retrieved successfully",
    )
```

For lists, use `PaginatedData`:

```python
@router.get("", response_model=APIResponse[PaginatedData[ItemOut]])
async def list_items(skip: int = 0, limit: int = 20):
    items, total = await item_service.list(skip=skip, limit=limit)
    return APIResponse.success(
        data=PaginatedData(items=items, total=total, skip=skip, limit=limit),
        message=f"Retrieved {len(items)} items",
    )
```

---

## 2. Custom Exceptions

**Never** use `HTTPException`. Use our custom exceptions:

```python
from app.core.exceptions import NotFoundError, ValidationError, ConflictError

# In service layer:
raise NotFoundError("User", user_id)
raise ValidationError("email", "Invalid format")
raise ConflictError("User with this email already exists")
```

Available exceptions:
- `NotFoundError(resource_type, resource_id)` → 404
- `ValidationError(field, reason)` → 400
- `ConflictError(message)` → 409
- `ForbiddenError(message)` → 403
- `RateLimitError(message)` → 429

---

## 3. Service Layer

Routes **delegate** to services. They don't contain business logic:

```python
# ✅ CORRECT - Route delegates to service
@router.post("", response_model=APIResponse[UserOut], status_code=201)
async def create_user(data: UserCreate) -> APIResponse[UserOut]:
    user = await user_service.create(data)  # Service handles logic
    return APIResponse.success(data=UserOut.model_validate(user))

# ❌ WRONG - Business logic in route
@router.post("")
async def create_user(data: UserCreate):
    if await db.get_by_email(data.email):  # NO! This belongs in service
        raise ConflictError("...")
    user = await db.insert(data)  # NO! Direct DB access
    return user
```

---

## 4. Structured Logging

Use `get_logger` with **key-value pairs**:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# ✅ CORRECT - Structured logging
logger.info("user_created", user_id=user.id, email=user.email)
logger.warning("rate_limit_approaching", user_id=user.id, current=95, limit=100)
logger.error("payment_failed", order_id=order.id, reason=str(e))

# ❌ WRONG - String interpolation
logger.info(f"Created user {user.id}")  # NO!
print(f"User created: {user}")  # NEVER use print!
```

---

## 5. Model Naming

Follow the naming convention:

- `{Entity}Create` - Input for creating (no id, no timestamps)
- `{Entity}Update` - Input for updating (all fields optional)
- `{Entity}Out` - Output to clients (no sensitive fields)
- `{Entity}InDB` - Internal with all fields

```python
# models/order.py
class OrderCreate(BaseModel):
    user_id: int
    items: list[OrderItemCreate]

class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    notes: str | None = None

class OrderOut(BaseModel):
    id: int
    user_id: int
    total: Decimal
    status: OrderStatus
    created_at: datetime
    
    model_config = {"from_attributes": True}

class OrderInDB(BaseModel):
    id: int
    user_id: int
    total: Decimal
    status: OrderStatus
    internal_notes: str  # Not exposed in OrderOut
    created_at: datetime
    updated_at: datetime
```

---

## 6. File Organization

New domains should follow this structure:

```
app/
├── models/
│   └── order.py          # OrderCreate, OrderUpdate, OrderOut, OrderInDB
├── services/
│   └── order_service.py  # OrderService class
└── routes/
    └── orders.py         # Router with endpoints
```

Don't forget to:
1. Export from `models/__init__.py`
2. Export from `services/__init__.py` (create singleton)
3. Export from `routes/__init__.py`
4. Register router in `main.py`

---

## Checklist for New Endpoints

- [ ] Created models in `models/{entity}.py`
- [ ] Created service in `services/{entity}_service.py`
- [ ] Created routes in `routes/{entity}s.py`
- [ ] All endpoints return `APIResponse[T]`
- [ ] Using `response_model=` declaration
- [ ] Using return type hints
- [ ] Delegating to service (no business logic in routes)
- [ ] Using custom exceptions (no HTTPException)
- [ ] Using structured logging
- [ ] Added to `__init__.py` exports
- [ ] Registered router in `main.py`
- [ ] Added tests in `tests/test_{entity}s.py`
