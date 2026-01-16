"""User interaction tool for ICICL CLI."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from icicl.cli.tools.base import Tool, ToolParameter, ToolResult


class AskUserQuestionTool(Tool):
    """Ask the user a clarifying question."""

    def __init__(
        self,
        working_dir: Path | None,
        callback: Callable[[str, list[str] | None], str],
    ):
        super().__init__(working_dir)
        self._callback = callback

    @property
    def name(self) -> str:
        return "AskUserQuestion"

    @property
    def description(self) -> str:
        return (
            "Ask the user a clarifying question. Use when you need more "
            "information or want to confirm before making significant changes."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="question",
                type="string",
                description="The question to ask the user",
            ),
            ToolParameter(
                name="options",
                type="array",
                description="Optional list of choices for multiple choice questions",
                required=False,
                items={"type": "string"},
            ),
        ]

    async def execute(
        self, question: str, options: list[str] | None = None, **kwargs: Any
    ) -> ToolResult:
        try:
            response = self._callback(question, options)
            return ToolResult(output=f"User response: {response}")
        except Exception as e:
            return ToolResult(output=f"Error getting user input: {e}", success=False)
