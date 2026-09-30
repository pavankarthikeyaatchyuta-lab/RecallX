import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes import router
from backend.app.core.config import BASE_DIR, DATA_DIR, SCREENSHOTS_DIR
from backend.app.embeddings.manager import model_manager
from backend.app.services.capture_service import capture_service
from backend.app.services.memory_service import memory_service
from backend.app.storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    # Ensure vector index matches active embedding model
    try:
        memory_service.sync_or_rebuild_index_if_needed()
    except Exception:
        pass
    # Warm up local embedding model weights for zero first-query latency
    try:
        model_manager.warmup()
    except Exception:
        pass
    yield
    # Gracefully terminate background capture loop on application exit
    try:
        capture_service.shutdown()
    except Exception:
        pass


app = FastAPI(
    title="RecallX Local AI Engine",
    description="Privacy-first, local-first visual memory application for Windows & Snapdragon PCs.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware restricted to local development origins
LOCAL_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount screenshots directory for image previewing
app.mount("/data/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")

# Include API routes
app.include_router(router, prefix="/api")

# Mount frontend production build if available
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    init_db()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
