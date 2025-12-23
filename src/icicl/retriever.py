"""Trajectory retriever for in-context learning."""

from icicl.database import TrajectoryDatabase
from icicl.models import Trajectory


class TrajectoryRetriever:
    """Retriever for finding relevant trajectories as in-context examples.

    Following the paper, retrieves different examples at each decision point
    based on relevance to the current situation.
    """

    def __init__(self, database: TrajectoryDatabase, k: int = 3) -> None:
        """Initialize the retriever.

        Args:
            database: The trajectory database to search.
            k: Default number of examples to retrieve.
        """
        self._database = database
        self._k = k
        self._retrieved_ids: list[str] = []

    def retrieve_for_plan(self, goal: str, k: int | None = None) -> list[Trajectory]:
        """Retrieve examples for planning phase.

        Args:
            goal: The goal description.
            k: Number of examples to retrieve. Uses default if None.

        Returns:
            List of relevant trajectories.
        """
        k = k or self._k
        trajectories = self._database.search(goal, k=k)
        self._track_retrieved(trajectories)
        return trajectories

    def retrieve_for_step(
        self,
        goal: str,
        plan: str,
        observation: str,
        k: int | None = None,
    ) -> list[Trajectory]:
        """Retrieve examples for a reasoning/acting step.

        Args:
            goal: The goal description.
            plan: The current plan.
            observation: The current observation.
            k: Number of examples to retrieve. Uses default if None.

        Returns:
            List of relevant trajectories.
        """
        k = k or self._k
        query = f"{goal}\n{plan}\n{observation}"
        trajectories = self._database.search(query, k=k)
        self._track_retrieved(trajectories)
        return trajectories

    def _track_retrieved(self, trajectories: list[Trajectory]) -> None:
        """Track which trajectories were retrieved for later curation."""
        for traj in trajectories:
            if traj.id not in self._retrieved_ids:
                self._retrieved_ids.append(traj.id)

    def get_retrieved_ids(self) -> list[str]:
        """Get all trajectory IDs retrieved in this session.

        Returns:
            List of trajectory IDs.
        """
        return list(self._retrieved_ids)

    def clear_retrieved(self) -> None:
        """Clear the list of retrieved trajectory IDs."""
        self._retrieved_ids = []

    def record_episode_result(self, success: bool) -> None:
        """Record the result of the episode for curation.

        Args:
            success: Whether the episode was successful.
        """
        if self._retrieved_ids:
            self._database.record_retrieval(self._retrieved_ids, success)
        self.clear_retrieved()

