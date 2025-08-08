from __future__ import annotations
from typing import Dict, Type, Optional, Iterable

from .cleaners.base import ICleaner
from .cleaners.simple import SimpleCleaner


class CleanerRouter:
    """Simple registry/factory for cleaners."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[ICleaner]] = {}
        self.register("simple", SimpleCleaner)

    def register(self, name: str, cls: Type[ICleaner]) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("**Cleaner name cannot be empty.**.")
        if not issubclass(cls, ICleaner):
            raise TypeError(f"{cls!r} **is not a subclass of ICleaner**")
        self._registry[key] = cls

    def create(self, name: Optional[str] = None) -> ICleaner:
        key = (name or "simple").strip().lower()
        try:
            cls = self._registry[key]
        except KeyError as e:
            raise ValueError(f"Cleaner '{name}' não registrado") from e
        return cls()

    def registered(self) -> Iterable[str]:
        return tuple(self._registry.keys())


def register_readability(router: CleanerRouter) -> None:
    try:
        from .cleaners.readability import ReadabilityCleaner  
    except Exception:
        return
    router.register("readability", ReadabilityCleaner)
