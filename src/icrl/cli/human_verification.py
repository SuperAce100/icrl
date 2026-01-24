"""Diff display utilities for file operations."""

from __future__ import annotations

import difflib
import os

from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text


def _get_lexer_for_file(path: str) -> str:
    """Determine the Pygments lexer name based on file extension."""
    ext_to_lexer = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".jsx": "jsx",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".mdx": "markdown",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sql": "sql",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".R": "r",
        ".lua": "lua",
        ".vim": "vim",
        ".dockerfile": "dockerfile",
        ".xml": "xml",
        ".graphql": "graphql",
        ".tf": "terraform",
        ".hcl": "hcl",
    }
    _, ext = os.path.splitext(path)
    return ext_to_lexer.get(ext.lower(), "text")


def _render_diff(
    path: str,
    old_lines: list[str],
    new_lines: list[str],
    console: Console,
    is_new_file: bool = False,
) -> None:
    """Render a unified diff with a clean header showing file and line counts.

    Args:
        path: File path being modified
        old_lines: Original content lines
        new_lines: New content lines
        console: Rich console for output
        is_new_file: Whether this is a new file creation
    """
    lexer = _get_lexer_for_file(path)

    diff_iter = difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm="",
        n=3,
    )
    diff_lines = list(diff_iter)

    if not diff_lines:
        console.print("[dim](no changes)[/dim]")
        return

    # Count additions and deletions (skip header lines)
    additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

    # Build clean header: path with +/- counts
    header = Text()
    header.append(path, style="bold")
    header.append("  ")
    if additions > 0:
        header.append(f"+{additions}", style="bold green")
    if additions > 0 and deletions > 0:
        header.append(" ")
    if deletions > 0:
        header.append(f"-{deletions}", style="bold red")
    if is_new_file:
        header.append(" ", style="dim")
        header.append("(new file)", style="dim")

    # Print separator line above
    console.print("[dim]" + "─" * 50 + "[/dim]")

    console.print(header)

    # Render diff content (skip the --- and +++ header lines from unified diff)
    for line in diff_lines:
        # Skip unified diff file headers
        if line.startswith("---") or line.startswith("+++"):
            continue
        elif line.startswith("@@"):
            # Hunk header - show in dim
            console.print(Text(line, style="dim"))
        elif line.startswith("-"):
            code_content = line[1:]
            console.print(Text("- " + code_content, style="bold red"))
        elif line.startswith("+"):
            code_content = line[1:]
            console.print(Text("+ " + code_content, style="bold green"))
        else:
            # Context line
            code_content = line[1:] if line.startswith(" ") else line
            console.print(
                Syntax("  " + code_content, lexer, theme="ansi_dark", word_wrap=False)
            )

    # Print separator line below
    console.print("[dim]" + "─" * 50 + "[/dim]")


def build_write_prompt(path: str, content: str) -> str:
    """Build a prompt asking the user to verify a write operation."""
    preview = content[:500] + "..." if len(content) > 500 else content
    return f"Allow writing to '{path}'?\n\nContent preview:\n{preview}"


def build_write_diff(
    path: str, old_content: str | None, new_content: str, console: Console
) -> None:
    """Display a diff for a write operation."""
    old_lines = (old_content or "").splitlines() if old_content else []
    new_lines = (new_content or "").splitlines()
    is_new_file = old_content is None

    _render_diff(path, old_lines, new_lines, console, is_new_file=is_new_file)


def build_edit_prompt(
    path: str, old_text: str, new_text: str, console: Console
) -> None:
    """Display a diff for an edit operation."""
    old_lines = (old_text or "").splitlines()
    new_lines = (new_text or "").splitlines()

    _render_diff(path, old_lines, new_lines, console)
