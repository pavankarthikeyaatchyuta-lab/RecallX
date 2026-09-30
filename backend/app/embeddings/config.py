from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CPUModelConfig:
    """Model configuration for host CPU development / fallback runtime."""
    model_id: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    runtime: str = "CPU"
    device: str = "Host CPU"
    framework: str = "SentenceTransformers / PyTorch"


@dataclass(frozen=True)
class QualcommModelConfig:
    """Model configuration for target Qualcomm Snapdragon Hexagon NPU runtime."""
    model_id: str = "nomic-ai/nomic-embed-text-v1.5"
    artifact_filename: str = "nomic_embed_text_qnn.onnx"
    dimension: Optional[int] = None  # Determined dynamically from ONNX metadata
    runtime: str = "QNN"
    device: str = "Snapdragon NPU (Hexagon)"
    backend: str = "QnnHtp.dll"
    performance_mode: str = "burst"
    precision: str = "fp16"


cpu_model_config = CPUModelConfig()
qualcomm_model_config = QualcommModelConfig()
