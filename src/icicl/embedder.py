"""Sentence Transformer embedder for trajectory retrieval."""

from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbedder:
    """Embedder using Sentence Transformers (matches paper's all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the embedder.

        Args:
            model_name: Name of the sentence-transformers model to use.
                       Defaults to all-MiniLM-L6-v2 as used in the paper.
        """
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors.
        """
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: String to embed.

        Returns:
            Embedding vector.
        """
        embedding = self._model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._model.get_sentence_embedding_dimension()  # type: ignore[return-value]
