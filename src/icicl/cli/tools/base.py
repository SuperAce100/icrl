"""Base tool infrastructure with JSON Schema support."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass
class ToolParameter:
    """A single tool parameter definition."""

    name: str
    type: Literal["string", "integer", "number", "boolean", "array", "object"]
    description: str
    required: bool = True
    enum: list[str] | None = None
    items: dict[str, Any] | None = None  # For array types
    default: Any = None


@dataclass
class ToolResult:
    """Result from a tool execution."""

    output: str
    success: bool = True
    error: str | None = None


class Tool(ABC):
    """Base class for all tools."""

    def __init__(self, working_dir: Path | None = None):
        """Initialize the tool.

        Args:
            working_dir: Working directory for file operations.
        """
        self._working_dir = working_dir or Path.cwd()

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name (used in function calling)."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for the LLM."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters."""
        ...

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling schema."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.items:
                prop["items"] = param.items
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def all_tools(self) -> list[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Get all tools in OpenAI schema format."""
        return [tool.to_openai_schema() for tool in self._tools.values()]


def create_default_registry(
    working_dir: Path | None = None,
    ask_user_callback: Callable[[str, list[str] | None], str] | None = None,
) -> ToolRegistry:
    """Create registry with all default tools.

    Args:
        working_dir: Working directory for file operations.
        ask_user_callback: Callback for asking user questions.

    Returns:
        ToolRegistry with all default tools registered.
    """
    from icicl.cli.tools.bash_tool import BashTool
    from icicl.cli.tools.file_tools import (
        EditTool,
        GlobTool,
        GrepTool,
        ReadTool,
        WriteTool,
    )
    from icicl.cli.tools.user_tool import AskUserQuestionTool
    from icicl.cli.tools.web_tools import WebFetchTool, WebSearchTool

    registry = ToolRegistry()

    # File tools
    registry.register(ReadTool(working_dir))
    registry.register(WriteTool(working_dir))
    registry.register(EditTool(working_dir))
    registry.register(GlobTool(working_dir))
    registry.register(GrepTool(working_dir))

    # Bash
    registry.register(BashTool(working_dir))

    # Web tools
    registry.register(WebSearchTool(working_dir))
    registry.register(WebFetchTool(working_dir))

    # User interaction
    if ask_user_callback:
        registry.register(AskUserQuestionTool(working_dir, ask_user_callback))

    return registry
