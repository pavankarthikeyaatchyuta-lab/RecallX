import threading
import time
from datetime import datetime
from typing import Optional

from backend.app.capture.engine import capture_screen
from backend.app.core.config import settings
from backend.app.models.schemas import CaptureStatus, Memory
from backend.app.ocr.engine import ocr_engine
from backend.app.services.memory_service import memory_service


class CaptureService:
    def __init__(self):
        self.is_capturing = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_captured_at: Optional[str] = None
        self.last_error: Optional[str] = None
        self._lock = threading.Lock()

    def get_status(self) -> CaptureStatus:
        return CaptureStatus(
            is_capturing=self.is_capturing,
            interval_seconds=settings.capture_interval_seconds,
            last_captured_at=self.last_captured_at,
            total_memories=memory_service.total_count(),
            last_error=self.last_error,
            cloud_requests=0,
        )

    def trigger_manual_capture(self) -> tuple[Optional[Memory], str]:
        """Manually captures the screen immediately and processes OCR + embeddings."""
        try:
            img_path, app_name, win_title, skip_reason = capture_screen()
            if skip_reason:
                return None, f"Capture skipped: {skip_reason}"

            if not img_path or not img_path.exists():
                return None, "Failed to capture screen image."

            # OCR step
            extracted_text, ocr_latency = ocr_engine.extract_text(img_path)

            # Store memory
            relative_screenshot_path = f"/data/screenshots/{img_path.name}"
            mem = memory_service.create_memory(
                screenshot_path=relative_screenshot_path,
                extracted_text=extracted_text,
                application_name=app_name,
                window_title=win_title,
                ocr_latency_ms=ocr_latency,
                is_demo=False,
            )

            now_str = datetime.now().strftime("%I:%M:%S %p")
            self.last_captured_at = now_str
            self.last_error = None
            return mem, "Screen memory captured successfully."
        except Exception as e:
            self.last_error = str(e)
            return None, f"Capture failed: {e}"

    def start_capture(self) -> CaptureStatus:
        with self._lock:
            if self.is_capturing:
                return self.get_status()

            self.is_capturing = True
            settings.capture_enabled = True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            return self.get_status()

    def stop_capture(self) -> CaptureStatus:
        with self._lock:
            if not self.is_capturing:
                return self.get_status()

            self.is_capturing = False
            settings.capture_enabled = False
            self._stop_event.set()
            return self.get_status()

    def _capture_loop(self):
        while not self._stop_event.is_set():
            try:
                self.trigger_manual_capture()
            except Exception as e:
                self.last_error = str(e)

            # Wait for interval or stop event
            self._stop_event.wait(timeout=settings.capture_interval_seconds)


capture_service = CaptureService()
