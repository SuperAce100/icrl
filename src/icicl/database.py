"""Trajectory database with filesystem storage and FAISS indexing."""

import json
from pathlib import Path

import faiss
import numpy as np

from icicl.embedder import SentenceTransformerEmbedder
from icicl.models import CurationMetadata, StepExample, Trajectory


class TrajectoryDatabase:
    """Database for storing and retrieving trajectories.

    Trajectories are stored as JSON files on the filesystem.
    FAISS is used for efficient vector similarity search.
    """

    def __init__(
        self,
        path: str | Path,
        embedder: SentenceTransformerEmbedder | None = None,
    ) -> None:
        """Initialize the trajectory database.

        Args:
            path: Directory path for storing trajectories and index.
            embedder: Embedder for generating trajectory embeddings.
                     If None, creates a SentenceTransformerEmbedder.
        """
        self._path = Path(path)
        self._path.mkdir(parents=True, exist_ok=True)

        self._embedder = embedder or SentenceTransformerEmbedder()
        self._trajectories: dict[str, Trajectory] = {}
        self._curation_metadata: dict[str, CurationMetadata] = {}
        # Legacy trajectory-level index (kept for compatibility)
        self._index: faiss.IndexFlatIP | None = None  # type: ignore[assignment]
        self._id_to_idx: dict[str, int] = {}
        self._idx_to_id: dict[int, str] = {}
        # Step-level index for fine-grained retrieval
        self._step_index: faiss.IndexFlatIP | None = None  # type: ignore[assignment]
        self._step_examples: list[StepExample] = []

        self._load()

    def _load(self) -> None:
        """Load trajectories and index from disk."""
        trajectories_dir = self._path / "trajectories"
        if trajectories_dir.exists():
            for traj_file in trajectories_dir.glob("*.json"):
                with open(traj_file) as f:
                    data = json.load(f)
                    traj = Trajectory.model_validate(data)
                    self._trajectories[traj.id] = traj

        curation_file = self._path / "curation.json"
        if curation_file.exists():
            with open(curation_file) as f:
                curation_data = json.load(f)
                for item in curation_data:
                    meta = CurationMetadata.model_validate(item)
                    self._curation_metadata[meta.trajectory_id] = meta

        index_file = self._path / "index.faiss"
        ids_file = self._path / "index_ids.json"
        if index_file.exists() and ids_file.exists():
            self._index = faiss.read_index(str(index_file))  # type: ignore[assignment]
            with open(ids_file) as f:
                id_list = json.load(f)
                self._id_to_idx = {id_: idx for idx, id_ in enumerate(id_list)}
                self._idx_to_id = {idx: id_ for idx, id_ in enumerate(id_list)}
        else:
            self._rebuild_index()

    def _save_trajectory(self, trajectory: Trajectory) -> None:
        """Save a single trajectory to disk."""
        trajectories_dir = self._path / "trajectories"
        trajectories_dir.mkdir(exist_ok=True)
        traj_file = trajectories_dir / f"{trajectory.id}.json"
        with open(traj_file, "w") as f:
            json.dump(trajectory.model_dump(), f, indent=2)

    def _save_index(self) -> None:
        """Save the FAISS index to disk."""
        if self._index is not None:
            index_file = self._path / "index.faiss"
            faiss.write_index(self._index, str(index_file))  # type: ignore[assignment]

            ids_file = self._path / "index_ids.json"
            id_list = [self._idx_to_id[i] for i in range(len(self._idx_to_id))]
            with open(ids_file, "w") as f:
                json.dump(id_list, f)

    def _save_curation(self) -> None:
        """Save curation metadata to disk."""
        curation_file = self._path / "curation.json"
        curation_data = [meta.model_dump() for meta in self._curation_metadata.values()]
        with open(curation_file, "w") as f:
            json.dump(curation_data, f, indent=2)

    def _rebuild_index(self) -> None:
        """Rebuild both trajectory-level and step-level FAISS indexes."""
        if not self._trajectories:
            self._index = faiss.IndexFlatIP(self._embedder.dimension)  # type: ignore[assignment]
            self._step_index = faiss.IndexFlatIP(self._embedder.dimension)  # type: ignore[assignment]
            self._id_to_idx = {}
            self._idx_to_id = {}
            self._step_examples = []
            return

        # Trajectory-level index (legacy)
        texts = []
        ids = []
        for traj_id, traj in self._trajectories.items():
            texts.append(self._get_embedding_text(traj))
            ids.append(traj_id)

        embeddings = self._embedder.embed(texts)
        embeddings_np = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_np)

        self._index = faiss.IndexFlatIP(embeddings_np.shape[1])  # type: ignore[assignment]
        self._index.add(embeddings_np)  # type: ignore[call-arg]

        self._id_to_idx = {id_: idx for idx, id_ in enumerate(ids)}
        self._idx_to_id = {idx: id_ for idx, id_ in enumerate(ids)}

        # Step-level index for fine-grained retrieval
        self._step_examples = []
        step_texts = []
        for traj_id, traj in self._trajectories.items():
            for step_idx, step in enumerate(traj.steps):
                step_ex = StepExample(
                    goal=traj.goal,
                    plan=traj.plan,
                    observation=step.observation,
                    reasoning=step.reasoning,
                    action=step.action,
                    trajectory_id=traj_id,
                    step_index=step_idx,
                )
                self._step_examples.append(step_ex)
                # Index on observation + reasoning for step-level similarity
                step_texts.append(f"{step.observation}\n{step.reasoning}")

        if step_texts:
            step_embeddings = self._embedder.embed(step_texts)
            step_embeddings_np = np.array(step_embeddings, dtype=np.float32)
            faiss.normalize_L2(step_embeddings_np)
            self._step_index = faiss.IndexFlatIP(step_embeddings_np.shape[1])  # type: ignore[assignment]
            self._step_index.add(step_embeddings_np)  # type: ignore[call-arg]
        else:
            self._step_index = faiss.IndexFlatIP(self._embedder.dimension)  # type: ignore[assignment]

        self._save_index()

    def _get_embedding_text(self, trajectory: Trajectory) -> str:
        """Get the text to embed for a trajectory."""
        return f"{trajectory.goal}\n{trajectory.plan}"

    def add(self, trajectory: Trajectory) -> None:
        """Add a trajectory to the database.

        Args:
            trajectory: The trajectory to add.
        """
        self._trajectories[trajectory.id] = trajectory
        self._save_trajectory(trajectory)

        if trajectory.id not in self._curation_metadata:
            self._curation_metadata[trajectory.id] = CurationMetadata(
                trajectory_id=trajectory.id
            )
            self._save_curation()

        # Add to trajectory-level index
        text = self._get_embedding_text(trajectory)
        embedding = self._embedder.embed_single(text)
        embedding_np = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_np)

        if self._index is None:
            self._index = faiss.IndexFlatIP(len(embedding))  # type: ignore[assignment]

        idx = self._index.ntotal
        self._index.add(embedding_np)  # type: ignore[call-arg]
        self._id_to_idx[trajectory.id] = idx
        self._idx_to_id[idx] = trajectory.id

        # Add steps to step-level index
        if self._step_index is None:
            self._step_index = faiss.IndexFlatIP(len(embedding))  # type: ignore[assignment]

        for step_idx, step in enumerate(trajectory.steps):
            step_ex = StepExample(
                goal=trajectory.goal,
                plan=trajectory.plan,
                observation=step.observation,
                reasoning=step.reasoning,
                action=step.action,
                trajectory_id=trajectory.id,
                step_index=step_idx,
            )
            self._step_examples.append(step_ex)
            step_text = f"{step.observation}\n{step.reasoning}"
            step_emb = self._embedder.embed_single(step_text)
            step_emb_np = np.array([step_emb], dtype=np.float32)
            faiss.normalize_L2(step_emb_np)
            self._step_index.add(step_emb_np)  # type: ignore[call-arg]

        self._save_index()

    def get(self, trajectory_id: str) -> Trajectory | None:
        """Get a trajectory by ID.

        Args:
            trajectory_id: The ID of the trajectory to retrieve.

        Returns:
            The trajectory if found, None otherwise.
        """
        return self._trajectories.get(trajectory_id)

    def search(self, query: str, k: int = 3) -> list[Trajectory]:
        """Search for similar trajectories (legacy, trajectory-level).

        Args:
            query: The query string to search for.
            k: Number of results to return.

        Returns:
            List of most similar trajectories.
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        embedding = self._embedder.embed_single(query)
        embedding_np = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_np)

        k = min(k, self._index.ntotal)
        _, indices = self._index.search(embedding_np, k)  # type: ignore[call-arg]

        results = []
        for idx in indices[0]:
            if idx >= 0 and idx in self._idx_to_id:
                traj_id = self._idx_to_id[idx]
                if traj_id in self._trajectories:
                    results.append(self._trajectories[traj_id])

        return results

    def search_steps(self, query: str, k: int = 3) -> list[StepExample]:
        """Search for similar steps (step-level retrieval).

        Args:
            query: The query string (typically observation or reasoning context).
            k: Number of step examples to return.

        Returns:
            List of most similar step examples with their trajectory context.
        """
        if self._step_index is None or self._step_index.ntotal == 0:
            return []

        embedding = self._embedder.embed_single(query)
        embedding_np = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_np)

        k = min(k, self._step_index.ntotal)
        _, indices = self._step_index.search(embedding_np, k)  # type: ignore[call-arg]

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self._step_examples):
                results.append(self._step_examples[idx])

        return results

    def record_retrieval(self, trajectory_ids: list[str], led_to_success: bool) -> None:
        """Record that trajectories were retrieved and whether they led to success.

        Args:
            trajectory_ids: IDs of trajectories that were retrieved.
            led_to_success: Whether the episode using these trajectories succeeded.
        """
        for traj_id in trajectory_ids:
            if traj_id in self._curation_metadata:
                meta = self._curation_metadata[traj_id]
                meta.times_retrieved += 1
                if led_to_success:
                    meta.times_led_to_success += 1
                meta.update_utility()

        self._save_curation()

    def get_all(self) -> list[Trajectory]:
        """Get all trajectories in the database.

        Returns:
            List of all trajectories.
        """
        return list(self._trajectories.values())

    def __len__(self) -> int:
        """Return the number of trajectories in the database."""
        return len(self._trajectories)

    def get_curation_metadata(self, trajectory_id: str) -> CurationMetadata | None:
        """Get curation metadata for a trajectory.

        Args:
            trajectory_id: The ID of the trajectory.

        Returns:
            The curation metadata if found, None otherwise.
        """
        return self._curation_metadata.get(trajectory_id)

    def remove(self, trajectory_id: str) -> bool:
        """Remove a trajectory from the database.

        Args:
            trajectory_id: The ID of the trajectory to remove.

        Returns:
            True if the trajectory was removed, False if it wasn't found.
        """
        if trajectory_id not in self._trajectories:
            return False

        del self._trajectories[trajectory_id]
        if trajectory_id in self._curation_metadata:
            del self._curation_metadata[trajectory_id]

        traj_file = self._path / "trajectories" / f"{trajectory_id}.json"
        if traj_file.exists():
            traj_file.unlink()

        self._rebuild_index()
        self._save_curation()

        return True
