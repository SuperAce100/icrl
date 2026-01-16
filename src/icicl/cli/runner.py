"""Agent runner for CLI."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from icicl.cli.config import Config, get_default_db_path
from icicl.cli.prompts import SYSTEM_PROMPT
from icicl.cli.providers.tool_provider import ToolLLMProvider
from icicl.cli.tool_loop import ToolLoop
from icicl.cli.tools.base import ToolResult, create_default_registry
from icicl.database import TrajectoryDatabase
from icicl.models import Trajectory


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

        # Initialize database
        db_path = config.db_path or str(get_default_db_path())
        self._database = TrajectoryDatabase(db_path)

    async def run(self, goal: str, train: bool = True) -> Trajectory:
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
        )

        # Create LLM provider
        llm = ToolLLMProvider(
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            registry=registry,
        )

        # Retrieve examples from database
        examples: list[str] = []
        if len(self._database) > 0:
            similar = self._database.search(goal, k=self._config.k)
            examples = [traj.to_example_string() for traj in similar]

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

        # Store if training and successful
        if train and trajectory.success:
            self._database.add(trajectory)

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
