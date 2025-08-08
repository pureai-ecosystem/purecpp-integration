from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass
class Settings:
    brave_api_key: str | None = None
    timeout_s: float = 20.0
    retries: int = 2
    user_agent: str = "purecpp-websearch/0.1"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            brave_api_key=os.getenv("BRAVE_API_KEY"),
            timeout_s=float(os.getenv("WEBSEARCH_TIMEOUT", "20")),
            retries=int(os.getenv("WEBSEARCH_RETRIES", "2")),
            user_agent=os.getenv("WEBSEARCH_UA", "purecpp-websearch/0.1"),
        )
