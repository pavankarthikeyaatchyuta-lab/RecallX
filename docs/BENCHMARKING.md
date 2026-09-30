# RecallX Benchmarking & Performance Guide

## Overview
RecallX includes a built-in benchmark harness designed to measure real, on-device performance across all stages of the visual memory pipeline.

---

## 1. Running the Benchmark

You can trigger benchmarks either through the **CLI** or via the **UI**:

### Via CLI
```powershell
python scripts/benchmark.py
```

### Via UI
Navigate to the **Benchmarks** tab and click **"Run Live Benchmark"**.

Results are saved to:
```
benchmarks/results.json
```

---

## 2. Measured Metrics

1. **OCR Latency (Avg)**:
   Measures time taken by Windows Native WinRT OCR to preprocess and extract text from 1080p/720p screens.
2. **Embedding Latency (Avg & P95)**:
   Measures time to generate normalized 384-dimensional dense semantic vectors.
3. **Search Latency (Avg)**:
   Measures time to execute candidate vector retrieval across the local cosine index combined with lexical scoring and recency decay.
4. **End-to-End Latency**:
   Total latency representing: `Capture -> Preprocess -> OCR -> Embed -> Store -> Index`.
5. **Process Memory Footprint**:
   Active resident set size (RSS) in megabytes.

---

## 3. Truthful Measurement Policy

RecallX enforces strict scientific reporting:
- Benchmark numbers are **never simulated, hardcoded, or fabricated**.
- If Qualcomm Snapdragon hardware is active, the benchmark records actual QNN HTP latency.
- If running on x86_64 development hardware, the benchmark records host CPU execution and labels it as:
  ```
  Execution Provider: PyTorch / CPU
  Acceleration Status: Qualcomm NPU unavailable — using CPU fallback
  ```
