#!/usr/bin/env python3
"""Detailed evaluation of IT Support demo responses.

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


def load_test_tickets() -> dict[str, dict]:
    """Load test tickets indexed by ID."""
    test_file = SCENARIOS_DIR / "test_tickets.json"
    with open(test_file) as f:
        tickets = json.load(f)
    return {t["id"]: t for t in tickets}


def analyze_by_category(results: dict, tickets: dict[str, dict]) -> dict:
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


def analyze_keyword_coverage(results: dict, tickets: dict[str, dict]) -> dict:
    """Analyze which keywords are consistently found or missed."""
    keyword_stats = defaultdict(lambda: {"icrl_found": 0, "vanilla_found": 0, "total": 0})
    
    for detail in results["details"]:
        ticket = tickets.get(detail["ticket_id"], {})
        expected = ticket.get("expected_keywords", [])
        
        for kw in expected:
            keyword_stats[kw]["total"] += 1
            if kw in detail.get("icrl_keywords_found", []):
                keyword_stats[kw]["icrl_found"] += 1
            if kw in detail.get("vanilla_keywords_found", []):
                keyword_stats[kw]["vanilla_found"] += 1
    
    return dict(keyword_stats)


def print_detailed_report(results: dict, tickets: dict[str, dict]):
    """Print a detailed analysis report."""
    print("=" * 70)
    print("📊 DETAILED EVALUATION REPORT")
    print("=" * 70)
    
    # Overall summary
    print(f"\n📅 Run timestamp: {results['timestamp']}")
    print(f"📋 Test cases: {results['num_tests']}")
    
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
    
    category_analysis = analyze_by_category(results, tickets)
    
    print(f"\n{'Category':<20} {'ICRL':<10} {'Vanilla':<10} {'Δ':<10} {'Count':<8}")
    print("─" * 58)
    
    for cat, data in sorted(category_analysis.items(), key=lambda x: -x[1]["improvement"]):
        delta_str = f"+{data['improvement']:.0f}%" if data["improvement"] > 0 else f"{data['improvement']:.0f}%"
        print(f"{cat:<20} {data['icrl_avg']:>5.0f}%    {data['vanilla_avg']:>5.0f}%    {delta_str:<10} {data['count']:<8}")
    
    # Per-ticket breakdown
    print("\n" + "─" * 70)
    print("PER-TICKET RESULTS")
    print("─" * 70)
    
    for detail in results["details"]:
        ticket = tickets.get(detail["ticket_id"], {})
        delta = detail["icrl_score"] - detail["vanilla_score"]
        
        print(f"\n{detail['ticket_id']}: {ticket.get('title', 'Unknown')}")
        print(f"  Category: {detail['category']}")
        print(f"  Expected root cause: {ticket.get('expected_root_cause', 'N/A')}")
        print(f"  ICRL Score: {detail['icrl_score']:.0f}% | Vanilla Score: {detail['vanilla_score']:.0f}% | Δ: {delta:+.0f}%")
        
        icrl_found = detail.get("icrl_keywords_found", [])
        vanilla_found = detail.get("vanilla_keywords_found", [])
        expected = ticket.get("expected_keywords", [])
        
        icrl_missing = [k for k in expected if k not in icrl_found]
        vanilla_missing = [k for k in expected if k not in vanilla_found]
        
        print(f"  ICRL keywords: {icrl_found}")
        if icrl_missing:
            print(f"  ICRL missing: {icrl_missing}")
        print(f"  Vanilla keywords: {vanilla_found}")
        if vanilla_missing:
            print(f"  Vanilla missing: {vanilla_missing}")
    
    # Keyword analysis
    print("\n" + "─" * 70)
    print("KEYWORD DETECTION RATES")
    print("─" * 70)
    
    keyword_stats = analyze_keyword_coverage(results, tickets)
    
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
    wins = [(d["ticket_id"], d["icrl_score"] - d["vanilla_score"]) 
            for d in results["details"]]
    wins.sort(key=lambda x: -x[1])
    
    if wins and wins[0][1] > 0:
        print(f"\n✅ Biggest ICRL win: {wins[0][0]} (+{wins[0][1]:.0f}%)")
        ticket = tickets.get(wins[0][0], {})
        print(f"   Issue type: {ticket.get('title', 'Unknown')}")
        print(f"   Root cause: {ticket.get('expected_root_cause', 'Unknown')}")
    
    # Find categories where ICRL helps most
    best_cat = max(category_analysis.items(), key=lambda x: x[1]["improvement"])
    if best_cat[1]["improvement"] > 0:
        print(f"\n✅ Best category for ICRL: {best_cat[0]} (+{best_cat[1]['improvement']:.0f}%)")
    
    # Find any cases where vanilla won
    vanilla_wins = [w for w in wins if w[1] < 0]
    if vanilla_wins:
        print(f"\n⚠️  Vanilla performed better in {len(vanilla_wins)} case(s):")
        for ticket_id, delta in vanilla_wins:
            print(f"   - {ticket_id}: {delta:.0f}%")
    
    # Overall assessment
    print("\n" + "─" * 70)
    print("OVERALL ASSESSMENT")
    print("─" * 70)
    
    improvement = results["improvement"]
    if improvement > 30:
        print("""
✅ EXCELLENT: ICRL dramatically outperforms vanilla.

The learned knowledge from past support tickets makes a significant
difference in identifying root causes and providing specific solutions.
This demonstrates the value of experience-based learning for support tasks.
""")
    elif improvement > 15:
        print("""
✅ GOOD: ICRL shows clear improvement over vanilla.

Past ticket knowledge helps identify issues faster and provide more
targeted solutions. The improvement is meaningful for support efficiency.
""")
    elif improvement > 5:
        print("""
👍 MODERATE: ICRL shows some improvement over vanilla.

There's a measurable benefit from past ticket knowledge, though
Claude's general knowledge also handles many cases reasonably well.
""")
    elif improvement > -5:
        print("""
⚠️  SIMILAR: ICRL and vanilla perform comparably.

The test cases may not differentiate enough, or Claude's general
knowledge is sufficient for these particular issues.
""")
    else:
        print("""
❌ UNEXPECTED: Vanilla performed better than ICRL.

This is unusual and may indicate issues with:
- Seed data quality
- Test case design
- Example retrieval relevance
""")


def main():
    parser = argparse.ArgumentParser(description="Evaluate IT Support demo results")
    parser.add_argument("--rerun", action="store_true", help="Re-run the demo first")
    args = parser.parse_args()
    
    if args.rerun:
        import subprocess
        print("🔄 Re-running demo...")
        subprocess.run([sys.executable, str(DEMO_DIR / "run_demo.py")])
        print("\n")
    
    results = load_results()
    tickets = load_test_tickets()
    
    print_detailed_report(results, tickets)


if __name__ == "__main__":
    main()
