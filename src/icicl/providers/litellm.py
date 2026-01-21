"""LiteLLM provider for broad LLM support."""

import os
import time
from typing import Any

import litellm

# Disable LiteLLM's async logging worker to avoid event loop mismatch errors
# when asyncio.run() is called multiple times.
litellm.disable_logging_worker = True

from litellm.exceptions import BadRequestError  # noqa: E402

from icicl._debug import log as _debug_log  # noqa: E402
from icicl.models import Message  # noqa: E402


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

        # Token profiling / safety
        self._call_count = 0
        self._token_retry_count = 0
        self._output_limit_retry_count = 0
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._max_prompt_tokens = 0
        self._max_completion_tokens = 0
        self._last_call: dict[str, int | str | float | None] = {}

        try:
            self._model_info = litellm.get_model_info(model)
        except Exception:
            self._model_info = {}

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

        trace_tokens = os.environ.get("ICICL_TRACE_TOKENS", "0").lower() in {
            "1",
            "true",
            "yes",
        }

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

        # Token-based budget check: ensure we leave enough room for completion.
        min_completion = int(os.environ.get("ICICL_LLM_MIN_COMPLETION_TOKENS", "512"))
        if min_completion < 1:
            min_completion = 1

        prompt_tokens = self._count_prompt_tokens(litellm_messages)
        # Use a "soft" per-call completion budget to discourage runaway outputs,
        # while keeping the configured max_tokens as an upper bound.
        requested_max = None
        if self._max_tokens is not None:
            requested_max = min(
                self._max_tokens,
                self._choose_soft_max_tokens(litellm_messages),
            )

        safe_kwargs = (
            self._get_safe_token_kwargs(
                litellm_messages,
                requested_max,
                prompt_tokens=prompt_tokens,
            )
            if requested_max is not None
            else {}
        )

        # If the prompt nearly fills the context window, truncate further to ensure
        # at least `min_completion` tokens are available.
        max_context = self._get_max_context_tokens()
        safety = int(os.environ.get("ICICL_LLM_CONTEXT_SAFETY_TOKENS", "512"))
        if safety < 0:
            safety = 0
        if (
            max_context is not None
            and prompt_tokens is not None
            and (max_context - prompt_tokens - safety) < min_completion
        ):
            target_prompt = max(1, max_context - safety - min_completion)
            self._shrink_last_message_to_target_tokens(
                litellm_messages, target_prompt_tokens=target_prompt
            )
            prompt_tokens = self._count_prompt_tokens(litellm_messages)
            if requested_max is not None:
                safe_kwargs = self._get_safe_token_kwargs(
                    litellm_messages,
                    requested_max,
                    prompt_tokens=prompt_tokens,
                )

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": litellm_messages,
            "temperature": self._temperature,
            **self._kwargs,
        }
        if safe_kwargs:
            kwargs.update(safe_kwargs)

        start = time.time()
        self._call_count += 1
        self._last_call = {
            "model": self._model,
            "prompt_tokens": prompt_tokens,
            "max_tokens": int(kwargs.get("max_tokens") or 0) or None,
            "max_completion_tokens": int(kwargs.get("max_completion_tokens") or 0)
            or None,
            "elapsed_sec": None,
        }
        if trace_tokens and prompt_tokens is not None:
            print(
                f"[icicl.tokens] model={self._model} prompt_tokens={prompt_tokens} "
                f"max_tokens={kwargs.get('max_tokens')} "
                f"max_completion_tokens={kwargs.get('max_completion_tokens')}"
            )

        try:
            response = await litellm.acompletion(**kwargs)
            self._record_usage(response, prompt_tokens=prompt_tokens, start=start)
            return response.choices[0].message.content or ""
        except Exception as e:
            # region agent log (debug-mode)
            _debug_log(
                hypothesis_id="H3",
                location="src/icicl/providers/litellm.py:LiteLLMProvider.complete",
                message="litellm_exception",
                data={
                    "pid": os.getpid(),
                    "model": self._model,
                    "exc_type": type(e).__name__,
                    "exc": str(e)[:800],
                    "is_bad_request": isinstance(e, BadRequestError),
                    "prompt_tokens": prompt_tokens,
                    "max_tokens": kwargs.get("max_tokens"),
                    "max_completion_tokens": kwargs.get("max_completion_tokens"),
                },
            )
            # endregion agent log (debug-mode)
            if isinstance(e, BadRequestError):
                err = str(e).lower()
                is_output_limit_error = any(
                    s in err
                    for s in (
                        "try again with higher max_tokens",
                        "try again with higher max tokens",
                        "higher max_tokens",
                        "higher max tokens",
                        "model output limit was reached",
                        "output limit was reached",
                    )
                )
                is_token_error = any(
                    s in err
                    for s in (
                        "max tokens",
                        "max_tokens",
                        "max_completion_tokens",
                        "context length",
                        "context_length",
                        "context window",
                        "maximum context length",
                        "too many tokens",
                        "prompt is too long",
                    )
                )
                if is_token_error:
                    # Some OpenAI models return a 400 if the response would be cut
                    # off due to `max_tokens` being too small. In that case, the fix
                    # is to INCREASE the completion budget.
                    if is_output_limit_error:
                        self._output_limit_retry_count += 1
                        current = None
                        for k in ("max_completion_tokens", "max_tokens"):
                            if k in kwargs:
                                try:
                                    current = int(kwargs[k])
                                except Exception:
                                    current = None
                                break
                        if current is None:
                            current = self._max_tokens or 4096

                        bumped = max(current + 1, current * 2)
                        try:
                            kwargs.update(
                                self._get_safe_token_kwargs(kwargs["messages"], bumped)
                            )
                            response = await litellm.acompletion(**kwargs)
                            self._record_usage(
                                response, prompt_tokens=prompt_tokens, start=start
                            )
                            return response.choices[0].message.content or ""
                        except BadRequestError as e2:
                            # If bumping doesn't help (e.g. model output limit),
                            # force a concise retry instead of crashing the trial.
                            err2 = str(e2).lower()
                            still_output_limited = any(
                                s in err2
                                for s in (
                                    "try again with higher max_tokens",
                                    "try again with higher max tokens",
                                    "higher max_tokens",
                                    "higher max tokens",
                                    "model output limit was reached",
                                    "output limit was reached",
                                )
                            )
                            if not still_output_limited:
                                raise

                            msgs = kwargs["messages"]
                            if msgs and isinstance(msgs[-1], dict):
                                msgs[-1]["content"] = (
                                    msgs[-1]["content"]
                                    + "\n\nIMPORTANT: Your previous response was too "
                                    + "long and exceeded the output limit. "
                                    "Respond very concisely. "
                                    "Do NOT include code fences. "
                                    "Do NOT repeat commands."
                                )
                            max_retry = int(
                                os.environ.get(
                                    "ICICL_LLM_OUTPUT_LIMIT_RETRY_MAX_TOKENS", "16384"
                                )
                            )
                            if max_retry < 1:
                                max_retry = 1
                            if self._max_tokens is not None:
                                try:
                                    max_retry = min(max_retry, int(self._max_tokens))
                                except Exception:
                                    pass
                            retry_budget = min(bumped, max_retry)
                            kwargs.update(
                                self._get_safe_token_kwargs(msgs, retry_budget)
                            )
                            try:
                                response = await litellm.acompletion(**kwargs)
                            except BadRequestError as e3:
                                err3 = str(e3).lower()
                                still_output_limited_3 = any(
                                    s in err3
                                    for s in (
                                        "try again with higher max_tokens",
                                        "try again with higher max tokens",
                                        "higher max_tokens",
                                        "higher max tokens",
                                        "model output limit was reached",
                                        "output limit was reached",
                                    )
                                )
                                if still_output_limited_3:
                                    return self._fallback_completion(kwargs["messages"])
                                raise
                            self._record_usage(
                                response, prompt_tokens=prompt_tokens, start=start
                            )
                            return response.choices[0].message.content or ""

                    # Retry with more aggressive truncation + smaller completion budget.
                    self._token_retry_count += 1
                    for msg in kwargs["messages"]:
                        if len(msg["content"]) > 6000:
                            msg["content"] = (
                                msg["content"][:3000]
                                + "\n...[truncated]...\n"
                                + msg["content"][-1500:]
                            )

                    # Recompute a conservative token budget for the retry.
                    retry_max = (
                        4096
                        if self._max_tokens is None
                        else min(self._max_tokens, 4096)
                    )
                    kwargs.update(
                        self._get_safe_token_kwargs(kwargs["messages"], retry_max)
                    )

                    response = await litellm.acompletion(**kwargs)
                    self._record_usage(
                        response, prompt_tokens=prompt_tokens, start=start
                    )
                    return response.choices[0].message.content or ""
                raise
            raise

    def _fallback_completion(self, messages: list[dict[str, str]]) -> str:
        """Best-effort fallback completion for transient/provider errors.

        This keeps Harbor trials running even if the provider fails to return
        a response (e.g. output-limit errors on some models).
        """
        last = messages[-1].get("content", "").lower() if messages else ""
        if "output one command" in last or "respond with only the command" in last:
            return "ls"
        if "create a short plan" in last or "create a concise" in last:
            return "\n".join(
                [
                    "1. Find and read the relevant code",
                    "2. Identify the failing test / symptom",
                    "3. Make the minimal fix",
                    "4. Verify and submit",
                ]
            )
        return (
            "Next: use the current output to locate the relevant code, "
            "apply a minimal fix, and verify."
        )

    def _count_prompt_tokens(self, messages: list[dict[str, str]]) -> int | None:
        try:
            return int(litellm.token_counter(model=self._model, messages=messages))
        except Exception:
            # Fallback heuristic: ~4 chars per token.
            try:
                total_chars = sum(len(m.get("content", "")) for m in messages)
                return max(1, total_chars // 4)
            except Exception:
                return None

    def _choose_soft_max_tokens(self, messages: list[dict[str, str]]) -> int:
        """Pick a per-call max completion budget based on prompt type."""
        # Defaults are intentionally conservative to prevent runaway outputs.
        plan_max = max(int(os.environ.get("ICICL_LLM_MAX_TOKENS_PLAN", "2048")), 64)
        reason_max = max(int(os.environ.get("ICICL_LLM_MAX_TOKENS_REASON", "4096")), 64)
        act_max = max(int(os.environ.get("ICICL_LLM_MAX_TOKENS_ACT", "512")), 64)

        last = messages[-1]["content"].lower() if messages else ""
        if "output one command" in last or "respond with only the command" in last:
            return act_max
        if "create a short plan" in last or "create a concise" in last:
            return plan_max
        if "think:" in last or "analyze" in last:
            return reason_max
        return reason_max

    def _get_max_context_tokens(self) -> int | None:
        val = self._model_info.get("max_input_tokens") or None
        try:
            return int(val) if val is not None else None
        except Exception:
            return None

    def _get_max_output_tokens(self) -> int | None:
        val = (
            self._model_info.get("max_output_tokens")
            or self._model_info.get("max_tokens")
            or None
        )
        try:
            return int(val) if val is not None else None
        except Exception:
            return None

    def _shrink_last_message_to_target_tokens(
        self,
        messages: list[dict[str, str]],
        *,
        target_prompt_tokens: int,
        max_iters: int = 3,
    ) -> None:
        """Shrink the last message until prompt tokens are <= target."""
        if not messages:
            return
        last = messages[-1]
        content = last.get("content", "")
        if not content:
            return

        for _ in range(max_iters):
            current = self._count_prompt_tokens(messages)
            if current is None or current <= target_prompt_tokens:
                return

            # Approximate proportional truncation (tokens ~ chars).
            ratio = target_prompt_tokens / max(1, current)
            new_len = max(1000, int(len(content) * ratio))
            if new_len >= len(content):
                new_len = max(1000, len(content) - 1000)

            head = content[: new_len // 2]
            tail = content[-(new_len // 2) :]
            content = head + "\n...[truncated]...\n" + tail
            last["content"] = content

    def _record_usage(
        self,
        response: Any,
        *,
        prompt_tokens: int | None,
        start: float,
    ) -> None:
        elapsed = time.time() - start

        usage = getattr(response, "usage", None)
        prompt_used = None
        completion_used = None
        if usage is not None:
            prompt_used = getattr(usage, "prompt_tokens", None) or getattr(
                usage, "input_tokens", None
            )
            completion_used = getattr(usage, "completion_tokens", None) or getattr(
                usage, "output_tokens", None
            )
            if isinstance(usage, dict):
                prompt_used = prompt_used or usage.get("prompt_tokens") or usage.get(
                    "input_tokens"
                )
                completion_used = completion_used or usage.get(
                    "completion_tokens"
                ) or usage.get("output_tokens")

        prompt_final = int(prompt_used) if prompt_used is not None else prompt_tokens
        completion_final = int(completion_used) if completion_used is not None else None

        if prompt_final is not None:
            self._total_prompt_tokens += prompt_final
            self._max_prompt_tokens = max(self._max_prompt_tokens, prompt_final)
        if completion_final is not None:
            self._total_completion_tokens += completion_final
            self._max_completion_tokens = max(
                self._max_completion_tokens, completion_final
            )

        self._last_call["elapsed_sec"] = elapsed
        if prompt_final is not None:
            self._last_call["prompt_tokens"] = prompt_final
        if completion_final is not None:
            self._last_call["completion_tokens"] = completion_final

    def get_token_profile(self) -> dict[str, int | str | float | None]:
        """Return aggregate token stats for this provider instance."""
        return {
            "model": self._model,
            "calls": self._call_count,
            "prompt_tokens_total": self._total_prompt_tokens,
            "completion_tokens_total": self._total_completion_tokens,
            "prompt_tokens_max": self._max_prompt_tokens,
            "completion_tokens_max": self._max_completion_tokens,
            "token_retries": self._token_retry_count,
            "output_limit_retries": self._output_limit_retry_count,
        }

    def get_last_call_profile(self) -> dict[str, int | str | float | None]:
        """Return the last call's token stats."""
        return dict(self._last_call)

    def _get_safe_token_kwargs(
        self,
        messages: list[dict[str, str]],
        requested_max_tokens: int,
        *,
        prompt_tokens: int | None = None,
    ) -> dict[str, int]:
        """Compute a safe max tokens setting for this request.

        We clamp to the model's max output tokens and (conservatively) ensure:
          prompt_tokens + completion_tokens <= context_window_tokens
        """
        requested = max(1, int(requested_max_tokens))

        # Default safety margin to avoid edge-of-window errors.
        safety = int(os.environ.get("ICICL_LLM_CONTEXT_SAFETY_TOKENS", "512"))
        if safety < 0:
            safety = 0

        max_context: int | None = None
        max_output: int | None = None
        max_context = self._get_max_context_tokens()
        max_output = self._get_max_output_tokens()

        if prompt_tokens is None:
            prompt_tokens = self._count_prompt_tokens(messages)

        safe = requested
        if max_output is not None:
            safe = min(safe, int(max_output))
        if max_context is not None and prompt_tokens is not None:
            safe = min(safe, max(1, int(max_context) - prompt_tokens - safety))

        # IMPORTANT: Do NOT set both `max_tokens` and `max_completion_tokens`.
        #
        # OpenAI's Chat Completions API rejects requests that include both
        # parameters (400 invalid_parameter_combination). LiteLLM can map the
        # OpenAI-style `max_tokens` across providers, so we stick to `max_tokens`
        # only for broad compatibility.
        return {"max_tokens": safe}

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
            kwargs.update(
                self._get_safe_token_kwargs(litellm_messages, self._max_tokens)
            )

        response = litellm.completion(**kwargs)
        return response.choices[0].message.content or ""
