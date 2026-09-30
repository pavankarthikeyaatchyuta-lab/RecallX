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

from backend.app.core.hardware import detect_hardware
from backend.app.embeddings.manager import model_manager
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
    # Never claim NPU unless host is truly Snapdragon
    if not hw.is_snapdragon:
        assert hw.qnn_available is False or hw.active_runtime != "Qualcomm QNN (NPU)"


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
    assert info["device"] == "Snapdragon NPU (Hexagon)"


def test_model_manager():
    status = model_manager.get_runtime_status()
    assert "active_model" in status
    assert "status_banner" in status
    vec, lat = model_manager.embed_text("Qualcomm Snapdragon AI Challenge")
    assert len(vec) == 384
    assert lat > 0.0


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
        custom_id="test_crud_mem",
    )
    assert mem.id == "test_crud_mem"

    retrieved = get_memory("test_crud_mem")
    assert retrieved is not None
    assert retrieved.application_name == "VS Code"

    # Search for this memory
    res = search_engine.search(SearchRequest(query="FastAPI test text", limit=5))
    ids = [r.id for r in res.results]
    assert "test_crud_mem" in ids

    # Delete memory
    deleted = memory_service.delete("test_crud_mem")
    assert deleted is True
    assert get_memory("test_crud_mem") is None


def test_privacy_guarantee():
    hw = detect_hardware()
    assert hw.cloud_requests == 0
