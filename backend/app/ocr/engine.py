import asyncio
import time
from pathlib import Path
from typing import Union
from PIL import Image

from backend.app.ocr.preprocessor import preprocess_for_ocr


class OCREngine:
    def __init__(self):
        self.engine_name = "Windows Native OCR (WinRT)"
        self._test_engine()

    def _test_engine(self):
        try:
            import winocr
            self._has_winocr = True
        except ImportError:
            self._has_winocr = False
            self.engine_name = "Local OCR Fallback"

    def extract_text(self, image_input: Union[Path, str, Image.Image]) -> tuple[str, float]:
        """
        Extracts text from image.
        Returns:
            (extracted_text, latency_ms)
        """
        start_time = time.perf_counter()

        if isinstance(image_input, (str, Path)):
            image = Image.open(str(image_input))
        else:
            image = image_input

        image = preprocess_for_ocr(image)
        extracted_text = ""

        # Strategy 1: Windows Native OCR via winocr
        if self._has_winocr:
            try:
                import winocr

                async def _run_winocr():
                    res = await winocr.recognize_pil(image, "en")
                    lines = [line.text for line in res.lines]
                    return "\n".join(lines).strip()

                try:
                    extracted_text = asyncio.run(_run_winocr())
                except RuntimeError:
                    # In case an event loop is already running in current thread
                    loop = asyncio.get_event_loop()
                    extracted_text = loop.run_until_complete(_run_winocr())

            except Exception:
                extracted_text = ""

        # Strategy 2: Tesseract if available and winocr produced nothing
        if not extracted_text:
            try:
                import pytesseract
                extracted_text = pytesseract.image_to_string(image).strip()
            except Exception:
                pass

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return extracted_text, elapsed_ms


ocr_engine = OCREngine()
