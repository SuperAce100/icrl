"""File system tools for ICICL CLI."""

import re
from typing import Any

from icicl.cli.tools.base import Tool, ToolParameter, ToolResult


class ReadTool(Tool):
    """Read file contents."""

    @property
    def name(self) -> str:
        return "Read"

    @property
    def description(self) -> str:
        return "Read the contents of a file. Returns content with line numbers."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="Path to the file to read (relative to working directory)",
            ),
            ToolParameter(
                name="start_line",
                type="integer",
                description="Starting line number (1-indexed, optional)",
                required=False,
            ),
            ToolParameter(
                name="end_line",
                type="integer",
                description="Ending line number (inclusive, optional)",
                required=False,
            ),
        ]

    async def execute(
        self,
        path: str,
        start_line: int | None = None,
        end_line: int | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        try:
            full_path = self._working_dir / path
            if not full_path.exists():
                return ToolResult(
                    output=f"Error: File not found: {path}", success=False
                )

            if not full_path.is_file():
                return ToolResult(output=f"Error: Not a file: {path}", success=False)

            # Security: ensure path is within working directory
            try:
                full_path.resolve().relative_to(self._working_dir.resolve())
            except ValueError:
                return ToolResult(
                    output="Error: Access denied - path outside working directory",
                    success=False,
                )

            content = full_path.read_text()
            lines = content.splitlines()

            # Apply line range if specified
            if start_line is not None or end_line is not None:
                start = (start_line or 1) - 1
                end = end_line or len(lines)
                lines = lines[start:end]
                line_offset = start
            else:
                line_offset = 0

            # Format with line numbers
            numbered = [
                f"{i + line_offset + 1:4d} | {line}" for i, line in enumerate(lines)
            ]

            # Truncate if too long
            if len(numbered) > 500:
                numbered = numbered[:250] + ["... (truncated) ..."] + numbered[-250:]

            return ToolResult(output="\n".join(numbered))
        except Exception as e:
            return ToolResult(output=f"Error reading file: {e}", success=False)


class WriteTool(Tool):
    """Create or overwrite a file."""

    @property
    def name(self) -> str:
        return "Write"

    @property
    def description(self) -> str:
        return "Create a new file or overwrite an existing file with content."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="Path to the file to write",
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write to the file",
            ),
        ]

    async def execute(self, path: str, content: str, **kwargs: Any) -> ToolResult:
        try:
            full_path = self._working_dir / path

            # Security check
            try:
                full_path.resolve().relative_to(self._working_dir.resolve())
            except ValueError:
                return ToolResult(output="Error: Access denied", success=False)

            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

            return ToolResult(
                output=f"Successfully wrote {len(content)} bytes to {path}"
            )
        except Exception as e:
            return ToolResult(output=f"Error writing file: {e}", success=False)


class EditTool(Tool):
    """Make precise edits to a file."""

    @property
    def name(self) -> str:
        return "Edit"

    @property
    def description(self) -> str:
        return (
            "Make a precise edit to a file by replacing exact text. "
            "Use for small, targeted changes."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="Path to the file to edit",
            ),
            ToolParameter(
                name="old_text",
                type="string",
                description="The exact text to find and replace (must match exactly)",
            ),
            ToolParameter(
                name="new_text",
                type="string",
                description="The new text to replace it with",
            ),
        ]

    async def execute(
        self, path: str, old_text: str, new_text: str, **kwargs: Any
    ) -> ToolResult:
        try:
            full_path = self._working_dir / path

            if not full_path.exists():
                return ToolResult(
                    output=f"Error: File not found: {path}", success=False
                )

            # Security check
            try:
                full_path.resolve().relative_to(self._working_dir.resolve())
            except ValueError:
                return ToolResult(output="Error: Access denied", success=False)

            content = full_path.read_text()

            if old_text not in content:
                # Show nearby content to help debug
                msg = (
                    "Error: Could not find exact text to replace. "
                    "Make sure the text matches exactly including whitespace."
                )
                return ToolResult(output=msg, success=False)

            # Count occurrences
            count = content.count(old_text)
            if count > 1:
                msg = (
                    f"Warning: Found {count} occurrences. Replacing all. "
                    "Use more specific text for single replacement."
                )
                return ToolResult(output=msg, success=True)

            new_content = content.replace(old_text, new_text)
            full_path.write_text(new_content)

            return ToolResult(
                output=f"Successfully edited {path} ({count} replacement(s))"
            )
        except Exception as e:
            return ToolResult(output=f"Error editing file: {e}", success=False)


class GlobTool(Tool):
    """Find files by pattern."""

    @property
    def name(self) -> str:
        return "Glob"

    @property
    def description(self) -> str:
        return "Find files matching a glob pattern (e.g., '**/*.py', 'src/**/*.ts')"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                type="string",
                description="Glob pattern to match files (e.g., '**/*.py', 'src/*.ts')",
            ),
            ToolParameter(
                name="path",
                type="string",
                description="Directory to search in (default: current directory)",
                required=False,
            ),
        ]

    async def execute(self, pattern: str, path: str = ".", **kwargs: Any) -> ToolResult:
        try:
            search_path = self._working_dir / path
            matches = list(search_path.glob(pattern))

            # Make paths relative and sort
            relative = sorted(
                str(m.relative_to(self._working_dir)) for m in matches if m.is_file()
            )

            if not relative:
                return ToolResult(output=f"No files found matching pattern: {pattern}")

            # Truncate if too many
            if len(relative) > 100:
                return ToolResult(
                    output="\n".join(relative[:100])
                    + f"\n... and {len(relative) - 100} more files"
                )

            return ToolResult(output="\n".join(relative))
        except Exception as e:
            return ToolResult(output=f"Error searching files: {e}", success=False)


class GrepTool(Tool):
    """Search file contents with regex."""

    @property
    def name(self) -> str:
        return "Grep"

    @property
    def description(self) -> str:
        return (
            "Search file contents using regex pattern. "
            "Returns matching lines with file paths and line numbers."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="pattern",
                type="string",
                description="Regex pattern to search for",
            ),
            ToolParameter(
                name="path",
                type="string",
                description="File or directory to search in (default: cwd)",
                required=False,
            ),
            ToolParameter(
                name="include",
                type="string",
                description="Glob pattern for files to include (e.g., '*.py')",
                required=False,
            ),
        ]

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        include: str | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return ToolResult(output=f"Invalid regex pattern: {e}", success=False)

        search_path = self._working_dir / path
        results: list[str] = []

        # Determine files to search
        if search_path.is_file():
            files = [search_path]
        else:
            glob_pattern = include or "**/*"
            files = [f for f in search_path.glob(glob_pattern) if f.is_file()]

        for file_path in files[:100]:  # Limit files
            try:
                content = file_path.read_text()
                for i, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        rel_path = file_path.relative_to(self._working_dir)
                        results.append(f"{rel_path}:{i}: {line.strip()}")
                        if len(results) >= 50:
                            break
            except Exception:
                continue  # Skip binary/unreadable files

            if len(results) >= 50:
                break

        if not results:
            return ToolResult(output=f"No matches found for pattern: {pattern}")

        return ToolResult(output="\n".join(results))
