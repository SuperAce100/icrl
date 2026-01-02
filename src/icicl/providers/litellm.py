"""LiteLLM provider for broad LLM support."""

from typing import Any

import litellm

from icicl.models import Message


class LiteLLMProvider:
    """LLM provider using LiteLLM for 100+ model support.

    Supports OpenAI, Anthropic, Google, Azure, and many other providers
    through a unified interface.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the LiteLLM provider.

        Args:
            model: The model identifier (e.g., "gpt-4o-mini", "claude-3-sonnet").
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate. None for model default.
            system_prompt: Optional system prompt to prepend to all requests.
            **kwargs: Additional arguments passed to litellm.acompletion.
        """
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt
        self._kwargs = kwargs

    async def complete(self, messages: list[Message]) -> str:
        """Generate a completion from the given messages.

        Args:
            messages: A list of Message objects representing the conversation.

        Returns:
            The generated completion as a string.

        Raises:
            Exception: If the LLM call fails (user should handle retries).
        """
        litellm_messages = []

        # Add system prompt if configured
        if self._system_prompt:
            litellm_messages.append({"role": "system", "content": self._system_prompt})

        litellm_messages.extend(
            [{"role": m.role, "content": m.content} for m in messages]
        )

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": litellm_messages,
            "temperature": self._temperature,
            **self._kwargs,
        }
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens

        response = await litellm.acompletion(**kwargs)
        return response.choices[0].message.content or ""

    def complete_sync(self, messages: list[Message]) -> str:
        """Synchronous version of complete.

        Args:
            messages: A list of Message objects representing the conversation.

        Returns:
            The generated completion as a string.
        """
        litellm_messages = []

        # Add system prompt if configured
        if self._system_prompt:
            litellm_messages.append({"role": "system", "content": self._system_prompt})

        litellm_messages.extend(
            [{"role": m.role, "content": m.content} for m in messages]
        )

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": litellm_messages,
            "temperature": self._temperature,
            **self._kwargs,
        }
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens

        response = litellm.completion(**kwargs)
        return response.choices[0].message.content or ""
