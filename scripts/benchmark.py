import json
import sys
import time
from pathlib import Path
import psutil

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.services.benchmark_service import benchmark_service


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n" + "=" * 60)
    print("           RecallX Benchmark Suite")
    print("=" * 60)
    print("Running on-device latency, throughput, and retrieval tests...\n")

    t0 = time.perf_counter()
    metrics = benchmark_service.run_benchmark(num_samples=5)
    total_elapsed = round(time.perf_counter() - t0, 2)

    mem_used_mb = round(psutil.Process().memory_info().rss / (1024 * 1024), 2)

    print("=" * 60)
    print("RecallX Benchmark Results (On-Device Local Inference)")
    print("=" * 60)
    print(f"Timestamp:                 {metrics.timestamp}")
    print(f"OS:                        {metrics.os}")
    print(f"Hardware Processor:        {metrics.processor}")
    print(f"Model:                     {metrics.model}")
    print(f"Active Provider:           {metrics.execution_provider}")
    print(f"Runtime State:             {metrics.runtime_state}")
    print(f"Snapdragon Validation:     {metrics.snapdragon_validation}")
    print(f"Acceleration Status:       {metrics.status}")
    print("-" * 60)
    print("Granular Pipeline Latency Breakdown:")
    print(f"  • Cold-Start / Warmup:          {metrics.cold_start_load_ms:>8.2f} ms")
    print(f"  • OCR Latency (WinRT / Native):  {metrics.ocr_latency_avg_ms:>8.2f} ms")
    print(f"  • Warm Embedding (Avg):          {metrics.warm_embedding_avg_ms:>8.2f} ms")
    print(f"  • Warm Embedding (P95):          {metrics.warm_embedding_p95_ms:>8.2f} ms")
    print(f"  • Batch Embedding (per item):    {metrics.batch_embedding_avg_ms_per_item:>8.2f} ms")
    print(f"  • Vector Cosine Search Alone:    {metrics.vector_search_latency_avg_ms:>8.2f} ms")
    print(f"  • Full Hybrid Search:            {metrics.full_search_latency_avg_ms:>8.2f} ms")
    print(f"  • End-to-End Pipeline:           {metrics.end_to_end_avg_ms:>8.2f} ms")
    print("-" * 60)
    print(f"Process Memory Usage:      {mem_used_mb} MB")
    print(f"Benchmark completed in {total_elapsed}s.")
    print("Exported results to: benchmarks/results.json")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
