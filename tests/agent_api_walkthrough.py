"""Offline walkthrough of the core Agent API.

This example is deterministic and requires no API keys.

It demonstrates:
- Agent.train / Agent.run
- Agent.train_sync / Agent.run_sync
- Agent.train_batch / Agent.run_batch
- seed_trajectories
- verify_trajectory callback
- on_step callback and get_stats

Run with:
    uv run python tests/agent_api_walkthrough.py
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from icrl import Agent, Step, StepContext, Trajectory
from icrl.models import Message

PLAN_PROMPT = "Goal: {goal}\nExamples:\n{examples}\nCreate a plan."
REASON_PROMPT = (
    "Goal: {goal}\nPlan: {plan}\nHistory:\n{history}\nObservation: {observation}\n"
    "Examples:\n{examples}\nThink:"
)
ACT_PROMPT = (
    "Goal: {goal}\nPlan: {plan}\nHistory:\n{history}\nObservation: {observation}\n"
    "Reasoning: {reasoning}\nExamples:\n{examples}\nAction:"
)


class AlwaysDoneLLM:
    """Deterministic provider that always chooses a one-step completion."""

    async def complete(self, messages: list[Message]) -> str:
        prompt = messages[-1].content.lower() if messages else ""
        if "action:" in prompt:
            return "done"
        if "think:" in prompt:
            return "One-step environment. Finish now."
        return "1. Execute `done`."


class OneStepEnvironment:
    """Environment that succeeds when action == 'done'."""

    def __init__(self) -> None:
        self._goal = ""
        self._finished = False

    def reset(self, goal: str) -> str:
        self._goal = goal
        self._finished = False
        return f"Goal: {goal}. Available command: done"

    def step(self, action: str) -> tuple[str, bool, bool]:
        if self._finished:
            return "Episode already finished.", True, False
        self._finished = True
        success = action.strip().lower() == "done"
        return f"Executed: {action}", True, success


async def run_async_api_examples(db_path: Path) -> None:
    step_calls: list[StepContext] = []

    def on_step(_step: Step, context: StepContext) -> None:
        step_calls.append(context)

    agent = Agent(
        llm=AlwaysDoneLLM(),
        db_path=str(db_path),
        plan_prompt=PLAN_PROMPT,
        reason_prompt=REASON_PROMPT,
        act_prompt=ACT_PROMPT,
        k=1,
        max_steps=3,
        on_step=on_step,
    )

    first = await agent.train(OneStepEnvironment(), "async training goal")
    assert first.success, "train() should succeed in OneStepEnvironment"

    second = await agent.train(OneStepEnvironment(), "async training goal")
    assert second.success, "second train() should also succeed"

    assert step_calls, "on_step callback should be called"
    assert step_calls[-1].examples, "retrieval should provide examples after bootstrap"

    before_run_db_size = len(agent.database)
    run_result = await agent.run(OneStepEnvironment(), "async inference goal")
    assert run_result.success, "run() should succeed"
    assert len(agent.database) == before_run_db_size, "run() must not mutate database"

    train_batch_results = await agent.train_batch(
        OneStepEnvironment,
        ["batch goal 1", "batch goal 2"],
    )
    assert len(train_batch_results) == 2
    assert all(t.success for t in train_batch_results)

    before_run_batch_db_size = len(agent.database)
    run_batch_results = await agent.run_batch(
        OneStepEnvironment,
        ["inference goal 1", "inference goal 2"],
    )
    assert len(run_batch_results) == 2
    assert all(t.success for t in run_batch_results)
    assert len(agent.database) == before_run_batch_db_size

    stats = agent.get_stats()
    assert stats["total_trajectories"] == len(agent.database)
    assert stats["successful_trajectories"] == len(agent.database)


def run_sync_api_examples(db_path: Path) -> None:
    agent = Agent(
        llm=AlwaysDoneLLM(),
        db_path=str(db_path),
        plan_prompt=PLAN_PROMPT,
        reason_prompt=REASON_PROMPT,
        act_prompt=ACT_PROMPT,
        k=1,
        max_steps=3,
    )

    train_result = agent.train_sync(OneStepEnvironment(), "sync training goal")
    assert train_result.success, "train_sync() should succeed"

    before_run_db_size = len(agent.database)
    run_result = agent.run_sync(OneStepEnvironment(), "sync inference goal")
    assert run_result.success, "run_sync() should succeed"
    assert len(agent.database) == before_run_db_size, "run_sync() must not add data"


def run_seed_and_verification_examples(db_path: Path) -> None:
    seed = Trajectory(
        goal="seeded example goal",
        plan="1. done",
        steps=[Step(observation="start", reasoning="finish", action="done")],
        success=True,
    )

    verified_goals: list[str] = []

    def verify_trajectory(trajectory: Trajectory) -> bool:
        verified_goals.append(trajectory.goal)
        return "accept" in trajectory.goal.lower()

    agent = Agent(
        llm=AlwaysDoneLLM(),
        db_path=str(db_path),
        plan_prompt=PLAN_PROMPT,
        reason_prompt=REASON_PROMPT,
        act_prompt=ACT_PROMPT,
        seed_trajectories=[seed],
        verify_trajectory=verify_trajectory,
        k=1,
        max_steps=3,
    )

    assert len(agent.database) == 1, "seed trajectory should be loaded at init"

    accepted = agent.train_sync(OneStepEnvironment(), "accept this trajectory")
    assert accepted.success
    after_accept = len(agent.database)

    rejected = agent.train_sync(OneStepEnvironment(), "reject this trajectory")
    assert rejected.success
    assert len(agent.database) == after_accept, "rejected trajectory should not store"

    assert verified_goals == [
        "accept this trajectory",
        "reject this trajectory",
    ]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        asyncio.run(run_async_api_examples(root / "async_db"))
        run_sync_api_examples(root / "sync_db")
        run_seed_and_verification_examples(root / "seed_db")

    print("Agent API walkthrough passed.")


if __name__ == "__main__":
    main()
