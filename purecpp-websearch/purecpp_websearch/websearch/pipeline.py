from __future__ import annotations
from typing import List, Optional, Type, Any, Dict

from .schemas import SearchResult, Document, Documents, Results
from .settings import Settings
from .router import CleanerRouter
from .fetchers.http_fetcher import HttpFetcher
from .providers.base import SearchProvider
from .providers.brave import BraveProvider
from .cleaners.base import ICleaner
from .output import build_search_response  

class WebSearch:
    """Pluggable pipeline: provider → fetch → cleaner."""

    def __init__(self, provider: str = "brave", cleaner: str = "simple", settings: Settings | None = None):
        self.settings = settings or Settings.from_env()
        self.cleaner_name = cleaner

        self._providers: dict[str, Type[SearchProvider]] = {
            "brave": BraveProvider,
        }
        self._provider = self._providers[provider](self.settings)

        self._fetcher = HttpFetcher(self.settings)
        self._cleaners = CleanerRouter()
        self._cleaner: ICleaner = self._cleaners.create(cleaner)

    def search(self, query: str, k: int = 5, **kwargs) -> Results:
        return self._provider.search(query, k=k, **kwargs)

    def read(self, url: str, *, mime: str = "text/html") -> Document:
        html = self._fetcher.fetch_html(url)
        md = self._cleaner.to_markdown(html, mime)
        return Document(url=url, content=md, raw_html=html, mime=mime)

    def search_and_read(self, query: str, k: int = 3, *, mime: str = "text/html", **kwargs) -> Documents:
        results = self.search(query, k=k, **kwargs)
        docs: Documents = []
        for r in results:
            try:
                doc = self.read(r.url, mime=mime)
                doc.title = r.title
                docs.append(doc)
            except Exception as e:
                print(f"[WebSearch] Failed to read '{r.url}': {e}")
                continue
        return docs

    def search_and_read_structured(
        self,
        query: str,
        k: int = 3,
        *,
        mime: str = "text/html",
        include_raw_html: bool = False,
        schema: str = "langchain",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        
        Executes search → fetch → clean and returns structured JSON:
        {
          "query": ...,
          "provider": ...,
          "params": {...},
          "results": [...],
          "documents": [{"page_content": "<markdown>", "metadata": {...}}, ...]
        }

        """
        # 1) Search (keeps the kwargs to log the parameters used)
        results = self.search(query, k=k, **kwargs)

        # 2) Fetching + cleaning
        docs: Documents = []
        for r in results:
            try:
                d = self.read(r.url, mime=mime)
                d.title = r.title
                docs.append(d)
            except Exception as e:
                print(f"[WebSearch] Failed to read '{r.url}': {e}")
                continue

        #3) Build payload**
        params: Dict[str, Any] = {"k": k, "mime": mime}
        params.update(kwargs or {})
        return build_search_response(
            query=query,
            provider=getattr(self._provider, "name", type(self._provider).__name__),
            params=params,
            results=results,
            documents=docs,
            include_raw_html=include_raw_html,
            schema=schema,
        )
