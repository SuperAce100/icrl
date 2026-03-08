"""Tests for inference mini-batches in the core agent and Harbor adapter."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, cast

from icrl import Agent, Step, Trajectory
from icrl.harbor.adapter import HarborEnvironmentAdapter, HarborTrial
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
    """Deterministic provider that completes in a single action."""

    async def complete(self, messages: list[Message]) -> str:
        prompt = messages[-1].content.lower() if messages else ""
        if "action:" in prompt:
            return "done"
        if "think:" in prompt:
            return "Finish immediately."
        return "1. Finish with `done`."


@dataclass
class ConcurrencyTracker:
    """Track how many trial executions overlap."""

    active: int = 0
    max_active: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def start(self) -> None:
        async with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)

    async def finish(self) -> None:
        async with self.lock:
            self.active -= 1


class SlowOneStepEnvironment:
    """One-step environment with goal-dependent async latency."""

    def __init__(self, tracker: ConcurrencyTracker, delays: dict[str, float]) -> None:
        self._tracker = tracker
        self._delays = delays
        self._goal = ""

    def reset(self, goal: str) -> str:
        self._goal = goal
        return f"Goal: {goal}"

    async def step(self, action: str) -> tuple[str, bool, bool]:
        await self._tracker.start()
        try:
            await asyncio.sleep(self._delays[self._goal])
        finally:
            await self._tracker.finish()
        return f"Executed: {action}", True, action == "done"


@dataclass(slots=True)
class FakeExecResult:
    """Minimal Harbor exec result shape."""

    stdout: str = ""
    stderr: str = ""
    return_code: int = 0


class FakeHarborEnvironment:
    """Tiny Harbor-like environment for adapter tests."""

    def __init__(self, tracker: ConcurrencyTracker, delays: dict[str, float]) -> None:
        self._tracker = tracker
        self._delays = delays
        self._goal = ""

    async def exec(self, command: str, timeout_sec: int) -> FakeExecResult:
        del timeout_sec
        goal = self._goal or command.removeprefix("echo ").strip()
        await self._tracker.start()
        try:
            await asyncio.sleep(self._delays[goal])
        finally:
            await self._tracker.finish()
        return FakeExecResult(stdout=f"{goal}:{command}")


class FakeHarborBatchAgent:
    """Simple agent that exercises the adapter command path."""

    async def run(
        self, env: HarborEnvironmentAdapter, goal: str
    ) -> Trajectory:
        initial_observation = env.reset(goal)
        command = f"echo {goal}"
        command_observation, done, success = await env.step(command)
        assert not done
        assert not success
        _, done, success = await env.step("submit")
        return Trajectory(
            goal=goal,
            plan="1. Run one command\n2. submit",
            steps=[
                Step(
                    observation=initial_observation,
                    reasoning="Run a command first.",
                    action=command,
                ),
                Step(
                    observation=command_observation,
                    reasoning="Finish once the command succeeds.",
                    action="submit",
                ),
            ],
            success=done and success,
        )


def _make_agent(db_path: str, *, k: int = 1) -> Agent:
    return Agent(
        llm=AlwaysDoneLLM(),
        db_path=db_path,
        plan_prompt=PLAN_PROMPT,
        reason_prompt=REASON_PROMPT,
        act_prompt=ACT_PROMPT,
        k=k,
        max_steps=3,
    )


def test_run_batch_mini_batch_parallelizes_and_preserves_order(tmp_path) -> None:
    async def run_test() -> None:
        tracker = ConcurrencyTracker()
        goals = ["slow", "fast", "medium"]
        delays = {
            "slow": 0.12,
            "fast": 0.02,
            "medium": 0.06,
        }

        agent = _make_agent(str(tmp_path / "parallel_db"), k=0)

        def env_factory() -> SlowOneStepEnvironment:
            return SlowOneStepEnvironment(tracker, delays)

        trajectories = await agent.run_batch(
            env_factory,
            goals,
            mini_batch_size=2,
        )

        assert [trajectory.goal for trajectory in trajectories] == goals
        assert all(trajectory.success for trajectory in trajectories)
        assert tracker.max_active == 2

    asyncio.run(run_test())


def test_run_batch_keeps_test_mode_database_frozen(tmp_path) -> None:
    async def run_test() -> None:
        seed = Trajectory(
            goal="seed goal",
            plan="1. done",
            steps=[Step(observation="start", reasoning="finish", action="done")],
            success=True,
        )
        agent = Agent(
            llm=AlwaysDoneLLM(),
            db_path=str(tmp_path / "frozen_db"),
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            seed_trajectories=[seed],
            k=1,
            max_steps=3,
        )

        before = agent.database.get_curation_metadata(seed.id)
        assert before is not None
        before_counts = (before.times_retrieved, before.times_led_to_success)

        trajectories = await agent.run_batch(
            lambda: SlowOneStepEnvironment(
                ConcurrencyTracker(),
                {"goal a": 0.0, "goal b": 0.0},
            ),
            ["goal a", "goal b"],
            mini_batch_size=2,
        )

        after = agent.database.get_curation_metadata(seed.id)
        assert after is not None
        assert all(trajectory.success for trajectory in trajectories)
        assert len(agent.database) == 1
        assert (after.times_retrieved, after.times_led_to_success) == before_counts

    asyncio.run(run_test())


def test_train_batch_rejects_parallel_mini_batches(tmp_path) -> None:
    async def run_test() -> None:
        agent = _make_agent(str(tmp_path / "train_db"), k=0)

        try:
            await agent.train_batch(
                lambda: SlowOneStepEnvironment(ConcurrencyTracker(), {"goal": 0.0}),
                ["goal"],
                mini_batch_size=2,
            )
        except ValueError as exc:
            assert "run_batch" in str(exc)
        else:
            raise AssertionError("train_batch should reject parallel mini-batches")

    asyncio.run(run_test())


def test_harbor_adapter_run_test_mini_batch_parallelizes() -> None:
    async def run_test() -> None:
        tracker = ConcurrencyTracker()
        goals = ["trial slow", "trial fast", "trial medium"]
        delays = {
            "trial slow": 0.12,
            "trial fast": 0.02,
            "trial medium": 0.06,
        }

        trials = [
            HarborTrial(
                instruction=goal,
                environment=cast(
                    Any,
                    FakeHarborEnvironment(tracker, delays),
                ),
            )
            for goal in goals
        ]

        trajectories = await HarborEnvironmentAdapter.run_test_mini_batch(
            trials,
            lambda: cast(Any, FakeHarborBatchAgent()),
            mini_batch_size=2,
            timeout_sec=5,
        )

        assert [trajectory.goal for trajectory in trajectories] == goals
        assert all(trajectory.success for trajectory in trajectories)
        assert tracker.max_active == 2

    previous = os.environ.get("ICRL_HARBOR_VERIFY_ON_SUBMIT")
    os.environ["ICRL_HARBOR_VERIFY_ON_SUBMIT"] = "0"
    try:
        asyncio.run(run_test())
    finally:
        if previous is None:
            os.environ.pop("ICRL_HARBOR_VERIFY_ON_SUBMIT", None)
        else:
            os.environ["ICRL_HARBOR_VERIFY_ON_SUBMIT"] = previous
