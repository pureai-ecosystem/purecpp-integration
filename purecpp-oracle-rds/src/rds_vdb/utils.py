from __future__ import annotations
import numpy as np
from typing import List



def pack_f32(vec: List[float]) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes(order="C")

def unpack_f32(buf: bytes) -> np.ndarray:
    return np.frombuffer(buf, dtype=np.float32)

def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-12
    return 1.0 - float(a.dot(b) / denom)