"""Simulated file system environment for icicl examples."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import PurePosixPath


@dataclass
class FileSystemState:
    """Tracks the current state of the virtual file system."""

    cwd: str = "/"
    last_output: str = ""
    files: dict[str, str] = field(default_factory=dict)
    directories: set[str] = field(default_factory=set)

    def file_exists(self, path: str) -> bool:
        """Check if a file exists at the given path."""
        normalized = self._normalize_path(path)
        return normalized in self.files

    def dir_exists(self, path: str) -> bool:
        """Check if a directory exists at the given path."""
        normalized = self._normalize_path(path)
        return normalized in self.directories

    def _normalize_path(self, path: str) -> str:
        """Normalize a path, handling relative and absolute paths."""
        if path.startswith("/"):
            parts = PurePosixPath(path).parts
        else:
            parts = (PurePosixPath(self.cwd) / path).parts

        normalized_parts: list[str] = []
        for part in parts:
            if part == "..":
                if normalized_parts and normalized_parts[-1] != "/":
                    normalized_parts.pop()
            elif part != ".":
                normalized_parts.append(part)

        if not normalized_parts:
            return "/"
        return str(PurePosixPath(*normalized_parts))

    def get_file_content(self, path: str) -> str | None:
        """Get the content of a file."""
        normalized = self._normalize_path(path)
        return self.files.get(normalized)

    def list_dir(self, path: str) -> list[str]:
        """List contents of a directory."""
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
class Task:
    """A verifiable task for the file system environment."""

    goal: str
    verify: Callable[[FileSystemState], bool]
    setup: Callable[[FileSystemState], None] | None = None


def create_default_file_tree() -> tuple[dict[str, str], set[str]]:
    """Create the default virtual file tree.

    Returns:
        Tuple of (files dict, directories set)
    """
    files = {
        "/home/user/projects/README.md": "# My Projects\n\nThis is the projects directory.",
        "/home/user/projects/src/main.py": 'def main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()',
        "/home/user/projects/src/utils.py": "def helper():\n    return 42\n\ndef format_output(data):\n    return str(data)",
        "/home/user/projects/src/config.py": 'DATABASE_URL = "postgres://localhost/db"\nDEBUG = True',
        "/home/user/docs/notes.txt": "Meeting notes:\n- Discuss project timeline\n- Review code changes\n- Plan next sprint",
        "/etc/app/config.json": json.dumps(
            {"port": 8080, "db_password": "secret123", "debug": False}, indent=2
        ),
    }

    directories = {
        "/",
        "/home",
        "/home/user",
        "/home/user/projects",
        "/home/user/projects/src",
        "/home/user/docs",
        "/etc",
        "/etc/app",
        "/backup",
        "/tmp",
    }

    return files, directories


class FileSystemEnvironment:
    """Simulated file system environment implementing the Environment protocol."""

    def __init__(self, task: Task) -> None:
        """Initialize the environment with a task.

        Args:
            task: The task to complete in this environment.
        """
        self._task = task
        self._state = FileSystemState()
        self._done = False
        self._max_actions = 20
        self._action_count = 0

    def reset(self, goal: str) -> str:
        """Reset the environment for a new episode.

        Args:
            goal: The goal description (used for context, task defines actual goal).

        Returns:
            The initial observation.
        """
        files, directories = create_default_file_tree()
        self._state = FileSystemState(
            cwd="/",
            last_output="",
            files=files,
            directories=directories,
        )
        self._done = False
        self._action_count = 0

        if self._task.setup:
            self._task.setup(self._state)

        return f"You are in a file system. Current directory: /\nGoal: {self._task.goal}\nAvailable commands: ls, cd <dir>, cat <file>, find <pattern>, pwd, mkdir <name>, cp <src> <dst>"

    def step(self, action: str) -> tuple[str, bool]:
        """Execute an action in the environment.

        Args:
            action: The action to execute.

        Returns:
            Tuple of (observation, done).
        """
        self._action_count += 1
        action = action.strip()

        if self._action_count >= self._max_actions:
            self._done = True
            return "Maximum actions reached. Episode ended.", True

        observation = self._execute_action(action)
        self._state.last_output = observation

        if self._task.verify(self._state):
            self._done = True
            return observation + "\n[Task completed successfully!]", True

        return observation, False

    def is_success(self) -> bool:
        """Check if the task was completed successfully."""
        return self._task.verify(self._state)

    def _execute_action(self, action: str) -> str:
        """Execute a single action and return the observation."""
        parts = action.split(maxsplit=1)
        if not parts:
            return "Error: Empty command"

        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        handlers = {
            "ls": self._cmd_ls,
            "cd": self._cmd_cd,
            "cat": self._cmd_cat,
            "find": self._cmd_find,
            "pwd": self._cmd_pwd,
            "mkdir": self._cmd_mkdir,
            "cp": self._cmd_cp,
        }

        if cmd in handlers:
            return handlers[cmd](args)
        return f"Error: Unknown command '{cmd}'. Available: ls, cd, cat, find, pwd, mkdir, cp"

    def _cmd_ls(self, args: str) -> str:
        """List directory contents."""
        path = args.strip() if args.strip() else self._state.cwd
        normalized = self._state._normalize_path(path)

        if not self._state.dir_exists(normalized):
            return f"Error: Directory '{path}' not found"

        entries = self._state.list_dir(normalized)
        if not entries:
            return "(empty directory)"
        return "\n".join(entries)

    def _cmd_cd(self, args: str) -> str:
        """Change directory."""
        if not args.strip():
            return "Error: cd requires a directory argument"

        path = args.strip()
        if path == "..":
            parent = str(PurePosixPath(self._state.cwd).parent)
            self._state.cwd = parent
            return f"Changed directory to {parent}"

        normalized = self._state._normalize_path(path)
        if not self._state.dir_exists(normalized):
            return f"Error: Directory '{path}' not found"

        self._state.cwd = normalized
        return f"Changed directory to {normalized}"

    def _cmd_cat(self, args: str) -> str:
        """Display file contents."""
        if not args.strip():
            return "Error: cat requires a file argument"

        path = args.strip()
        content = self._state.get_file_content(path)
        if content is None:
            return f"Error: File '{path}' not found"
        return content

    def _cmd_find(self, args: str) -> str:
        """Find files matching a pattern."""
        if not args.strip():
            return "Error: find requires a pattern argument"

        pattern = args.strip().lower()
        matches = []

        for file_path in self._state.files:
            if pattern in file_path.lower():
                matches.append(file_path)

        if not matches:
            return f"No files found matching '{pattern}'"
        return "\n".join(sorted(matches))

    def _cmd_pwd(self, args: str) -> str:
        """Print working directory."""
        return self._state.cwd

    def _cmd_mkdir(self, args: str) -> str:
        """Create a directory."""
        if not args.strip():
            return "Error: mkdir requires a directory name"

        path = args.strip()
        normalized = self._state._normalize_path(path)

        if self._state.dir_exists(normalized):
            return f"Error: Directory '{path}' already exists"

        parent = str(PurePosixPath(normalized).parent)
        if not self._state.dir_exists(parent):
            return "Error: Parent directory does not exist"

        self._state.directories.add(normalized)
        return f"Created directory {normalized}"

    def _cmd_cp(self, args: str) -> str:
        """Copy a file."""
        parts = args.strip().split()
        if len(parts) != 2:
            return "Error: cp requires exactly two arguments: cp <source> <destination>"

        src, dst = parts
        src_normalized = self._state._normalize_path(src)
        dst_normalized = self._state._normalize_path(dst)

        if src_normalized not in self._state.files:
            return f"Error: Source file '{src}' not found"

        if dst_normalized in self._state.directories:
            filename = PurePosixPath(src_normalized).name
            dst_normalized = str(PurePosixPath(dst_normalized) / filename)

        dst_parent = str(PurePosixPath(dst_normalized).parent)
        if not self._state.dir_exists(dst_parent):
            return "Error: Destination directory does not exist"

        self._state.files[dst_normalized] = self._state.files[src_normalized]
        return f"Copied {src_normalized} to {dst_normalized}"

