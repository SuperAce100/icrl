#!/usr/bin/env python3
"""Setup script for the codebase patterns demo.

This script prepares the demo environment by:
1. Creating a fresh trajectory database for the demo
2. Optionally pre-seeding with example trajectories
3. Verifying the mock codebase is properly structured

Usage:
    python setup_demo.py           # Fresh start
    python setup_demo.py --seed    # Pre-seed with example trajectories
    python setup_demo.py --clean   # Remove all demo data
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


DEMO_DIR = Path(__file__).parent
MOCK_CODEBASE = DEMO_DIR / "mock_codebase"
DEMO_DB_PATH = DEMO_DIR / ".demo_trajectories"


def verify_codebase_structure() -> bool:
    """Verify the mock codebase has the expected structure."""
    required_files = [
        "app/main.py",
        "app/core/response.py",
        "app/core/exceptions.py",
        "app/core/logging.py",
        "app/routes/users.py",
        "app/services/user_service.py",
        "app/models/user.py",
    ]
    
    missing = []
    for file in required_files:
        if not (MOCK_CODEBASE / file).exists():
            missing.append(file)
    
    if missing:
        print("❌ Missing required files:")
        for f in missing:
            print(f"   - {f}")
        return False
    
    print("✅ Mock codebase structure verified")
    return True


def clean_demo_data():
    """Remove all demo trajectory data."""
    if DEMO_DB_PATH.exists():
        shutil.rmtree(DEMO_DB_PATH)
        print(f"✅ Removed demo database: {DEMO_DB_PATH}")
    else:
        print("ℹ️  No demo database to clean")


def create_fresh_database():
    """Create a fresh trajectory database for the demo."""
    clean_demo_data()
    DEMO_DB_PATH.mkdir(parents=True, exist_ok=True)
    (DEMO_DB_PATH / "trajectories").mkdir(exist_ok=True)
    print(f"✅ Created fresh demo database: {DEMO_DB_PATH}")


def create_example_trajectory() -> dict:
    """Create an example trajectory showing the correct patterns.
    
    This represents what ICRL would learn from a successful "add products endpoint" task.
    """
    return {
        "id": "demo-products-trajectory-001",
        "goal": "Add a GET /products endpoint that returns a list of products. Follow the existing patterns in the codebase.",
        "plan": """1. Explore the existing codebase structure to understand patterns
2. Look at users.py route as a reference for the pattern
3. Create ProductInDB, ProductCreate, ProductUpdate, ProductOut models
4. Create ProductService with list() method
5. Create products.py route following the users.py pattern
6. Register the router in main.py
7. Add tests following test_users.py pattern""",
        "steps": [
            {
                "observation": "Found app/routes/users.py with APIResponse pattern, app/core/response.py with APIResponse class, app/services/user_service.py with service pattern",
                "reasoning": "The codebase uses a consistent pattern: routes return APIResponse[T], delegate to services, use custom exceptions. I should follow this exactly.",
                "action": "Read app/routes/users.py to understand the exact pattern"
            },
            {
                "observation": "users.py shows: 1) Import APIResponse, PaginatedData from app.core.response 2) Import get_logger from app.core.logging 3) Use response_model=APIResponse[PaginatedData[UserOut]] 4) Call service methods 5) Return APIResponse.success(data=..., message=...)",
                "reasoning": "I need to create the same structure for products: models, service, route. The route should use APIResponse wrapper and delegate to ProductService.",
                "action": "Create app/models/product.py with ProductCreate, ProductUpdate, ProductOut, ProductInDB following user.py pattern"
            },
            {
                "observation": "Created product models following the user.py naming convention",
                "reasoning": "Now I need to create the service layer. Looking at user_service.py, it uses structured logging, raises custom exceptions (NotFoundError, ConflictError), and returns internal models.",
                "action": "Create app/services/product_service.py with ProductService class following user_service.py pattern"
            },
            {
                "observation": "Created ProductService with list(), get_by_id(), create(), update(), delete() methods using structured logging and custom exceptions",
                "reasoning": "Now I need to create the route. It should import from app.core.response, app.core.logging, use APIResponse wrapper, and delegate to product_service.",
                "action": "Create app/routes/products.py following users.py pattern exactly"
            },
            {
                "observation": "Created products.py route with all CRUD endpoints using APIResponse wrapper",
                "reasoning": "Need to register the router in main.py and update __init__.py files",
                "action": "Update app/routes/__init__.py to export products_router, update app/main.py to include products_router"
            }
        ],
        "success": True,
        "metadata": {
            "demo": True,
            "patterns_demonstrated": [
                "APIResponse wrapper",
                "Service layer pattern", 
                "Custom exceptions",
                "Structured logging",
                "Pydantic model conventions"
            ]
        }
    }


def seed_example_trajectories():
    """Pre-seed the database with example trajectories."""
    trajectories_dir = DEMO_DB_PATH / "trajectories"
    trajectories_dir.mkdir(parents=True, exist_ok=True)
    
    # Create example trajectory
    trajectory = create_example_trajectory()
    traj_file = trajectories_dir / f"{trajectory['id']}.json"
    
    with open(traj_file, "w") as f:
        json.dump(trajectory, f, indent=2)
    
    print(f"✅ Seeded example trajectory: {trajectory['id']}")
    print(f"   Goal: {trajectory['goal'][:60]}...")


def print_demo_instructions():
    """Print instructions for running the demo."""
    print("\n" + "=" * 60)
    print("🎯 CODEBASE PATTERNS DEMO READY")
    print("=" * 60)
    print("""
This demo shows how ICRL learns your team's coding patterns.

DEMO WORKFLOW:
─────────────────────────────────────────────────────────────

1. FIRST TASK - ICRL explores and learns patterns:
   
   cd mock_codebase
   icrl chat
   
   Then ask: "Add a GET /orders endpoint that returns a list of 
   orders. Follow the existing patterns in the codebase."
   
   → ICRL will explore users.py, products.py, etc.
   → It will create orders following the patterns
   → Say 'yes' to save the trajectory

2. SECOND TASK - ICRL applies learned patterns:
   
   Ask: "Add a GET /categories endpoint with CRUD operations"
   
   → ICRL retrieves the orders trajectory as an example
   → It immediately applies correct patterns
   → Fewer exploration steps, faster completion

3. ABLATION - See the difference:
   
   icrl chat --no-examples
   
   Ask the same question and compare:
   → Without examples: generic FastAPI patterns
   → With examples: your team's specific patterns

WHAT TO OBSERVE:
─────────────────────────────────────────────────────────────

✓ APIResponse wrapper usage (not raw dicts)
✓ Custom exceptions (NotFoundError, not HTTPException)
✓ Service layer pattern (routes don't contain logic)
✓ Structured logging (logger.info("event", key=value))
✓ Model naming conventions (Create, Update, Out, InDB)

The key insight: After 2-3 successful tasks, ICRL stops
needing to explore your codebase - it already knows your patterns!
""")


def main():
    parser = argparse.ArgumentParser(description="Setup the codebase patterns demo")
    parser.add_argument("--seed", action="store_true", help="Pre-seed with example trajectories")
    parser.add_argument("--clean", action="store_true", help="Remove all demo data")
    args = parser.parse_args()
    
    print("🔧 Setting up Codebase Patterns Demo\n")
    
    # Verify codebase structure
    if not verify_codebase_structure():
        sys.exit(1)
    
    if args.clean:
        clean_demo_data()
        print("\n✅ Demo cleaned. Run without --clean to set up fresh.")
        return
    
    # Create fresh database
    create_fresh_database()
    
    # Optionally seed with examples
    if args.seed:
        seed_example_trajectories()
    
    # Print instructions
    print_demo_instructions()


if __name__ == "__main__":
    main()
