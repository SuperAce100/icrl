"""Harbor-compatible ICICL agents.

This module provides agents for use with the Harbor CLI:
- ICICLTrainAgent: Training mode that stores successful trajectories
- ICICLTestAgent: Evaluation mode with frozen database
- ICICLZeroShotAgent: Zero-shot baseline (no retrieval)

Example usage:
    # Training
    harbor run -d "swebench-verified@1.0.0" \
        --agent-import-path icicl.harbor.agents:ICICLTrainAgent

    # Evaluation
    harbor run -d "swebench-verified@1.0.0" \
        --agent-import-path icicl.harbor.agents:ICICLTestAgent

    # Zero-shot baseline
    harbor run -d "swebench-verified@1.0.0" \
        --agent-import-path icicl.harbor.agents:ICICLZeroShotAgent
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import litellm
from dotenv import load_dotenv
from harbor.agents.base import BaseAgent

from icicl import Agent, LiteLLMProvider, Step, StepContext
from icicl.harbor.adapter import HarborEnvironmentAdapter
from icicl.harbor.prompts import (
    ACT_PROMPT,
    PLAN_PROMPT,
    REASON_PROMPT,
    SYSTEM_PROMPT,
)

# Drop unsupported params for newer models like GPT-5
litellm.drop_params = True

if TYPE_CHECKING:
    from harbor.models.agent.context import AgentContext
    from harbor.environments.base import BaseEnvironment

load_dotenv()


def _get_db_path() -> str:
    """Get the trajectory database path from environment or default."""
    default_path = Path.home() / ".icicl" / "trajectories"
    return os.environ.get("ICICL_DB_PATH", str(default_path))


def _get_model() -> str:
    """Get the LLM model from environment or default."""
    return os.environ.get("MODEL", "gpt-5")


def _get_k() -> int:
    """Get the number of examples to retrieve from environment or default."""
    # Keep default small to reduce prompt size / embedding overhead.
    return int(os.environ.get("ICICL_K", "1"))


def _get_max_completion_tokens() -> int:
    """Get the maximum completion tokens per LLM call (output budget)."""
    # ReAct prompts expect short outputs (plans/reasoning/commands), so keep this
    # conservative by default to avoid provider-side validation errors.
    return int(os.environ.get("ICICL_MAX_COMPLETION_TOKENS", "2048"))


def _get_max_steps() -> int:
    """Get the maximum steps per episode from environment or default."""
    return int(os.environ.get("ICICL_MAX_STEPS", "100"))


def _create_step_callback(
    context: AgentContext,
    trajectory_log: list[dict],
    mode: str = "train",
):
    """Create a step callback that populates the Harbor AgentContext.

    Args:
        context: The Harbor AgentContext to populate.
        trajectory_log: List to accumulate step information.
        mode: Agent mode ("train", "test", "zero-shot").

    Returns:
        A callback function for each step.
    """
    # Initialize metadata immediately so we have something even on early timeout
    # Note: Don't reference trajectory_log directly, it will be copied on each step
    context.metadata = {
        "icicl_success": False,  # Updated when agent finishes
        "icicl_plan": None,
        "icicl_steps": 0,
        "icicl_mode": mode,
        "trajectory": [],  # Will be updated with copies in callback
    }

    def callback(step: Step, step_context: StepContext) -> None:
        """Record step information to the trajectory log."""
        step_data = {
            "observation": step.observation[:500] if step.observation else "",
            "reasoning": step.reasoning or "",
            "action": step.action or "",
            "examples_used": len(step_context.examples),
        }
        trajectory_log.append(step_data)

        # Update context incrementally so we capture data even on timeout
        meta = context.metadata or {}
        meta["icicl_steps"] = len(trajectory_log)
        meta["trajectory"] = trajectory_log.copy()
        context.metadata = meta

    return callback


class ICICLTrainAgent(BaseAgent):
    """ICICL agent in training mode.

    This agent stores successful trajectories to a persistent database,
    building up a library of examples for future retrieval.

    Environment variables:
        ICICL_DB_PATH: Path to trajectory database (default: ~/.icicl/trajectories)
        MODEL: LLM model to use (default: gpt-5)
        ICICL_K: Number of examples to retrieve (default: 3)
        ICICL_MAX_STEPS: Maximum steps per episode (default: 100)
    """

    @staticmethod
    def name() -> str:
        """Return the agent name."""
        return "icicl-train"

    def version(self) -> str | None:
        """Return the agent version."""
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Set up the agent (no-op for ICICL)."""
        pass

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Run the agent in training mode.

        Successful trajectories are stored to the database for future retrieval.

        Args:
            instruction: The task instruction/goal.
            environment: The Harbor environment.
            context: The Harbor agent context to populate.
        """
        db_path = _get_db_path()
        model = _get_model()
        k = _get_k()
        max_steps = _get_max_steps()

        # Initialize the LLM provider with system prompt
        # GPT-5 only supports temperature=1, use 0.3 for other models
        temp = 1.0 if "gpt-5" in model.lower() else 0.3
        llm = LiteLLMProvider(
            model=model,
            temperature=temp,
            max_tokens=_get_max_completion_tokens(),
            system_prompt=SYSTEM_PROMPT,
        )

        trajectory_log: list[dict] = []

        agent = Agent(
            llm=llm,
            db_path=db_path,
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=k,
            max_steps=max_steps,
            on_step=_create_step_callback(context, trajectory_log, mode="train"),
        )

        adapter = HarborEnvironmentAdapter(
            environment=environment,
            max_actions=max_steps + 10,
            timeout_sec=180,
        )

        # Run in training mode - only stores when agent signals completion (submit)
        trajectory = await agent.train(adapter, instruction)

        # Update metadata with final values (only runs if no timeout)
        if context.metadata is None:
            context.metadata = {}
        context.metadata.update(
            {
                "icicl_success": trajectory.success,
                "icicl_plan": trajectory.plan,
                "icicl_steps": len(trajectory.steps),
                "icicl_db_trajectories": agent.get_stats()["total_trajectories"],
                "icicl_stored": trajectory.success,  # Only stored if agent submitted
                "trajectory": trajectory_log,
            }
        )


class ICICLZeroShotAgent(BaseAgent):
    """ICICL agent in zero-shot mode (no retrieval, no storage).

    This agent serves as a baseline - it uses the same prompts and ReAct loop
    but does NOT retrieve examples or store trajectories.

    Environment variables:
        MODEL: LLM model to use (default: gpt-5)
        ICICL_MAX_STEPS: Maximum steps per episode (default: 100)
    """

    @staticmethod
    def name() -> str:
        """Return the agent name."""
        return "icicl-zeroshot"

    def version(self) -> str | None:
        """Return the agent version."""
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Set up the agent (no-op for ICICL)."""
        pass

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Run the agent in zero-shot mode (no retrieval).

        Args:
            instruction: The task instruction/goal.
            environment: The Harbor environment.
            context: The Harbor agent context to populate.
        """
        model = _get_model()
        max_steps = _get_max_steps()

        # Use a temporary empty database (no retrieval)
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_db_path = f"{tmpdir}/empty_db"

            temp = 1.0 if "gpt-5" in model.lower() else 0.3
            llm = LiteLLMProvider(
                model=model,
                temperature=temp,
                max_tokens=_get_max_completion_tokens(),
                system_prompt=SYSTEM_PROMPT,
            )

            trajectory_log: list[dict] = []

            agent = Agent(
                llm=llm,
                db_path=temp_db_path,
                plan_prompt=PLAN_PROMPT,
                reason_prompt=REASON_PROMPT,
                act_prompt=ACT_PROMPT,
                k=0,  # NO retrieval - zero-shot baseline
                max_steps=max_steps,
                on_step=_create_step_callback(
                    context, trajectory_log, mode="zero-shot"
                ),
            )

            adapter = HarborEnvironmentAdapter(
                environment=environment,
                max_actions=max_steps + 10,
                timeout_sec=180,
            )

            trajectory = await agent.run(adapter, instruction)

            # Update metadata with final values (only runs if no timeout)
            if context.metadata is None:
                context.metadata = {}
            context.metadata.update(
                {
                    "icicl_success": trajectory.success,
                    "icicl_plan": trajectory.plan,
                    "icicl_steps": len(trajectory.steps),
                    "icicl_k": 0,
                }
            )


class ICICLTestAgent(BaseAgent):
    """ICICL agent in evaluation/test mode.

    This agent uses a frozen database for retrieval without storing
    new trajectories. Use this for benchmarking after training.

    Environment variables:
        ICICL_DB_PATH: Path to trajectory database (default: ~/.icicl/trajectories)
        MODEL: LLM model to use (default: gpt-5)
        ICICL_K: Number of examples to retrieve (default: 3)
        ICICL_MAX_STEPS: Maximum steps per episode (default: 100)
    """

    @staticmethod
    def name() -> str:
        """Return the agent name."""
        return "icicl-test"

    def version(self) -> str | None:
        """Return the agent version."""
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Set up the agent (no-op for ICICL)."""
        pass

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Run the agent in evaluation mode.

        The database is frozen - trajectories are retrieved but not stored.

        Args:
            instruction: The task instruction/goal.
            environment: The Harbor environment.
            context: The Harbor agent context to populate.
        """
        db_path = _get_db_path()
        model = _get_model()
        k = _get_k()
        max_steps = _get_max_steps()

        temp = 1.0 if "gpt-5" in model.lower() else 0.3
        llm = LiteLLMProvider(
            model=model,
            temperature=temp,
            max_tokens=_get_max_completion_tokens(),
            system_prompt=SYSTEM_PROMPT,
        )

        trajectory_log: list[dict] = []

        agent = Agent(
            llm=llm,
            db_path=db_path,
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=k,
            max_steps=max_steps,
            on_step=_create_step_callback(context, trajectory_log, mode="test"),
        )

        adapter = HarborEnvironmentAdapter(
            environment=environment,
            max_actions=max_steps + 10,
            timeout_sec=180,
        )

        # Record retrieved examples for analysis
        initial_examples = agent.database.search(instruction, k=k)
        retrieved_example_info = {
            "count": len(initial_examples),
            "goals": [ex.goal[:100] for ex in initial_examples],
        }

        # Run in evaluation mode (frozen database)
        trajectory = await agent.run(adapter, instruction)

        # Update metadata with final values (only runs if no timeout)
        if context.metadata is None:
            context.metadata = {}
        context.metadata.update(
            {
                "icicl_success": trajectory.success,
                "icicl_plan": trajectory.plan,
                "icicl_steps": len(trajectory.steps),
                "icicl_db_trajectories": agent.get_stats()["total_trajectories"],
                "icicl_retrieved_examples": retrieved_example_info,
            }
        )
