import os
from pathlib import Path
from pydantic import BaseModel, Field

# Root directory of the RecallX project
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Data paths
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
INDEX_DIR = DATA_DIR / "index"
DEMO_DIR = DATA_DIR / "demo"
DB_PATH = DATA_DIR / "recallx.db"
MODELS_DIR = BASE_DIR / "models"
BENCHMARKS_DIR = BASE_DIR / "benchmarks"
BENCHMARKS_FILE = BENCHMARKS_DIR / "results.json"

# Ensure runtime directories exist
for directory in [DATA_DIR, SCREENSHOTS_DIR, INDEX_DIR, DEMO_DIR, MODELS_DIR, BENCHMARKS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class AppSettings(BaseModel):
    capture_interval_seconds: int = Field(default=30, ge=5, le=3600)
    capture_enabled: bool = Field(default=False)
    excluded_applications: list[str] = Field(
        default_factory=lambda: [
            "Keepass",
            "1Password",
            "Bitwarden",
            "LastPass",
            "Banking",
            "Private Browsing",
            "Incognito",
        ]
    )
    # Search ranking weights
    semantic_weight: float = Field(default=0.65, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    recency_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    # Provider preference: "auto", "qualcomm", "cpu"
    preferred_provider: str = Field(default="auto")
    # OCR preference: "winocr", "local", "auto"
    preferred_ocr: str = Field(default="auto")


settings = AppSettings()
