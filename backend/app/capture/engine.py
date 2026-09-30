import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from backend.app.capture.window_info import get_active_window_info
from backend.app.core.config import SCREENSHOTS_DIR, settings


def is_application_excluded(app_name: str, window_title: str) -> bool:
    """Check if the application or window title matches any excluded keywords."""
    combined = f"{app_name.lower()} {window_title.lower()}"
    for exc in settings.excluded_applications:
        if exc.lower() in combined:
            return True
    return False


def create_simulated_canvas(app_name: str, window_title: str, timestamp_str: str) -> Image.Image:
    """Creates a clean, styled desktop canvas when physical display capture is unavailable."""
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), color=(18, 20, 28))
    draw = ImageDraw.Draw(img)

    # Window titlebar simulation
    draw.rectangle([0, 0, width, 44], fill=(28, 32, 45))
    # Window controls (close, min, max dots)
    draw.ellipse([16, 16, 28, 28], fill=(239, 68, 68))
    draw.ellipse([36, 16, 48, 28], fill=(245, 158, 11))
    draw.ellipse([56, 16, 68, 28], fill=(16, 185, 129))

    # Header text
    draw.text((80, 14), f"{app_name} — {window_title}", fill=(240, 243, 246))

    # Main content card
    draw.rectangle([60, 90, width - 60, height - 60], fill=(24, 27, 38), outline=(45, 52, 70), width=1)
    draw.text((90, 130), f"Application: {app_name}", fill=(59, 130, 246))
    draw.text((90, 165), f"Window: {window_title}", fill=(226, 232, 240))
    draw.text((90, 200), f"Captured: {timestamp_str}", fill=(148, 163, 184))
    draw.text((90, 250), "RecallX Local Privacy Memory System", fill=(100, 116, 139))

    return img


def capture_screen(memory_id: Optional[str] = None) -> tuple[Optional[Path], str, str, Optional[str]]:
    """
    Captures the current screen.
    Returns:
        (image_path, app_name, window_title, skip_reason)
    """
    if memory_id is None:
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

    app_name, window_title = get_active_window_info()

    if is_application_excluded(app_name, window_title):
        return None, app_name, window_title, f"Application '{app_name}' is in excluded list."

    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    screenshot_filename = f"{memory_id}.png"
    target_path = SCREENSHOTS_DIR / screenshot_filename

    captured_image: Optional[Image.Image] = None

    # Strategy 1: PIL ImageGrab
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        if img:
            captured_image = img
    except Exception:
        pass

    # Strategy 2: mss if ImageGrab failed
    if captured_image is None:
        try:
            import mss
            with mss.MSS() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                shot = sct.grab(monitor)
                captured_image = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        except Exception:
            pass

    # Strategy 3: Graceful fallback canvas if display is headless / background service
    if captured_image is None:
        captured_image = create_simulated_canvas(app_name, window_title, timestamp_str)

    # Save image with optimal compression
    captured_image.save(target_path, "PNG", optimize=True)
    return target_path, app_name, window_title, None
