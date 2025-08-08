from ..http import HttpClient
from ..settings import Settings

class HttpFetcher:
    def __init__(self, settings: Settings):
        self._http = HttpClient(timeout=settings.timeout_s, retries=settings.retries, headers={
            "User-Agent": settings.user_agent
        })

    def fetch_html(self, url: str) -> str:
        return self._http.get_text(url)
