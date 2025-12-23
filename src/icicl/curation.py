"""Automatic curation for trajectory databases."""

from icicl.database import TrajectoryDatabase


class CurationManager:
    """Manages automatic curation of trajectory databases.

    Implements exemplar-level curation from the SGICL paper:
    - Tracks which trajectories are retrieved and whether they lead to success
    - Periodically prunes trajectories with low utility scores
    """

    def __init__(
        self,
        database: TrajectoryDatabase,
        threshold: float = 0.3,
        min_retrievals: int = 5,
        curate_every: int = 10,
    ) -> None:
        """Initialize the curation manager.

        Args:
            database: The trajectory database to curate.
            threshold: Utility score threshold below which trajectories are pruned.
            min_retrievals: Minimum number of times a trajectory must be retrieved
                           before it can be considered for pruning.
            curate_every: Run curation after this many successful episodes.
        """
        self._database = database
        self._threshold = threshold
        self._min_retrievals = min_retrievals
        self._curate_every = curate_every
        self._episodes_since_curation = 0

    def maybe_curate(self) -> bool:
        """Check if curation should run and run it if so.

        Returns:
            True if curation was performed, False otherwise.
        """
        self._episodes_since_curation += 1

        if self._episodes_since_curation >= self._curate_every:
            self.curate()
            self._episodes_since_curation = 0
            return True

        return False

    def curate(self) -> list[str]:
        """Run curation to prune low-utility trajectories.

        Returns:
            List of trajectory IDs that were removed.
        """
        removed_ids: list[str] = []

        for trajectory in self._database.get_all():
            metadata = self._database.get_curation_metadata(trajectory.id)

            if metadata is None:
                continue

            if metadata.times_retrieved < self._min_retrievals:
                continue

            if metadata.utility_score < self._threshold:
                if self._database.remove(trajectory.id):
                    removed_ids.append(trajectory.id)

        return removed_ids

    def get_utility_scores(self) -> dict[str, float]:
        """Get utility scores for all trajectories.

        Returns:
            Dictionary mapping trajectory IDs to their utility scores.
        """
        scores = {}
        for trajectory in self._database.get_all():
            metadata = self._database.get_curation_metadata(trajectory.id)
            if metadata:
                scores[trajectory.id] = metadata.utility_score
        return scores

    def get_low_utility_trajectories(self) -> list[str]:
        """Get trajectory IDs that would be pruned if curation ran now.

        Returns:
            List of trajectory IDs with low utility.
        """
        low_utility = []

        for trajectory in self._database.get_all():
            metadata = self._database.get_curation_metadata(trajectory.id)

            if metadata is None:
                continue

            if metadata.times_retrieved < self._min_retrievals:
                continue

            if metadata.utility_score < self._threshold:
                low_utility.append(trajectory.id)

        return low_utility
