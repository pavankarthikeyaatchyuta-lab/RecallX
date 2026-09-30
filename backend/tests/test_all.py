import os
import sys
import time
from pathlib import Path
import pytest
from PIL import Image, ImageDraw

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.capture.engine import is_application_excluded
from backend.app.core.config import SCREENSHOTS_DIR, settings
from backend.app.core.hardware import detect_hardware
from backend.app.embeddings.manager import CPUEmbeddingProvider, QualcommQNNEmbeddingProvider, model_manager
from backend.app.embeddings.providers.cpu_provider import LocalCPUProvider
from backend.app.embeddings.providers.qualcomm_provider import QualcommQNNProvider
from backend.app.models.schemas import SearchRequest
from backend.app.ocr.engine import ocr_engine
from backend.app.search.engine import search_engine
from backend.app.search.hybrid_ranker import (
    compute_hybrid_rank,
    compute_keyword_score,
    compute_recency_score,
)
from backend.app.search.vector_index import vector_index
from backend.app.services.capture_service import capture_service
from backend.app.services.memory_service import memory_service
from backend.app.storage.database import (
    count_memories,
    delete_memory,
    get_memory,
    init_db,
    insert_memory,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()


def test_hardware_detection():
    hw = detect_hardware()
    assert hw.os != ""
    assert hw.total_ram_gb > 0
    assert hw.cloud_requests == 0
    assert isinstance(hw.execution_providers, list)
    assert hw.runtime_state in ("CPU_FALLBACK", "QNN_AVAILABLE", "QNN_ACTIVE")
    # Never claim NPU unless host is truly Snapdragon
    if not hw.is_snapdragon:
        assert hw.qnn_available is False or hw.active_runtime != "Qualcomm QNN (NPU)"
        assert hw.runtime_state == "CPU_FALLBACK"


def test_ocr_pipeline():
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 30), "RecallX Unit Test OCR", fill=(0, 0, 0))
    text, lat = ocr_engine.extract_text(img)
    assert lat >= 0.0
    assert isinstance(text, str)


def test_embedding_providers():
    cpu_p = LocalCPUProvider()
    assert cpu_p.is_available() is True
    vec = cpu_p.embed_text("Test embedding query")
    assert len(vec) == 384
    assert round(sum(x**2 for x in vec), 3) == 1.0  # normalized

    qnn_p = QualcommQNNProvider()
    # Factual availability verification: should not crash
    avail = qnn_p.is_available()
    info = qnn_p.get_info()
    assert "name" in info
    assert "is_available" in info
    assert "runtime_state" in info
    assert info["device"] == "Snapdragon NPU (Hexagon)"
    assert CPUEmbeddingProvider == LocalCPUProvider
    assert QualcommQNNEmbeddingProvider == QualcommQNNProvider


def test_model_manager():
    status = model_manager.get_runtime_status()
    assert "active_model" in status
    assert "status_banner" in status
    assert "runtime_state" in status
    assert status["runtime_state"] in ("CPU_FALLBACK", "QNN_AVAILABLE", "QNN_ACTIVE", "QNN_ERROR", "MODEL_UNAVAILABLE")

    vec, lat = model_manager.embed_text("Qualcomm Snapdragon AI Challenge")
    assert len(vec) == 384
    assert lat > 0.0

    warm_ms = model_manager.warmup()
    assert warm_ms >= 0.0


def test_vector_index():
    test_id = "test_vec_01"
    vec = [0.1] * 384
    vector_index.add(test_id, vec)
    assert vector_index.size() > 0

    results = vector_index.search(vec, top_k=5)
    assert len(results) > 0
    found_ids = [r[0] for r in results]
    assert test_id in found_ids

    vector_index.remove(test_id)


def test_hybrid_ranking():
    # Test keyword scoring
    kw_score = compute_keyword_score(
        query="internship deadline",
        text="The internship closes on September 30 deadline.",
        title="Application",
        app="Chrome",
    )
    assert kw_score > 0.5

    # Test recency scoring
    now = time.time()
    recent = compute_recency_score(now - 3600, now)
    older = compute_recency_score(now - 86400 * 14, now)
    assert recent > older

    # Test combined score
    hybrid = compute_hybrid_rank(semantic_score=0.8, keyword_score=0.9, recency_score=0.5)
    assert 0.0 <= hybrid <= 1.0


def test_memory_crud_service():
    mem = memory_service.create_memory(
        screenshot_path="/data/screenshots/test_crud.png",
        extracted_text="Python FastAPI test text",
        application_name="VS Code",
        window_title="test_all.py",
        ocr_latency_ms=5.0,
        ocr_status="ok",
        custom_id="test_crud_mem",
    )
    assert mem.id == "test_crud_mem"
    assert mem.ocr_status == "ok"

    retrieved = get_memory("test_crud_mem")
    assert retrieved is not None
    assert retrieved.application_name == "VS Code"
    assert retrieved.ocr_status == "ok"

    # Search for this memory
    res = search_engine.search(SearchRequest(query="FastAPI test text", limit=5))
    ids = [r.id for r in res.results]
    assert "test_crud_mem" in ids

    # Delete memory safely
    deleted = memory_service.delete("test_crud_mem")
    assert deleted is True
    assert get_memory("test_crud_mem") is None


def test_capture_lifecycle_and_exclusions():
    # 1. Excluded applications check
    assert is_application_excluded("1Password", "Vault") is True
    assert is_application_excluded("Bank of America", "Account Summary") is True
    assert is_application_excluded("KeePass", "Database") is True
    assert is_application_excluded("Visual Studio Code", "main.py") is False

    # 2. Lifecycle methods: start, stop, restart, shutdown
    status_start = capture_service.start_capture()
    assert status_start.is_capturing is True

    status_stop = capture_service.stop_capture()
    assert status_stop.is_capturing is False

    status_restart = capture_service.restart_capture()
    assert status_restart.is_capturing is True

    capture_service.shutdown()
    assert capture_service.is_capturing is False


def test_privacy_guarantee():
    hw = detect_hardware()
    assert hw.cloud_requests == 0
    assert hasattr(hw, "qualcomm_hardware_detected")
    assert hasattr(hw, "cpu")
    assert hasattr(hw, "architecture")
    if not hw.is_snapdragon:
        assert hw.qualcomm_hardware_detected is False


def test_capture_failure_never_creates_synthetic_memory(monkeypatch):
    """Verifies screen capture failure returns an error and never injects fake memories."""
    from backend.app.capture import engine
    from backend.app.storage.database import count_memories

    initial_count = count_memories()

    # Force grab methods to fail / return None
    monkeypatch.setattr("PIL.ImageGrab.grab", lambda: None)
    if "mss" in sys.modules:
        monkeypatch.setattr("mss.MSS.grab", lambda self, mon: None)

    mem, msg = capture_service.trigger_manual_capture()
    # Must fail cleanly and not create a memory
    assert mem is None
    assert "failed" in msg.lower() or "skipped" in msg.lower()
    assert count_memories() == initial_count


def test_vector_index_metadata_and_rebuild():
    """Verifies vector index companion metadata and safe rebuild capabilities."""
    from backend.app.search.vector_index import INDEX_META_FILE

    # Ensure index save writes companion metadata
    test_id = "test_meta_mem_01"
    vector_index.add(test_id, [0.05] * 384)
    assert INDEX_META_FILE.exists()

    # Rebuild from existing memories should succeed without crashing
    mems = memory_service.list_memories(limit=5)
    rebuilt_count = vector_index.rebuild_from_memories(
        memories=mems,
        embed_fn=model_manager.embed_text,
        model_id="all-MiniLM-L6-v2",
        dimension=384,
    )
    assert rebuilt_count == len(mems)

