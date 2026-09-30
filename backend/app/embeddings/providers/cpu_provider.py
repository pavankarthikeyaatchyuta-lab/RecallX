from typing import Any
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.embeddings.providers.base import EmbeddingProvider


class LocalCPUProvider(EmbeddingProvider):
    """
    Local CPU-compatible embedding provider.
    Uses all-MiniLM-L6-v2 (384-dim) via SentenceTransformers.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._dim = 384
        self._cache: dict[str, list[float]] = {}

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            import os
            # Prefer local cache to prevent unnecessary external network calls
            try:
                self._model = SentenceTransformer(self.model_name, local_files_only=True)
            except Exception:
                self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def name(self) -> str:
        return "Local CPU Embedding Provider"

    @property
    def runtime(self) -> str:
        return "PyTorch / CPU"

    @property
    def device(self) -> str:
        return "CPU"

    @property
    def dimension(self) -> int:
        return self._dim

    def is_available(self) -> bool:
        return True

    def embed_text(self, text: str) -> list[float]:
        text_clean = text.strip()
        if not text_clean:
            return [0.0] * self._dim

        if text_clean in self._cache:
            return self._cache[text_clean]

        model = self._load_model()
        vec = model.encode(text_clean, convert_to_numpy=True, normalize_embeddings=True)
        res = vec.tolist()
        self._cache[text_clean] = res
        return res

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        results: list[list[float]] = []
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for idx, t in enumerate(texts):
            clean_t = t.strip()
            if not clean_t:
                results.append([0.0] * self._dim)
            elif clean_t in self._cache:
                results.append(self._cache[clean_t])
            else:
                results.append([])
                uncached_indices.append(idx)
                uncached_texts.append(clean_t)

        if uncached_texts:
            model = self._load_model()
            embeddings = model.encode(
                uncached_texts,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            for orig_idx, emb, txt in zip(uncached_indices, embeddings, uncached_texts):
                res = emb.tolist()
                self._cache[txt] = res
                results[orig_idx] = res

        return results

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model": self.model_name,
            "runtime": self.runtime,
            "device": self.device,
            "dimension": self.dimension,
            "is_active": True,
            "cached_items": len(self._cache),
        }


# Aliases for unified specification
CPUEmbeddingProvider = LocalCPUProvider
