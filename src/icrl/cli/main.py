"""ICRL CLI - Main entry point."""

# Configure litellm BEFORE any other imports to avoid event loop issues
import litellm  # noqa: E402

litellm.disable_logging_worker = True

import asyncio  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Annotated  # noqa: E402

# Better interactive input editing (e.g., backspace across wrapped lines)
try:  # pragma: no cover
    import readline  # noqa: F401
except Exception:  # pragma: no cover
    readline = None  # type: ignore

# Suppress litellm async client cleanup warning
warnings.filterwarnings("ignore", message="coroutine 'close_litellm_async_clients'")

import typer  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.prompt import Confirm  # noqa: E402
from rich.table import Table  # noqa: E402

from icrl import __version__  # noqa: E402
from icrl.cli.config import Config, get_config_dir, get_default_db_path  # noqa: E402
from icrl.cli.runner import AgentRunner, SimpleCallbacks  # noqa: E402
from icrl.cli.tools.base import ToolResult  # noqa: E402
from icrl.database import TrajectoryDatabase  # noqa: E402

app = typer.Typer(
    name="icrl",
    help="ICRL - Interactive coding assistant with example retrieval.",
    no_args_is_help=True,
)

# Subcommand groups
config_app = typer.Typer(help="Configuration management commands.")
db_app = typer.Typer(help="Trajectory database management commands.")
app.add_typer(config_app, name="config")
app.add_typer(db_app, name="db")

console = Console()


@app.command()
def version() -> None:
    """Show the version."""
    console.print(f"icrl version {__version__}")


@app.command()
def run(
    goal: Annotated[
        str,
        typer.Argument(help="The task to accomplish"),
    ],
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="LLM model to use"),
    ] = None,
    no_train: Annotated[
        bool,
        typer.Option("--no-train", help="Don't store trajectory in database"),
    ] = False,
    compare: Annotated[
        bool,
        typer.Option(
            "--compare",
            help="Generate two candidate final responses and let you choose which to store (or reject both)",
        ),
    ] = False,
    working_dir: Annotated[
        Path | None,
        typer.Option("--dir", "-d", help="Working directory"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed output"),
    ] = False,
    vertex_credentials: Annotated[
        Path | None,
        typer.Option(
            "--vertex-credentials",
            help="Path to GCP service account JSON for Vertex AI",
        ),
    ] = None,
    vertex_project: Annotated[
        str | None,
        typer.Option("--vertex-project", help="GCP project ID for Vertex AI"),
    ] = None,
    vertex_location: Annotated[
        str | None,
        typer.Option(
            "--vertex-location", help="GCP region for Vertex AI (e.g., global, us-east5)"
        ),
    ] = None,
    stats: Annotated[
        bool,
        typer.Option("--stats/--no-stats", help="Show latency and throughput statistics"),
    ] = True,
    auto_approve: Annotated[
        bool,
        typer.Option(
            "--auto-approve/--no-auto-approve",
            "-y",
            help="Auto-approve file writes and edits without confirmation prompts",
        ),
    ] = True,
) -> None:
    """Run a coding task with the agent."""
    config = Config.load()
    if model:
        config.model = model
    if vertex_credentials:
        config.vertex_credentials_path = str(vertex_credentials)
    if vertex_project:
        config.vertex_project_id = vertex_project
    if vertex_location:
        config.vertex_location = vertex_location
    config.show_stats = stats
    config.auto_approve = auto_approve

    work_dir = working_dir or Path.cwd()

    def on_thinking(text: str) -> None:
        if verbose:
            console.print(
                Panel(text, title="[bold blue]Thinking[/]", border_style="blue")
            )
        else:
            # Just show a summary
            lines = text.strip().split("\n")
            if lines:
                preview = lines[0][:100]
                suffix = "..." if len(lines[0]) > 100 else ""
                console.print(f"[dim]{preview}{suffix}[/]")

    _last_bash_command: str | None = None

    def on_tool_start(tool: str, params: dict) -> None:
        # Prefer past-tense action verbs in logs (matches the user's mental model of
        # "what happened"), while still being emitted at tool start.
        nonlocal _last_bash_command

        if tool == "Bash":
            # Print like a terminal: command (white) prefixed with `$`, then print the
            # result dimmed in `on_tool_end`.
            cmd = params.get("command", "")
            _last_bash_command = cmd
            console.print(f"[white]$ {cmd}[/]")
            return

        if tool == "Read":
            console.print(f"[cyan]Read[/] {params.get('path', '')}")
        elif tool == "Write":
            console.print(f"[green]Wrote[/] {params.get('path', '')}")
        elif tool == "Edit":
            console.print(f"[yellow]Edited[/] {params.get('path', '')}")
        elif tool == "Glob":
            console.print(f"[cyan]Globbed[/] {params.get('pattern', '')}")
        elif tool == "Grep":
            console.print(f"[cyan]Grepped[/] {params.get('pattern', '')}")
        elif tool == "WebSearch":
            console.print(f"[blue]Searched web[/] {params.get('query', '')}")
        elif tool == "WebFetch":
            console.print(f"[blue]Fetched[/] {params.get('url', '')}")
        else:
            console.print(f"[dim]Used tool: {tool}[/]")

    def on_tool_end(tool: str, result: ToolResult) -> None:
        nonlocal _last_bash_command

        if tool == "Bash":
            output = result.output.rstrip("\n")
            if output:
                lines = output.splitlines()
                tail = "\n".join(lines[-5:])
                console.print(f"[dim]{tail}[/]")
            _last_bash_command = None
            return

        if verbose:
            output = result.output
            if len(output) > 500:
                output = output[:500] + "\n...(truncated)..."
            style = "green" if result.success else "red"
            console.print(
                Panel(output, title=f"[{style}]{tool} result[/]", border_style=style)
            )

    def on_complete(trajectory) -> None:
        if trajectory.success:
            console.print("\n[bold green]Task completed successfully![/]")
            if trajectory.metadata.get("final_response"):
                console.print(
                    Panel(
                        trajectory.metadata["final_response"],
                        title="[bold]Summary[/]",
                        border_style="green",
                    )
                )
        else:
            console.print("\n[bold red]Task did not complete successfully.[/]")

        console.print(f"[dim]Steps taken: {len(trajectory.steps)}[/]")

        # Display stats if enabled
        if config.show_stats and trajectory.metadata.get("stats"):
            stats_data = trajectory.metadata["stats"]
            latency_s = stats_data.get("total_latency_ms", 0) / 1000
            tokens = stats_data.get("total_tokens", 0)
            completion_tokens = stats_data.get("total_completion_tokens", 0)
            prompt_tokens = stats_data.get("total_prompt_tokens", 0)
            tps = stats_data.get("tokens_per_second", 0)
            llm_calls = stats_data.get("llm_calls", 0)

            parts = []
            if latency_s > 0:
                parts.append(f"{latency_s:.1f}s")
            if tokens > 0:
                parts.append(f"{tokens:,} tokens ({prompt_tokens:,}↑ {completion_tokens:,}↓)")
            if tps > 0:
                parts.append(f"{tps:.0f} tok/s")
            if llm_calls > 0:
                parts.append(f"{llm_calls} calls")

            if parts:
                console.print(f"[dim]⏱ {' · '.join(parts)}[/dim]")

    def ask_user(question: str, options: list[str] | None) -> str:
        """Cleaner AskUserQuestion UI (matches the rest of the app)."""

        # Special-case yes/no prompts (used by human verification gates).
        if options and {o.strip().lower() for o in options} <= {"yes", "no", "y", "n"}:
            approved = Confirm.ask(question, default=True)
            return "yes" if approved else "no"

        console.print()
        console.print(f"[bold]Question[/]  {question}")

        if options:
            for i, opt in enumerate(options, 1):
                console.print(f"  [cyan]{i}.[/] {opt}")
            console.print(
                "[dim]Select 1-{n}, or type the option text.[/]".format(n=len(options))
            )
            # Return the raw selection so the caller can interpret it.
            return typer.prompt("→", default="1")

        return typer.prompt("→")

    callbacks = SimpleCallbacks(
        on_thinking=on_thinking,
        on_tool_start=on_tool_start,
        on_tool_end=on_tool_end,
        on_complete=on_complete,
        ask_user=ask_user,
    )

    runner = AgentRunner(config=config, callbacks=callbacks, working_dir=work_dir)

    console.print(f"\n[bold]Goal:[/] {goal}")
    console.print(f"[dim]Model: {config.model} | Working dir: {work_dir}[/]\n")

    try:
        asyncio.run(runner.run(goal, train=not no_train, compare_mode=compare))
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/]")
        runner.cancel()


@app.command()
def tui(
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="LLM model to use"),
    ] = None,
    compare: Annotated[
        bool,
        typer.Option(
            "--compare",
            help="Generate two candidate final responses and let you choose which to store (or reject both)",
        ),
    ] = False,
    working_dir: Annotated[
        Path | None,
        typer.Option("--dir", "-d", help="Working directory"),
    ] = None,
    stats: Annotated[
        bool,
        typer.Option("--stats/--no-stats", help="Show latency and throughput statistics"),
    ] = True,
    auto_approve: Annotated[
        bool,
        typer.Option(
            "--auto-approve/--no-auto-approve",
            "-y",
            help="Auto-approve file writes and edits without confirmation prompts",
        ),
    ] = True,
) -> None:
    """Start the interactive TUI (Terminal User Interface)."""
    from icrl.cli.tui import run_tui

    config = Config.load()
    if model:
        config.model = model
    config.show_stats = stats
    config.auto_approve = auto_approve

    work_dir = working_dir or Path.cwd()
    run_tui(config=config, working_dir=work_dir, compare_mode=compare)


@app.command()
def chat(
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="LLM model to use"),
    ] = None,
    compare: Annotated[
        bool,
        typer.Option(
            "--compare",
            help="Generate two candidate final responses and let you choose which to store (or reject both)",
        ),
    ] = False,
    working_dir: Annotated[
        Path | None,
        typer.Option("--dir", "-d", help="Working directory"),
    ] = None,
    stats: Annotated[
        bool,
        typer.Option("--stats/--no-stats", help="Show latency and throughput statistics"),
    ] = True,
    auto_approve: Annotated[
        bool,
        typer.Option(
            "--auto-approve/--no-auto-approve",
            "-y",
            help="Auto-approve file writes and edits without confirmation prompts",
        ),
    ] = True,
) -> None:
    """Start an interactive chat session."""
    from icrl.cli.tui import run_tui

    config = Config.load()
    if model:
        config.model = model
    config.show_stats = stats
    config.auto_approve = auto_approve

    work_dir = working_dir or Path.cwd()
    run_tui(config=config, working_dir=work_dir, compare_mode=compare)


# Config subcommands
@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    config = Config.load()
    table = Table(title="ICRL Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, value in config.to_dict().items():
        table.add_row(key, str(value))

    console.print(table)
    console.print(f"\n[dim]Config file: {get_config_dir() / 'config.json'}[/]")


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Configuration key")],
    value: Annotated[str, typer.Argument(help="Configuration value")],
) -> None:
    """Set a configuration value."""
    config = Config.load()

    if key == "model":
        config.model = value
    elif key == "temperature":
        config.temperature = float(value)
    elif key == "max_tokens":
        config.max_tokens = int(value)
    elif key == "max_steps":
        config.max_steps = int(value)
    elif key == "k":
        config.k = int(value)
    elif key == "show_stats":
        config.show_stats = value.lower() in ("true", "1", "yes", "on")
    elif key == "auto_approve":
        config.auto_approve = value.lower() in ("true", "1", "yes", "on")
    elif key == "db_path":
        config.db_path = value
    elif key == "vertex_credentials_path":
        config.vertex_credentials_path = value
    elif key == "vertex_project_id":
        config.vertex_project_id = value
    elif key == "vertex_location":
        config.vertex_location = value
    else:
        console.print(f"[red]Unknown configuration key: {key}[/]")
        console.print(
            "[dim]Valid keys: model, temperature, max_tokens, max_steps, k, show_stats, auto_approve, "
            "db_path, vertex_credentials_path, vertex_project_id, vertex_location[/]"
        )
        raise typer.Exit(1)

    config.save()
    console.print(f"[green]Set {key} = {value}[/]")


@config_app.command("reset")
def config_reset() -> None:
    """Reset configuration to defaults."""
    config = Config()
    config.save()
    console.print("[green]Configuration reset to defaults.[/]")


# Database subcommands
@db_app.command("stats")
def db_stats() -> None:
    """Show database statistics."""
    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())

    db = TrajectoryDatabase(db_path)

    console.print("\n[bold]Database Statistics[/]")
    console.print(f"Path: {db_path}")
    console.print(f"Trajectories: {len(db)}")

    if len(db) > 0:
        trajectories = db.get_all()
        successful = sum(1 for t in trajectories if t.success)
        total_steps = sum(len(t.steps) for t in trajectories)

        console.print(f"Successful: {successful}")
        console.print(f"Total steps: {total_steps}")
        console.print(f"Avg steps/trajectory: {total_steps / len(trajectories):.1f}")

        # Curation stats
        with_artifacts = sum(
            1 for m in db._curation_metadata.values() if m.code_artifacts
        )
        validated = sum(
            1 for m in db._curation_metadata.values() if m.persistence_score is not None
        )
        deprecated = sum(
            1 for m in db._curation_metadata.values() if m.is_deprecated
        )

        if with_artifacts > 0 or validated > 0 or deprecated > 0:
            console.print("\n[bold]Curation Stats[/]")
            console.print(f"With code artifacts: {with_artifacts}")
            console.print(f"Validated: {validated}")
            console.print(f"Deprecated: {deprecated}")
            console.print(f"Active: {len(db) - deprecated}")


@db_app.command("list")
def db_list(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max items to show")] = 10,
) -> None:
    """List trajectories in the database."""
    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())

    from icrl.database import TrajectoryDatabase

    db = TrajectoryDatabase(db_path)
    trajectories = db.get_all()[:limit]

    if not trajectories:
        console.print("[dim]No trajectories in database.[/]")
        return

    table = Table(title="Trajectories")
    table.add_column("ID", style="dim", max_width=8)
    table.add_column("Goal", max_width=50)
    table.add_column("Steps", justify="right")
    table.add_column("Success", justify="center")

    for traj in trajectories:
        goal = traj.goal[:47] + "..." if len(traj.goal) > 50 else traj.goal
        success = "[green]Yes[/]" if traj.success else "[red]No[/]"
        table.add_row(traj.id[:8], goal, str(len(traj.steps)), success)

    console.print(table)

    if len(db) > limit:
        console.print(f"\n[dim]Showing {limit} of {len(db)} trajectories.[/]")


@db_app.command("show")
def db_show(
    trajectory_id: Annotated[str, typer.Argument(help="Trajectory ID (or prefix)")],
) -> None:
    """Show details of a specific trajectory."""
    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())

    from icrl.database import TrajectoryDatabase

    db = TrajectoryDatabase(db_path)

    # Find trajectory by ID or prefix
    trajectory = None
    for traj in db.get_all():
        if traj.id.startswith(trajectory_id):
            trajectory = traj
            break

    if not trajectory:
        console.print(f"[red]Trajectory not found: {trajectory_id}[/]")
        raise typer.Exit(1)

    console.print(
        Panel(
            f"[bold]Goal:[/] {trajectory.goal}\n\n"
            f"[bold]Plan:[/] {trajectory.plan or '(none)'}\n\n"
            f"[bold]Success:[/] {'Yes' if trajectory.success else 'No'}\n"
            f"[bold]Steps:[/] {len(trajectory.steps)}",
            title=f"Trajectory {trajectory.id[:8]}",
        )
    )

    for i, step in enumerate(trajectory.steps, 1):
        console.print(f"\n[bold cyan]Step {i}:[/] {step.action[:80]}...")
        if step.reasoning:
            console.print(f"  [dim]Reasoning: {step.reasoning[:100]}...[/]")


@db_app.command("search")
def db_search(
    query: Annotated[str, typer.Argument(help="Search query")],
    k: Annotated[int, typer.Option("--k", "-k", help="Number of results")] = 5,
) -> None:
    """Search for similar trajectories."""
    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())

    from icrl.database import TrajectoryDatabase

    db = TrajectoryDatabase(db_path)

    if len(db) == 0:
        console.print("[dim]No trajectories in database.[/]")
        return

    results = db.search(query, k=k)

    table = Table(title=f"Search results for: {query}")
    table.add_column("ID", style="dim", max_width=8)
    table.add_column("Goal", max_width=60)
    table.add_column("Success", justify="center")

    for traj in results:
        goal = traj.goal[:57] + "..." if len(traj.goal) > 60 else traj.goal
        success = "[green]Yes[/]" if traj.success else "[red]No[/]"
        table.add_row(traj.id[:8], goal, success)

    console.print(table)


@db_app.command("clear")
def db_clear(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Clear all trajectories from the database."""
    if not force:
        confirm = typer.confirm("Are you sure you want to clear all trajectories?")
        if not confirm:
            raise typer.Abort()

    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())

    import shutil

    db_path_obj = Path(db_path)
    if db_path_obj.exists():
        shutil.rmtree(db_path_obj)
        console.print("[green]Database cleared.[/]")
    else:
        console.print("[dim]Database directory doesn't exist.[/]")


@db_app.command("validate")
def db_validate(
    trajectory_id: Annotated[
        str | None,
        typer.Argument(help="Trajectory ID to validate (validates all if not specified)"),
    ] = None,
    working_dir: Annotated[
        Path | None,
        typer.Option("--dir", "-d", help="Working directory for validation"),
    ] = None,
    include_deprecated: Annotated[
        bool,
        typer.Option("--include-deprecated", help="Include deprecated trajectories"),
    ] = False,
) -> None:
    """Validate code persistence for trajectories.

    Checks whether code changes from trajectories still exist in the codebase.
    This provides implicit feedback about trajectory quality over time.
    """
    from rich.table import Table

    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())
    database = TrajectoryDatabase(db_path)

    work_dir = working_dir or Path.cwd()

    if trajectory_id:
        # Validate single trajectory
        validation = database.validate_trajectory(trajectory_id, work_dir)
        if validation is None:
            console.print(f"[red]Trajectory not found or has no code artifacts: {trajectory_id}[/]")
            raise typer.Exit(1)

        console.print(f"[bold]Validation for {trajectory_id}[/]")
        console.print(f"  Score: {validation.score:.1%}")
        console.print(f"  Status: {validation.reason}")
        if validation.details:
            console.print(f"  Artifacts: {validation.details.get('artifact_count', 0)}")
            console.print(f"  Intact: {validation.details.get('intact_count', 0)}")
            console.print(f"  Modified: {validation.details.get('modified_count', 0)}")
            console.print(f"  Removed: {validation.details.get('removed_count', 0)}")
    else:
        # Validate all trajectories
        results = database.validate_all(work_dir, include_deprecated=include_deprecated)

        if not results:
            console.print("[dim]No trajectories with code artifacts to validate.[/]")
            return

        table = Table(title="Validation Results")
        table.add_column("Trajectory ID", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Status")
        table.add_column("Artifacts", justify="right")
        table.add_column("Intact", justify="right")

        for traj_id, validation in results:
            score_str = f"{validation.score:.0%}"
            if validation.score >= 0.8:
                score_style = "green"
            elif validation.score >= 0.5:
                score_style = "yellow"
            else:
                score_style = "red"

            table.add_row(
                traj_id[:12] + "...",
                f"[{score_style}]{score_str}[/{score_style}]",
                validation.reason,
                str(validation.details.get("artifact_count", 0)),
                str(validation.details.get("intact_count", 0)),
            )

        console.print(table)
        console.print(f"\n[dim]Validated {len(results)} trajectories.[/]")


@db_app.command("deprecated")
def db_deprecated() -> None:
    """List deprecated trajectories."""
    from rich.table import Table

    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())
    database = TrajectoryDatabase(db_path)

    deprecated = database.get_deprecated_trajectories()

    if not deprecated:
        console.print("[dim]No deprecated trajectories.[/]")
        return

    table = Table(title="Deprecated Trajectories")
    table.add_column("Trajectory ID", style="cyan")
    table.add_column("Reason")
    table.add_column("Superseded By")
    table.add_column("Deprecated At")

    for meta in deprecated:
        superseded_by = meta.superseded_by[:12] + "..." if meta.superseded_by else "-"
        deprecated_at = meta.deprecated_at.strftime("%Y-%m-%d %H:%M") if meta.deprecated_at else "-"

        table.add_row(
            meta.trajectory_id[:12] + "...",
            meta.deprecation_reason or "-",
            superseded_by,
            deprecated_at,
        )

    console.print(table)
    console.print(f"\n[dim]{len(deprecated)} deprecated trajectories.[/]")


@db_app.command("prune")
def db_prune(
    min_utility: Annotated[
        float,
        typer.Option("--min-utility", "-u", help="Minimum utility score to keep"),
    ] = 0.3,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show what would be pruned without removing"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Prune low-utility and deprecated trajectories.

    Removes trajectories that have been deprecated or have utility scores
    below the specified threshold.
    """
    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())
    database = TrajectoryDatabase(db_path)

    # Find trajectories to prune
    to_prune: list[str] = []

    for meta in database._curation_metadata.values():
        if meta.is_deprecated:
            to_prune.append(meta.trajectory_id)
        elif meta.utility_score < min_utility and (
            meta.times_retrieved >= 3 or meta.persistence_score is not None
        ):
            # Only prune if we have enough signal
            to_prune.append(meta.trajectory_id)

    if not to_prune:
        console.print("[dim]No trajectories to prune.[/]")
        return

    console.print(f"[bold]Found {len(to_prune)} trajectories to prune:[/]")
    for traj_id in to_prune[:10]:
        meta = database.get_curation_metadata(traj_id)
        reason = "deprecated" if meta and meta.is_deprecated else f"utility={meta.utility_score:.1%}" if meta else "unknown"
        console.print(f"  - {traj_id[:12]}... ({reason})")
    if len(to_prune) > 10:
        console.print(f"  ... and {len(to_prune) - 10} more")

    if dry_run:
        console.print("\n[dim]Dry run - no changes made.[/]")
        return

    if not force:
        confirm = typer.confirm(f"Remove {len(to_prune)} trajectories?")
        if not confirm:
            raise typer.Abort()

    removed = 0
    for traj_id in to_prune:
        if database.remove(traj_id):
            removed += 1

    console.print(f"[green]Removed {removed} trajectories.[/]")


@db_app.command("extract-artifacts")
def db_extract_artifacts(
    working_dir: Annotated[
        Path | None,
        typer.Option("--dir", "-d", help="Working directory for artifact extraction"),
    ] = None,
) -> None:
    """Extract code artifacts from existing trajectories.

    This retroactively extracts code artifacts (Write/Edit operations) from
    trajectories that were added before artifact extraction was implemented.
    """
    from icrl.validators.code import extract_code_artifacts

    config = Config.load()
    db_path = config.db_path or str(get_default_db_path())
    database = TrajectoryDatabase(db_path)

    work_dir = working_dir or Path.cwd()

    updated = 0
    for traj_id, trajectory in database._trajectories.items():
        meta = database._curation_metadata.get(traj_id)
        if meta is None:
            continue

        # Skip if already has artifacts
        if meta.code_artifacts:
            continue

        # Extract artifacts
        artifacts = extract_code_artifacts(trajectory, work_dir)
        if artifacts:
            meta.code_artifacts = artifacts
            updated += 1
            console.print(f"  Extracted {len(artifacts)} artifacts from {traj_id[:12]}...")

    if updated > 0:
        database._save_curation()
        console.print(f"\n[green]Updated {updated} trajectories with code artifacts.[/]")
    else:
        console.print("[dim]No trajectories needed artifact extraction.[/]")


if __name__ == "__main__":
    app()
