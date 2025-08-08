from __future__ import annotations


class WebSearchError(Exception):
    """Base error for the websearch module."""


# --- Cleaners ---
class CleanerError(WebSearchError):
    """Generic cleaner error."""


class UnsupportedMimeError(CleanerError):
    """MIME type not supported by the cleaner."""


class DependencyNotInstalled(CleanerError):
    """Optional dependency not installed (e.g., bs4, markdownify, lxml)."""


# --- Providers / Fetchers (optional, useful for pipeline) ---
class ProviderError(WebSearchError):
    """Failed to query the search provider."""


class FetchError(WebSearchError):
    """Failed to download HTML content."""


class ConfigError(WebSearchError):
    """Invalid configuration (e.g., missing API key)."""