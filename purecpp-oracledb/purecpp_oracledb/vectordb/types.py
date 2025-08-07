from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class QueryResult:
    doc: "Document"
    score: float  # **Smaller = better when the metric is COSINE with `SORT ASC`**
