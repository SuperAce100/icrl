"""Simple CLI for ICICL."""

import asyncio
import sys
from pathlib import Path
from typing import Any

from rich.console import Console

from icicl.cli.config import Config, get_default_db_path
from icicl.cli.prompts import SYSTEM_PROMPT
from icicl.cli.providers.tool_provider import ToolLLMProvider
from icicl.cli.tool_loop import ToolLoop
from icicl.cli.tools.base import ToolResult, create_default_registry
from icicl.database import TrajectoryDatabase


def format_model_name(model: str) -> str:
    """Format the model name for display."""
    model_parts = model.split("/")
    model_name = model_parts[-1] if model_parts else model

    name_map = {
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


async def run_task(
    goal: str,
    config: Config,
    working_dir: Path,
    database: TrajectoryDatabase,
    console: Console,
) -> None:
    """Run a single task."""

    def on_thinking(text: str) -> None:
        lines = text.strip().split("\n")
        preview = lines[0][:80] + "..." if len(lines[0]) > 80 else lines[0]
        console.print(f"[dim italic]{preview}[/]")

    def on_tool_start(tool: str, params: dict[str, Any]) -> None:
        def _dim(val: str) -> str:
            return f"[dim]{val}[/]" if val else ""

        if tool == "Bash":
            cmd = params.get("command", "")
            if len(cmd) > 60:
                cmd = cmd[:60] + "..."
            console.print(f"  Bash {_dim(cmd)}")
        elif tool == "Read":
            console.print(f"  Read {_dim(params.get('path', ''))}")
        elif tool == "Write":
            console.print(f"  Write {_dim(params.get('path', ''))}")
        elif tool == "Edit":
            console.print(f"  Edit {_dim(params.get('path', ''))}")
        elif tool == "Grep":
            console.print(f"  Grep {_dim(params.get('pattern', ''))}")
        elif tool == "Glob":
            console.print(f"  Glob {_dim(params.get('pattern', ''))}")
        else:
            console.print(f"  {tool}")

    def on_tool_end(tool: str, result: ToolResult) -> None:
        pass

    def ask_user(question: str, options: list[str] | None) -> str:
        console.print(f"\n[bold]{question}[/]")
        if options:
            for i, opt in enumerate(options, 1):
                console.print(f"  {i}. {opt}")
        console.print("> ", end="")
        return console.input()

    registry = create_default_registry(
        working_dir=working_dir,
        ask_user_callback=ask_user,
    )

    llm = ToolLLMProvider(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        registry=registry,
    )

    # Retrieve examples
    examples: list[str] = []
    if len(database) > 0:
        similar = database.search(goal, k=config.k)
        examples = [traj.to_example_string() for traj in similar]

    loop = ToolLoop(
        llm=llm,
        registry=registry,
        system_prompt=SYSTEM_PROMPT,
        max_steps=config.max_steps,
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
        on_thinking=on_thinking,
    )

    trajectory = await loop.run(goal, examples=examples if examples else None)

    if trajectory.success:
        database.add(trajectory)

    console.print()
    if trajectory.success:
        console.print("[green]✓[/] Done")
        if trajectory.metadata.get("final_response"):
            response = trajectory.metadata["final_response"]
            if len(response) > 500:
                response = response[:500] + "..."
            console.print(response)
    else:
        console.print("[red]✗[/] Failed")

    console.print(f"[dim]({len(trajectory.steps)} steps)[/]\n")


def run_tui(config: Config | None = None, working_dir: Path | None = None) -> None:
    """Run the simple CLI."""
    console = Console()
    config = config or Config.load()
    working_dir = working_dir or Path.cwd()

    # One-time intro banner for the current process (i.e., first time entering chat)
    if not getattr(run_tui, "_intro_printed", False):
        run_tui._intro_printed = True  # type: ignore[attr-defined]
        console.print(
            "[bold cyan]"
            "  ___ ____ ___ ____ _     \n"
            " |_ _/ ___|_ _/ ___| |    \n"
            "  | | |    | | |   | |    \n"
            "  | | |___ | | |___| |___ \n"
            " |___\\____|___\\____|_____|\n"
            "[/]"
        )
        console.print("[dim]Type a task and press Enter. 'exit' to quit.[/]\n")

    db_path = config.db_path or str(get_default_db_path())
    database = TrajectoryDatabase(db_path)

    model_display = format_model_name(config.model)

    # Shorten working dir for display
    try:
        cwd_display = f"~/{working_dir.relative_to(Path.home())}"
    except ValueError:
        cwd_display = str(working_dir)

    while True:
        try:
            # Info line: model · cwd · examples
            db_count = len(database)
            console.print(
                f"\n[dim]{model_display} · {cwd_display} · {db_count} examples[/]"
            )

            # Prompt
            console.print("→ ", end="")
            goal = console.input()

            if not goal.strip():
                continue

            if goal.strip().lower() in ("exit", "quit", "q"):
                break

            console.print()
            asyncio.run(run_task(goal, config, working_dir, database, console))

        except KeyboardInterrupt:
            console.print("\n[dim]^C[/]")
            continue
        except EOFError:
            break

    console.print("[dim]bye[/]")
    sys.exit(0)
