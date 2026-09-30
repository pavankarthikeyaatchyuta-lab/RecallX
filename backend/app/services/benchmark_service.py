import json
import time
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


class BenchmarkService:
    def run_benchmark(self, num_samples: int = 5) -> BenchmarkMetrics:
        """
        Executes real latency measurements across OCR, Embedding, Search, and End-to-End.
        Never invents or fakes any numbers.
        """
        hw = detect_hardware()
        status = model_manager.get_runtime_status()

        # 1. OCR Latency Benchmark with test synthetic frames
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

        # 2. Embedding Latency Benchmark
        test_queries = [
            "Find the internship application with the September deadline",
            "Where did I see the Qualcomm AI Hub documentation?",
            "Show me the Python project I worked on yesterday",
            "Find the document with the ₹50,000 amount",
            "Locate the meeting notes from yesterday afternoon",
        ]
        embedding_latencies: list[float] = []
        for q in test_queries:
            _, lat = model_manager.embed_text(q)
            embedding_latencies.append(lat)

        avg_emb = round(float(np.mean(embedding_latencies)), 2)
        p95_emb = round(float(np.percentile(embedding_latencies, 95)), 2)

        # 3. Search Latency Benchmark
        search_latencies: list[float] = []
        for q in test_queries:
            t0 = time.perf_counter()
            search_engine.search(SearchRequest(query=q, limit=10))
            search_latencies.append((time.perf_counter() - t0) * 1000)

        avg_search = round(float(np.mean(search_latencies)), 2)

        # 4. End-to-end average estimated latency
        avg_e2e = round(avg_ocr + avg_emb + avg_search, 2)

        metrics = BenchmarkMetrics(
            timestamp=datetime.now().isoformat(),
            processor=hw.processor,
            os=f"{hw.os} {hw.os_version}",
            model=status["active_model"],
            execution_provider=status["active_runtime"],
            ocr_latency_avg_ms=avg_ocr,
            embedding_latency_avg_ms=avg_emb,
            embedding_latency_p95_ms=p95_emb,
            search_latency_avg_ms=avg_search,
            end_to_end_avg_ms=avg_e2e,
            samples_count=len(test_queries),
            status=status["status_banner"],
        )

        # Persist to benchmarks/results.json
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
