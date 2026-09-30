from PIL import Image, ImageEnhance, ImageOps


def preprocess_for_ocr(image: Image.Image, max_dim: int = 1920) -> Image.Image:
    """Preprocesses screenshot for maximum OCR clarity and speed."""
    # Ensure RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Downscale if image is exceptionally large (e.g. 4K screen) for latency control
    width, height = image.size
    if width > max_dim or height > max_dim:
        ratio = min(max_dim / width, max_dim / height)
        new_size = (int(width * ratio), int(height * ratio))
        image = image.resize(new_size, Image.Resampling.BILINEAR)

    # Slight contrast enhancement to make text pop against dark/light backgrounds
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)

    return image
