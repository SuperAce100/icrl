"""Protocol definitions for ICICL components."""

from typing import Protocol, runtime_checkable

from icicl.models import Message


@runtime_checkable
class Environment(Protocol):
    """Protocol for environments that the agent interacts with."""

    def reset(self, goal: str) -> str:
        """Reset the environment for a new episode.

        The environment should store the goal internally for use
        when determining success in step().

        Args:
            goal: The goal description for this episode.

        Returns:
            The initial observation as a string.
        """
        ...

    def step(self, action: str) -> tuple[str, bool, bool]:
        """Execute an action in the environment.

        Args:
            action: The action to execute.

        Returns:
            A tuple of (observation, done, success) where:
            - observation: The resulting observation string
            - done: Whether the episode has ended
            - success: Whether the goal was achieved (use stored goal from reset)
        """
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers.

    Users can implement this protocol or use the built-in LiteLLMProvider.
    """

    async def complete(self, messages: list[Message]) -> str:
        """Generate a completion from the given messages.

        Args:
            messages: A list of Message objects representing the conversation.

        Returns:
            The generated completion as a string.
        """
        ...


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding providers (internal use)."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors.
        """
        ...

    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: String to embed.

        Returns:
            Embedding vector.
        """
        ...
