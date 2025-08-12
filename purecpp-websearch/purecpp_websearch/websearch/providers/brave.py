from __future__ import annotations
from typing import List, Optional, Any, Dict

from ..http import HttpClient
from ..schemas import SearchResult
from ..settings import Settings
from ..exceptions import ConfigError

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

def _clean_params(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None and v != ""}

class BraveProvider:
    name = "brave"

    def __init__(self, settings: Settings) -> None:
        if not settings.brave_api_key:
            raise ConfigError("`BRAVE_API_KEY` not found in the environment..")
        self._http = HttpClient(
            timeout=settings.timeout_s,
            retries=settings.retries,
            headers={
                "X-Subscription-Token": settings.brave_api_key,
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
            },
        )

    def search(
        self,
        query: str,
        k: int = 5,
        *,
        lang: Optional[str] = None,
        ui_lang: Optional[str] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        params: Dict[str, Any] = _clean_params({
            "q": query,
            "count": min(int(k), 20),
            "search_lang": lang or "en",
            "ui_lang": ui_lang or "en-US",
            "country": kwargs.get("country", "US"),
            "safesearch": kwargs.get("safesearch", "moderate"),
            "freshness": kwargs.get("freshness", "pm"),
        })

        data = self._http.get_json(BRAVE_ENDPOINT, params=params)
        web = (data or {}).get("web", {})
        results = []
        for item in web.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description"),
                source="brave",
                score=item.get("page_age"),
                metadata={"brave_raw": item},
            ))
        return results
