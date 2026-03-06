#!/usr/bin/env python3
"""Run Lean theorem proving experiments with ICRL.

Examples:
    # Run 1 toy theorem (no Lean required)
    uv run python experiments/lean/run.py --dataset toy --n 1

    # Run 3 toy theorems
    uv run python experiments/lean/run.py --dataset toy --n 3

    # Run specific toy theorem by name
    uv run python experiments/lean/run.py --dataset toy --theorem one_plus_one

    # Run miniF2F (requires GITHUB_ACCESS_TOKEN and Lean toolchain)
    uv run python experiments/lean/run.py --dataset minif2f --n 1

    # List available theorems
    uv run python experiments/lean/run.py --list
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load .env file automatically

from icrl import Agent, LiteLLMProvider
from icrl.lean import (
    LeanEnvironment,
    MiniF2FLoader,
    ToyLeanEnvironment,
    get_toy_theorem_by_name,
    get_toy_theorems,
)

LEAN_ACT_PROMPT = """You are a Lean 4 theorem prover.

Theorem: {goal}

Current proof state:
{observation}

{examples}

Output the next Lean 4 tactic to apply. Common tactics:
- rfl: reflexivity (a = a, or definitional equality)
- ring: polynomial arithmetic
- linarith: linear arithmetic over ordered rings
- norm_num: numeric computation
- simp: simplification
- exact h: use hypothesis h directly
- trivial: solve trivial goals

Respond with ONLY the tactic, nothing else."""


def print_header(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_step(step_num: int, action: str, observation: str) -> None:
    print(f"  Step {step_num}: {action}")
    if "complete" not in observation.lower():
        print(f"         → {observation[:80]}...")


def run_toy(args: argparse.Namespace) -> None:
    print_header("TOY DATASET (Mock Environment)")
    
    if args.theorem:
        thm = get_toy_theorem_by_name(args.theorem)
        if not thm:
            print(f"Error: Unknown theorem '{args.theorem}'")
            print("Available:", [t.name for t in get_toy_theorems()])
            sys.exit(1)
        theorems = [thm]
    else:
        theorems = get_toy_theorems(args.n)

    print(f"Running {len(theorems)} theorem(s)")
    print(f"Model: {args.model}")

    with tempfile.TemporaryDirectory() as tmpdir:
        agent = Agent(
            llm=LiteLLMProvider(model=args.model, temperature=0.0),
            db_path=str(Path(tmpdir) / "trajectories"),
            plan_prompt="",
            reason_prompt="",
            act_prompt=LEAN_ACT_PROMPT,
            k=3,
            max_steps=args.max_steps,
        )

        results = []
        for i, thm in enumerate(theorems):
            print(f"\n[{i+1}/{len(theorems)}] {thm.name}")
            print(f"  Statement: {thm.statement}")
            print(f"  Expected: {thm.expected_tactic}")

            env = ToyLeanEnvironment(thm)
            try:
                trajectory = agent.train_sync(env, goal=thm.statement)
                results.append(trajectory.success)

                if trajectory.success:
                    print(f"  ✓ Proved in {len(trajectory.steps)} step(s)")
                else:
                    print(f"  ✗ Failed after {len(trajectory.steps)} step(s)")

                for j, step in enumerate(trajectory.steps):
                    print_step(j + 1, step.action, step.observation)

            except Exception as e:
                print(f"  ✗ Error: {e}")
                results.append(False)
            finally:
                env.close()

        print_header("RESULTS")
        n_success = sum(results)
        n_total = len(results)
        print(f"  Proved: {n_success}/{n_total} ({100*n_success/n_total:.1f}%)")


def run_minif2f(args: argparse.Namespace) -> None:
    print_header("MINIF2F DATASET (Real Lean)")

    if not os.environ.get("GITHUB_ACCESS_TOKEN"):
        print("Error: GITHUB_ACCESS_TOKEN required for LeanDojo")
        print("Set it with: export GITHUB_ACCESS_TOKEN=...")
        sys.exit(1)

    print("Loading miniF2F theorems (this may take a while on first run)...")
    loader = MiniF2FLoader()
    loader.trace_repo()

    if args.theorem:
        theorems = [t for t in loader.get_easy_subset() if args.theorem in t.full_name]
        if not theorems:
            print(f"Error: No theorem matching '{args.theorem}'")
            sys.exit(1)
    else:
        theorems = loader.get_easy_subset()[:args.n]

    print(f"Running {len(theorems)} theorem(s)")
    print(f"Model: {args.model}")

    with tempfile.TemporaryDirectory() as tmpdir:
        agent = Agent(
            llm=LiteLLMProvider(model=args.model, temperature=0.0),
            db_path=str(Path(tmpdir) / "trajectories"),
            plan_prompt="",
            reason_prompt="",
            act_prompt=LEAN_ACT_PROMPT,
            k=3,
            max_steps=args.max_steps,
        )

        results = []
        for i, thm in enumerate(theorems):
            print(f"\n[{i+1}/{len(theorems)}] {thm.full_name}")

            env = LeanEnvironment(thm)
            try:
                trajectory = agent.train_sync(env, goal=str(thm))
                results.append(trajectory.success)

                if trajectory.success:
                    print(f"  ✓ Proved in {len(trajectory.steps)} step(s)")
                else:
                    print(f"  ✗ Failed after {len(trajectory.steps)} step(s)")

                for j, step in enumerate(trajectory.steps):
                    print_step(j + 1, step.action, step.observation)

            except Exception as e:
                print(f"  ✗ Error: {e}")
                results.append(False)
            finally:
                env.close()

        print_header("RESULTS")
        n_success = sum(results)
        n_total = len(results)
        print(f"  Proved: {n_success}/{n_total} ({100*n_success/n_total:.1f}%)")


def list_theorems() -> None:
    print_header("AVAILABLE THEOREMS")

    print("\n[TOY DATASET]")
    for thm in get_toy_theorems():
        print(f"  {thm.name:20} - {thm.description}")

    print("\n[MINIF2F DATASET]")
    print("  Run with --dataset minif2f to load (requires GITHUB_ACCESS_TOKEN)")
    print("  Categories: mathd_algebra_*, mathd_numbertheory_*, amc*, aime*")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Lean theorem proving experiments with ICRL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dataset",
        choices=["toy", "minif2f"],
        default="toy",
        help="Dataset to use (default: toy)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of theorems to run (default: 1)",
    )
    parser.add_argument(
        "--theorem",
        type=str,
        help="Run a specific theorem by name",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("ICRL_MODEL", "gemini/gemini-2.0-flash"),
        help="LLM model to use (default: gemini/gemini-2.0-flash or ICRL_MODEL env var)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=5,
        help="Maximum proof steps (default: 5)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available theorems and exit",
    )

    args = parser.parse_args()

    if args.list:
        list_theorems()
        return

    if args.dataset == "toy":
        run_toy(args)
    elif args.dataset == "minif2f":
        run_minif2f(args)


if __name__ == "__main__":
    main()
