from abc import ABC, abstractmethod
from typing import Any


class BaseAIBackend(ABC):

    @abstractmethod
    def generate_script(self, topic: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def generate_image(self, prompt: str, index: int) -> dict[str, Any]:
        ...

    @abstractmethod
    def generate_video(self, scenes: list[dict], images: list[dict]) -> dict[str, Any]:
        ...
