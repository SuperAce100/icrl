#!/usr/bin/env python3
"""SGICL vs Zero-Shot Comparison Experiment.

This script runs a direct comparison between:
1. Zero-shot baseline: No retrieval, each task solved independently
2. SGICL (train mode): Sequential with trajectory storage and retrieval

The key insight: with SGICL, as the agent solves tasks, it stores successful
trajectories. Later tasks can retrieve these as in-context examples, improving
performance over time.

Usage:
    # Run with default settings (hello-world dataset, 10 tasks)
    PYTHONPATH=. uv run python examples/sgicl_comparison_experiment.py

    # Run on SWE-bench Django tasks
    PYTHONPATH=. uv run python examples/sgicl_comparison_experiment.py --dataset django

    # Run with more tasks
    PYTHONPATH=. uv run python examples/sgicl_comparison_experiment.py --n-tasks 20

Environment:
    MODEL: LLM model to use (default: gpt-4o-mini)
    OPENAI_API_KEY / ANTHROPIC_API_KEY: API credentials
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from icicl import Agent, LiteLLMProvider, Step, StepContext, Trajectory

load_dotenv()

console = Console()


# =============================================================================
# Simple Task Environment (for quick testing without Harbor)
# =============================================================================


@dataclass
class SimpleTask:
    """A simple verifiable task."""

    goal: str
    category: str
    verify: callable
    setup_files: dict[str, str] | None = None


@dataclass
class FileSystemState:
    """Simple file system state for testing."""

    cwd: str = "/workspace"
    files: dict[str, str] = None
    directories: set[str] = None
    last_output: str = ""

    def __post_init__(self):
        if self.files is None:
            self.files = {}
        if self.directories is None:
            self.directories = {"/", "/workspace", "/tmp"}

    def file_exists(self, path: str) -> bool:
        return self._normalize(path) in self.files

    def dir_exists(self, path: str) -> bool:
        return self._normalize(path) in self.directories

    def get_file(self, path: str) -> str | None:
        return self.files.get(self._normalize(path))

    def write_file(self, path: str, content: str):
        self.files[self._normalize(path)] = content

    def _normalize(self, path: str) -> str:
        if path.startswith("/"):
            return path
        return f"{self.cwd.rstrip('/')}/{path}"


class SimpleEnvironment:
    """Simple environment for testing SGICL without Harbor."""

    def __init__(self, task: SimpleTask, max_steps: int = 20):
        self._task = task
        self._state = FileSystemState()
        self._max_steps = max_steps
        self._step_count = 0

    def reset(self, goal: str) -> str:
        """Reset environment."""
        self._state = FileSystemState()
        self._step_count = 0

        # Set up initial files
        if self._task.setup_files:
            for path, content in self._task.setup_files.items():
                self._state.files[path] = content
                # Ensure parent directories exist
                parent = "/".join(path.split("/")[:-1])
                while parent and parent != "/":
                    self._state.directories.add(parent)
                    parent = "/".join(parent.split("/")[:-1])

        return f"""You are working in a sandboxed Linux environment.
Current directory: {self._state.cwd}

Goal: {self._task.goal}

Available commands: ls, cd, cat, grep, find, pwd, echo, sed, mkdir, cp, mv, rm
"""

    def step(self, action: str) -> tuple[str, bool, bool]:
        """Execute action."""
        self._step_count += 1
        action = action.strip()

        if self._step_count >= self._max_steps:
            return "Max steps reached.", True, False

        output = self._execute(action)
        self._state.last_output = output

        success = self._task.verify(self._state)
        if success:
            return output + "\n[SUCCESS]", True, True

        return output, False, False

    def _execute(self, cmd: str) -> str:
        """Execute a simple command."""
        parts = cmd.split(maxsplit=1)
        if not parts:
            return "Error: empty command"

        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "ls":
            path = args.strip() if args else self._state.cwd
            normalized = self._state._normalize(path)
            if normalized not in self._state.directories:
                return f"ls: {path}: No such directory"
            entries = []
            for f in self._state.files:
                if f.startswith(normalized + "/") or (
                    normalized == "/" and f.count("/") == 1
                ):
                    rel = f[len(normalized) :].lstrip("/")
                    if "/" not in rel:
                        entries.append(rel)
            for d in self._state.directories:
                if d.startswith(normalized + "/") and d != normalized:
                    rel = d[len(normalized) :].lstrip("/")
                    if "/" not in rel:
                        entries.append(rel + "/")
            return "\n".join(sorted(set(entries))) or "(empty)"

        elif command == "cd":
            path = args.strip() if args else "/workspace"
            normalized = self._state._normalize(path)
            if normalized not in self._state.directories:
                return f"cd: {path}: No such directory"
            self._state.cwd = normalized
            return f"Changed to {normalized}"

        elif command == "cat":
            path = args.strip()
            content = self._state.get_file(path)
            if content is None:
                return f"cat: {path}: No such file"
            return content

        elif command == "pwd":
            return self._state.cwd

        elif command == "grep":
            parts = args.split(maxsplit=1)
            if len(parts) < 2:
                return "Usage: grep PATTERN FILE"
            pattern, filepath = parts[0].strip("'\""), parts[1]
            content = self._state.get_file(filepath)
            if content is None:
                return f"grep: {filepath}: No such file"
            matches = [l for l in content.split("\n") if pattern in l]
            return "\n".join(matches) or f"(no matches for '{pattern}')"

        elif command == "find":
            pattern = args.strip().lower()
            matches = [f for f in self._state.files if pattern in f.lower()]
            return "\n".join(sorted(matches)) or f"No files matching '{pattern}'"

        elif command == "echo":
            if ">" in args:
                text, filepath = args.split(">", 1)
                text = text.strip().strip("'\"")
                filepath = filepath.strip()
                self._state.write_file(filepath, text)
                return f"Wrote to {filepath}"
            return args.strip().strip("'\"")

        elif command == "mkdir":
            path = args.strip().replace("-p", "").strip()
            normalized = self._state._normalize(path)
            self._state.directories.add(normalized)
            return f"Created {normalized}"

        elif command == "sed":
            # Simple sed -i 's/old/new/g' file
            if "-i" not in args:
                return "Only sed -i supported"
            args = args.replace("-i", "").strip()
            if args.startswith("'s/"):
                try:
                    end = args.rfind("'")
                    pattern = args[1:end]
                    filepath = args[end + 1 :].strip()
                    parts = pattern.split("/")
                    old, new = parts[1], parts[2]
                    content = self._state.get_file(filepath)
                    if content is None:
                        return f"sed: {filepath}: No such file"
                    self._state.write_file(filepath, content.replace(old, new))
                    return f"Modified {filepath}"
                except Exception as e:
                    return f"sed error: {e}"
            return "Invalid sed pattern"

        return f"Unknown command: {command}"


# =============================================================================
# Task Definitions
# =============================================================================


def create_coding_tasks() -> list[SimpleTask]:
    """Create a set of related coding tasks for testing SGICL."""
    return [
        # === Bug Fix Tasks (similar pattern: find file, identify bug, fix) ===
        SimpleTask(
            goal="Fix the port configuration in config.py - change default from 8000 to 3000",
            category="bugfix",
            verify=lambda s: "port = 3000"
            in (s.get_file("/workspace/src/config.py") or ""),
            setup_files={
                "/workspace/src/config.py": "# Config\nport = 8000\ndebug = False\n",
                "/workspace/src/main.py": "from config import port\nprint(f'Running on {port}')\n",
            },
        ),
        SimpleTask(
            goal="Fix the timeout setting in settings.py - change from 30 to 60 seconds",
            category="bugfix",
            verify=lambda s: "timeout = 60"
            in (s.get_file("/workspace/config/settings.py") or ""),
            setup_files={
                "/workspace/config/settings.py": "# Settings\ntimeout = 30\nmax_retries = 3\n",
            },
        ),
        SimpleTask(
            goal="Fix the max_connections value in db_config.py - change from 10 to 100",
            category="bugfix",
            verify=lambda s: "max_connections = 100"
            in (s.get_file("/workspace/db_config.py") or ""),
            setup_files={
                "/workspace/db_config.py": "# Database Config\nmax_connections = 10\npool_size = 5\n",
            },
        ),
        SimpleTask(
            goal="Fix the log_level in logging.py - change from 'INFO' to 'DEBUG'",
            category="bugfix",
            verify=lambda s: "log_level = 'DEBUG'"
            in (s.get_file("/workspace/src/logging.py") or "")
            or 'log_level = "DEBUG"' in (s.get_file("/workspace/src/logging.py") or ""),
            setup_files={
                "/workspace/src/logging.py": "# Logging\nlog_level = 'INFO'\nlog_format = 'json'\n",
            },
        ),
        # === Find Information Tasks (similar pattern: search and extract) ===
        SimpleTask(
            goal="Find and display the API key value in the secrets file",
            category="find",
            verify=lambda s: "sk-12345" in s.last_output,
            setup_files={
                "/workspace/.secrets": "API_KEY=sk-12345\nDB_PASS=secret\n",
            },
        ),
        SimpleTask(
            goal="Find the database password in the config files",
            category="find",
            verify=lambda s: "dbpass123" in s.last_output,
            setup_files={
                "/workspace/config/db.json": '{"host": "localhost", "password": "dbpass123"}\n',
            },
        ),
        SimpleTask(
            goal="Find the cache TTL value in the application config",
            category="find",
            verify=lambda s: "3600" in s.last_output,
            setup_files={
                "/workspace/app/config.yaml": "cache:\n  ttl: 3600\n  enabled: true\n",
            },
        ),
        # === File Creation Tasks (similar pattern: create file with content) ===
        SimpleTask(
            goal="Create a new file called test.py with a simple hello world function",
            category="create",
            verify=lambda s: s.file_exists("/workspace/test.py")
            and "def" in (s.get_file("/workspace/test.py") or "")
            and "hello" in (s.get_file("/workspace/test.py") or "").lower(),
            setup_files={},
        ),
        SimpleTask(
            goal="Create a README.md file with a project description",
            category="create",
            verify=lambda s: s.file_exists("/workspace/README.md")
            and len(s.get_file("/workspace/README.md") or "") > 10,
            setup_files={},
        ),
        SimpleTask(
            goal="Create a requirements.txt file with flask and requests packages",
            category="create",
            verify=lambda s: s.file_exists("/workspace/requirements.txt")
            and "flask" in (s.get_file("/workspace/requirements.txt") or "").lower()
            and "requests" in (s.get_file("/workspace/requirements.txt") or "").lower(),
            setup_files={},
        ),
    ]


# =============================================================================
# Prompts
# =============================================================================


PLAN_PROMPT = """You are working in a Linux terminal environment.

Goal: {goal}

=== RETRIEVED FEW-SHOT EXAMPLES ===
The following are successful demonstrations from SIMILAR PAST TASKS (not your current conversation).
Study these examples to learn effective strategies, then apply them to your current goal.

{examples}

=== END EXAMPLES ===

Create a SHORT numbered plan (max 4 steps) to accomplish this goal.
Learn from the examples above if they are relevant."""

REASON_PROMPT = """Goal: {goal}
Plan: {plan}

=== YOUR CURRENT TASK HISTORY ===
Previous steps in THIS task:
{history}

Current output:
{observation}

=== RETRIEVED FEW-SHOT EXAMPLES ===
These are successful steps from SIMILAR PAST TASKS (for reference, not your history):
{examples}
=== END EXAMPLES ===

Based on the examples and your current progress, what did you learn? What's next?"""

ACT_PROMPT = """Goal: {goal}

Steps done in THIS task:
{history}

Current output:
{observation}

Your thinking: {reasoning}

Output ONLY the next shell command (no explanation):"""


# =============================================================================
# Experiment Runner
# =============================================================================


async def run_single_task(
    agent: Agent,
    task: SimpleTask,
    task_idx: int,
    mode: str,
) -> tuple[bool, int, float, Trajectory]:
    """Run a single task and return (success, steps, time, trajectory)."""
    import time

    env = SimpleEnvironment(task)
    start = time.time()

    if mode == "train":
        trajectory = await agent.train(env, task.goal)
    else:
        trajectory = await agent.run(env, task.goal)

    elapsed = time.time() - start
    return trajectory.success, len(trajectory.steps), elapsed, trajectory


def load_checkpoint(checkpoint_path: Path) -> dict | None:
    """Load existing checkpoint if it exists."""
    if checkpoint_path.exists():
        with open(checkpoint_path) as f:
            return json.load(f)
    return None


def save_checkpoint(results: dict, checkpoint_path: Path) -> None:
    """Save current results to checkpoint file."""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w") as f:
        json.dump(results, f, indent=2, default=str)


async def run_experiment(
    tasks: list[SimpleTask],
    model: str,
    max_steps: int = 15,
    checkpoint_path: Path | None = None,
) -> dict:
    """Run the full 3-way comparison experiment with resume support.

    Runs 3 conditions:
    1. Zero-shot: No examples (k=0)
    2. SGICL Online: Examples accumulated on-the-fly
    3. SGICL Full DB: All examples available from start (pre-loaded)

    Args:
        tasks: List of tasks to run
        model: LLM model name
        max_steps: Max steps per task
        checkpoint_path: Path to save/load checkpoints for resuming
    """

    # Try to load existing checkpoint
    existing_results = None
    if checkpoint_path:
        existing_results = load_checkpoint(checkpoint_path)
        if existing_results:
            console.print(
                f"[yellow]Resuming from checkpoint with "
                f"{len(existing_results.get('zero_shot', {}).get('successes', []))} zero-shot, "
                f"{len(existing_results.get('sgicl_online', {}).get('successes', []))} online, "
                f"{len(existing_results.get('sgicl_full_db', {}).get('successes', []))} full-db "
                f"tasks completed[/yellow]\n"
            )

    # Initialize or restore results
    if existing_results:
        results = existing_results
        # Ensure n_tasks matches current run
        results["n_tasks"] = len(tasks)
    else:
        results = {
            "model": model,
            "n_tasks": len(tasks),
            "timestamp": datetime.now().isoformat(),
            "zero_shot": {"successes": [], "steps": [], "times": []},
            "sgicl_online": {"successes": [], "steps": [], "times": [], "db_size": []},
            "sgicl_full_db": {"successes": [], "steps": [], "times": [], "db_size": []},
        }

    # GPT-5 only supports temperature=1, use 0.7 for others (not 0)
    temp = 1.0 if "gpt-5" in model.lower() else 0.7
    llm = LiteLLMProvider(model=model, temperature=temp, max_tokens=1024)

    # Track where we left off for each condition
    zs_start = len(results["zero_shot"]["successes"])
    online_start = len(results["sgicl_online"]["successes"])
    full_start = len(results["sgicl_full_db"]["successes"])

    # =========================================================================
    # Condition 1: Zero-shot baseline (no retrieval, no storage)
    # =========================================================================
    if zs_start < len(tasks):
        console.print(
            "\n[bold cyan]═══ Condition 1: Zero-Shot (No Examples) ═══[/bold cyan]"
        )
        if zs_start > 0:
            console.print(f"[yellow]Resuming from task {zs_start + 1}[/yellow]")
        console.print("[dim]k=0, each task solved independently[/dim]\n")

        zs_trajectories: list[Trajectory] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            zs_db_path = f"{tmpdir}/zeroshot_db"

            zs_agent = Agent(
                llm=llm,
                db_path=zs_db_path,
                plan_prompt=PLAN_PROMPT,
                reason_prompt=REASON_PROMPT,
                act_prompt=ACT_PROMPT,
                k=0,  # NO retrieval
                max_steps=max_steps,
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                for i, task in enumerate(tasks):
                    # Skip already completed tasks
                    if i < zs_start:
                        continue

                    task_id = progress.add_task(
                        f"[{i + 1}/{len(tasks)}] {task.goal[:50]}...", total=1
                    )

                    success, steps, time_taken, trajectory = await run_single_task(
                        zs_agent, task, i, mode="run"
                    )

                    results["zero_shot"]["successes"].append(success)
                    results["zero_shot"]["steps"].append(steps)
                    results["zero_shot"]["times"].append(time_taken)

                    # Collect successful trajectories for full-db condition
                    if success:
                        zs_trajectories.append(trajectory)

                    status = "[green]✓[/green]" if success else "[red]✗[/red]"
                    progress.update(
                        task_id,
                        completed=1,
                        description=f"{status} {task.goal[:45]}...",
                    )

                    # Save checkpoint after each task
                    if checkpoint_path:
                        # Store trajectories as serializable data
                        results["_zs_trajectories"] = [
                            {"goal": t.goal, "plan": t.plan, "success": t.success}
                            for t in zs_trajectories
                        ]
                        save_checkpoint(results, checkpoint_path)
    else:
        console.print("[dim]Zero-shot condition already complete, skipping...[/dim]")
        zs_trajectories = []  # Will be loaded from online results if needed

    # =========================================================================
    # Condition 2: SGICL Online (examples accumulated on-the-fly)
    # =========================================================================
    if online_start < len(tasks):
        console.print(
            "\n[bold cyan]═══ Condition 2: SGICL Online (On-the-fly) ═══[/bold cyan]"
        )
        if online_start > 0:
            console.print(f"[yellow]Resuming from task {online_start + 1}[/yellow]")
        console.print(
            "[dim]k=3, DB starts empty, accumulates successful trajectories[/dim]\n"
        )

        # Use persistent DB path for online condition (to support resume)
        online_db_path = (
            checkpoint_path.parent / "online_db"
            if checkpoint_path
            else Path(tempfile.mkdtemp()) / "online_db"
        )
        online_db_path.parent.mkdir(parents=True, exist_ok=True)

        online_agent = Agent(
            llm=llm,
            db_path=str(online_db_path),
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=3,  # Retrieve top 3 examples
            max_steps=max_steps,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for i, task in enumerate(tasks):
                # Skip already completed tasks
                if i < online_start:
                    continue

                db_size = len(online_agent.database)
                task_id = progress.add_task(
                    f"[{i + 1}/{len(tasks)}] (db: {db_size}) {task.goal[:40]}...",
                    total=1,
                )

                success, steps, time_taken, _ = await run_single_task(
                    online_agent, task, i, mode="train"
                )

                results["sgicl_online"]["successes"].append(success)
                results["sgicl_online"]["steps"].append(steps)
                results["sgicl_online"]["times"].append(time_taken)
                results["sgicl_online"]["db_size"].append(len(online_agent.database))

                status = "[green]✓[/green]" if success else "[red]✗[/red]"
                progress.update(
                    task_id,
                    completed=1,
                    description=f"{status} (db: {len(online_agent.database)}) {task.goal[:35]}...",
                )

                # Save checkpoint after each task
                if checkpoint_path:
                    save_checkpoint(results, checkpoint_path)
    else:
        console.print("[dim]SGICL Online condition already complete, skipping...[/dim]")

    # =========================================================================
    # Condition 3: SGICL Full DB (all examples available from start)
    # =========================================================================
    if full_start < len(tasks):
        console.print(
            "\n[bold cyan]═══ Condition 3: SGICL Full DB (Pre-loaded) ═══[/bold cyan]"
        )
        if full_start > 0:
            console.print(f"[yellow]Resuming from task {full_start + 1}[/yellow]")
        console.print(
            f"[dim]k=3, DB pre-loaded with {len(zs_trajectories)} successful trajectories[/dim]\n"
        )

        # Use persistent DB path for full-db condition (to support resume)
        full_db_path = (
            checkpoint_path.parent / "full_db"
            if checkpoint_path
            else Path(tempfile.mkdtemp()) / "full_db"
        )
        full_db_path.parent.mkdir(parents=True, exist_ok=True)

        full_db_agent = Agent(
            llm=llm,
            db_path=str(full_db_path),
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=3,  # Retrieve top 3 examples
            max_steps=max_steps,
            seed_trajectories=zs_trajectories
            if full_start == 0
            else None,  # Only seed on fresh start
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for i, task in enumerate(tasks):
                # Skip already completed tasks
                if i < full_start:
                    continue

                db_size = len(full_db_agent.database)
                task_id = progress.add_task(
                    f"[{i + 1}/{len(tasks)}] (db: {db_size}) {task.goal[:40]}...",
                    total=1,
                )

                success, steps, time_taken, _ = await run_single_task(
                    full_db_agent, task, i, mode="train"
                )

                results["sgicl_full_db"]["successes"].append(success)
                results["sgicl_full_db"]["steps"].append(steps)
                results["sgicl_full_db"]["times"].append(time_taken)
                results["sgicl_full_db"]["db_size"].append(len(full_db_agent.database))

                status = "[green]✓[/green]" if success else "[red]✗[/red]"
                progress.update(
                    task_id,
                    completed=1,
                    description=f"{status} (db: {len(full_db_agent.database)}) {task.goal[:35]}...",
                )

                # Save checkpoint after each task
                if checkpoint_path:
                    save_checkpoint(results, checkpoint_path)
    else:
        console.print(
            "[dim]SGICL Full DB condition already complete, skipping...[/dim]"
        )

    # Final save
    if checkpoint_path:
        save_checkpoint(results, checkpoint_path)
        console.print(f"\n[dim]Results saved to {checkpoint_path}[/dim]")

    return results


def print_results(results: dict):
    """Print experiment results in a nice table."""
    console.print("\n")
    console.print(
        Panel.fit("[bold]3-Way Comparison Results[/bold]", border_style="cyan")
    )

    n = results["n_tasks"]

    # Extract success counts
    zs_success = sum(results["zero_shot"]["successes"])
    online_success = sum(results["sgicl_online"]["successes"])
    full_success = sum(results["sgicl_full_db"]["successes"])

    # Summary table
    table = Table(title="Zero-Shot vs SGICL Online vs SGICL Full DB")
    table.add_column("Metric", style="cyan")
    table.add_column("Zero-Shot\n(k=0)", justify="center")
    table.add_column("SGICL Online\n(k=3, on-the-fly)", justify="center")
    table.add_column("SGICL Full DB\n(k=3, pre-loaded)", justify="center")

    # Success rates
    table.add_row(
        "Success Rate",
        f"{zs_success}/{n} ({100 * zs_success / n:.0f}%)",
        f"{online_success}/{n} ({100 * online_success / n:.0f}%)",
        f"{full_success}/{n} ({100 * full_success / n:.0f}%)",
    )

    # Average steps
    zs_avg_steps = sum(results["zero_shot"]["steps"]) / n
    online_avg_steps = sum(results["sgicl_online"]["steps"]) / n
    full_avg_steps = sum(results["sgicl_full_db"]["steps"]) / n
    table.add_row(
        "Avg Steps",
        f"{zs_avg_steps:.1f}",
        f"{online_avg_steps:.1f}",
        f"{full_avg_steps:.1f}",
    )

    # Average time
    zs_avg_time = sum(results["zero_shot"]["times"]) / n
    online_avg_time = sum(results["sgicl_online"]["times"]) / n
    full_avg_time = sum(results["sgicl_full_db"]["times"]) / n
    table.add_row(
        "Avg Time (s)",
        f"{zs_avg_time:.1f}",
        f"{online_avg_time:.1f}",
        f"{full_avg_time:.1f}",
    )

    # Final DB sizes
    online_final_db = (
        results["sgicl_online"]["db_size"][-1]
        if results["sgicl_online"]["db_size"]
        else 0
    )
    full_final_db = (
        results["sgicl_full_db"]["db_size"][-1]
        if results["sgicl_full_db"]["db_size"]
        else 0
    )
    table.add_row(
        "Final DB Size",
        "0",
        str(online_final_db),
        str(full_final_db),
    )

    console.print(table)

    # Delta table
    console.print("\n[bold]Improvements vs Zero-Shot:[/bold]")
    delta_table = Table()
    delta_table.add_column("Condition", style="cyan")
    delta_table.add_column("Δ Success", justify="center")
    delta_table.add_column("Δ Steps", justify="center")

    online_delta = online_success - zs_success
    full_delta = full_success - zs_success
    online_step_delta = online_avg_steps - zs_avg_steps
    full_step_delta = full_avg_steps - zs_avg_steps

    delta_table.add_row(
        "SGICL Online",
        f"[green]+{online_delta}[/green]"
        if online_delta > 0
        else f"[red]{online_delta}[/red]"
        if online_delta < 0
        else "0",
        f"[green]{online_step_delta:+.1f}[/green]"
        if online_step_delta < 0
        else f"{online_step_delta:+.1f}",
    )
    delta_table.add_row(
        "SGICL Full DB",
        f"[green]+{full_delta}[/green]"
        if full_delta > 0
        else f"[red]{full_delta}[/red]"
        if full_delta < 0
        else "0",
        f"[green]{full_step_delta:+.1f}[/green]"
        if full_step_delta < 0
        else f"{full_step_delta:+.1f}",
    )
    console.print(delta_table)

    # Per-task breakdown
    console.print("\n[bold]Per-Task Breakdown:[/bold]")
    task_table = Table()
    task_table.add_column("#", style="dim")
    task_table.add_column("ZS", justify="center")
    task_table.add_column("Online", justify="center")
    task_table.add_column("Full", justify="center")
    task_table.add_column("Online DB", justify="center", style="dim")
    task_table.add_column("Full DB", justify="center", style="dim")

    for i in range(n):
        zs_ok = (
            "[green]✓[/green]"
            if results["zero_shot"]["successes"][i]
            else "[red]✗[/red]"
        )
        online_ok = (
            "[green]✓[/green]"
            if results["sgicl_online"]["successes"][i]
            else "[red]✗[/red]"
        )
        full_ok = (
            "[green]✓[/green]"
            if results["sgicl_full_db"]["successes"][i]
            else "[red]✗[/red]"
        )
        online_db = results["sgicl_online"]["db_size"][i]
        full_db = results["sgicl_full_db"]["db_size"][i]
        task_table.add_row(
            str(i + 1), zs_ok, online_ok, full_ok, str(online_db), str(full_db)
        )

    console.print(task_table)

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    if full_success > zs_success:
        improvement = (full_success - zs_success) / max(zs_success, 1) * 100
        console.print(
            f"[bold green]✓ SGICL Full DB improved by {full_success - zs_success} tasks ({improvement:.0f}% relative)[/bold green]"
        )
    if online_success > zs_success:
        improvement = (online_success - zs_success) / max(zs_success, 1) * 100
        console.print(
            f"[bold green]✓ SGICL Online improved by {online_success - zs_success} tasks ({improvement:.0f}% relative)[/bold green]"
        )
    if full_success <= zs_success and online_success <= zs_success:
        console.print(
            "[yellow]No improvement observed - try different tasks or more examples[/yellow]"
        )


async def main():
    parser = argparse.ArgumentParser(description="3-Way SGICL Comparison Experiment")
    parser.add_argument(
        "--n-tasks", type=int, default=10, help="Number of tasks to run"
    )
    parser.add_argument("--model", type=str, default=None, help="Model to use")
    parser.add_argument("--max-steps", type=int, default=15, help="Max steps per task")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Checkpoint file for resume support (e.g., experiment_checkpoint.json)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing checkpoint (requires --checkpoint)",
    )
    args = parser.parse_args()

    model = args.model or os.environ.get("MODEL", "gpt-4o-mini")

    # Setup checkpoint path
    checkpoint_path = None
    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint)
    elif args.resume:
        # Default checkpoint location
        checkpoint_path = Path("sgicl_experiment_checkpoint.json")

    resume_str = ""
    if checkpoint_path and checkpoint_path.exists():
        resume_str = " | [yellow]RESUMING[/yellow]"

    console.print(
        Panel.fit(
            "[bold magenta]3-Way SGICL Comparison Experiment[/bold magenta]\n"
            f"Model: {model} | Tasks: {args.n_tasks} | Max Steps: {args.max_steps}{resume_str}\n"
            "[dim]Conditions: Zero-Shot | SGICL Online | SGICL Full DB[/dim]",
            border_style="magenta",
        )
    )

    if checkpoint_path:
        console.print(f"[dim]Checkpoint: {checkpoint_path}[/dim]")

    # Check for API key
    if "OPENAI_API_KEY" not in os.environ and "ANTHROPIC_API_KEY" not in os.environ:
        console.print("[red]Error: Set OPENAI_API_KEY or ANTHROPIC_API_KEY[/red]")
        return

    # Create tasks
    all_tasks = create_coding_tasks()
    tasks = (all_tasks * ((args.n_tasks // len(all_tasks)) + 1))[: args.n_tasks]

    console.print(
        f"[dim]Running {len(tasks)} tasks across {len(set(t.category for t in tasks))} categories[/dim]"
    )

    # Run 3-way experiment with checkpoint support
    results = await run_experiment(
        tasks, model, args.max_steps, checkpoint_path=checkpoint_path
    )

    # Print results
    print_results(results)

    # Save final results
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, indent=2, default=str))
        console.print(f"\n[dim]Final results saved to {output_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
