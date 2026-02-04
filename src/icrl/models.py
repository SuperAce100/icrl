"""Pydantic models for ICRL trajectories and messages."""

import os
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in an LLM conversation."""

    role: str
    content: str


class Step(BaseModel):
    """A single step in a trajectory."""

    observation: str
    reasoning: str
    action: str


class Trajectory(BaseModel):
    """A complete trajectory from an episode."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    plan: str
    steps: list[Step]
    success: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_example_string(self) -> str:
        """Convert trajectory to a string format suitable for in-context examples."""
        lines = [f"Goal: {self.goal}", f"Plan: {self.plan}", "Steps:"]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  Step {i}:")
            lines.append(f"    Observation: {step.observation}")
            lines.append(f"    Reasoning: {step.reasoning}")
            lines.append(f"    Action: {step.action}")
        lines.append(f"Success: {self.success}")
        return "\n".join(lines)


class StepContext(BaseModel):
    """Context available during a step for prompt formatting."""

    goal: str
    plan: str
    observation: str
    reasoning: str = ""
    history: list[Step] = Field(default_factory=list)
    examples: list["StepExample"] = Field(default_factory=list)

    def format_examples(self) -> str:
        """Format retrieved step examples as a string."""
        if not self.examples:
            return "(No similar examples found in database yet)"

        # Hard cap to prevent prompt explosions (esp. when actions contain patches).
        # Set ICRL_MAX_EXAMPLES_CHARS=-1 for unlimited.
        max_examples = int(os.environ.get("ICRL_MAX_EXAMPLES", "5"))
        max_chars = int(os.environ.get("ICRL_MAX_EXAMPLES_CHARS", "6000"))
        
        # max_examples <= 0 means no examples
        if max_examples <= 0:
            return "(No similar examples found in database yet)"
        
        # max_chars == -1 means unlimited
        unlimited_chars = max_chars == -1

        parts: list[str] = []
        total = 0
        omitted = 0

        considered = min(len(self.examples), max_examples)
        for ex in self.examples[:considered]:
            s = ex.to_example_string()
            if not unlimited_chars and total + len(s) > max_chars:
                omitted += 1
                continue
            parts.append(s)
            total += len(s)

        omitted += max(0, len(self.examples) - considered)
        if omitted > 0:
            parts.append(f"[{omitted} additional example(s) available]")

        return "\n\n".join(parts)

    def format_history(self) -> str:
        """Format step history as a string (truncated for context window)."""
        if not self.history:
            return "No previous steps."
        lines = []
        # Only show last 5 steps to keep context manageable
        recent = self.history[-5:] if len(self.history) > 5 else self.history
        start_idx = len(self.history) - len(recent) + 1
        if len(self.history) > 5:
            lines.append(f"[{len(self.history) - 5} earlier steps omitted]")
        for i, step in enumerate(recent, start_idx):
            # Truncate observation in history
            obs = step.observation.replace("\n", " ")
            if len(obs) > 300:
                obs = obs[:300] + "..."

            action = step.action.replace("\n", " ").strip()
            if len(action) > 200:
                action = action[:200] + "..."

            lines.append(f"Step {i}: {action} -> {obs}")
        return "\n".join(lines)


class StepExample(BaseModel):
    """A single step with its trajectory context, used for step-level retrieval."""

    goal: str
    plan: str
    observation: str
    reasoning: str
    action: str
    trajectory_id: str
    step_index: int

    def to_example_string(self) -> str:
        """Format as in-context example with truncated observation."""
        # Truncate observation but keep newlines for readability
        obs = self.observation
        if len(obs) > 800:
            obs = obs[:800] + "\n...[truncated]..."

        reasoning = self.reasoning.strip()
        if len(reasoning) > 400:
            reasoning = reasoning[:400] + "..."

        action = self.action.strip()
        if len(action) > 300:
            action = action[:300] + "..."

        # Format as a clear example with task context
        goal_short = self.goal[:150] + "..." if len(self.goal) > 150 else self.goal

        return f"""[EXAMPLE from similar task: {goal_short}]
Output observed:
{obs}

Reasoning applied:
{reasoning}

Command executed:
{action}
[END EXAMPLE]"""


class CodeArtifact(BaseModel):
    """A code change artifact from a trajectory, captured at creation time.

    Used for deferred validation to check if code changes persisted.
    """

    file_path: str
    change_type: Literal["write", "edit"]

    # For writes: hash of full content written
    # For edits: hash of new_text that was inserted
    content_hash: str

    # Working directory where change was made
    working_dir: str  # Absolute path to repo root where change was made
    git_commit: str | None = None  # Commit hash after the change (kept for reference)

    # For edits: store snippet to help find the lines later
    # (first N chars of new_text for matching)
    content_snippet: str = ""

    created_at: datetime = Field(default_factory=datetime.utcnow)


class DeferredValidation(BaseModel):
    """Result of a deferred validation check.

    Deferred validation answers: "Now that time has passed,
    was this trajectory actually good?" This is distinct from
    immediate approval (user says yes/no at creation time).
    """

    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validator_type: str  # "code_persistence", "supersession", etc.
    score: float  # 0.0 (bad) to 1.0 (good)
    reason: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class CurationMetadata(BaseModel):
    """Metadata for tracking trajectory utility in curation.

    Tracks multiple signals:
    1. Retrieval feedback: When retrieved as an example, did it help?
    2. Deferred validation: Did the outcomes actually hold up over time?

    The utility_score combines these signals to determine trajectory quality.
    """

    trajectory_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # --- Retrieval-based signals (indirect deferred feedback) ---
    times_retrieved: int = 0
    times_led_to_success: int = 0

    # --- Code artifacts for persistence tracking ---
    code_artifacts: list[CodeArtifact] = Field(default_factory=list)

    # --- Deferred validation history ---
    validations: list[DeferredValidation] = Field(default_factory=list)

    # --- Computed scores ---
    retrieval_score: float | None = None  # Success rate from retrievals
    persistence_score: float | None = None  # Latest persistence validation score
    utility_score: float = 1.0  # Combined score (starts optimistic - user approved it)

    # --- Status ---
    is_deprecated: bool = False
    deprecated_at: datetime | None = None
    deprecation_reason: str | None = None
    superseded_by: str | None = None  # ID of trajectory that superseded this one

    def add_validation(self, validation: DeferredValidation) -> None:
        """Record a deferred validation result."""
        self.validations.append(validation)

        # Update persistence score if this is a code persistence validation
        if validation.validator_type == "code_persistence":
            self.persistence_score = validation.score

        self._update_utility()

    def deprecate(self, reason: str, superseded_by: str | None = None) -> None:
        """Mark this trajectory as deprecated."""
        self.is_deprecated = True
        self.deprecated_at = datetime.utcnow()
        self.deprecation_reason = reason
        self.superseded_by = superseded_by

    def _update_utility(self) -> None:
        """Update overall utility from all available signals."""
        scores: list[float] = []
        weights: list[float] = []

        # Signal 1: Retrieval success rate (if enough data)
        if self.times_retrieved >= 3:
            self.retrieval_score = self.times_led_to_success / self.times_retrieved
            scores.append(self.retrieval_score)
            weights.append(1.0)

        # Signal 2: Persistence score (if validated)
        if self.persistence_score is not None:
            scores.append(self.persistence_score)
            # Weight persistence more heavily - it's direct evidence
            weights.append(2.0)

        if scores:
            self.utility_score = sum(s * w for s, w in zip(scores, weights)) / sum(
                weights
            )
        else:
            # No signals yet - stay optimistic (user approved it initially)
            self.utility_score = 1.0

    def update_utility(self) -> None:
        """Update utility score based on all available signals.

        Public method for backward compatibility.
        """
        # Update retrieval score if we have data
        if self.times_retrieved > 0:
            self.retrieval_score = self.times_led_to_success / self.times_retrieved

        self._update_utility()
