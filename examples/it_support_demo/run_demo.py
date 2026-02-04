#!/usr/bin/env python3
"""Run the IT Support demo comparing ICRL vs vanilla responses.

This script:
1. Loads test tickets
2. Runs each through ICRL (with examples from past tickets)
3. Runs each through vanilla (no examples)
4. Evaluates and compares the responses

Usage:
    python run_demo.py              # Run full comparison
    python run_demo.py --quick      # Run only 3 test cases
    python run_demo.py --verbose    # Show full responses
"""

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


DEMO_DIR = Path(__file__).parent
SCENARIOS_DIR = DEMO_DIR / "scenarios"
DEMO_DB_PATH = DEMO_DIR / ".demo_trajectories"
KNOWLEDGE_BASE = DEMO_DIR / "knowledge_base" / "official_docs.md"


@dataclass
class TestResult:
    """Result from a single test."""
    ticket_id: str
    mode: str  # "icrl" or "vanilla"
    response: str
    duration: float
    keywords_found: list[str]
    keywords_missing: list[str]
    score: float


def load_test_tickets() -> list[dict]:
    """Load test tickets from JSON file."""
    test_file = SCENARIOS_DIR / "test_tickets.json"
    with open(test_file) as f:
        return json.load(f)


def load_knowledge_base() -> str:
    """Load the official (incomplete) documentation."""
    if KNOWLEDGE_BASE.exists():
        return KNOWLEDGE_BASE.read_text()
    return ""


async def get_support_response(
    issue: str,
    with_examples: bool = True,
    knowledge_base: str = "",
) -> tuple[str, float]:
    """Get a support response for an issue.
    
    Args:
        issue: The user's reported issue
        with_examples: Whether to use ICRL examples
        knowledge_base: Official documentation to include
        
    Returns:
        Tuple of (response text, duration in seconds)
    """
    from icrl.cli.config import Config
    from icrl.cli.providers import AnthropicVertexToolProvider
    from icrl.database import TrajectoryDatabase
    
    config = Config.load()
    
    # Create LLM provider
    llm = AnthropicVertexToolProvider(
        model=config.model,
        temperature=0.3,
        max_tokens=1024,
        credentials_path=config.vertex_credentials_path,
        project_id=config.vertex_project_id,
        location=config.vertex_location,
    )
    
    # Build the prompt
    system_prompt = """You are an IT support specialist at ACME Corp. Your job is to help employees resolve technical issues quickly and accurately.

When responding to issues:
1. Identify the most likely root cause based on the symptoms
2. Provide specific, actionable steps to resolve the issue
3. Be confident when you recognize a known issue
4. Explain why the issue occurred if you know

Keep responses concise but complete. Focus on solving the problem, not generic troubleshooting."""

    # Add knowledge base if available
    if knowledge_base:
        system_prompt += f"\n\nOfficial IT Documentation:\n{knowledge_base}"
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add examples if using ICRL
    if with_examples:
        db = TrajectoryDatabase(str(DEMO_DB_PATH))
        if len(db) > 0:
            # Search for similar past tickets
            similar = db.search(issue, k=3)
            
            if similar:
                examples_text = "Here are some similar issues that were resolved previously:\n\n"
                for i, traj in enumerate(similar, 1):
                    resolution = traj.metadata.get("final_response", "")
                    root_cause = traj.metadata.get("root_cause", "")
                    examples_text += f"--- Past Ticket {i} ---\n"
                    examples_text += f"Issue: {traj.goal}\n"
                    if root_cause:
                        examples_text += f"Root Cause: {root_cause}\n"
                    if resolution:
                        examples_text += f"Resolution: {resolution}\n"
                    examples_text += "\n"
                
                messages.append({
                    "role": "user",
                    "content": f"{examples_text}\n---\n\nNow, please help with this new issue:\n\n{issue}"
                })
            else:
                messages.append({"role": "user", "content": issue})
        else:
            messages.append({"role": "user", "content": issue})
    else:
        messages.append({"role": "user", "content": issue})
    
    # Get response
    start_time = datetime.now()
    response = await llm.complete_text(messages)
    duration = (datetime.now() - start_time).total_seconds()
    
    return response, duration


def evaluate_response(response: str, expected_keywords: list[str]) -> tuple[list[str], list[str], float]:
    """Evaluate a response against expected keywords.
    
    Returns:
        Tuple of (found keywords, missing keywords, score 0-100)
    """
    response_lower = response.lower()
    
    found = []
    missing = []
    
    for keyword in expected_keywords:
        if keyword.lower() in response_lower:
            found.append(keyword)
        else:
            missing.append(keyword)
    
    # Score is percentage of keywords found
    if expected_keywords:
        score = (len(found) / len(expected_keywords)) * 100
    else:
        score = 50  # Neutral if no keywords defined
    
    return found, missing, score


async def run_test(ticket: dict, with_examples: bool, knowledge_base: str, verbose: bool = False) -> TestResult:
    """Run a single test case."""
    mode = "icrl" if with_examples else "vanilla"
    
    response, duration = await get_support_response(
        issue=ticket["issue"],
        with_examples=with_examples,
        knowledge_base=knowledge_base,
    )
    
    found, missing, score = evaluate_response(response, ticket["expected_keywords"])
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Response ({mode}):")
        print(f"{'='*60}")
        print(response)
        print(f"\nKeywords found: {found}")
        print(f"Keywords missing: {missing}")
    
    return TestResult(
        ticket_id=ticket["id"],
        mode=mode,
        response=response,
        duration=duration,
        keywords_found=found,
        keywords_missing=missing,
        score=score,
    )


async def main():
    parser = argparse.ArgumentParser(description="Run IT Support demo")
    parser.add_argument("--quick", action="store_true", help="Run only 3 test cases")
    parser.add_argument("--verbose", action="store_true", help="Show full responses")
    args = parser.parse_args()
    
    print("🎯 IT Support Demo: ICRL vs Vanilla Comparison")
    print("=" * 60)
    
    # Check if database exists
    if not DEMO_DB_PATH.exists():
        print("❌ Demo database not found. Run setup_demo.py first.")
        sys.exit(1)
    
    # Load test tickets
    tickets = load_test_tickets()
    if args.quick:
        tickets = tickets[:3]
    
    print(f"\n📋 Running {len(tickets)} test cases...")
    
    # Load knowledge base
    knowledge_base = load_knowledge_base()
    
    # Store results
    icrl_results: list[TestResult] = []
    vanilla_results: list[TestResult] = []
    
    for i, ticket in enumerate(tickets, 1):
        print(f"\n{'─'*60}")
        print(f"Test {i}/{len(tickets)}: {ticket['title']}")
        print(f"{'─'*60}")
        print(f"Issue: {ticket['issue'][:100]}...")
        
        # Run ICRL (with examples)
        print("\n🧠 Running ICRL (with examples)...")
        icrl_result = await run_test(ticket, with_examples=True, knowledge_base=knowledge_base, verbose=args.verbose)
        icrl_results.append(icrl_result)
        print(f"   Score: {icrl_result.score:.0f}% ({len(icrl_result.keywords_found)}/{len(ticket['expected_keywords'])} keywords)")
        
        # Run vanilla (no examples)
        print("\n📝 Running Vanilla (no examples)...")
        vanilla_result = await run_test(ticket, with_examples=False, knowledge_base=knowledge_base, verbose=args.verbose)
        vanilla_results.append(vanilla_result)
        print(f"   Score: {vanilla_result.score:.0f}% ({len(vanilla_result.keywords_found)}/{len(ticket['expected_keywords'])} keywords)")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"\n{'Ticket':<12} {'Category':<15} {'ICRL':<10} {'Vanilla':<10} {'Δ':<8}")
    print("─" * 55)
    
    total_icrl = 0
    total_vanilla = 0
    
    for ticket, icrl, vanilla in zip(tickets, icrl_results, vanilla_results):
        delta = icrl.score - vanilla.score
        delta_str = f"+{delta:.0f}%" if delta > 0 else f"{delta:.0f}%"
        print(f"{ticket['id']:<12} {ticket['category']:<15} {icrl.score:>5.0f}%    {vanilla.score:>5.0f}%    {delta_str:<8}")
        total_icrl += icrl.score
        total_vanilla += vanilla.score
    
    avg_icrl = total_icrl / len(tickets)
    avg_vanilla = total_vanilla / len(tickets)
    avg_delta = avg_icrl - avg_vanilla
    
    print("─" * 55)
    delta_str = f"+{avg_delta:.0f}%" if avg_delta > 0 else f"{avg_delta:.0f}%"
    print(f"{'AVERAGE':<12} {'':<15} {avg_icrl:>5.0f}%    {avg_vanilla:>5.0f}%    {delta_str:<8}")
    
    # Analysis
    print("\n" + "=" * 60)
    print("📈 ANALYSIS")
    print("=" * 60)
    
    print(f"\n  ICRL Average Score:    {avg_icrl:.1f}%")
    print(f"  Vanilla Average Score: {avg_vanilla:.1f}%")
    print(f"  Improvement:           {avg_delta:+.1f}%")
    
    if avg_delta > 20:
        print("\n  ✅ ICRL significantly outperforms vanilla!")
        print("     The learned knowledge from past tickets makes a clear difference.")
    elif avg_delta > 5:
        print("\n  ✅ ICRL shows improvement over vanilla.")
        print("     Past ticket knowledge helps identify issues faster.")
    elif avg_delta > -5:
        print("\n  ⚠️  Results are similar between ICRL and vanilla.")
        print("     The test cases may not be differentiated enough.")
    else:
        print("\n  ❌ Unexpected: vanilla performed better.")
        print("     Check the seed data and test cases.")
    
    # Show example comparison
    if icrl_results and vanilla_results:
        # Find the test with biggest difference
        best_diff_idx = 0
        best_diff = 0
        for i, (icrl, vanilla) in enumerate(zip(icrl_results, vanilla_results)):
            diff = icrl.score - vanilla.score
            if diff > best_diff:
                best_diff = diff
                best_diff_idx = i
        
        if best_diff > 0:
            ticket = tickets[best_diff_idx]
            icrl = icrl_results[best_diff_idx]
            vanilla = vanilla_results[best_diff_idx]
            
            print(f"\n{'─'*60}")
            print(f"📌 Best Example: {ticket['title']}")
            print(f"{'─'*60}")
            print(f"\nExpected root cause: {ticket['expected_root_cause']}")
            print(f"\nICRL found keywords: {icrl.keywords_found}")
            print(f"Vanilla found keywords: {vanilla.keywords_found}")
            print(f"\nICRL response (excerpt):")
            print(f"  {icrl.response[:300]}...")
            print(f"\nVanilla response (excerpt):")
            print(f"  {vanilla.response[:300]}...")
    
    print("\n" + "=" * 60)
    print("🏁 Demo Complete!")
    print("=" * 60)
    
    # Save results
    results_file = DEMO_DIR / "demo_results.json"
    results = {
        "timestamp": datetime.now().isoformat(),
        "num_tests": len(tickets),
        "icrl_avg_score": avg_icrl,
        "vanilla_avg_score": avg_vanilla,
        "improvement": avg_delta,
        "details": [
            {
                "ticket_id": t["id"],
                "category": t["category"],
                "icrl_score": i.score,
                "vanilla_score": v.score,
                "icrl_keywords_found": i.keywords_found,
                "vanilla_keywords_found": v.keywords_found,
            }
            for t, i, v in zip(tickets, icrl_results, vanilla_results)
        ]
    }
    
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
