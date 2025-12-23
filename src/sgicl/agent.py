"""Main Agent class for SGICL."""

import asyncio
from typing import Callable

from sgicl.curation import CurationManager
from sgicl.database import TrajectoryDatabase
from sgicl.loop import ReActLoop
from sgicl.models import Step, StepContext, Trajectory
from sgicl.protocols import Environment, LLMProvider
from sgicl.retriever import TrajectoryRetriever


class Agent:
    """SGICL Agent that learns from self-generated trajectories.

    This agent implements the Self-Generated In-Context Learning algorithm,
    which bootstraps performance by accumulating successful trajectories
    and using them as in-context examples for future tasks.
    """

    def __init__(
        self,
        llm: LLMProvider,
        db_path: str,
        plan_prompt: str,
        reason_prompt: str,
        act_prompt: str,
        k: int = 3,
        max_steps: int = 30,
        seed_trajectories: list[Trajectory] | None = None,
        on_step: Callable[[Step, StepContext], None] | None = None,
        curation_threshold: float = 0.3,
        curation_min_retrievals: int = 5,
    ) -> None:
        """Initialize the SGICL Agent.

        Args:
            llm: The LLM provider for generating completions.
            db_path: Path to the trajectory database directory.
            plan_prompt: Template for planning prompts.
                        Placeholders: {goal}, {examples}
            reason_prompt: Template for reasoning prompts.
                          Placeholders: {goal}, {plan}, {observation}, {history}, {examples}
            act_prompt: Template for action prompts.
                       Placeholders: {goal}, {plan}, {reasoning}, {history}, {examples}
            k: Number of examples to retrieve at each decision point.
            max_steps: Maximum number of steps per episode.
            seed_trajectories: Initial trajectories to populate the database.
            on_step: Optional callback called after each step.
            curation_threshold: Utility threshold below which trajectories are pruned.
            curation_min_retrievals: Minimum retrievals before a trajectory can be pruned.
        """
        self._llm = llm
        self._plan_prompt = plan_prompt
        self._reason_prompt = reason_prompt
        self._act_prompt = act_prompt
        self._k = k
        self._max_steps = max_steps
        self._on_step = on_step

        self._database = TrajectoryDatabase(db_path)

        if seed_trajectories:
            for traj in seed_trajectories:
                if traj.id not in [t.id for t in self._database.get_all()]:
                    self._database.add(traj)

        self._retriever = TrajectoryRetriever(self._database, k=k)

        self._curation = CurationManager(
            self._database,
            threshold=curation_threshold,
            min_retrievals=curation_min_retrievals,
        )

        self._loop = ReActLoop(
            llm=llm,
            retriever=self._retriever,
            plan_prompt=plan_prompt,
            reason_prompt=reason_prompt,
            act_prompt=act_prompt,
            max_steps=max_steps,
            on_step=on_step,
        )

    @property
    def database(self) -> TrajectoryDatabase:
        """Access the trajectory database."""
        return self._database

    async def train(self, env: Environment, goal: str) -> Trajectory:
        """Run a training episode.

        In training mode, successful trajectories are added to the database
        and used as examples for future episodes.

        Args:
            env: The environment to interact with.
            goal: The goal description.

        Returns:
            The resulting trajectory.
        """
        trajectory = await self._loop.run(env, goal)

        if trajectory.success:
            self._database.add(trajectory)
            self._curation.maybe_curate()

        return trajectory

    async def run(self, env: Environment, goal: str) -> Trajectory:
        """Run an inference episode.

        In inference mode, the database is frozen and trajectories are
        not added regardless of success.

        Args:
            env: The environment to interact with.
            goal: The goal description.

        Returns:
            The resulting trajectory.
        """
        return await self._loop.run(env, goal)

    def train_sync(self, env: Environment, goal: str) -> Trajectory:
        """Synchronous wrapper for train.

        Args:
            env: The environment to interact with.
            goal: The goal description.

        Returns:
            The resulting trajectory.
        """
        return asyncio.run(self.train(env, goal))

    def run_sync(self, env: Environment, goal: str) -> Trajectory:
        """Synchronous wrapper for run.

        Args:
            env: The environment to interact with.
            goal: The goal description.

        Returns:
            The resulting trajectory.
        """
        return asyncio.run(self.run(env, goal))

    async def train_batch(
        self,
        env_factory: Callable[[], Environment],
        goals: list[str],
    ) -> list[Trajectory]:
        """Train on multiple goals.

        Note: Environments are created fresh for each goal using the factory.

        Args:
            env_factory: A callable that returns a new environment instance.
            goals: List of goal descriptions.

        Returns:
            List of resulting trajectories.
        """
        trajectories = []
        for goal in goals:
            env = env_factory()
            trajectory = await self.train(env, goal)
            trajectories.append(trajectory)
        return trajectories

    async def run_batch(
        self,
        env_factory: Callable[[], Environment],
        goals: list[str],
    ) -> list[Trajectory]:
        """Run inference on multiple goals.

        Note: Environments are created fresh for each goal using the factory.

        Args:
            env_factory: A callable that returns a new environment instance.
            goals: List of goal descriptions.

        Returns:
            List of resulting trajectories.
        """
        trajectories = []
        for goal in goals:
            env = env_factory()
            trajectory = await self.run(env, goal)
            trajectories.append(trajectory)
        return trajectories

    def get_stats(self) -> dict[str, int | float]:
        """Get statistics about the agent's database.

        Returns:
            Dictionary with statistics.
        """
        all_trajs = self._database.get_all()
        successful = sum(1 for t in all_trajs if t.success)

        return {
            "total_trajectories": len(all_trajs),
            "successful_trajectories": successful,
            "success_rate": successful / len(all_trajs) if all_trajs else 0.0,
        }

