"""Embedding utilities for trajectory retrieval.

The original SGICL/ICICL paper uses Sentence-Transformers (`all-MiniLM-L6-v2`)
for semantic retrieval. In practice (especially under multi-processing and/or
restricted internet), eagerly downloading/loading HF models can make agents
appear "stuck" before they ever take a step.

To keep Harbor/SWE-bench runs robust, ICICL defaults to a lightweight,
deterministic **hash embedder** that requires no external downloads.
You can opt into Sentence-Transformers by setting:

  ICICL_EMBEDDER=sentence-transformers
  ICICL_EMBEDDER_ALLOW_DOWNLOAD=1  # optional
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Final

import numpy as np

from icicl.protocols import Embedder

_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_]+")


class HashEmbedder:
    """Fast, deterministic embedder using feature hashing.

    This is not as semantically rich as Sentence-Transformers, but it is:
    - offline-safe (no downloads)
    - deterministic across runs/processes
    - cheap enough to run inside tight Harbor loops
    """

    def __init__(self, dimension: int = 384, seed: str = "icicl-hash-v1") -> None:
        self._dimension = int(dimension)
        if self._dimension <= 0:
            raise ValueError("dimension must be positive")
        self._seed = seed.encode("utf-8")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_single(t) for t in texts]

    def embed_single(self, text: str) -> list[float]:
        vec = np.zeros(self._dimension, dtype=np.float32)
        for token in _TOKEN_RE.findall(text.lower()):
            h64 = self._hash64(token)
            idx = int(h64 % self._dimension)
            sign = 1.0 if (h64 & 1) == 0 else -1.0
            vec[idx] += sign

        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def _hash64(self, token: str) -> int:
        digest = hashlib.blake2b(
            token.encode("utf-8"), digest_size=8, key=self._seed
        ).digest()
        return int.from_bytes(digest, "little", signed=False)

    @property
    def dimension(self) -> int:
        return self._dimension


class SentenceTransformerEmbedder:
    """Embedder using Sentence-Transformers (paper default: all-MiniLM-L6-v2)."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        *,
        allow_download: bool | None = None,
    ) -> None:
        # Avoid noisy "tokenizers parallelism after fork" warnings by default.
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

        if allow_download is None:
            env_val = os.environ.get("ICICL_EMBEDDER_ALLOW_DOWNLOAD", "0").lower()
            allow_download = env_val in {"1", "true", "yes"}

        # Default to offline-safe behavior unless explicitly allowed.
        if not allow_download:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

        # Import lazily so the default HashEmbedder path stays lightweight.
        from sentence_transformers import SentenceTransformer

        # Some versions accept local_files_only; others rely on env vars above.
        try:
            self._model = SentenceTransformer(
                model_name,
                local_files_only=not allow_download,
            )
        except TypeError:
            self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_single(self, text: str) -> list[float]:
        embedding = self._model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()  # type: ignore[return-value]


def default_embedder() -> Embedder:
    """Create the default embedder based on environment configuration.

    Env:
      - ICICL_EMBEDDER: "hash" (default) or "sentence-transformers"
      - ICICL_EMBEDDER_ALLOW_DOWNLOAD: "1" to allow HF downloads (ST only)
    """
    kind = os.environ.get("ICICL_EMBEDDER", "hash").strip().lower()
    if kind in {"sentence-transformers", "sentence_transformers", "st"}:
        try:
            return SentenceTransformerEmbedder()
        except Exception:
            # Fall back silently; Harbor runs must not hang on embedder init.
            return HashEmbedder()
    return HashEmbedder()
