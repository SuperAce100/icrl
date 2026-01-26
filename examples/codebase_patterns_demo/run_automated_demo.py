#!/usr/bin/env python3
"""Automated demo comparing ICRL with examples vs vanilla (no examples).

This script:
1. Sets up the demo environment
2. Runs ICRL with examples to generate an orders endpoint
3. Runs ICRL without examples (vanilla) to generate a categories endpoint
4. Validates both outputs using the pattern checker
5. Compares the results

Usage:
    python run_automated_demo.py
"""

import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from validate_patterns import PatternChecker


DEMO_DIR = Path(__file__).parent
MOCK_CODEBASE = DEMO_DIR / "mock_codebase"
DEMO_DB_PATH = DEMO_DIR / ".demo_trajectories"


def setup_demo():
    """Set up the demo environment."""
    print("🔧 Setting up demo environment...")
    
    # Clean and recreate demo database
    if DEMO_DB_PATH.exists():
        shutil.rmtree(DEMO_DB_PATH)
    DEMO_DB_PATH.mkdir(parents=True, exist_ok=True)
    (DEMO_DB_PATH / "trajectories").mkdir(exist_ok=True)
    
    # Remove any previously generated files
    for f in ["orders.py", "categories.py", "orders_vanilla.py", "categories_vanilla.py"]:
        path = MOCK_CODEBASE / "app" / "routes" / f
        if path.exists():
            path.unlink()
    
    print("✅ Demo environment ready")


def seed_example_trajectory():
    """Seed the database with an example trajectory for products."""
    from icrl.database import TrajectoryDatabase
    from icrl.models import Trajectory, Step
    
    db = TrajectoryDatabase(str(DEMO_DB_PATH))
    
    # Create a trajectory that demonstrates the correct patterns
    trajectory = Trajectory(
        goal="Add a GET /products endpoint that returns a list of products. Follow the existing patterns in the codebase.",
        plan="""1. Explore the existing codebase structure to understand patterns
2. Look at users.py route as a reference for the pattern
3. Create ProductInDB, ProductCreate, ProductUpdate, ProductOut models
4. Create ProductService with list() method
5. Create products.py route following the users.py pattern
6. Register the router in main.py""",
        steps=[
            Step(
                observation="Found app/routes/users.py with APIResponse pattern",
                reasoning="The codebase uses a consistent pattern: routes return APIResponse[T], delegate to services, use custom exceptions.",
                action="Read app/routes/users.py to understand the exact pattern"
            ),
            Step(
                observation="users.py shows: Import APIResponse from app.core.response, use response_model=APIResponse[T], call service methods, return APIResponse.success()",
                reasoning="I need to create the same structure for products: models, service, route with APIResponse wrapper.",
                action="Create app/routes/products.py following users.py pattern exactly"
            ),
        ],
        success=True,
        metadata={
            "demo": True,
            "final_response": "Created products endpoint following the ACME API patterns with APIResponse wrapper, service layer, and structured logging."
        }
    )
    
    db.add(trajectory)
    print(f"✅ Seeded example trajectory: {trajectory.id}")
    return trajectory.id


async def run_icrl_task(goal: str, with_examples: bool = True) -> str:
    """Run an ICRL task and return the generated code.
    
    Args:
        goal: The task goal
        with_examples: Whether to use example retrieval
        
    Returns:
        The generated route file content
    """
    from icrl.cli.config import Config
    from icrl.cli.providers import AnthropicVertexToolProvider
    from icrl.cli.tools.base import create_default_registry
    from icrl.cli.tool_loop import ToolLoop
    from icrl.cli.prompts import SYSTEM_PROMPT
    from icrl.database import TrajectoryDatabase
    
    config = Config.load()
    
    # Override database path for demo
    db = TrajectoryDatabase(str(DEMO_DB_PATH))
    
    # Create registry
    registry = create_default_registry(
        working_dir=MOCK_CODEBASE,
        ask_user_callback=lambda q, o: "yes",  # Auto-approve
    )
    
    # Create LLM provider
    llm = AnthropicVertexToolProvider(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        registry=registry,
        credentials_path=config.vertex_credentials_path,
        project_id=config.vertex_project_id,
        location=config.vertex_location,
    )
    
    # Create tool loop
    loop = ToolLoop(
        llm=llm,
        registry=registry,
        system_prompt=SYSTEM_PROMPT,
        max_steps=30,
    )
    
    # Get examples if enabled
    examples = []
    if with_examples and len(db) > 0:
        similar = db.search(goal, k=3)
        examples = [traj.to_example_string() for traj in similar]
        print(f"  📚 Retrieved {len(examples)} example(s)")
    else:
        print("  📚 No examples (vanilla mode)")
    
    # Run the task
    trajectory = await loop.run(goal, examples=examples if examples else None)
    
    # Save trajectory if successful
    if trajectory.success and with_examples:
        db.add(trajectory)
        print(f"  💾 Saved trajectory: {trajectory.id}")
    
    return trajectory


def validate_and_compare(icrl_file: Path, vanilla_file: Path):
    """Validate both files and compare results."""
    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)
    
    results = {}
    
    for label, filepath in [("ICRL (with examples)", icrl_file), ("Vanilla (no examples)", vanilla_file)]:
        print(f"\n{label}:")
        print("-" * 40)
        
        if not filepath.exists():
            print(f"  ❌ File not generated: {filepath.name}")
            results[label] = {"score": 0, "passes": 0, "issues": 0}
            continue
        
        checker = PatternChecker(filepath)
        passed = checker.check_all()
        
        score = len(checker.passes) / (len(checker.passes) + len(checker.issues)) * 100
        results[label] = {
            "score": score,
            "passes": len(checker.passes),
            "issues": len(checker.issues),
            "pass_list": checker.passes,
            "issue_list": checker.issues,
        }
        
        for p in checker.passes:
            print(f"  {p}")
        for i in checker.issues:
            print(f"  {i}")
        print(f"\n  Pattern Score: {score:.0f}%")
    
    # Summary comparison
    print("\n" + "=" * 60)
    print("📈 COMPARISON SUMMARY")
    print("=" * 60)
    
    icrl_score = results.get("ICRL (with examples)", {}).get("score", 0)
    vanilla_score = results.get("Vanilla (no examples)", {}).get("score", 0)
    
    print(f"\n  ICRL (with examples):    {icrl_score:.0f}%")
    print(f"  Vanilla (no examples):   {vanilla_score:.0f}%")
    print(f"  Difference:              {icrl_score - vanilla_score:+.0f}%")
    
    if icrl_score > vanilla_score:
        print("\n  ✅ ICRL with examples produces better pattern compliance!")
    elif icrl_score == vanilla_score:
        print("\n  ⚠️  Both approaches produced similar results")
    else:
        print("\n  ❌ Unexpected: vanilla performed better (check the setup)")
    
    return results


async def main():
    print("🎯 ICRL Codebase Patterns Demo - Automated Comparison")
    print("=" * 60)
    print()
    
    # Setup
    setup_demo()
    
    # Seed with an example trajectory
    print("\n📦 Seeding example trajectory...")
    seed_example_trajectory()
    
    # Task 1: ICRL with examples - generate orders endpoint
    print("\n" + "-" * 60)
    print("🚀 Task 1: Generate orders endpoint WITH examples")
    print("-" * 60)
    
    orders_goal = """Add a GET /orders endpoint that returns a list of orders.
Follow the existing patterns in the codebase exactly.
Create:
1. app/models/order.py with OrderCreate, OrderUpdate, OrderOut, OrderInDB
2. app/services/order_service.py with OrderService
3. app/routes/orders.py following the users.py pattern exactly

Use APIResponse wrapper, structured logging, and service layer pattern."""
    
    try:
        icrl_trajectory = await run_icrl_task(orders_goal, with_examples=True)
        print(f"  ✅ ICRL task completed (success={icrl_trajectory.success})")
    except Exception as e:
        print(f"  ❌ ICRL task failed: {e}")
        icrl_trajectory = None
    
    # Task 2: Vanilla (no examples) - generate categories endpoint
    print("\n" + "-" * 60)
    print("🚀 Task 2: Generate categories endpoint WITHOUT examples (vanilla)")
    print("-" * 60)
    
    categories_goal = """Add a GET /categories endpoint that returns a list of categories.
Create:
1. app/models/category.py with CategoryCreate, CategoryUpdate, CategoryOut
2. app/services/category_service.py with CategoryService  
3. app/routes/categories.py with CRUD operations

Make it consistent with the rest of the codebase."""
    
    try:
        vanilla_trajectory = await run_icrl_task(categories_goal, with_examples=False)
        print(f"  ✅ Vanilla task completed (success={vanilla_trajectory.success})")
    except Exception as e:
        print(f"  ❌ Vanilla task failed: {e}")
        vanilla_trajectory = None
    
    # Validate and compare
    orders_file = MOCK_CODEBASE / "app" / "routes" / "orders.py"
    categories_file = MOCK_CODEBASE / "app" / "routes" / "categories.py"
    
    results = validate_and_compare(orders_file, categories_file)
    
    print("\n" + "=" * 60)
    print("🏁 Demo Complete!")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    results = asyncio.run(main())
