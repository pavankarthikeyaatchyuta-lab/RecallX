# RecallX — Qualcomm Snapdragon Validation Checklist

**Challenge:** Qualcomm Snapdragon AI Lab Build & Present Challenge 2026  
**Document:** Snapdragon X Elite / Hexagon NPU Validation Guide  
**Target Hardware:** Qualcomm Snapdragon X Elite / Snapdragon X Plus (Windows 11 on ARM64)  
**Execution Provider:** ONNX Runtime QNN Execution Provider (`QNNExecutionProvider`)  

---

## 1. Hardware & System Prerequisites

- [ ] **Physical Host:** Qualcomm Snapdragon X Elite CRD (Compute Reference Device) or commercial Snapdragon AI PC (e.g., Surface Pro 11th Gen, Surface Laptop 7th Gen, Lenovo Yoga Slim 7x, Dell XPS 13 Snapdragon Edition).
- [ ] **Operating System:** Windows 11 on ARM64 (Build 26100+ recommended).
- [ ] **Hexagon NPU Driver:** Qualcomm Hexagon HTP driver installed and updated via Windows Update.
- [ ] **Python Environment:** Python 3.10, 3.11, or 3.12 (ARM64 native build recommended for optimal host CPU orchestration).
- [ ] **Qualcomm AI Engine Direct SDK / QNN SDK:** QNN SDK 2.20+ (included with `onnxruntime-qnn`).

---

## 2. Environment Setup on Snapdragon Hardware

Clone the repository and install dependencies on the Snapdragon machine:

```powershell
# 1. Clone repository
git clone https://github.com/pavankarthikeyaatchyuta-lab/RecallX.git
cd RecallX

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Install Qualcomm QNN Execution Provider for ONNX Runtime (Windows on ARM)
pip install onnxruntime-qnn
```

Verify that `QNNExecutionProvider` is detected by ONNX Runtime:

```powershell
python -c "import onnxruntime as ort; print('Providers:', ort.get_available_providers())"
```
*Expected Output:* `Providers: ['QNNExecutionProvider', 'CPUExecutionProvider']`

---

## 3. Qualcomm AI Hub Model Preparation

The embedding pipeline is designed for **Nomic Embed Text** or **all-MiniLM-L6-v2** exported for the Hexagon HTP backend:

1. **Option A: Export via Qualcomm AI Hub CLI**
   ```bash
   # Install Qualcomm AI Hub client
   pip install qai-hub

   # Compile model for Snapdragon X Elite Hexagon NPU
   qai-hub compile \
     --model nomic_ai/nomic-embed-text-v1.5 \
     --device "Snapdragon X Elite CRD" \
     --target-runtime qnn_lib_direct \
     --output-dir ./export
   ```

2. **Option B: Place Compiled Model in RecallX**
   Move the resulting ONNX model artifact into the `models/` folder:
   ```powershell
   Copy-Item ./export/nomic_embed_text_qnn.onnx ./models/nomic_embed_text_qnn.onnx
   ```

The file structure should be:
```
RecallX/
├── models/
│   └── nomic_embed_text_qnn.onnx
```

---

## 4. Execution Provider Configuration Verification

RecallX automatically configures the QNN Execution Provider in `backend/app/embeddings/providers/qualcomm_provider.py` with peak NPU settings:

```python
qnn_options = {
    "backend_path": "QnnHtp.dll",       # Hexagon Tensor Processor backend library
    "profiling_level": "basic",
    "htp_performance_mode": "burst",    # Peak performance mode for NPU
    "enable_htp_fp16_precision": "1",   # Optimal FP16 throughput on NPU
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

## 5. Live Snapdragon Validation Execution Steps

Execute the following test sequence in PowerShell on the Snapdragon device:

### Step 5.1: Run the Qualcomm NPU Benchmark Harness
```powershell
python scripts/qualcomm_benchmark.py
```
*Expected Result:*
- Detects Snapdragon processor (`Snapdragon X Elite`).
- Initializes `QNNExecutionProvider` with `QnnHtp.dll`.
- Measures warm NPU embedding latency (target: < 5 ms).

### Step 5.2: Run the Comprehensive System Benchmark
```powershell
python scripts/benchmark.py
```
*Expected Result:*
- `Runtime State:` **`QNN_ACTIVE`**
- `Active Provider:` **`Qualcomm Snapdragon QNN Provider`**
- `Acceleration Status:` **`Snapdragon AI acceleration available (QNN NPU Active)`**
- Records results to `benchmarks/results.json`.

### Step 5.3: Verify Zero-Cloud Offline Guarantees
```powershell
python scripts/offline_test.py
```
*Expected Result:*
- 0 outbound socket connections.
- Model executes offline with `HF_HUB_OFFLINE=1`.

### Step 5.4: Run Search Accuracy Evaluation
```powershell
python scripts/evaluate_search.py
```
*Expected Result:*
- Top-1 and Top-3 accuracy evaluated against the 16 synthetic visual memories in under 1 second.

### Step 5.5: Run Unit & Integration Test Suite
```powershell
python -m pytest backend/tests/test_all.py
```
*Expected Result:* All tests pass (`100%`).

---

## 6. Frontend UI Verification on Snapdragon

Start the unified server on the Snapdragon machine:

```powershell
python backend/main.py
```

Open a browser to: `http://127.0.0.1:8000/`

- [ ] **Runtime Page (`/` -> Runtime tab):**
  - Banner displays green badge: **`QNN_ACTIVE • Snapdragon NPU`**
  - Host Processor displays `Snapdragon X Elite (ARM64)`
  - Active Execution Device displays `Snapdragon NPU (Hexagon)`
  - `QNNExecutionProvider (Qualcomm)` displays `Active (Snapdragon HTP)`
- [ ] **Benchmark Page (`/` -> Benchmarks tab):**
  - Displays warm embedding latency, batch indexing speed, and vector retrieval.
  - Zero-fabrication guarantee verified.
- [ ] **Search Page (`/` -> Search tab):**
  - Natural-language query: `"Find the internship application with the September deadline"`
  - Returns top result instantly with screenshot card, OCR text, match snippet, and semantic score.
- [ ] **Privacy Guard (`/` -> Privacy tab):**
  - Cloud request counter is strictly `0`.

---

## 7. Troubleshooting & Graceful Fallback Matrix

| Condition | Observed State | Cause | Remediation |
| :--- | :--- | :--- | :--- |
| Running on Intel/AMD Host | `CPU_FALLBACK` | Non-Snapdragon CPU | Expected behavior during x86 development. Seamless PyTorch CPU provider active. |
| Snapdragon host without model file | `MODEL_UNAVAILABLE` | `models/nomic_embed_text_qnn.onnx` missing | Place exported model in `models/` per Section 3. |
| Snapdragon host without `onnxruntime-qnn` | `CPU_FALLBACK` | ONNX Runtime lacks QNN EP | Run `pip install onnxruntime-qnn`. |
| Driver mismatch or invalid HTP DLL | `QNN_ERROR` | Hexagon driver error | Verify `QnnHtp.dll` in system PATH or Windows System32; update Qualcomm Adreno/Hexagon drivers. |
