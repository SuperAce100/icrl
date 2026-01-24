"""Simple CLI for ICRL."""

import asyncio
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt

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


def format_model_name(model: str) -> str:
    """Format the model name for display."""
    model_parts = model.split("/")
    model_name = model_parts[-1] if model_parts else model

    name_map = {
        "claude-opus-4.5": "Claude Opus 4.5",
        "claude-opus-4-5": "Claude Opus 4.5",
        "claude-sonnet-4.5": "Claude Sonnet 4.5",
        "claude-sonnet-4-5": "Claude Sonnet 4.5",
        "claude-haiku-4.5": "Claude Haiku 4.5",
        "claude-haiku-4-5": "Claude Haiku 4.5",
        "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
        "claude-3-5-sonnet": "Claude 3.5 Sonnet",
        "claude-3-opus": "Claude 3 Opus",
        "claude-3-sonnet": "Claude 3 Sonnet",
        "claude-3-haiku": "Claude 3 Haiku",
        "claude-sonnet-4-20250514": "Claude Sonnet 4",
        "claude-4-5-opus": "Claude 4.5 Opus",
        "gpt-4": "GPT-4",
        "gpt-4-turbo": "GPT-4 Turbo",
        "gpt-4o": "GPT-4o",
        "gpt-4o-mini": "GPT-4o Mini",
        "gpt-3.5-turbo": "GPT-3.5 Turbo",
    }

    for key, display in name_map.items():
        if key in model_name.lower():
            return display

    return model_name


class ChatSession:
    """Manages a multi-turn chat session with conversation history."""

    def __init__(
        self,
        config: Config,
        working_dir: Path,
        database: TrajectoryDatabase,
        console: Console,
    ):
        self.config = config
        self.working_dir = working_dir
        self.database = database
        self.console = console
        self._loop: ToolLoop | None = None
        self._turn_count = 0

    def _create_callbacks(self) -> tuple:
        """Create callback functions for the tool loop."""

        def on_thinking(text: str) -> None:
            lines = text.strip().split("\n")
            preview = lines[0][:80] + "..." if len(lines[0]) > 80 else lines[0]
            self.console.print(f"[dim italic]{preview}[/dim italic]")

        def on_tool_start(tool: str, params: dict[str, Any]) -> None:
            def _dim(val: str) -> str:
                return f"[dim]{val}[/dim]" if val else ""

            if tool == "Bash":
                cmd = params.get("command", "")
                self.console.print(f"$ {cmd}")
            elif tool == "Read":
                self.console.print(f"  Read {_dim(params.get('path', ''))}")
            elif tool == "Write":
                self.console.print(f"  Wrote {_dim(params.get('path', ''))}")
            elif tool == "Edit":
                self.console.print(f"  Edited {_dim(params.get('path', ''))}")
            elif tool == "Grep":
                self.console.print(f"  Grepped {_dim(params.get('pattern', ''))}")
            elif tool == "Glob":
                self.console.print(f"  Globbed {_dim(params.get('pattern', ''))}")
            else:
                self.console.print(f"  {tool}")

        def on_tool_end(tool: str, result: ToolResult) -> None:
            if tool == "Bash":
                output = result.output.rstrip("\n")
                if output:
                    lines = output.splitlines()
                    tail = "\n".join(lines[-5:])
                    self.console.print(f"[dim]{tail}[/dim]")

        def ask_user(question: str, options: list[str] | None) -> str:
            """Cleaner AskUserQuestion UI (matches the rest of the TUI)."""
            self.console.print()
            self.console.print(f"[bold]{question}[/bold]")

            if options:
                for i, opt in enumerate(options, 1):
                    self.console.print(f"  [cyan]{i}.[/cyan] {opt}")
                return Prompt.ask("->", default="1")

            return Prompt.ask("->")

        return on_thinking, on_tool_start, on_tool_end, ask_user

    def _ensure_loop(self) -> ToolLoop:
        """Create or return the existing tool loop."""
        if self._loop is None:
            on_thinking, on_tool_start, on_tool_end, ask_user = self._create_callbacks()

            registry = create_default_registry(
                working_dir=self.working_dir,
                ask_user_callback=ask_user,
            )

            # Create LLM provider (auto-detect Vertex AI models)
            if is_vertex_model(self.config.model):
                llm = AnthropicVertexToolProvider(
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    registry=registry,
                    credentials_path=self.config.vertex_credentials_path,
                    project_id=self.config.vertex_project_id,
                    location=self.config.vertex_location,
                )
            else:
                llm = ToolLLMProvider(
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    registry=registry,
                )

            self._loop = ToolLoop(
                llm=llm,
                registry=registry,
                system_prompt=SYSTEM_PROMPT,
                max_steps=self.config.max_steps,
                on_tool_start=on_tool_start,
                on_tool_end=on_tool_end,
                on_thinking=on_thinking,
            )

        return self._loop

    def clear(self) -> None:
        """Clear conversation history and start fresh."""
        if self._loop is not None:
            self._loop.clear_history()
        self._turn_count = 0
        self.console.print("[dim]Conversation cleared.[/dim]")

    async def run_turn(self, goal: str) -> None:
        """Run a single turn of conversation."""
        loop = self._ensure_loop()

        # Only retrieve examples on the first turn
        examples: list[str] = []
        if self._turn_count == 0 and len(self.database) > 0:
            similar = self.database.search(goal, k=self.config.k)
            examples = [traj.to_example_string() for traj in similar]

        # Continue conversation if not the first turn
        continue_conversation = self._turn_count > 0

        trajectory = await loop.run(
            goal,
            examples=examples if examples else None,
            continue_conversation=continue_conversation,
        )

        self._turn_count += 1

        # Show the result first
        self.console.print()
        if trajectory.success:
            self.console.print("[green]OK[/green] Done")
            if trajectory.metadata.get("final_response"):
                response = trajectory.metadata["final_response"]
                self.console.print(Markdown(response))
        else:
            self.console.print("[red]X[/red] Failed")

        # Then ask about storing (after user has seen the final response)
        if trajectory.success:
            self.console.print()
            approved = Confirm.ask(
                "Store this successful run as a new example?", default=True
            )
            if approved:
                self.database.add(trajectory)
            else:
                self.console.print("[dim]Trajectory discarded.[/dim]")


async def run_task(
    goal: str,
    config: Config,
    working_dir: Path,
    database: TrajectoryDatabase,
    console: Console,
) -> None:
    """Run a single task (legacy single-turn mode)."""
    session = ChatSession(config, working_dir, database, console)
    await session.run_turn(goal)


def run_tui(config: Config | None = None, working_dir: Path | None = None) -> None:
    """Run the simple CLI with multi-turn chat support."""
    console = Console()
    config = config or Config.load()
    working_dir = working_dir or Path.cwd()

    # One-time intro banner for the current process (i.e., first time entering chat)
    if not getattr(run_tui, "_intro_printed", False):
        run_tui._intro_printed = True  # type: ignore[attr-defined]
        console.print(
            "[bold cyan]"
            "  ___ ____ ____  _     \n"
            " |_ _/ ___|  _ \\| |    \n"
            "  | | |   | |_) | |    \n"
            "  | | |___|  _ <| |___ \n"
            " |___\\____|_| \\_\\_____|\n"
            "[/bold cyan]"
        )
        console.print("Type a task and press Enter. '/clear' to reset, 'exit' to quit.")

    db_path = config.db_path or str(get_default_db_path())
    database = TrajectoryDatabase(db_path)

    model_display = format_model_name(config.model)

    # Shorten working dir for display
    try:
        cwd_display = f"~/{working_dir.relative_to(Path.home())}"
    except ValueError:
        cwd_display = str(working_dir)

    # Create a persistent chat session for multi-turn conversation
    session = ChatSession(config, working_dir, database, console)

    # Reuse a single event loop to avoid cross-loop async logging issues.
    with asyncio.Runner() as runner:
        while True:
            try:
                # Info line: model . cwd . examples . turn indicator
                db_count = len(database)
                turn_info = ""
                if session._turn_count > 0:
                    turn_info = f" . turn {session._turn_count + 1}"
                console.print(
                    f"{model_display} . {cwd_display} . {db_count} examples{turn_info}"
                )

                # Prompt with simple bordered line
                console.print("[green]" + "-" * 50 + "[/green]")
                goal = Prompt.ask("[bold green]>>[/bold green]")
                console.print("[green]" + "-" * 50 + "[/green]")

                if not goal.strip():
                    continue

                if goal.strip().lower() in ("exit", "quit", "q"):
                    break

                # Handle /clear command
                if goal.strip().lower() == "/clear":
                    session.clear()
                    continue

                console.print()
                runner.run(session.run_turn(goal))

            except KeyboardInterrupt:
                console.print("\n^C")
                continue
            except EOFError:
                break

    console.print("bye")
    sys.exit(0)
