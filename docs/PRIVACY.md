# RecallX Privacy Specification

## Core Product Promise
> **"Your screen history stays on your device."**

RecallX core processing does not require external network services. Privacy is not an add-on feature in RecallX; it is the fundamental architectural constraint of the entire system.

---

## 1. Zero-Cloud Guarantees

| Property | RecallX Architecture | Traditional Cloud AI Tools |
| :--- | :--- | :--- |
| **Screenshot Processing** | 100% on-device (RAM/Local disk) | Uploaded to remote servers |
| **OCR Extraction** | Windows Native WinRT / Local ONNX | Remote Cloud Vision APIs |
| **Embedding Generation** | Local Snapdragon NPU / Local CPU | Remote OpenAI/Cohere APIs |
| **Vector Storage** | Local SQLite + NumPy array files | Pinecone / Weaviate Cloud |
| **Telemetry & Tracking** | **0 outbound packets** | Continuous user analytics |
| **User Account** | None required | Mandatory sign-in |

---

## 2. Sensitive Application Exclusions

RecallX features an active application barrier that intercepts screen capture before any image saving or OCR extraction takes place:

### Default Excluded Apps
- Password managers (`Keepass`, `1Password`, `Bitwarden`, `LastPass`)
- Financial applications (`Banking`, `Payment`, `Wallet`)
- Private browser windows (`Incognito`, `Private Browsing`, `InPrivate`)

Users can add or remove applications in real-time from the **Privacy & Settings** interface.

---

## 3. Data Deletion & Retention

RecallX provides complete data sovereignty to the user:

1. **Individual Memory Deletion**:
   - Deletes the screenshot file (`data/screenshots/<id>.png`).
   - Removes the record from the SQLite database.
   - Evicts the vector row from `data/index/vectors.npz`.

2. **Total Vault Erasure ("Clear All")**:
   - Atomically truncates the SQLite `memories` table.
   - Removes all `.png` files in the screenshots directory.
   - Clears and unlinks the vector index file.

---

## 4. Verification

To verify that RecallX performs zero external network calls:
```powershell
python scripts/offline_test.py
```
This test monkey-patches socket connections and asserts that `cloud_requests == 0` while executing screen capture, OCR, embedding, and hybrid search.
