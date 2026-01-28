"""Anthropic Vertex AI provider with native tool calling support."""

import json
import os
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import litellm

# Disable LiteLLM's async logging worker to avoid event loop issues
litellm.disable_logging_worker = True

# Suppress the "Provider List" debug message
litellm.suppress_debug_info = True

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
class LLMStats:
    """Statistics from an LLM call."""

    latency_ms: float = 0.0  # Time to first response / total time in milliseconds
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0  # Tokens served from cache (prompt caching)
    cache_creation_tokens: int = 0  # Tokens written to cache (Anthropic-specific)

    @property
    def tokens_per_second(self) -> float:
        """Calculate throughput in tokens per second."""
        if self.latency_ms <= 0:
            return 0.0
        return (self.completion_tokens / self.latency_ms) * 1000

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage of prompt tokens."""
        if self.prompt_tokens <= 0:
            return 0.0
        return (self.cached_tokens / self.prompt_tokens) * 100


@dataclass
class ToolResponse:
    """Response from tool calling completion."""

    content: str | None  # Text content if any
    tool_calls: list[ToolCall]  # Tool calls to execute
    finish_reason: str  # "tool_calls", "stop", etc.
    stats: LLMStats = field(default_factory=LLMStats)  # Latency and token stats


class AnthropicVertexToolProvider:
    """Anthropic Vertex AI provider with native tool calling support.

    This provider uses Anthropic Claude models on Google Cloud Vertex AI
    with native tool calling capabilities.
    """

    def __init__(
        self,
        model: str = "claude-opus-4-5",
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
            location: GCP region (e.g., "global", "us-east5").
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

        start_time = time.perf_counter()
        response = await litellm.acompletion(**kwargs)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # Extract token usage from response
        usage = getattr(response, "usage", None)
        stats = LLMStats(latency_ms=elapsed_ms)
        if usage:
            stats.prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            stats.completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            stats.total_tokens = getattr(usage, "total_tokens", 0) or 0

            # Extract prompt caching info
            # LiteLLM returns cache info in multiple places:
            # 1. prompt_tokens_details.cached_tokens (cache reads)
            # 2. prompt_tokens_details.cache_creation_tokens (cache writes)
            # 3. model_extra: cache_read_input_tokens, cache_creation_input_tokens
            prompt_details = getattr(usage, "prompt_tokens_details", None)
            if prompt_details:
                stats.cached_tokens = getattr(prompt_details, "cached_tokens", 0) or 0
                # Also check cache_creation_tokens in prompt_details
                stats.cache_creation_tokens = (
                    getattr(prompt_details, "cache_creation_tokens", 0) or 0
                )

            # Fallback to model_extra for Anthropic-specific fields
            model_extra = getattr(usage, "model_extra", {}) or {}
            if not stats.cached_tokens:
                stats.cached_tokens = model_extra.get("cache_read_input_tokens", 0) or 0
            if not stats.cache_creation_tokens:
                stats.cache_creation_tokens = (
                    model_extra.get("cache_creation_input_tokens", 0) or 0
                )

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
            stats=stats,
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

    async def complete_text(self, messages: list[dict[str, Any]]) -> str:
        """Completion that returns text only and never uses tools."""
        response = await litellm.acompletion(
            model=self._model,
            messages=messages,
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
