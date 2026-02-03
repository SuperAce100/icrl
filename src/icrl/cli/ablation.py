"""Ablation mode for comparing runs with and without in-context examples.

This module provides functionality to run the same task in parallel:
1. With retrieved in-context examples (current behavior)
2. Without in-context examples (baseline)

This allows measuring the impact of the trajectory database on task performance.
"""

import asyncio
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from icrl.cli.config import Config, get_project_db_path
from icrl.cli.runner import AgentRunner, SimpleCallbacks
from icrl.models import Trajectory


@dataclass
class AblationResult:
    """Results from a single ablation run."""

    trajectory: Trajectory
    with_examples: bool
    examples_count: int
    db_size: int

    @property
    def success(self) -> bool:
        return self.trajectory.success

    @property
    def steps_count(self) -> int:
        return len(self.trajectory.steps)

    @property
    def stats(self) -> dict[str, Any]:
        return self.trajectory.metadata.get("stats", {})

    @property
    def total_tokens(self) -> int:
        return self.stats.get("total_tokens", 0)

    @property
    def prompt_tokens(self) -> int:
        return self.stats.get("total_prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        return self.stats.get("total_completion_tokens", 0)

    @property
    def latency_s(self) -> float:
        return self.stats.get("total_latency_ms", 0) / 1000

    @property
    def final_response(self) -> str:
        return self.trajectory.metadata.get("final_response", "")


@dataclass
class AblationComparison:
    """Comparison of two ablation runs."""

    with_examples: AblationResult
    without_examples: AblationResult
    llm_analysis: str = ""  # LLM-generated analysis of differences


def is_git_repo(path: Path) -> bool:
    """Check if the given path is inside a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def get_git_root(path: Path) -> Path | None:
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def has_uncommitted_changes(path: Path) -> bool:
    """Check if there are uncommitted changes in the repository."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def create_worktree(git_root: Path, worktree_path: Path, branch_name: str) -> bool:
    """Create a git worktree at the specified path.

    Args:
        git_root: Root of the git repository
        worktree_path: Path where the worktree should be created
        branch_name: Name for the temporary branch

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current HEAD commit
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False
        commit = result.stdout.strip()

        # Create worktree with detached HEAD at current commit
        result = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree_path), commit],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def remove_worktree(git_root: Path, worktree_path: Path) -> bool:
    """Remove a git worktree.

    Args:
        git_root: Root of the git repository
        worktree_path: Path to the worktree to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        # Force remove the worktree
        result = subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


class AblationRunner:
    """Runs ablation studies comparing with/without in-context examples."""

    def __init__(
        self,
        config: Config,
        working_dir: Path,
        on_status: Callable[[str], None] | None = None,
    ):
        """Initialize the ablation runner.

        Args:
            config: Configuration for the runs
            working_dir: Base working directory (must be in a git repo)
            on_status: Callback for status updates (str) -> None
        """
        self._config = config
        self._working_dir = working_dir
        self._on_status = on_status or (lambda x: None)
        self._git_root: Path | None = None
        self._worktrees: list[Path] = []

    def _status(self, msg: str) -> None:
        """Report status update."""
        self._on_status(msg)

    def _validate_git_repo(self) -> bool:
        """Validate that we're in a git repository."""
        if not is_git_repo(self._working_dir):
            return False
        self._git_root = get_git_root(self._working_dir)
        return self._git_root is not None

    def _create_worktrees(self) -> tuple[Path, Path] | None:
        """Create two worktrees for the ablation study.

        Returns:
            Tuple of (with_examples_path, without_examples_path) or None on failure
        """
        if self._git_root is None:
            return None

        # Create worktrees in temp directory
        temp_base = Path(tempfile.gettempdir()) / "icrl-ablation"
        temp_base.mkdir(parents=True, exist_ok=True)

        run_id = uuid.uuid4().hex[:8]
        worktree_a = temp_base / f"with-examples-{run_id}"
        worktree_b = temp_base / f"without-examples-{run_id}"

        self._status("Creating worktree for run with examples...")
        if not create_worktree(self._git_root, worktree_a, f"ablation-a-{run_id}"):
            return None
        self._worktrees.append(worktree_a)

        self._status("Creating worktree for run without examples...")
        if not create_worktree(self._git_root, worktree_b, f"ablation-b-{run_id}"):
            # Clean up first worktree
            remove_worktree(self._git_root, worktree_a)
            self._worktrees.remove(worktree_a)
            return None
        self._worktrees.append(worktree_b)

        return worktree_a, worktree_b

    def _cleanup_worktrees(self) -> None:
        """Clean up all created worktrees."""
        if self._git_root is None:
            return

        for worktree in self._worktrees:
            self._status(f"Cleaning up worktree: {worktree.name}...")
            remove_worktree(self._git_root, worktree)

        self._worktrees.clear()

    async def _run_single(
        self,
        goal: str,
        working_dir: Path,
        use_examples: bool,
        callbacks: SimpleCallbacks | None = None,
    ) -> AblationResult:
        """Run a single agent with or without examples.

        Args:
            goal: The task to accomplish
            working_dir: Working directory for this run (e.g., worktree)
            use_examples: Whether to use in-context examples
            callbacks: Optional callbacks for progress

        Returns:
            AblationResult with trajectory and metadata
        """
        # Use the original project's database, not the worktree's
        # This ensures we retrieve examples from the project being ablated
        config = Config(
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            max_steps=self._config.max_steps,
            k=self._config.k,
            context_compression_threshold=self._config.context_compression_threshold,
            enable_prompt_caching=self._config.enable_prompt_caching,
            show_stats=self._config.show_stats,
            auto_approve=self._config.auto_approve,
            # Use the original project's database path
            db_path=str(get_project_db_path(self._working_dir)),
            vertex_credentials_path=self._config.vertex_credentials_path,
            vertex_project_id=self._config.vertex_project_id,
            vertex_location=self._config.vertex_location,
        )
        
        runner = AgentRunner(
            config=config,
            callbacks=callbacks,
            working_dir=working_dir,
        )

        trajectory = await runner.run(
            goal=goal,
            train=False,  # Never store ablation runs
            use_examples=use_examples,
        )

        return AblationResult(
            trajectory=trajectory,
            with_examples=use_examples,
            examples_count=runner.last_examples_count if use_examples else 0,
            db_size=runner.last_db_size,
        )

    async def run(
        self,
        goal: str,
        callbacks_with: SimpleCallbacks | None = None,
        callbacks_without: SimpleCallbacks | None = None,
    ) -> AblationComparison | None:
        """Run the ablation study.

        Args:
            goal: The task to accomplish
            callbacks_with: Callbacks for the run with examples
            callbacks_without: Callbacks for the run without examples

        Returns:
            AblationComparison with both results, or None on failure
        """
        # Validate git repo
        if not self._validate_git_repo():
            self._status("Error: Not in a git repository. Ablation mode requires git.")
            return None

        # Warn about uncommitted changes
        if has_uncommitted_changes(self._working_dir):
            self._status(
                "Warning: Uncommitted changes detected. "
                "Worktrees will only contain committed changes."
            )

        # Create worktrees
        worktrees = self._create_worktrees()
        if worktrees is None:
            self._status("Error: Failed to create worktrees.")
            return None

        worktree_with, worktree_without = worktrees

        try:
            self._status("Starting parallel runs...")

            # Run both in parallel
            results = await asyncio.gather(
                self._run_single(
                    goal=goal,
                    working_dir=worktree_with,
                    use_examples=True,
                    callbacks=callbacks_with,
                ),
                self._run_single(
                    goal=goal,
                    working_dir=worktree_without,
                    use_examples=False,
                    callbacks=callbacks_without,
                ),
                return_exceptions=True,
            )

            # Handle exceptions
            result_with, result_without = results

            if isinstance(result_with, Exception):
                self._status(f"Error in run with examples: {result_with}")
                return None
            if isinstance(result_without, Exception):
                self._status(f"Error in run without examples: {result_without}")
                return None

            return AblationComparison(
                with_examples=result_with,
                without_examples=result_without,
            )

        finally:
            # Always clean up worktrees
            self._cleanup_worktrees()

    async def analyze_comparison(
        self,
        comparison: AblationComparison,
        llm_provider: Any,
    ) -> str:
        """Use an LLM to analyze the differences between the two runs.

        Args:
            comparison: The ablation comparison results
            llm_provider: LLM provider with complete_text method

        Returns:
            LLM-generated analysis string
        """
        # Build analysis prompt
        with_result = comparison.with_examples
        without_result = comparison.without_examples

        prompt = f"""Analyze the differences between two runs of the same coding task.

## Task Goal
{with_result.trajectory.goal}

## Run A: WITH In-Context Examples ({with_result.examples_count} examples from {with_result.db_size} in database)
- Success: {with_result.success}
- Steps taken: {with_result.steps_count}
- Input tokens: {with_result.prompt_tokens:,}
- Output tokens: {with_result.completion_tokens:,}
- Latency: {with_result.latency_s:.1f}s

### Steps (Run A):
{self._format_steps(with_result.trajectory)}

### Final Response (Run A):
{with_result.final_response[:2000] if with_result.final_response else "(no response)"}

---

## Run B: WITHOUT In-Context Examples (baseline)
- Success: {without_result.success}
- Steps taken: {without_result.steps_count}
- Input tokens: {without_result.prompt_tokens:,}
- Output tokens: {without_result.completion_tokens:,}
- Latency: {without_result.latency_s:.1f}s

### Steps (Run B):
{self._format_steps(without_result.trajectory)}

### Final Response (Run B):
{without_result.final_response[:2000] if without_result.final_response else "(no response)"}

---

## Analysis Request

Please provide a concise analysis comparing these two runs:

1. **Outcome Comparison**: Did both succeed? If different outcomes, why?
2. **Efficiency**: Which was more efficient (fewer steps, less tokens)?
3. **Approach Differences**: Did the examples lead to a different problem-solving approach?
4. **Quality**: Any observable differences in the quality of the solution?
5. **Example Impact**: What specific impact did the in-context examples have (positive, negative, or neutral)?

Keep the analysis focused and actionable (2-3 paragraphs max).
"""

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert at analyzing AI agent behavior. "
                        "Provide concise, insightful analysis of ablation study results."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            analysis = await llm_provider.complete_text(messages)
            return analysis.strip()
        except Exception as e:
            return f"(Analysis failed: {e})"

    def _format_steps(self, trajectory: Trajectory, max_steps: int = 10) -> str:
        """Format trajectory steps for analysis prompt."""
        if not trajectory.steps:
            return "(no steps)"

        lines = []
        steps = trajectory.steps[:max_steps]
        for i, step in enumerate(steps, 1):
            # Extract tool name from action string like "Read({...})"
            action = step.action
            if "(" in action:
                tool_name = action.split("(")[0]
            else:
                tool_name = action[:50]
            lines.append(f"{i}. {tool_name}")

        if len(trajectory.steps) > max_steps:
            lines.append(f"   ... and {len(trajectory.steps) - max_steps} more steps")

        return "\n".join(lines)
