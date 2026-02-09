#!/usr/bin/env python3
"""Setup script for the Exception Handling demo.

This script prepares the demo environment by:
1. Creating a fresh trajectory database for the demo
2. Seeding it with past exception-handling decisions as trajectories
3. Verifying the test scenarios are ready

Usage:
    python setup_demo.py           # Fresh start with seeded decisions
    python setup_demo.py --clean   # Remove all demo data
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


DEMO_DIR = Path(__file__).parent
SCENARIOS_DIR = DEMO_DIR / "scenarios"
DEMO_DB_PATH = DEMO_DIR / ".demo_trajectories"


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


def load_seed_decisions() -> list[dict]:
    """Load seed decisions from JSON file."""
    seed_file = SCENARIOS_DIR / "seed_decisions.json"
    if not seed_file.exists():
        print(f"❌ Seed decisions file not found: {seed_file}")
        sys.exit(1)
    
    with open(seed_file) as f:
        return json.load(f)


def decision_to_trajectory(decision: dict):
    """Convert an exception-handling decision to an ICRL trajectory."""
    from icrl.models import Trajectory, Step
    
    # Create a trajectory that represents handling this exception
    trajectory = Trajectory(
        goal=f"Exception Handling Request: {decision['title']}\n\nSituation: {decision['situation']}",
        plan=f"""1. Analyze the situation and identify key factors
2. Consider relevant policies and precedents
3. Determine the appropriate action
4. Identify if escalation is needed
5. Execute the decision and document reasoning""",
        steps=[
            Step(
                observation=f"Situation: {decision['situation']}",
                reasoning=f"Key factors to consider: {', '.join(decision['key_factors'])}",
                action="Analyze against policies and precedents"
            ),
            Step(
                observation=f"Policy would suggest a rigid response, but this situation has nuances",
                reasoning=decision["reasoning"],
                action="Determine appropriate exception handling"
            ),
            Step(
                observation=f"Decision made: {decision['decision'][:100]}...",
                reasoning=f"Escalation path: {decision['escalation']}",
                action="Execute decision and document"
            ),
        ],
        success=True,
        metadata={
            "case_id": decision["id"],
            "category": decision["category"],
            "key_factors": decision["key_factors"],
            "escalation": decision["escalation"],
            "outcome": decision["outcome"],
            "final_response": decision["decision"],
            "reasoning": decision["reasoning"],
        }
    )
    
    return trajectory


def seed_trajectories():
    """Seed the database with trajectories from past decisions."""
    from icrl.database import TrajectoryDatabase
    
    db = TrajectoryDatabase(str(DEMO_DB_PATH))
    decisions = load_seed_decisions()
    
    print(f"\n📦 Seeding {len(decisions)} exception-handling precedents...")
    
    for decision in decisions:
        trajectory = decision_to_trajectory(decision)
        db.add(trajectory)
        print(f"  ✅ {decision['id']}: {decision['title'][:50]}...")
    
    print(f"\n✅ Seeded {len(decisions)} precedents into database")
    return len(decisions)


def verify_test_scenarios() -> bool:
    """Verify test scenarios are ready."""
    test_file = SCENARIOS_DIR / "test_scenarios.json"
    if not test_file.exists():
        print(f"❌ Test scenarios file not found: {test_file}")
        return False
    
    with open(test_file) as f:
        test_scenarios = json.load(f)
    
    print(f"✅ Found {len(test_scenarios)} test scenarios")
    return True


def print_demo_instructions():
    """Print instructions for running the demo."""
    print("\n" + "=" * 60)
    print("🎯 EXCEPTION HANDLING DEMO READY")
    print("=" * 60)
    print("""
This demo compares ICRL (with learned precedents) vs vanilla 
Claude (policy-only) for exception handling decisions.

WHAT'S BEEN SET UP:
─────────────────────────────────────────────────────────────
• Trajectory database seeded with 10 past decisions
• Each decision includes: situation, action, reasoning, outcome
• Test scenarios ready for comparison

RUN THE DEMO:
─────────────────────────────────────────────────────────────

  python run_demo.py

This will:
1. Run each scenario through ICRL (with precedents)
2. Run each scenario through vanilla (policy-only)
3. Compare and score the responses

WHAT TO OBSERVE:
─────────────────────────────────────────────────────────────
• ICRL should match precedent-based decisions
• ICRL should know when to escalate and to whom
• Vanilla will likely apply rigid policy interpretations

Example:
  Situation: "Loyal 3-year customer wants refund after 45 days"
  
  ICRL: "Approve as goodwill gesture - customer LTV of $7k+ 
         far exceeds the refund amount. Document as one-time
         courtesy."
  
  Vanilla: "Deny - policy clearly states 30-day refund window
            with no exceptions."
""")


def main():
    parser = argparse.ArgumentParser(description="Setup the Exception Handling demo")
    parser.add_argument("--clean", action="store_true", help="Remove all demo data")
    args = parser.parse_args()
    
    print("🔧 Setting up Exception Handling Demo\n")
    
    if args.clean:
        clean_demo_data()
        print("\n✅ Demo cleaned. Run without --clean to set up fresh.")
        return
    
    # Create fresh database
    create_fresh_database()
    
    # Seed with past decisions
    seed_trajectories()
    
    # Verify test scenarios
    if not verify_test_scenarios():
        sys.exit(1)
    
    # Print instructions
    print_demo_instructions()


if __name__ == "__main__":
    main()
