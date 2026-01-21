"""Test example demonstrating icrl with a mock LLM.

This script runs without requiring any API keys, demonstrating:
- Basic training loop with trajectory accumulation
- Trajectory retrieval for in-context examples
- Step callbacks for observing agent behavior
- Database persistence across sessions

Run with: uv run examples/test_with_mock.py
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from rich.console import Console

from examples.file_api_env import FileSystemEnvironment, Task
from examples.mock_llm import MockLLMProvider
from examples.tasks import EVAL_TASKS, TRAINING_TASKS
from icrl import Agent, Step, StepContext

console = Console()

PLAN_PROMPT = """You are a file system navigation agent.

Goal: {goal}

Previous successful examples:
{examples}

Create a plan to accomplish the goal. Be concise."""

REASON_PROMPT = """Goal: {goal}
Plan: {plan}

Previous steps:
{history}

Current observation: {observation}

Examples of similar situations:
{examples}

Think: What should you do next and why?"""

ACT_PROMPT = """Goal: {goal}
Plan: {plan}

Previous steps:
{history}

Current observation: {observation}
Reasoning: {reasoning}

Examples:
{examples}

Action: Provide ONLY the command to execute (e.g., "ls", "cd /home", "cat file.txt")"""


def step_callback(step: Step, context: StepContext) -> None:
    """Callback to display each step with rich formatting."""
    console.print(f"\n[dim]Observation:[/dim] {step.observation[:100]}...")
    console.print(f"[blue]Reasoning:[/blue] {step.reasoning}")
    console.print(f"[green]Action:[/green] {step.action}")

    if context.examples:
        console.print(
            f"[dim]Retrieved {len(context.examples)} example(s) for context[/dim]"
        )


def create_env_factory(task: Task):
    """Create a factory function for the environment."""

    def factory() -> FileSystemEnvironment:
        return FileSystemEnvironment(task)

    return factory


async def run_training_demo(db_path: Path) -> None:
    """Run the training demonstration."""
    console.print("\n[bold cyan]═══ Training Phase ═══[/bold cyan]")
    console.print(
        "[dim]Training the agent on tasks. "
        "Successful trajectories will be stored.[/dim]\n"
    )

    llm = MockLLMProvider()
    agent = Agent(
        llm=llm,
        db_path=str(db_path),
        plan_prompt=PLAN_PROMPT,
        reason_prompt=REASON_PROMPT,
        act_prompt=ACT_PROMPT,
        k=2,
        max_steps=10,
        on_step=step_callback,
    )

    for i, task in enumerate(TRAINING_TASKS, 1):
        console.print(f"\n[bold]Task {i}/{len(TRAINING_TASKS)}:[/bold] {task.goal}")
        console.print("[dim]─" * 60 + "[/dim]")

        env = FileSystemEnvironment(task)
        trajectory = await agent.train(env, task.goal)

        if trajectory.success:
            console.print(
                f"[green]✓ Success![/green] Completed in {len(trajectory.steps)} steps"
            )
        else:
            console.print(f"[red]✗ Failed[/red] after {len(trajectory.steps)} steps")

    stats = agent.get_stats()
    console.print("\n[bold]Training Statistics:[/bold]")
    console.print(f"  Total trajectories: [cyan]{stats['total_trajectories']}[/cyan]")
    console.print(f"  Successful: [green]{stats['successful_trajectories']}[/green]")
    console.print(f"  Success rate: [yellow]{stats['success_rate']:.1%}[/yellow]")


async def run_persistence_demo(db_path: Path) -> None:
    """Demonstrate database persistence by loading from disk."""
    console.print("\n[bold cyan]═══ Persistence Demo ═══[/bold cyan]")
    console.print(
        "[dim]Creating a new agent that loads trajectories from disk...[/dim]\n"
    )

    llm = MockLLMProvider()
    new_agent = Agent(
        llm=llm,
        db_path=str(db_path),
        plan_prompt=PLAN_PROMPT,
        reason_prompt=REASON_PROMPT,
        act_prompt=ACT_PROMPT,
        k=2,
        max_steps=10,
    )

    trajectories = new_agent.database.get_all()
    console.print(f"[green]Loaded {len(trajectories)} trajectories from disk[/green]")

    for traj in trajectories[:3]:
        console.print(f"  [dim]•[/dim] Goal: {traj.goal[:50]}...")
        console.print(
            f"    [dim]Steps: {len(traj.steps)}, Success: {traj.success}[/dim]"
        )


async def run_evaluation_demo(db_path: Path) -> None:
    """Run evaluation on held-out tasks."""
    console.print("\n[bold cyan]═══ Evaluation Phase ═══[/bold cyan]")
    console.print(
        "[dim]Testing on held-out tasks using frozen database "
        "(no new learning)...[/dim]\n"
    )

    llm = MockLLMProvider()
    agent = Agent(
        llm=llm,
        db_path=str(db_path),
        plan_prompt=PLAN_PROMPT,
        reason_prompt=REASON_PROMPT,
        act_prompt=ACT_PROMPT,
        k=2,
        max_steps=10,
    )

    successes = 0
    for i, task in enumerate(EVAL_TASKS, 1):
        console.print(f"\n[bold]Eval Task {i}/{len(EVAL_TASKS)}:[/bold] {task.goal}")

        env = FileSystemEnvironment(task)
        trajectory = await agent.run(env, task.goal)

        if trajectory.success:
            console.print(
                f"  [green]✓ Success[/green] in {len(trajectory.steps)} steps"
            )
            successes += 1
        else:
            console.print("  [red]✗ Failed[/red]")

    console.print(
        f"\n[bold]Evaluation Results:[/bold] "
        f"{successes}/{len(EVAL_TASKS)} tasks succeeded"
    )


async def run_retrieval_demo(db_path: Path) -> None:
    """Demonstrate trajectory retrieval."""
    console.print("\n[bold cyan]═══ Retrieval Demo ═══[/bold cyan]")
    console.print(
        "[dim]Showing how similar trajectories are retrieved for new goals...[/dim]\n"
    )

    llm = MockLLMProvider()
    agent = Agent(
        llm=llm,
        db_path=str(db_path),
        plan_prompt=PLAN_PROMPT,
        reason_prompt=REASON_PROMPT,
        act_prompt=ACT_PROMPT,
        k=3,
        max_steps=10,
    )

    test_queries = [
        "Find configuration files in the system",
        "Navigate to the projects folder",
        "Copy a file to backup",
    ]

    for query in test_queries:
        console.print(f"\n[bold]Query:[/bold] {query}")
        results = agent.database.search(query, k=2)

        if results:
            for j, traj in enumerate(results, 1):
                console.print(f"  [cyan]{j}.[/cyan] {traj.goal[:60]}...")
                console.print(
                    f"     [dim]Success: {traj.success}, Steps: {len(traj.steps)}[/dim]"
                )
        else:
            console.print("  [dim]No matching trajectories found[/dim]")


async def main() -> None:
    """Run all demonstrations."""
    console.print(
        "[bold magenta]╔══════════════════════════════════════════╗[/bold magenta]"
    )
    console.print(
        "[bold magenta]║   ICRL File System Agent - Mock Demo   ║[/bold magenta]"
    )
    console.print(
        "[bold magenta]╚══════════════════════════════════════════╝[/bold magenta]"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "trajectories"

        await run_training_demo(db_path)
        await run_persistence_demo(db_path)
        await run_retrieval_demo(db_path)
        await run_evaluation_demo(db_path)

        console.print("\n[bold green]✓ All demonstrations completed![/bold green]")
        console.print(f"[dim]Temporary database was at: {db_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
