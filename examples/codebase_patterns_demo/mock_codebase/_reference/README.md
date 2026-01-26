# Reference Solutions

This directory contains **reference implementations** showing what ICRL should generate when asked to add new endpoints.

**These files are NOT imported by the app** - they're just for comparison and validation.

## Purpose

When running the demo, you can compare ICRL's output against these reference files to see:

1. **Pattern adherence**: Does ICRL use `APIResponse` wrapper, custom exceptions, etc.?
2. **Code structure**: Does it follow the service layer pattern?
3. **Logging style**: Does it use structured logging with key-value pairs?
4. **Model conventions**: Does it use the `Create/Update/Out/InDB` naming?

## Files

- `orders_model.py` - Expected Pydantic models for orders
- `orders_service.py` - Expected service layer implementation
- `orders_routes.py` - Expected route handlers

## Comparison Checklist

After ICRL generates an orders endpoint, check:

| Pattern | Expected | Check |
|---------|----------|-------|
| Response wrapper | `APIResponse[OrderOut]` | ☐ |
| Pagination | `PaginatedData[OrderOut]` | ☐ |
| Exceptions | `NotFoundError`, not `HTTPException` | ☐ |
| Logging | `logger.info("event", key=value)` | ☐ |
| Service layer | Routes call `order_service.method()` | ☐ |
| Model naming | `OrderCreate`, `OrderOut`, `OrderInDB` | ☐ |

## Ablation Comparison

When running with `--no-examples`, you'll likely see:

- Raw dict returns instead of `APIResponse`
- `HTTPException` instead of custom exceptions
- Business logic in routes instead of service layer
- `print()` or f-string logging instead of structured logging

This demonstrates the value of ICRL's pattern learning!
