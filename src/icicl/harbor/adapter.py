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

        return f"""You are in a sandboxed Linux environment to fix a bug.

Goal: {goal}

Commands:
- Standard bash: ls, cat, grep, find, sed, python3, etc.
- submit - Run this when you have completed the fix

Start by exploring the codebase to find the relevant code."""

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
            output, return_code = await self._execute_command_async(action)
            self._last_output = output

            # Handle submit command - signals task completion.
            # IMPORTANT: We still execute it in the Harbor environment so the harness
            # can record the final state / patch and run verification.
            if self._is_completion_signal(action):
                return output, True, return_code == 0

            return output, False, False

        except Exception as e:
            error_msg = f"Error executing command: {e}"
            self._last_output = error_msg
            return error_msg, False, False

    async def _execute_command_async(self, command: str) -> tuple[str, int]:
        """Execute a command via Harbor's environment asynchronously.

        Args:
            command: The shell command to execute.

        Returns:
            Tuple of (formatted output, return_code). Output combines stdout/stderr
            and is truncated if too long.
        """
        try:
            result = await self._environment.exec(
                command,
                timeout_sec=self._timeout_sec,
            )

            output_parts = []
            if result.stdout:
                stdout = result.stdout
                # Truncate very long outputs to keep context manageable
                if len(stdout) > 3000:
                    stdout = (
                        stdout[:1500]
                        + (
                            "\n\n... [output truncated; showing first 1500"
                            " and last 1500 chars] ...\n\n"
                        )
                        + stdout[-1500:]
                    )
                output_parts.append(stdout)
            if result.stderr:
                stderr = result.stderr
                if len(stderr) > 2000:
                    stderr = stderr[:2000] + "\n... [stderr truncated] ..."
                output_parts.append(f"[stderr]: {stderr}")
            if result.return_code != 0:
                output_parts.append(f"[exit code: {result.return_code}]")

            output = "\n".join(output_parts) if output_parts else "(no output)"
            return output, result.return_code

        except TimeoutError:
            return f"Command timed out after {self._timeout_sec} seconds", 124
        except Exception as e:
            return f"Execution error: {e}", 1

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
        action_lower = action.strip().lower()
        return action_lower == "submit" or action_lower.startswith("submit ")

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
