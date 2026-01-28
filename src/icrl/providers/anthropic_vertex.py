"""Anthropic Vertex AI provider for Claude models on Google Cloud."""

import json
import os
import time
from pathlib import Path
from typing import Any

import litellm

# Disable LiteLLM's async logging worker to avoid event loop mismatch errors
litellm.disable_logging_worker = True

# Suppress the "Provider List" debug message
litellm.suppress_debug_info = True

from litellm.exceptions import BadRequestError  # noqa: E402

from icrl._debug import log as _debug_log  # noqa: E402
from icrl.models import Message  # noqa: E402


class AnthropicVertexProvider:
    """LLM provider for Anthropic Claude models via Google Cloud Vertex AI.

    This provider uses LiteLLM under the hood but handles Vertex AI authentication
    and model naming automatically.

    Supported models:
        - claude-3-opus (maps to vertex_ai/claude-3-opus@20240229)
        - claude-3-5-sonnet / claude-3.5-sonnet (maps to claude-3-5-sonnet-v2)
        - claude-3-sonnet (maps to vertex_ai/claude-3-sonnet@20240229)
        - claude-3-haiku (maps to vertex_ai/claude-3-haiku@20240307)
        - claude-3-7-sonnet / claude-3.7-sonnet (maps to claude-3-7-sonnet)
        - claude-sonnet-4 (maps to vertex_ai/claude-sonnet-4@20250514)

    Or use the full model name directly (e.g., "vertex_ai/claude-3-5-sonnet").
    """

    # Model aliases for convenient shorthand names
    MODEL_ALIASES: dict[str, str] = {
        # Claude 3 models
        "claude-3-opus": "vertex_ai/claude-3-opus@20240229",
        "claude-3-sonnet": "vertex_ai/claude-3-sonnet@20240229",
        "claude-3-haiku": "vertex_ai/claude-3-haiku@20240307",
        # Claude 3.5 models
        "claude-3-5-sonnet": "vertex_ai/claude-3-5-sonnet-v2@20241022",
        "claude-3.5-sonnet": "vertex_ai/claude-3-5-sonnet-v2@20241022",
        "claude-3-5-sonnet-v1": "vertex_ai/claude-3-5-sonnet@20240620",
        "claude-3-5-haiku": "vertex_ai/claude-3-5-haiku@20241022",
        "claude-3.5-haiku": "vertex_ai/claude-3-5-haiku@20241022",
        # Claude 3.7 models
        "claude-3-7-sonnet": "vertex_ai/claude-3-7-sonnet@20250219",
        "claude-3.7-sonnet": "vertex_ai/claude-3-7-sonnet@20250219",
        # Claude 4 models
        "claude-sonnet-4": "vertex_ai/claude-sonnet-4@20250514",
        "claude-4-sonnet": "vertex_ai/claude-sonnet-4@20250514",
        "claude-opus-4": "vertex_ai/claude-opus-4@20250514",
        "claude-4-opus": "vertex_ai/claude-opus-4@20250514",
        # Claude 4.5 models (latest)
        "claude-opus-4.5": "vertex_ai/claude-opus-4-5@20251101",
        "claude-opus-4-5": "vertex_ai/claude-opus-4-5@20251101",
        "claude-4.5-opus": "vertex_ai/claude-opus-4-5@20251101",
        "claude-sonnet-4.5": "vertex_ai/claude-sonnet-4-5@20251101",
        "claude-sonnet-4-5": "vertex_ai/claude-sonnet-4-5@20251101",
        "claude-4.5-sonnet": "vertex_ai/claude-sonnet-4-5@20251101",
        "claude-haiku-4.5": "vertex_ai/claude-haiku-4-5@20251101",
        "claude-haiku-4-5": "vertex_ai/claude-haiku-4-5@20251101",
        "claude-4.5-haiku": "vertex_ai/claude-haiku-4-5@20251101",
    }

    def __init__(
        self,
        model: str = "claude-opus-4-5",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        credentials_path: str | Path | None = None,
        project_id: str | None = None,
        location: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Anthropic Vertex AI provider.

        Args:
            model: Model name (shorthand or full vertex_ai/ path).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate. None for model default.
            system_prompt: Optional system prompt to prepend to all requests.
            credentials_path: Path to GCP service account JSON file.
                             Falls back to GOOGLE_APPLICATION_CREDENTIALS env var.
            project_id: GCP project ID. Falls back to VERTEXAI_PROJECT env var
                       or extracted from credentials file.
            location: GCP region (e.g., "global", "us-east5"). Falls back to 
                     VERTEXAI_LOCATION env var or defaults to "global".
            **kwargs: Additional arguments passed to litellm.acompletion.
        """
        # Resolve model name
        self._model = self._resolve_model(model)
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt
        self._kwargs = kwargs

        # Set up credentials
        self._setup_credentials(credentials_path, project_id, location)

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
            self._model_info = litellm.get_model_info(self._model)
        except Exception:
            self._model_info = {}

    def _resolve_model(self, model: str) -> str:
        """Resolve model shorthand to full vertex_ai model path."""
        # Check if it's already a full vertex_ai path
        if model.startswith("vertex_ai/"):
            return model

        # Check aliases
        if model in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model]

        # Assume it's a full model name and add vertex_ai prefix
        return f"vertex_ai/{model}"

    def _setup_credentials(
        self,
        credentials_path: str | Path | None,
        project_id: str | None,
        location: str | None,
    ) -> None:
        """Set up GCP credentials for Vertex AI authentication."""
        # Handle credentials file path
        creds_path = credentials_path
        if creds_path is None:
            # Check environment variable
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path is None:
                # Check common locations
                gcloud_default = (
                    Path.home()
                    / ".config"
                    / "gcloud"
                    / "application_default_credentials.json"
                )
                for candidate in [Path("credentials.json"), gcloud_default]:
                    if candidate.exists():
                        creds_path = str(candidate)
                        break

        if creds_path:
            creds_path = Path(creds_path)
            if creds_path.exists():
                creds_abs = str(creds_path.absolute())
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_abs

                # Try to extract project_id from credentials if not provided
                if project_id is None:
                    try:
                        with open(creds_path) as f:
                            creds_data = json.load(f)
                            project_id = creds_data.get("project_id")
                    except (json.JSONDecodeError, OSError):
                        pass
            else:
                raise FileNotFoundError(
                    f"Credentials file not found: {creds_path}. "
                    "Please provide a valid path to your GCP service account JSON file."
                )

        # Set project ID
        if project_id:
            os.environ["VERTEXAI_PROJECT"] = project_id
            self._project_id = project_id
        else:
            self._project_id = os.environ.get("VERTEXAI_PROJECT")
            if not self._project_id:
                raise ValueError(
                    "GCP project ID not found. Provide project_id parameter, "
                    "set VERTEXAI_PROJECT environment variable, or ensure your "
                    "credentials.json contains a project_id field."
                )

        # Set location (default to global for Anthropic models on Vertex AI)
        if location:
            os.environ["VERTEXAI_LOCATION"] = location
            self._location = location
        else:
            self._location = os.environ.get("VERTEXAI_LOCATION", "global")
            os.environ["VERTEXAI_LOCATION"] = self._location

    @property
    def model(self) -> str:
        """Return the resolved model name."""
        return self._model

    @property
    def project_id(self) -> str | None:
        """Return the GCP project ID."""
        return self._project_id

    @property
    def location(self) -> str:
        """Return the GCP location/region."""
        return self._location

    async def complete(self, messages: list[Message]) -> str:
        """Generate a completion from the given messages.

        Args:
            messages: A list of Message objects representing the conversation.

        Returns:
            The generated completion as a string.

        Raises:
            Exception: If the LLM call fails.
        """
        litellm_messages: list[dict[str, str]] = []

        # Add system prompt if configured
        if self._system_prompt:
            litellm_messages.append({"role": "system", "content": self._system_prompt})

        litellm_messages.extend(
            [{"role": m.role, "content": m.content} for m in messages]
        )

        # Defensive truncation
        max_total_chars = int(os.environ.get("ICRL_LLM_MAX_INPUT_CHARS", "50000"))
        max_msg_chars = int(os.environ.get("ICRL_LLM_MAX_MESSAGE_CHARS", "25000"))
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
            "vertex_ai_project": self._project_id,
            "vertex_ai_location": self._location,
            **self._kwargs,
        }
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens

        start = time.time()
        self._call_count += 1
        prompt_tokens = self._count_prompt_tokens(litellm_messages)
        self._last_call = {
            "model": self._model,
            "prompt_tokens": prompt_tokens,
            "max_tokens": self._max_tokens,
            "elapsed_sec": None,
        }

        try:
            response = await litellm.acompletion(**kwargs)
            self._record_usage(response, prompt_tokens=prompt_tokens, start=start)
            return response.choices[0].message.content or ""
        except Exception as e:
            _debug_log(
                hypothesis_id="H3",
                location="src/icrl/providers/anthropic_vertex.py:AnthropicVertexProvider.complete",
                message="vertex_ai_exception",
                data={
                    "pid": os.getpid(),
                    "model": self._model,
                    "exc_type": type(e).__name__,
                    "exc": str(e)[:800],
                    "is_bad_request": isinstance(e, BadRequestError),
                    "prompt_tokens": prompt_tokens,
                    "max_tokens": kwargs.get("max_tokens"),
                },
            )
            if isinstance(e, BadRequestError):
                err = str(e).lower()
                is_token_error = any(
                    s in err
                    for s in (
                        "max tokens",
                        "max_tokens",
                        "context length",
                        "context_length",
                        "too many tokens",
                        "prompt is too long",
                    )
                )
                if is_token_error:
                    # Retry with truncation
                    self._token_retry_count += 1
                    for msg in kwargs["messages"]:
                        if len(msg["content"]) > 6000:
                            msg["content"] = (
                                msg["content"][:3000]
                                + "\n...[truncated]...\n"
                                + msg["content"][-1500:]
                            )
                    response = await litellm.acompletion(**kwargs)
                    self._record_usage(
                        response, prompt_tokens=prompt_tokens, start=start
                    )
                    return response.choices[0].message.content or ""
            raise

    def _count_prompt_tokens(self, messages: list[dict[str, str]]) -> int | None:
        """Count approximate prompt tokens."""
        try:
            return int(litellm.token_counter(model=self._model, messages=messages))
        except Exception:
            try:
                total_chars = sum(len(m.get("content", "")) for m in messages)
                return max(1, total_chars // 4)
            except Exception:
                return None

    def _record_usage(
        self,
        response: Any,
        *,
        prompt_tokens: int | None,
        start: float,
    ) -> None:
        """Record token usage from response."""
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

    def complete_sync(self, messages: list[Message]) -> str:
        """Synchronous version of complete."""
        litellm_messages: list[dict[str, str]] = []

        if self._system_prompt:
            litellm_messages.append({"role": "system", "content": self._system_prompt})

        litellm_messages.extend(
            [{"role": m.role, "content": m.content} for m in messages]
        )

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": litellm_messages,
            "temperature": self._temperature,
            "vertex_ai_project": self._project_id,
            "vertex_ai_location": self._location,
            **self._kwargs,
        }
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens

        response = litellm.completion(**kwargs)
        return response.choices[0].message.content or ""
