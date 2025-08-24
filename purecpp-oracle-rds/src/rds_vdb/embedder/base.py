from __future__ import annotations
from typing import List

class Embedder:
    dim: int
    def embed(self, texts: List[str]) -> List[List[float]]: ...