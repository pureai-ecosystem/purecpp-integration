from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..schemas import SearchResult

class SearchProvider(ABC):
    name: str = "base"

    @abstractmethod
    def search(self, query: str, k: int = 5, *, lang: Optional[str] = None, **kwargs: Any) -> List[SearchResult]:
        ...
