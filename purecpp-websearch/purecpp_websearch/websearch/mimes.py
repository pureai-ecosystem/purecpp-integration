from __future__ import annotations
from enum import Enum


class Mime(Enum):
    TEXT_HTML = "text/html"
    TEXT_PLAIN = "text/plain"
    APPLICATION_XML = "application/xml"
    APPLICATION_XHTML = "application/xhtml+xml"

    @classmethod
    def from_string(cls, value: str) -> "Mime | None":
        """Normalizes a MIME string to a known enum or None.."""
        if not value:
            return None
        v = value.split(";", 1)[0].strip().lower()
        for m in cls:
            if m.value == v:
                return m
        return None
