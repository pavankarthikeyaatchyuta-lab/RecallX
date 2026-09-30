# RecallX Hackathon Demonstration Guide

This guide describes the ideal 10-step judging demonstration flow for the **Qualcomm Snapdragon AI Lab Challenge**.

---

## Preparation (Pre-Demo)

Ensure the demo dataset is loaded:
```powershell
python scripts/seed_demo.py
```
This populates the local database and vector index with **16 realistic scenarios** (internship applications, AI documentation, expenses, pitch decks, meeting notes, etc.).

---

## 10-Step Judging Walkthrough

### STEP 1: Local Privacy Verification
- Launch RecallX at `http://127.0.0.1:8000/`.
- Show the top badge: `● LOCAL`.
- Show the Privacy metric card: **Cloud Requests: 0**.

### STEP 2: Live Memory Capture
- Click **"Capture Now"** or toggle **"Automatic Capture: ON"**.
- Open a browser window or document.
- Demonstrate that a new memory is created and indexed within milliseconds.

### STEP 3: Natural Language Semantic Query
- In the search bar, type:
  ```
  Find the internship application with the September deadline
  ```
- Press Enter or click Search.

### STEP 4: Instant Retrieval with Explanation
- RecallX retrieves the Google Chrome screenshot: *Qualcomm Careers — AI Software Engineer Internship Application*.
- Highlight:
  - Match confidence percentage (e.g. `94% Match`).
  - Extracted snippet: *"Applications close on September 30."*
  - **Deterministic match explanation**: *"Matched because text in Google Chrome contains keywords 'internship', 'application' with semantic relevance."*

### STEP 5: Technical Documentation Query
- Search:
  ```
  Where did I see the Qualcomm AI Hub documentation?
  ```
- RecallX retrieves the Brave Browser screen showing the ONNX Runtime QNN Execution Provider options.

### STEP 6: Financial Query
- Search:
  ```
  Find the document with the ₹50,000 amount
  ```
- RecallX immediately matches the Microsoft Excel expense report for Qualcomm development hardware.

### STEP 7: Inspect AI Runtime Status
- Click the **"AI Runtime"** tab.
- Review the execution provider detection breakdown:
  - Host processor detected.
  - Active runtime (QNN HTP NPU if on Snapdragon, or CPU fallback).
  - Truthful status reporting without fake claims.

### STEP 8: Live Performance Benchmarks
- Click the **"Benchmarks"** tab.
- Click **"Run Live Benchmark"**.
- Observe live latency measurements across OCR, Embedding, and Search (sub-5ms vector search).

### STEP 9: Offline Mode Validation
- Disconnect internet connectivity (turn off Wi-Fi).
- Search:
  ```
  Show me what I was looking at regarding Snapdragon NPU
  ```
- RecallX returns the result instantly with **0 cloud dependencies**.
- Or run `python scripts/offline_test.py` to show socket-level verification.

### STEP 10: Complete User Data Sovereignty
- Navigate to **"Privacy & Settings"**.
- View the **Excluded Applications** list (banking, password managers).
- Click **"Delete All Memories"** and confirm to show instant local purge.
