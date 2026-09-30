import socket
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from backend.app.core.hardware import detect_hardware
from backend.app.embeddings.manager import model_manager
from backend.app.models.schemas import SearchRequest
from backend.app.ocr.engine import ocr_engine
from backend.app.search.engine import search_engine
from backend.app.services.memory_service import memory_service
from backend.app.storage.database import init_db

# Intercept socket calls to verify strict offline execution
_original_connect = socket.socket.connect
_network_calls_attempted = []


def _blocked_connect(self, address):
    # Allow local connections (127.0.0.1 / localhost)
    host = address[0] if isinstance(address, tuple) else address
    if host in ("127.0.0.1", "localhost", "::1"):
        return _original_connect(self, address)
    _network_calls_attempted.append(address)
    raise socket.error(f"Network call to {address} blocked by RecallX Offline Enforcement Test.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n" + "=" * 60)
    print("RecallX Strict Offline Mode Verification")
    print("=" * 60)
    print("Enforcing zero-external-network barrier via socket interception...\n")

    socket.socket.connect = _blocked_connect

    try:
        print("[1/5] Checking hardware & cloud request counters...")
        hw = detect_hardware()
        assert hw.cloud_requests == 0, "Cloud requests must be strictly 0"
        print(f"      [OK] Host: {hw.processor} | Cloud Requests: {hw.cloud_requests}")

        print("[2/5] Testing local OCR in offline mode...")
        test_img = Image.new("RGB", (600, 150), color=(255, 255, 255))
        d = ImageDraw.Draw(test_img)
        d.text((20, 40), "Offline Memory: Final Submission September 30", fill=(0, 0, 0))
        text, ocr_lat = ocr_engine.extract_text(test_img)
        print(f"      [OK] OCR completed in {ocr_lat} ms (No external network used)")

        print("[3/5] Testing local dense embedding generation in offline mode...")
        query = "Final submission deadline"
        vec, emb_lat = model_manager.embed_text(query)
        assert len(vec) == 384, f"Expected 384 dimensions, got {len(vec)}"
        print(f"      [OK] Local Embedding (384-dim) computed in {emb_lat} ms")

        print("[4/5] Testing local indexing & SQLite persistence in offline mode...")
        mem = memory_service.create_memory(
            screenshot_path="/data/screenshots/offline_test.png",
            extracted_text="Offline Memory: Final Submission September 30",
            application_name="Offline App",
            window_title="Offline Task Window",
            ocr_latency_ms=ocr_lat,
            is_demo=False,
            custom_id="mem_offline_test",
        )
        print(f"      [OK] Memory indexed into SQLite and Vector Index: ID {mem.id}")

        print("[5/5] Testing hybrid vector search in offline mode...")
        search_res = search_engine.search(SearchRequest(query="When is the submission deadline?", limit=3))
        assert len(search_res.results) > 0, "Search should return relevant memories"
        top = search_res.results[0]
        print(f"      [OK] Search returned {len(search_res.results)} results in {search_res.elapsed_ms} ms")
        print(f"      Top match: [{top.application_name}] {top.window_title} (Score: {round(top.score * 100, 1)}%)")

        print("\n" + "-" * 60)
        print(f"Total External Network Calls Attempted: {len(_network_calls_attempted)}")
        if len(_network_calls_attempted) == 0:
            print("[SUCCESS] RecallX operates 100% locally with ZERO cloud dependencies!")
        else:
            print(f"[FAIL] Blocked external calls: {_network_calls_attempted}")
            sys.exit(1)
        print("-" * 60 + "\n")

    finally:
        socket.socket.connect = _original_connect


if __name__ == "__main__":
    main()
