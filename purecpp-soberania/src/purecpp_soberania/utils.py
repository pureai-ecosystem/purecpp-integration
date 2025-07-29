# src/soberano_client/utils.py
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, List, Optional, Union

from .schemas import Message, ChatRequest


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> str:
    val = os.getenv(key, default)
    if required and not val:
        raise ValueError(f"Environment variable {key} is required.")
    return val

def normalize_messages(
    messages: Union[str, Dict[str, str], Message, Iterable[Union[Message, Dict[str, str]]]]
) -> List[Message]:
    """
    Aceita:
      - string -> vira user message
      - dict {"role": "...", "content": "..."}
      - Message
      - iterável de Message ou dict
    Retorna sempre List[Message].
    """
    if isinstance(messages, str):
        return [Message(role="user", content=messages)]

    if isinstance(messages, Message):
        return [messages]

    if isinstance(messages, dict):
        return [Message(**messages)]

    out: List[Message] = []
    for m in messages:
        if isinstance(m, Message):
            out.append(m)
        elif isinstance(m, dict):
            out.append(Message(**m))
        else:
            raise TypeError(f"Unsupported message type: {type(m)}")
    return out


def build_chat_request(
    messages: Union[str, Dict[str, str], Message, Iterable[Union[Message, Dict[str, str]]]],
    **params: Any
) -> ChatRequest:
    """Creates a normalized ChatRequest"""
    return ChatRequest(messages=normalize_messages(messages), **params)


def iter_jsonl(lines: Iterable[bytes]) -> Iterator[Dict[str, Any]]:
    """
    Iterates over JSONL lines (each line is a complete JSON).
    """
    for raw in lines:
        if not raw:
            continue
        try:
            yield json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            continue


def iter_sse(lines: Iterable[bytes]) -> Iterator[str]:
    """
    Iterates over Server-Sent Event lines starting with 'data:'.
    Returns the content after 'data:' (string).
    """
    for raw in lines:
        if not raw:
            continue
        line = raw.decode("utf-8").strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if chunk == "[DONE]":
            break
        yield chunk

def extract_text_from_stream_chunk(chunk: Union[str, Dict[str, Any]]) -> Optional[str]:
    """
    Attempts to extract text from a chunk coming from the stream.
    Adjust according to the actual format
    """
    if isinstance(chunk, str):
        return chunk

    if "choices" in chunk:
        choice = chunk["choices"][0]
        delta = choice.get("delta") or choice.get("message")
        if delta and "content" in delta:
            return delta["content"]

        if "text" in choice:
            return choice["text"]
    # fallback
    return None


def safe_json_loads(s: str) -> Optional[Any]:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


@contextmanager
def timer(name: str = "block"):
    """Simple runtime timer."""
    start = time.perf_counter()
    try:
        yield
    finally:
        dur = (time.perf_counter() - start) * 1000
        print(f"[{name}] {dur:.2f} ms")

def redact_key(s: str, keep_last: int = 4) -> str:
    """Masks an API key for logs.."""
    if not s:
        return ""
    return "*" * max(0, len(s) - keep_last) + s[-keep_last:]

def merge_dicts(base: Dict[str, Any], override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Shallow merge"""
    if not override:
        return dict(base)
    out = dict(base)
    out.update(override)
    return out
