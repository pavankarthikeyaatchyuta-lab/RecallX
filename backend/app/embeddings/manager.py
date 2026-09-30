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

    def warmup(self) -> float:
        """
        Pre-loads embedding model weights into memory and executes a warm-up inference.
        Eliminates first-query latency penalty for the user.
        Returns warm-up elapsed time in milliseconds.
        """
        start = time.perf_counter()
        _ = self.embed_text("RecallX on-device privacy engine warmup query.")
        return round((time.perf_counter() - start) * 1000, 2)

    def get_runtime_state(self) -> str:
        """
        Calculates the active runtime state matching the RecallX state machine:
        - QNN_ACTIVE: Qualcomm NPU provider is active and running
        - QNN_AVAILABLE: Snapdragon NPU hardware and EP available, but CPU selected by user
        - QNN_ERROR: Hardware exists but initialization failed
        - MODEL_UNAVAILABLE: Model file missing
        - CPU_FALLBACK: Host is Intel/AMD or QNN provider unavailable
        """
        if self._active_provider == self.qualcomm_provider:
            return self.qualcomm_provider.get_runtime_state()
        
        qnn_state = self.qualcomm_provider.get_runtime_state()
        if qnn_state in ("QNN_AVAILABLE", "QNN_SESSION_READY", "QNN_ERROR", "MODEL_UNAVAILABLE"):
            return qnn_state
        
        return "CPU_FALLBACK"

    def get_runtime_status(self) -> dict[str, Any]:
        """Detailed runtime information for UI inspection."""
        is_qnn_active = (
            self._active_provider == self.qualcomm_provider
            and self.qualcomm_provider.inference_verified
        )
        qnn_info = self.qualcomm_provider.get_info()
        cpu_info = self.cpu_provider.get_info()
        runtime_state = self.get_runtime_state()

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
            "runtime_state": runtime_state,
            "snapdragon_validation": "Pending" if not is_qnn_active else "Verified",
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


# Aliases for unified specification
CPUEmbeddingProvider = LocalCPUProvider
QualcommQNNEmbeddingProvider = QualcommQNNProvider

model_manager = ModelManager()
