"""Pydantic models for ICICL trajectories and messages."""

import os
import uuid
from typing import Any

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
            return "No examples available."

        # Hard cap to prevent prompt explosions (esp. when actions contain patches).
        max_examples = int(os.environ.get("ICICL_MAX_EXAMPLES", "3"))
        max_chars = int(os.environ.get("ICICL_MAX_EXAMPLES_CHARS", "4000"))
        if max_examples <= 0 or max_chars <= 0:
            return "No examples available."

        parts: list[str] = []
        total = 0
        omitted = 0

        considered = min(len(self.examples), max_examples)
        for ex in self.examples[:considered]:
            s = ex.to_example_string()
            if total + len(s) > max_chars:
                omitted += 1
                continue
            parts.append(s)
            total += len(s)

        omitted += max(0, len(self.examples) - considered)
        if omitted > 0:
            parts.append(f"[{omitted} example(s) omitted to fit context budget]")

        return "\n\n---\n\n".join(parts)

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
        # Truncate observation aggressively (full obs can be 8000+ chars)
        obs = self.observation.replace("\n", " ")
        if len(obs) > 500:
            obs = obs[:500] + "..."

        reasoning = self.reasoning.replace("\n", " ").strip()
        if len(reasoning) > 300:
            reasoning = reasoning[:300] + "..."

        action = self.action.replace("\n", " ").strip()
        if len(action) > 250:
            action = action[:250] + "..."

        return f"Observation: {obs}\nReasoning: {reasoning}\nAction: {action}"


class CurationMetadata(BaseModel):
    """Metadata for tracking trajectory utility in curation."""

    trajectory_id: str
    times_retrieved: int = 0
    times_led_to_success: int = 0
    utility_score: float = 0.0

    def update_utility(self) -> None:
        """Update utility score based on retrieval statistics."""
        if self.times_retrieved > 0:
            self.utility_score = self.times_led_to_success / self.times_retrieved
        else:
            self.utility_score = 0.0
