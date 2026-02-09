"""Minimal OpenAI demo for getting started with ICRL.

Prerequisites:
- OPENAI_API_KEY set in your environment
- Optional: MODEL (defaults to gpt-4o-mini)

Run with:
    uv run python examples/basic_openai_demo.py
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
    if not os.environ.get("OPENAI_API_KEY"):
        print("Missing OPENAI_API_KEY. Set it and rerun.")
        return

    model = os.environ.get("MODEL", "gpt-4o-mini")
    llm = LiteLLMProvider(model=model, temperature=0.0, max_tokens=256)

    with tempfile.TemporaryDirectory() as tmpdir:
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


if __name__ == "__main__":
    asyncio.run(main())
