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
    print("\n" + "=" * 50)
    print("           RecallX Benchmark Suite")
    print("=" * 50)
    print("Running on-device latency and throughput tests...\n")

    t0 = time.perf_counter()
    metrics = benchmark_service.run_benchmark(num_samples=5)
    total_elapsed = round(time.perf_counter() - t0, 2)

    vm = psutil.virtual_memory()
    mem_used_mb = round(psutil.Process().memory_info().rss / (1024 * 1024), 2)

    print("=" * 50)
    print("RecallX Benchmark Results")
    print("=" * 50)
    print(f"Timestamp:                 {metrics.timestamp}")
    print(f"OS:                        {metrics.os}")
    print(f"Hardware Processor:        {metrics.processor}")
    print(f"Model:                     {metrics.model}")
    print(f"Embedding Runtime:         {metrics.execution_provider}")
    print(f"Acceleration Status:       {metrics.status}")
    print("-" * 50)
    print(f"Average OCR Latency:       {metrics.ocr_latency_avg_ms} ms")
    print(f"Average Embedding Latency: {metrics.embedding_latency_avg_ms} ms")
    print(f"P95 Embedding Latency:     {metrics.embedding_latency_p95_ms} ms")
    print(f"Average Search Latency:    {metrics.search_latency_avg_ms} ms")
    print(f"End-to-End Latency:        {metrics.end_to_end_avg_ms} ms")
    print(f"Process Memory Usage:      {mem_used_mb} MB")
    print("-" * 50)
    print(f"Benchmark run completed in {total_elapsed}s.")
    print("Exported results to: benchmarks/results.json")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
