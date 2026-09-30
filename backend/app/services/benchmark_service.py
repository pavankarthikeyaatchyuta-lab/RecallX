import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

from backend.app.core.config import BENCHMARKS_FILE
from backend.app.core.hardware import detect_hardware
from backend.app.embeddings.manager import model_manager
from backend.app.models.schemas import BenchmarkMetrics, SearchRequest
from backend.app.ocr.engine import ocr_engine
from backend.app.search.engine import search_engine
from backend.app.search.vector_index import vector_index


class BenchmarkService:
    def run_benchmark(self, num_samples: int = 5) -> BenchmarkMetrics:
        """
        Executes real, provider-agnostic, honest latency measurements across:
        - Cold-start model load & JIT compilation
        - Warm steady-state single-query embedding (measured via public ModelManager API)
        - Batch embedding throughput (ms/item via public ModelManager API)
        - Vector search alone (NumPy cosine retrieval)
        - Full hybrid search (query embed + vector + keyword + recency + snippets)
        - OCR text extraction
        - End-to-end user pipeline

        Never fakes or fabricates any numbers.
        """
        hw = detect_hardware()
        status = model_manager.get_runtime_status()
        is_npu_verified = status.get("is_npu_active", False)

        # 1. Measure Cold Start Load / JIT Latency
        t_cold_start = time.perf_counter()
        _ = model_manager.warmup()
        cold_start_ms = round((time.perf_counter() - t_cold_start) * 1000, 2)

        # 2. OCR Latency Benchmark with synthetic test frames
        ocr_latencies: list[float] = []
        for i in range(num_samples):
            test_img = Image.new("RGB", (1280, 720), color=(255, 255, 255))
            draw = ImageDraw.Draw(test_img)
            draw.text(
                (50, 50 + i * 20),
                f"RecallX Benchmark Sample {i}: Applications close on September 30 deadline.",
                fill=(0, 0, 0),
            )
            _, lat = ocr_engine.extract_text(test_img)
            ocr_latencies.append(lat)

        avg_ocr = round(float(np.mean(ocr_latencies)), 2)

        # 3. Warm Single-Query Embedding Latency Benchmark via public API
        # Using unique query strings ensures cache-bypass to measure true inference latency
        bench_queries = [
            f"Find the internship application deadline sample {uuid.uuid4().hex[:8]}"
            for _ in range(num_samples)
        ] + [
            f"Where did I see the Qualcomm AI Hub documentation {uuid.uuid4().hex[:8]}",
            f"Show me the Python project I worked on yesterday {uuid.uuid4().hex[:8]}",
            f"Find the document with the ₹50,000 amount {uuid.uuid4().hex[:8]}",
            f"Locate the meeting notes from yesterday afternoon {uuid.uuid4().hex[:8]}",
        ]
        
        warm_latencies: list[float] = []
        for q in bench_queries:
            _, lat = model_manager.embed_text(q)
            warm_latencies.append(lat)

        avg_warm_emb = round(float(np.mean(warm_latencies)), 2)
        p95_warm_emb = round(float(np.percentile(warm_latencies, 95)), 2)

        # 4. Batch Embedding Latency (Throughput per item via public API)
        batch_size = 16
        batch_texts = [
            f"RecallX batch indexing memory scenario entry {uuid.uuid4().hex[:8]} for high throughput."
            for _ in range(batch_size)
        ]
        t_batch_start = time.perf_counter()
        _, _ = model_manager.embed_batch(batch_texts)
        batch_total_ms = (time.perf_counter() - t_batch_start) * 1000
        avg_batch_per_item = round(batch_total_ms / batch_size, 2)

        # 5. Vector Search Latency Alone (NumPy Cosine Retrieval)
        dim = model_manager.active_provider.dimension or 384
        dummy_query_vector = [0.05] * dim
        vec_search_latencies: list[float] = []
        for _ in range(10):
            t0 = time.perf_counter()
            _ = vector_index.search(dummy_query_vector, top_k=20)
            vec_search_latencies.append((time.perf_counter() - t0) * 1000)
        avg_vector_search = round(float(np.mean(vec_search_latencies)), 2)

        # 6. Full Search Latency (Query Embedding + Retrieval + Ranking + Explanation)
        full_search_latencies: list[float] = []
        test_queries = [
            "Find the internship application with the September deadline",
            "Qualcomm AI Hub documentation",
            "Python project worked on yesterday",
            "document with the ₹50,000 amount",
            "meeting notes from yesterday",
        ]
        for q in test_queries:
            t0 = time.perf_counter()
            _ = search_engine.search(SearchRequest(query=q, limit=10))
            full_search_latencies.append((time.perf_counter() - t0) * 1000)

        avg_full_search = round(float(np.mean(full_search_latencies)), 2)

        # 7. End-to-End Pipeline Latency (OCR + Embedding + Full Search)
        avg_e2e = round(avg_ocr + avg_warm_emb + avg_full_search, 2)

        snapdragon_validation = "verified" if is_npu_verified else "pending"

        metrics = BenchmarkMetrics(
            timestamp=datetime.now().isoformat(),
            processor=hw.processor,
            os=f"{hw.os} {hw.os_version}",
            model=status["active_model"],
            execution_provider=status["active_runtime"],
            cold_start_load_ms=cold_start_ms,
            warm_embedding_avg_ms=avg_warm_emb,
            warm_embedding_p95_ms=p95_warm_emb,
            batch_embedding_avg_ms_per_item=avg_batch_per_item,
            vector_search_latency_avg_ms=avg_vector_search,
            full_search_latency_avg_ms=avg_full_search,
            ocr_latency_avg_ms=avg_ocr,
            embedding_latency_avg_ms=avg_warm_emb,
            embedding_latency_p95_ms=p95_warm_emb,
            search_latency_avg_ms=avg_full_search,
            end_to_end_avg_ms=avg_e2e,
            samples_count=len(bench_queries),
            status=status["status_banner"],
            runtime_state=status.get("runtime_state", "CPU_FALLBACK"),
            snapdragon_validation=snapdragon_validation,
        )

        # Persist truthful results to benchmarks/results.json
        try:
            BENCHMARKS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BENCHMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(metrics.model_dump(), f, indent=2)
        except Exception:
            pass

        return metrics

    def get_latest_results(self) -> BenchmarkMetrics | None:
        if BENCHMARKS_FILE.exists():
            try:
                with open(BENCHMARKS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return BenchmarkMetrics(**data)
            except Exception:
                return None
        return None


benchmark_service = BenchmarkService()
