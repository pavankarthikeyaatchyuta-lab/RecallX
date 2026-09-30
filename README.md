# RecallX

> **"Your PC remembers, so you don't have to."**
>
> *Privacy-first, local-first visual memory application for Windows PCs and Qualcomm Snapdragon NPUs.*

---

## 1. Problem
Modern knowledge workers navigate hundreds of tabs, documents, spreadsheets, meeting transcripts, and chat messages daily. Crucial details—deadlines, code snippets, financial figures, research papers, and login credentials—are lost in time. Existing cloud-based recall solutions compromise user trust by uploading sensitive screens to remote third-party AI clouds.

## 2. Solution
**RecallX** captures desktop screens locally, extracts textual context using Windows native OCR, computes dense semantic embeddings on-device, and stores everything in a local SQLite database. Users query past activity using natural-language queries (e.g. *"Find the internship application with the September deadline"*), retrieving the exact screenshot, context snippet, and deterministic match explanations in milliseconds.

## 3. Why RecallX
- **Zero Cloud Requests**: Never uploads a single byte or screenshot to any cloud.
- **Snapdragon NPU Optimized**: Architected for Qualcomm Snapdragon X Elite Hexagon NPUs via ONNX Runtime QNN Execution Provider.
- **Truth in Hardware**: Honest hardware profiling; never fakes NPU execution or benchmark numbers.
- **Deterministic Explanations**: Grounds search results in retrieved textual evidence without hallucinating LLMs.
- **Sub-5ms Vector Search**: Ultra-fast local cosine similarity matrix.

---

## 4. Key Features
1. **Manual & Periodic Screen Capture**: One-click capture or user-controlled periodic background capture (default 30s) with active ON/OFF toggle.
2. **Offline Local OCR**: Native Windows 11 WinRT OCR engine with zero internet requirements.
3. **Hybrid Semantic Search**: Combines semantic embedding similarity (0.65), keyword overlap (0.25), and recency decay (0.10).
4. **Deterministic Match Explanations**: Highlights matching words and evidence snippets explaining why each card matched.
5. **Snapdragon AI Hub Abstraction**: Pluggable `EmbeddingProvider` supporting Qualcomm QNN HTP backend and CPU fallback.
6. **Privacy Shield**: Real-time exclusion list protecting password managers, banking apps, and incognito sessions.
7. **Complete Data Sovereignty**: One-click individual memory deletion and permanent data vault purge.
8. **Built-in Benchmark Suite**: Real latency profiling across OCR, Embedding, Search, and E2E pipelines exported to JSON.

---

## 5. Architecture
```
Windows Screen -> Capture Engine -> Windows Native OCR -> Text & Metadata
                                                               |
                                                               v
                                                      EmbeddingProvider
                                                    (Qualcomm QNN / CPU)
                                                               |
                                                               v
                                                    Local Vector Index (NPZ)
                                                               +
                                                    SQLite Metadata (WAL)
                                                               |
                                                               v
                                                      Hybrid Search Engine
                                                               |
                                                               v
                                                    FastAPI REST Service
                                                               |
                                                               v
                                                    React + Tailwind UI
```

---

## 6. Privacy Architecture
- **Local Storage Only**: Screenshots stored in `data/screenshots/`, vectors in `data/index/`, metadata in `data/recallx.db`.
- **Zero Outbound Telemetry**: 0 analytics, 0 network dependencies, 0 cloud storage.
- **Application Exclusion**: Capture engine rejects sensitive processes (e.g. 1Password, Bitwarden, Banking) before saving images.
- **Verifiable Offline Mode**: Verified via `python scripts/offline_test.py` with socket-level enforcement.

---

## 7. Qualcomm Snapdragon Optimization & AI Hub
- **Target Platform**: Windows 11 on ARM64 (Snapdragon X Elite / Snapdragon X Plus).
- **Runtime**: ONNX Runtime with `QNNExecutionProvider`.
- **Backend**: `QnnHtp.dll` (Hexagon Tensor Processor).
- **Model**: Nomic Embed Text / MiniLM exported from Qualcomm AI Hub.
- **Truthful Status**: On non-Snapdragon development machines, RecallX clearly reports:
  `Qualcomm NPU unavailable — using CPU fallback.`

---

## 8. Installation

### Prerequisites
- Windows 11 (x86_64 or ARM64 / Snapdragon)
- Python 3.11+
- Node.js 18+ and npm

### Clone and Setup
```powershell
# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies and build SPA
cd frontend
npm install
npm run build
cd ..
```

---

## 9. Running Locally

### Start Application (Single Command)
Run the backend server, which automatically serves the production frontend at `http://127.0.0.1:8000/`:
```powershell
python backend/main.py
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

### Development Mode (Optional)
If developing frontend components with hot reload:
```powershell
# Terminal 1: Backend
python backend/main.py

# Terminal 2: Frontend dev server
cd frontend
npm run dev
```

---

## 10. Demo Dataset (Hackathon Mode)
To seed 16 realistic demo scenarios covering internship applications, AI documentation, hackathon guidelines, research papers, financial reports, and meeting notes:
```powershell
python scripts/seed_demo.py
```

---

## 11. Benchmarking & Evaluation
Run live on-device benchmarks and retrieval quality evaluations:
```powershell
# Measure granular latency (cold start, warm query, batch, vector retrieval)
python scripts/benchmark.py

# Evaluate Top-1 and Top-3 search accuracy over synthetic memory set
python scripts/evaluate_search.py

# Run Qualcomm Snapdragon QNN benchmark harness (or check hardware readiness)
python scripts/qualcomm_benchmark.py
```
Benchmark numbers are stored in `benchmarks/results.json`.

---

## 12. Automated Testing
Run automated unit, integration, and offline privacy tests:
```powershell
# Run Pytest suite (9 unit & integration tests)
python -m pytest backend/tests/test_all.py

# Run End-to-End Smoke Test
python scripts/smoke_test.py

# Run Socket-Level Offline Mode Verification (0 outbound packets)
python scripts/offline_test.py
```

---

## 13. Documentation Suite
Detailed technical documentation and submission materials:
- [**Final Development Report**](docs/FINAL_DEVELOPMENT_REPORT.md): System architecture, tradeoffs, performance profile, and design rationale.
- [**Final Pre-Submission Audit**](docs/FINAL_AUDIT.md): Comprehensive claim-by-claim verification, latency disaggregation, and evaluation results.
- [**Qualcomm Validation Checklist**](docs/QUALCOMM_VALIDATION_CHECKLIST.md): Step-by-step procedures for deploying and testing on Snapdragon X Elite hardware.
- [**Architecture Guide**](docs/ARCHITECTURE.md): Complete backend and frontend data flow diagrams.
- [**Privacy Architecture**](docs/PRIVACY.md): Local-only guarantees and zero-telemetry enforcement.
- [**Qualcomm AI Hub Setup**](docs/QUALCOMM_SETUP.md): Exporting models from Qualcomm AI Hub for Hexagon NPU.

---

## 14. Project Structure
```
recallx/
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # FastAPI endpoints
│   │   ├── capture/               # Screen grabber & window detector
│   │   ├── core/                  # Config & truthful hardware detection
│   │   ├── embeddings/            # Qualcomm QNN & CPU providers
│   │   ├── ocr/                   # Windows Native WinRT OCR engine
│   │   ├── search/                # Vector index & hybrid ranker
│   │   ├── services/              # Memory, capture & benchmark services
│   │   └── storage/               # SQLite database & file store
│   ├── tests/test_all.py          # Automated pytest suite
│   ├── requirements.txt
│   └── main.py                    # Entry point & static SPA server
│
├── frontend/
│   ├── src/                       # React 19, TypeScript, Tailwind components
│   ├── dist/                      # Pre-built SPA assets served by FastAPI
│   ├── package.json
│   └── vite.config.ts
│
├── data/
│   ├── screenshots/               # Stored screenshot images
│   ├── index/                     # Serialized vector embeddings
│   ├── demo/                      # Demo artifacts
│   └── recallx.db                 # SQLite database
│
├── benchmarks/results.json        # Real benchmark measurements
├── scripts/
│   ├── benchmark.py               # Granular latency profiler
│   ├── evaluate_search.py         # Top-1 & Top-3 retrieval evaluator
│   ├── qualcomm_benchmark.py      # Snapdragon NPU benchmark harness
│   ├── seed_demo.py               # Demo memory generator (16 scenarios)
│   ├── offline_test.py            # Zero-cloud verification
│   └── smoke_test.py              # End-to-end pipeline tester
│
├── docs/                          # Comprehensive technical docs
└── README.md
```

---

## 14. Limitations & Future Roadmap
- **Multi-Monitor**: Currently captures the active primary screen; multi-display coordinate mapping planned for v1.1.
- **Audio Memory**: Transcription of system audio / meetings via local Whisper ONNX QNN pipeline.
- **Tauri Windows App Packaging**: Bundle frontend into a native `.exe` installer.

---

## 15. License
MIT License. Built for the Qualcomm Snapdragon AI Lab Build & Present Challenge 2026.
