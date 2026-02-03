"""Harbor environment adapter for ICRL.

This module bridges Harbor's BaseEnvironment to ICRL's Environment protocol,
enabling ICRL agents to work with Harbor's sandboxed execution environment.
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from icrl._debug import log as _debug_log

if TYPE_CHECKING:
    from harbor.environments.base import BaseEnvironment


class HarborEnvironmentAdapter:
    """Adapts Harbor's BaseEnvironment to ICRL's Environment protocol.

    This adapter wraps Harbor's exec() method to provide the reset/step
    interface expected by ICRL agents.

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

        # Harness behavior flags (env-configurable)
        self._trace_steps = os.environ.get("ICRL_TRACE_STEPS", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        self._enforce_single_command = os.environ.get(
            "ICRL_ENFORCE_SINGLE_COMMAND", "1"
        ).lower() in {"1", "true", "yes"}
        self._verify_on_submit = os.environ.get(
            "ICRL_HARBOR_VERIFY_ON_SUBMIT", "1"
        ).lower() in {"1", "true", "yes"}
        try:
            self._verify_timeout_sec = int(
                os.environ.get("ICRL_HARBOR_VERIFY_TIMEOUT_SEC", "900")
            )
        except ValueError:
            self._verify_timeout_sec = 900
        try:
            self._verifier_tail_chars = int(
                os.environ.get("ICRL_HARBOR_VERIFIER_TAIL_CHARS", "4000")
            )
        except ValueError:
            self._verifier_tail_chars = 4000

        # Used to avoid log spam and to correlate verification output.
        self._last_verify_started_at: float | None = None

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
- submit - Run this to verify and finish (submit may fail; keep fixing and re-submit)

Start by exploring the codebase to find the relevant code."""

    async def step(self, action: str) -> tuple[str, bool, bool]:
        """Execute an action in the environment.

        Like the original Terminus harness, this executes each command in the
        response individually with its own timeout, then returns the combined output.

        Args:
            action: The raw LLM response containing commands.

        Returns:
            Tuple of (observation, done, success) where:
            - observation: The command output (stdout/stderr)
            - done: Whether the episode has ended
            - success: Whether the goal was achieved
        """
        self._action_count += 1

        if self._action_count >= self._max_actions:
            return (
                "Maximum actions reached. Episode ended.",
                True,
                False,
            )

        try:
            # Parse the response to extract commands with their timeouts
            commands, is_task_complete = self._parse_xml_response(action)

            # If task is marked complete, run submit
            if is_task_complete:
                observation, done, success = await self._handle_submit()
                self._last_output = observation
                return observation, done, success

            # Execute each command individually (like original harness)
            all_outputs: list[str] = []
            last_return_code = 0

            for cmd, timeout in commands:
                if not cmd:
                    continue

                # Check if this command is a submit
                if self._is_completion_signal(cmd):
                    observation, done, success = await self._handle_submit()
                    self._last_output = observation
                    return observation, done, success

                # Execute with command-specific timeout
                output, return_code = await self._execute_command_async(
                    cmd, timeout_override=timeout
                )
                last_return_code = return_code

                self._maybe_trace_step(cmd, output)
                self._maybe_write_agent_log(cmd, output, return_code)

                all_outputs.append(output)

            # Combine all outputs
            combined_output = "\n".join(all_outputs) if all_outputs else "(no output)"
            self._last_output = combined_output

            return combined_output, False, False

        except Exception as e:
            error_msg = f"Error executing command: {e}"
            self._last_output = error_msg
            return error_msg, False, False

    def _parse_xml_response(self, action: str) -> tuple[list[tuple[str, float]], bool]:
        """Parse XML response to extract commands with their timeouts.

        Like the original Terminus harness, extracts individual commands
        with their timeout_sec (duration) values.

        Args:
            action: Raw LLM response string.

        Returns:
            Tuple of (list of (command, timeout) tuples, is_task_complete)
        """
        import re

        action = action.strip()
        commands: list[tuple[str, float]] = []
        is_task_complete = False

        # Check for task completion signal
        if "<task_complete>true</task_complete>" in action.lower():
            is_task_complete = True

        # Strip outer <response> tags if present
        response_match = re.search(
            r"<response>(.*)</response>", action, re.DOTALL | re.IGNORECASE
        )
        if response_match:
            action = response_match.group(1).strip()

        # Extract keystrokes with their duration attributes
        # Pattern: <keystrokes duration="X">command</keystrokes>
        keystrokes_pattern = r'<keystrokes(?:\s+duration=["\']?(\d*\.?\d+)["\']?)?[^>]*>([\s\S]*?)</keystrokes>'
        matches = re.findall(keystrokes_pattern, action, re.IGNORECASE)

        for duration_str, keystroke in matches:
            cmd = keystroke.strip()
            if not cmd:
                continue

            # Parse duration (default to 1.0 if not specified)
            try:
                timeout = float(duration_str) if duration_str else 1.0
            except ValueError:
                timeout = 1.0

            # Map duration to actual timeout (duration is wait time, add buffer)
            # Minimum 5 seconds, scale up for longer durations
            actual_timeout = max(5.0, timeout * 2 + 3)

            # Handle control sequences
            if cmd in ("C-c", "C-d"):
                # For control sequences, we'd need tmux integration
                # For now, skip them as we can't send raw keystrokes via exec
                continue

            commands.append((cmd, actual_timeout))

        # If no XML keystrokes found, fall back to legacy parsing
        if not commands and not is_task_complete:
            legacy_cmd = self._clean_command_legacy(action)
            if legacy_cmd:
                commands.append((legacy_cmd, self._timeout_sec))

        return commands, is_task_complete

    async def _handle_submit(self) -> tuple[str, bool, bool]:
        """Handle the `submit` meta-action.

        In Harbor, official verification normally runs AFTER the agent exits, so the
        agent would never see failing test output. To make the harness interactive,
        we optionally run the official Harbor verifier here and only finish when
        it passes.
        """
        if not self._verify_on_submit:
            return "submit", True, True

        started_at = time.time()
        self._last_verify_started_at = started_at
        if self._trace_steps:
            print("[icrl.verify] Running official Harbor verifier...")

        try:
            passed, summary = await asyncio.wait_for(
                self._run_official_verifier(),
                timeout=max(1, self._verify_timeout_sec),
            )
        except TimeoutError:
            return (
                "submit: verifier timed out. Try running a smaller, targeted test "
                "subset, then submit again.",
                False,
                False,
            )
        except Exception as e:
            return (
                f"submit: verifier failed to run ({e}). "
                "Keep working, then submit again.",
                False,
                False,
            )
        finally:
            if self._trace_steps:
                elapsed = time.time() - started_at
                print(f"[icrl.verify] Done in {elapsed:.1f}s")

        if passed:
            self._maybe_trace_step("submit", summary)
            self._maybe_write_agent_log("submit", summary, 0)
            return summary, True, True
        self._maybe_trace_step("submit", summary)
        self._maybe_write_agent_log("submit", summary, 1)
        return summary, False, False

    async def _run_official_verifier(self) -> tuple[bool, str]:
        """Run Harbor's official verifier against the current environment state."""
        # Lazy imports: keep non-Harbor usage light.
        from harbor.models.task.task import Task
        from harbor.verifier.verifier import Verifier

        task_dir = Path(self._environment.environment_dir).parent
        task = Task(task_dir)

        verifier = Verifier(
            task=task,
            trial_paths=self._environment.trial_paths,
            environment=self._environment,
        )
        verifier_result = await verifier.verify()

        rewards = verifier_result.rewards or {}
        reward_val = None
        if "reward" in rewards:
            reward_val = rewards["reward"]
        elif rewards:
            reward_val = next(iter(rewards.values()))
        else:
            reward_val = 0.0

        passed = float(reward_val) > 0.0

        stdout_tail = self._read_file_tail(
            self._environment.trial_paths.test_stdout_path,
            max_chars=self._verifier_tail_chars,
        )
        stderr_tail = self._read_file_tail(
            self._environment.trial_paths.test_stderr_path,
            max_chars=min(self._verifier_tail_chars, 2000),
        )

        status = "PASSED" if passed else "FAILED"
        test_rel = task.paths.test_path.relative_to(task.paths.tests_dir)
        lines: list[str] = [
            f"submit: VERIFIER {status} (reward={reward_val})",
            "",
            "To reproduce / run tests in this environment:",
            "- submit   (recommended; runs the official verifier)",
            f"- bash /tests/{test_rel}   (only if /tests is available)",
        ]
        if stdout_tail:
            lines.extend(["", "[verifier stdout tail]", stdout_tail])
        if stderr_tail:
            lines.extend(["", "[verifier stderr tail]", stderr_tail])

        if not passed:
            lines.extend(
                [
                    "",
                    "Fix the failures above, then run: submit",
                ]
            )
        return passed, "\n".join(lines)

    def _read_file_tail(self, path: Path, *, max_chars: int) -> str | None:
        """Read the tail of a text file (best-effort)."""
        if max_chars <= 0:
            return None
        try:
            if not path.exists():
                return None
            max_bytes = max_chars * 4
            with path.open("rb") as f:
                f.seek(0, os.SEEK_END)
                size = f.tell()
                start = max(0, size - max_bytes)
                f.seek(start)
                data = f.read()
            text = data.decode("utf-8", errors="replace")
            text = text[-max_chars:] if len(text) > max_chars else text
            if start > 0:
                return "...\n" + text
            return text
        except Exception:
            return None

    def _maybe_trace_step(self, command: str, output: str) -> None:
        if not self._trace_steps:
            return
        out = output.replace("\n", "\\n")
        if len(out) > 400:
            out = out[:400] + "...[truncated]"
        print(f"[icrl.step] cmd={command!r} out={out}")

    def _maybe_write_agent_log(
        self, command: str, output: str, return_code: int
    ) -> None:
        """Write step logs to the trial's mounted agent dir (best-effort)."""
        try:
            agent_dir = self._environment.trial_paths.agent_dir
            agent_dir.mkdir(parents=True, exist_ok=True)
            log_path = agent_dir / "icrl_steps.log"
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"\n[{ts}]$ {command}\n")
                if output:
                    f.write(output)
                    if not output.endswith("\n"):
                        f.write("\n")
                f.write(f"[exit code: {return_code}]\n")
        except Exception:
            return

    async def _execute_command_async(
        self, command: str, timeout_override: float | None = None
    ) -> tuple[str, int]:
        """Execute a command via Harbor's environment asynchronously.

        Args:
            command: The shell command to execute.
            timeout_override: Optional timeout to use instead of default.

        Returns:
            Tuple of (formatted output, return_code). Output combines stdout/stderr
            and is truncated if too long.
        """
        timeout = (
            timeout_override if timeout_override is not None else self._timeout_sec
        )
        try:
            result = await self._environment.exec(
                command,
                timeout_sec=int(timeout),
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
            # region agent log (debug-mode)
            _debug_log(
                hypothesis_id="H4",
                location="src/icrl/harbor/adapter.py:HarborEnvironmentAdapter._execute_command_async",
                message="harbor_exec_exception",
                data={
                    "pid": os.getpid(),
                    "timeout_sec": self._timeout_sec,
                    "command_prefix": command[:120],
                    "exc_type": type(e).__name__,
                    "exc": str(e)[:800],
                },
            )
            # endregion agent log (debug-mode)
            return f"Execution error: {e}", 1

    def _clean_command_legacy(self, action: str) -> str:
        """Legacy command extraction for non-XML responses.

        Handles cases where the agent wraps commands in markdown code blocks
        or other formats (fallback when XML parsing fails).

        Args:
            action: Raw action string from the agent.

        Returns:
            Cleaned command string.
        """
        import re

        action = action.strip()

        # Check for task completion signal
        if "submit" in action.lower() and len(action) < 50:
            return "submit"

        # If action still looks like XML with no extractable commands, return echo error
        if action.startswith("<") and ("analysis>" in action or "plan>" in action):
            return "echo 'Error: Could not parse XML response'"

        # Handle XML-style tags that Claude sometimes uses: <bash>command</bash>
        xml_match = re.search(
            r"<(?:bash|shell|command|cmd)>(.*?)</(?:bash|shell|command|cmd)>",
            action,
            re.DOTALL,
        )
        if xml_match:
            action = xml_match.group(1).strip()

        # Also handle unclosed XML tags: <bash>command
        if (
            action.startswith("<bash>")
            or action.startswith("<shell>")
            or action.startswith("<command>")
        ):
            action = re.sub(r"^<(?:bash|shell|command|cmd)>", "", action).strip()
        if (
            action.endswith("</bash>")
            or action.endswith("</shell>")
            or action.endswith("</command>")
        ):
            action = re.sub(r"</(?:bash|shell|command|cmd)>$", "", action).strip()

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

        # Strip common tool/trace artifacts that sometimes leak into model output.
        # These are not valid shell syntax and can cause confusing failures.
        action = action.replace("<meta_sep>", " ").strip()
        for marker in ("commentary to=submit", "analysis to=submit", "to=submit"):
            if marker in action:
                action = action.replace(marker, " ").strip()

        # Some models try to keep commands "single-line" by emitting literal "\n"
        # sequences inside shell strings (e.g., a heredoc inside `bash -lc "..."`).
        # That breaks heredocs because bash treats "\n" as characters, not a newline.
        # When we detect a heredoc, normalize these sequences back to real newlines.
        if "\\n" in action and "<<" in action:
            action = action.replace("\\n", "\n")

        if not self._enforce_single_command:
            return action

        # Enforce "one command per step", but allow common multi-line *single-command*
        # blocks (heredocs, python -c blocks). If extra commands are present after
        # a block, they are dropped.
        raw_lines = action.splitlines()
        while raw_lines and not raw_lines[0].strip():
            raw_lines.pop(0)
        while raw_lines and not raw_lines[-1].strip():
            raw_lines.pop()

        if not raw_lines:
            return ""
        if len(raw_lines) == 1:
            return raw_lines[0].strip()

        first = raw_lines[0].strip()

        if first.startswith(("python ", "python3 ")) and " -c" in first:
            return self._extract_python_c_block(raw_lines)

        if first.startswith(("bash ", "sh ")) and (" -c" in first or " -lc" in first):
            return self._extract_quoted_block(raw_lines)

        # IMPORTANT: check quoted bash/sh blocks *before* generic heredocs.
        #
        # Many SWE-bench fixes use a nested heredoc inside a quoted `bash -lc "..."`,
        # e.g.:
        #   bash -lc "python3 - <<'PY'\n...\nPY"
        #   submit
        #
        # If we treat that as an outer heredoc, we fail to find the delimiter (it is
        # typically `PY"` with the closing quote) and we end up executing the entire
        # multi-line action including a trailing `submit` as a shell command.
        if "<<" in first:
            return self._extract_heredoc_block(raw_lines)

        # Fallback: the model sometimes emits a brief sentence before the command.
        # Prefer the first line that *looks like* a shell command.
        def _strip_bullets(s: str) -> str:
            s = s.strip()
            if s.startswith(("- ", "* ")):
                return s[2:].lstrip()
            # Strip simple enumerations like "1. cmd" or "2) cmd".
            i = 0
            while i < len(s) and s[i].isdigit():
                i += 1
            if i and i < len(s) and s[i] in {".", ")"}:
                rest = s[i + 1 :].lstrip()
                if rest:
                    return rest
            return s

        allowed_prefixes = (
            "submit",
            "ls",
            "cd",
            "pwd",
            "cat",
            "grep",
            "find",
            "sed",
            "python",
            "python3",
            "bash",
            "sh",
            "git",
            "./",
            "/",
            "echo",
            "export",
            "mkdir",
            "cp",
            "mv",
            "rm",
            "touch",
            "chmod",
        )

        for raw in raw_lines:
            cand = _strip_bullets(raw)
            if not cand or cand.startswith("#"):
                continue
            for prefix in allowed_prefixes:
                # Path-like prefixes should match literally (/, ./)
                if prefix in {"/", "./"}:
                    if cand.startswith(prefix):
                        return cand
                    continue

                # Word-like commands: require a token boundary to avoid matching
                # accidental prose like "bash:" or "submit:".
                if cand == prefix or cand.startswith(prefix + " "):
                    return cand

        # If nothing matches, fall back to executing only the first non-empty line.
        # The agent can chain with `&&` or use a heredoc for multi-line scripts.
        return first

    def _extract_heredoc_block(self, lines: list[str]) -> str:
        """Extract a heredoc command block from multi-line output."""
        first = lines[0]
        idx = first.find("<<")
        if idx == -1:
            return first.strip()

        after = first[idx + 2 :].strip()
        if not after:
            return "\n".join(lines).strip()

        token = after.split()[0]
        delim = token.strip("'\"")
        if not delim:
            return "\n".join(lines).strip()

        for i in range(1, len(lines)):
            if lines[i].strip() == delim:
                return "\n".join(lines[: i + 1]).strip()

        return "\n".join(lines).strip()

    def _extract_python_c_block(self, lines: list[str]) -> str:
        """Extract a `python -c "<multi-line>"` block, dropping trailing commands."""
        first = lines[0]
        parts = first.split("-c", 1)
        if len(parts) != 2:
            return first.strip()

        rest = parts[1].lstrip()
        if not rest:
            return first.strip()

        quote = rest[0]
        if quote not in ("'", '"'):
            return first.strip()

        # Common pattern: python3 -c " ... \n ... \n"
        for i in range(1, len(lines)):
            if lines[i].strip() == quote:
                return "\n".join(lines[: i + 1]).strip()

        # Fallback: keep full block (best-effort).
        return "\n".join(lines).strip()

    def _extract_quoted_block(self, lines: list[str]) -> str:
        """Extract a `bash -c "<...>"` block, dropping trailing commands.

        The model sometimes emits multi-line actions like:
            bash -lc "<script...>"
            submit

        We must only execute the *first* shell command, not the trailing lines.
        This implementation finds the closing quote of the -c/-lc argument and
        truncates everything after it.
        """
        full = "\n".join(lines)

        # Find the -c/-lc argument start (near the beginning).
        idx_lc = full.find(" -lc")
        idx_c = full.find(" -c")
        idxs = [i for i in (idx_lc, idx_c) if i != -1]
        if not idxs:
            return lines[0].strip()

        start = min(idxs)
        token = " -lc" if start == idx_lc else " -c"

        i = start + len(token)
        while i < len(full) and full[i].isspace():
            i += 1
        if i >= len(full):
            return lines[0].strip()

        quote = full[i]
        if quote not in ("'", '"'):
            # Unquoted -c argument; fall back to first line only.
            return lines[0].strip()

        # Scan for the matching closing quote (best-effort, handles backslash escapes).
        i += 1
        escaped = False
        while i < len(full):
            ch = full[i]
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                end = i + 1
                return full[:end].strip()
            i += 1

        # If we can't find a closing quote, keep the whole block.
        return full.strip()

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
