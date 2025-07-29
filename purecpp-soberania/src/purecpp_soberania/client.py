# src/purecpp/soberania/client.py
from __future__ import annotations

import json
import os
from typing import AsyncIterator, Iterator, Optional, Dict, Any, List, Tuple

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt

from .schemas import ChatRequest, ChatResponse
from .exceptions import SoberanoHTTPError

DEFAULT_BASE_URL = ""


def _extract_token(obj: Dict[str, Any]) -> Optional[str]:
    """Extract the delta.content"""
    try:
        choice = obj["choices"][0]
        delta = choice.get("delta") or {}
        return delta.get("content")
    except (KeyError, IndexError, TypeError):
        return None


def _pluck_json_objects(buf: str) -> Tuple[List[str], str]:
    """
    Returns (complete_jsons, incomplete_remainder) from the buffer.
    Uses brace counting to detect complete JSON objects.
    """
    objs: List[str] = []
    depth = 0
    start = -1

    for i, ch in enumerate(buf):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                objs.append(buf[start : i + 1])
                start = -1

    if depth == 0:
        return objs, ""  
    remainder = buf[start:] if start != -1 else buf
    return objs, remainder


class SoberanoClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        client: Optional[httpx.Client] = None,
    ):
        self.api_key = api_key or os.getenv("SOBERANO_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided. Set SOBERANO_API_KEY or pass api_key.")
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = client or httpx.Client(timeout=timeout)

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    def chat(self, req: ChatRequest) -> ChatResponse:
        url = f"{self.base_url}/api/v1/chat/completions"
        r = self._client.post(url, json=req.model_dump(), headers=self._headers())
        if r.status_code >= 400:
            raise SoberanoHTTPError(r.status_code, r.text)
        return ChatResponse.model_validate(r.json())

    def stream(self, req: ChatRequest) -> Iterator[str]:
        """Generates tokens as they arrive via JSON stream.."""
        stream_req = req.model_copy(update={"stream": True})
        url = f"{self.base_url}/api/v1/chat/completions"

        with self._client.stream("POST", url, json=stream_req.model_dump(), headers=self._headers()) as r:
            if r.status_code >= 400:
                raise SoberanoHTTPError(r.status_code, r.text)

            buffer = ""
            for chunk in r.iter_bytes():
                if not chunk:
                    continue
                buffer += chunk.decode("utf-8", errors="ignore")

                objs, buffer = _pluck_json_objects(buffer)
                for obj_str in objs:
                    try:
                        obj = json.loads(obj_str)
                    except json.JSONDecodeError:
                        continue
                    token = _extract_token(obj)
                    if token:
                        yield token
                    if obj.get("choices", [{}])[0].get("finish_reason"):
                        return


class AsyncSoberanoClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key or os.getenv("SOBERANO_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided. Set SOBERANO_API_KEY or pass api_key.")
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = client or httpx.AsyncClient(timeout=timeout)

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def chat(self, req: ChatRequest) -> ChatResponse:
        url = f"{self.base_url}/api/v1/chat/completions"
        r = await self._client.post(url, json=req.model_dump(), headers=self._headers())
        if r.status_code >= 400:
            raise SoberanoHTTPError(r.status_code, r.text)
        return ChatResponse.model_validate(r.json())

    async def stream(self, req: ChatRequest) -> AsyncIterator[str]:
        stream_req = req.model_copy(update={"stream": True})
        url = f"{self.base_url}/api/v1/chat/completions"

        async with self._client.stream("POST", url, json=stream_req.model_dump(), headers=self._headers()) as r:
            if r.status_code >= 400:
                raise SoberanoHTTPError(r.status_code, await r.text())

            buffer = ""
            async for chunk in r.aiter_bytes():
                if not chunk:
                    continue
                buffer += chunk.decode("utf-8", errors="ignore")

                objs, buffer = _pluck_json_objects(buffer)
                for obj_str in objs:
                    try:
                        obj = json.loads(obj_str)
                    except json.JSONDecodeError:
                        continue
                    token = _extract_token(obj)
                    if token:
                        yield token
                    if obj.get("choices", [{}])[0].get("finish_reason"):
                        return
