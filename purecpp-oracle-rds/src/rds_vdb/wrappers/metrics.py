from __future__ import annotations
import json, math, time, threading
from typing import Dict
from ..backend import VectorBackend

class CallStats:
    __slots__ = ("calls", "errors", "total", "min_t", "max_t")
    def __init__(self) -> None:
        self.calls = 0; self.errors = 0; self.total = 0.0
        self.min_t = math.inf; self.max_t = 0.0
    def observe(self, elapsed: float, ok: bool) -> None:
        self.calls += 1; self.errors += (0 if ok else 1)
        self.total += elapsed; self.min_t = min(self.min_t, elapsed); self.max_t = max(self.max_t, elapsed)

class MetricsWrapper(VectorBackend):
    def __init__(self, backend: VectorBackend, namespace: str = "vdb") -> None:
        self._backend = backend; self._ns = namespace; self._stats: Dict[str, CallStats] = {}; self._lock = threading.Lock(); self.dim = backend.dim
    def _measure(self, method: str, fn, *args, **kwargs):
        t0 = time.perf_counter(); ok = True
        try:
            return fn(*args, **kwargs)
        except Exception:
            ok = False; raise
        finally:
            dt = time.perf_counter() - t0
            with self._lock:
                s = self._stats.setdefault(method, CallStats()); s.observe(dt, ok)
    def is_open(self) -> bool: return self._measure("is_open", self._backend.is_open)
    def insert(self, docs): return self._measure("insert", self._backend.insert, docs)
    def query(self, embedding, k, filter=None): return self._measure("query", self._backend.query, embedding, k, filter)
    def close(self) -> None: return self._measure("close", self._backend.close)
    def snapshot(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            out = {}
            for k, s in self._stats.items():
                out[k] = {"calls": s.calls, "errors": s.errors, "total": s.total, "min": None if math.isinf(s.min_t) else s.min_t, "max": s.max_t, "avg": 0.0 if s.calls == 0 else (s.total/s.calls)}
            return out
    def snapshot_json(self, indent: int = 2) -> str: return json.dumps(self.snapshot(), indent=indent)
    def reset(self) -> None:
        with self._lock: self._stats.clear()