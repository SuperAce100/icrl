#!/usr/bin/env python3
"""Setup script for the IT Support demo.

This script prepares the demo environment by:
1. Creating a fresh trajectory database for the demo
2. Seeding it with past resolved support tickets as trajectories
3. Verifying the test scenarios are ready

Usage:
    python setup_demo.py           # Fresh start with seeded tickets
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


def load_seed_tickets() -> list[dict]:
    """Load seed tickets from JSON file."""
    seed_file = SCENARIOS_DIR / "seed_tickets.json"
    if not seed_file.exists():
        print(f"❌ Seed tickets file not found: {seed_file}")
        sys.exit(1)
    
    with open(seed_file) as f:
        return json.load(f)


def ticket_to_trajectory(ticket: dict):
    """Convert a support ticket to an ICRL trajectory."""
    from icrl.models import Trajectory, Step
    
    # Create a trajectory that represents resolving this ticket
    trajectory = Trajectory(
        goal=f"IT Support Request: {ticket['title']}\n\nUser reported: {ticket['issue']}",
        plan=f"""1. Analyze the reported issue
2. Identify the root cause based on symptoms
3. Provide step-by-step resolution
4. Document the solution for future reference""",
        steps=[
            Step(
                observation=f"User reports: {ticket['issue']}",
                reasoning=f"Based on the symptoms described, this appears to be related to: {ticket['root_cause']}",
                action="Investigate the specific issue"
            ),
            Step(
                observation=f"Identified root cause: {ticket['root_cause']}",
                reasoning="This is a known issue with a documented solution. Applying the standard fix.",
                action="Apply resolution steps"
            ),
            Step(
                observation="Resolution steps applied successfully",
                reasoning="The issue has been resolved. Documenting for future reference.",
                action="Confirm resolution with user"
            ),
        ],
        success=True,
        metadata={
            "ticket_id": ticket["id"],
            "category": ticket["category"],
            "resolution_time_minutes": ticket["resolution_time_minutes"],
            "frequency": ticket["frequency"],
            "root_cause": ticket["root_cause"],
            "final_response": ticket["resolution"],
        }
    )
    
    return trajectory


def seed_trajectories():
    """Seed the database with trajectories from past tickets."""
    from icrl.database import TrajectoryDatabase
    
    db = TrajectoryDatabase(str(DEMO_DB_PATH))
    tickets = load_seed_tickets()
    
    print(f"\n📦 Seeding {len(tickets)} support ticket trajectories...")
    
    for ticket in tickets:
        trajectory = ticket_to_trajectory(ticket)
        db.add(trajectory)
        print(f"  ✅ {ticket['id']}: {ticket['title'][:50]}...")
    
    print(f"\n✅ Seeded {len(tickets)} trajectories into database")
    return len(tickets)


def verify_test_scenarios() -> bool:
    """Verify test scenarios are ready."""
    test_file = SCENARIOS_DIR / "test_tickets.json"
    if not test_file.exists():
        print(f"❌ Test tickets file not found: {test_file}")
        return False
    
    with open(test_file) as f:
        test_tickets = json.load(f)
    
    print(f"✅ Found {len(test_tickets)} test scenarios")
    return True


def print_demo_instructions():
    """Print instructions for running the demo."""
    print("\n" + "=" * 60)
    print("🎯 IT SUPPORT DEMO READY")
    print("=" * 60)
    print("""
This demo compares ICRL (with learned support knowledge) vs
vanilla Claude (no examples) for IT support tasks.

WHAT'S BEEN SET UP:
─────────────────────────────────────────────────────────────
• Trajectory database seeded with 10 past resolved tickets
• Each ticket includes: issue, resolution, root cause
• Test scenarios ready for comparison

RUN THE DEMO:
─────────────────────────────────────────────────────────────

  python run_demo.py

This will:
1. Run each test ticket through ICRL (with examples)
2. Run each test ticket through vanilla (no examples)
3. Compare and score the responses

WHAT TO OBSERVE:
─────────────────────────────────────────────────────────────
• ICRL should identify root causes immediately
• ICRL should provide specific, actionable fixes
• Vanilla will likely give generic troubleshooting advice

Example:
  Issue: "VPN won't connect after Mac update"
  
  ICRL: "This is the macOS Sonoma IPv6 bug. Disable IPv6 in
         Network preferences and reconnect."
  
  Vanilla: "Try reinstalling GlobalProtect, check your
            credentials, or contact IT support."
""")


def main():
    parser = argparse.ArgumentParser(description="Setup the IT Support demo")
    parser.add_argument("--clean", action="store_true", help="Remove all demo data")
    args = parser.parse_args()
    
    print("🔧 Setting up IT Support Demo\n")
    
    if args.clean:
        clean_demo_data()
        print("\n✅ Demo cleaned. Run without --clean to set up fresh.")
        return
    
    # Create fresh database
    create_fresh_database()
    
    # Seed with past tickets
    seed_trajectories()
    
    # Verify test scenarios
    if not verify_test_scenarios():
        sys.exit(1)
    
    # Print instructions
    print_demo_instructions()


if __name__ == "__main__":
    main()
