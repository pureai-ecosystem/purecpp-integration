from __future__ import annotations
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from .base import Embedder

class HuggingFaceEmbedder(Embedder):
    """Embedder based on Sentence-Transformers (Hugging Face).
        Examples:

        * `'sentence-transformers/all-MiniLM-L6-v2'` (dim=384)
        * `'intfloat/multilingual-e5-base'` (dim=768)

    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: Optional[str] = None, normalize: bool = True):
        self.model = SentenceTransformer(model_name, device=device)
        self.normalize = normalize
        self.dim = int(self.model.get_sentence_embedding_dimension())
    def embed(self, texts: List[str]) -> List[List[float]]:
        vecs = self.model.encode(texts, normalize_embeddings=self.normalize, convert_to_numpy=True)
        return vecs.astype(np.float32).tolist()