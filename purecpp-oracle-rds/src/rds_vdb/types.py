from __future__ import annotations
from dataclasses import dataclass

@dataclass
class QueryResult:
    doc: "Document" 
    score: float     