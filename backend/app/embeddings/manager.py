import time
from typing import Any

from backend.app.core.config import settings
from backend.app.embeddings.providers.base import EmbeddingProvider
from backend.app.embeddings.providers.cpu_provider import LocalCPUProvider
from backend.app.embeddings.providers.qualcomm_provider import QualcommQNNProvider


class ModelManager:
    """
    Manages embedding model providers, runtime selection, and inference fallbacks.
    Truthfully switches between Qualcomm QNN (NPU) and Local CPU fallback.
    """

    def __init__(self):
        self.cpu_provider = LocalCPUProvider()
        self.qualcomm_provider = QualcommQNNProvider()
        self._active_provider: EmbeddingProvider = self.cpu_provider
        self.refresh_provider()

    def refresh_provider(self) -> None:
        """Selects provider according to user settings and hardware availability."""
        pref = settings.preferred_provider.lower()

        if pref == "qualcomm":
            if self.qualcomm_provider.is_available():
                self._active_provider = self.qualcomm_provider
            else:
                self._active_provider = self.cpu_provider
        elif pref == "cpu":
            self._active_provider = self.cpu_provider
        else:  # "auto"
            if self.qualcomm_provider.is_available():
                self._active_provider = self.qualcomm_provider
            else:
                self._active_provider = self.cpu_provider

    @property
    def active_provider(self) -> EmbeddingProvider:
        return self._active_provider

    def embed_text(self, text: str) -> tuple[list[float], float]:
        """
        Embeds a single string.
        Returns:
            (embedding_vector, latency_ms)
        """
        start = time.perf_counter()
        try:
            vec = self._active_provider.embed_text(text)
        except Exception:
            # Automatic fallback to CPU if active provider encounters error
            vec = self.cpu_provider.embed_text(text)
            self._active_provider = self.cpu_provider

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return vec, latency_ms

    def embed_batch(self, texts: list[str]) -> tuple[list[list[float]], float]:
        """
        Embeds a batch of strings.
        Returns:
            (embedding_vectors, latency_ms)
        """
        start = time.perf_counter()
        try:
            vecs = self._active_provider.embed_batch(texts)
        except Exception:
            vecs = self.cpu_provider.embed_batch(texts)
            self._active_provider = self.cpu_provider

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return vecs, latency_ms

    def get_runtime_status(self) -> dict[str, Any]:
        """Detailed runtime information for UI inspection."""
        is_qnn_active = self._active_provider == self.qualcomm_provider
        qnn_info = self.qualcomm_provider.get_info()
        cpu_info = self.cpu_provider.get_info()

        return {
            "active_model": (
                self.qualcomm_provider.model_name if is_qnn_active else self.cpu_provider.model_name
            ),
            "active_runtime": (
                self.qualcomm_provider.runtime if is_qnn_active else self.cpu_provider.runtime
            ),
            "active_device": (
                self.qualcomm_provider.device if is_qnn_active else self.cpu_provider.device
            ),
            "active_provider_name": self._active_provider.name,
            "dimension": self._active_provider.dimension,
            "is_npu_active": is_qnn_active,
            "fallback_in_use": not is_qnn_active,
            "status_banner": (
                "Snapdragon NPU Acceleration Active"
                if is_qnn_active
                else "Qualcomm NPU unavailable — using CPU fallback."
            ),
            "providers": {
                "qualcomm": qnn_info,
                "cpu": cpu_info,
            },
        }


model_manager = ModelManager()
