#!/usr/bin/env python3
"""Setup script for the Preference Learning demo.

This script prepares the demo environment by:
1. Creating separate trajectory databases for each user profile
2. Seeding each with profile-specific past interactions
3. Verifying the test requests are ready

Usage:
    python setup_demo.py           # Fresh start with seeded interactions
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
PROFILES_DIR = DEMO_DIR / "user_profiles"
DEMO_DB_BASE = DEMO_DIR / ".demo_trajectories"


def clean_demo_data():
    """Remove all demo trajectory data."""
    if DEMO_DB_BASE.exists():
        shutil.rmtree(DEMO_DB_BASE)
        print(f"✅ Removed demo databases: {DEMO_DB_BASE}")
    else:
        print("ℹ️  No demo databases to clean")


def create_fresh_databases():
    """Create fresh trajectory databases for each user profile."""
    clean_demo_data()
    
    # Create a database for each profile
    for profile_file in PROFILES_DIR.glob("*.json"):
        profile_id = profile_file.stem
        db_path = DEMO_DB_BASE / profile_id
        db_path.mkdir(parents=True, exist_ok=True)
        (db_path / "trajectories").mkdir(exist_ok=True)
        print(f"✅ Created database for profile: {profile_id}")


def load_user_profiles() -> dict[str, dict]:
    """Load all user profiles."""
    profiles = {}
    for profile_file in PROFILES_DIR.glob("*.json"):
        with open(profile_file) as f:
            profile = json.load(f)
            profiles[profile["profile_id"]] = profile
    return profiles


def load_seed_interactions() -> list[dict]:
    """Load seed interactions from JSON file."""
    seed_file = SCENARIOS_DIR / "seed_interactions.json"
    if not seed_file.exists():
        print(f"❌ Seed interactions file not found: {seed_file}")
        sys.exit(1)
    
    with open(seed_file) as f:
        return json.load(f)


def interaction_to_trajectory(interaction: dict, profile: dict):
    """Convert a user interaction to an ICRL trajectory."""
    from icrl.models import Trajectory, Step
    
    # Create a trajectory that represents this interaction style
    trajectory = Trajectory(
        goal=interaction["request"],
        plan=f"Respond in {profile['name']} style: {profile['preferences']['verbosity']} verbosity, {profile['preferences']['format']} format",
        steps=[
            Step(
                observation=f"User request: {interaction['request']}",
                reasoning=interaction["reasoning"],
                action="Generate response matching user preferences"
            ),
        ],
        success=True,
        metadata={
            "interaction_id": interaction["id"],
            "profile_id": interaction["profile"],
            "profile_name": profile["name"],
            "final_response": interaction["response"],
            "preferences": profile["preferences"],
            "style_markers": profile.get("style_markers", {}),
        }
    )
    
    return trajectory


def seed_trajectories():
    """Seed each profile's database with their interactions."""
    from icrl.database import TrajectoryDatabase
    
    profiles = load_user_profiles()
    interactions = load_seed_interactions()
    
    # Group interactions by profile
    interactions_by_profile: dict[str, list] = {}
    for interaction in interactions:
        profile_id = interaction["profile"]
        if profile_id not in interactions_by_profile:
            interactions_by_profile[profile_id] = []
        interactions_by_profile[profile_id].append(interaction)
    
    print(f"\n📦 Seeding trajectories for {len(profiles)} user profiles...")
    
    for profile_id, profile in profiles.items():
        db_path = DEMO_DB_BASE / profile_id
        db = TrajectoryDatabase(str(db_path))
        
        profile_interactions = interactions_by_profile.get(profile_id, [])
        
        for interaction in profile_interactions:
            trajectory = interaction_to_trajectory(interaction, profile)
            db.add(trajectory)
        
        print(f"  ✅ {profile['name']}: {len(profile_interactions)} interactions seeded")
    
    return len(interactions)


def verify_test_requests() -> bool:
    """Verify test requests are ready."""
    test_file = SCENARIOS_DIR / "test_requests.json"
    if not test_file.exists():
        print(f"❌ Test requests file not found: {test_file}")
        return False
    
    with open(test_file) as f:
        test_requests = json.load(f)
    
    print(f"✅ Found {len(test_requests)} test requests")
    return True


def print_demo_instructions():
    """Print instructions for running the demo."""
    profiles = load_user_profiles()
    
    print("\n" + "=" * 60)
    print("🎯 PREFERENCE LEARNING DEMO READY")
    print("=" * 60)
    print(f"""
This demo shows how ICRL adapts to different user preferences
by learning from past interactions.

USER PROFILES CONFIGURED:
─────────────────────────────────────────────────────────────""")
    
    for profile_id, profile in profiles.items():
        print(f"  • {profile['name']}: {profile['description'][:50]}...")
    
    print("""
WHAT'S BEEN SET UP:
─────────────────────────────────────────────────────────────
• Separate trajectory database for each user profile
• Each database seeded with 5 past interactions
• Interactions reflect each user's preferred style

RUN THE DEMO:
─────────────────────────────────────────────────────────────

  python run_demo.py

This will:
1. Run each test request through ICRL for each user profile
2. Run each request through vanilla (no preference learning)
3. Compare how well responses match user preferences

WHAT TO OBSERVE:
─────────────────────────────────────────────────────────────
• Same question → different answers for different users
• Expert gets terse commands
• Learner gets detailed explanations
• Manager gets high-level overviews
• Vanilla gives everyone the same generic response

Example - "How do I squash commits?"

  Expert:     git rebase -i HEAD~3
  
  Learner:    ## What is Squashing?
              Squashing combines multiple commits...
              [20+ lines of explanation]
  
  Manager:    **Impact**: Cleaner git history
              **Risk**: Low for local branches
              **Who**: Developer who owns the branch
""")


def main():
    parser = argparse.ArgumentParser(description="Setup the Preference Learning demo")
    parser.add_argument("--clean", action="store_true", help="Remove all demo data")
    args = parser.parse_args()
    
    print("🔧 Setting up Preference Learning Demo\n")
    
    if args.clean:
        clean_demo_data()
        print("\n✅ Demo cleaned. Run without --clean to set up fresh.")
        return
    
    # Create fresh databases
    create_fresh_databases()
    
    # Seed with past interactions
    seed_trajectories()
    
    # Verify test requests
    if not verify_test_requests():
        sys.exit(1)
    
    # Print instructions
    print_demo_instructions()


if __name__ == "__main__":
    main()
