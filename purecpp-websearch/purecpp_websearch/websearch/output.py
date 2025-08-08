from __future__ import annotations
from typing import Any, Dict, List, Optional
from .schemas import Results, Documents, SearchResult, Document

def to_langchain_results(results: Results) -> List[Dict[str, Any]]:
    """
    Converts SearchResult[] into a list of simple dicts compatible with search tools:
    [
  {"title": "...", "url": "...", "content": "snippet...", "score": 0.9, "source": "brave", "metadata": {...}},
  ...
    ]
    """
    out: List[Dict[str, Any]] = []
    for r in results:
        out.append({
            "title": r.title,
            "url": r.url,
            "content": r.snippet or "",
            "score": r.score,
            "source": r.source,
            "metadata": r.metadata or {},
        })
    return out

def to_langchain_docs(docs: Documents, *, include_raw_html: bool = False) -> List[Dict[str, Any]]:
    """
    Converts Document[] into a list of LangChain Document-like objects:
    [
  {"page_content": "<markdown>", "metadata": {"title": "...", "url": "...", "mime": "...", ...}},
  ...
    ]   
    It always returns the content in MARKDOWN (since it comes directly from the cleaner).
    """
    out: List[Dict[str, Any]] = []
    for d in docs:
        md = d.content or ""  # markdown cleaner
        meta: Dict[str, Any] = {
            "title": d.title,
            "url": d.url,
            "mime": d.mime,
        }
        if d.meta:
            meta.update(d.meta)
        if include_raw_html and d.raw_html:
            meta["raw_html"] = d.raw_html
        out.append({
            "page_content": md,
            "metadata": meta,
        })
    return out

def build_search_response(
    *,
    query: str,
    provider: str,
    params: Dict[str, Any],
    results: Results,
    documents: Documents,
    include_raw_html: bool = False,
    schema: str = "langchain",
) -> Dict[str, Any]:
    """
    Builds a complete, LangChain-style response payload, including a results block.

    Structure:
    {
    "query": "...",
    "provider": "brave",
    "params": {...},
    "results": [ {title, url, content, score, source, metadata}, ... ],
    "documents": [ {page_content, metadata{title,url,mime,...}}, ... ]
    }
    """
    if schema != "langchain":
        raise ValueError(f"Unknown schema:: {schema}")

    return {
        "query": query,
        "provider": provider,
        "params": params,
        "results": to_langchain_results(results),
        "documents": to_langchain_docs(documents, include_raw_html=include_raw_html),
    }
