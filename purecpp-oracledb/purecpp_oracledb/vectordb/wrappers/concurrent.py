from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from ..backend import VectorBackend  
from ..document import Document
from ..types import QueryResult
import threading

class ConcurrentSearchWrapper(VectorBackend):
    def __init__(self, backend: VectorBackend, max_workers: int | None = None,
                 backend_thread_safe: bool = True) -> None:
        self._backend = backend
        self._pool = ThreadPoolExecutor(max_workers=max_workers or None)
        self._backend_thread_safe = backend_thread_safe
        self._lock = threading.Lock()  # Serialize when necessary.
        self.dim = backend.dim

    def is_open(self) -> bool:
        return self._backend.is_open()

    def insert(self, docs: List[Document]) -> None:
        # Inserts are always serialized (they mutate state).**
        with self._lock:
            self._backend.insert(docs)

    def query(self, embedding: List[float], k: int, filter: Optional[Dict[str, str]] = None) -> List[QueryResult]:
        if not self._backend_thread_safe:
            with self._lock:
                return self._backend.query(embedding, k, filter)
        return self._backend.query(embedding, k, filter)

    def query_many(self, embeddings: List[List[float]], k: int = 5,
                   filter: Optional[Dict[str, str]] = None,
                   raise_on_err: bool = False) -> List[List[QueryResult]]:
        futures = []
        for e in embeddings:
            futures.append(self._pool.submit(self.query, e, k, filter))
        out = [[] for _ in range(len(futures))]
        for i, f in enumerate(futures):
            try:
                out[i] = f.result()
            except Exception:
                if raise_on_err:
                    raise
                out[i] = []
        return out

    def close(self) -> None:
        with self._lock:
            try:
                self._backend.close()
            finally:
                self._pool.shutdown(wait=True)
