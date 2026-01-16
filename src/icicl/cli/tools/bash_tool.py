"""Bash command execution tool for ICICL CLI."""

import asyncio
from typing import Any

from icicl.cli.tools.base import Tool, ToolParameter, ToolResult


class BashTool(Tool):
    """Execute shell commands."""

    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        "> /dev/sda",
        "mkfs.",
        ":(){:|:&};:",
        "dd if=/dev/zero",
        "chmod -R 777 /",
    ]

    @property
    def name(self) -> str:
        return "Bash"

    @property
    def description(self) -> str:
        return (
            "Execute a shell command in the working directory. "
            "Use for running scripts, git operations, tests, etc."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                type="string",
                description="The shell command to execute",
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="Timeout in seconds (default: 120)",
                required=False,
            ),
        ]

    async def execute(
        self, command: str, timeout: int = 120, **kwargs: Any
    ) -> ToolResult:
        # Safety check
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command:
                msg = f"Blocked potentially dangerous command: {pattern}"
                return ToolResult(output=msg, success=False)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._working_dir,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            output_parts = []
            if stdout:
                stdout_text = stdout.decode("utf-8", errors="replace")
                if len(stdout_text) > 10000:
                    stdout_text = (
                        stdout_text[:5000]
                        + "\n...(truncated)...\n"
                        + stdout_text[-5000:]
                    )
                output_parts.append(stdout_text)

            if stderr:
                stderr_text = stderr.decode("utf-8", errors="replace")
                if len(stderr_text) > 2000:
                    stderr_text = stderr_text[:2000] + "\n...(truncated)..."
                output_parts.append(f"[stderr]: {stderr_text}")

            if proc.returncode != 0:
                output_parts.append(f"[exit code: {proc.returncode}]")

            output = "\n".join(output_parts) if output_parts else "(no output)"
            return ToolResult(output=output, success=proc.returncode == 0)

        except TimeoutError:
            return ToolResult(
                output=f"Command timed out after {timeout} seconds", success=False
            )
        except Exception as e:
            return ToolResult(output=f"Error executing command: {e}", success=False)
