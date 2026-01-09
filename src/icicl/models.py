"""Pydantic models for ICICL trajectories and messages."""

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
        return "\n\n---\n\n".join(ex.to_example_string() for ex in self.examples)

    def format_history(self) -> str:
        """Format step history as a string."""
        if not self.history:
            return "No previous steps."
        lines = []
        for i, step in enumerate(self.history, 1):
            lines.append(f"Step {i}: {step.action} -> {step.observation}")
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
        """Format as in-context example."""
        return f"Goal: {self.goal}\nPlan: {self.plan}\nObservation: {self.observation}\nReasoning: {self.reasoning}\nAction: {self.action}"


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
