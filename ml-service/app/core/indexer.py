import threading
import numpy as np
from typing import List, Dict, Any, Optional
from app.schemas.models import VectorSearchItem

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

class VectorIndexManager:
    """
    Manages vector indices with cosine similarity and collection isolation.
    Uses FAISS IndexFlatIP when available; falls back seamlessly to NumPy exact
    inner product on platforms where FAISS native binaries are unavailable.
    """

    def __init__(self, dimension: int = 512):
        self.dimension = dimension
        self.lock = threading.Lock()
        self.faiss_indices: Dict[str, Any] = {}
        self.numpy_matrices: Dict[str, np.ndarray] = {}
        self.id_maps: Dict[str, List[str]] = {}
        self.metadata_maps: Dict[str, Dict[str, Any]] = {}

    def _ensure_collection(self, collection: str):
        if collection not in self.id_maps:
            self.id_maps[collection] = []
            self.metadata_maps[collection] = {}
            if HAS_FAISS:
                self.faiss_indices[collection] = faiss.IndexFlatIP(self.dimension)
            else:
                self.numpy_matrices[collection] = np.empty((0, self.dimension), dtype=np.float32)

    def index_vectors(self, collection: str, items: List[Dict[str, Any]]) -> int:
        if not items:
            return 0

        with self.lock:
            self._ensure_collection(collection)
            vectors = []
            valid_ids = []

            for item in items:
                v = np.array(item['vector'], dtype=np.float32)
                norm = np.linalg.norm(v)
                if norm > 0:
                    v = v / norm
                vectors.append(v)
                valid_ids.append(item['id'])
                if 'metadata' in item and item['metadata'] is not None:
                    self.metadata_maps[collection][item['id']] = item['metadata']

            matrix = np.vstack(vectors).astype(np.float32)

            if HAS_FAISS:
                self.faiss_indices[collection].add(matrix)
            else:
                self.numpy_matrices[collection] = np.vstack([self.numpy_matrices[collection], matrix])

            self.id_maps[collection].extend(valid_ids)
            return len(valid_ids)

    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        threshold: float = 0.55
    ) -> List[VectorSearchItem]:
        with self.lock:
            self._ensure_collection(collection)
            total = len(self.id_maps[collection])
            if total == 0:
                return []

            qv = np.array(query_vector, dtype=np.float32).reshape(1, -1)
            norm = np.linalg.norm(qv)
            if norm > 0:
                qv = qv / norm

            k = min(top_k, total)

            if HAS_FAISS:
                scores, indices = self.faiss_indices[collection].search(qv, k)
                scores_arr = scores[0]
                indices_arr = indices[0]
            else:
                # Exact cosine similarity via inner product of normalized vectors
                sims = np.dot(self.numpy_matrices[collection], qv.T).flatten()
                # Top k indices
                sorted_idx = np.argsort(-sims)[:k]
                scores_arr = sims[sorted_idx]
                indices_arr = sorted_idx

            results: List[VectorSearchItem] = []
            for score, idx in zip(scores_arr, indices_arr):
                if idx < 0 or idx >= len(self.id_maps[collection]):
                    continue
                score_float = float(score)
                if score_float >= threshold:
                    item_id = self.id_maps[collection][idx]
                    meta = self.metadata_maps[collection].get(item_id)
                    results.append(
                        VectorSearchItem(
                            id=item_id,
                            score=round(score_float, 4),
                            metadata=meta
                        )
                    )

            return results

    def clear(self, collection: str):
        with self.lock:
            self.id_maps[collection] = []
            self.metadata_maps[collection] = {}
            if HAS_FAISS:
                self.faiss_indices[collection] = faiss.IndexFlatIP(self.dimension)
            else:
                self.numpy_matrices[collection] = np.empty((0, self.dimension), dtype=np.float32)

    def get_count(self, collection: str) -> int:
        with self.lock:
            if collection in self.id_maps:
                return len(self.id_maps[collection])
            return 0

vector_manager = VectorIndexManager(dimension=512)
