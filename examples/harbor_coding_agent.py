"""Harbor Coding Agent Example with ICRL Performance Improvement.

This example demonstrates how to create a coding agent using the ICRL framework
that is compatible with Harbor/Terminal-Bench 2.0. It shows how trajectory-based
learning improves agent performance on realistic coding tasks.

Key Features:
- Coding-focused environment with shell commands (similar to Harbor's sandboxed agents)
- Realistic software engineering tasks (file editing, code analysis, debugging)
- Performance improvement tracking before/after training
- Compatible with Harbor's BaseAgent interface pattern

Harbor (https://harborframework.com) is a framework for evaluating and optimizing
agents and models using sandboxed environments, and is the official harness for
Terminal-Bench 2.0.

Prerequisites:
- Add OPENAI_API_KEY to .env file (or another provider's key)
- Optionally set MODEL env var (default: gpt-4o-mini)

Run with: PYTHONPATH=. uv run python examples/harbor_coding_agent.py
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from icrl import Agent, LiteLLMProvider, Step, StepContext, Trajectory

load_dotenv()

console = Console()


# =============================================================================
# Coding Environment - Harbor-Compatible Sandbox Simulation
# =============================================================================


@dataclass
class CodingWorkspaceState:
    """State of the coding workspace (simulates a Harbor sandbox)."""

    cwd: str = "/workspace"
    last_output: str = ""
    files: dict[str, str] = field(default_factory=dict)
    directories: set[str] = field(default_factory=set)
    shell_history: list[str] = field(default_factory=list)

    def file_exists(self, path: str) -> bool:
        normalized = self._normalize_path(path)
        return normalized in self.files

    def dir_exists(self, path: str) -> bool:
        normalized = self._normalize_path(path)
        return normalized in self.directories

    def _normalize_path(self, path: str) -> str:
        if path.startswith("/"):
            return path
        return f"{self.cwd.rstrip('/')}/{path}"

    def get_file_content(self, path: str) -> str | None:
        normalized = self._normalize_path(path)
        return self.files.get(normalized)

    def write_file(self, path: str, content: str) -> None:
        normalized = self._normalize_path(path)
        self.files[normalized] = content

    def list_dir(self, path: str) -> list[str]:
        normalized = self._normalize_path(path)
        if normalized not in self.directories:
            return []

        entries = []
        prefix = normalized if normalized == "/" else normalized + "/"

        for file_path in self.files:
            if file_path.startswith(prefix):
                relative = file_path[len(prefix) :]
                if "/" not in relative:
                    entries.append(relative)

        for dir_path in self.directories:
            if dir_path.startswith(prefix) and dir_path != normalized:
                relative = dir_path[len(prefix) :]
                if "/" not in relative:
                    entries.append(relative + "/")

        return sorted(set(entries))


@dataclass
class CodingTask:
    """A coding task with verification (similar to Harbor task format)."""

    goal: str
    verify: Callable[[CodingWorkspaceState], bool]
    setup: Callable[[CodingWorkspaceState], None] | None = None
    difficulty: str = "medium"  # easy, medium, hard
    category: str = "general"  # debugging, refactoring, testing, etc.


def create_coding_workspace() -> tuple[dict[str, str], set[str]]:
    """Create a realistic coding workspace (simulates Harbor sandbox)."""
    files = {
        # Main application code
        "/workspace/src/main.py": '''"""Main application entry point."""
import logging
from app import create_app
from config import Config

logger = logging.getLogger(__name__)

def main():
    config = Config.load()
    app = create_app(config)
    logger.info(f"Starting app on port {config.port}")
    app.run(host="0.0.0.0", port=config.port)

if __name__ == "__main__":
    main()
''',
        # Config with a bug (wrong default port)
        "/workspace/src/config.py": '''"""Application configuration."""
import os
from dataclasses import dataclass

@dataclass
class Config:
    port: int = 8000
    debug: bool = False
    database_url: str = ""
    secret_key: str = ""

    @classmethod
    def load(cls) -> "Config":
        return cls(
            port=int(os.getenv("PORT", 8000)),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            database_url=os.getenv("DATABASE_URL", "sqlite:///app.db"),
            secret_key=os.getenv("SECRET_KEY", "dev-key"),
        )
''',
        # App factory
        "/workspace/src/app.py": '''"""Application factory."""
from flask import Flask
from config import Config

def create_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = config.debug

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.route("/api/data")
    def get_data():
        return {"data": [1, 2, 3]}

    return app
''',
        # Tests with missing test case
        "/workspace/tests/test_app.py": '''"""Application tests."""
import pytest
from src.app import create_app
from src.config import Config

@pytest.fixture
def app():
    config = Config(port=5000, debug=True)
    return create_app(config)

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}

# TODO: Add test for /api/data endpoint
''',
        # README
        "/workspace/README.md": """# Sample Application

A Flask-based web application.

## Requirements
- Python 3.12+
- Flask

## Configuration
- PORT: Application port (default: 3000)
- DEBUG: Enable debug mode
- DATABASE_URL: Database connection string
- SECRET_KEY: Secret key for sessions

## Running
```bash
python src/main.py
```

## Testing
```bash
pytest tests/
```
""",
        # pyproject.toml
        "/workspace/pyproject.toml": '''[project]
name = "sample-app"
version = "0.1.0"
dependencies = [
    "flask>=3.0.0",
    "pytest>=8.0.0",
]
''',
        # Utility module with code smell
        "/workspace/src/utils.py": '''"""Utility functions."""

def format_response(data):
    """Format API response."""
    # TODO: This function is too simple, could use better error handling
    return {"data": data, "success": True}

def validate_input(value):
    """Validate input value."""
    if value is None:
        return False
    if isinstance(value, str) and len(value) == 0:
        return False
    return True

def calculate_hash(data: str) -> str:
    """Calculate hash of data."""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()
''',
        # Database module (incomplete)
        "/workspace/src/db.py": '''"""Database operations."""
from typing import Any

class Database:
    def __init__(self, url: str):
        self.url = url
        self._connected = False

    def connect(self) -> bool:
        # TODO: Implement actual connection logic
        self._connected = True
        return True

    def query(self, sql: str) -> list[dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("Not connected to database")
        # Placeholder - would execute actual query
        return []

    def close(self):
        self._connected = False
''',
    }

    directories = {
        "/",
        "/workspace",
        "/workspace/src",
        "/workspace/tests",
        "/workspace/.git",
    }

    return files, directories


class CodingEnvironment:
    """Coding environment compatible with ICRL Environment protocol.

    This simulates a Harbor sandbox environment where a coding agent
    can execute shell commands to complete software engineering tasks.
    """

    def __init__(self, task: CodingTask) -> None:
        self._task = task
        self._state = CodingWorkspaceState()
        self._done = False
        self._max_actions = 25
        self._action_count = 0

    def reset(self, goal: str) -> str:
        """Reset environment for new episode (Harbor-compatible interface)."""
        files, directories = create_coding_workspace()
        self._state = CodingWorkspaceState(
            cwd="/workspace",
            last_output="",
            files=files,
            directories=directories,
        )
        self._done = False
        self._action_count = 0

        if self._task.setup:
            self._task.setup(self._state)

        return f"""You are a coding agent in a sandboxed Linux environment.
Current directory: {self._state.cwd}

Goal: {self._task.goal}

Available commands:
- ls [dir] - list directory contents
- cd <dir> - change directory
- cat <file> - display file contents
- grep <pattern> <file> - search in file
- find <pattern> - find files by name
- pwd - print working directory
- echo <text> > <file> - write to file
- sed -i 's/old/new/g' <file> - replace text in file
- head/tail <file> - show start/end of file
- python <file> - run Python script
- pytest <path> - run tests

You can chain commands with && and use standard shell syntax."""

    def step(self, action: str) -> tuple[str, bool, bool]:
        """Execute action and return (observation, done, success)."""
        self._action_count += 1
        action = action.strip()

        if self._action_count >= self._max_actions:
            self._done = True
            return "Maximum actions reached. Episode ended.", True, False

        observation = self._execute_command(action)
        self._state.last_output = observation
        self._state.shell_history.append(action)

        success = self._task.verify(self._state)
        if success:
            self._done = True
            return observation + "\n\n[Task completed successfully!]", True, True

        return observation, False, False

    def _execute_command(self, cmd: str) -> str:
        """Execute a shell command (simulated)."""
        cmd = cmd.strip()

        # Handle command chaining
        if " && " in cmd:
            results = []
            for subcmd in cmd.split(" && "):
                result = self._execute_single_command(subcmd.strip())
                results.append(result)
                if "Error:" in result:
                    break
            return "\n".join(results)

        return self._execute_single_command(cmd)

    def _execute_single_command(self, cmd: str) -> str:
        """Execute a single command."""
        parts = cmd.split(maxsplit=1)
        if not parts:
            return "Error: Empty command"

        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        handlers = {
            "ls": self._cmd_ls,
            "cd": self._cmd_cd,
            "cat": self._cmd_cat,
            "grep": self._cmd_grep,
            "find": self._cmd_find,
            "pwd": self._cmd_pwd,
            "echo": self._cmd_echo,
            "sed": self._cmd_sed,
            "head": self._cmd_head,
            "tail": self._cmd_tail,
            "python": self._cmd_python,
            "pytest": self._cmd_pytest,
        }

        if command in handlers:
            return handlers[command](args)
        return f"Error: Unknown command '{command}'"

    def _cmd_ls(self, args: str) -> str:
        path = args.strip() if args.strip() else self._state.cwd
        normalized = self._state._normalize_path(path)
        if not self._state.dir_exists(normalized):
            return f"ls: cannot access '{path}': No such file or directory"
        entries = self._state.list_dir(normalized)
        return "\n".join(entries) if entries else "(empty directory)"

    def _cmd_cd(self, args: str) -> str:
        if not args.strip():
            self._state.cwd = "/workspace"
            return f"Changed to /workspace"
        path = args.strip()
        normalized = self._state._normalize_path(path)
        if not self._state.dir_exists(normalized):
            return f"cd: {path}: No such file or directory"
        self._state.cwd = normalized
        return f"Changed to {normalized}"

    def _cmd_cat(self, args: str) -> str:
        if not args.strip():
            return "Error: cat requires a file argument"
        content = self._state.get_file_content(args.strip())
        if content is None:
            return f"cat: {args.strip()}: No such file or directory"
        return content

    def _cmd_grep(self, args: str) -> str:
        parts = args.split()
        if len(parts) < 2:
            return "Usage: grep <pattern> <file>"
        pattern = parts[0].strip("'\"")
        filepath = parts[1]
        content = self._state.get_file_content(filepath)
        if content is None:
            return f"grep: {filepath}: No such file or directory"
        matches = [line for line in content.split("\n") if pattern in line]
        return "\n".join(matches) if matches else f"(no matches for '{pattern}')"

    def _cmd_find(self, args: str) -> str:
        pattern = args.strip().lower()
        matches = [p for p in self._state.files if pattern in p.lower()]
        return "\n".join(sorted(matches)) if matches else f"No files matching '{pattern}'"

    def _cmd_pwd(self, args: str) -> str:
        return self._state.cwd

    def _cmd_echo(self, args: str) -> str:
        if ">" in args:
            parts = args.split(">", 1)
            text = parts[0].strip().strip("'\"")
            filepath = parts[1].strip()
            normalized = self._state._normalize_path(filepath)
            self._state.files[normalized] = text
            return f"Wrote to {normalized}"
        return args.strip().strip("'\"")

    def _cmd_sed(self, args: str) -> str:
        # Simple sed -i 's/old/new/g' file implementation
        if not args.startswith("-i "):
            return "Error: Only sed -i supported"
        args = args[3:].strip()

        # Parse s/old/new/g pattern
        if not args.startswith("'s/"):
            return "Error: Expected sed pattern 's/old/new/g'"

        try:
            # Find the closing quote and filename
            pattern_end = args.rfind("'")
            if pattern_end <= 2:
                return "Error: Invalid sed pattern"

            pattern_str = args[1:pattern_end]  # Remove outer quotes
            filepath = args[pattern_end + 1 :].strip()

            # Parse s/old/new/g
            parts = pattern_str.split("/")
            if len(parts) < 4:
                return "Error: Invalid sed pattern"

            old_text = parts[1]
            new_text = parts[2]

            content = self._state.get_file_content(filepath)
            if content is None:
                return f"sed: {filepath}: No such file or directory"

            new_content = content.replace(old_text, new_text)
            normalized = self._state._normalize_path(filepath)
            self._state.files[normalized] = new_content
            return f"Modified {filepath}"
        except Exception as e:
            return f"Error: sed failed - {e}"

    def _cmd_head(self, args: str) -> str:
        filepath = args.strip()
        content = self._state.get_file_content(filepath)
        if content is None:
            return f"head: {filepath}: No such file or directory"
        lines = content.split("\n")[:10]
        return "\n".join(lines)

    def _cmd_tail(self, args: str) -> str:
        filepath = args.strip()
        content = self._state.get_file_content(filepath)
        if content is None:
            return f"tail: {filepath}: No such file or directory"
        lines = content.split("\n")[-10:]
        return "\n".join(lines)

    def _cmd_python(self, args: str) -> str:
        return f"[Would execute: python {args}]\nExecution simulated - check file for syntax."

    def _cmd_pytest(self, args: str) -> str:
        return "[pytest output]\n1 passed, 0 failed\nTests completed."


# =============================================================================
# Coding Tasks - Harbor/Terminal-Bench Style
# =============================================================================


CODING_TASKS = {
    "training": [
        CodingTask(
            goal="Find the config.py file and identify the default port value",
            verify=lambda s: "8000" in s.last_output or "port" in s.last_output.lower(),
            difficulty="easy",
            category="code-analysis",
        ),
        CodingTask(
            goal="Fix the port configuration in config.py - change default from 8000 to 3000 to match README requirements",
            verify=lambda s: s.file_exists("/workspace/src/config.py")
            and "port:int=3000" in (s.get_file_content("/workspace/src/config.py") or "").lower().replace(" ", ""),
            difficulty="medium",
            category="debugging",
        ),
        CodingTask(
            goal="List all Python files in the src directory",
            verify=lambda s: "main.py" in s.last_output and "config.py" in s.last_output,
            difficulty="easy",
            category="navigation",
        ),
        CodingTask(
            goal="Find all TODO comments in the codebase",
            verify=lambda s: "TODO" in s.last_output,
            difficulty="easy",
            category="code-analysis",
        ),
        CodingTask(
            goal="Add a test for the /api/data endpoint in test_app.py",
            verify=lambda s: s.file_exists("/workspace/tests/test_app.py")
            and "test_data_endpoint" in (s.get_file_content("/workspace/tests/test_app.py") or "")
            or "api/data" in (s.get_file_content("/workspace/tests/test_app.py") or "")
            and "def test_" in (s.get_file_content("/workspace/tests/test_app.py") or "").split("TODO")[-1],
            difficulty="hard",
            category="testing",
        ),
    ],
    "evaluation": [
        CodingTask(
            goal="Find where the database URL is configured and identify its default value",
            verify=lambda s: "sqlite" in s.last_output.lower()
            or "database_url" in s.last_output.lower(),
            difficulty="easy",
            category="code-analysis",
        ),
        CodingTask(
            goal="Fix the debug mode default in config.py - it should be True for development",
            verify=lambda s: s.file_exists("/workspace/src/config.py")
            and "debug:bool=true" in (s.get_file_content("/workspace/src/config.py") or "").lower().replace(" ", ""),
            difficulty="medium",
            category="debugging",
        ),
        CodingTask(
            goal="Add input validation to the format_response function in utils.py",
            verify=lambda s: s.file_exists("/workspace/src/utils.py")
            and ("if " in (s.get_file_content("/workspace/src/utils.py") or "").split("def format_response")[1].split("def ")[0]
                 if "def format_response" in (s.get_file_content("/workspace/src/utils.py") or "") else False)
            or "validate" in (s.get_file_content("/workspace/src/utils.py") or "").lower(),
            difficulty="hard",
            category="refactoring",
        ),
    ],
}


# =============================================================================
# Prompts for Coding Agent
# =============================================================================

PLAN_PROMPT = """You are a skilled software engineer working in a sandboxed coding environment.
You have access to standard shell commands to navigate, read, and modify code.

Goal: {goal}

Previous successful approaches to similar coding tasks:
{examples}

Create a concise, numbered plan to accomplish this goal. Consider:
1. What files you need to find or examine
2. What changes need to be made
3. How to verify the changes are correct"""

REASON_PROMPT = """You are working on a coding task in a sandboxed environment.

Goal: {goal}

Your plan: {plan}

Previous steps:
{history}

Current observation:
{observation}

Similar situations from past experience:
{examples}

Analyze the current state:
- What did you learn from the last command output?
- Are you making progress toward the goal?
- What should be your next step?"""

ACT_PROMPT = """Goal: {goal}
Plan: {plan}

Steps so far:
{history}

Current observation:
{observation}

Your analysis: {reasoning}

Provide the SINGLE next shell command to execute.
Use standard Linux commands: ls, cd, cat, grep, find, sed, echo, etc.
Respond with ONLY the command, no explanation."""


# =============================================================================
# Step Callback for Visualization
# =============================================================================


def create_step_callback(show_details: bool = True):
    """Create a step callback for rich output."""

    def callback(step: Step, context: StepContext) -> None:
        if not show_details:
            return

        obs_preview = step.observation[:120].replace("\n", " ")
        if len(step.observation) > 120:
            obs_preview += "..."

        console.print(f"\n[dim]┌─ Obs:[/dim] {obs_preview}")
        console.print(f"[dim]├─ Think:[/dim] [blue]{step.reasoning[:100]}...[/blue]")
        console.print(f"[dim]└─ Cmd:[/dim] [green]{step.action}[/green]")

        if context.examples:
            console.print(f"   [dim]({len(context.examples)} examples retrieved)[/dim]")

    return callback


# =============================================================================
# Main Demo - Performance Improvement Showcase
# =============================================================================


async def run_baseline_evaluation(
    agent: Agent, tasks: list[CodingTask]
) -> tuple[int, list[Trajectory]]:
    """Run baseline evaluation without learned examples."""
    successes = 0
    trajectories = []

    for task in tasks:
        env = CodingEnvironment(task)
        trajectory = await agent.run(env, task.goal)
        trajectories.append(trajectory)
        if trajectory.success:
            successes += 1

    return successes, trajectories


async def run_training(agent: Agent, tasks: list[CodingTask]) -> list[Trajectory]:
    """Run training phase to accumulate successful trajectories."""
    trajectories = []

    for i, task in enumerate(tasks, 1):
        console.print(f"\n[bold]Training {i}/{len(tasks)}:[/bold] {task.goal[:60]}...")
        console.print(f"[dim]Category: {task.category} | Difficulty: {task.difficulty}[/dim]")

        env = CodingEnvironment(task)
        trajectory = await agent.train(env, task.goal)
        trajectories.append(trajectory)

        status = "[green]✓ Success[/green]" if trajectory.success else "[red]✗ Failed[/red]"
        console.print(f"{status} ({len(trajectory.steps)} steps)")

    return trajectories


async def run_demo() -> None:
    """Run the full Harbor coding agent demonstration."""
    model = os.environ.get("MODEL", "gpt-4o-mini")

    console.print(
        "\n[bold magenta]╔═══════════════════════════════════════════════════════════╗[/bold magenta]"
    )
    console.print(
        "[bold magenta]║  Harbor Coding Agent with ICRL Performance Improvement   ║[/bold magenta]"
    )
    console.print(
        "[bold magenta]║  Terminal-Bench 2.0 Compatible Agent Framework            ║[/bold magenta]"
    )
    console.print(
        "[bold magenta]╚═══════════════════════════════════════════════════════════╝[/bold magenta]"
    )
    console.print(f"\n[dim]Using model: {model}[/dim]")
    console.print(
        "[dim]This demo shows how ICRL's trajectory learning improves "
        "coding agent performance.[/dim]\n"
    )

    if "OPENAI_API_KEY" not in os.environ and "ANTHROPIC_API_KEY" not in os.environ:
        console.print(
            "[yellow]Warning: No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.[/yellow]"
        )
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "trajectories"

        llm = LiteLLMProvider(model=model, temperature=0.3, max_tokens=500)

        # Create agent with ICRL learning enabled
        agent = Agent(
            llm=llm,
            db_path=str(db_path),
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=3,  # Retrieve 3 most similar examples
            max_steps=20,
            on_step=create_step_callback(show_details=True),
        )

        # =================================================================
        # Phase 1: Baseline Evaluation (No Examples)
        # =================================================================
        console.print("\n[bold cyan]═══ Phase 1: Baseline Evaluation (No Examples) ═══[/bold cyan]")
        console.print("[dim]Testing agent on evaluation tasks without any learned examples...[/dim]")

        baseline_success, baseline_trajectories = await run_baseline_evaluation(
            agent, CODING_TASKS["evaluation"]
        )

        console.print(f"\n[bold]Baseline Results:[/bold] {baseline_success}/{len(CODING_TASKS['evaluation'])} tasks succeeded")

        # =================================================================
        # Phase 2: Training Phase
        # =================================================================
        console.print("\n[bold cyan]═══ Phase 2: Training Phase ═══[/bold cyan]")
        console.print("[dim]Agent learns from successful trajectories on training tasks...[/dim]")

        training_trajectories = await run_training(agent, CODING_TASKS["training"])
        training_success = sum(1 for t in training_trajectories if t.success)

        stats = agent.get_stats()
        console.print(f"\n[bold]Training Summary:[/bold]")
        console.print(f"  Tasks completed: [green]{training_success}/{len(CODING_TASKS['training'])}[/green]")
        console.print(f"  Trajectories stored: [cyan]{stats['total_trajectories']}[/cyan]")

        # =================================================================
        # Phase 3: Improved Evaluation (With Examples)
        # =================================================================
        console.print("\n[bold cyan]═══ Phase 3: Improved Evaluation (With Examples) ═══[/bold cyan]")
        console.print("[dim]Re-testing on evaluation tasks with learned examples...[/dim]")

        improved_success, improved_trajectories = await run_baseline_evaluation(
            agent, CODING_TASKS["evaluation"]
        )

        # =================================================================
        # Results Summary
        # =================================================================
        console.print("\n[bold cyan]═══ Performance Comparison ═══[/bold cyan]")

        table = Table(title="Evaluation Results")
        table.add_column("Task", style="cyan")
        table.add_column("Baseline", justify="center")
        table.add_column("With ICRL", justify="center")
        table.add_column("Improvement", justify="center")

        for i, task in enumerate(CODING_TASKS["evaluation"]):
            baseline_ok = baseline_trajectories[i].success
            improved_ok = improved_trajectories[i].success

            baseline_str = "[green]✓[/green]" if baseline_ok else "[red]✗[/red]"
            improved_str = "[green]✓[/green]" if improved_ok else "[red]✗[/red]"

            if improved_ok and not baseline_ok:
                improvement = "[green]↑ Fixed[/green]"
            elif improved_ok and baseline_ok:
                # Compare step counts
                baseline_steps = len(baseline_trajectories[i].steps)
                improved_steps = len(improved_trajectories[i].steps)
                if improved_steps < baseline_steps:
                    improvement = f"[green]↑ {baseline_steps - improved_steps} fewer steps[/green]"
                else:
                    improvement = "[dim]Same[/dim]"
            else:
                improvement = "[dim]—[/dim]"

            table.add_row(task.goal[:40] + "...", baseline_str, improved_str, improvement)

        console.print(table)

        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Baseline success rate: [yellow]{baseline_success}/{len(CODING_TASKS['evaluation'])}[/yellow]")
        console.print(f"  ICRL success rate:    [green]{improved_success}/{len(CODING_TASKS['evaluation'])}[/green]")

        improvement_pct = ((improved_success - baseline_success) / max(len(CODING_TASKS['evaluation']), 1)) * 100
        if improvement_pct > 0:
            console.print(f"  [bold green]Performance improved by {improvement_pct:.0f}%![/bold green]")

        # Show stored trajectories
        console.print("\n[bold]Stored Trajectories (Available for Future Tasks):[/bold]")
        for traj in agent.database.get_all()[:5]:
            status = "[green]✓[/green]" if traj.success else "[red]✗[/red]"
            console.print(f"  {status} {traj.goal[:55]}...")

        console.print(
            "\n[bold green]✓ Demo completed![/bold green]"
            "\n[dim]The agent learned from successful coding task trajectories "
            "and improved on similar evaluation tasks.[/dim]"
        )


def main() -> None:
    """Entry point."""
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
