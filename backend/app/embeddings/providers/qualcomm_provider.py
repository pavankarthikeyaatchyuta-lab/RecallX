import os
import platform
from pathlib import Path
from typing import Any
import numpy as np

from backend.app.core.config import MODELS_DIR
from backend.app.embeddings.providers.base import EmbeddingProvider


class QualcommQNNProvider(EmbeddingProvider):
    """
    Qualcomm Snapdragon / QNN Execution Provider for ONNX Runtime.
    Designed for Qualcomm AI Hub exported models (e.g. Nomic Embed Text / MiniLM ONNX).
    Targets Snapdragon NPU via QNN HTP (Hexagon Tensor Processor) backend.
    """

    def __init__(self, model_path: Path | None = None):
        self.model_name = "Nomic Embed Text (Qualcomm AI Hub / ONNX)"
        self.model_path = model_path or (MODELS_DIR / "nomic_embed_text_qnn.onnx")
        self._dim = 384
        self._session = None
        self._tokenizer = None
        self._last_error: str | None = None
        self._check_availability()

    def _check_availability(self) -> None:
        self._available_providers: list[str] = []
        try:
            import onnxruntime as ort
            self._available_providers = ort.get_available_providers()
        except Exception:
            self._available_providers = []

        self._has_qnn = "QNNExecutionProvider" in self._available_providers

        # Verify host platform architecture truthfully
        proc = (platform.processor() or "").lower()
        machine = platform.machine().lower()
        self._is_snapdragon_device = (
            "snapdragon" in proc
            or "qualcomm" in proc
            or "qcom" in proc
            or ("arm64" in machine and ("snapdragon" in proc or "qualcomm" in proc))
        )

    @property
    def name(self) -> str:
        return "Qualcomm Snapdragon QNN Provider"

    @property
    def runtime(self) -> str:
        return "Qualcomm QNN"

    @property
    def device(self) -> str:
        return "Snapdragon NPU (Hexagon)"

    @property
    def dimension(self) -> int:
        return self._dim

    def is_available(self) -> bool:
        """
        Truthful check: True ONLY if QNNExecutionProvider is physically available,
        host is a Snapdragon processor, and model file exists.
        """
        return self._has_qnn and self._is_snapdragon_device and self.model_path.exists()

    def get_runtime_state(self) -> str:
        """
        Calculates exact runtime state matching the RecallX state machine:
        - QNN_ACTIVE: Running with QNN on Snapdragon NPU
        - QNN_AVAILABLE: Hardware & EP ready, session standby
        - QNN_ERROR: Encountered error during QNN initialization/run
        - MODEL_UNAVAILABLE: Model file missing
        - CPU_FALLBACK: Host is Intel/AMD or QNN missing
        """
        if self._last_error:
            return "QNN_ERROR"

        if not self._is_snapdragon_device or not self._has_qnn:
            return "CPU_FALLBACK"

        if not self.model_path.exists():
            return "MODEL_UNAVAILABLE"

        if self._session is not None:
            return "QNN_ACTIVE"

        return "QNN_AVAILABLE"

    def get_unavailability_reason(self) -> str:
        if self._last_error:
            return f"QNN Runtime Error: {self._last_error}"
        if not self._is_snapdragon_device and not self._has_qnn:
            return "Host processor is Intel/AMD (x86_64) and QNNExecutionProvider is not present in ONNX Runtime."
        if not self._is_snapdragon_device:
            return "Current host is an Intel/AMD development machine. Snapdragon NPU requires Snapdragon X Elite/Plus hardware."
        if not self._has_qnn:
            return "QNNExecutionProvider is not registered in ONNX Runtime. Install onnxruntime-qnn for Windows on ARM."
        if not self.model_path.exists():
            return f"Model file not found at {self.model_path}. Follow docs/QUALCOMM_SETUP.md to export model from Qualcomm AI Hub."
        return "Ready for Snapdragon NPU acceleration."

    def _get_tokenizer(self):
        if self._tokenizer is None:
            try:
                from transformers import AutoTokenizer
                self._tokenizer = AutoTokenizer.from_pretrained(
                    "sentence-transformers/all-MiniLM-L6-v2",
                    local_files_only=True,
                )
            except Exception:
                try:
                    from transformers import AutoTokenizer
                    self._tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
                except Exception as e:
                    self._last_error = f"Failed to initialize tokenizer: {e}"
                    raise
        return self._tokenizer

    def _init_session(self):
        if not (self._has_qnn and self._is_snapdragon_device):
            raise RuntimeError(f"Qualcomm QNN is unavailable on this host: {self.get_unavailability_reason()}")

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file missing: {self.model_path}")

        import onnxruntime as ort

        # QNN Execution Provider configuration for Qualcomm Hexagon HTP
        qnn_options = {
            "backend_path": "QnnHtp.dll",       # Hexagon Tensor Processor backend library
            "profiling_level": "basic",
            "htp_performance_mode": "burst",    # Peak performance mode
            "enable_htp_fp16_precision": "1",   # Optimal FP16 throughput on NPU
        }

        try:
            self._session = ort.InferenceSession(
                str(self.model_path),
                providers=[
                    ("QNNExecutionProvider", qnn_options),
                    "CPUExecutionProvider",
                ],
            )
            # Detect output dimension dynamically from model
            outputs = self._session.get_outputs()
            if outputs and len(outputs[0].shape) > 1:
                self._dim = int(outputs[0].shape[-1])
        except Exception as e:
            self._last_error = str(e)
            raise RuntimeError(f"Failed to initialize QNN Execution Provider session: {e}")

    def embed_text(self, text: str) -> list[float]:
        res = self.embed_batch([text])
        return res[0] if res else [0.0] * self._dim

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self._is_snapdragon_device or not self._has_qnn:
            raise RuntimeError(
                f"Cannot execute on Qualcomm NPU: {self.get_unavailability_reason()}. Use CPU fallback."
            )

        if self._session is None:
            self._init_session()

        tokenizer = self._get_tokenizer()
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )

        session_inputs = {}
        model_input_names = [inp.name for inp in self._session.get_inputs()]

        if "input_ids" in model_input_names:
            session_inputs["input_ids"] = inputs["input_ids"].astype(np.int64)
        if "attention_mask" in model_input_names:
            session_inputs["attention_mask"] = inputs["attention_mask"].astype(np.int64)
        if "token_type_ids" in model_input_names:
            if "token_type_ids" in inputs:
                session_inputs["token_type_ids"] = inputs["token_type_ids"].astype(np.int64)
            else:
                session_inputs["token_type_ids"] = np.zeros_like(inputs["input_ids"], dtype=np.int64)

        # Run inference through ONNX Runtime QNN Execution Provider
        outputs = self._session.run(None, session_inputs)
        raw_embeddings = outputs[0]

        # Apply mean pooling if output has sequence dimension (batch, seq, dim)
        if len(raw_embeddings.shape) == 3:
            mask = inputs["attention_mask"][:, :, np.newaxis]
            sum_embeddings = np.sum(raw_embeddings * mask, axis=1)
            sum_mask = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
            sentence_embeddings = sum_embeddings / sum_mask
        else:
            sentence_embeddings = raw_embeddings

        # L2 Normalize embeddings to unit vectors for exact cosine similarity
        norms = np.linalg.norm(sentence_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = sentence_embeddings / norms

        return normalized.astype(np.float32).tolist()

    def get_info(self) -> dict[str, Any]:
        state = self.get_runtime_state()
        return {
            "name": self.name,
            "model": self.model_name,
            "runtime": self.runtime,
            "device": self.device,
            "dimension": self.dimension,
            "runtime_state": state,
            "is_available": self.is_available(),
            "is_active": state == "QNN_ACTIVE",
            "qnn_provider_present": self._has_qnn,
            "snapdragon_detected": self._is_snapdragon_device,
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists(),
            "last_error": self._last_error,
            "reason": self.get_unavailability_reason(),
        }


# Aliases for Phase 5 specification
QualcommQNNEmbeddingProvider = QualcommQNNProvider
