"""Harbor environment adapter for ICICL.

This module bridges Harbor's BaseEnvironment to ICICL's Environment protocol,
enabling ICICL agents to work with Harbor's sandboxed execution environment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from harbor.environments.base import BaseEnvironment


class HarborEnvironmentAdapter:
    """Adapts Harbor's BaseEnvironment to ICICL's Environment protocol.

    This adapter wraps Harbor's exec() method to provide the reset/step
    interface expected by ICICL agents.

    Attributes:
        environment: The Harbor BaseEnvironment instance.
        goal: The current task goal/instruction.
        max_actions: Maximum number of actions before episode ends.
    """

    def __init__(
        self,
        environment: BaseEnvironment,
        max_actions: int = 50,
        timeout_sec: int = 120,
    ) -> None:
        """Initialize the adapter.

        Args:
            environment: The Harbor BaseEnvironment to wrap.
            max_actions: Maximum actions before forcing episode end.
            timeout_sec: Timeout in seconds for each command execution.
        """
        self._environment = environment
        self._max_actions = max_actions
        self._timeout_sec = timeout_sec
        self._action_count = 0
        self._goal = ""
        self._last_output = ""

    def reset(self, goal: str) -> str:
        """Reset the environment for a new episode.

        Args:
            goal: The goal/instruction for this episode.

        Returns:
            Initial observation describing the environment.
        """
        self._goal = goal
        self._action_count = 0
        self._last_output = ""

        return f"""You are a software engineer working in a sandboxed Linux environment.
You have access to standard shell commands to complete coding tasks.

Current directory: /workspace (the repository root)

Goal: {goal}

Available commands include:
- ls, cd, pwd - navigate the filesystem
- cat, head, tail, less - view file contents
- grep, find, ag, rg - search for patterns and files
- sed, awk - text processing and editing
- echo "content" > file - write to files
- git diff, git log, git status - version control
- python, pytest - run Python code and tests
- Any other standard Linux commands

You can chain commands with && and use standard shell syntax.
Start by exploring the codebase to understand its structure."""

    async def step(self, action: str) -> tuple[str, bool, bool]:
        """Execute an action in the environment.

        Args:
            action: The shell command to execute.

        Returns:
            Tuple of (observation, done, success) where:
            - observation: The command output (stdout/stderr)
            - done: Whether the episode has ended
            - success: Whether the goal was achieved
        """
        self._action_count += 1
        action = self._clean_command(action)

        if self._action_count >= self._max_actions:
            return (
                "Maximum actions reached. Episode ended.",
                True,
                False,
            )

        try:
            result = await self._execute_command_async(action)
            self._last_output = result

            # Check for common success indicators
            # Note: Harbor's task verification handles actual success determination
            # We return done=False to let the agent continue until it decides to stop
            # or hits max_actions. The actual success is determined by Harbor's
            # task verification after the run completes.

            # Check if agent explicitly signals completion
            if self._is_completion_signal(action):
                return result, True, True

            return result, False, False

        except Exception as e:
            error_msg = f"Error executing command: {e}"
            self._last_output = error_msg
            return error_msg, False, False

    async def _execute_command_async(self, command: str) -> str:
        """Execute a command via Harbor's environment asynchronously.

        Args:
            command: The shell command to execute.

        Returns:
            The command output (combined stdout and stderr).
        """
        try:
            result = await self._environment.exec(
                command,
                timeout_sec=self._timeout_sec,
            )

            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(f"[stderr]: {result.stderr}")
            if result.return_code != 0:
                output_parts.append(f"[exit code: {result.return_code}]")

            return "\n".join(output_parts) if output_parts else "(no output)"

        except TimeoutError:
            return f"Command timed out after {self._timeout_sec} seconds"
        except Exception as e:
            return f"Execution error: {e}"

    def _clean_command(self, action: str) -> str:
        """Clean and extract the actual command from agent output.

        Handles cases where the agent wraps commands in markdown code blocks.

        Args:
            action: Raw action string from the agent.

        Returns:
            Cleaned command string.
        """
        action = action.strip()

        # Handle markdown code blocks: ```bash\ncommand\n``` or ```\ncommand\n```
        if action.startswith("```"):
            lines = action.split("\n")
            # Remove first line (```bash or ```)
            if len(lines) > 1:
                lines = lines[1:]
            # Remove last line if it's just ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            action = "\n".join(lines).strip()

        # Handle inline backticks: `command`
        if action.startswith("`") and action.endswith("`"):
            action = action[1:-1].strip()

        return action

    def _is_completion_signal(self, action: str) -> bool:
        """Check if the action signals task completion.

        Args:
            action: The executed action.

        Returns:
            True if the action indicates the agent believes it's done.
        """
        completion_signals = [
            "echo 'TASK_COMPLETE'",
            'echo "TASK_COMPLETE"',
            "echo TASK_COMPLETE",
            "# DONE",
            "# COMPLETE",
        ]
        return any(signal in action for signal in completion_signals)

    @property
    def goal(self) -> str:
        """Get the current goal."""
        return self._goal

    @property
    def action_count(self) -> int:
        """Get the current action count."""
        return self._action_count

    @property
    def last_output(self) -> str:
        """Get the last command output."""
        return self._last_output

