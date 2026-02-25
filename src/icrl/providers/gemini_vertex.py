"""Gemini Vertex AI provider for Gemini models on Google Cloud."""

from pathlib import Path
from typing import Any

from icrl.providers.anthropic_vertex import AnthropicVertexProvider


class GeminiVertexProvider(AnthropicVertexProvider):
    """LLM provider for Gemini models via Google Cloud Vertex AI.

    This provider reuses the same Vertex AI credential setup as
    ``AnthropicVertexProvider``.

    Supported models:
        - gemini-3-flash-preview (maps to vertex_ai/gemini-3-flash-preview)
        - gemini-3.1-pro-preview (maps to vertex_ai/gemini-3.1-pro-preview)

    Or use the full model name directly (e.g., ``vertex_ai/gemini-3-flash-preview``).
    """

    MODEL_ALIASES: dict[str, str] = {
        "gemini-3-flash-preview": "vertex_ai/gemini-3-flash-preview",
        "gemini-3.1-pro-preview": "vertex_ai/gemini-3.1-pro-preview",
    }

    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        credentials_path: str | Path | None = None,
        project_id: str | None = None,
        location: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Gemini Vertex AI provider."""
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            credentials_path=credentials_path,
            project_id=project_id,
            location=location,
            **kwargs,
        )
