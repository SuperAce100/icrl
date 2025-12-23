"""Mock LLM provider for testing icicl without API calls."""

from __future__ import annotations

import re

from icicl.models import Message


class MockLLMProvider:
    """A deterministic mock LLM that generates sensible responses for file system tasks.

    This mock uses pattern matching on the prompt to generate appropriate plans,
    reasoning, and actions without requiring actual LLM API calls.
    """

    def __init__(self, success_rate: float = 1.0) -> None:
        """Initialize the mock LLM.

        Args:
            success_rate: Probability of generating a correct action (1.0 = always correct).
        """
        self._success_rate = success_rate
        self._step_count = 0

    async def complete(self, messages: list[Message]) -> str:
        """Generate a completion based on the prompt content.

        Args:
            messages: List of messages (we look at the last user message).

        Returns:
            Generated response based on pattern matching.
        """
        if not messages:
            return "I need more context to help."

        prompt = messages[-1].content.lower()

        if "create a plan" in prompt and "action:" not in prompt:
            return self._generate_plan(prompt)
        elif "action:" in prompt and "command" in prompt:
            self._step_count += 1
            return self._generate_action(prompt)
        elif "think:" in prompt:
            return self._generate_reasoning(prompt)
        else:
            self._step_count += 1
            return self._generate_action(prompt)

    def _generate_plan(self, prompt: str) -> str:
        """Generate a plan based on the goal."""
        if "navigate" in prompt and "list" in prompt:
            return "1. Use cd to navigate to the target directory\n2. Use ls to list the files"
        elif "copy" in prompt:
            if "find" in prompt:
                return "1. Use find to locate the file\n2. Use cp to copy it to the destination"
            return "1. Use cp to copy the file directly with full paths"
        elif "find" in prompt and "password" in prompt:
            return "1. Navigate to /etc/app\n2. Use cat to read config.json"
        elif "find" in prompt and ("python" in prompt or ".py" in prompt):
            return "1. Use find command with .py pattern"
        elif "find" in prompt and "port" in prompt:
            return "1. Use cat to read /etc/app/config.json"
        elif "read" in prompt or "display" in prompt or "contents" in prompt:
            return "1. Navigate to the file location\n2. Use cat to display contents"
        elif "create" in prompt and "directory" in prompt:
            return "1. Use mkdir to create new directory\n2. Copy required files"
        elif "list" in prompt:
            return "1. Use ls with the target directory path"
        else:
            return "1. Explore the file system\n2. Complete the task"

    def _generate_reasoning(self, prompt: str) -> str:
        """Generate reasoning based on the current observation."""
        if "error:" in prompt:
            return "The last command failed. I need to try a different approach or check the path."
        elif "changed directory" in prompt:
            return "Successfully changed directory. I should now use the appropriate command."
        elif "copied" in prompt:
            return "File copied successfully. The task should be complete."
        elif "task completed" in prompt:
            return "The task is done."
        else:
            return "I should continue with the next step of the plan."

    def _generate_action(self, prompt: str) -> str:
        """Generate an action based on the goal and current state."""
        if "task completed successfully" in prompt:
            return "done"

        goal = self._extract_goal(prompt)
        history = self._extract_history(prompt)

        if "navigate to /home/user/projects and list" in goal:
            if "cd /home/user/projects" in history:
                return "ls"
            return "cd /home/user/projects"

        elif "navigate to /home/user/docs" in goal and "notes.txt" in goal:
            if "cd /home/user/docs" in history:
                return "cat notes.txt"
            return "cd /home/user/docs"

        elif "database password" in goal or ("password" in goal and "config" in goal):
            if "cd /etc/app" in history:
                return "cat config.json"
            return "cd /etc/app"

        elif "port number" in goal or ("port" in goal and "config" in goal):
            if "cd /etc/app" in history:
                return "cat config.json"
            return "cd /etc/app"

        elif "python files" in goal or ("python" in goal and "list" in goal):
            return "find .py"

        elif "copy" in goal and "notes.txt" in goal:
            return "cp /home/user/docs/notes.txt /backup"

        elif "find" in goal and "main.py" in goal and "copy" in goal:
            if "find main.py" in history:
                return "cp /home/user/projects/src/main.py /backup"
            return "find main.py"

        elif "list" in goal and "/etc/app" in goal:
            return "ls /etc/app"

        elif "read" in goal and "main.py" in goal:
            if "cd /home/user/projects/src" in history:
                return "cat main.py"
            return "cd /home/user/projects/src"

        elif "debug" in goal and "config" in goal:
            if "find config.py" in history:
                return "cat /home/user/projects/src/config.py"
            return "find config.py"

        elif "create" in goal and "archive" in goal:
            if "mkdir /tmp/archive" in history:
                return "cp /home/user/projects/README.md /tmp/archive"
            return "mkdir /tmp/archive"

        elif "what directory" in goal or ("current" in goal and "directory" in goal):
            return "pwd"

        else:
            if self._step_count == 1:
                return "ls"
            elif self._step_count == 2:
                return "find ."
            else:
                return "pwd"

    def _extract_goal(self, prompt: str) -> str:
        """Extract the goal from the prompt."""
        goal_match = re.search(r"goal:\s*(.+?)(?:\n|plan:|$)", prompt, re.IGNORECASE)
        if goal_match:
            return goal_match.group(1).strip().lower()
        return prompt.lower()

    def _extract_history(self, prompt: str) -> str:
        """Extract action history from the prompt."""
        history_match = re.search(
            r"(?:previous steps|steps so far|history).*?:\s*(.+?)(?:\ncurrent|\nobservation|\nreasoning|\nexamples|\n\n|$)",
            prompt,
            re.IGNORECASE | re.DOTALL,
        )
        if history_match:
            return history_match.group(1).strip().lower()
        return ""
