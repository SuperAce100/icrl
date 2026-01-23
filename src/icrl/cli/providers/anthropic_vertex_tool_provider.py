"""Anthropic Vertex AI provider with native tool calling support."""

import json
import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import litellm

# Disable LiteLLM's async logging worker to avoid event loop issues
litellm.disable_logging_worker = True

# Suppress the async client cleanup warning
warnings.filterwarnings("ignore", message="coroutine 'close_litellm_async_clients'")

from icrl.cli.tools.base import ToolRegistry  # noqa: E402
from icrl.models import Message  # noqa: E402
from icrl.providers.anthropic_vertex import AnthropicVertexProvider  # noqa: E402


@dataclass
class ToolCall:
    """A tool call from the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResponse:
    """Response from tool calling completion."""

    content: str | None  # Text content if any
    tool_calls: list[ToolCall]  # Tool calls to execute
    finish_reason: str  # "tool_calls", "stop", etc.


class AnthropicVertexToolProvider:
    """Anthropic Vertex AI provider with native tool calling support.

    This provider uses Anthropic Claude models on Google Cloud Vertex AI
    with native tool calling capabilities.
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        registry: ToolRegistry | None = None,
        credentials_path: str | Path | None = None,
        project_id: str | None = None,
        location: str | None = None,
    ):
        """Initialize the Anthropic Vertex AI tool provider.

        Args:
            model: Model name (shorthand or full vertex_ai/ path).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            registry: Tool registry for available tools.
            credentials_path: Path to GCP service account JSON file.
            project_id: GCP project ID.
            location: GCP region (e.g., "us-east5").
        """
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._registry = registry

        # Create base provider to handle credentials setup
        self._base_provider = AnthropicVertexProvider(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            credentials_path=credentials_path,
            project_id=project_id,
            location=location,
        )

        self._model = self._base_provider.model
        self._project_id = self._base_provider.project_id
        self._location = self._base_provider.location

    @property
    def model(self) -> str:
        """Return the resolved model name."""
        return self._model

    def set_registry(self, registry: ToolRegistry) -> None:
        """Set the tool registry."""
        self._registry = registry

    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
    ) -> ToolResponse:
        """Generate completion with potential tool calls.

        Args:
            messages: Conversation messages in LiteLLM format

        Returns:
            ToolResponse with content and/or tool calls
        """
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "vertex_ai_project": self._project_id,
            "vertex_ai_location": self._location,
        }

        # Add tools if registry is set
        if self._registry:
            tools = self._registry.to_openai_tools()
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

        response = await litellm.acompletion(**kwargs)

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # Parse tool calls if present
        tool_calls: list[ToolCall] = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        return ToolResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )

    async def complete(self, messages: list[Message]) -> str:
        """Simple completion without tools (for compatibility)."""
        litellm_messages = [{"role": m.role, "content": m.content} for m in messages]
        response = await litellm.acompletion(
            model=self._model,
            messages=litellm_messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            vertex_ai_project=self._project_id,
            vertex_ai_location=self._location,
        )
        return response.choices[0].message.content or ""


def is_vertex_model(model: str) -> bool:
    """Check if a model string indicates Vertex AI usage.

    Args:
        model: Model name to check.

    Returns:
        True if the model should use Vertex AI.
    """
    # Explicit vertex_ai/ prefix
    if model.startswith("vertex_ai/"):
        return True

    # Check for Anthropic model aliases that should use Vertex
    vertex_aliases = set(AnthropicVertexProvider.MODEL_ALIASES.keys())
    if model in vertex_aliases:
        return True

    # Check for environment variable indicating Vertex preference
    if os.environ.get("ICRL_USE_VERTEX_AI", "").lower() in {"1", "true", "yes"}:
        # Claude models should use Vertex if env var is set
        if "claude" in model.lower():
            return True

    return False
