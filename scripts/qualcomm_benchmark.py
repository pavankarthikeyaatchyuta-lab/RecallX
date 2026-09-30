import platform
import sys
import time
from pathlib import Path

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import MODELS_DIR
from backend.app.embeddings.providers.qualcomm_provider import QualcommQNNProvider


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n" + "=" * 65)
    print("      RecallX Qualcomm Snapdragon NPU Benchmark Harness")
    print("=" * 65)

    proc = platform.processor() or "Unknown"
    machine = platform.machine()
    proc_lower = proc.lower()
    machine_lower = machine.lower()

    # Check available ONNX Runtime providers
    available_providers: list[str] = []
    try:
        import onnxruntime as ort
        available_providers = ort.get_available_providers()
    except Exception:
        available_providers = []

    has_qnn = "QNNExecutionProvider" in available_providers
    is_snapdragon = (
        "snapdragon" in proc_lower
        or "qualcomm" in proc_lower
        or "qcom" in proc_lower
        or ("arm64" in machine_lower and "snapdragon" in proc_lower)
    )

    print(f"Host Processor:           {proc}")
    print(f"Machine Architecture:     {machine}")
    print(f"Available ONNX Providers: {', '.join(available_providers) if available_providers else 'None'}")
    print(f"QNN Provider Registered:  {has_qnn}")
    print(f"Snapdragon Hardware:      {is_snapdragon}")
    print("-" * 65)

    if not is_snapdragon or not has_qnn:
        print("[!] NOTICE: Qualcomm QNN benchmark requires a compatible Snapdragon environment.")
        print()
        print("    Current Host: Intel / AMD x86_64 Development Machine.")
        print("    Status:       QNNExecutionProvider is not available on this host.")
        print("    Execution:    RecallX operates in truthful CPU fallback mode on Intel.")
        print()
        print("To run on Snapdragon Hardware (e.g. Snapdragon X Elite / Plus CRD):")
        print("  1. Boot Windows 11 on ARM64 on Snapdragon X Elite device.")
        print("  2. Install ONNX Runtime with Qualcomm QNN support:")
        print("       pip install onnxruntime-qnn")
        print("  3. Place Qualcomm AI Hub exported model at:")
        print(f"       {MODELS_DIR / 'nomic_embed_text_qnn.onnx'}")
        print("  4. Re-run this benchmark script.")
        print("=" * 65 + "\n")
        sys.exit(0)

    # If running on genuine Snapdragon with QNNExecutionProvider
    provider = QualcommQNNProvider()
    if not provider.is_available():
        print(f"[!] QNN Provider Unavailable: {provider.get_unavailability_reason()}")
        print("=" * 65 + "\n")
        sys.exit(1)

    print("[+] Snapdragon NPU detected. Initializing QNN HTP Session...")
    try:
        # Warmup pass
        _ = provider.embed_text("RecallX NPU warm-up prompt.")

        queries = [
            "Find the internship application with the September deadline",
            "Where did I see the Qualcomm AI Hub documentation?",
            "Show me the Python project I worked on yesterday",
            "Find the document with the ₹50,000 amount",
            "Locate the meeting notes from yesterday afternoon",
        ]

        latencies: list[float] = []
        for q in queries:
            t0 = time.perf_counter()
            _ = provider.embed_text(q)
            lat = (time.perf_counter() - t0) * 1000
            latencies.append(lat)

        import numpy as np
        avg_lat = round(float(np.mean(latencies)), 2)
        p95_lat = round(float(np.percentile(latencies, 95)), 2)

        print("[+] Benchmark complete on Hexagon NPU.")
        print(f"    Average NPU Latency: {avg_lat} ms")
        print(f"    P95 NPU Latency:     {p95_lat} ms")
        print("=" * 65 + "\n")

    except Exception as e:
        print(f"[-] QNN Benchmark Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
