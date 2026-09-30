import os
import platform
from pathlib import Path
from typing import Any, Optional
import numpy as np

from backend.app.core.config import MODELS_DIR
from backend.app.embeddings.config import qualcomm_model_config
from backend.app.embeddings.providers.base import EmbeddingProvider


class NomicModelAdapter:
    """
    Adapter for Qualcomm AI Hub Nomic Embed Text models.
    Dynamically inspects ONNX model metadata (inputs, shapes, types, outputs)
    and executes tokenization, tensor packing, mean pooling, and L2 normalization.
    """

    def __init__(self, session: Any, tokenizer_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        self.session = session
        self.tokenizer_name = tokenizer_name
        self._tokenizer = None
        self.input_metadata = {}
        self.output_metadata = {}
        self.detected_dimension: Optional[int] = None
        self._inspect_model()

    def _inspect_model(self) -> None:
        """Dynamically inspects inputs and outputs without hardcoded tensor assumptions."""
        try:
            for inp in self.session.get_inputs():
                self.input_metadata[inp.name] = {
                    "shape": inp.shape,
                    "type": inp.type,
                }

            for out in self.session.get_outputs():
                self.output_metadata[out.name] = {
                    "shape": out.shape,
                    "type": out.type,
                }
                # Determine embedding dimension from output tensor shape if available
                if out.shape and len(out.shape) > 1:
                    last_dim = out.shape[-1]
                    if isinstance(last_dim, int):
                        self.detected_dimension = last_dim
        except Exception:
            pass

    def get_tokenizer(self):
        if self._tokenizer is None:
            from transformers import AutoTokenizer
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.tokenizer_name,
                    local_files_only=True,
                )
            except Exception:
                self._tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        return self._tokenizer

    def preprocess(self, texts: list[str]) -> dict[str, np.ndarray]:
        """Prepares input tensors matching the dynamically discovered ONNX input names."""
        tokenizer = self.get_tokenizer()
        encoded = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )

        session_inputs = {}
        input_names = set(self.input_metadata.keys())

        if "input_ids" in input_names:
            expected_type = self.input_metadata["input_ids"]["type"]
            dtype = np.int32 if "int32" in expected_type else np.int64
            session_inputs["input_ids"] = encoded["input_ids"].astype(dtype)

        if "attention_mask" in input_names:
            expected_type = self.input_metadata["attention_mask"]["type"]
            dtype = np.int32 if "int32" in expected_type else np.int64
            session_inputs["attention_mask"] = encoded["attention_mask"].astype(dtype)

        if "token_type_ids" in input_names:
            expected_type = self.input_metadata["token_type_ids"]["type"]
            dtype = np.int32 if "int32" in expected_type else np.int64
            if "token_type_ids" in encoded:
                session_inputs["token_type_ids"] = encoded["token_type_ids"].astype(dtype)
            else:
                session_inputs["token_type_ids"] = np.zeros_like(encoded["input_ids"], dtype=dtype)

        return session_inputs, encoded.get("attention_mask")

    def postprocess(self, raw_outputs: list[np.ndarray], attention_mask: Optional[np.ndarray]) -> list[list[float]]:
        """Applies pooling (if 3D) and exact L2 normalization."""
        raw_embeddings = raw_outputs[0]

        # Apply mean pooling if sequence dimension is preserved: (batch, seq, dim)
        if len(raw_embeddings.shape) == 3 and attention_mask is not None:
            mask = attention_mask[:, :, np.newaxis]
            sum_embeddings = np.sum(raw_embeddings * mask, axis=1)
            sum_mask = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
            sentence_embeddings = sum_embeddings / sum_mask
        else:
            sentence_embeddings = raw_embeddings

        if self.detected_dimension is None and len(sentence_embeddings.shape) > 1:
            self.detected_dimension = int(sentence_embeddings.shape[-1])

        # L2 Normalize embeddings to unit vectors for exact cosine similarity
        norms = np.linalg.norm(sentence_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = sentence_embeddings / norms
        return normalized.astype(np.float32).tolist()


class QualcommQNNEmbeddingProvider(EmbeddingProvider):
    """
    Qualcomm Snapdragon / QNN Execution Provider for ONNX Runtime.
    Designed for Qualcomm AI Hub models (e.g. Nomic Embed Text v1.5).
    Targets Snapdragon Hexagon NPU via QNN HTP (Hexagon Tensor Processor) backend.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_name = qualcomm_model_config.model_id
        self.model_path = model_path or (MODELS_DIR / qualcomm_model_config.artifact_filename)
        self._detected_dim: Optional[int] = None
        self._session = None
        self._adapter: Optional[NomicModelAdapter] = None
        self._last_error: Optional[str] = None

        # Lifecycle state flags
        self.hardware_detected: bool = False
        self.qnn_ep_available: bool = False
        self.model_available: bool = False
        self.session_initialized: bool = False
        self.inference_verified: bool = False

        self._check_environment()

    def _check_environment(self) -> None:
        """Inspects host hardware and ONNX execution providers truthfully."""
        available_providers: list[str] = []
        try:
            import onnxruntime as ort
            available_providers = ort.get_available_providers()
        except Exception:
            available_providers = []

        self.qnn_ep_available = "QNNExecutionProvider" in available_providers

        # Verify host platform architecture truthfully
        proc = (platform.processor() or "").lower()
        machine = platform.machine().lower()
        self.hardware_detected = (
            "snapdragon" in proc
            or "qualcomm" in proc
            or "qcom" in proc
            or ("arm64" in machine and ("snapdragon" in proc or "qualcomm" in proc))
        )

        self.model_available = self.model_path.exists()

    @property
    def name(self) -> str:
        return "Qualcomm Snapdragon QNN Provider"

    @property
    def runtime(self) -> str:
        return qualcomm_model_config.runtime

    @property
    def device(self) -> str:
        return qualcomm_model_config.device

    @property
    def dimension(self) -> int:
        """Determined dynamically from the model artifact; never hardcoded."""
        return self._detected_dim if self._detected_dim is not None else 0

    def is_available(self) -> bool:
        """
        Truthful check: True ONLY if QNN Execution Provider is registered,
        host is a physical Snapdragon processor, and model artifact exists.
        """
        return self.hardware_detected and self.qnn_ep_available and self.model_available

    def get_runtime_state(self) -> str:
        """
        Calculates exact runtime state matching the RecallX state machine:
        - QNN_ACTIVE: Real inference was successfully executed through QNN on Snapdragon NPU
        - QNN_SESSION_READY: QNN InferenceSession initialized, awaiting inference
        - QNN_AVAILABLE: Snapdragon hardware & QNN EP present, model artifact found
        - MODEL_UNAVAILABLE: Snapdragon detected but model file missing
        - QNN_ERROR: Encountered error during QNN initialization/run
        - CPU_FALLBACK: Host is Intel/AMD or QNN missing
        """
        if self._last_error:
            return "QNN_ERROR"

        if not self.hardware_detected or not self.qnn_ep_available:
            return "CPU_FALLBACK"

        if not self.model_available:
            return "MODEL_UNAVAILABLE"

        if self.inference_verified:
            return "QNN_ACTIVE"

        if self.session_initialized:
            return "QNN_SESSION_READY"

        return "QNN_AVAILABLE"

    def get_unavailability_reason(self) -> str:
        if self._last_error:
            return f"QNN Runtime Error: {self._last_error}"
        if not self.hardware_detected and not self.qnn_ep_available:
            return "Host processor is Intel/AMD (x86_64) and QNNExecutionProvider is not present in ONNX Runtime."
        if not self.hardware_detected:
            return "Current host is an Intel/AMD development machine. Snapdragon NPU requires Snapdragon X Elite/Plus hardware."
        if not self.qnn_ep_available:
            return "QNNExecutionProvider is not registered in ONNX Runtime. Install onnxruntime-qnn for Windows on ARM."
        if not self.model_available:
            return f"Model artifact not found at {self.model_path}. Follow docs/QUALCOMM_SETUP.md to export model from Qualcomm AI Hub."
        return "Ready for Snapdragon NPU acceleration."

    def init_session(self) -> None:
        """Initializes ONNX Runtime session with QNNExecutionProvider."""
        if not (self.hardware_detected and self.qnn_ep_available):
            raise RuntimeError(f"Qualcomm QNN is unavailable on this host: {self.get_unavailability_reason()}")

        if not self.model_path.exists():
            self.model_available = False
            raise FileNotFoundError(f"Model file missing: {self.model_path}")

        import onnxruntime as ort

        # QNN Execution Provider configuration for Qualcomm Hexagon HTP
        qnn_options = {
            "backend_path": qualcomm_model_config.backend,
            "profiling_level": "basic",
            "htp_performance_mode": qualcomm_model_config.performance_mode,
            "enable_htp_fp16_precision": "1" if qualcomm_model_config.precision == "fp16" else "0",
        }

        try:
            self._session = ort.InferenceSession(
                str(self.model_path),
                providers=[
                    ("QNNExecutionProvider", qnn_options),
                    "CPUExecutionProvider",
                ],
            )
            self._adapter = NomicModelAdapter(self._session, tokenizer_name=self.model_name)
            if self._adapter.detected_dimension is not None:
                self._detected_dim = self._adapter.detected_dimension
            self.session_initialized = True
        except Exception as e:
            self._last_error = str(e)
            self.session_initialized = False
            raise RuntimeError(f"Failed to initialize QNN Execution Provider session: {e}")

    def embed_text(self, text: str) -> list[float]:
        res = self.embed_batch([text])
        return res[0] if res else [0.0] * self.dimension

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.is_available():
            raise RuntimeError(
                f"Cannot execute on Qualcomm NPU: {self.get_unavailability_reason()}. Use CPU fallback."
            )

        if not self.session_initialized or self._session is None or self._adapter is None:
            self.init_session()

        try:
            session_inputs, attention_mask = self._adapter.preprocess(texts)
            raw_outputs = self._session.run(None, session_inputs)
            embeddings = self._adapter.postprocess(raw_outputs, attention_mask)
            self.inference_verified = True
            if self._adapter.detected_dimension is not None:
                self._detected_dim = self._adapter.detected_dimension
            return embeddings
        except Exception as e:
            self._last_error = str(e)
            raise RuntimeError(f"Qualcomm QNN inference error: {e}")

    def get_model_metadata(self) -> dict[str, Any]:
        """Exposes dynamic ONNX model metadata."""
        if self._adapter:
            return {
                "inputs": self._adapter.input_metadata,
                "outputs": self._adapter.output_metadata,
                "detected_dimension": self._detected_dim,
            }
        return {
            "inputs": {},
            "outputs": {},
            "detected_dimension": self._detected_dim,
        }

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
            "qnn_provider_present": self.qnn_ep_available,
            "snapdragon_detected": self.hardware_detected,
            "model_path": str(self.model_path),
            "model_exists": self.model_available,
            "session_initialized": self.session_initialized,
            "inference_verified": self.inference_verified,
            "model_metadata": self.get_model_metadata(),
            "last_error": self._last_error,
            "reason": self.get_unavailability_reason(),
        }


# Aliases for backward compatibility
QualcommQNNProvider = QualcommQNNEmbeddingProvider
