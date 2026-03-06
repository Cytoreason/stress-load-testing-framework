from __future__ import annotations

from collections.abc import Awaitable, Callable

Journey = Callable[[], Awaitable[None]]


class JourneyCatalog:
    def __init__(self) -> None:
        self._items: dict[str, Journey] = {}

    def register(self, name: str, journey: Journey) -> None:
        self._items[name] = journey

    def get(self, name: str) -> Journey:
        return self._items[name]
