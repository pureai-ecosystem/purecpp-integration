from __future__ import annotations
from typing import List
import numpy as np
from .base import Embedder

class DummyEmbedder(Embedder):
    def __init__(self, dim: int):
        self.dim = dim
    def embed(self, texts: List[str]) -> List[List[float]]:
        out = []
        for t in texts:
            rng = np.random.default_rng(abs(hash(t)) % (2**32))
            out.append(rng.standard_normal(self.dim).astype("f4").tolist())
        return out