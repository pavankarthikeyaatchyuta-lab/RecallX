import platform
import psutil
from pydantic import BaseModel


class HardwareInfo(BaseModel):
    cpu: str
    architecture: str
    os: str
    os_version: str
    processor: str
    machine: str
    total_ram_gb: float
    available_ram_gb: float
    is_snapdragon: bool
    qualcomm_hardware_detected: bool
    execution_providers: list[str]
    qnn_available: bool
    cuda_available: bool
    active_runtime: str
    acceleration_status: str
    runtime_state: str = "CPU_FALLBACK"
    cloud_requests: int = 0


def detect_hardware() -> HardwareInfo:
    """Truthful detection of host hardware and AI execution providers."""
    os_name = platform.system()
    os_ver = f"{platform.release()} ({platform.version()})"
    proc = platform.processor() or "Unknown Processor"
    machine = platform.machine()
    
    vm = psutil.virtual_memory()
    total_ram = round(vm.total / (1024**3), 2)
    avail_ram = round(vm.available / (1024**3), 2)

    # Detect execution providers via ONNX Runtime if available
    available_providers: list[str] = []
    try:
        import onnxruntime as ort
        available_providers = ort.get_available_providers()
    except Exception:
        available_providers = ["CPUExecutionProvider"]

    qnn_available = "QNNExecutionProvider" in available_providers
    cuda_available = "CUDAExecutionProvider" in available_providers

    # Check if host CPU/architecture is Qualcomm/Snapdragon
    proc_lower = proc.lower()
    machine_lower = machine.lower()
    is_snapdragon = (
        "snapdragon" in proc_lower
        or "qualcomm" in proc_lower
        or "qcom" in proc_lower
        or ("arm64" in machine_lower and "snapdragon" in proc_lower)
    )

    if is_snapdragon and qnn_available:
        acceleration_status = "Snapdragon AI acceleration available (QNN NPU Active)"
        active_runtime = "Qualcomm QNN (NPU)"
        runtime_state = "QNN_ACTIVE"
    elif is_snapdragon and not qnn_available:
        acceleration_status = "Snapdragon hardware detected — QNN Execution Provider not active, using CPU fallback"
        active_runtime = "CPU Fallback"
        runtime_state = "CPU_FALLBACK"
    else:
        acceleration_status = "Development mode: Qualcomm NPU unavailable — using CPU fallback"
        active_runtime = "CPU"
        runtime_state = "CPU_FALLBACK"

    return HardwareInfo(
        cpu=proc,
        architecture=machine,
        os=os_name,
        os_version=os_ver,
        processor=proc,
        machine=machine,
        total_ram_gb=total_ram,
        available_ram_gb=avail_ram,
        is_snapdragon=is_snapdragon,
        qualcomm_hardware_detected=is_snapdragon,
        execution_providers=available_providers,
        qnn_available=qnn_available,
        cuda_available=cuda_available,
        active_runtime=active_runtime,
        acceleration_status=acceleration_status,
        runtime_state=runtime_state,
        cloud_requests=0,
    )
