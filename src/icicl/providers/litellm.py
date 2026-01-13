"""LiteLLM provider for broad LLM support."""

import os
from typing import Any

import litellm
from litellm.exceptions import BadRequestError

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
        litellm_messages: list[dict[str, str]] = []

        # Add system prompt if configured
        if self._system_prompt:
            litellm_messages.append({"role": "system", "content": self._system_prompt})

        litellm_messages.extend(
            [{"role": m.role, "content": m.content} for m in messages]
        )

        # Defensive truncation: keep prompts within a conservative character budget.
        # This avoids hard failures on models with smaller context windows.
        max_total_chars = int(os.environ.get("ICICL_LLM_MAX_INPUT_CHARS", "50000"))
        max_msg_chars = int(os.environ.get("ICICL_LLM_MAX_MESSAGE_CHARS", "25000"))
        if max_total_chars > 0 and max_msg_chars > 0:
            for msg in litellm_messages:
                if len(msg["content"]) > max_msg_chars:
                    msg["content"] = (
                        msg["content"][: (max_msg_chars // 2)]
                        + "\n...[truncated]...\n"
                        + msg["content"][-(max_msg_chars // 2) :]
                    )
            total = sum(len(m["content"]) for m in litellm_messages)
            if total > max_total_chars and litellm_messages:
                # Prefer truncating the last (user) message since system prompts
                # often contain critical constraints.
                over = total - max_total_chars
                last = litellm_messages[-1]
                if len(last["content"]) > over + 1000:
                    keep = len(last["content"]) - over
                    last["content"] = last["content"][:keep] + "\n...[truncated]..."

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": litellm_messages,
            "temperature": self._temperature,
            **self._kwargs,
        }
        if self._max_tokens is not None:
            # GPT-5 models use max_completion_tokens instead of max_tokens
            if "gpt-5" in self._model.lower():
                kwargs["max_completion_tokens"] = self._max_tokens
            else:
                kwargs["max_tokens"] = self._max_tokens

        try:
            response = await litellm.acompletion(**kwargs)
            return response.choices[0].message.content or ""
        except BadRequestError as e:
            err = str(e).lower()
            is_token_error = any(
                s in err
                for s in (
                    "max_tokens",
                    "max_completion_tokens",
                    "context length",
                    "context_length",
                    "too many tokens",
                    "prompt is too long",
                )
            )
            if is_token_error:
                # Retry with more aggressive truncation + smaller completion budget.
                for msg in kwargs["messages"]:
                    if len(msg["content"]) > 6000:
                        msg["content"] = (
                            msg["content"][:3000]
                            + "\n...[truncated]...\n"
                            + msg["content"][-1500:]
                        )

                # If caller asked for a huge completion, clamp it on retry.
                if "max_completion_tokens" in kwargs:
                    kwargs["max_completion_tokens"] = min(
                        int(kwargs["max_completion_tokens"]), 2048
                    )
                if "max_tokens" in kwargs:
                    kwargs["max_tokens"] = min(int(kwargs["max_tokens"]), 2048)

                response = await litellm.acompletion(**kwargs)
                return response.choices[0].message.content or ""
            raise

    def complete_sync(self, messages: list[Message]) -> str:
        """Synchronous version of complete.

        Args:
            messages: A list of Message objects representing the conversation.

        Returns:
            The generated completion as a string.
        """
        litellm_messages: list[dict[str, str]] = []

        # Add system prompt if configured
        if self._system_prompt:
            litellm_messages.append({"role": "system", "content": self._system_prompt})

        litellm_messages.extend(
            [{"role": m.role, "content": m.content} for m in messages]
        )

        max_total_chars = int(os.environ.get("ICICL_LLM_MAX_INPUT_CHARS", "50000"))
        max_msg_chars = int(os.environ.get("ICICL_LLM_MAX_MESSAGE_CHARS", "25000"))
        if max_total_chars > 0 and max_msg_chars > 0:
            for msg in litellm_messages:
                if len(msg["content"]) > max_msg_chars:
                    msg["content"] = (
                        msg["content"][: (max_msg_chars // 2)]
                        + "\n...[truncated]...\n"
                        + msg["content"][-(max_msg_chars // 2) :]
                    )
            total = sum(len(m["content"]) for m in litellm_messages)
            if total > max_total_chars and litellm_messages:
                over = total - max_total_chars
                last = litellm_messages[-1]
                if len(last["content"]) > over + 1000:
                    keep = len(last["content"]) - over
                    last["content"] = last["content"][:keep] + "\n...[truncated]..."

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": litellm_messages,
            "temperature": self._temperature,
            **self._kwargs,
        }
        if self._max_tokens is not None:
            # GPT-5 models use max_completion_tokens instead of max_tokens
            if "gpt-5" in self._model.lower():
                kwargs["max_completion_tokens"] = self._max_tokens
            else:
                kwargs["max_tokens"] = self._max_tokens

        response = litellm.completion(**kwargs)
        return response.choices[0].message.content or ""
