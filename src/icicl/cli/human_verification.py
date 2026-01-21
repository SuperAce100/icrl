"""Human verification utilities for file operations."""

from __future__ import annotations

import difflib

from rich.console import Console
from rich.syntax import Syntax


def build_write_prompt(path: str, content: str) -> str:
    """Build a prompt asking the user to verify a write operation."""
    preview = content[:500] + "..." if len(content) > 500 else content
    return f"Allow writing to '{path}'?\n\nContent preview:\n{preview}"


def build_edit_prompt(path: str, old_text: str, new_text: str) -> str:
    """Build a prompt asking the user to verify an edit operation.

    Returns a single string containing a Rich-rendered, colorized unified diff.
    This is designed to be displayed by an outer UI (e.g. Typer/Rich).
    """

    # Build a unified diff (closest to what developers expect).
    old_lines = (old_text or "").splitlines(keepends=True)
    new_lines = (new_text or "").splitlines(keepends=True)

    # difflib expects file names; we keep them informative.
    diff_iter = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
        n=3,
    )
    diff_text = "\n".join(diff_iter)
    if not diff_text.strip():
        diff_text = "(no textual changes detected)"

    # Render diff with Rich's syntax highlighter.
    # `diff` lexer colors +/-, headers, and hunk markers nicely.
    console = Console(width=100)
    syntax = Syntax(diff_text, "diff", theme="ansi_dark", word_wrap=True)

    with console.capture() as capture:
        console.print(syntax)
    return capture.get()
