"""LLM provider with native tool calling support."""

import json
import time
import warnings
from dataclasses import dataclass, field
from typing import Any

import litellm

# Disable LiteLLM's async logging worker to avoid event loop issues
# when asyncio.run() is called multiple times (e.g., in chat mode)
litellm.disable_logging_worker = True

# Suppress the "Provider List" debug message
litellm.suppress_debug_info = True

# Suppress the async client cleanup warning
warnings.filterwarnings("ignore", message="coroutine 'close_litellm_async_clients'")

from icrl.cli.tools.base import ToolRegistry  # noqa: E402
from icrl.models import Message  # noqa: E402


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


class ToolLLMProvider:
    """LLM provider with native tool calling support."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        registry: ToolRegistry | None = None,
    ):
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._registry = registry

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
        )
        return response.choices[0].message.content or ""

    async def complete_text(self, messages: list[dict[str, Any]]) -> str:
        """Completion that returns text only and never uses tools.

        This is useful for UI-only generations (e.g., generating alternative summaries)
        where tool calls are not desired.
        """
        response = await litellm.acompletion(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content or ""
