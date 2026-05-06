from .base import BaseAIBackend
from .mock import MockAIBackend
from .deepseek import DeepSeekBackend

__all__ = ["BaseAIBackend", "MockAIBackend", "DeepSeekBackend"]

_registry = {
    "mock": MockAIBackend,
    "deepseek": DeepSeekBackend,
}


def get_backend(name: str = "mock") -> BaseAIBackend:
    backend_cls = _registry.get(name)
    if backend_cls is None:
        raise ValueError(f"Unknown AI backend: {name}. Available: {list(_registry.keys())}")
    return backend_cls()
