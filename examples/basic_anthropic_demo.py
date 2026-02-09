"""Minimal Anthropic demo for getting started with ICRL.

Prerequisites:
- ANTHROPIC_API_KEY set in your environment
- Optional: MODEL (tried first if set; otherwise common Anthropic candidates)

Run with:
    uv run python examples/basic_anthropic_demo.py
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from icrl import Agent, LiteLLMProvider

PLAN_PROMPT = "Goal: {goal}\nExamples:\n{examples}\nPlan:"
REASON_PROMPT = "Goal: {goal}\nPlan: {plan}\nObservation: {observation}\nThink:"
ACT_PROMPT = "Goal: {goal}\nPlan: {plan}\nReasoning: {reasoning}\nAction:"


class MinimalEnvironment:
    """Tiny environment that succeeds after one action."""

    def reset(self, goal: str) -> str:
        return f"Goal: {goal}"

    def step(self, action: str) -> tuple[str, bool, bool]:
        return f"Action received: {action}", True, True


async def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Missing ANTHROPIC_API_KEY. Set it and rerun.")
        return

    model_candidates = []
    if os.environ.get("MODEL"):
        model_candidates.append(os.environ["MODEL"])
    model_candidates.extend(
        [
            "claude-sonnet-4-5",
            "claude-sonnet-4",
            "claude-3-7-sonnet-latest",
            "claude-3-5-sonnet-latest",
        ]
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        for model in model_candidates:
            try:
                llm = LiteLLMProvider(model=model, temperature=0.0, max_tokens=256)
                agent = Agent(
                    llm=llm,
                    db_path=str(Path(tmpdir) / "trajectories"),
                    plan_prompt=PLAN_PROMPT,
                    reason_prompt=REASON_PROMPT,
                    act_prompt=ACT_PROMPT,
                    k=1,
                    max_steps=3,
                )

                goal = "Demonstrate one minimal training run"
                trajectory = await agent.train(MinimalEnvironment(), goal=goal)
                print(f"Model: {model}")
                print(f"Success: {trajectory.success}")
                print(f"Steps: {len(trajectory.steps)}")
                return
            except Exception as exc:
                print(f"Model failed: {model} ({type(exc).__name__})")

    print("Could not run Anthropic demo with available model candidates.")


if __name__ == "__main__":
    asyncio.run(main())
