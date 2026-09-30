from typing import Optional
from pydantic import BaseModel, Field


class Memory(BaseModel):
    id: str
    timestamp: float
    iso_timestamp: str
    screenshot_path: str
    extracted_text: str
    application_name: str
    window_title: str
    ocr_latency_ms: float = 0.0
    embedding_latency_ms: float = 0.0
    ocr_status: str = "ok"
    is_demo: bool = False
    created_at: str


class SearchResult(BaseModel):
    id: str
    screenshot_path: str
    timestamp: float
    iso_timestamp: str
    extracted_text: str
    snippet: str
    application_name: str
    window_title: str
    score: float
    semantic_score: float
    keyword_score: float
    recency_score: float
    match_explanation: str
    is_demo: bool = False


class SearchRequest(BaseModel):
    query: str
    application: Optional[str] = None
    date_from: Optional[str] = None  # ISO date string YYYY-MM-DD
    date_to: Optional[str] = None    # ISO date string YYYY-MM-DD
    limit: int = Field(default=20, ge=1, le=100)


class SearchResponse(BaseModel):
    query: str
    total: int
    elapsed_ms: float
    results: list[SearchResult]


class CaptureStatus(BaseModel):
    is_capturing: bool
    interval_seconds: int
    last_captured_at: Optional[str] = None
    total_memories: int = 0
    last_error: Optional[str] = None
    cloud_requests: int = 0


class MemoryListResponse(BaseModel):
    total: int
    memories: list[Memory]
    unique_apps: list[str]


class SettingsModel(BaseModel):
    capture_interval_seconds: int
    capture_enabled: bool
    excluded_applications: list[str]
    semantic_weight: float
    keyword_weight: float
    recency_weight: float
    preferred_provider: str
    preferred_ocr: str


class BenchmarkMetrics(BaseModel):
    timestamp: str
    processor: str
    os: str
    model: str
    execution_provider: str
    cold_start_load_ms: float = 0.0
    warm_embedding_avg_ms: float = 0.0
    warm_embedding_p95_ms: float = 0.0
    batch_embedding_avg_ms_per_item: float = 0.0
    vector_search_latency_avg_ms: float = 0.0
    full_search_latency_avg_ms: float = 0.0
    ocr_latency_avg_ms: float = 0.0
    embedding_latency_avg_ms: float = 0.0
    embedding_latency_p95_ms: float = 0.0
    search_latency_avg_ms: float = 0.0
    end_to_end_avg_ms: float = 0.0
    samples_count: int = 5
    status: str
    runtime_state: str = "CPU_FALLBACK"
    snapdragon_validation: str = "pending"
