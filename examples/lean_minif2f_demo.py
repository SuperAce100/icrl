"""Demo: ICRL on miniF2F-lean4 mathd theorems.

Run with:
    export GITHUB_ACCESS_TOKEN=...  # Optional: helps avoid GitHub rate limits
    uv run python examples/lean_minif2f_demo.py
"""

import os
from icrl import Agent, LiteLLMProvider
from icrl.lean import LeanEnvironment, MiniF2FLoader

LEAN_ACT_PROMPT = """You are a Lean 4 theorem prover.

Theorem: {goal}

Current proof state:
{observation}

{examples}

Output the next Lean 4 tactic to apply. Common tactics:
- ring: polynomial arithmetic
- linarith: linear arithmetic
- norm_num: numeric computation
- simp: simplification
- exact h: use hypothesis h directly
- field_simp: clear denominators

Respond with ONLY the tactic, nothing else."""


def main():
    model = os.environ.get("ICRL_MODEL", "gemini/gemini-2.0-flash")
    print(f"Using model: {model}")

    print("Loading miniF2F theorems...")
    loader = MiniF2FLoader()
    loader.trace_repo()

    easy_theorems = loader.get_easy_subset()
    print(f"Found {len(easy_theorems)} easy theorems (mathd_algebra + mathd_numbertheory)")

    agent = Agent(
        llm=LiteLLMProvider(model=model, temperature=0.0),
        db_path="./lean_trajectories",
        plan_prompt="",
        reason_prompt="",
        act_prompt=LEAN_ACT_PROMPT,
        k=3,
        max_steps=10,
    )

    n_success = 0
    n_total = 0
    for i, thm in enumerate(easy_theorems[:10]):
        print(f"\n[{i+1}/10] {thm.full_name}")
        env = LeanEnvironment(thm)
        try:
            trajectory = agent.train_sync(env, goal=str(thm))
            n_total += 1
            if trajectory.success:
                n_success += 1
                print(f"  ✓ Proved in {len(trajectory.steps)} steps")
                for step in trajectory.steps:
                    print(f"    → {step.action}")
            else:
                print(f"  ✗ Failed after {len(trajectory.steps)} steps")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        finally:
            env.close()

    print(f"\n{'='*50}")
    print(f"Results: {n_success}/{n_total} proved ({100*n_success/n_total:.1f}%)")
    print(f"Trajectories stored: {agent.get_stats()}")


if __name__ == "__main__":
    main()
