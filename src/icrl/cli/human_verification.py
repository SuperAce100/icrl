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


def build_write_prompt(path: str, content: str) -> str:
    """Build a prompt asking the user to verify a write operation."""
    preview = content[:500] + "..." if len(content) > 500 else content
    return f"Allow writing to '{path}'?\n\nContent preview:\n{preview}"


def build_edit_prompt(path: str, old_text: str, new_text: str) -> str:
    """Build a Rich-rendered diff for an edit operation.

    Returns a single string containing a Rich-rendered diff with both:
    - Diff coloring (red for deletions, green for additions)
    - Syntax highlighting for the code content

    This is designed to be displayed by an outer UI (e.g. Typer/Rich).
    """
    console = Console(width=100, force_terminal=True)
    lexer = _get_lexer_for_file(path)

    # Build a unified diff
    old_lines = (old_text or "").splitlines()
    new_lines = (new_text or "").splitlines()

    diff_iter = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
        n=3,
    )
    diff_lines = list(diff_iter)

    if not diff_lines:
        return "(no textual changes detected)"

    # Build a combined output with both diff colors and syntax highlighting
    output_parts: list[Text | str] = []

    for line in diff_lines:
        if line.startswith("---") or line.startswith("+++"):
            # File headers - style as bold
            output_parts.append(Text(line, style="bold cyan"))
        elif line.startswith("@@"):
            # Hunk headers - style as magenta
            output_parts.append(Text(line, style="magenta"))
        elif line.startswith("-"):
            # Deletion - bold red text, no background
            code_content = line[1:]  # Remove the leading -
            deletion_line = Text("- " + code_content, style="bold red")
            output_parts.append(deletion_line)
        elif line.startswith("+"):
            # Addition - bold green text, no background
            code_content = line[1:]  # Remove the leading +
            addition_line = Text("+ " + code_content, style="bold green")
            output_parts.append(addition_line)
        else:
            # Context line - just syntax highlight
            code_content = line[1:] if line.startswith(" ") else line
            highlighted = _highlight_code_line(code_content, lexer, console)
            context_line = Text("  ")
            context_line.append_text(highlighted)
            output_parts.append(context_line)

    # Render all parts
    with console.capture() as capture:
        for part in output_parts:
            console.print(part)

    return capture.get()


def _highlight_code_line(code: str, lexer: str, console: Console) -> Text:
    """Apply syntax highlighting to a single line of code and return as Text."""
    if not code.strip():
        return Text(code)

    try:
        # Use Syntax to highlight, then extract the Text
        syntax = Syntax(code, lexer, theme="monokai", word_wrap=False)
        with console.capture() as capture:
            console.print(syntax, end="")
        # Parse the captured output back to Text
        highlighted_str = capture.get().rstrip("\n")
        return Text.from_ansi(highlighted_str)
    except Exception:
        # Fallback to plain text if highlighting fails
        return Text(code)
