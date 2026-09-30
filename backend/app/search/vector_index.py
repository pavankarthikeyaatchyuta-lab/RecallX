import threading
from pathlib import Path
import numpy as np

from backend.app.core.config import INDEX_DIR

INDEX_FILE = INDEX_DIR / "vectors.npz"


class LocalVectorIndex:
    """
    Lightweight, fast, local vector index using normalized NumPy arrays.
    Guarantees pure local execution with zero cloud or external dependencies.
    """

    def __init__(self, dimension: int = 384):
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

    def size(self) -> int:
        return len(self._ids)

    def save(self) -> None:
        try:
            if self._vectors is not None and len(self._vectors) > 0:
                np.savez_compressed(
                    str(INDEX_FILE),
                    ids=np.array(self._ids),
                    vectors=self._vectors,
                )
            elif INDEX_FILE.exists():
                INDEX_FILE.unlink()
        except Exception:
            pass

    def load(self) -> None:
        if INDEX_FILE.exists():
            try:
                data = np.load(str(INDEX_FILE), allow_pickle=True)
                self._ids = data["ids"].tolist()
                self._vectors = data["vectors"]
            except Exception:
                self._ids = []
                self._vectors = None


vector_index = LocalVectorIndex()
