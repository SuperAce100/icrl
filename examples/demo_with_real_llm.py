"""Demo example using a real LLM for file system navigation.

This script demonstrates icicl with actual LLM calls, showing how the agent:
- Learns from successful trajectories over multiple episodes
- Retrieves relevant examples to improve performance
- Reasons through multi-step tasks

Prerequisites:
- Add OPENAI_API_KEY to .env file (or another provider's key)
- Optionally set MODEL env var (default: gpt-4o-mini)

Run with: PYTHONPATH=. uv run python examples/demo_with_real_llm.py
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

from examples.file_api_env import FileSystemEnvironment
from examples.tasks import EVAL_TASKS, TRAINING_TASKS
from icicl import Agent, LiteLLMProvider, Step, StepContext

console = Console()

PLAN_PROMPT = """You are a file system navigation agent. You can execute commands like:
- ls [dir] - list directory contents
- cd <dir> - change directory
- cat <file> - display file contents
- find <pattern> - search for files matching pattern
- pwd - print working directory
- mkdir <name> - create a directory
- cp <src> <dst> - copy a file

Goal: {goal}

Previous successful examples from similar tasks:
{examples}

Create a brief, numbered plan to accomplish the goal. Be specific about the commands you'll use."""

REASON_PROMPT = """You are navigating a file system to accomplish a goal.

Goal: {goal}

Your plan: {plan}

Previous steps you've taken:
{history}

Current observation: {observation}

Examples from similar situations:
{examples}

Think step by step: What have you learned from the observation? What should you do next to make progress toward the goal?"""

ACT_PROMPT = """Goal: {goal}
Plan: {plan}

Steps so far:
{history}

Current observation: {observation}

Your reasoning: {reasoning}

Based on your reasoning, what is the SINGLE next command to execute?
Respond with ONLY the command (e.g., "ls", "cd /home/user", "cat config.json").
Do not include any explanation, just the command."""


def step_callback(step: Step, context: StepContext) -> None:
    """Callback to display each step with rich formatting."""
    obs_preview = step.observation[:150].replace("\n", " ")
    if len(step.observation) > 150:
        obs_preview += "..."

    console.print(f"\n[dim]┌─ Observation:[/dim]")
    console.print(f"[dim]│[/dim]  {obs_preview}")
    console.print(f"[dim]├─ Reasoning:[/dim]")
    console.print(f"[blue]│[/blue]  {step.reasoning[:200]}...")
    console.print(f"[dim]└─ Action:[/dim] [green]{step.action}[/green]")

    if context.examples:
        console.print(
            f"   [dim](Using {len(context.examples)} retrieved example(s))[/dim]"
        )


async def run_demo() -> None:
    """Run the full demonstration."""
    model = os.environ.get("MODEL", "gpt-4o-mini")

    console.print("[bold magenta]╔═══════════════════════════════════════════════╗[/bold magenta]")
    console.print("[bold magenta]║   ICICL File System Agent - Real LLM Demo    ║[/bold magenta]")
    console.print("[bold magenta]╚═══════════════════════════════════════════════╝[/bold magenta]")
    console.print(f"\n[dim]Using model: {model}[/dim]")

    if "OPENAI_API_KEY" not in os.environ and "ANTHROPIC_API_KEY" not in os.environ:
        console.print("[yellow]Warning: No API key found. Set OPENAI_API_KEY or another provider's key.[/yellow]")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "trajectories"

        llm = LiteLLMProvider(
            model=model,
            temperature=0.3,
            max_tokens=500,
        )

        agent = Agent(
            llm=llm,
            db_path=str(db_path),
            plan_prompt=PLAN_PROMPT,
            reason_prompt=REASON_PROMPT,
            act_prompt=ACT_PROMPT,
            k=2,
            max_steps=15,
            on_step=step_callback,
        )

        console.print("\n[bold cyan]═══ Training Phase ═══[/bold cyan]")
        console.print("[dim]The agent will learn from successful episodes...[/dim]")

        training_results = []
        for i, task in enumerate(TRAINING_TASKS, 1):
            console.print(f"\n[bold]Training Task {i}/{len(TRAINING_TASKS)}:[/bold]")
            console.print(f"  [yellow]Goal:[/yellow] {task.goal}")
            console.print("[dim]" + "─" * 50 + "[/dim]")

            env = FileSystemEnvironment(task)

            try:
                trajectory = await agent.train(env, task.goal)

                if trajectory.success:
                    console.print(
                        f"\n[green]✓ Success![/green] Completed in {len(trajectory.steps)} steps"
                    )
                    training_results.append(True)
                else:
                    console.print(
                        f"\n[red]✗ Failed[/red] after {len(trajectory.steps)} steps"
                    )
                    training_results.append(False)
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}")
                training_results.append(False)

        stats = agent.get_stats()
        console.print("\n[bold]Training Summary:[/bold]")
        console.print(f"  Trajectories stored: [cyan]{stats['total_trajectories']}[/cyan]")
        console.print(f"  Success rate: [yellow]{stats['success_rate']:.1%}[/yellow]")

        console.print("\n[bold cyan]═══ Evaluation Phase ═══[/bold cyan]")
        console.print("[dim]Testing on new tasks using learned examples (no new learning)...[/dim]")

        eval_results = []
        for i, task in enumerate(EVAL_TASKS, 1):
            console.print(f"\n[bold]Eval Task {i}/{len(EVAL_TASKS)}:[/bold]")
            console.print(f"  [yellow]Goal:[/yellow] {task.goal}")
            console.print("[dim]" + "─" * 50 + "[/dim]")

            retrieved = agent.database.search(task.goal, k=2)
            if retrieved:
                console.print(f"  [dim]Retrieved examples for planning:[/dim]")
                for r in retrieved:
                    console.print(f"    [dim]• {r.goal[:50]}...[/dim]")

            env = FileSystemEnvironment(task)

            try:
                trajectory = await agent.run(env, task.goal)

                if trajectory.success:
                    console.print(
                        f"\n[green]✓ Success![/green] Completed in {len(trajectory.steps)} steps"
                    )
                    eval_results.append(True)
                else:
                    console.print(f"\n[red]✗ Failed[/red]")
                    eval_results.append(False)
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}")
                eval_results.append(False)

        console.print("\n[bold cyan]═══ Final Results ═══[/bold cyan]")
        console.print(
            f"Training: [green]{sum(training_results)}/{len(training_results)}[/green] tasks succeeded"
        )
        console.print(
            f"Evaluation: [green]{sum(eval_results)}/{len(eval_results)}[/green] tasks succeeded"
        )

        console.print("\n[bold]Stored Trajectories:[/bold]")
        for traj in agent.database.get_all():
            status = "[green]✓[/green]" if traj.success else "[red]✗[/red]"
            console.print(f"  {status} {traj.goal[:60]}...")
            console.print(f"     [dim]Plan: {traj.plan[:80]}...[/dim]")


def main() -> None:
    """Entry point."""
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()

