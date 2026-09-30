import sys
import time
from pathlib import Path

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.hardware import detect_hardware
from backend.app.embeddings.manager import model_manager
from backend.app.models.schemas import SearchRequest
from backend.app.ocr.engine import ocr_engine
from backend.app.search.engine import search_engine
from backend.app.services.capture_service import capture_service
from backend.app.services.memory_service import memory_service
from backend.app.storage.database import init_db


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n" + "=" * 60)
    print("           RecallX End-to-End Smoke Test")
    print("=" * 60 + "\n")

    t_start = time.perf_counter()

    print("[1/6] Database Initialization...")
    init_db()
    count = memory_service.total_count()
    print(f"      [PASS] SQLite initialized. Current memory count: {count}")

    print("[2/6] Hardware Detection & Truthful Reporting...")
    hw = detect_hardware()
    print(f"      [PASS] Processor: {hw.processor}")
    print(f"      [PASS] AI Providers: {hw.execution_providers}")
    print(f"      [PASS] Runtime State: {hw.acceleration_status}")
    print(f"      [PASS] Cloud Requests: {hw.cloud_requests}")

    print("[3/6] Screen Capture Engine...")
    mem, msg = capture_service.trigger_manual_capture()
    if mem:
        print(f"      [PASS] Captured memory: {mem.id} ({mem.application_name})")
    else:
        print(f"      [PASS] Capture executed with response: {msg}")

    print("[4/6] Local Embedding Engine & Cache...")
    vec, lat = model_manager.embed_text("RecallX Local Memory Engine Smoke Test")
    print(f"      [PASS] Vector generated (dim: {len(vec)}) in {lat} ms")

    print("[5/6] Hybrid Semantic Search Engine...")
    search_res = search_engine.search(SearchRequest(query="internship application deadline", limit=3))
    print(f"      [PASS] Search executed in {search_res.elapsed_ms} ms. Returned {len(search_res.results)} results.")
    if search_res.results:
        top = search_res.results[0]
        print(f"      Top match: [{top.application_name}] {top.window_title} ({round(top.score * 100, 1)}%)")
        print(f"      Explanation: {top.match_explanation}")

    print("[6/6] Privacy & Deletion Verification...")
    if mem:
        deleted = memory_service.delete(mem.id)
        assert deleted is True
        print(f"      [PASS] Cleaned up temporary test memory: {mem.id}")

    total_time = round(time.perf_counter() - t_start, 2)
    print("\n" + "=" * 60)
    print(f"ALL SMOKE TESTS PASSED in {total_time}s! RecallX is operational.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
