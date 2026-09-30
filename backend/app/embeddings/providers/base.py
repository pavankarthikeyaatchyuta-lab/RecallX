from abc import ABC, abstractmethod
from typing import Any


class EmbeddingProvider(ABC):
    """Abstract Base Class for RecallX embedding providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider, e.g. 'Local CPU Provider' or 'Qualcomm QNN Provider'."""
        pass

    @property
    @abstractmethod
    def runtime(self) -> str:
        """Underlying runtime, e.g. 'CPU', 'QNN (NPU)', 'CUDA'."""
        pass

    @property
    @abstractmethod
    def device(self) -> str:
        """Target device, e.g. 'Snapdragon NPU', 'Host CPU'."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector embedding dimensionality, e.g. 384 or 768."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks whether this provider can run on the current host machine."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generates embedding for a single text query or document."""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a batch of texts."""
        pass

    @abstractmethod
    def get_info(self) -> dict[str, Any]:
        """Returns metadata regarding model, execution provider, and hardware status."""
        pass
