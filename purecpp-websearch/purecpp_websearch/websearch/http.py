from __future__ import annotations
import httpx
from typing import Any, Dict

class HttpClient:
    def __init__(self, timeout: float = 20.0, retries: int = 2, headers: Dict[str, str] | None = None):
        self._timeout = timeout
        self._retries = retries
        self._headers = headers or {}

    def get_json(self, url: str, headers: Dict[str, str] | None = None, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        h = {**self._headers, **(headers or {})}
        last_exc = None
        for _ in range(self._retries + 1):
            try:
                r = httpx.get(url, headers=h, params=params, timeout=self._timeout)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_exc = e
        raise last_exc  # type: ignore[misc]

    def get_text(self, url: str, headers: Dict[str, str] | None = None) -> str:
        h = {**self._headers, **(headers or {})}
        last_exc = None
        for _ in range(self._retries + 1):
            try:
                r = httpx.get(url, headers=h, timeout=self._timeout)
                r.raise_for_status()
                return r.text
            except Exception as e:
                last_exc = e
        raise last_exc  # type: ignore[misc]
