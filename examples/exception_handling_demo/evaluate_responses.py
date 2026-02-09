#!/usr/bin/env python3
"""Detailed evaluation of Exception Handling demo responses.

This script provides detailed analysis of the demo results,
including per-category breakdowns and response quality metrics.

Usage:
    python evaluate_responses.py              # Analyze last run
    python evaluate_responses.py --rerun      # Re-run and analyze
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

DEMO_DIR = Path(__file__).parent
RESULTS_FILE = DEMO_DIR / "demo_results.json"
SCENARIOS_DIR = DEMO_DIR / "scenarios"


def load_results() -> dict:
    """Load results from the last demo run."""
    if not RESULTS_FILE.exists():
        print("❌ No results file found. Run 'python run_demo.py' first.")
        sys.exit(1)
    
    with open(RESULTS_FILE) as f:
        return json.load(f)


def load_test_scenarios() -> dict[str, dict]:
    """Load test scenarios indexed by ID."""
    test_file = SCENARIOS_DIR / "test_scenarios.json"
    with open(test_file) as f:
        scenarios = json.load(f)
    return {s["id"]: s for s in scenarios}


def analyze_by_category(results: dict, scenarios: dict[str, dict]) -> dict:
    """Analyze results by category."""
    categories = defaultdict(lambda: {"icrl_scores": [], "vanilla_scores": []})
    
    for detail in results["details"]:
        cat = detail["category"]
        categories[cat]["icrl_scores"].append(detail["icrl_score"])
        categories[cat]["vanilla_scores"].append(detail["vanilla_score"])
    
    analysis = {}
    for cat, data in categories.items():
        icrl_avg = sum(data["icrl_scores"]) / len(data["icrl_scores"])
        vanilla_avg = sum(data["vanilla_scores"]) / len(data["vanilla_scores"])
        analysis[cat] = {
            "icrl_avg": icrl_avg,
            "vanilla_avg": vanilla_avg,
            "improvement": icrl_avg - vanilla_avg,
            "count": len(data["icrl_scores"]),
        }
    
    return analysis


def analyze_by_action(results: dict, scenarios: dict[str, dict]) -> dict:
    """Analyze results by expected action type."""
    actions = defaultdict(lambda: {"icrl_scores": [], "vanilla_scores": []})
    
    for detail in results["details"]:
        action = detail.get("expected_action", "unknown")
        actions[action]["icrl_scores"].append(detail["icrl_score"])
        actions[action]["vanilla_scores"].append(detail["vanilla_score"])
    
    analysis = {}
    for action, data in actions.items():
        icrl_avg = sum(data["icrl_scores"]) / len(data["icrl_scores"])
        vanilla_avg = sum(data["vanilla_scores"]) / len(data["vanilla_scores"])
        analysis[action] = {
            "icrl_avg": icrl_avg,
            "vanilla_avg": vanilla_avg,
            "improvement": icrl_avg - vanilla_avg,
            "count": len(data["icrl_scores"]),
        }
    
    return analysis


def analyze_keyword_coverage(results: dict, scenarios: dict[str, dict]) -> dict:
    """Analyze which keywords are consistently found or missed."""
    keyword_stats = defaultdict(lambda: {"icrl_found": 0, "vanilla_found": 0, "total": 0})
    
    for detail in results["details"]:
        scenario = scenarios.get(detail["scenario_id"], {})
        expected = scenario.get("expected_keywords", [])
        
        for kw in expected:
            keyword_stats[kw]["total"] += 1
            if kw in detail.get("icrl_keywords_found", []):
                keyword_stats[kw]["icrl_found"] += 1
            if kw in detail.get("vanilla_keywords_found", []):
                keyword_stats[kw]["vanilla_found"] += 1
    
    return dict(keyword_stats)


def print_detailed_report(results: dict, scenarios: dict[str, dict]):
    """Print a detailed analysis report."""
    print("=" * 70)
    print("📊 DETAILED EVALUATION REPORT: Exception Handling Demo")
    print("=" * 70)
    
    # Overall summary
    print(f"\n📅 Run timestamp: {results['timestamp']}")
    print(f"📋 Test scenarios: {results['num_tests']}")
    
    print("\n" + "─" * 70)
    print("OVERALL SCORES")
    print("─" * 70)
    print(f"  ICRL Average:    {results['icrl_avg_score']:.1f}%")
    print(f"  Vanilla Average: {results['vanilla_avg_score']:.1f}%")
    print(f"  Improvement:     {results['improvement']:+.1f}%")
    
    # Category breakdown
    print("\n" + "─" * 70)
    print("SCORES BY CATEGORY")
    print("─" * 70)
    
    category_analysis = analyze_by_category(results, scenarios)
    
    print(f"\n{'Category':<20} {'ICRL':<10} {'Vanilla':<10} {'Δ':<10} {'Count':<8}")
    print("─" * 58)
    
    for cat, data in sorted(category_analysis.items(), key=lambda x: -x[1]["improvement"]):
        delta_str = f"+{data['improvement']:.0f}%" if data["improvement"] > 0 else f"{data['improvement']:.0f}%"
        print(f"{cat:<20} {data['icrl_avg']:>5.0f}%    {data['vanilla_avg']:>5.0f}%    {delta_str:<10} {data['count']:<8}")
    
    # Action type breakdown
    print("\n" + "─" * 70)
    print("SCORES BY EXPECTED ACTION")
    print("─" * 70)
    
    action_analysis = analyze_by_action(results, scenarios)
    
    print(f"\n{'Action':<25} {'ICRL':<10} {'Vanilla':<10} {'Δ':<10}")
    print("─" * 55)
    
    for action, data in sorted(action_analysis.items(), key=lambda x: -x[1]["improvement"]):
        delta_str = f"+{data['improvement']:.0f}%" if data["improvement"] > 0 else f"{data['improvement']:.0f}%"
        print(f"{action:<25} {data['icrl_avg']:>5.0f}%    {data['vanilla_avg']:>5.0f}%    {delta_str:<10}")
    
    # Per-scenario breakdown
    print("\n" + "─" * 70)
    print("PER-SCENARIO RESULTS")
    print("─" * 70)
    
    for detail in results["details"]:
        scenario = scenarios.get(detail["scenario_id"], {})
        delta = detail["icrl_score"] - detail["vanilla_score"]
        
        print(f"\n{detail['scenario_id']}: {scenario.get('title', 'Unknown')}")
        print(f"  Category: {detail['category']}")
        print(f"  Expected action: {detail.get('expected_action', 'N/A')}")
        print(f"  Expected reasoning: {scenario.get('expected_reasoning', 'N/A')}")
        print(f"  ICRL Score: {detail['icrl_score']:.0f}% | Vanilla Score: {detail['vanilla_score']:.0f}% | Δ: {delta:+.0f}%")
        
        icrl_found = detail.get("icrl_keywords_found", [])
        vanilla_found = detail.get("vanilla_keywords_found", [])
        expected = scenario.get("expected_keywords", [])
        
        icrl_missing = [k for k in expected if k not in icrl_found]
        vanilla_missing = [k for k in expected if k not in vanilla_found]
        
        print(f"  ICRL keywords: {icrl_found}")
        if icrl_missing:
            print(f"  ICRL missing: {icrl_missing}")
        print(f"  Vanilla keywords: {vanilla_found}")
        if vanilla_missing:
            print(f"  Vanilla missing: {vanilla_missing}")
        
        # Show vanilla's likely response vs what we got
        vanilla_likely = scenario.get("vanilla_likely_response", "")
        if vanilla_likely:
            print(f"  Expected vanilla behavior: {vanilla_likely}")
    
    # Keyword analysis
    print("\n" + "─" * 70)
    print("KEYWORD DETECTION RATES")
    print("─" * 70)
    
    keyword_stats = analyze_keyword_coverage(results, scenarios)
    
    print(f"\n{'Keyword':<30} {'ICRL':<15} {'Vanilla':<15}")
    print("─" * 60)
    
    for kw, stats in sorted(keyword_stats.items(), key=lambda x: -(x[1]["icrl_found"] - x[1]["vanilla_found"])):
        icrl_rate = (stats["icrl_found"] / stats["total"] * 100) if stats["total"] > 0 else 0
        vanilla_rate = (stats["vanilla_found"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"{kw:<30} {icrl_rate:>5.0f}%         {vanilla_rate:>5.0f}%")
    
    # Insights
    print("\n" + "─" * 70)
    print("KEY INSIGHTS")
    print("─" * 70)
    
    # Find biggest wins
    wins = [(d["scenario_id"], d["icrl_score"] - d["vanilla_score"]) 
            for d in results["details"]]
    wins.sort(key=lambda x: -x[1])
    
    if wins and wins[0][1] > 0:
        print(f"\n✅ Biggest ICRL win: {wins[0][0]} (+{wins[0][1]:.0f}%)")
        scenario = scenarios.get(wins[0][0], {})
        print(f"   Scenario: {scenario.get('title', 'Unknown')}")
        print(f"   Expected action: {scenario.get('expected_action', 'Unknown')}")
        print(f"   Why ICRL wins: Precedent-based judgment vs rigid policy")
    
    # Find categories where ICRL helps most
    if category_analysis:
        best_cat = max(category_analysis.items(), key=lambda x: x[1]["improvement"])
        if best_cat[1]["improvement"] > 0:
            print(f"\n✅ Best category for ICRL: {best_cat[0]} (+{best_cat[1]['improvement']:.0f}%)")
    
    # Find any cases where vanilla won
    vanilla_wins = [w for w in wins if w[1] < 0]
    if vanilla_wins:
        print(f"\n⚠️  Vanilla performed better in {len(vanilla_wins)} case(s):")
        for scenario_id, delta in vanilla_wins:
            scenario = scenarios.get(scenario_id, {})
            print(f"   - {scenario_id}: {delta:.0f}% ({scenario.get('title', 'Unknown')})")
    
    # Cases where policy should be followed
    hold_line_cases = [d for d in results["details"] if d.get("expected_action") == "hold_line"]
    if hold_line_cases:
        print(f"\n📋 'Hold the line' cases (policy should be followed):")
        for case in hold_line_cases:
            scenario = scenarios.get(case["scenario_id"], {})
            print(f"   - {case['scenario_id']}: ICRL {case['icrl_score']:.0f}% vs Vanilla {case['vanilla_score']:.0f}%")
            print(f"     Both should correctly deny the exception request")
    
    # Overall assessment
    print("\n" + "─" * 70)
    print("OVERALL ASSESSMENT")
    print("─" * 70)
    
    improvement = results["improvement"]
    if improvement > 30:
        print("""
✅ EXCELLENT: ICRL dramatically outperforms vanilla.

The learned precedents from past exception-handling decisions enable
nuanced, business-appropriate responses that balance policy with
customer value. This demonstrates the power of institutional memory.

Key advantages:
• Knows when to approve exceptions (loyal customers, high value)
• Knows when to escalate and to whom
• Provides confident, consistent decisions
• Matches real-world business practice, not just written policy
""")
    elif improvement > 15:
        print("""
✅ GOOD: ICRL shows clear improvement over vanilla.

Past decision precedents help guide judgment calls in edge cases.
ICRL better understands the unwritten rules of exception handling.

Key advantages:
• Better customer retention decisions
• More appropriate escalation paths
• Less rigid policy interpretation
""")
    elif improvement > 5:
        print("""
👍 MODERATE: ICRL shows some improvement over vanilla.

There's a measurable benefit from learned precedents, though
Claude's general reasoning also handles some cases reasonably.
""")
    elif improvement > -5:
        print("""
⚠️  SIMILAR: ICRL and vanilla perform comparably.

The test cases may not differentiate enough, or the policies
are clear enough that precedents don't add much value.
""")
    else:
        print("""
❌ UNEXPECTED: Vanilla performed better than ICRL.

This is unusual and may indicate issues with:
- Seed decision quality or relevance
- Test scenario design
- Example retrieval relevance
""")
    
    # Show response comparison for best case
    if wins and wins[0][1] > 10:
        best_id = wins[0][0]
        best_detail = next((d for d in results["details"] if d["scenario_id"] == best_id), None)
        if best_detail:
            print("\n" + "─" * 70)
            print(f"RESPONSE COMPARISON: {best_id}")
            print("─" * 70)
            
            scenario = scenarios.get(best_id, {})
            print(f"\nSituation: {scenario.get('situation', 'N/A')[:200]}...")
            
            print(f"\n📗 ICRL Response:")
            print(f"   {best_detail.get('icrl_response', 'N/A')[:400]}...")
            
            print(f"\n📕 Vanilla Response:")
            print(f"   {best_detail.get('vanilla_response', 'N/A')[:400]}...")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Exception Handling demo results")
    parser.add_argument("--rerun", action="store_true", help="Re-run the demo first")
    args = parser.parse_args()
    
    if args.rerun:
        import subprocess
        print("🔄 Re-running demo...")
        subprocess.run([sys.executable, str(DEMO_DIR / "run_demo.py")])
        print("\n")
    
    results = load_results()
    scenarios = load_test_scenarios()
    
    print_detailed_report(results, scenarios)


if __name__ == "__main__":
    main()
