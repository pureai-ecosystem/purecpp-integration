from __future__ import annotations
import re


_WHITESPACE_RE = re.compile(r"[ \t\f\v]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    text = _WHITESPACE_RE.sub(" ", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip()
