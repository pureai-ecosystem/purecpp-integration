from __future__ import annotations
from typing import Callable, Dict, List, TYPE_CHECKING
from .exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from .backend import VectorBackend  

Factory = Callable[[dict], "VectorBackend"]

class Registry:
    _factories: Dict[str, Factory] = {}

    @classmethod
    def register_backend(cls, name: str, factory: Factory, allow_override: bool = False) -> None:
        key = name.lower()
        if not allow_override and key in cls._factories:
            raise InvalidConfiguration(f"backend '{key}' Already registered.")
        cls._factories[key] = factory

    @classmethod
    def make(cls, name: str, cfg: dict) -> "VectorBackend":
        key = name.lower()
        try:
            return cls._factories[key](cfg)
        except KeyError:
            raise InvalidConfiguration(f"backend '{name}' not found")

    @classmethod
    def list(cls) -> List[str]:
        return sorted(cls._factories.keys())
