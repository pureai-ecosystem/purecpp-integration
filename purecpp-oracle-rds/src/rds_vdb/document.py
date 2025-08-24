from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import json

@dataclass
class Document:
    page_content: str
    embedding: List[float]
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def dim(self) -> int:
        return len(self.embedding)

    def to_json(self) -> str:
        return json.dumps({"page_content": self.page_content, "metadata": self.metadata})

    @staticmethod
    def from_json(s: str) -> "Document":
        obj = json.loads(s)
        return Document(page_content=obj.get("page_content", ""), embedding=[], metadata=obj.get("metadata", {}))