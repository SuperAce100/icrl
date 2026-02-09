#!/usr/bin/env python3
"""Run the Preference Learning demo.

This script demonstrates how ICRL adapts to different user preferences by:
1. Loading user-specific trajectory databases (seeded by setup_demo.py)
2. Running the same test requests through ICRL for each user profile
3. Running requests through vanilla LLM (no preference learning) for comparison
4. Displaying side-by-side comparison of responses

Usage:
    python run_demo.py                    # Run full demo
    python run_demo.py --profile expert   # Run for specific profile only
    python run_demo.py --request 1        # Run specific test request only
    python run_demo.py --no-vanilla       # Skip vanilla comparison
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from icrl.database import TrajectoryDatabase
from icrl.models import Message
from icrl.retriever import TrajectoryRetriever

DEMO_DIR = Path(__file__).parent
SCENARIOS_DIR = DEMO_DIR / "scenarios"
PROFILES_DIR = DEMO_DIR / "user_profiles"
DEMO_DB_BASE = DEMO_DIR / ".demo_trajectories"
RESULTS_DIR = DEMO_DIR / ".demo_results"


def load_user_profiles() -> dict[str, dict]:
    """Load all user profiles."""
    profiles = {}
    for profile_file in PROFILES_DIR.glob("*.json"):
        with open(profile_file) as f:
            profile = json.load(f)
            profiles[profile["profile_id"]] = profile
    return profiles


def load_test_requests() -> list[dict]:
    """Load test requests."""
    test_file = SCENARIOS_DIR / "test_requests.json"
    with open(test_file) as f:
        return json.load(f)


def get_llm_provider():
    """Get the LLM provider for generating responses."""
    # Try to use LiteLLM with a reasonable default
    try:
        from icrl.providers import LiteLLMProvider
        
        # Check for API keys
        model = os.environ.get("ICRL_DEMO_MODEL", "gpt-4o-mini")
        return LiteLLMProvider(model=model)
    except Exception as e:
        print(f"⚠️  Could not initialize LLM provider: {e}")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        sys.exit(1)


def format_examples_for_prompt(examples: list, profile: dict) -> str:
    """Format retrieved examples for inclusion in the prompt."""
    if not examples:
        return "No previous examples available."
    
    formatted = []
    for i, ex in enumerate(examples, 1):
        # Get the trajectory to access metadata
        formatted.append(f"""Example {i}:
Request: {ex.goal}
Response style: {profile['preferences']['verbosity']} verbosity, {profile['preferences']['format']} format
Reasoning: {ex.reasoning}
""")
    
    return "\n".join(formatted)


def build_icrl_prompt(request: str, examples: list, profile: dict) -> str:
    """Build a prompt that incorporates ICRL examples and user preferences."""
    examples_text = format_examples_for_prompt(examples, profile)
    
    # Include style guidance from the profile
    style_guidance = f"""
User Preferences:
- Verbosity: {profile['preferences']['verbosity']}
- Format: {profile['preferences']['format']}
- Explanation depth: {profile['preferences']['explanation_depth']}
- Tone: {profile['preferences']['tone']}
- Examples: {profile['preferences']['examples']}
"""
    
    # Add style markers if available
    if profile.get('style_markers'):
        markers = profile['style_markers']
        if markers.get('max_response_lines'):
            style_guidance += f"- Maximum response lines: {markers['max_response_lines']}\n"
        if markers.get('min_response_lines'):
            style_guidance += f"- Minimum response lines: {markers['min_response_lines']}\n"
        if markers.get('prefers_commands'):
            style_guidance += "- User prefers direct commands over explanations\n"
        if markers.get('wants_warnings'):
            style_guidance += "- Include relevant warnings and caveats\n"
        if markers.get('wants_business_impact'):
            style_guidance += "- Focus on business impact and risk assessment\n"
    
    prompt = f"""You are a helpful assistant that adapts to user preferences.

{style_guidance}

Here are examples of how this user prefers responses:

{examples_text}

Based on these examples and preferences, respond to the following request in the user's preferred style:

Request: {request}

Response:"""
    
    return prompt


def build_vanilla_prompt(request: str) -> str:
    """Build a vanilla prompt without any preference learning."""
    return f"""You are a helpful assistant. Please respond to the following request:

Request: {request}

Response:"""


async def generate_response(llm, prompt: str) -> str:
    """Generate a response using the LLM."""
    messages = [Message(role="user", content=prompt)]
    return await llm.complete(messages)


async def run_icrl_for_profile(
    llm,
    profile: dict,
    test_requests: list[dict],
    k: int = 3,
) -> list[dict]:
    """Run ICRL for a specific user profile."""
    profile_id = profile["profile_id"]
    db_path = DEMO_DB_BASE / profile_id
    
    if not db_path.exists():
        print(f"❌ Database not found for profile: {profile_id}")
        print("   Run setup_demo.py first")
        return []
    
    db = TrajectoryDatabase(str(db_path))
    retriever = TrajectoryRetriever(db, k=k)
    
    results = []
    for request in test_requests:
        # Retrieve relevant examples
        examples = retriever.retrieve_for_plan(request["request"], k=k)
        
        # Build prompt with examples
        prompt = build_icrl_prompt(request["request"], examples, profile)
        
        # Generate response
        response = await generate_response(llm, prompt)
        
        results.append({
            "request_id": request["id"],
            "request": request["request"],
            "profile_id": profile_id,
            "response": response,
            "num_examples_used": len(examples),
            "method": "icrl",
        })
    
    return results


async def run_vanilla(llm, test_requests: list[dict]) -> list[dict]:
    """Run vanilla LLM without preference learning."""
    results = []
    for request in test_requests:
        prompt = build_vanilla_prompt(request["request"])
        response = await generate_response(llm, prompt)
        
        results.append({
            "request_id": request["id"],
            "request": request["request"],
            "profile_id": "vanilla",
            "response": response,
            "num_examples_used": 0,
            "method": "vanilla",
        })
    
    return results


def print_comparison(
    request: dict,
    icrl_responses: dict[str, str],
    vanilla_response: str | None,
    profiles: dict[str, dict],
):
    """Print a side-by-side comparison of responses."""
    print("\n" + "=" * 80)
    print(f"📝 REQUEST: {request['request']}")
    print("=" * 80)
    
    for profile_id, response in icrl_responses.items():
        profile = profiles[profile_id]
        print(f"\n🎯 {profile['name'].upper()} (ICRL)")
        print("-" * 40)
        # Truncate long responses for display
        lines = response.split('\n')
        if len(lines) > 20:
            print('\n'.join(lines[:20]))
            print(f"... [{len(lines) - 20} more lines]")
        else:
            print(response)
    
    if vanilla_response:
        print(f"\n⚪ VANILLA (No Preference Learning)")
        print("-" * 40)
        lines = vanilla_response.split('\n')
        if len(lines) > 20:
            print('\n'.join(lines[:20]))
            print(f"... [{len(lines) - 20} more lines]")
        else:
            print(vanilla_response)


def save_results(all_results: list[dict]):
    """Save results to JSON for later evaluation."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_DIR / "demo_results.json"
    
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")


async def main():
    parser = argparse.ArgumentParser(description="Run the Preference Learning demo")
    parser.add_argument(
        "--profile",
        type=str,
        help="Run for specific profile only (expert, learner, manager)",
    )
    parser.add_argument(
        "--request",
        type=int,
        help="Run specific test request only (1-8)",
    )
    parser.add_argument(
        "--no-vanilla",
        action="store_true",
        help="Skip vanilla comparison",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Number of examples to retrieve (default: 3)",
    )
    args = parser.parse_args()
    
    print("🎯 PREFERENCE LEARNING DEMO")
    print("=" * 60)
    print("This demo shows how ICRL adapts to different user preferences.\n")
    
    # Check if setup has been run
    if not DEMO_DB_BASE.exists():
        print("❌ Demo not set up. Run setup_demo.py first:")
        print("   python setup_demo.py")
        sys.exit(1)
    
    # Load data
    profiles = load_user_profiles()
    test_requests = load_test_requests()
    
    # Filter by profile if specified
    if args.profile:
        profile_map = {
            "expert": "expert_terse",
            "learner": "learner_detailed",
            "manager": "manager_summary",
        }
        profile_id = profile_map.get(args.profile, args.profile)
        if profile_id not in profiles:
            print(f"❌ Unknown profile: {args.profile}")
            print(f"   Available: {', '.join(profile_map.keys())}")
            sys.exit(1)
        profiles = {profile_id: profiles[profile_id]}
    
    # Filter by request if specified
    if args.request:
        if args.request < 1 or args.request > len(test_requests):
            print(f"❌ Invalid request number: {args.request}")
            print(f"   Available: 1-{len(test_requests)}")
            sys.exit(1)
        test_requests = [test_requests[args.request - 1]]
    
    print(f"📊 Running {len(test_requests)} test request(s) across {len(profiles)} profile(s)")
    print(f"   Examples per request: {args.k}")
    print()
    
    # Initialize LLM
    llm = get_llm_provider()
    print(f"✅ LLM initialized: {llm._model}")
    
    all_results = []
    
    # Run ICRL for each profile
    for profile_id, profile in profiles.items():
        print(f"\n🔄 Running ICRL for {profile['name']}...")
        results = await run_icrl_for_profile(llm, profile, test_requests, k=args.k)
        all_results.extend(results)
        print(f"   ✅ Generated {len(results)} responses")
    
    # Run vanilla if not skipped
    vanilla_results = {}
    if not args.no_vanilla:
        print(f"\n🔄 Running vanilla (no preference learning)...")
        vanilla_list = await run_vanilla(llm, test_requests)
        for r in vanilla_list:
            vanilla_results[r["request_id"]] = r["response"]
        all_results.extend(vanilla_list)
        print(f"   ✅ Generated {len(vanilla_list)} responses")
    
    # Display comparisons
    print("\n" + "=" * 80)
    print("📊 RESPONSE COMPARISON")
    print("=" * 80)
    
    for request in test_requests:
        icrl_responses = {}
        for result in all_results:
            if result["request_id"] == request["id"] and result["method"] == "icrl":
                icrl_responses[result["profile_id"]] = result["response"]
        
        vanilla_response = vanilla_results.get(request["id"])
        print_comparison(request, icrl_responses, vanilla_response, profiles)
    
    # Save results
    save_results(all_results)
    
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE")
    print("=" * 80)
    print("""
Next steps:
  1. Review the responses above - notice how each profile gets different answers
  2. Run evaluation to score preference matching:
     
     python evaluate_responses.py
     
  3. Try different test requests:
     
     python run_demo.py --request 3
     
  4. Focus on a specific profile:
     
     python run_demo.py --profile expert
""")


if __name__ == "__main__":
    asyncio.run(main())
