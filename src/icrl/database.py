"""Trajectory database with filesystem storage and FAISS indexing."""

import json
import os
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from icrl._debug import log as _debug_log
from icrl.embedder import default_embedder
from icrl.models import CodeArtifact, CurationMetadata, DeferredValidation, StepExample, Trajectory
from icrl.protocols import Embedder


class TrajectoryDatabase:
    """Database for storing and retrieving trajectories.

    Trajectories are stored as JSON files on the filesystem.
    FAISS is used for efficient vector similarity search.
    """

    def __init__(
        self,
        path: str | Path,
        embedder: Embedder | None = None,
    ) -> None:
        """Initialize the trajectory database.

        Args:
            path: Directory path for storing trajectories and index.
            embedder: Embedder for generating trajectory embeddings.
                     If None, creates a SentenceTransformerEmbedder.
        """
        self._path = Path(path)
        self._path.mkdir(parents=True, exist_ok=True)

        self._embedder = embedder or default_embedder()
        self._embedder_meta = {
            "id": (
                f"{type(self._embedder).__module__}:{type(self._embedder).__qualname__}"
            ),
            "dimension": int(self._embedder.dimension),
        }
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

    def _truncate_for_embedding(self, text: str) -> str:
        """Truncate text before embedding to keep compute bounded."""
        max_chars = int(os.environ.get("ICRL_EMBED_TEXT_CHARS", "2000"))
        if max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text
        return text[:max_chars]

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

        # Load embedder metadata (if present) to decide whether persisted
        # indexes are valid.
        meta_file = self._path / "embedder.json"
        stored_meta: dict[str, object] | None = None
        if meta_file.exists():
            try:
                with open(meta_file) as f:
                    stored_meta = json.load(f)
            except Exception:
                stored_meta = None

        meta_matches = (
            isinstance(stored_meta, dict)
            and stored_meta.get("id") == self._embedder_meta["id"]
            and stored_meta.get("dimension") == self._embedder_meta["dimension"]
        )

        index_file = self._path / "index.faiss"
        ids_file = self._path / "index_ids.json"
        if index_file.exists() and ids_file.exists() and meta_matches:
            self._index = faiss.read_index(str(index_file))  # type: ignore[assignment]
            with open(ids_file) as f:
                id_list = json.load(f)
                self._id_to_idx = {id_: idx for idx, id_ in enumerate(id_list)}
                self._idx_to_id = {idx: id_ for idx, id_ in enumerate(id_list)}
            # Always rebuild step index from trajectories (not persisted)
            self._build_step_index()
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
            # region agent log (debug-mode)
            _debug_log(
                hypothesis_id="H1",
                location="src/icrl/database.py:TrajectoryDatabase._save_index",
                message="db_save_index",
                data={
                    "pid": os.getpid(),
                    "db_path": str(self._path),
                    "index_ntotal": int(getattr(self._index, "ntotal", 0)),
                    "ids_count": len(self._idx_to_id),
                },
            )
            # endregion agent log (debug-mode)
            index_file = self._path / "index.faiss"
            faiss.write_index(self._index, str(index_file))  # type: ignore[assignment]

            ids_file = self._path / "index_ids.json"
            id_list = [self._idx_to_id[i] for i in range(len(self._idx_to_id))]
            with open(ids_file, "w") as f:
                json.dump(id_list, f)

            # Persist which embedder produced this index so we can detect mismatches.
            meta_file = self._path / "embedder.json"
            with open(meta_file, "w") as f:
                json.dump(self._embedder_meta, f, indent=2)

    def _save_curation(self) -> None:
        """Save curation metadata to disk."""
        # region agent log (debug-mode)
        _debug_log(
            hypothesis_id="H1",
            location="src/icrl/database.py:TrajectoryDatabase._save_curation",
            message="db_save_curation",
            data={
                "pid": os.getpid(),
                "db_path": str(self._path),
                "curation_count": len(self._curation_metadata),
            },
        )
        # endregion agent log (debug-mode)
        curation_file = self._path / "curation.json"
        # Use mode='json' to ensure datetime objects are serialized as ISO strings
        curation_data = [meta.model_dump(mode='json') for meta in self._curation_metadata.values()]
        with open(curation_file, "w") as f:
            json.dump(curation_data, f, indent=2)

    def _build_step_index(self) -> None:
        """Build the step-level index from loaded trajectories."""
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
                step_texts.append(
                    self._truncate_for_embedding(f"{step.observation}\n{step.reasoning}")
                )

        if step_texts:
            step_embeddings = self._embedder.embed(step_texts)
            step_embeddings_np = np.array(step_embeddings, dtype=np.float32)
            faiss.normalize_L2(step_embeddings_np)
            self._step_index = faiss.IndexFlatIP(step_embeddings_np.shape[1])  # type: ignore[assignment]
            self._step_index.add(step_embeddings_np)  # type: ignore[call-arg]
        else:
            self._step_index = faiss.IndexFlatIP(self._embedder.dimension)  # type: ignore[assignment]

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
            texts.append(self._truncate_for_embedding(self._get_embedding_text(traj)))
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
                step_texts.append(
                    self._truncate_for_embedding(f"{step.observation}\n{step.reasoning}")
                )

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

    def add(
        self,
        trajectory: Trajectory,
        working_dir: Path | str | None = None,
        extract_artifacts: bool = True,
    ) -> None:
        """Add a trajectory to the database.

        Args:
            trajectory: The trajectory to add.
            working_dir: Working directory for code artifact extraction.
                        If None, uses current directory.
            extract_artifacts: Whether to extract code artifacts for
                             deferred validation. Default True.
        """
        self._trajectories[trajectory.id] = trajectory
        self._save_trajectory(trajectory)

        # Create or update curation metadata
        if trajectory.id not in self._curation_metadata:
            self._curation_metadata[trajectory.id] = CurationMetadata(
                trajectory_id=trajectory.id
            )

        # Extract code artifacts if requested
        if extract_artifacts:
            artifacts = self._extract_code_artifacts(
                trajectory, working_dir or Path.cwd()
            )
            if artifacts:
                self._curation_metadata[trajectory.id].code_artifacts = artifacts
                # Check for superseded trajectories
                self._handle_supersession(trajectory.id, artifacts)

        self._save_curation()

        # Add to trajectory-level index
        text = self._get_embedding_text(trajectory)
        embedding = self._embedder.embed_single(self._truncate_for_embedding(text))
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
            step_text = self._truncate_for_embedding(
                f"{step.observation}\n{step.reasoning}"
            )
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

    def search(
        self,
        query: str,
        k: int = 3,
        include_deprecated: bool = False,
    ) -> list[Trajectory]:
        """Search for similar trajectories (legacy, trajectory-level).

        Args:
            query: The query string to search for.
            k: Number of results to return.
            include_deprecated: Whether to include deprecated trajectories.
                              Default False (only return active trajectories).

        Returns:
            List of most similar trajectories.
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        embedding = self._embedder.embed_single(self._truncate_for_embedding(query))
        embedding_np = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_np)

        # Request more results than k to account for filtering
        search_k = min(k * 3, self._index.ntotal) if not include_deprecated else k
        search_k = min(search_k, self._index.ntotal)
        _, indices = self._index.search(embedding_np, search_k)  # type: ignore[call-arg]

        results = []
        for idx in indices[0]:
            if len(results) >= k:
                break
            if idx >= 0 and idx in self._idx_to_id:
                traj_id = self._idx_to_id[idx]
                if traj_id in self._trajectories:
                    # Check if deprecated
                    if not include_deprecated:
                        meta = self._curation_metadata.get(traj_id)
                        if meta and meta.is_deprecated:
                            continue
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

        embedding = self._embedder.embed_single(self._truncate_for_embedding(query))
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

    # -------------------------------------------------------------------------
    # Code Artifact Extraction and Deferred Validation
    # -------------------------------------------------------------------------

    def _extract_code_artifacts(
        self,
        trajectory: Trajectory,
        working_dir: Path | str,
    ) -> list[CodeArtifact]:
        """Extract code artifacts from a trajectory.

        Args:
            trajectory: The trajectory to extract artifacts from.
            working_dir: The working directory where changes were made.

        Returns:
            List of CodeArtifact objects.
        """
        # Import here to avoid circular imports
        from icrl.validators.code import extract_code_artifacts

        return extract_code_artifacts(trajectory, working_dir)

    def _handle_supersession(
        self,
        new_trajectory_id: str,
        new_artifacts: list[CodeArtifact],
    ) -> list[str]:
        """Handle supersession of old trajectories by a new one.

        A trajectory is superseded when a newer trajectory modifies the
        same content (detected via content_snippet overlap). Simply editing
        the same file is NOT enough - the edits must touch the same code.

        Args:
            new_trajectory_id: ID of the new trajectory.
            new_artifacts: Code artifacts from the new trajectory.

        Returns:
            List of trajectory IDs that were superseded.
        """
        if not new_artifacts:
            return []

        superseded: list[str] = []

        for traj_id, meta in self._curation_metadata.items():
            if traj_id == new_trajectory_id:
                continue
            if meta.is_deprecated:
                continue
            if not meta.code_artifacts:
                continue

            # Check for content overlap, not just file overlap
            has_overlap = False
            for new_art in new_artifacts:
                for old_art in meta.code_artifacts:
                    # Must be same file
                    if new_art.file_path != old_art.file_path:
                        continue

                    # Check if the content snippets overlap
                    # This catches cases where the new edit modifies code
                    # that was introduced by the old edit
                    if old_art.content_snippet and new_art.content_snippet:
                        # If the old snippet appears in the new edit's context,
                        # or vice versa, they're touching the same code
                        old_lines = set(old_art.content_snippet.splitlines())
                        new_lines = set(new_art.content_snippet.splitlines())

                        # Check for significant line overlap (at least 2 lines)
                        common_lines = old_lines & new_lines
                        significant_lines = [l for l in common_lines if len(l.strip()) > 10]
                        if len(significant_lines) >= 2:
                            has_overlap = True
                            break

                if has_overlap:
                    break

            if has_overlap:
                meta.deprecate(
                    reason="superseded",
                    superseded_by=new_trajectory_id,
                )
                superseded.append(traj_id)

                _debug_log(
                    hypothesis_id="H1",
                    location="src/icrl/database.py:TrajectoryDatabase._handle_supersession",
                    message="trajectory_superseded",
                    data={
                        "old_trajectory_id": traj_id,
                        "new_trajectory_id": new_trajectory_id,
                    },
                )

        if superseded:
            self._save_curation()

        return superseded

    def validate_trajectory(
        self,
        trajectory_id: str,
        working_dir: Path | str | None = None,
    ) -> DeferredValidation | None:
        """Validate a trajectory's code persistence.

        Args:
            trajectory_id: ID of the trajectory to validate.
            working_dir: Working directory for validation.
                        If None, uses the working_dir from artifacts.

        Returns:
            DeferredValidation result, or None if trajectory not found
            or has no code artifacts.
        """
        meta = self._curation_metadata.get(trajectory_id)
        if not meta or not meta.code_artifacts:
            return None

        trajectory = self._trajectories.get(trajectory_id)
        if not trajectory:
            return None

        # Import validator
        from icrl.validators.code import CodePersistenceValidator

        # Determine working directory
        if working_dir:
            wd = Path(working_dir)
        elif meta.code_artifacts:
            wd = Path(meta.code_artifacts[0].working_dir)
        else:
            wd = Path.cwd()

        validator = CodePersistenceValidator(working_dir=wd)
        validation = validator.validate(
            trajectory,
            meta.code_artifacts,
            context={"working_dir": str(wd)},
        )

        # Record the validation
        meta.add_validation(validation)
        self._save_curation()

        return validation

    def validate_all(
        self,
        working_dir: Path | str | None = None,
        include_deprecated: bool = False,
    ) -> list[tuple[str, DeferredValidation]]:
        """Validate all trajectories with code artifacts.

        Args:
            working_dir: Working directory for validation.
            include_deprecated: Whether to validate deprecated trajectories.

        Returns:
            List of (trajectory_id, validation) tuples.
        """
        results: list[tuple[str, DeferredValidation]] = []

        for traj_id, meta in self._curation_metadata.items():
            if not include_deprecated and meta.is_deprecated:
                continue
            if not meta.code_artifacts:
                continue

            validation = self.validate_trajectory(traj_id, working_dir)
            if validation:
                results.append((traj_id, validation))

        return results

    def get_superseded_trajectories(self) -> list[tuple[str, str]]:
        """Get all superseded trajectories.

        Returns:
            List of (superseded_id, superseded_by_id) tuples.
        """
        return [
            (meta.trajectory_id, meta.superseded_by)
            for meta in self._curation_metadata.values()
            if meta.is_deprecated and meta.superseded_by
        ]

    def get_deprecated_trajectories(self) -> list[CurationMetadata]:
        """Get all deprecated trajectories.

        Returns:
            List of CurationMetadata for deprecated trajectories.
        """
        return [
            meta
            for meta in self._curation_metadata.values()
            if meta.is_deprecated
        ]

    def get_active_trajectories(self) -> list[Trajectory]:
        """Get all non-deprecated trajectories.

        Returns:
            List of active (non-deprecated) trajectories.
        """
        active_ids = {
            meta.trajectory_id
            for meta in self._curation_metadata.values()
            if not meta.is_deprecated
        }
        return [
            traj
            for traj_id, traj in self._trajectories.items()
            if traj_id in active_ids or traj_id not in self._curation_metadata
        ]
