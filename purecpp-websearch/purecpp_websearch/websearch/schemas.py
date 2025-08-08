from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = None

@dataclass
class Document:
    url: str
    content: str           
    title: Optional[str] = None
    mime: str = "text/html"
    raw_html: Optional[str] = None
    meta: Dict[str, Any] = None

Results = List[SearchResult]
Documents = List[Document]
