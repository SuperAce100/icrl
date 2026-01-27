"""Code persistence validator for ICRL trajectories.

This validator checks whether code changes from trajectories persisted
in the codebase, providing implicit feedback about trajectory quality.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from icrl.models import CodeArtifact, DeferredValidation, Trajectory


# Maximum length of content snippet to store for matching
SNIPPET_MAX_LENGTH = 500


def extract_code_artifacts(
    trajectory: Trajectory,
    working_dir: Path | str,
) -> list[CodeArtifact]:
    """Extract code change artifacts from a trajectory's steps.

    Parses Write and Edit actions from the trajectory and creates
    CodeArtifact objects that can be used for persistence validation.

    Args:
        trajectory: The trajectory to extract artifacts from.
        working_dir: The working directory where the changes were made.

    Returns:
        List of CodeArtifact objects representing code changes.
    """
    working_dir = Path(working_dir).resolve()
    artifacts: list[CodeArtifact] = []

    for step in trajectory.steps:
        action = step.action

        # Parse Write actions: Write({"path": "...", "content": "..."})
        write_artifact = _parse_write_action(action, working_dir)
        if write_artifact:
            artifacts.append(write_artifact)
            continue

        # Parse Edit actions: Edit({"path": "...", "old_text": "...", "new_text": "..."})
        edit_artifact = _parse_edit_action(action, working_dir)
        if edit_artifact:
            artifacts.append(edit_artifact)

    return artifacts


def _parse_write_action(
    action: str,
    working_dir: Path,
) -> CodeArtifact | None:
    """Parse a Write action and create a CodeArtifact."""
    # Match Write({"path": "...", "content": "..."})
    # The JSON may span multiple lines
    match = re.match(r"Write\((\{.*\})\)", action, re.DOTALL)
    if not match:
        return None

    try:
        params = json.loads(match.group(1))
        path = params.get("path", "")
        content = params.get("content", "")

        if not path or not content:
            return None

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        snippet = content[:SNIPPET_MAX_LENGTH]

        return CodeArtifact(
            file_path=path,
            change_type="write",
            content_hash=content_hash,
            working_dir=str(working_dir),
            content_snippet=snippet,
        )
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None


def _parse_edit_action(
    action: str,
    working_dir: Path,
) -> CodeArtifact | None:
    """Parse an Edit action and create a CodeArtifact."""
    # Match Edit({"path": "...", "old_text": "...", "new_text": "..."})
    match = re.match(r"Edit\((\{.*\})\)", action, re.DOTALL)
    if not match:
        return None

    try:
        params = json.loads(match.group(1))
        path = params.get("path", "")
        new_text = params.get("new_text", "")

        if not path or not new_text:
            return None

        content_hash = hashlib.sha256(new_text.encode()).hexdigest()
        snippet = new_text[:SNIPPET_MAX_LENGTH]

        return CodeArtifact(
            file_path=path,
            change_type="edit",
            content_hash=content_hash,
            working_dir=str(working_dir),
            content_snippet=snippet,
        )
    except (json.JSONDecodeError, TypeError, AttributeError):
        return None


class CodePersistenceValidator:
    """Validates that code changes from trajectories persisted in the codebase.

    Uses line-based content comparison to determine if changes made by a
    trajectory are still present in the codebase.
    """

    validator_type: str = "code_persistence"

    def __init__(self, working_dir: Path | str | None = None):
        """Initialize the validator.

        Args:
            working_dir: Default working directory for validation.
                        Can be overridden per-validation via context.
        """
        self._working_dir = Path(working_dir) if working_dir else None

    def validate(
        self,
        trajectory: Trajectory,
        artifacts: list[CodeArtifact],
        context: dict[str, Any] | None = None,
    ) -> DeferredValidation:
        """Validate whether code changes from a trajectory persisted.

        Args:
            trajectory: The trajectory to validate.
            artifacts: Code artifacts extracted from the trajectory.
            context: Optional context with 'working_dir' override.

        Returns:
            DeferredValidation with persistence score and details.
        """
        if not artifacts:
            return DeferredValidation(
                validator_type=self.validator_type,
                score=1.0,
                reason="no_code_artifacts",
                details={"artifact_count": 0},
            )

        # Determine working directory
        if context and "working_dir" in context:
            working_dir = Path(context["working_dir"])
        elif self._working_dir:
            working_dir = self._working_dir
        elif artifacts:
            # Use working_dir from first artifact
            working_dir = Path(artifacts[0].working_dir)
        else:
            working_dir = Path.cwd()

        # Validate each artifact
        artifact_results: list[dict[str, Any]] = []
        scores: list[float] = []

        for artifact in artifacts:
            result = self._validate_artifact(artifact, working_dir)
            artifact_results.append(result)
            scores.append(result["score"])

        # Compute overall score (average of artifact scores)
        avg_score = sum(scores) / len(scores) if scores else 1.0

        # Determine overall status
        intact_count = sum(1 for r in artifact_results if r["status"] == "intact")
        modified_count = sum(1 for r in artifact_results if r["status"] == "modified")
        removed_count = sum(1 for r in artifact_results if r["status"] == "removed")

        if intact_count == len(artifacts):
            reason = "all_changes_intact"
        elif removed_count == len(artifacts):
            reason = "all_changes_removed"
        elif removed_count > 0:
            reason = "some_changes_removed"
        elif modified_count > 0:
            reason = "some_changes_modified"
        else:
            reason = "mixed_results"

        return DeferredValidation(
            validator_type=self.validator_type,
            score=avg_score,
            reason=reason,
            details={
                "artifact_count": len(artifacts),
                "intact_count": intact_count,
                "modified_count": modified_count,
                "removed_count": removed_count,
                "artifact_results": artifact_results,
            },
        )

    def _validate_artifact(
        self,
        artifact: CodeArtifact,
        working_dir: Path,
    ) -> dict[str, Any]:
        """Validate a single code artifact.

        Both writes and edits are treated the same way:
        1. Check if content hash matches exactly (100% persistence)
        2. If not, compute line-based similarity to see how much persisted

        Returns:
            Dict with 'status', 'score', and 'message' keys.
        """
        file_path = working_dir / artifact.file_path

        # Check if file exists
        if not file_path.exists():
            return {
                "file_path": artifact.file_path,
                "status": "removed",
                "score": 0.0,
                "message": "File no longer exists",
            }

        try:
            current_content = file_path.read_text()
        except (OSError, UnicodeDecodeError) as e:
            return {
                "file_path": artifact.file_path,
                "status": "error",
                "score": 0.5,
                "message": f"Error reading file: {e}",
            }

        # Check if content hash matches exactly (applies to both writes and edits)
        current_hash = hashlib.sha256(current_content.encode()).hexdigest()
        if current_hash == artifact.content_hash:
            return {
                "file_path": artifact.file_path,
                "status": "intact",
                "score": 1.0,
                "message": "Content unchanged",
            }

        # Content has changed - compute how much of our content persisted
        # Use line-based similarity for both writes and edits
        score = self._compute_content_persistence(
            artifact.content_snippet, current_content
        )

        # Determine status based on score
        if score > 0.8:
            status = "intact"
            message = f"Content mostly preserved ({score:.0%})"
        elif score > 0.3:
            status = "modified"
            message = f"Content partially preserved ({score:.0%})"
        else:
            status = "removed"
            message = f"Content largely replaced ({score:.0%})"

        return {
            "file_path": artifact.file_path,
            "status": status,
            "score": score,
            "message": message,
        }

    def _compute_content_persistence(self, snippet: str, current_content: str) -> float:
        """Compute how much of the original content persisted.

        Uses line-based matching: checks what fraction of non-trivial lines
        from the original snippet are still present in the current content.

        This works for both writes and edits - we check how much of what
        we wrote/edited is still there.

        Args:
            snippet: The content snippet from the original write/edit (first N chars).
            current_content: The current file content.

        Returns:
            Float between 0.0 and 1.0 representing persistence ratio.
        """
        if not snippet:
            return 0.5  # No snippet to check, assume neutral

        # Get non-trivial lines (ignore empty lines and very short lines)
        snippet_lines = [
            line.strip() 
            for line in snippet.splitlines() 
            if line.strip() and len(line.strip()) > 3  # Ignore trivial lines like "}", ")"
        ]
        
        if not snippet_lines:
            return 0.5  # No meaningful lines to check

        # Count how many lines are still present in current content
        matches = sum(1 for line in snippet_lines if line in current_content)
        
        return matches / len(snippet_lines)


def find_superseded_trajectories(
    new_artifacts: list[CodeArtifact],
    all_curation_metadata: dict[str, "CurationMetadata"],
) -> list[str]:
    """Find trajectories that may be superseded by new code changes.

    A trajectory is superseded if a newer trajectory modifies the same files.

    Args:
        new_artifacts: Artifacts from the new trajectory.
        all_curation_metadata: Dict mapping trajectory_id to CurationMetadata.

    Returns:
        List of trajectory IDs that are superseded.
    """
    # Import here to avoid circular import
    from icrl.models import CurationMetadata  # noqa: F811

    new_files = {a.file_path for a in new_artifacts}
    if not new_files:
        return []

    superseded: list[str] = []

    for traj_id, meta in all_curation_metadata.items():
        if meta.is_deprecated:
            continue  # Already deprecated

        old_files = {a.file_path for a in meta.code_artifacts}
        overlap = new_files & old_files

        if overlap:
            superseded.append(traj_id)

    return superseded
