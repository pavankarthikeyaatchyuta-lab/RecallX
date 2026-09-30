# Qualcomm Snapdragon & AI Hub Integration Guide

RecallX is developed for the **Qualcomm Snapdragon AI Lab Build & Present Challenge**. It is architected to utilize the Qualcomm Hexagon NPU on Snapdragon-powered Windows 11 PCs (such as Snapdragon X Elite and Snapdragon X Plus).

---

## 1. Qualcomm AI Architecture Overview

RecallX isolates hardware-dependent embedding inference behind the `EmbeddingProvider` interface:

```
EmbeddingProvider (Abstract Base Class)
  ├── QualcommQNNProvider (Snapdragon Hexagon NPU via QNN Execution Provider)
  └── LocalCPUProvider (Host CPU Fallback via PyTorch / ONNX)
```

When deployed on a Snapdragon Windows 11 device, the pipeline targets the **QNN Execution Provider (QNN EP)** in ONNX Runtime, which routes computation directly to the **Hexagon Tensor Processor (HTP)**.

---

## 2. Prerequisites for Snapdragon NPU Acceleration

To run with full hardware NPU acceleration on a Snapdragon PC:

1. **Hardware**: Qualcomm Snapdragon X Elite, Snapdragon X Plus, or Snapdragon Compute Platform device running Windows 11 on ARM64.
2. **QNN SDK**: Qualcomm Neural Processing SDK / QNN binaries installed (`QnnHtp.dll`, `libQnnHtp.so`).
3. **ONNX Runtime QNN Package**:
   ```powershell
   pip install onnxruntime-qnn
   ```
4. **Compiled Model**: Exported ONNX model optimized for Hexagon HTP from Qualcomm AI Hub.

---

## 3. Exporting Models from Qualcomm AI Hub

Qualcomm AI Hub provides pre-optimized models compiled specifically for Snapdragon NPUs.

### Step 1: Install Qualcomm AI Hub Client
```bash
pip install qai-hub
qai-hub configure --api_token <YOUR_QUALCOMM_AI_HUB_TOKEN>
```

### Step 2: Compile Nomic Embed Text for Snapdragon X Elite
```bash
# Compile for Snapdragon X Elite CRD target with QNN runtime
qai-hub compile \
  --model "nomic-ai/nomic-embed-text-v1.5" \
  --device "Snapdragon X Elite CRD" \
  --target-runtime qnn_lib_direct \
  --output-dir models/qnn_export
```

### Step 3: Place the Artifact in RecallX
Copy the compiled model into the RecallX models directory:
```powershell
Copy-Item models/qnn_export/model.onnx models/nomic_embed_text_qnn.onnx
```

---

## 4. QNN Session Options in RecallX

RecallX configures the ONNX Runtime session in `backend/app/embeddings/providers/qualcomm_provider.py` as follows:

```python
import onnxruntime as ort

qnn_options = {
    "backend_path": "QnnHtp.dll",       # Hexagon Tensor Processor backend
    "profiling_level": "basic",
    "htp_performance_mode": "burst",    # Maximum NPU throughput
    "enable_htp_fp16_precision": "1",   # Optimal FP16 inference on NPU
}

session = ort.InferenceSession(
    "models/nomic_embed_text_qnn.onnx",
    providers=[
        ("QNNExecutionProvider", qnn_options),
        "CPUExecutionProvider",
    ],
)
```

---

## 5. Truthful Hardware Detection & Fallback Policy

RecallX enforces a strict **Truth in Hardware** standard:
- It **never claims NPU acceleration** unless `is_snapdragon` is verified on the host and `QNNExecutionProvider` is active in `ort.get_available_providers()`.
- On non-Snapdragon development machines (e.g., Intel/AMD x86_64), RecallX displays:
  ```
  Development mode: Qualcomm NPU unavailable — using CPU fallback
  ```
- The application **never crashes** if Qualcomm hardware or QNN libraries are not present; the `ModelManager` seamlessly routes inference through `LocalCPUProvider`.
