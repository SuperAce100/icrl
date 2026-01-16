"""LLM provider with native tool calling support."""

import json
from dataclasses import dataclass
from typing import Any

import litellm

from icicl.cli.tools.base import ToolRegistry
from icicl.models import Message


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
        )
        return response.choices[0].message.content or ""
