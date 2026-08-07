"""Abstract base for RViz backends (mock + live)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseBackend(ABC):
    """Shared interface for MockBackend and LiveBackend."""

    @abstractmethod
    def toggle_topic_visibility(self, display_name: str, topic: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_topic_visibility(self, display_name: str) -> dict[str, Any]: ...

    @abstractmethod
    def view_presets(self) -> dict[str, Any]: ...

    @abstractmethod
    def set_view_preset(self, name: str) -> dict[str, Any]: ...

    @abstractmethod
    def display_properties(self, display_name: str) -> dict[str, Any]: ...

    @abstractmethod
    def update_display_properties(
        self,
        display_name: str,
        color: list[float] | None = None,
        size: float | None = None,
        alpha: float | None = None,
    ) -> dict[str, Any]: ...
