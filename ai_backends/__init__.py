from .base import BaseAIBackend
from .mock import MockAIBackend

__all__ = ["BaseAIBackend", "MockAIBackend"]

_registry = {"mock": MockAIBackend}


def get_backend(name: str = "mock") -> BaseAIBackend:
    backend_cls = _registry.get(name)
    if backend_cls is None:
        raise ValueError(f"Unknown AI backend: {name}. Available: {list(_registry.keys())}")
    return backend_cls()
