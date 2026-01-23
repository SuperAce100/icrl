"""Agent runner for CLI."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from icrl.cli.config import Config, get_default_db_path
from icrl.cli.prompts import SYSTEM_PROMPT
from icrl.cli.providers import (
    AnthropicVertexToolProvider,
    ToolLLMProvider,
    is_vertex_model,
)
from icrl.cli.tool_loop import ToolLoop
from icrl.cli.tools.base import ToolResult, create_default_registry
from icrl.database import TrajectoryDatabase
from icrl.models import Trajectory


class RunnerCallbacks(Protocol):
    """Callbacks for runner events."""

    def on_thinking(self, text: str) -> None:
        """Called when LLM produces thinking/reasoning text."""
        ...

    def on_tool_start(self, tool: str, params: dict[str, Any]) -> None:
        """Called when a tool is about to be executed."""
        ...

    def on_tool_end(self, tool: str, result: ToolResult) -> None:
        """Called when a tool execution completes."""
        ...

    def on_complete(self, trajectory: Trajectory) -> None:
        """Called when the run completes."""
        ...

    def ask_user(self, question: str, options: list[str] | None) -> str:
        """Called to ask the user a question."""
        ...


class SimpleCallbacks:
    """Simple implementation of RunnerCallbacks for basic CLI usage."""

    def __init__(
        self,
        on_thinking: Callable[[str], None] | None = None,
        on_tool_start: Callable[[str, dict[str, Any]], None] | None = None,
        on_tool_end: Callable[[str, ToolResult], None] | None = None,
        on_complete: Callable[[Trajectory], None] | None = None,
        ask_user: Callable[[str, list[str] | None], str] | None = None,
    ):
        self._on_thinking = on_thinking
        self._on_tool_start = on_tool_start
        self._on_tool_end = on_tool_end
        self._on_complete = on_complete
        self._ask_user = ask_user

    def on_thinking(self, text: str) -> None:
        if self._on_thinking:
            self._on_thinking(text)

    def on_tool_start(self, tool: str, params: dict[str, Any]) -> None:
        if self._on_tool_start:
            self._on_tool_start(tool, params)

    def on_tool_end(self, tool: str, result: ToolResult) -> None:
        if self._on_tool_end:
            self._on_tool_end(tool, result)

    def on_complete(self, trajectory: Trajectory) -> None:
        if self._on_complete:
            self._on_complete(trajectory)

    def ask_user(self, question: str, options: list[str] | None) -> str:
        if self._ask_user:
            return self._ask_user(question, options)
        # Default: prompt via input()
        if options:
            print(f"\n{question}")
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
            return input("Your choice: ")
        return input(f"\n{question}\n> ")


class AgentRunner:
    """Runs coding tasks with tool-calling agent."""

    def __init__(
        self,
        config: Config,
        callbacks: RunnerCallbacks | SimpleCallbacks | None = None,
        working_dir: Path | None = None,
    ):
        self._config = config
        self._callbacks = callbacks
        self._working_dir = working_dir or Path.cwd()
        self._cancelled = False
        self._loop: ToolLoop | None = None

        # For UI (e.g., chat prompt bar)
        self.last_examples_count: int = 0
        self.last_db_size: int = 0

        # Initialize database
        db_path = config.db_path or str(get_default_db_path())
        self._database = TrajectoryDatabase(db_path)

    async def run(
        self,
        goal: str,
        train: bool = True,
        compare_mode: bool = False,
    ) -> Trajectory:
        """Run a coding task.

        Args:
            goal: The task to accomplish
            train: If True, store successful trajectories

        Returns:
            The resulting trajectory
        """
        self._cancelled = False

        # Create tool registry
        ask_user_callback = self._callbacks.ask_user if self._callbacks else None
        registry = create_default_registry(
            working_dir=self._working_dir,
            ask_user_callback=ask_user_callback,
            auto_approve=self._config.auto_approve,
        )

        # Create LLM provider (auto-detect Vertex AI models)
        if is_vertex_model(self._config.model):
            llm = AnthropicVertexToolProvider(
                model=self._config.model,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
                registry=registry,
                credentials_path=self._config.vertex_credentials_path,
                project_id=self._config.vertex_project_id,
                location=self._config.vertex_location,
            )
        else:
            llm = ToolLLMProvider(
                model=self._config.model,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
                registry=registry,
            )

        # Retrieve examples from database
        self.last_db_size = len(self._database)
        examples: list[str] = []
        if self.last_db_size > 0:
            similar = self._database.search(goal, k=self._config.k)
            examples = [traj.to_example_string() for traj in similar]
        self.last_examples_count = len(examples)

        # Create and run loop
        self._loop = ToolLoop(
            llm=llm,
            registry=registry,
            system_prompt=SYSTEM_PROMPT,
            max_steps=self._config.max_steps,
            on_tool_start=(self._callbacks.on_tool_start if self._callbacks else None),
            on_tool_end=self._callbacks.on_tool_end if self._callbacks else None,
            on_thinking=self._callbacks.on_thinking if self._callbacks else None,
        )

        trajectory = await self._loop.run(goal, examples=examples if examples else None)

        # Store if training and successful (with human verification)
        if train and trajectory.success:
            approved = True

            if compare_mode:
                # Generate a second candidate response (same trajectory/tools, different wording)
                # by asking the model to produce an alternative final summary.
                alt_text = ""
                try:
                    alt_text = await llm.complete_text(
                        [
                            {
                                "role": "system",
                                "content": (
                                    "You are generating an alternative final response for the user. "
                                    "Do not call tools. Keep it concise and helpful."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    "Here is the original final response. Produce an alternative phrasing "
                                    "that preserves the same meaning and key details.\n\n"
                                    f"ORIGINAL:\n{trajectory.metadata.get('final_response','').strip()}"
                                ),
                            },
                        ]
                    )
                except Exception:
                    alt_text = ""

                a = (trajectory.metadata.get("final_response") or "").strip()
                b = (alt_text or "").strip()

                # If we couldn't produce a meaningful alternative, fall back to normal approval.
                if a and b and a != b:
                    choice = "1"
                    if self._callbacks:
                        choice = self._callbacks.ask_user(
                            "Two candidate final responses were generated. Which one should be stored as the example?",
                            ["Store response A", "Store response B", "Reject both"],
                        )

                    sel = choice.strip().lower()
                    if sel in {"1", "a", "store response a"}:
                        trajectory.metadata["final_response"] = a
                        approved = True
                    elif sel in {"2", "b", "store response b"}:
                        trajectory.metadata["final_response"] = b
                        approved = True
                    else:
                        approved = False
                else:
                    # No usable alternative
                    if self._callbacks:
                        resp = self._callbacks.ask_user(
                            "Store this successful run as a new example in your trajectory database?",
                            ["yes", "no"],
                        )
                        approved = resp.strip().lower() in {"yes", "y", "1", "true"}
            else:
                if self._callbacks:
                    resp = self._callbacks.ask_user(
                        "Store this successful run as a new example in your trajectory database?",
                        ["yes", "no"],
                    )
                    approved = resp.strip().lower() in {"yes", "y", "1", "true"}

            if approved:
                self._database.add(trajectory, working_dir=self._working_dir)

        if self._callbacks:
            self._callbacks.on_complete(trajectory)

        return trajectory

    def cancel(self) -> None:
        """Cancel the current run."""
        self._cancelled = True
        if self._loop:
            self._loop.cancel()

    @property
    def database(self) -> TrajectoryDatabase:
        """Access the trajectory database."""
        return self._database
