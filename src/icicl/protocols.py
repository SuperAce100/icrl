"""Protocol definitions for icicl components."""

from typing import Protocol, runtime_checkable

from icicl.models import Message


@runtime_checkable
class Environment(Protocol):
    """Protocol for environments that the agent interacts with.

    Users must implement this protocol for their specific environment.
    """

    def reset(self, goal: str) -> str:
        """Reset the environment for a new episode.

        Args:
            goal: The goal description for this episode.

        Returns:
            The initial observation as a string.
        """
        ...

    def step(self, action: str) -> tuple[str, bool]:
        """Execute an action in the environment.

        Args:
            action: The action to execute.

        Returns:
            A tuple of (observation, done) where observation is the resulting
            observation string and done indicates if the episode has ended.
        """
        ...

    def is_success(self) -> bool:
        """Check if the current episode was successful.

        Returns:
            True if the episode ended successfully, False otherwise.
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

