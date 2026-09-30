from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.core.config import settings
from backend.app.core.hardware import HardwareInfo, detect_hardware
from backend.app.embeddings.manager import model_manager
from backend.app.models.schemas import (
    BenchmarkMetrics,
    CaptureStatus,
    Memory,
    MemoryListResponse,
    SearchRequest,
    SearchResponse,
    SettingsModel,
)
from backend.app.search.engine import search_engine
from backend.app.services.benchmark_service import benchmark_service
from backend.app.services.capture_service import capture_service
from backend.app.services.demo_service import seed_demo_memories
from backend.app.services.memory_service import memory_service
from backend.app.storage.database import set_setting

router = APIRouter()


@router.get("/health")
def get_health():
    return {
        "status": "ok",
        "app": "RecallX",
        "privacy": "local-only",
        "cloud_requests": 0,
    }


@router.get("/status", response_model=CaptureStatus)
def get_status():
    return capture_service.get_status()


@router.get("/hardware", response_model=HardwareInfo)
def get_hardware():
    return detect_hardware()


@router.get("/runtime")
def get_runtime():
    return model_manager.get_runtime_status()


@router.get("/memories", response_model=MemoryListResponse)
def get_memories(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    app: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    memories = memory_service.list_memories(
        limit=limit,
        offset=offset,
        app=app,
        date_from=date_from,
        date_to=date_to,
    )
    total = memory_service.total_count()
    unique_apps = memory_service.get_apps()
    return MemoryListResponse(total=total, memories=memories, unique_apps=unique_apps)


@router.get("/memories/{memory_id}", response_model=Memory)
def get_memory_detail(memory_id: str):
    mem = memory_service.get_by_id(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    return mem


@router.post("/capture")
def trigger_capture():
    mem, message = capture_service.trigger_manual_capture()
    if not mem:
        return {"status": "skipped", "message": message, "memory": None}
    return {"status": "success", "message": message, "memory": mem}


@router.post("/capture/start", response_model=CaptureStatus)
def start_capture():
    return capture_service.start_capture()


@router.post("/capture/stop", response_model=CaptureStatus)
def stop_capture():
    return capture_service.stop_capture()


@router.post("/search", response_model=SearchResponse)
def execute_search(request: SearchRequest):
    return search_engine.search(request)


@router.get("/settings", response_model=SettingsModel)
def get_settings():
    return SettingsModel(
        capture_interval_seconds=settings.capture_interval_seconds,
        capture_enabled=settings.capture_enabled,
        excluded_applications=settings.excluded_applications,
        semantic_weight=settings.semantic_weight,
        keyword_weight=settings.keyword_weight,
        recency_weight=settings.recency_weight,
        preferred_provider=settings.preferred_provider,
        preferred_ocr=settings.preferred_ocr,
    )


@router.put("/settings", response_model=SettingsModel)
def update_settings(new_settings: SettingsModel):
    settings.capture_interval_seconds = new_settings.capture_interval_seconds
    settings.capture_enabled = new_settings.capture_enabled
    settings.excluded_applications = new_settings.excluded_applications
    settings.semantic_weight = new_settings.semantic_weight
    settings.keyword_weight = new_settings.keyword_weight
    settings.recency_weight = new_settings.recency_weight
    settings.preferred_provider = new_settings.preferred_provider
    settings.preferred_ocr = new_settings.preferred_ocr

    # Persist in SQLite
    set_setting("capture_interval_seconds", settings.capture_interval_seconds)
    set_setting("excluded_applications", settings.excluded_applications)
    set_setting("preferred_provider", settings.preferred_provider)

    # Refresh model manager provider choice
    model_manager.refresh_provider()

    return new_settings


@router.delete("/memories/{memory_id}")
def delete_single_memory(memory_id: str):
    deleted = memory_service.delete(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "id": memory_id}


@router.delete("/memories")
def delete_all():
    count = memory_service.delete_all()
    return {"status": "cleared", "deleted_count": count}


@router.get("/benchmark", response_model=Optional[BenchmarkMetrics])
def get_benchmark():
    res = benchmark_service.get_latest_results()
    if not res:
        # Run an initial benchmark if none exists
        res = benchmark_service.run_benchmark(num_samples=3)
    return res


@router.post("/benchmark/run", response_model=BenchmarkMetrics)
def run_benchmark_now():
    return benchmark_service.run_benchmark(num_samples=5)


@router.post("/demo/seed")
def seed_demo_data():
    count = seed_demo_memories()
    return {"status": "seeded", "count": count}
