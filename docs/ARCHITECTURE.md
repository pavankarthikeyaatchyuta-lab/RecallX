# RecallX Architecture

## Overview
RecallX is a privacy-first, local-first visual memory system designed for Windows PCs and optimized for Qualcomm Snapdragon hardware. It periodically or manually captures the active desktop screen, extracts high-fidelity textual evidence through local OCR, generates dense semantic embeddings on-device, and stores both vector index entries and metadata in local storage.

```
+-------------------------------------------------------------+
|                        Windows 11 Screen                    |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     Screen Capture Engine                   |
|   - PIL ImageGrab / mss display grabbing                    |
|   - Active window & process inspection (win32gui / psutil)  |
|   - Privacy filter: Excluded Applications                   |
|   - Resilient simulated canvas fallback for headless runs   |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                  Image Preprocessor & OCR                   |
|   - Resolution scaling & contrast enhancement               |
|   - Windows Native WinRT OCR Engine (Local)                 |
|   - Zero-cloud text extraction & latency profiling          |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     Embedding Provider                      |
|                  (EmbeddingProvider Abstraction)            |
|       +----------------------------+                        |
|       |  QualcommQNNProvider       | (Hexagon NPU)          |
|       |  - ONNX Runtime QNN EP     |                        |
|       |  - Nomic Embed Text ONNX   |                        |
|       +----------------------------+                        |
|                     | (Fallback if not Snapdragon / no QNN) |
|       +----------------------------+                        |
|       |  LocalCPUProvider          | (PyTorch / CPU)        |
|       |  - all-MiniLM-L6-v2        |                        |
|       |  - In-memory vector cache  |                        |
|       +----------------------------+                        |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                   Local Vector Index & SQLite               |
|   - LocalVectorIndex (NumPy Cosine Similarity Matrix)       |
|   - SQLite WAL mode database (recallx.db)                   |
|   - Local image store (data/screenshots/*.png)              |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                   Hybrid Ranking Engine                     |
|   - Semantic Score (Vector Cosine Similarity, w=0.65)       |
|   - Keyword Score (Lexical Overlap & Title Match, w=0.25)   |
|   - Recency Score (Exponential Half-Life Decay, w=0.10)     |
|   - Deterministic Match Explainer (Evidence snippets)       |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                    FastAPI Local Service                    |
|   - REST endpoints (/api/search, /api/capture, /api/status) |
|   - Static file mounts (/data/screenshots, frontend dist)   |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     React + TypeScript UI                   |
|   - Vite, Tailwind CSS, Lucide icons                        |
|   - Ctrl+Shift+Space global quick-focus shortcut            |
|   - Live capture toggle, AI runtime inspection, benchmarks  |
+-------------------------------------------------------------+
```

## Core Subsystems

### 1. Screen Capture Engine (`backend/app/capture/`)
- Intercepts the foreground display frame using native GDI/Win32 or mss.
- Obtains active application name and window title via Win32 API.
- Masks 64-bit PIDs accurately to avoid overflow errors.
- Enforces an application exclusion list before performing any OCR or image saving.

### 2. OCR Engine (`backend/app/ocr/`)
- Utilizes the Windows 10/11 built-in WinRT `Windows.Media.Ocr.OcrEngine` API.
- Fully offline, running on the client machine's native language dictionaries.
- Records exact millisecond latency for each extraction.

### 3. Embedding Provider Abstraction (`backend/app/embeddings/`)
- Defines `EmbeddingProvider` with methods `embed_text()`, `embed_batch()`, `is_available()`, and `get_info()`.
- `QualcommQNNProvider`: Designed specifically for Snapdragon X Elite and Qualcomm NPUs using ONNX Runtime `QNNExecutionProvider` with `QnnHtp.dll` backend.
- `LocalCPUProvider`: High-speed local CPU provider with in-memory caching to prevent duplicate inferences.
- `ModelManager`: Dynamically selects the best available provider, truth-checks hardware, and falls back to CPU if Snapdragon NPU or QNN EP is unavailable.

### 4. Local Vector Index & Storage (`backend/app/search/`, `backend/app/storage/`)
- Normalized 384-dimensional vector arrays with dot product calculation equivalent to cosine similarity.
- Persistent serialization to `data/index/vectors.npz`.
- Metadata stored in SQLite with Write-Ahead Logging (WAL) enabled for concurrency.

### 5. Hybrid Ranker (`backend/app/search/hybrid_ranker.py`)
Combines three distinct signals into an explainable score:
$$\text{Score} = (w_{\text{sem}} \times S_{\text{semantic}}) + (w_{\text{kw}} \times S_{\text{keyword}}) + (w_{\text{rec}} \times S_{\text{recency}})$$
- Semantic weight: 0.65
- Keyword weight: 0.25
- Recency weight: 0.10
- Scores are strictly bounded in $[0.0, 1.0]$.
