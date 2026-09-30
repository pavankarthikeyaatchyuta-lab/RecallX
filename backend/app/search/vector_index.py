import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
import numpy as np

from backend.app.core.config import INDEX_DIR

logger = logging.getLogger("recallx.vector_index")

INDEX_FILE = INDEX_DIR / "vectors.npz"
INDEX_META_FILE = INDEX_DIR / "vectors_meta.json"


class LocalVectorIndex:
    """
    Lightweight, fast, local vector index using normalized NumPy arrays.
    Guarantees pure local execution with zero cloud or external dependencies.
    Tracks model ID and vector dimensions to prevent cross-model vector pollution.
    """

    def __init__(self, model_id: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.model_id = model_id
        self.dimension = dimension
        self._lock = threading.Lock()
        self._ids: list[str] = []
        self._vectors: np.ndarray | None = None  # Shape (N, D)
        self.load()

    def add(self, memory_id: str, vector: list[float]) -> None:
        with self._lock:
            vec_arr = np.array(vector, dtype=np.float32)
            # Ensure unit normalization for exact cosine similarity
            norm = np.linalg.norm(vec_arr)
            if norm > 0:
                vec_arr = vec_arr / norm

            if memory_id in self._ids:
                idx = self._ids.index(memory_id)
                if self._vectors is not None:
                    self._vectors[idx] = vec_arr
            else:
                self._ids.append(memory_id)
                vec_arr = vec_arr.reshape(1, -1)
                if self._vectors is None or len(self._vectors) == 0:
                    self._vectors = vec_arr
                else:
                    self._vectors = np.vstack([self._vectors, vec_arr])

            self.save()

    def add_batch(self, ids: list[str], vectors: list[list[float]]) -> None:
        if not ids:
            return
        with self._lock:
            for memory_id, vec in zip(ids, vectors):
                vec_arr = np.array(vec, dtype=np.float32)
                norm = np.linalg.norm(vec_arr)
                if norm > 0:
                    vec_arr = vec_arr / norm

                if memory_id in self._ids:
                    idx = self._ids.index(memory_id)
                    if self._vectors is not None:
                        self._vectors[idx] = vec_arr
                else:
                    self._ids.append(memory_id)
                    vec_arr = vec_arr.reshape(1, -1)
                    if self._vectors is None or len(self._vectors) == 0:
                        self._vectors = vec_arr
                    else:
                        self._vectors = np.vstack([self._vectors, vec_arr])

            self.save()

    def remove(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id not in self._ids:
                return False
            idx = self._ids.index(memory_id)
            self._ids.pop(idx)
            if self._vectors is not None:
                self._vectors = np.delete(self._vectors, idx, axis=0)
                if len(self._vectors) == 0:
                    self._vectors = None
            self.save()
            return True

    def search(self, query_vector: list[float], top_k: int = 50) -> list[tuple[str, float]]:
        """
        Calculates cosine similarities between query_vector and all indexed memories.
        Returns list of (memory_id, similarity_score).
        """
        with self._lock:
            if self._vectors is None or len(self._vectors) == 0:
                return []

            q = np.array(query_vector, dtype=np.float32)
            norm = np.linalg.norm(q)
            if norm > 0:
                q = q / norm

            # Dot product of normalized vectors = Cosine Similarity (-1 to 1)
            scores = np.dot(self._vectors, q)
            # Clip to [0.0, 1.0] for clean confidence interpretation
            scores = np.clip(scores, 0.0, 1.0)

            top_indices = np.argsort(scores)[::-1][:top_k]
            results = []
            for idx in top_indices:
                results.append((self._ids[idx], float(scores[idx])))
            return results

    def clear(self) -> None:
        with self._lock:
            self._ids = []
            self._vectors = None
            if INDEX_FILE.exists():
                try:
                    INDEX_FILE.unlink()
                except Exception:
                    pass
            if INDEX_META_FILE.exists():
                try:
                    INDEX_META_FILE.unlink()
                except Exception:
                    pass

    def size(self) -> int:
        return len(self._ids)

    def save(self) -> None:
        try:
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            if self._vectors is not None and len(self._vectors) > 0:
                np.savez_compressed(
                    str(INDEX_FILE),
                    ids=np.array(self._ids),
                    vectors=self._vectors,
                )
                meta = {
                    "model_id": self.model_id,
                    "dimension": self.dimension,
                    "normalized": True,
                    "created_at": datetime.now().isoformat(),
                    "total_vectors": len(self._ids),
                }
                with open(INDEX_META_FILE, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
            else:
                if INDEX_FILE.exists():
                    INDEX_FILE.unlink()
                if INDEX_META_FILE.exists():
                    INDEX_META_FILE.unlink()
        except Exception as e:
            logger.error(f"Failed to save vector index: {e}")

    def load(self) -> None:
        if not INDEX_FILE.exists():
            self._ids = []
            self._vectors = None
            return

        # Check metadata compatibility
        if INDEX_META_FILE.exists():
            try:
                with open(INDEX_META_FILE, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                stored_model = meta.get("model_id")
                stored_dim = meta.get("dimension")
                if (stored_model and stored_model != self.model_id) or (
                    stored_dim and stored_dim != self.dimension
                ):
                    print("Embedding model changed. Rebuilding local search index...")
                    logger.warning("Embedding model changed. Rebuilding local search index...")
                    self._ids = []
                    self._vectors = None
                    return
            except Exception:
                pass

        try:
            data = np.load(str(INDEX_FILE), allow_pickle=True)
            self._ids = data["ids"].tolist()
            self._vectors = data["vectors"]
            if self._vectors is not None and len(self._vectors) > 0:
                actual_dim = self._vectors.shape[-1]
                if actual_dim != self.dimension:
                    print("Embedding model changed. Rebuilding local search index...")
                    logger.warning("Embedding model changed. Rebuilding local search index...")
                    self._ids = []
                    self._vectors = None
        except Exception as e:
            logger.error(f"Vector index corrupted or invalid: {e}")
            self._ids = []
            self._vectors = None

    def rebuild_from_memories(
        self,
        memories: list[Any],
        embed_fn: Callable[[str], tuple[list[float], float]],
        model_id: str,
        dimension: int,
    ) -> int:
        """
        Safely rebuilds the local vector index from database memories when model/dimension changes.
        """
        with self._lock:
            self.model_id = model_id
            self.dimension = dimension
            self._ids = []
            self._vectors = None

            for mem in memories:
                # Construct indexable string
                app = getattr(mem, "application_name", "")
                title = getattr(mem, "window_title", "")
                text = getattr(mem, "extracted_text", "")
                mem_id = getattr(mem, "id")
                indexable_content = f"{app} - {title}\n{text}"
                vec, _ = embed_fn(indexable_content)

                vec_arr = np.array(vec, dtype=np.float32)
                norm = np.linalg.norm(vec_arr)
                if norm > 0:
                    vec_arr = vec_arr / norm

                self._ids.append(mem_id)
                vec_arr = vec_arr.reshape(1, -1)
                if self._vectors is None or len(self._vectors) == 0:
                    self._vectors = vec_arr
                else:
                    self._vectors = np.vstack([self._vectors, vec_arr])

            self.save()
            return len(self._ids)


vector_index = LocalVectorIndex()
