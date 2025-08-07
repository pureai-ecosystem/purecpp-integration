from .document import Document
from .types import QueryResult
from .backend import VectorBackend
from .exceptions import *
from .registry import Registry
from .wrappers.concurrent import ConcurrentSearchWrapper
from .wrappers.metrics import MetricsWrapper, CallStats

from .backends import oracle_backend as _oracle_backend  

def make_backend(name: str, cfg: dict) -> VectorBackend:
    return Registry.make(name, cfg)

def list_backends():
    return Registry.list()
