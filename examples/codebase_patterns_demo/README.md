# Codebase-Specific Patterns Demo

This demo showcases ICRL's ability to learn and apply your team's specific coding patterns, conventions, and architectural decisions.

## The Problem with Vanilla Claude/Cursor

Every time you ask a vanilla LLM to add a new API endpoint, it uses generic patterns:
- Generic error handling
- Standard response formats
- Default logging approaches

You end up repeatedly correcting it: *"No, we use our custom `APIResponse` wrapper, not raw dicts!"*

## How ICRL Solves This

After successfully completing 2-3 similar tasks, ICRL:
1. **Stores successful trajectories** with your corrections baked in
2. **Retrieves relevant examples** when you ask for similar tasks
3. **Applies your patterns automatically** without re-prompting

## Demo Structure

```
mock_codebase/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with custom patterns
│   ├── core/
│   │   ├── __init__.py
│   │   ├── response.py      # Custom APIResponse wrapper
│   │   ├── exceptions.py    # Custom exception hierarchy
│   │   └── logging.py       # Structured logging setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # Example model
│   ├── routes/
│   │   ├── __init__.py
│   │   └── users.py         # Example endpoint (our pattern)
│   └── services/
│       ├── __init__.py
│       └── user_service.py  # Business logic layer
├── tests/
│   └── test_users.py
└── pyproject.toml
```

## The Custom Patterns (What ICRL Should Learn)

### 1. Response Wrapper
All endpoints return `APIResponse[T]` with consistent structure:
```python
@router.get("/users/{user_id}", response_model=APIResponse[UserOut])
async def get_user(user_id: int) -> APIResponse[UserOut]:
    user = await user_service.get_by_id(user_id)
    return APIResponse.success(data=user, message="User retrieved")
```

### 2. Exception Handling
We use custom exceptions that auto-convert to proper HTTP responses:
```python
from app.core.exceptions import NotFoundError, ValidationError

# NOT: raise HTTPException(status_code=404, ...)
# YES: raise NotFoundError(f"User {user_id} not found")
```

### 3. Service Layer Pattern
Routes don't contain business logic - they delegate to services:
```python
# Route just orchestrates
user = await user_service.create(user_data)

# Service contains logic
class UserService:
    async def create(self, data: UserCreate) -> User:
        # validation, business rules, DB operations
```

### 4. Structured Logging
All operations log with consistent context:
```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("user_created", user_id=user.id, email=user.email)
```

## Running the Demo

```bash
# 1. Set up the demo environment
cd examples/codebase_patterns_demo
python setup_demo.py

# 2. Navigate to the mock codebase
cd mock_codebase

# 3. First task: Add an orders endpoint (ICRL explores and learns)
icrl chat
# Ask: "Add a GET /orders endpoint that returns a list of orders. Follow the existing patterns."
# ICRL will explore users.py, products.py, etc. and learn the patterns
# Say 'yes' to save the trajectory

# 4. Second task: Add a categories endpoint (ICRL applies learned patterns)
# Ask: "Add a GET /categories endpoint with CRUD operations"
# ICRL retrieves the orders trajectory and applies patterns immediately
# Fewer steps, faster completion!

# 5. Ablation: See the difference without examples
icrl chat --no-examples
# Ask the same question and compare the output
```

## What to Observe

### First Task (Orders)
- ICRL explores the codebase structure
- Discovers patterns in `users.py`, `products.py`, `response.py`, etc.
- Creates endpoint following the exact patterns
- Trajectory is saved to the database

### Second Task (Categories)  
- ICRL retrieves the orders trajectory as an example
- Immediately applies correct patterns:
  - Uses `APIResponse` wrapper
  - Creates `CategoryService` 
  - Uses custom exceptions (`NotFoundError`, etc.)
  - Adds structured logging
- **Fewer exploration steps, faster completion**

### Ablation Mode (`--no-examples`)
- Side-by-side comparison shows the difference
- **With examples**: Follows your team's patterns from step 1
- **Without examples**: Uses generic FastAPI patterns
- Clear difference in code style and correctness

## Existing Patterns in the Codebase

The mock codebase already has `users` and `products` domains implemented correctly. These serve as:

1. **Learning examples** - ICRL can study these to understand patterns
2. **Consistency check** - New code should match existing style
3. **Reference implementations** - See `_reference/` for expected outputs

### File Structure

```
mock_codebase/
├── app/
│   ├── main.py                    # FastAPI app with exception handlers
│   ├── core/
│   │   ├── response.py            # APIResponse wrapper (MUST USE)
│   │   ├── exceptions.py          # Custom exception hierarchy
│   │   └── logging.py             # Structured logging setup
│   ├── models/
│   │   ├── user.py                # User domain models
│   │   └── product.py             # Product domain models
│   ├── routes/
│   │   ├── users.py               # User CRUD endpoints
│   │   └── products.py            # Product CRUD endpoints
│   └── services/
│       ├── user_service.py        # User business logic
│       └── product_service.py     # Product business logic
├── tests/
│   ├── test_users.py
│   └── test_products.py
├── _reference/                    # Expected outputs for comparison
│   ├── orders_model.py
│   ├── orders_service.py
│   └── orders_routes.py
└── pyproject.toml
```

## Why This Matters

Without ICRL, every time you ask an LLM to add a new endpoint:

```python
# What vanilla Claude/GPT might generate:
@router.get("/orders/{order_id}")
async def get_order(order_id: int):
    order = db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order  # Raw dict!
```

With ICRL after learning your patterns:

```python
# What ICRL generates after learning:
@router.get("/{order_id}", response_model=APIResponse[OrderOut])
async def get_order(order_id: int) -> APIResponse[OrderOut]:
    logger.info("get_order_request", order_id=order_id)
    order = await order_service.get_by_id(order_id)  # Service layer!
    return APIResponse.success(
        data=OrderOut.model_validate(order),
        message="Order retrieved successfully",
    )
```

The difference compounds across your entire codebase!
