#!/usr/bin/env python3
"""Ablation test comparing ICRL with examples vs vanilla (no examples).

This test is designed to show the difference more clearly by:
1. Using a more ambiguous prompt that doesn't explicitly mention patterns
2. Limiting the exploration steps
3. Comparing the number of steps taken and pattern compliance

Usage:
    python run_ablation_test.py
"""

import asyncio
import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

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
    for f in ["orders.py", "categories.py", "reviews.py", "inventory.py"]:
        path = MOCK_CODEBASE / "app" / "routes" / f
        if path.exists():
            path.unlink()
        # Also remove models and services
        for subdir in ["models", "services"]:
            model_path = MOCK_CODEBASE / "app" / subdir / f.replace(".py", ".py")
            if model_path.exists():
                model_path.unlink()
    
    print("✅ Demo environment ready")


def seed_rich_trajectory():
    """Seed the database with a rich trajectory that includes corrections."""
    from icrl.database import TrajectoryDatabase
    from icrl.models import Trajectory, Step
    
    db = TrajectoryDatabase(str(DEMO_DB_PATH))
    
    # Create a trajectory that shows the learning process with corrections
    trajectory = Trajectory(
        goal="Add a reviews endpoint for product reviews",
        plan="""1. Create review models following the existing pattern
2. Create ReviewService with business logic
3. Create reviews.py route with CRUD operations
4. Use APIResponse wrapper, structured logging, and service layer""",
        steps=[
            Step(
                observation="Looking at the codebase structure",
                reasoning="I need to understand the patterns used in this codebase before creating new code.",
                action="Read app/routes/users.py and app/routes/products.py"
            ),
            Step(
                observation="Found consistent patterns: APIResponse wrapper, service layer, structured logging with key=value, custom exceptions",
                reasoning="I should follow these patterns exactly. Key things: 1) Import APIResponse from app.core.response 2) Use response_model=APIResponse[T] 3) Delegate to service 4) Use logger.info('event', key=value) format",
                action="Create app/models/review.py with ReviewCreate, ReviewUpdate, ReviewOut, ReviewInDB"
            ),
            Step(
                observation="Created review models",
                reasoning="Now I need to create the service layer. Looking at user_service.py, it uses structured logging and raises custom exceptions like NotFoundError.",
                action="Create app/services/review_service.py with ReviewService"
            ),
            Step(
                observation="Created ReviewService with list, get_by_id, create, update, delete methods",
                reasoning="Now create the route file. Must use: 1) APIResponse.success() 2) response_model=APIResponse[T] 3) logger.info('event', key=value) 4) Service delegation",
                action="Create app/routes/reviews.py following the exact pattern"
            ),
        ],
        success=True,
        metadata={
            "demo": True,
            "patterns_learned": [
                "APIResponse wrapper from app.core.response",
                "response_model=APIResponse[T] on all endpoints",
                "Structured logging: logger.info('event', key=value)",
                "Service layer delegation",
                "Custom exceptions (NotFoundError, ConflictError)",
            ],
            "final_response": """Created reviews endpoint following ACME API patterns:
- app/models/review.py with ReviewCreate, ReviewUpdate, ReviewOut, ReviewInDB
- app/services/review_service.py with ReviewService class
- app/routes/reviews.py with full CRUD operations

All endpoints use APIResponse wrapper, structured logging, and delegate to service layer."""
        }
    )
    
    db.add(trajectory)
    print(f"✅ Seeded rich trajectory: {trajectory.id}")
    return trajectory.id


async def run_icrl_task(goal: str, with_examples: bool = True, max_steps: int = 20) -> dict:
    """Run an ICRL task and return metrics.
    
    Args:
        goal: The task goal
        with_examples: Whether to use example retrieval
        max_steps: Maximum steps allowed
        
    Returns:
        Dict with trajectory info and metrics
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
        max_steps=max_steps,
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
    start_time = datetime.now()
    trajectory = await loop.run(goal, examples=examples if examples else None)
    end_time = datetime.now()
    
    # Count steps
    num_steps = len(trajectory.steps)
    
    # Save trajectory if successful
    if trajectory.success and with_examples:
        db.add(trajectory)
        print(f"  💾 Saved trajectory: {trajectory.id}")
    
    return {
        "trajectory": trajectory,
        "num_steps": num_steps,
        "success": trajectory.success,
        "duration": (end_time - start_time).total_seconds(),
        "with_examples": with_examples,
    }


def validate_file(filepath: Path) -> dict:
    """Validate a file and return results."""
    if not filepath.exists():
        return {
            "exists": False,
            "score": 0,
            "passes": [],
            "issues": ["File not generated"],
        }
    
    checker = PatternChecker(filepath)
    checker.check_all()
    
    score = len(checker.passes) / (len(checker.passes) + len(checker.issues)) * 100
    return {
        "exists": True,
        "score": score,
        "passes": checker.passes,
        "issues": checker.issues,
    }


async def main():
    print("🎯 ICRL Ablation Test - ICRL vs Vanilla Comparison")
    print("=" * 60)
    print()
    
    # Setup
    setup_demo()
    
    # Seed with an example trajectory
    print("\n📦 Seeding example trajectory...")
    seed_rich_trajectory()
    
    # Use a more ambiguous prompt that doesn't explicitly mention patterns
    ambiguous_goal = """Add an inventory endpoint for tracking product inventory.
It should support listing inventory items and updating stock levels."""
    
    results = {}
    
    # Task 1: ICRL with examples
    print("\n" + "-" * 60)
    print("🚀 Task 1: Generate inventory endpoint WITH examples")
    print("-" * 60)
    
    try:
        icrl_result = await run_icrl_task(ambiguous_goal, with_examples=True, max_steps=25)
        print(f"  ✅ ICRL task completed in {icrl_result['num_steps']} steps ({icrl_result['duration']:.1f}s)")
        results["icrl"] = icrl_result
    except Exception as e:
        print(f"  ❌ ICRL task failed: {e}")
        import traceback
        traceback.print_exc()
        results["icrl"] = {"success": False, "num_steps": 0, "duration": 0}
    
    # Clean up generated files for vanilla test
    for f in ["inventory.py"]:
        for subdir in ["routes", "models", "services"]:
            path = MOCK_CODEBASE / "app" / subdir / f
            if path.exists():
                # Rename to keep for comparison
                path.rename(path.with_suffix(".py.icrl"))
    
    # Task 2: Vanilla (no examples)
    print("\n" + "-" * 60)
    print("🚀 Task 2: Generate inventory endpoint WITHOUT examples (vanilla)")
    print("-" * 60)
    
    try:
        vanilla_result = await run_icrl_task(ambiguous_goal, with_examples=False, max_steps=25)
        print(f"  ✅ Vanilla task completed in {vanilla_result['num_steps']} steps ({vanilla_result['duration']:.1f}s)")
        results["vanilla"] = vanilla_result
    except Exception as e:
        print(f"  ❌ Vanilla task failed: {e}")
        import traceback
        traceback.print_exc()
        results["vanilla"] = {"success": False, "num_steps": 0, "duration": 0}
    
    # Rename files for comparison
    icrl_file = MOCK_CODEBASE / "app" / "routes" / "inventory.py.icrl"
    vanilla_file = MOCK_CODEBASE / "app" / "routes" / "inventory.py"
    
    # Validate both
    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)
    
    for label, filepath in [("ICRL (with examples)", icrl_file), ("Vanilla (no examples)", vanilla_file)]:
        print(f"\n{label}:")
        print("-" * 40)
        
        validation = validate_file(filepath)
        
        if not validation["exists"]:
            print(f"  ❌ File not generated")
            continue
        
        for p in validation["passes"]:
            print(f"  {p}")
        for i in validation["issues"]:
            print(f"  {i}")
        print(f"\n  Pattern Score: {validation['score']:.0f}%")
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 COMPARISON SUMMARY")
    print("=" * 60)
    
    icrl_validation = validate_file(icrl_file)
    vanilla_validation = validate_file(vanilla_file)
    
    icrl_score = icrl_validation.get("score", 0)
    vanilla_score = vanilla_validation.get("score", 0)
    
    icrl_steps = results.get("icrl", {}).get("num_steps", 0)
    vanilla_steps = results.get("vanilla", {}).get("num_steps", 0)
    
    icrl_time = results.get("icrl", {}).get("duration", 0)
    vanilla_time = results.get("vanilla", {}).get("duration", 0)
    
    print(f"\n  Metric                    ICRL        Vanilla     Difference")
    print(f"  ─────────────────────────────────────────────────────────────")
    print(f"  Pattern Score             {icrl_score:>5.0f}%      {vanilla_score:>5.0f}%      {icrl_score - vanilla_score:>+5.0f}%")
    print(f"  Steps Taken               {icrl_steps:>5}       {vanilla_steps:>5}       {icrl_steps - vanilla_steps:>+5}")
    print(f"  Duration (seconds)        {icrl_time:>5.1f}       {vanilla_time:>5.1f}       {icrl_time - vanilla_time:>+5.1f}")
    
    print("\n  Analysis:")
    if icrl_score > vanilla_score:
        print("  ✅ ICRL with examples produces better pattern compliance!")
    elif icrl_score == vanilla_score:
        if icrl_steps < vanilla_steps:
            print("  ✅ Same quality, but ICRL was more efficient (fewer steps)!")
        else:
            print("  ⚠️  Both approaches produced similar results")
    else:
        print("  ❌ Unexpected: vanilla performed better (check the setup)")
    
    print("\n" + "=" * 60)
    print("🏁 Ablation Test Complete!")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    results = asyncio.run(main())
