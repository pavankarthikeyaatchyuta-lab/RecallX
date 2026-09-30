import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.app.core.config import SCREENSHOTS_DIR
from backend.app.embeddings.manager import model_manager
from backend.app.models.schemas import Memory
from backend.app.search.vector_index import vector_index
from backend.app.storage.database import (
    count_memories,
    delete_all_memories as db_delete_all,
    delete_memory as db_delete_memory,
    get_memory,
    get_unique_applications,
    insert_memory,
    list_memories,
)


class MemoryService:
    def create_memory(
        self,
        screenshot_path: str,
        extracted_text: str,
        application_name: str,
        window_title: str,
        ocr_latency_ms: float = 0.0,
        ocr_status: str = "ok",
        is_demo: bool = False,
        custom_id: Optional[str] = None,
        custom_timestamp: Optional[float] = None,
    ) -> Memory:
        mem_id = custom_id or f"mem_{uuid.uuid4().hex[:12]}"
        ts = custom_timestamp or time.time()
        iso_ts = datetime.fromtimestamp(ts).isoformat()
        now_str = datetime.now().isoformat()

        # Combine title, app, and OCR text for richer semantic indexing
        indexable_content = f"{application_name} - {window_title}\n{extracted_text}"
        vector, emb_latency_ms = model_manager.embed_text(indexable_content)

        # Store vector in local vector index
        vector_index.add(mem_id, vector)

        memory = Memory(
            id=mem_id,
            timestamp=ts,
            iso_timestamp=iso_ts,
            screenshot_path=screenshot_path,
            extracted_text=extracted_text,
            application_name=application_name,
            window_title=window_title,
            ocr_latency_ms=ocr_latency_ms,
            embedding_latency_ms=emb_latency_ms,
            ocr_status=ocr_status,
            is_demo=is_demo,
            created_at=now_str,
        )

        insert_memory(memory)
        return memory

    def get_by_id(self, memory_id: str) -> Optional[Memory]:
        return get_memory(memory_id)

    def list_memories(
        self,
        limit: int = 50,
        offset: int = 0,
        app: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[Memory]:
        return list_memories(
            limit=limit,
            offset=offset,
            app=app,
            date_from=date_from,
            date_to=date_to,
        )

    def total_count(self) -> int:
        return count_memories()

    def get_apps(self) -> list[str]:
        return get_unique_applications()

    def delete(self, memory_id: str) -> bool:
        mem = get_memory(memory_id)
        if not mem:
            return False

        # Remove screenshot image if exists (safely contained in SCREENSHOTS_DIR)
        try:
            filename = Path(mem.screenshot_path).name
            if filename:
                target_path = (SCREENSHOTS_DIR / filename).resolve()
                if target_path.parent == SCREENSHOTS_DIR.resolve() and target_path.exists():
                    target_path.unlink()
        except Exception:
            pass

        # Remove from vector index
        vector_index.remove(memory_id)

        # Remove from database
        return db_delete_memory(memory_id)

    def delete_all(self) -> int:
        # Clear vector index
        vector_index.clear()

        # Delete screenshot files
        try:
            for file in SCREENSHOTS_DIR.glob("*.png"):
                try:
                    file.unlink()
                except Exception:
                    pass
        except Exception:
            pass

        # Clear database
        return db_delete_all()

    def sync_or_rebuild_index_if_needed(self) -> None:
        """Ensures vector index matches active embedding model and database state."""
        active_model = model_manager.active_provider.name
        active_dim = model_manager.active_provider.dimension
        memories = list_memories(limit=10000, offset=0)
        if len(memories) > 0 and vector_index.size() == 0:
            vector_index.rebuild_from_memories(
                memories=memories,
                embed_fn=model_manager.embed_text,
                model_id=active_model,
                dimension=active_dim,
            )


memory_service = MemoryService()
