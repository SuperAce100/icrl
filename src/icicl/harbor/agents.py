"""Harbor-compatible ICICL agents.

This module provides two agents for use with the Harbor CLI:
- ICICLTrainAgent: Training mode that stores successful trajectories
- ICICLTestAgent: Evaluation mode with frozen database

Example usage:
    # Training
    harbor run -d "swebench-verified@1.0.0" \
        --agent-import-path icicl.harbor.agents:ICICLTrainAgent

    # Evaluation
    harbor run -d "swebench-verified@1.0.0" \
        --agent-import-path icicl.harbor.agents:ICICLTestAgent
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from harbor.agents.base import BaseAgent

from icicl import Agent, LiteLLMProvider, Step, StepContext
from icicl.harbor.adapter import HarborEnvironmentAdapter
from icicl.harbor.prompts import ACT_PROMPT, PLAN_PROMPT, REASON_PROMPT

if TYPE_CHECKING:
    from harbor.agents.context import AgentContext
    from harbor.environments.base import BaseEnvironment

load_dotenv()


def _get_db_path() -> str:
    """Get the trajectory database path from environment or default."""
    default_path = Path.home() / ".icicl" / "trajectories"
    return os.environ.get("ICICL_DB_PATH", str(default_path))


def _get_model() -> str:
    """Get the LLM model from environment or default."""
    return os.environ.get("MODEL", "gpt-4o-mini")


def _get_k() -> int:
    """Get the number of examples to retrieve from environment or default."""
    return int(os.environ.get("ICICL_K", "3"))


def _get_max_steps() -> int:
    """Get the maximum steps per episode from environment or default."""
    return int(os.environ.get("ICICL_MAX_STEPS", "30"))


def _create_step_callback(context: AgentContext, trajectory_log: list[dict]):
    """Create a step callback that populates the Harbor AgentContext.

    Args:
        context: The Harbor AgentContext to populate.
        trajectory_log: List to accumulate step information.

    Returns:
        A callback function for each step.
    """

    def callback(step: Step, step_context: StepContext) -> None:
        """Record step information to the trajectory log."""
        trajectory_log.append(
            {
                "observation": step.observation[:500],  # Truncate for storage
                "reasoning": step.reasoning,
                "action": step.action,
                "examples_used": len(step_context.examples),
            }
        )

    return callback


class ICICLTrainAgent(BaseAgent):
    """ICICL agent in training mode.

    This agent stores successful trajectories to a persistent database,
    building up a library of examples for future retrieval.

    Environment variables:
        ICICL_DB_PATH: Path to trajectory database (default: ~/.icicl/trajectories)
        MODEL: LLM model to use (default: gpt-4o-mini)
        ICICL_K: Number of examples to retrieve (default: 3)
        ICICL_MAX_STEPS: Maximum steps per episode (default: 30)
    """

    @staticmethod
    def name() -> str:
        """Return the agent name."""
        return "icicl-train"

    def version(self) -> str | None:
        """Return the agent version."""
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Set up the agent (no-op for ICICL).

        Args:
            environment: The Harbor environment.
        """
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

        # Initialize the LLM provider
        llm = LiteLLMProvider(
            model=model,
            temperature=0.3,
            max_tokens=1000,
        )

        # Log for collecting trajectory steps
        trajectory_log: list[dict] = []

        # Create the ICICL agent
        agent = Agent(
            llm=llm,
            db_path=db_path,
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=k,
            max_steps=max_steps,
            on_step=_create_step_callback(context, trajectory_log),
        )

        # Wrap Harbor environment with our adapter
        adapter = HarborEnvironmentAdapter(
            environment=environment,
            max_actions=max_steps + 10,  # Allow some buffer
            timeout_sec=120,
        )

        # Run in training mode (stores successful trajectories)
        trajectory = await agent.train(adapter, instruction)

        # Populate Harbor context with results
        context.metadata = {
            "icicl_success": trajectory.success,
            "icicl_plan": trajectory.plan,
            "icicl_steps": len(trajectory.steps),
            "icicl_db_trajectories": agent.get_stats()["total_trajectories"],
            "icicl_stored": trajectory.success,
            "trajectory": trajectory_log,
        }
        context.rollout_details = trajectory_log


class ICICLTestAgent(BaseAgent):
    """ICICL agent in evaluation/test mode.

    This agent uses a frozen database for retrieval without storing
    new trajectories. Use this for benchmarking after training.

    Environment variables:
        ICICL_DB_PATH: Path to trajectory database (default: ~/.icicl/trajectories)
        MODEL: LLM model to use (default: gpt-4o-mini)
        ICICL_K: Number of examples to retrieve (default: 3)
        ICICL_MAX_STEPS: Maximum steps per episode (default: 30)
    """

    @staticmethod
    def name() -> str:
        """Return the agent name."""
        return "icicl-test"

    def version(self) -> str | None:
        """Return the agent version."""
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Set up the agent (no-op for ICICL).

        Args:
            environment: The Harbor environment.
        """
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

        # Initialize the LLM provider
        llm = LiteLLMProvider(
            model=model,
            temperature=0.3,
            max_tokens=1000,
        )

        # Log for collecting trajectory steps
        trajectory_log: list[dict] = []

        # Create the ICICL agent
        agent = Agent(
            llm=llm,
            db_path=db_path,
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=k,
            max_steps=max_steps,
            on_step=_create_step_callback(context, trajectory_log),
        )

        # Wrap Harbor environment with our adapter
        adapter = HarborEnvironmentAdapter(
            environment=environment,
            max_actions=max_steps + 10,
            timeout_sec=120,
        )

        # Record retrieved examples for analysis
        initial_examples = agent.database.search(instruction, k=k)
        retrieved_example_info = {
            "count": len(initial_examples),
            "goals": [ex.goal[:100] for ex in initial_examples],
        }

        # Run in evaluation mode (frozen database)
        trajectory = await agent.run(adapter, instruction)

        # Populate Harbor context with results
        context.metadata = {
            "icicl_success": trajectory.success,
            "icicl_plan": trajectory.plan,
            "icicl_steps": len(trajectory.steps),
            "icicl_db_trajectories": agent.get_stats()["total_trajectories"],
            "icicl_retrieved_examples": retrieved_example_info,
            "trajectory": trajectory_log,
        }
        context.rollout_details = trajectory_log

