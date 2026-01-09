#!/usr/bin/env python3
"""Harbor 3-Way SGICL Comparison Script.

This script runs a 3-way comparison on real Harbor/SWE-bench tasks:
1. Zero-shot: No retrieval (k=0)
2. SGICL Online: Examples accumulated on-the-fly
3. SGICL Full DB: All examples pre-loaded

Unlike the simulated experiment, this uses actual Harbor environments
and SWE-bench tasks.

Usage:
    # Run on Django tasks from SWE-bench
    python examples/harbor_comparison.py --filter "*django*"

    # Run on specific tasks
    python examples/harbor_comparison.py --tasks django__django-11885 django__django-13590

    # Resume from checkpoint
    python examples/harbor_comparison.py --checkpoint harbor_experiment.json --resume

Requirements:
    - Harbor CLI installed and configured
    - Docker running (for SWE-bench environments)
    - OPENAI_API_KEY or ANTHROPIC_API_KEY set

Environment variables:
    MODEL: LLM model to use (default: gpt-4o-mini)
    ICICL_MAX_STEPS: Max steps per task (default: 50)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import shutil

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()

# Default paths
DEFAULT_CHECKPOINT = Path("harbor_comparison_checkpoint.json")
DEFAULT_DB_DIR = Path.home() / ".icicl" / "harbor_comparison"


def load_checkpoint(path: Path) -> dict | None:
    """Load checkpoint if it exists."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def save_checkpoint(results: dict, path: Path) -> None:
    """Save results to checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)


def run_harbor_command(
    agent_import_path: str,
    dataset: str,
    task_filter: str | None = None,
    task_names: list[str] | None = None,
    job_name: str = "sgicl-run",
    db_path: str | None = None,
    extra_env: dict | None = None,
    n_parallel: int = 1,
) -> dict:
    """Run Harbor CLI and return results.
    
    Args:
        agent_import_path: Import path for the agent class
        dataset: Dataset name (e.g., swebench-verified@1.0)
        task_filter: Optional glob filter for tasks (e.g., "*django*")
        task_names: Optional specific task names to run
        job_name: Name for the Harbor job
        db_path: Path to ICICL database
        extra_env: Additional environment variables
    
    Returns:
        Dictionary with results from the Harbor run
    """
    cmd = [
        "uv", "run", "harbor", "run",
        "-d", dataset,
        "--agent-import-path", agent_import_path,
        "--job-name", job_name,
        "--jobs-dir", "harbor_jobs",
        "-n", str(n_parallel),
    ]
    
    if task_filter:
        cmd.extend(["-t", task_filter])
    
    if task_names:
        for name in task_names:
            cmd.extend(["-t", name])
    
    # Set up environment
    env = os.environ.copy()
    if db_path:
        env["ICICL_DB_PATH"] = db_path
    if extra_env:
        env.update(extra_env)
    
    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    
    try:
        # Run without capturing to see live output
        result = subprocess.run(
            cmd,
            env=env,
            timeout=3600 * 6,  # 6 hour timeout
        )
        
        console.print(f"[dim]Harbor exit code: {result.returncode}[/dim]")
        
        # Parse results from job directory
        job_dir = Path("harbor_jobs") / job_name
        result_file = job_dir / "result.json"
        
        if result_file.exists():
            with open(result_file) as f:
                return json.load(f)
        else:
            console.print(f"[red]No result file found at {result_file}[/red]")
            # List what's in the job directory
            if job_dir.exists():
                console.print(f"[dim]Contents of {job_dir}: {list(job_dir.iterdir())}[/dim]")
            return {"error": "No result file", "returncode": result.returncode}
            
    except subprocess.TimeoutExpired:
        console.print("[red]Harbor run timed out[/red]")
        return {"error": "timeout"}
    except Exception as e:
        console.print(f"[red]Error running Harbor: {e}[/red]")
        return {"error": str(e)}


def extract_success_rate(harbor_result: dict) -> tuple[int, int]:
    """Extract success count and total from Harbor result."""
    stats = harbor_result.get("stats", {})
    evals = stats.get("evals", {})
    
    total_success = 0
    total_tasks = 0
    
    for eval_name, eval_stats in evals.items():
        reward_stats = eval_stats.get("reward_stats", {}).get("reward", {})
        for reward_val, task_list in reward_stats.items():
            if float(reward_val) == 1.0:
                total_success += len(task_list)
            total_tasks += len(task_list)
    
    # Also count from n_trials if reward_stats is empty
    if total_tasks == 0:
        for eval_name, eval_stats in evals.items():
            total_tasks += eval_stats.get("n_trials", 0) - eval_stats.get("n_errors", 0)
    
    return total_success, total_tasks


async def run_comparison(
    dataset: str,
    task_filter: str | None = None,
    task_names: list[str] | None = None,
    checkpoint_path: Path | None = None,
    model: str = "gpt-4o-mini",
    max_steps: int = 50,
    n_parallel: int = 1,
) -> dict:
    """Run the 3-way Harbor comparison.
    
    Args:
        dataset: Harbor dataset (e.g., swebench-verified@1.0)
        task_filter: Glob filter for tasks
        task_names: Specific task names
        checkpoint_path: Path for saving progress
        model: LLM model to use
        max_steps: Max steps per task
    
    Returns:
        Results dictionary
    """
    # Load existing checkpoint
    results = None
    if checkpoint_path:
        results = load_checkpoint(checkpoint_path)
        if results:
            console.print(f"[yellow]Loaded checkpoint from {checkpoint_path}[/yellow]")
    
    if not results:
        results = {
            "dataset": dataset,
            "task_filter": task_filter,
            "task_names": task_names,
            "model": model,
            "max_steps": max_steps,
            "timestamp": datetime.now().isoformat(),
            "zero_shot": None,
            "sgicl_online": None,
        }
    
    # Common environment
    common_env = {
        "MODEL": model,
        "ICICL_MAX_STEPS": str(max_steps),
    }
    
    # Setup database directories
    db_base = DEFAULT_DB_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    zs_db = db_base / "zeroshot"
    online_db = db_base / "online"
    
    # =========================================================================
    # Condition 1: Zero-shot
    # =========================================================================
    if results["zero_shot"] is None:
        console.print("\n[bold cyan]═══ Condition 1: Zero-Shot (k=0) ═══[/bold cyan]")
        console.print("[dim]No retrieval, each task solved independently[/dim]\n")
        
        zs_result = run_harbor_command(
            agent_import_path="icicl.harbor.agents:ICICLZeroShotAgent",
            dataset=dataset,
            task_filter=task_filter,
            task_names=task_names,
            job_name="sgicl-zeroshot",
            db_path=str(zs_db),
            extra_env={**common_env, "ICICL_K": "0"},
            n_parallel=n_parallel,  # Zero-shot can run in parallel
        )
        
        results["zero_shot"] = zs_result
        if checkpoint_path:
            save_checkpoint(results, checkpoint_path)
    else:
        console.print("[dim]Zero-shot already complete, skipping...[/dim]")
    
    # =========================================================================
    # Condition 2: SGICL Online
    # =========================================================================
    if results["sgicl_online"] is None:
        console.print("\n[bold cyan]═══ Condition 2: SGICL Online (k=3) ═══[/bold cyan]")
        console.print("[dim]Examples accumulated on-the-fly[/dim]\n")
        
        online_result = run_harbor_command(
            agent_import_path="icicl.harbor.agents:ICICLTrainAgent",
            dataset=dataset,
            task_filter=task_filter,
            task_names=task_names,
            job_name="sgicl-online",
            db_path=str(online_db),
            extra_env={**common_env, "ICICL_K": "3"},
            n_parallel=min(n_parallel, 8),  # Cap at 8 for online learning
        )
        
        results["sgicl_online"] = online_result
        if checkpoint_path:
            save_checkpoint(results, checkpoint_path)
    else:
        console.print("[dim]SGICL Online already complete, skipping...[/dim]")
    
    return results


def print_results(results: dict):
    """Print comparison results."""
    console.print("\n")
    console.print(Panel.fit("[bold]Harbor SGICL Comparison Results[/bold]", border_style="cyan"))
    
    # Extract success rates
    zs_success, zs_total = extract_success_rate(results.get("zero_shot", {}))
    online_success, online_total = extract_success_rate(results.get("sgicl_online", {}))
    
    table = Table(title=f"Results on {results.get('dataset', 'unknown')}")
    table.add_column("Condition", style="cyan")
    table.add_column("Success Rate", justify="center")
    table.add_column("Δ vs Zero-Shot", justify="center")
    
    zs_pct = 100 * zs_success / max(zs_total, 1)
    online_pct = 100 * online_success / max(online_total, 1)
    
    table.add_row(
        "Zero-Shot (k=0)",
        f"{zs_success}/{zs_total} ({zs_pct:.0f}%)",
        "baseline",
    )
    
    online_delta = online_success - zs_success
    table.add_row(
        "SGICL Online (k=3)",
        f"{online_success}/{online_total} ({online_pct:.0f}%)",
        f"[green]+{online_delta}[/green]" if online_delta > 0 else str(online_delta),
    )
    
    console.print(table)
    
    # Summary
    console.print("\n[bold]Summary:[/bold]")
    if online_success > zs_success:
        console.print(f"[green]✓ SGICL Online improved by {online_delta} tasks[/green]")
    else:
        console.print("[yellow]No improvement observed[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="Harbor 3-Way SGICL Comparison")
    parser.add_argument(
        "--dataset", type=str, default="swebench-verified@1.0",
        help="Harbor dataset (default: swebench-verified@1.0)"
    )
    parser.add_argument(
        "--filter", type=str, default=None,
        help="Task filter glob (e.g., '*django*')"
    )
    parser.add_argument(
        "--tasks", nargs="+", type=str, default=None,
        help="Specific task names to run"
    )
    parser.add_argument(
        "--n-tasks", type=int, default=None,
        help="Limit number of tasks (uses --limit in Harbor)"
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="LLM model to use"
    )
    parser.add_argument(
        "--max-steps", type=int, default=50,
        help="Max steps per task"
    )
    parser.add_argument(
        "--parallel", "-p", type=int, default=1,
        help="Number of parallel trials (default: 1)"
    )
    parser.add_argument(
        "--checkpoint", type=str, default=None,
        help="Checkpoint file for resume support"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from default checkpoint"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output file for final results"
    )
    args = parser.parse_args()
    
    model = args.model or os.environ.get("MODEL", "gpt-4o-mini")
    
    # Setup checkpoint
    checkpoint_path = None
    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint)
    elif args.resume:
        checkpoint_path = DEFAULT_CHECKPOINT
    
    console.print(
        Panel.fit(
            "[bold magenta]Harbor 3-Way SGICL Comparison[/bold magenta]\n"
            f"Dataset: {args.dataset}\n"
            f"Model: {model} | Max Steps: {args.max_steps} | Parallel: {args.parallel}\n"
            f"Filter: {args.filter or 'none'} | Tasks: {len(args.tasks) if args.tasks else 'all'}",
            border_style="magenta",
        )
    )
    
    if checkpoint_path:
        console.print(f"[dim]Checkpoint: {checkpoint_path}[/dim]")
    
    # Check uv and harbor are available
    if shutil.which("uv") is None:
        console.print("[red]Error: uv not found[/red]")
        sys.exit(1)
    
    # Run comparison
    results = asyncio.run(run_comparison(
        dataset=args.dataset,
        task_filter=args.filter,
        task_names=args.tasks,
        checkpoint_path=checkpoint_path,
        model=model,
        max_steps=args.max_steps,
        n_parallel=args.parallel,
    ))
    
    # Print results
    print_results(results)
    
    # Save final output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, indent=2, default=str))
        console.print(f"\n[dim]Results saved to {output_path}[/dim]")


if __name__ == "__main__":
    main()

