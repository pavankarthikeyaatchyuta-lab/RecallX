import os
import platform
import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.config import MODELS_DIR
from backend.app.core.hardware import detect_hardware
from backend.app.embeddings.config import qualcomm_model_config
from backend.app.embeddings.providers.qualcomm_provider import QualcommQNNEmbeddingProvider


def main():
    hw = detect_hardware()
    qnn_provider = QualcommQNNEmbeddingProvider()

    cpu_name = platform.processor() or "Unknown CPU"
    os_str = f"{platform.system()} {platform.release()} ({platform.version()})"
    
    # ONNX Runtime version
    ort_version = "Not Installed"
    providers_list = []
    try:
        import onnxruntime as ort
        ort_version = ort.__version__
        providers_list = ort.get_available_providers()
    except Exception as e:
        ort_version = f"Error: {e}"

    qnn_ep_avail = "YES" if "QNNExecutionProvider" in providers_list else "NO"
    hardware_detected = "YES" if hw.qualcomm_hardware_detected else "NO"
    
    model_path = MODELS_DIR / qualcomm_model_config.artifact_filename
    model_found = "FOUND" if model_path.exists() else "NOT FOUND"

    input_meta_str = "N/A (Artifact pending)"
    output_meta_str = "N/A (Artifact pending)"
    session_status = "SKIPPED (Host CPU / Non-Snapdragon)"
    inference_status = "SKIPPED"
    npu_verified = "NOT VERIFIED"

    if model_path.exists() and qnn_ep_avail == "YES" and hardware_detected == "YES":
        try:
            qnn_provider.init_session()
            session_status = "SUCCESS"
            meta = qnn_provider.get_model_metadata()
            input_meta_str = str(list(meta.get("inputs", {}).keys()))
            output_meta_str = str(list(meta.get("outputs", {}).keys()))

            # Attempt real inference
            _ = qnn_provider.embed_text("RecallX verification inference test.")
            inference_status = "SUCCESS"
            npu_verified = "VERIFIED"
        except Exception as e:
            session_status = f"FAILED ({e})"
            inference_status = "SKIPPED"
            npu_verified = "NOT VERIFIED"

    runtime_state = qnn_provider.get_runtime_state()

    print("==================================================")
    print("RECALLX QUALCOMM VALIDATION REPORT")
    print("==================================================")
    print(f"CPU: {cpu_name}")
    print(f"OS: {os_str}")
    print(f"ONNX Runtime: {ort_version}")
    print(f"Execution Providers: {', '.join(providers_list)}")
    print(f"QNN EP Available: {qnn_ep_avail}")
    print(f"Qualcomm Hardware Detected: {hardware_detected}")
    print(f"Qualcomm Model Artifact: {model_found} ({model_path.name})")
    print(f"Model Input Metadata: {input_meta_str}")
    print(f"Model Output Metadata: {output_meta_str}")
    print(f"Session Initialized: {session_status}")
    print(f"Test Inference: {inference_status}")
    print(f"NPU Execution: {npu_verified}")
    print(f"Overall Status: {runtime_state} (Snapdragon validation pending)")
    print("==================================================")


if __name__ == "__main__":
    main()
