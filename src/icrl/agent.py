"""Main Agent class for ICRL."""

import asyncio
import copy
from collections.abc import Callable
from typing import cast

from icrl.curation import CurationManager
from icrl.database import TrajectoryDatabase
from icrl.loop import ReActLoop
from icrl.models import Step, StepContext, Trajectory
from icrl.protocols import Environment, LLMProvider
from icrl.retriever import TrajectoryRetriever


class Agent:
    """ICRL Agent that learns from self-generated trajectories.

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
        verify_trajectory: Callable[[Trajectory], bool] | None = None,
    ) -> None:
        """Initialize the ICRL Agent.

        Args:
            llm: The LLM provider for generating completions.
            db_path: Path to the trajectory database directory.
            plan_prompt: Template for planning prompts.
                        Placeholders: {goal}, {examples}
            reason_prompt: Template for reasoning prompts.
                          Placeholders: {goal}, {plan}, {observation},
                          {history}, {examples}
            act_prompt: Template for action prompts.
                       Placeholders: {goal}, {plan}, {reasoning}, {history}, {examples}
            k: Number of examples to retrieve at each decision point.
            max_steps: Maximum number of steps per episode.
            seed_trajectories: Initial trajectories to populate the database.
            on_step: Optional callback called after each step.
            curation_threshold: Utility threshold below which trajectories are pruned.
            curation_min_retrievals: Minimum retrievals before a trajectory
                can be pruned.
            verify_trajectory: Optional callback to verify a trajectory before storing.
                If provided, called with the trajectory after a successful run.
                Return True to store the trajectory, False to discard it.
                If None, trajectories are stored automatically (no verification).
        """
        self._llm = llm
        self._db_path = db_path
        self._plan_prompt = plan_prompt
        self._reason_prompt = reason_prompt
        self._act_prompt = act_prompt
        self._k = k
        self._max_steps = max_steps
        self._on_step = on_step
        self._verify_trajectory = verify_trajectory
        self._curation_threshold = curation_threshold
        self._curation_min_retrievals = curation_min_retrievals

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
        and used as examples for future episodes. If a verify_trajectory
        callback was provided, it will be called to confirm before storing.

        Args:
            env: The environment to interact with.
            goal: The goal description.

        Returns:
            The resulting trajectory.
        """
        trajectory = await self._loop.run(env, goal)

        if trajectory.success:
            # Check verification callback if provided
            should_store = True
            if self._verify_trajectory is not None:
                should_store = self._verify_trajectory(trajectory)

            if should_store:
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
        return await self._loop.run(env, goal, record_retrieval_result=False)

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
        mini_batch_size: int = 1,
    ) -> list[Trajectory]:
        """Train on multiple goals.

        Note: Environments are created fresh for each goal using the factory.

        Args:
            env_factory: A callable that returns a new environment instance.
            goals: List of goal descriptions.
            mini_batch_size: Maximum number of concurrent episodes. Training
                uses shared mutable state, so values above 1 are not supported.

        Returns:
            List of resulting trajectories.
        """
        mini_batch_size = self._validate_mini_batch_size(mini_batch_size)
        if mini_batch_size != 1:
            raise ValueError(
                "Parallel mini-batches are only supported for run_batch() in "
                "inference/test mode."
            )

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
        mini_batch_size: int = 1,
    ) -> list[Trajectory]:
        """Run inference on multiple goals.

        Note: Environments are created fresh for each goal using the factory.

        Args:
            env_factory: A callable that returns a new environment instance.
            goals: List of goal descriptions.
            mini_batch_size: Maximum number of concurrent episodes to run.

        Returns:
            List of resulting trajectories.
        """
        mini_batch_size = self._validate_mini_batch_size(mini_batch_size)
        if not goals:
            return []

        if mini_batch_size == 1:
            trajectories = []
            for goal in goals:
                env = env_factory()
                trajectory = await self.run(env, goal)
                trajectories.append(trajectory)
            return trajectories

        semaphore = asyncio.Semaphore(mini_batch_size)
        results = cast(list[Trajectory | None], [None] * len(goals))

        async def _run_goal(index: int, goal: str) -> None:
            async with semaphore:
                env = env_factory()
                batch_agent = self._create_isolated_batch_agent()
                results[index] = await batch_agent.run(env, goal)

        await asyncio.gather(
            *(_run_goal(index, goal) for index, goal in enumerate(goals))
        )
        return [trajectory for trajectory in results if trajectory is not None]

    def _validate_mini_batch_size(self, mini_batch_size: int) -> int:
        """Validate and normalize batch concurrency values."""
        if mini_batch_size < 1:
            raise ValueError("mini_batch_size must be >= 1")
        return mini_batch_size

    def _create_isolated_batch_agent(self) -> "Agent":
        """Create a fresh agent instance for concurrent inference work."""
        return Agent(
            llm=self._clone_llm_provider(),
            db_path=self._db_path,
            plan_prompt=self._plan_prompt,
            reason_prompt=self._reason_prompt,
            act_prompt=self._act_prompt,
            k=self._k,
            max_steps=self._max_steps,
            on_step=self._on_step,
            curation_threshold=self._curation_threshold,
            curation_min_retrievals=self._curation_min_retrievals,
            verify_trajectory=self._verify_trajectory,
        )

    def _clone_llm_provider(self) -> LLMProvider:
        """Best-effort clone for known providers used in concurrent batches."""
        clone = getattr(self._llm, "clone", None)
        if callable(clone):
            return clone()

        from icrl.providers import AnthropicVertexProvider, LiteLLMProvider

        if isinstance(self._llm, LiteLLMProvider):
            return LiteLLMProvider(
                model=self._llm._model,
                temperature=self._llm._temperature,
                max_tokens=self._llm._max_tokens,
                system_prompt=self._llm._system_prompt,
                **self._llm._kwargs,
            )

        if isinstance(self._llm, AnthropicVertexProvider):
            return AnthropicVertexProvider(
                model=self._llm._model,
                temperature=self._llm._temperature,
                max_tokens=self._llm._max_tokens,
                system_prompt=self._llm._system_prompt,
                project_id=self._llm.project_id,
                location=self._llm.location,
                **self._llm._kwargs,
            )

        try:
            return copy.deepcopy(self._llm)
        except Exception:
            return self._llm

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
